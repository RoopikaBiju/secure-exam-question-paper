const express = require("express");
const crypto = require("crypto");
const { decrypt } = require("../encryption/aes");
const { getPaperFromChain } = require("../blockchain/blockchain");
const uploadRoute = require("./upload");

const router = express.Router();

router.post("/verify-qr", async (req, res) => {
  try {
    const { paperId, role } = req.body;

    // 1️⃣ Role check
    if (role !== "exam_center") {
      return res.json({
        status: "DENIED",
        reason: "Unauthorized role"
      });
    }

    // 2️⃣ Paper existence check
    const paperData = uploadRoute.paperStore[paperId];
    if (!paperData) {
      return res.json({
        status: "DENIED",
        reason: "Paper not found"
      });
    }

    const { paperName, encryptedPaper, examTime } = paperData;

    // 3️⃣ Exam time check
    if (Date.now() < examTime) {
      return res.json({
        status: "DENIED",
        paperName,
        examTime,
        reason: "Exam has not started yet"
      });
    }

    // 4️⃣ Blockchain integrity check
    const localHash = crypto
      .createHash("sha256")
      .update(encryptedPaper)
      .digest("hex");

    let chainHash;
    try {
      [chainHash] = await getPaperFromChain(paperId);
    } catch (err) {
      return res.json({
        status: "DENIED",
        paperName,
        examTime,
        reason: "Blockchain verification failed"
      });
    }

    if (localHash !== chainHash) {
      return res.json({
        status: "DENIED",
        paperName,
        examTime,
        reason: "Paper tampered"
      });
    }

    // 5️⃣ Decrypt ONLY after all checks
    const decryptedPaper = decrypt(encryptedPaper);

    return res.json({
      status: "ALLOWED",
      paperId,
      paperName,
      examTime,
      paper: decryptedPaper
    });

  } catch (error) {
    console.error("VERIFY ERROR:", error);
    return res.status(500).json({ error: "Verification failed" });
  }
});

module.exports = router;
