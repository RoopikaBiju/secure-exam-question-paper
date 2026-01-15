import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const login = async () => {
    if (!username || !password) {
      alert("Please enter username and password");
      return;
    }

    try {
      setLoading(true);

      const res = await axios.post("http://localhost:5000/api/login", {
        username,
        password
        });

        localStorage.clear();
        localStorage.setItem("role", res.data.role);
        localStorage.setItem("loginTime", Date.now());

      if (res.data.role === "admin") {
        navigate("/upload");
      } else {
        navigate("/verify");
      }

    } catch {
      alert("Invalid login credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2>Secure Exam System Login</h2>

      <input
        placeholder="Username"
        onChange={(e) => setUsername(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />

      <button onClick={login} disabled={loading}>
        {loading ? "Authenticating..." : "Login"}
      </button>
      <p style={{ fontSize: "12px", opacity: 0.7 }}>
        Admin uploads papers · Exam Center verifies access
      </p>

    </div>
  );
}

export default Login;
