// backend/data/users.js
const users = [
  {
    username: "admin",
    password: "$2a$12$dGuMfxT1UGG/H18jKD5Ii.mNMwom2Vhtabgf66T7UUxTReDeISGm2", // bcrypt("admin123")
    role: "admin"
  },
  {
    username: "center1",
    password: "$2a$12$XVl1Mjb9cYF9stKiyjWId.gxi8IJY4HGAEU32.qF8AcHgKZ6Znn0C", // bcrypt("center123")
    role: "exam_center"
  }
];


module.exports = users;
