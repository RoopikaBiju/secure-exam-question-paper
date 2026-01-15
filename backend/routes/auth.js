const express = require("express");
const bcrypt = require("bcrypt");

const router = express.Router();

// In-memory users (OK for mini-project)
const users = require("../data/users");


/**
 * SIGNUP
 */
router.post("/signup", async (req, res) => {
  const { username, password, role } = req.body;

  if (!username || !password || !role) {
    return res.status(400).json({ error: "All fields required" });
  }
  if (role === "admin") {
  return res.status(403).json({ error: "Admin signup disabled" });
}


  const existing = users.find(u => u.username === username);
  if (existing) {
    return res.status(400).json({ error: "User already exists" });
  }

  const hashedPassword = await bcrypt.hash(password, 10);

  users.push({
    username,
    password: hashedPassword,
    role
  });

  res.json({ message: "Signup successful" });
});

/**
 * LOGIN
 */
router.post("/login", async (req, res) => {
  const { username, password } = req.body;

  console.log("LOGIN ATTEMPT:", username, password);
  console.log("USERS ARRAY:", users);

  if (!username || !password) {
    return res.status(400).json({ error: "All fields required" });
  }

  // ✅ DEFINE user FIRST
  const user = users.find(u => u.username === username);

  if (!user) {
    return res.status(401).json({ error: "Invalid login credentials" });
  }

  console.log("HASH IN DB:", user.password);

  // ✅ bcrypt compare AFTER user exists
  const isMatch = await bcrypt.compare(password, user.password);
  console.log("PASSWORD MATCH:", isMatch);

  if (!isMatch) {
    return res.status(401).json({ error: "Invalid login credentials" });
  }

  // ✅ SUCCESS
  return res.json({
    role: user.role,
    message: "Login successful"
  });
});





module.exports = router;
