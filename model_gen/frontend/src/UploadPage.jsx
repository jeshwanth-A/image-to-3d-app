import React, { useState } from "react";
import axios from "axios";
export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [modelUrl, setModelUrl] = useState("");

  const handleUpload = async () => {
    if (!file) return alert("Please select an image");

    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await axios.post("http://localhost:8003/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setModelUrl(response.data.model_url);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Check backend logs.");
    }
  };

  return (
    <div>
      <h2>Upload an Image to Generate a 3D Model</h2>
      <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>

      {modelUrl && (
        <div>
          <p>3D Model Ready: <a href={modelUrl} target="_blank" rel="noopener noreferrer">Download Here</a></p>
        </div>
      )}
    </div>
  );
}