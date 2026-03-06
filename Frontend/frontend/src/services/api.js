import axios from "axios";

/* ─────────────────────────────────────────────────────────────
   Base config
───────────────────────────────────────────────────────────── */
const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error(
      "API ERROR:",
      err?.response?.data?.message || err?.response?.data || err.message
    );
    return Promise.reject(err);
  }
);

/* ─────────────────────────────────────────────────────────────
   Creator APIs
───────────────────────────────────────────────────────────── */
export const getCreatorByUsername = (username) =>
  api.get(`/api/creator/username/${username}`);

export const getCreatorProfile = (id) =>
  api.get(`/api/creator/profile/${id}`);

export const getCreatorAnalytics = (id) =>
  api.get(`/api/creator/analytics/${id}`);

export const getCreatorScore = (id) =>
  api.get(`/api/creator/score/${id}`);

export const getAllCreators = () => api.get("/api/creator/all");

export const registerCreator = (data) =>
  api.post("/api/creator/register", data);

/* ─────────────────────────────────────────────────────────────
   Analytics APIs
───────────────────────────────────────────────────────────── */
export const getDashboard   = (id) => api.get(`/api/analytics/dashboard/${id}`);
export const getEngagement  = (id) => api.get(`/api/analytics/engagement/${id}`);
export const getDealsSummary = (id) => api.get(`/api/analytics/deals/summary/${id}`);

/* ─────────────────────────────────────────────────────────────
   ML — Price Prediction
   POST /api/ai/price/predict   { username }
───────────────────────────────────────────────────────────── */
export const predictPrice = (data) =>
  api.post("/api/ai/price/predict", data);

/* ─────────────────────────────────────────────────────────────
   ML — Risk Prediction
   POST /api/ai/risk/predict            { username }
   POST /api/ai/risk/predict/features   { followers, … }
───────────────────────────────────────────────────────────── */
export const predictRisk = (data) =>
  api.post("/api/ai/risk/predict", data);

export const predictRiskFromFeatures = (data) =>
  api.post("/api/ai/risk/predict/features", data);

/* ─────────────────────────────────────────────────────────────
   ML — Creator Score
   POST /api/ai/score/predict           { username }
   POST /api/ai/score/predict/features  { followers, … }
───────────────────────────────────────────────────────────── */
export const predictCreatorScore = (data) =>
  api.post("/api/ai/score/predict", data);

export const predictCreatorScoreFromFeatures = (data) =>
  api.post("/api/ai/score/predict/features", data);

/* ─────────────────────────────────────────────────────────────
   Combined helper – fires all three models in parallel for a username
───────────────────────────────────────────────────────────── */
export const predictAll = async (username) => {
  const [priceRes, riskRes, scoreRes] = await Promise.all([
    predictPrice({ username }),
    predictRisk({ username }),
    predictCreatorScore({ username }),
  ]);
  return {
    price: priceRes.data.data,
    risk:  riskRes.data.data,
    score: scoreRes.data.data,
  };
};

/* ─────────────────────────────────────────────────────────────
   Collaboration APIs
───────────────────────────────────────────────────────────── */
export const getCollaborations = (creatorId, status = null) =>
  api.get(`/api/collaboration/list/${creatorId}`, {
    params: status ? { status } : {},
  });

export const getCollaborationById = (collabId) =>
  api.get(`/api/collaboration/${collabId}`);

export const createCollaboration = (data) =>
  api.post("/api/collaboration/create", data);

export const updateCollaboration = (collabId, data) =>
  api.put(`/api/collaboration/update/${collabId}`, data);

export const deleteCollaboration = (collabId) =>
  api.delete(`/api/collaboration/${collabId}`);

export default api;
