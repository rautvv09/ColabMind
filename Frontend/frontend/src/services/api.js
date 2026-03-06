import axios from "axios";

/* ─────────────────────────────────────────────
   Base Config
───────────────────────────────────────────── */

const BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json"
  }
});


/* ─────────────────────────────────────────────
   Attach JWT Token Automatically
───────────────────────────────────────────── */

api.interceptors.request.use((config) => {

  const token = sessionStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;

});


/* ─────────────────────────────────────────────
   Global API Error Logger
───────────────────────────────────────────── */

api.interceptors.response.use(

  (res) => res,

  (err) => {

    console.error(
      "API ERROR:",
      err?.response?.data?.message ||
      err?.response?.data ||
      err.message
    );

    return Promise.reject(err);

  }

);


/* ======================================================
   Brand Authentication APIs
====================================================== */

export const loginBrand = (data) =>
  api.post("/api/brand/login", data);

export const registerBrand = (data) =>
  api.post("/api/brand/register", data);


/* ======================================================
   Creator APIs
====================================================== */

export const getAllCreators = () =>
  api.get("/api/creator/all");

export const registerCreator = (data) =>
  api.post("/api/creator/register", data);

export const getCreatorByUsername = (username) =>
  api.get(`/api/creator/username/${username}`);

export const getCreatorProfile = (id) =>
  api.get(`/api/creator/profile/${id}`);

export const getCreatorAnalytics = (id) =>
  api.get(`/api/creator/analytics/${id}`);

export const getCreatorScore = (id) =>
  api.get(`/api/creator/score/${id}`);


/* ======================================================
   Analytics APIs
====================================================== */

export const getDashboard = (id) =>
  api.get(`/api/analytics/dashboard/${id}`);

export const getEngagement = (id) =>
  api.get(`/api/analytics/engagement/${id}`);

export const getDealsSummary = (id) =>
  api.get(`/api/analytics/deals/summary/${id}`);


/* ======================================================
   AI / ML APIs
====================================================== */

export const predictPrice = (data) =>
  api.post("/api/ai/price/predict", data);

export const predictRisk = (data) =>
  api.post("/api/ai/risk/predict", data);

export const predictRiskFromFeatures = (data) =>
  api.post("/api/ai/risk/predict/features", data);

export const predictCreatorScore = (data) =>
  api.post("/api/ai/score/predict", data);

export const predictCreatorScoreFromFeatures = (data) =>
  api.post("/api/ai/score/predict/features", data);


/* ======================================================
   Combined ML Helper
====================================================== */

export const predictAll = async (username) => {

  const [priceRes, riskRes, scoreRes] = await Promise.all([
    predictPrice({ username }),
    predictRisk({ username }),
    predictCreatorScore({ username })
  ]);

  return {
    price: priceRes.data.data,
    risk: riskRes.data.data,
    score: scoreRes.data.data
  };

};


/* ======================================================
   Collaboration APIs
====================================================== */

export const createCollaboration = (data) =>
  api.post("/api/collaboration/create", data);

export const getCollaborations = () =>
  api.get("/api/collaboration/list");

export const getCollaborationById = (id) =>
  api.get(`/api/collaboration/${id}`);

export const updateCollaboration = (id, data) =>
  api.put(`/api/collaboration/update/${id}`, data);

export const deleteCollaboration = (id) =>
  api.delete(`/api/collaboration/${id}`);


/* ======================================================
   Export Axios instance
====================================================== */

export default api;