import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Upload from "./pages/Upload";
import Verify from "./pages/Verify";
import Download from "./pages/Download";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import "./App.css";

// Simple route guard
function ProtectedRoute({ children, allowedRole }) {
  const role = localStorage.getItem("role");

  if (!role || role !== allowedRole) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Protected routes */}
        <Route
          path="/upload"
          element={
            <ProtectedRoute allowedRole="admin">
              <Upload />
            </ProtectedRoute>
          }
        />

        <Route
          path="/verify"
          element={
            <ProtectedRoute allowedRole="exam_center">
              <Verify />
            </ProtectedRoute>
          }
        />

        <Route
          path="/download"
          element={
            <ProtectedRoute allowedRole="exam_center">
              <Download />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
