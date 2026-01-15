// backend/routes/papers.js
const express = require("express");
const router = express.Router();
const uploadRoute = require("./upload");

router.get("/papers", (req, res) => {
  const papers = Object.entries(uploadRoute.paperStore).map(
    ([paperId, data]) => ({
      paperId,
      paperName: data.paperName,
      examTime: data.examTime
    })
  );

  res.json(papers);
});

module.exports = router;
