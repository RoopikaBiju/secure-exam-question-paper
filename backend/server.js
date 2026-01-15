const express = require("express");
const cors = require("cors");
require("dotenv").config();

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// routes
const uploadRoute = require("./routes/upload");
const verifyRoute = require("./routes/verify");
const authRoute = require("./routes/auth");
const papersRoute = require("./routes/papers");

app.use("/api", uploadRoute);
app.use("/api", verifyRoute);
app.use("/api", authRoute);
app.use("/api", papersRoute);

app.get("/", (req, res) => {
  res.send("Secure Exam System Backend Running");
});

// 🚨 THIS MUST EXIST
app.listen(5000, () => {
  console.log("Server running on port 5000");
});

// 🔒 Global crash guards (recommended)
process.on("uncaughtException", err => {
  console.error("UNCAUGHT EXCEPTION:", err);
});

process.on("unhandledRejection", err => {
  console.error("UNHANDLED PROMISE REJECTION:", err);
});
