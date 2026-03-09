import json
import hashlib
import os
import io
import base64
import socket
import logging
import time
import qrcode
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request, session, send_file
from web3 import Web3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('secureexam.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secureexam_secret_2024")

# ── Config ───────────────────────────────────────────────
ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD",  "admin123")
CENTER_PASSWORD = os.environ.get("CENTER_PASSWORD", "center123")

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_DIR = os.path.join(BASE_DIR, "papers")
KEYS_FILE  = os.path.join(BASE_DIR, "all_keys.json")
os.makedirs(PAPERS_DIR, exist_ok=True)

# ── Web3 ─────────────────────────────────────────────────
w3 = Web3(Web3.HTTPProvider(os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")))

with open(os.path.join(BASE_DIR, "abi.json")) as f:
    CONTRACT_ABI = json.load(f)

with open(os.path.join(BASE_DIR, "contract_address.txt")) as f:
    CONTRACT_ADDRESS = f.read().strip()

ADMIN_ADDRESS     = os.environ.get("ADMIN_ADDRESS",     "0x78DEF89DbffA1B6eF4787Cf72ac07a78B0b7790B")
ADMIN_PRIVATE_KEY = os.environ.get("ADMIN_PRIVATE_KEY", "0x407394046adad7a1dad93054408228a71bb6cd324f1613fb83903dda0703124d")

# ── Helpers ──────────────────────────────────────────────
def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            return json.load(f)
    return {}

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_admin():
    return session.get("role") == "admin"

def is_center(exam_id=None):
    if session.get("role") != "center":
        return False
    if exam_id is not None:
        return session.get("center_exam_id") == exam_id
    return True

def get_contract():
    return w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def send_tx(tx):
    signed  = w3.eth.account.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()

def decrypt_paper(exam_id):
    contract = get_contract()
    enc_file, paper_hash, _, is_released, exam_name = \
        contract.functions.getPaper(exam_id).call()

    if not is_released:
        raise Exception("Key not released yet")

    events      = contract.events.KeyReleased.get_logs(from_block=0)
    aes_key_hex = None
    for ev in events:
        if ev["args"]["examId"] == exam_id:
            aes_key_hex = ev["args"]["decryptionKey"]
            break

    if not aes_key_hex:
        raise Exception("Key not found in blockchain events")

    enc_path = os.path.join(PAPERS_DIR, enc_file)
    if not os.path.exists(enc_path):
        enc_path = os.path.join(BASE_DIR, enc_file)

    with open(enc_path, "rb") as f:
        enc_data = f.read()

    aesgcm    = AESGCM(bytes.fromhex(aes_key_hex))
    decrypted = aesgcm.decrypt(enc_data[:12], enc_data[12:], None)

    computed = hashlib.sha256(decrypted).hexdigest()
    if computed != paper_hash.hex():
        raise Exception("Integrity check failed — paper hash mismatch!")

    return decrypted, enc_file.replace(".enc", ""), exam_name

# ── Auto-Release Scheduler ────────────────────────────────
def auto_release_keys():
    """Runs every minute. Automatically releases keys whose exam time has passed."""
    try:
        if not w3.is_connected():
            log.warning("Auto-release: Ganache not connected, skipping.")
            return

        contract = get_contract()
        count    = contract.functions.paperCount().call()
        now      = int(time.time())

        for i in range(count):
            try:
                _, _, unlock_time, is_released, exam_name = \
                    contract.functions.getPaper(i).call()

                if not is_released and now >= unlock_time:
                    tx = contract.functions.releaseKey(i).build_transaction({
                        "from":     ADMIN_ADDRESS,
                        "nonce":    w3.eth.get_transaction_count(ADMIN_ADDRESS),
                        "gas":      100000,
                        "gasPrice": w3.to_wei("20", "gwei")
                    })
                    tx_hash = send_tx(tx)
                    log.info(f"[AUTO-RELEASE] Exam #{i} '{exam_name}' key released | TX: {tx_hash}")

            except Exception as e:
                # Skip already-released or errored exams silently
                err = str(e).lower()
                if "already released" not in err and "exam time not reached" not in err:
                    log.warning(f"[AUTO-RELEASE] Exam #{i} error: {e}")

    except Exception as e:
        log.error(f"[AUTO-RELEASE] Scheduler error: {e}")

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(auto_release_keys, 'interval', minutes=1, id='auto_release')
scheduler.start()
log.info("Auto-release scheduler started — checks every 60 seconds")

# ── Pages ────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/exam/<int:exam_id>")
def exam_center(exam_id):
    return render_template("exam_center.html", exam_id=exam_id)

# ── Auth ─────────────────────────────────────────────────
@app.route("/api/auth")
def auth_status():
    return jsonify({
        "role":           session.get("role", "public"),
        "is_admin":       is_admin(),
        "center_exam_id": session.get("center_exam_id")
    })

@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    password = data.get("password", "")
    exam_id  = data.get("exam_id")

    if password == ADMIN_PASSWORD:
        session["role"] = "admin"
        log.info(f"Admin login from {request.remote_addr}")
        return jsonify({"success": True, "role": "admin"})

    elif password == CENTER_PASSWORD and exam_id is not None:
        session["role"]           = "center"
        session["center_exam_id"] = int(exam_id)
        return jsonify({"success": True, "role": "center", "exam_id": exam_id})

    return jsonify({"success": False, "error": "Wrong password"})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

# ── Papers (public can see status only) ──────────────────
@app.route("/api/papers")
def get_papers():
    try:
        contract = get_contract()
        count    = contract.functions.paperCount().call()
        papers   = []
        for i in range(count):
            enc_file, paper_hash, unlock_time, is_released, exam_name = \
                contract.functions.getPaper(i).call()
            papers.append({
                "id":          i,
                "exam_name":   exam_name,
                "enc_file":    enc_file,
                "paper_hash":  paper_hash.hex(),
                "unlock_time": unlock_time,
                "unlock_str":  datetime.fromtimestamp(unlock_time).strftime("%d %b %Y, %I:%M %p"),
                "is_released": is_released,
            })
        return jsonify({"success": True, "papers": papers, "count": count, "contract": CONTRACT_ADDRESS})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── Upload (admin only) ───────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload_paper():
    if not is_admin():
        return jsonify({"success": False, "error": "Unauthorized — admin only"})
    try:
        exam_name     = request.form.get("exam_name", "").strip()
        exam_datetime = request.form.get("exam_datetime", "").strip()
        content_type  = request.form.get("content_type", "text")

        if not exam_name:
            return jsonify({"success": False, "error": "Exam name is required"})
        if len(exam_name) > 100:
            return jsonify({"success": False, "error": "Exam name too long (max 100 chars)"})
        if not exam_datetime:
            return jsonify({"success": False, "error": "Exam date/time is required"})
        if content_type not in ("text", "file"):
            return jsonify({"success": False, "error": "Invalid content type"})

        if content_type == "file":
            f = request.files.get("paper_file")
            if not f:
                return jsonify({"success": False, "error": "No file uploaded"})
            paper_bytes = f.read()
            base_name   = f.filename
        else:
            text = request.form.get("paper_text", "").strip()
            if not text:
                return jsonify({"success": False, "error": "Paper text cannot be empty"})
            paper_bytes = text.encode("utf-8")
            base_name   = exam_name.replace(" ", "_") + ".txt"

        original_hash = hashlib.sha256(paper_bytes).hexdigest()
        aes_key       = AESGCM.generate_key(bit_length=256)
        nonce         = os.urandom(12)
        aesgcm        = AESGCM(aes_key)
        encrypted     = aesgcm.encrypt(nonce, paper_bytes, None)

        enc_name = base_name + ".enc"
        enc_path = os.path.join(PAPERS_DIR, enc_name)
        with open(enc_path, "wb") as ef:
            ef.write(nonce + encrypted)

        exam_dt     = datetime.strptime(exam_datetime, "%Y-%m-%dT%H:%M")
        unlock_time = int(exam_dt.timestamp())

        contract         = get_contract()
        paper_hash_bytes = bytes.fromhex(original_hash)

        tx = contract.functions.uploadPaper(
            enc_name, paper_hash_bytes, unlock_time, aes_key.hex(), exam_name
        ).build_transaction({
            "from":     ADMIN_ADDRESS,
            "nonce":    w3.eth.get_transaction_count(ADMIN_ADDRESS),
            "gas":      400000,
            "gasPrice": w3.to_wei("20", "gwei")
        })
        tx_hash = send_tx(tx)

        keys    = load_keys()
        exam_id = contract.functions.paperCount().call() - 1
        keys[str(exam_id)] = {
            "exam_name":     exam_name,
            "original_hash": original_hash,
            "aes_key_hex":   aes_key.hex(),
            "enc_path":      enc_path,
            "tx_hash":       tx_hash
        }
        save_keys(keys)
        log.info(f"Paper uploaded: '{exam_name}' (ID #{exam_id}) | unlock: {exam_datetime}")

        return jsonify({"success": True, "exam_id": exam_id, "tx_hash": tx_hash,
                        "hash": original_hash, "enc_file": enc_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── Release key (admin only) ──────────────────────────────
@app.route("/api/release/<int:exam_id>", methods=["POST"])
def release_key(exam_id):
    if not is_admin():
        return jsonify({"success": False, "error": "Unauthorized — admin only"})
    try:
        contract = get_contract()
        tx = contract.functions.releaseKey(exam_id).build_transaction({
            "from":     ADMIN_ADDRESS,
            "nonce":    w3.eth.get_transaction_count(ADMIN_ADDRESS),
            "gas":      100000,
            "gasPrice": w3.to_wei("20", "gwei")
        })
        tx_hash = send_tx(tx)
        log.info(f"[MANUAL RELEASE] Exam #{exam_id} key released | TX: {tx_hash}")
        return jsonify({"success": True, "tx_hash": tx_hash})
    except Exception as e:
        err = str(e).lower()
        if "exam time not reached" in err or "revert" in err:
            msg = "❌ Cannot release key yet — exam time has not been reached."
        elif "already released" in err:
            msg = "❌ Key has already been released for this exam."
        else:
            msg = "❌ Transaction failed. Make sure Ganache is running."
        return jsonify({"success": False, "error": msg})

# ── Verify — PUBLIC, anyone can check hash ───────────────
@app.route("/api/verify/<int:exam_id>")
def verify_paper(exam_id):
    try:
        decrypted, _, _        = decrypt_paper(exam_id)
        contract               = get_contract()
        _, paper_hash, _, _, _ = contract.functions.getPaper(exam_id).call()
        computed = hashlib.sha256(decrypted).hexdigest()
        stored   = paper_hash.hex()
        return jsonify({"success": True, "verified": computed == stored,
                        "computed_hash": computed, "stored_hash": stored})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── View paper (center or admin only) ────────────────────
@app.route("/api/view/<int:exam_id>")
def view_paper(exam_id):
    if not is_admin() and not is_center(exam_id):
        return jsonify({"success": False, "error": "Unauthorized — please login as exam center"})
    try:
        decrypted, original_name, exam_name = decrypt_paper(exam_id)
        is_pdf = decrypted[:4] == b'%PDF'
        if is_pdf:
            return jsonify({"success": True, "type": "pdf",
                            "content": base64.b64encode(decrypted).decode(),
                            "filename": exam_name})
        else:
            return jsonify({"success": True, "type": "text",
                            "content": decrypted.decode("utf-8"),
                            "filename": exam_name})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── Download (center or admin only) ──────────────────────
@app.route("/api/download/<int:exam_id>")
def download_paper(exam_id):
    if not is_admin() and not is_center(exam_id):
        return jsonify({"success": False, "error": "Unauthorized — please login as exam center"}), 403
    try:
        decrypted, original_name, exam_name = decrypt_paper(exam_id)
        is_pdf  = decrypted[:4] == b'%PDF'
        mime    = "application/pdf" if is_pdf else "application/octet-stream"
        dl_name = f"{exam_name.replace(' ', '_')}.pdf" if is_pdf else original_name
        return send_file(io.BytesIO(decrypted), as_attachment=True,
                         download_name=dl_name, mimetype=mime)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ── Tamper demo (admin/center only) ──────────────────────
@app.route("/api/tamper/<int:exam_id>")
def tamper_demo(exam_id):
    if not is_admin() and not is_center(exam_id):
        return jsonify({"success": False, "error": "Exam center login required"})
    try:
        keys      = load_keys()
        key_entry = keys.get(str(exam_id))
        if not key_entry:
            return jsonify({"success": False, "error": "Key data not found locally"})

        enc_path = key_entry["enc_path"]
        if not os.path.exists(enc_path):
            enc_path = os.path.join(PAPERS_DIR, os.path.basename(enc_path))

        with open(enc_path, "rb") as f:
            original = f.read()

        aes_key = bytes.fromhex(key_entry["aes_key_hex"])
        aesgcm  = AESGCM(aes_key)

        try:
            aesgcm.decrypt(original[:12], original[12:], None)
            original_ok = True
        except Exception:
            original_ok = False

        tampered     = bytearray(original)
        tampered[20] = (tampered[20] + 1) % 256
        tampered[21] = (tampered[21] + 1) % 256

        try:
            aesgcm.decrypt(bytes(tampered[:12]), bytes(tampered[12:]), None)
            detected = False
        except Exception:
            detected = True

        return jsonify({"success": True, "original_ok": original_ok,
                        "detected": detected, "bytes_changed": 2,
                        "message": "AES-GCM auth tag mismatch — tampering instantly detected!"
                                   if detected else "No tampering detected"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── Update unlock time (admin only) ──────────────────────
@app.route("/api/update-time/<int:exam_id>", methods=["POST"])
def update_unlock_time(exam_id):
    if not is_admin():
        return jsonify({"success": False, "error": "Unauthorized — admin only"})
    try:
        data         = request.get_json()
        new_datetime = data.get("exam_datetime", "").strip()
        if not new_datetime:
            return jsonify({"success": False, "error": "Date/time is required"})

        exam_dt    = datetime.strptime(new_datetime, "%Y-%m-%dT%H:%M")
        new_unlock = int(exam_dt.timestamp())

        contract = get_contract()
        _, _, _, is_released, exam_name = contract.functions.getPaper(exam_id).call()
        if is_released:
            return jsonify({"success": False, "error": "Cannot change time — key already released"})

        tx = contract.functions.updateUnlockTime(exam_id, new_unlock).build_transaction({
            "from":     ADMIN_ADDRESS,
            "nonce":    w3.eth.get_transaction_count(ADMIN_ADDRESS),
            "gas":      100000,
            "gasPrice": w3.to_wei("20", "gwei")
        })
        tx_hash = send_tx(tx)
        log.info(f"Unlock time updated for exam #{exam_id} to {new_datetime}")

        return jsonify({
            "success":   True,
            "tx_hash":   tx_hash,
            "new_time":  datetime.fromtimestamp(new_unlock).strftime("%d %b %Y, %I:%M %p"),
            "exam_name": exam_name
        })
    except Exception as e:
        err = str(e)
        if "revert" in err.lower():
            return jsonify({"success": False, "error": "Cannot update — check exam exists and key not released"})
        return jsonify({"success": False, "error": "Transaction failed: " + err})

# ── QR code (admin only) ──────────────────────────────────
@app.route("/api/qr/<int:exam_id>")
def generate_qr(exam_id):
    if not is_admin():
        return jsonify({"success": False, "error": "Unauthorized — admin only"})
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        exam_url = f"http://{local_ip}:5000/exam/{exam_id}"
        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_H,
                           box_size=10, border=4)
        qr.add_data(exam_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#3dffa0", back_color="#0b1120")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return jsonify({"success": True,
                        "qr_b64": base64.b64encode(buf.getvalue()).decode(),
                        "exam_url": exam_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    log.info(f"Ganache connected: {w3.is_connected()}")
    log.info(f"Contract: {CONTRACT_ADDRESS}")
    log.info(f"Admin address: {ADMIN_ADDRESS}")
    log.info("Passwords loaded from environment")
    log.info("Running at http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)