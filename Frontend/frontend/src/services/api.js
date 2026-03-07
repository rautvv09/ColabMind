import axios from "axios";

/* ======================================================
   Base API Configuration
====================================================== */

const BASE_URL =
  import.meta.env.VITE_API_URL || "https://colabmind.onrender.com";
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

/* ======================================================
   Attach JWT Token Automatically
====================================================== */

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ======================================================
   Global Error Handler
====================================================== */

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error   ||
      error?.response?.data          ||
      error.message;
    console.error("API ERROR:", message);
    return Promise.reject(error);
  }
);

/* ======================================================
   Brand Authentication APIs
====================================================== */

export const loginBrand    = (data) => api.post("/api/brand/login",    data);
export const registerBrand = (data) => api.post("/api/brand/register", data);


/* ======================================================
   Creator APIs
====================================================== */

export const getAllCreators = () =>
  api.get("/api/creator/all");

export const getCreatorByUsername = (username) =>
  api.get(`/api/creator/username/${username}`);

// Smart lookup — checks DB first, auto-scrapes via SearchAPI if missing.
// Response: { data: { ...profileDoc, scraped_fresh: true|false } }
export const lookupCreator = (username) =>
  api.get(`/api/creator/lookup/${username}`);

export const getCreatorProfile   = (id) => api.get(`/api/creator/profile/${id}`);
export const getCreatorAnalytics = (id) => api.get(`/api/creator/analytics/${id}`);
export const getCreatorScore     = (id) => api.get(`/api/creator/score/${id}`);

export const registerCreator = (data) =>
  api.post("/api/creator/register", data);


/* ======================================================
   Analytics APIs
====================================================== */

export const getDashboard    = (id) => api.get(`/api/analytics/dashboard/${id}`);
export const getEngagement   = (id) => api.get(`/api/analytics/engagement/${id}`);
export const getDealsSummary = (id) => api.get(`/api/analytics/deals/summary/${id}`);


/* ======================================================
   AI / ML — Price Prediction
   POST /api/ai/price/predict  { username }
====================================================== */

// Accepts plain string username — wraps in { username } for the backend
export const predictPrice = (username) =>
  api.post("/api/ai/price/predict", { username });


/* ======================================================
   AI / ML — Risk Prediction
   POST /api/ai/risk/predict  { username }  OR  { features }
====================================================== */

export const predictRisk = (data) =>
  api.post("/api/ai/risk/predict", data);


/* ======================================================
   AI / ML — Creator Score
   POST /api/ai/score/predict           { username }
   POST /api/ai/score/predict/features  { followers, … }
====================================================== */

export const predictCreatorScore = (username) =>
  api.post("/api/ai/score/predict", { username });

export const predictCreatorScoreFromFeatures = (data) =>
  api.post("/api/ai/score/predict/features", data);


/* ======================================================
   Combined helper — runs all 3 ML models in parallel
====================================================== */

export const predictAll = async (username) => {
  const u = username.trim().toLowerCase();

  const [priceRes, riskRes, scoreRes] = await Promise.all([
    predictPrice(u),
    predictRisk({ username: u }),
    predictCreatorScore(u),
  ]);

  return {
    price:         priceRes.data.data,
    risk:          riskRes.data.data,
    score:         scoreRes.data.data,
    scraped_fresh: priceRes.data.scraped_fresh ?? false,
  };
};


/* ======================================================
   Collaboration APIs
====================================================== */

export const createCollaboration = (data) =>
  api.post("/api/collaboration/create", data);

export const getCollaborations = (creatorId = null, status = null) =>
  creatorId
    ? api.get(`/api/collaboration/list/${creatorId}`, { params: status ? { status } : {} })
    : api.get("/api/collaboration/list");

export const getCollaborationById = (id)       => api.get(`/api/collaboration/${id}`);
export const updateCollaboration  = (id, data) => api.put(`/api/collaboration/update/${id}`, data);
export const deleteCollaboration  = (id)       => api.delete(`/api/collaboration/${id}`);


/* ======================================================
   Export Axios Instance
====================================================== */

export default api;