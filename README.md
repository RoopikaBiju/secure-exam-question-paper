# SecureExam — Blockchain-Based Exam Paper Security System

A lightweight blockchain framework for secure exam paper distribution using Python, Flask, Solidity, and Ganache. Exam papers are encrypted with AES-256-GCM, hashed with SHA-256, and stored on a local Ethereum blockchain. Keys are released automatically at exam time via a background scheduler.

---

## Features

- **AES-256-GCM Encryption** — Exam papers are encrypted before storage; unreadable until key is released
- **SHA-256 Integrity Hashing** — Paper hash stored immutably on blockchain; any tampering is detected
- **Admin Digital Signature** — Admin signs each paper hash with their Ethereum private key; proves authenticity and non-repudiation
- **Smart Contract Time-Lock** — `unlock_time` enforced on-chain; key cannot be released before exam time
- **Auto-Release Scheduler** — Background job checks every 60 seconds and releases keys automatically at exam time — no admin presence required
- **QR Code Access** — Admin generates QR code for each exam; exam center scans to access their paper
- **Role-Based Access** — Admin / Exam Center / Public viewer with separate permissions
- **Public Verification** — Anyone can verify paper integrity using the blockchain hash
- **Light/Dark Mode** — Full theme toggle across all pages

---

## Project Structure

```
exam_blockchain/
├── backend/
│   ├── decrypt.py          # Standalone decrypt & verify script
│   ├── deploy.py           # Deploy smart contract to Ganache
│   └── encrypt.py          # Standalone encrypt script
├── contracts/
│   └── ExamPaper.sol       # Solidity smart contract
├── frontend/
│   └── templates/
│       ├── index.html      # Admin dashboard
│       └── exam_center.html # Exam center portal
├── papers/                 # Encrypted paper files (.enc)
├── app.py                  # Flask backend
├── abi.json                # Contract ABI (from Remix)
├── bytecode.json           # Contract bytecode (from Remix)
├── contract_address.txt    # Deployed contract address
├── all_keys.json           # Local key store (gitignored)
├── requirements.txt        # Python dependencies
├── .env                    # Secrets (gitignored)
├── .env.example            # Template for .env
└── .gitignore
```

---

## Prerequisites

- Python 3.10+
- [Ganache](https://trufflesuite.com/ganache/) (local Ethereum blockchain)
- [Remix IDE](https://remix.ethereum.org/) (to compile contract)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/exam_blockchain.git
cd exam_blockchain
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your Ganache values:

```bash
cp .env.example .env
```

```env
SECRET_KEY=your_random_secret_key_here
ADMIN_PASSWORD=your_admin_password
CENTER_PASSWORD=your_center_password
ADMIN_ADDRESS=0xYourGanacheAddress
ADMIN_PRIVATE_KEY=0xYourPrivateKey
GANACHE_URL=http://127.0.0.1:7545
```

### 4. Start Ganache

Open Ganache and start a workspace quickstart. Copy the first account address and private key into `.env`.

### 5. Compile and deploy the smart contract

Open [Remix IDE](https://remix.ethereum.org/), paste `contracts/ExamPaper.sol`, compile it, then copy the generated `abi.json` and `bytecode.json` into the project root.

Then deploy:

```bash
python backend/deploy.py
```

This creates `contract_address.txt` automatically.

### 6. Run the application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## Usage

### Admin
1. Login with admin password
2. Go to **Upload Paper** — upload PDF or text, set exam date/time
3. System encrypts paper, signs hash, stores on blockchain
4. Generate **QR Code** and share with exam center
5. Key releases automatically at exam time — no manual action needed

### Exam Center
1. Scan QR code or visit `http://<ip>:5000/exam/<id>`
2. Login with center password
3. After key is released — **View Paper** or **Download Paper**

### Public
1. Visit the dashboard
2. Click **Verify** on any released exam to confirm paper integrity

---

## Security Model

```
Layer 1 — Confidentiality:   AES-256-GCM encryption
          Paper unreadable until key released at exam time

Layer 2 — Integrity:         SHA-256 hash stored on blockchain
          Any file tampering detected immediately

Layer 3 — Authenticity:      Admin digital signature (Ethereum private key)
          Proves admin uploaded the paper — non-repudiation
```

---

## Dependencies

```
flask==3.0.3
web3==6.15.1
cryptography==42.0.5
qrcode[pil]==7.4.2
Pillow==10.3.0
python-dotenv==1.0.1
apscheduler==3.10.4
```

---

## Important Notes

- **Never commit `.env`** — blocked by `.gitignore`
- **Never commit `all_keys.json`** — contains AES decryption keys
- **Never commit `papers/`** — contains encrypted exam files
- After restarting Ganache with a new workspace, update `.env` with new address/key and re-run `deploy.py`
- Run Flask with `debug=False` — `debug=True` starts Flask twice and causes duplicate scheduler transactions

---

## Based On

> Akhmetshin et al., *"A Lightweight Blockchain Framework for Secure Academic Credential Verification Using Python and Docker"*, ICCAMS 2025, IEEE.

This project extends the base paper's concepts (SHA-256 hashing, QR codes, blockchain immutability) to the exam paper distribution problem, adding AES-256-GCM encryption, smart contract time-lock, auto-release scheduling, and admin digital signatures.
