import json
import hashlib
import os
import logging
from web3 import Web3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")))

with open("abi.json") as f:
    CONTRACT_ABI = json.load(f)
with open("contract_address.txt") as f:
    CONTRACT_ADDRESS = f.read().strip()


def fetch_and_decrypt(exam_id: int, output_path: str):
    try:
        contract    = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        paper_count = contract.functions.paperCount().call()

        if exam_id >= paper_count:
            log.error(f"Exam ID {exam_id} does not exist (total: {paper_count})")
            return

        ipfs_hash, paper_hash, unlock_time, is_released, exam_name = \
            contract.functions.getPaper(exam_id).call()

        log.info(f"Exam: {exam_name} | Released: {is_released}")

        if not is_released:
            log.error("Key not released yet — exam time not reached!")
            return

        events      = contract.events.KeyReleased.get_logs(from_block=0)
        aes_key_hex = None
        for event in events:
            if event['args']['examId'] == exam_id:
                aes_key_hex = event['args']['decryptionKey']
                break

        if not aes_key_hex:
            log.error("Key not found in blockchain events!")
            return

        with open("all_keys.json") as f:
            all_keys = json.load(f)

        key_entry = all_keys.get(str(exam_id))
        if not key_entry:
            log.error(f"No key entry found for exam {exam_id}")
            return

        enc_path = key_entry["enc_path"]
        if not os.path.exists(enc_path):
            log.error(f"Encrypted file not found: {enc_path}")
            return

        with open(enc_path, 'rb') as f:
            enc_data = f.read()

        try:
            aesgcm    = AESGCM(bytes.fromhex(aes_key_hex))
            decrypted = aesgcm.decrypt(enc_data[:12], enc_data[12:], None)
        except Exception:
            log.error("Decryption FAILED — AES-GCM tag mismatch. File may be tampered!")
            return

        computed = hashlib.sha256(decrypted).hexdigest()
        stored   = paper_hash.hex()

        if computed != stored:
            log.error(f"Integrity FAILED!\nComputed: {computed}\nStored  : {stored}")
            return

        log.info("Integrity verified — paper is genuine!")

        with open(output_path, 'wb') as f:
            f.write(decrypted)

        log.info(f"Paper saved to: {output_path}")

    except Exception as e:
        log.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    fetch_and_decrypt(exam_id=0, output_path="decrypted_paper.pdf")
