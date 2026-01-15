import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Signup() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("exam_center");
  const navigate = useNavigate();

  const signup = async () => {
    try {
      await axios.post("http://localhost:5000/api/signup", {
        username,
        password,
        role
      });

      alert("Signup successful. Please login.");
      navigate("/");
    } catch (err) {
      alert(err.response?.data?.error || "Signup failed");
    }
  };

  return (
    <div className="container">
      <h2>Signup</h2>

      <input placeholder="Username" onChange={e => setUsername(e.target.value)} />
      <input type="password" placeholder="Password" onChange={e => setPassword(e.target.value)} />

      <select onChange={e => setRole(e.target.value)}>
        <option value="exam_center">Exam Center</option>
      </select>

      <button onClick={signup}>Signup</button>
    </div>
  );
}

export default Signup;
