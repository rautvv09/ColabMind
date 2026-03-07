import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { predictAll } from "../services/api";
import {
  RiMoneyDollarCircleLine,
  RiStarLine,
  RiShieldLine,
  RiSearchLine,
  RiLoader4Line,
  RiErrorWarningLine,
} from "react-icons/ri";
import "./PricePredictor.css";

/* ───────── Helpers ───────── */

const riskColour = (label = "") => {
  const l = label.toLowerCase();
  if (l.includes("low")) return "#00d4aa";
  if (l.includes("medium")) return "#f59e0b";
  if (l.includes("high")) return "#ef4444";
  return "var(--text-secondary)";
};

const scoreColour = (s = 0) =>
  s >= 7 ? "#00d4aa" : s >= 4 ? "#f59e0b" : "#ef4444";

const scoreTier = (s = 0) =>
  s >= 7 ? "Top Creator" : s >= 4 ? "Growing Creator" : "Emerging Creator";

/* ───────── Probability Bar ───────── */

const ProbBar = ({ label, pct }) => {
  const colour = riskColour(label);

  return (
    <div style={{ marginBottom: 10 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: "0.82rem",
          marginBottom: 3,
        }}
      >
        <span style={{ color: "var(--text-secondary)" }}>
          {label} Risk
        </span>
        <span style={{ color: colour, fontWeight: 600 }}>
          {pct}%
        </span>
      </div>

      <div
        style={{
          background: "var(--border)",
          borderRadius: 6,
          height: 6,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: colour,
            borderRadius: 6,
            transition: "width .6s ease",
          }}
        />
      </div>
    </div>
  );
};

/* ───────── Error Banner ───────── */

const ErrorBanner = ({ msg }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 8,
      color: "#ef4444",
      margin: "12px 0",
      padding: "10px 14px",
      background: "rgba(239,68,68,.08)",
      borderRadius: 8,
      fontSize: "0.88rem",
    }}
  >
    <RiErrorWarningLine /> {msg}
  </div>
);

/* ───────── Main Component ───────── */

export default function PricePredictor() {

  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const initialUsername = params.get("username") || "";

  const [username, setUsername] = useState(initialUsername);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  /* Auto prediction */

  useEffect(() => {

    if (!initialUsername) return;

    runPrediction(initialUsername);

  }, [initialUsername]);

  const runPrediction = async (user) => {

    if (!user) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {

      const data = await predictAll(user.toLowerCase());

      setResult(data);

    } catch (err) {

      setError(
        err.response?.data?.message ||
        "Prediction failed — username not found."
      );

    } finally {

      setLoading(false);

    }

  };

  const handleSubmit = (e) => {
    e.preventDefault();
    runPrediction(username);
  };

  return (

    <div>

      <h1 className="page-title">AI Price Predictor</h1>

      <p className="page-subtitle">
        ML-powered influencer collaboration pricing
      </p>

      {/* Search */}

      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", gap: 10, marginTop: 20 }}
      >

        <input
          type="text"
          placeholder="Instagram username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            flex: 1,
            padding: "12px 16px",
            borderRadius: 10,
            border: "1px solid var(--border)",
            background: "var(--bg-surface)",
            color: "inherit",
          }}
        />

        <button
          type="submit"
          className="btn-cm"
          disabled={loading}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          {loading ? <RiLoader4Line className="cm-spin" /> : <RiSearchLine />}
          Predict
        </button>

      </form>

      {error && <ErrorBanner msg={error} />}

      {/* Results */}

      {result && (

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))",
            gap: 20,
            marginTop: 30,
          }}
        >

          {/* PRICE */}

          <div className="cm-card">

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <RiMoneyDollarCircleLine color="var(--accent)" />
              <h5>Collaboration Price</h5>
            </div>

            <div style={{ textAlign: "center", marginTop: 10 }}>

              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: 800,
                  color: "var(--accent)",
                }}
              >
                ₹{Number(result.price?.predicted_price).toLocaleString("en-IN")}
              </div>

              <p style={{ color: "var(--text-secondary)" }}>
                Range: {result.price?.price_band}
              </p>

            </div>

          </div>


          {/* CREATOR SCORE */}

          <div className="cm-card">

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <RiStarLine color="#00d4aa" />
              <h5>Creator Score</h5>
            </div>

            <div
              style={{
                fontSize: "2rem",
                fontWeight: 700,
                textAlign: "center",
                marginTop: 10,
                color: scoreColour(result.score?.creator_score),
              }}
            >
              {result.score?.creator_score?.toFixed(2)}
            </div>

            <p style={{ textAlign: "center", color: "var(--text-secondary)" }}>
              {scoreTier(result.score?.creator_score)}
            </p>

          </div>


          {/* BRAND RISK */}

          <div className="cm-card">

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <RiShieldLine color={riskColour(result.risk?.risk_label)} />
              <h5>Brand Risk</h5>
            </div>

            <div
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                textAlign: "center",
                marginBottom: 16,
                color: riskColour(result.risk?.risk_label),
              }}
            >
              {result.risk?.risk_label}
            </div>

            {/* Restore High / Medium / Low probabilities */}

            {result.risk?.probabilities &&
              Object.entries(result.risk.probabilities).map(([k, v]) => (
                <ProbBar key={k} label={k} pct={Math.round(v * 100)} />
              ))}

          </div>

        </div>

      )}

      <style>{`
        .cm-spin { animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

    </div>

  );
}