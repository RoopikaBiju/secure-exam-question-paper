const express = require("express");
const { decrypt } = require("../encryption/aes");
const { isExamTimeAllowed } = require("../utils/timeCheck");
// later we’ll add blockchain verification here

const router = express.Router();

/*
  This route is called ONLY at exam time
*/
router.post("/decrypt", async (req, res) => {
  const { encryptedPaper } = req.body;

  if (!encryptedPaper) {
    return res.status(400).json({ message: "Encrypted paper missing" });
  }

  // 1️⃣ Exam-time check
  if (!isExamTimeAllowed()) {
    return res.status(403).json({ message: "Exam not started yet" });
  }

  // 2️⃣ Decrypt
  const decryptedPaper = decrypt(encryptedPaper);

  res.json({
    message: "Paper decrypted successfully",
    paper: decryptedPaper
  });
});

module.exports = router;
