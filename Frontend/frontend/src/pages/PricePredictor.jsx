import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { predictPrice, predictRisk, getCreatorByUsername } from "../services/api";
import { RiSparklingLine, RiSearchLine, RiShieldLine } from "react-icons/ri";

export default function PricePredictor() {

  const [searchParams] = useSearchParams();
  const creatorId = searchParams.get("id");

  const [username, setUsername] = useState("");
  const [priceResult, setPriceResult] = useState(null);
  const [riskResult, setRiskResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    followers: "",
    avg_likes: "",
    avg_comments: "",
    avg_reel_views: "",
    niche: "fashion",
    avg_deal_value: "",
  });

  const niches = [
    "fashion","beauty","fitness","tech","food","travel",
    "lifestyle","gaming","education","finance","other"
  ];

  /* --------------------------------------------------
     AUTO PREDICT WHEN OPENED FROM CREATOR PAGE
  -------------------------------------------------- */

  useEffect(() => {

    if (!creatorId) return;

    const autoPredict = async () => {

      setLoading(true);

      try {

        const [priceRes, riskRes] = await Promise.all([
          predictPrice({ creator_id: creatorId }),
          predictRisk({
            avg_payment_delay_days: 0,
            late_payment_count: 0,
            total_deals: 0,
            deal_completion_rate: 1.0,
          }),
        ]);

        setPriceResult(priceRes.data.data);
        setRiskResult(riskRes.data.data);

      } catch {
        setError("Automatic prediction failed.");
      }

      setLoading(false);
    };

    autoPredict();

  }, [creatorId]);


  /* --------------------------------------------------
     USERNAME PREDICTION
  -------------------------------------------------- */

  const handleUsernamePredict = async (e) => {

    e.preventDefault();
    if (!username.trim()) return;

    setLoading(true);
    setError("");

    try {

      const creatorRes = await getCreatorByUsername(username.trim());
      const creator = creatorRes.data.data;

      const [priceRes, riskRes] = await Promise.all([
        predictPrice({ creator_id: creator._id }),
        predictRisk({
          avg_payment_delay_days: 0,
          late_payment_count: 0,
          total_deals: creator.total_collaborations || 0,
          deal_completion_rate: 1.0,
        }),
      ]);

      setPriceResult(priceRes.data.data);
      setRiskResult(riskRes.data.data);

    } catch (err) {

      setError(
        err.response?.data?.message ||
        "Prediction failed. Check username."
      );

    }

    setLoading(false);
  };


  /* --------------------------------------------------
     MANUAL INPUT
  -------------------------------------------------- */

  const handleManualPredict = async (e) => {

    e.preventDefault();
    setLoading(true);
    setError("");

    try {

      const res = await predictPrice({
        followers: parseFloat(form.followers),
        avg_likes: parseFloat(form.avg_likes),
        avg_comments: parseFloat(form.avg_comments),
        avg_reel_views: parseFloat(form.avg_reel_views),
        niche: form.niche,
        avg_deal_value: parseFloat(form.avg_deal_value),
      });

      setPriceResult(res.data.data);

    } catch {

      setError("Prediction failed. Fill all fields.");

    }

    setLoading(false);
  };


  return (
    <div>

      <h1 className="page-title">AI Price Predictor</h1>
      <p className="page-subtitle">
        ML-powered collaboration pricing for Instagram creators
      </p>

      {loading && <div className="cm-spinner" />}

      {/* RESULTS */}

      {priceResult && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: riskResult ? "1fr 1fr" : "1fr",
            gap: 20,
            marginTop: 28,
          }}
        >

          {/* PRICE CARD */}

          <div className="cm-card" style={{ textAlign: "center" }}>

            <div style={{
              color: "var(--text-muted)",
              marginBottom: 8,
              fontSize: "0.85rem",
              textTransform: "uppercase",
              letterSpacing: 1,
            }}>
              Recommended Price
            </div>

            <div style={{
              fontFamily: "'Syne',sans-serif",
              fontWeight: 800,
              fontSize: "3rem",
              background: "var(--gradient)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}>
              ₹{Number(priceResult.recommended_price).toLocaleString()}
            </div>

            <div style={{ color: "var(--text-muted)", marginTop: 8 }}>
              Confidence: {((priceResult.confidence_score || 0) * 100).toFixed(0)}%
            </div>

          </div>

          {/* RISK CARD */}

          {riskResult && (
            <div className="cm-card" style={{ textAlign: "center" }}>

              <div style={{
                color: "var(--text-muted)",
                marginBottom: 8,
                fontSize: "0.85rem",
                textTransform: "uppercase",
                letterSpacing: 1,
              }}>
                <RiShieldLine /> Brand Risk
              </div>

              <div style={{
                fontFamily: "'Syne',sans-serif",
                fontWeight: 800,
                fontSize: "2.5rem",
                color:
                  riskResult.risk_label === "Low"
                    ? "#00d4aa"
                    : riskResult.risk_label === "Medium"
                    ? "#ffc107"
                    : "#ff6b6b",
              }}>
                {riskResult.risk_label}
              </div>

              <div style={{ color: "var(--text-muted)", marginTop: 8 }}>
                Risk Score: {(riskResult.risk_score * 100).toFixed(0)}%
              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
}