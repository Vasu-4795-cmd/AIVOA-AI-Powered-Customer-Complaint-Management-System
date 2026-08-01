import React, { useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { uploadAndExtract } from "../store/complaintsSlice";

export default function FileUpload() {
  const dispatch = useDispatch();
  const inputRef = useRef();
  const { extractStatus, extractError } = useSelector((s) => s.complaints);

  const handleFile = (file) => {
    if (!file) return;
    dispatch(uploadAndExtract(file));
  };

  return (
    <div>
      <div
        className="upload-box"
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFile(e.dataTransfer.files[0]);
        }}
      >
        <strong>Upload complaint PDF / email / image</strong>
        <div style={{ marginTop: 6 }}>
          Drag & drop, or click to browse — AI will auto-fill the form below
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt,.eml,.png,.jpg,.jpeg"
          hidden
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>
      {extractStatus === "loading" && <p>Extracting fields with AI Copilot…</p>}
      {extractStatus === "failed" && <p className="error-text">{extractError}</p>}
    </div>
  );
}
