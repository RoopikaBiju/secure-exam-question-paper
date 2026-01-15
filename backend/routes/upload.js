const express = require("express");
const multer = require("multer");
const crypto = require("crypto");
const QRCode = require("qrcode");

const { encrypt } = require("../encryption/aes");
const { storePaperOnChain } = require("../blockchain/blockchain");

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

// TEMP in-memory store (OK for mini-project)
const paperStore = {};

router.post("/upload", upload.single("paper"), async (req, res) => {
  try {
    const { paperName, examTime } = req.body;

    if (!paperName || !examTime) {
      return res.status(400).json({ error: "Paper name and exam time required" });
    }

    if (!req.file) {
      return res.status(400).json({ error: "Paper file required" });
    }

    const examTimeMs = Number(examTime);

    if (isNaN(examTimeMs)) {
      return res.status(400).json({ error: "Invalid exam time" });
    }

    const paperId = "PAPER_" + crypto.randomUUID();
    const paperText = req.file.buffer.toString("base64");

    // Encrypt
    const encrypted = encrypt(paperText);

    // Hash
    const hash = crypto.createHash("sha256").update(encrypted).digest("hex");

    // Blockchain (seconds)
    await storePaperOnChain(paperId, hash, Math.floor(examTimeMs / 1000));

    // Store locally
    paperStore[paperId] = {
        paperName,
        encryptedPaper: encrypted,
        examTime: examTimeMs,
        status: "PUBLISHED"
    };


    // QR payload
    const qrPayload = {
      paperId,
      issuedAt: Date.now(),
      expiresAt: examTimeMs + (5 * 60 * 1000)
    };

    const qrCode = await QRCode.toDataURL(JSON.stringify(qrPayload));

    res.json({
      message: "Paper uploaded successfully",
      paperId,
      paperName,
      examTime: examTimeMs,
      qrCode
    });

  } catch (error) {
    console.error("UPLOAD ERROR:", error);
    res.status(500).json({ error: "Upload failed" });
  }
});


// EXPORT paperStore SAFELY
// router.paperStore = paperStore;

module.exports = router;
module.exports.paperStore = paperStore;

