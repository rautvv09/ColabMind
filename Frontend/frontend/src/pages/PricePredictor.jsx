import React, { useState } from "react";
import { predictPrice, predictRisk } from "../services/api";
import { RiShieldLine } from "react-icons/ri";

const PricePredictor = () => {

  const [username, setUsername] = useState("");
  const [priceResult, setPriceResult] = useState(null);
  const [riskResult, setRiskResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handlePredict = async (e) => {
    e.preventDefault();

    if (!username.trim()) {
      setError("Please enter an Instagram username");
      return;
    }

    setLoading(true);
    setError("");

    try {

      // Call backend APIs
      const priceResponse = await predictPrice({
        username: username.trim()
      });

      const riskResponse = await predictRisk({
        username: username.trim()
      });

      // Set results — unwrap axios .data then Flask's nested .data
      setPriceResult(priceResponse.data.data);
      setRiskResult(riskResponse.data.data);

    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.response?.data?.error ||
        "Prediction failed. Please try again."
      );
    }

    setLoading(false);
  };

  return (
    <div>

      <h1 className="page-title">AI Price Predictor</h1>
      <p className="page-subtitle">ML-powered collaboration pricing</p>

      {/* Input Form */}

      <form onSubmit={handlePredict} style={{ marginTop: 20 }}>

        <input
          type="text"
          placeholder="Enter Instagram username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            padding: 10,
            width: 250,
            marginRight: 10
          }}
        />

        <button type="submit">
          Predict
        </button>

      </form>

      {loading && <p>Predicting...</p>}

      {error && (
        <p style={{ color: "red" }}>
          {error}
        </p>
      )}

      {/* Results */}

      {priceResult && (

        <div style={{ marginTop: 30 }}>

          <div className="cm-card">

            <h3>Recommended Price</h3>

            <h1>
              ₹{Number(priceResult.predicted_price).toLocaleString()}
            </h1>

            <p>
              Range: {priceResult.price_band}
            </p>

          </div>

          {riskResult && (

            <div className="cm-card" style={{ marginTop: 20 }}>

              <h3>
                <RiShieldLine /> Brand Risk
              </h3>

              <h2>{riskResult.risk_label}</h2>

              <p>
                Risk Score: {(riskResult.risk_score * 100).toFixed(0)}%
              </p>

            </div>

          )}

        </div>

      )}

    </div>
  );
};

export default PricePredictor;