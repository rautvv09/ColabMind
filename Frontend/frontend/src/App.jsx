import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import CreatorSearch from "./pages/CreatorSearch";
import CreatorProfile from "./pages/CreatorProfile";
import Analytics from "./pages/Analytics";
import PricePredictor from "./pages/PricePredictor";
import CollaborationHistory from "./pages/CollaborationHistory";
import CreateCollaboration from "./pages/CreateCollaboration";

export default function App() {

  return (

    <BrowserRouter>

      <div className="app-layout">

        {/* Sidebar */}

        <Navbar />

        {/* Main Content */}

        <main className="main-content">

          <Routes>

            <Route
              path="/"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route
              path="/dashboard"
              element={<Dashboard />}
            />

            <Route
              path="/search"
              element={<CreatorSearch />}
            />

            <Route
              path="/creator/:username"
              element={<CreatorProfile />}
            />

            <Route
              path="/analytics/:id"
              element={<Analytics />}
            />

            <Route
              path="/price-predictor"
              element={<PricePredictor />}
            />

            <Route
              path="/create-collaboration"
              element={<CreateCollaboration />}
            />

            <Route
              path="/collaborations/:id"
              element={<CollaborationHistory />}
            />

          </Routes>

        </main>

      </div>

    </BrowserRouter>

  );

}