import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";

import Dashboard from "./pages/Dashboard";
import CreatorSearch from "./pages/CreatorSearch";
import CreatorProfile from "./pages/CreatorProfile";
import Analytics from "./pages/Analytics";
import PricePredictor from "./pages/PricePredictor";
import CollaborationHistory from "./pages/CollaborationHistory";
import CreateCollaboration from "./pages/CreateCollaboration";
import UpdateCollaboration from "./pages/UpdateCollaboration";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {

  const token = sessionStorage.getItem("token");

  return (

    <BrowserRouter>

      {token && <Navbar />}

      <div className="app-layout">

        <main className="main-content">

          <Routes>

            {/* Public Routes */}

            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Routes */}

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/search"
              element={
                <ProtectedRoute>
                  <CreatorSearch />
                </ProtectedRoute>
              }
            />

            <Route
              path="/creator/:username"
              element={
                <ProtectedRoute>
                  <CreatorProfile />
                </ProtectedRoute>
              }
            />

            <Route
              path="/analytics/:id"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />

            <Route
              path="/price-predictor"
              element={
                <ProtectedRoute>
                  <PricePredictor />
                </ProtectedRoute>
              }
            />

            <Route
              path="/create-collaboration"
              element={
                <ProtectedRoute>
                  <CreateCollaboration />
                </ProtectedRoute>
              }
            />

            <Route
              path="/collaborations"
              element={
                <ProtectedRoute>
                  <CollaborationHistory />
                </ProtectedRoute>
              }
            />

            <Route
              path="/update-collaboration/:id"
              element={
                <ProtectedRoute>
                  <UpdateCollaboration />
                </ProtectedRoute>
              }
            />

            {/* Default Route */}

            <Route
              path="/"
              element={
                token
                  ? <Navigate to="/dashboard" />
                  : <Navigate to="/login" />
              }
            />

          </Routes>

        </main>

      </div>

    </BrowserRouter>

  );

}