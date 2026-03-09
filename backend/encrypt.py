import os
import hashlib
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)


def encrypt_paper(paper_path: str) -> dict:
    """
    Encrypts a question paper using AES-256-GCM.
    Returns key data dict. Does NOT save to disk — app.py handles storage.
    """
    if not os.path.exists(paper_path):
        raise FileNotFoundError(f"Paper not found: {paper_path}")

    with open(paper_path, 'rb') as f:
        paper_bytes = f.read()

    if not paper_bytes:
        raise ValueError("Paper file is empty")

    original_hash = hashlib.sha256(paper_bytes).hexdigest()
    log.info(f"Paper SHA-256: {original_hash[:16]}...")

    aes_key = AESGCM.generate_key(bit_length=256)
    nonce   = os.urandom(12)

    aesgcm    = AESGCM(aes_key)
    encrypted = aesgcm.encrypt(nonce, paper_bytes, None)

    encrypted_path = paper_path + ".enc"
    with open(encrypted_path, 'wb') as f:
        f.write(nonce + encrypted)

    log.info(f"Encrypted paper saved: {os.path.basename(encrypted_path)}")

    return {
        "original_hash":  original_hash,
        "aes_key_hex":    aes_key.hex(),
        "encrypted_path": encrypted_path
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "question_paper.txt"
    result = encrypt_paper(path)
    log.info(f"Done. Hash: {result['original_hash']}")
