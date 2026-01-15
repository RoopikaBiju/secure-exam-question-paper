import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Download() {
  const navigate = useNavigate();
  const paperBase64 = localStorage.getItem("paperBase64");

  useEffect(() => {
    if (!paperBase64) return;

    const ACCESS_WINDOW = 5 * 60 * 1000; // 5 minutes

    const timer = setTimeout(() => {
      localStorage.removeItem("paperBase64");
      alert("Access expired. Please verify QR again.");
      navigate("/verify");
    }, ACCESS_WINDOW);

    return () => clearTimeout(timer);
  }, [paperBase64, navigate]);

  // 🔒 Access denied UI
  if (!paperBase64) {
    return (
      <div className="container">
        <h3 className="status denied">Access Denied</h3>
        <p>Please verify the QR code again.</p>
      </div>
    );
  }

  const download = () => {
    try {
      const binary = atob(paperBase64);
      const bytes = new Uint8Array(binary.length);

      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      const blob = new Blob([bytes], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = "QuestionPaper.pdf";
      a.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download paper. Please verify again.");
      localStorage.removeItem("paperBase64");
      navigate("/verify");
    }
  };

  return (
    <div className="container">
      <h2>Decrypted Question Paper</h2>

      <p style={{ color: "#28a745", fontWeight: "bold" }}>
        🔐 Access valid for 5 minutes
      </p>

      <button className="download-btn" onClick={download}>
        Download Question Paper (PDF)
      </button>
    </div>
  );
}

export default Download;
