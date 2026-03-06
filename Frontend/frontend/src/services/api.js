import axios from "axios";

/* ======================================================
   Base API Configuration
====================================================== */

const BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json"
  }
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

export const getDashboard = (creatorId) =>
  api.get(`/api/analytics/dashboard/${creatorId}`);

export const getEngagement = (creatorId) =>
  api.get(`/api/analytics/engagement/${creatorId}`);

export const getDealsSummary = (creatorId) =>
  api.get(`/api/analytics/deals/summary/${creatorId}`);


/* ======================================================
   AI / ML APIs
====================================================== */

export const predictPrice = (data) =>
  api.post("/api/ai/price/predict", data);

export const predictRisk = (data) =>
  api.post("/api/ai/risk/predict", data);


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
   Export Axios Instance
====================================================== */

export default api;