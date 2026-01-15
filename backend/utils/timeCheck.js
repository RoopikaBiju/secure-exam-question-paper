function isExamTimeAllowed() {
  const now = new Date();
  const examTime = new Date(process.env.EXAM_START_TIME);
  return now >= examTime;
}

module.exports = { isExamTimeAllowed };
