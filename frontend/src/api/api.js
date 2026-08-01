import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

export const listComplaints = () => api.get("/api/complaints").then(r => r.data);
export const getComplaint = (id) => api.get(`/api/complaints/${id}`).then(r => r.data);
export const createComplaint = (payload) => api.post("/api/complaints", payload).then(r => r.data);
export const updateComplaint = (id, payload) => api.put(`/api/complaints/${id}`, payload).then(r => r.data);

export const extractFromFile = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/ai/extract", form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then(r => r.data);
};

export const analyzeComplaint = (complaintId) =>
  api.post("/api/ai/analyze", { complaint_id: complaintId }).then(r => r.data);
