import json
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ.get("GANACHE_URL", "http://127.0.0.1:7545")))

ADMIN_ADDRESS     = os.environ.get("ADMIN_ADDRESS")
ADMIN_PRIVATE_KEY = os.environ.get("ADMIN_PRIVATE_KEY")

if not ADMIN_ADDRESS or not ADMIN_PRIVATE_KEY:
    print("[✗] Set ADMIN_ADDRESS and ADMIN_PRIVATE_KEY in your .env file!")
    exit(1)

with open("abi.json") as f:
    CONTRACT_ABI = json.load(f)
with open("bytecode.json") as f:
    CONTRACT_BYTECODE = json.load(f)["object"]

if not w3.is_connected():
    print("[✗] Cannot connect to Ganache! Make sure it is running.")
    exit(1)

print("[✓] Connected to Ganache!")


def deploy_contract():
    contract = w3.eth.contract(abi=CONTRACT_ABI, bytecode=CONTRACT_BYTECODE)
    tx = contract.constructor().build_transaction({
        'from':     ADMIN_ADDRESS,
        'nonce':    w3.eth.get_transaction_count(ADMIN_ADDRESS),
        'gas':      2000000,
        'gasPrice': w3.to_wei('20', 'gwei')
    })
    signed  = w3.eth.account.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"[✓] Contract deployed at: {receipt.contractAddress}")
    with open("contract_address.txt", "w") as f:
        f.write(receipt.contractAddress)
    return receipt.contractAddress


if __name__ == "__main__":
    deploy_contract()
