import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

function Verify() {
  const navigate = useNavigate();

  const [papers, setPapers] = useState([]);
  const [status, setStatus] = useState("");
  const [reason, setReason] = useState("");
  const [paperName, setPaperName] = useState("");
  const [examTime, setExamTime] = useState("");

  // ✅ LOGOUT FUNCTION
  const logout = () => {
    localStorage.clear();
    navigate("/");
  };

  // 1️⃣ Load available papers
  useEffect(() => {
    axios
      .get("http://localhost:5000/api/papers")
      .then(res => setPapers(res.data))
      .catch(err => console.error(err));
  }, []);

  // 2️⃣ Verify selected paper
  const verifyPaper = async (paperId) => {
    try {
      const res = await axios.post(
        "http://localhost:5000/api/verify-qr",
        {
          paperId,
          role: "exam_center"
        }
      );

      setStatus(res.data.status);
      setPaperName(res.data.paperName || "");
      setExamTime(res.data.examTime || "");
      setReason(res.data.reason || "");

      if (res.data.status === "ALLOWED") {
        localStorage.setItem("paperBase64", res.data.paperBase64);
        navigate("/download");
    }


    } catch (err) {
      console.error(err);
      setStatus("DENIED");
      setReason("Verification failed");
    }
  };

  return (
    <div className="container">
      <h2>Exam Center - Verify Question Paper</h2>

      {/* ✅ Logout button */}
      <button
        onClick={logout}
        style={{ float: "right", backgroundColor: "#dc3545" }}
      >
        Logout
      </button>

      <h3>Available Question Papers</h3>

      {papers.length === 0 && <p>No papers uploaded yet.</p>}

      <ul>
        {papers.map(p => (
          <li key={p.paperId}>
            <button onClick={() => verifyPaper(p.paperId)}>
              {p.paperName}
            </button>
          </li>
        ))}
      </ul>

      {paperName && (
        <div className="section">
          <p><strong>Paper:</strong> {paperName}</p>
          <p><strong>Exam Time:</strong> {new Date(examTime).toLocaleString()}</p>
        </div>
      )}

      {status && (
        <h3 className={status === "ALLOWED" ? "status" : "status denied"}>
          Status: {status}
        </h3>
      )}

      {reason && (
        <p className="status denied">
          Reason: {reason}
        </p>
      )}
    </div>
  );
}

export default Verify;
