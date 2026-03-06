import axios from "axios";

/* ======================================================
   Base API Configuration
====================================================== */

const BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

/* ======================================================
   Global Response / Error Handler
====================================================== */

api.interceptors.response.use(
  (response) => response,
  (error) => {

    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error ||
      error?.response?.data ||
      error.message;

    console.error("API ERROR:", message);

    return Promise.reject(error);
  }
);

/* ======================================================
   Creator APIs
====================================================== */

export const getCreatorByUsername = (username) =>
  api.get(`/api/creator/username/${username}`);

export const getCreatorProfile = (id) =>
  api.get(`/api/creator/profile/${id}`);

export const getCreatorAnalytics = (id) =>
  api.get(`/api/creator/analytics/${id}`);

export const getCreatorScore = (id) =>
  api.get(`/api/creator/score/${id}`);

export const getAllCreators = () =>
  api.get("/api/creator/all");

export const registerCreator = (data) =>
  api.post("/api/creator/register", data);


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

/* Price Prediction (uses username) */
export const predictPrice = (data) =>
  api.post("/api/ai/price/predict", data);

/* Brand Risk Prediction (uses username) */
export const predictRisk = (data) =>
  api.post("/api/ai/risk/predict", data);


/* ======================================================
   Collaboration APIs
====================================================== */

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


/* ======================================================
   Export Axios Instance
====================================================== */

export default api;