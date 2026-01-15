const express = require("express");
const uploadRoute = require("./upload");

const router = express.Router();

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
