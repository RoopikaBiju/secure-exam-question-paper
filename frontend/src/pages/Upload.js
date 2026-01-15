import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

function Upload() {
  const [file, setFile] = useState(null);
  const [paperName, setPaperName] = useState("");
  const [qr, setQr] = useState("");
  const navigate = useNavigate();
  const [examTime, setExamTime] = useState("");


  // ✅ LOGOUT FUNCTION (correct place)
  const logout = () => {
    localStorage.clear();
    navigate("/");
  };

  const uploadPaper = async () => {
  if (!file || !paperName || !examTime) {
    alert("Please fill all fields (paper, name, exam time)");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("paper", file);
    formData.append("paperName", paperName);
    formData.append("examTime", new Date(examTime).getTime()); // ✅ ADD THIS

    const res = await axios.post(
      "http://localhost:5000/api/upload",
      formData
    );

    setQr(res.data.qrCode);
  } catch (err) {
    console.error(err);
    alert("Upload failed");
  }
};


  return (
    <div className="container">
      <h2>Admin - Upload Paper</h2>

      {/* ✅ Logout button */}
      <button
        onClick={logout}
        style={{ float: "right", backgroundColor: "#dc3545" }}
      >
        Logout
      </button>

      <input
        type="text"
        placeholder="Paper Name (e.g., CS301 - End Semester Exam)"
        value={paperName}
        onChange={(e) => setPaperName(e.target.value)}
      />

        <input
    type="datetime-local"
    onChange={(e) => setExamTime(e.target.value)}
    />


      <br /><br />

      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br /><br />

      <button onClick={uploadPaper}>Upload</button>

      {qr && (
        <>
          <br /><br />
          <h4>QR Code for Exam Center</h4>
          <img src={qr} width="250" alt="QR Code" />
          <br /><br />
          <button onClick={() => navigate("/verify")}>
            Go to Exam Center
          </button>
        </>
      )}
    </div>
  );
}

export default Upload;
