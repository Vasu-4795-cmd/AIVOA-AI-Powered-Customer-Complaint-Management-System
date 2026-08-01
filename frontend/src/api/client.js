// import axios from 'axios'

// const api = axios.create({
//   baseURL: import.meta.env.VITE_API_BASE_URL || '',
//   timeout: 30000,
// })

// export default api



import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "https://aivoa-ai-powered-customer-complaint.onrender.com";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    Accept: "application/json",
  },
});

export default api;
