// import axios from "axios";

// const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

// export const api = axios.create({ baseURL: API_BASE });

// export const listComplaints = () => api.get("/api/complaints").then(r => r.data);
// export const getComplaint = (id) => api.get(`/api/complaints/${id}`).then(r => r.data);
// export const createComplaint = (payload) => api.post("/api/complaints", payload).then(r => r.data);
// export const updateComplaint = (id, payload) => api.put(`/api/complaints/${id}`, payload).then(r => r.data);

// export const extractFromFile = (file) => {
//   const form = new FormData();
//   form.append("file", file);
//   return api.post("/api/ai/extract", form, {
//     headers: { "Content-Type": "multipart/form-data" },
//   }).then(r => r.data);
// };

// export const analyzeComplaint = (complaintId) =>
//   api.post("/api/ai/analyze", { complaint_id: complaintId }).then(r => r.data);


import axios from "axios";

// Render backend URL
const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://aivoa-ai-powered-customer-complaint.onrender.com";

// Axios instance
export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    Accept: "application/json",
  },
});

// ==============================
// Complaints
// ==============================

export const listComplaints = async () => {
  const response = await api.get("/api/complaints");
  return response.data;
};

export const getComplaint = async (id) => {
  const response = await api.get(`/api/complaints/${id}`);
  return response.data;
};

export const createComplaint = async (payload) => {
  const response = await api.post("/api/complaints", payload);
  return response.data;
};

export const updateComplaint = async (id, payload) => {
  const response = await api.put(`/api/complaints/${id}`, payload);
  return response.data;
};

// ==============================
// AI - Extract complaint from file
// ==============================

export const extractFromFile = async (file) => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post("/api/ai/extract", formData);

  return response.data;
};

// ==============================
// AI - Analyze complaint
// ==============================

export const analyzeComplaint = async (complaintId) => {
  const response = await api.post("/api/ai/analyze", {
    complaint_id: complaintId,
  });

  return response.data;
};

// ==============================
// AI Copilot - Parse complaint
// ==============================

export const parseCopilotComplaint = async (payload) => {
  const response = await api.post("/api/copilot/parse", payload);

  return response.data;
};

// ==============================
// Health Check
// ==============================

export const healthCheck = async () => {
  const response = await api.get("/");
  return response.data;
};
