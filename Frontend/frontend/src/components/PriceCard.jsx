import React from "react";
import { RiSparklingLine, RiShieldCheckLine, RiInformationLine } from "react-icons/ri";

const TIER_CONFIG = {
  nano:   { label: "Nano",   color: "#7a82a0", range: "1K–10K followers" },
  micro:  { label: "Micro",  color: "#00d4aa", range: "10K–100K followers" },
  mid:    { label: "Mid",    color: "#6c63ff", range: "100K–1M followers" },
  macro:  { label: "Macro",  color: "#ffc107", range: "1M–10M followers" },
  mega:   { label: "Mega",   color: "#ff6b6b", range: "10M+ followers" },
};

export default function PriceCard({ result, creatorName = "" }) {
  if (!result) return null;

  const {
    recommended_price = 0,
    min_price         = 0,
    max_price         = 0,
    confidence_score  = 0,
    tier              = "micro",
    note              = "",
    features_used     = {},
  } = result;

  const tierConf   = TIER_CONFIG[tier] || TIER_CONFIG.micro;
  const confidence = Math.round(confidence_score * 100);

  // Confidence bar color
  const confColor = confidence >= 80 ? "#00d4aa" : confidence >= 60 ? "#ffc107" : "#ff6b6b";

  return (
    <div className="cm-card" style={{ position: "relative", overflow: "hidden" }}>

      {/* Glow */}
      <div style={{
        position: "absolute", top: -60, right: -60,
        width: 220, height: 220, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%)",
        pointerEvents: "none"
      }} />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <RiSparklingLine color="var(--accent)" size={18} />
            <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "1px" }}>
              AI Price Estimate
            </span>
          </div>
          {creatorName && (
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>for @{creatorName}</div>
          )}
        </div>

        {/* Tier badge */}
        <span style={{
          background: `${tierConf.color}20`,
          color: tierConf.color,
          border: `1px solid ${tierConf.color}40`,
          padding: "4px 12px", borderRadius: 20,
          fontSize: "0.75rem", fontWeight: 700, letterSpacing: "0.5px"
        }}>
          {tierConf.label}
        </span>
      </div>

      {/* Main price */}
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <div style={{
          fontFamily: "'Syne', sans-serif", fontWeight: 800,
          fontSize: "3.2rem", lineHeight: 1,
          background: "var(--gradient)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          marginBottom: 4
        }}>
          ₹{Number(recommended_price).toLocaleString()}
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
          Recommended per collaboration
        </div>
      </div>

      {/* Min / Max range */}
      <div style={{
        display: "flex", justifyContent: "space-between",
        background: "var(--bg-dark)", borderRadius: 10, padding: "12px 16px",
        marginBottom: 20
      }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>
            Min
          </div>
          <div style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700, color: "#7a82a0" }}>
            ₹{Number(min_price).toLocaleString()}
          </div>
        </div>

        {/* Range bar */}
        <div style={{ flex: 1, display: "flex", alignItems: "center", margin: "0 16px" }}>
          <div style={{ width: "100%", height: 4, background: "var(--border)", borderRadius: 2, position: "relative" }}>
            <div style={{
              position: "absolute", left: 0, right: 0, top: 0, bottom: 0,
              background: "var(--gradient)", borderRadius: 2
            }} />
            {/* Recommended marker */}
            {max_price > min_price && (
              <div style={{
                position: "absolute", top: "50%", transform: "translate(-50%, -50%)",
                left: `${((recommended_price - min_price) / (max_price - min_price)) * 100}%`,
                width: 12, height: 12, borderRadius: "50%",
                background: "white", border: "2px solid var(--accent)",
                boxShadow: "0 0 8px rgba(108,99,255,0.6)"
              }} />
            )}
          </div>
        </div>

        <div style={{ textAlign: "center" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>
            Max
          </div>
          <div style={{ fontFamily: "'Syne',sans-serif", fontWeight: 700, color: "var(--accent2)" }}>
            ₹{Number(max_price).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Confidence */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            <RiShieldCheckLine /> Model Confidence
          </span>
          <span style={{ color: confColor, fontWeight: 700, fontSize: "0.85rem" }}>{confidence}%</span>
        </div>
        <div style={{ height: 6, background: "var(--bg-dark)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            height: "100%", borderRadius: 3, width: `${confidence}%`,
            background: `linear-gradient(90deg, ${confColor}88, ${confColor})`,
            transition: "width 0.8s ease"
          }} />
        </div>
      </div>

      {/* Features used */}
      {Object.keys(features_used).length > 0 && (
        <div style={{
          background: "var(--bg-dark)", borderRadius: 10, padding: 14, marginBottom: 16
        }}>
          <div style={{
            color: "var(--text-muted)", fontSize: "0.7rem", textTransform: "uppercase",
            letterSpacing: "0.5px", marginBottom: 10
          }}>
            <RiInformationLine /> Inputs Used
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {Object.entries(features_used).map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                  {k.replace(/_/g, " ")}
                </span>
                <span style={{ fontWeight: 600, fontSize: "0.78rem" }}>
                  {typeof v === "number" ? v.toLocaleString() : String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Note */}
      {note && (
        <div style={{
          padding: "10px 14px", borderRadius: 8,
          background: "rgba(108,99,255,0.08)", borderLeft: "3px solid var(--accent)",
          fontSize: "0.82rem", color: "var(--text-muted)", fontStyle: "italic"
        }}>
          {note}
        </div>
      )}
    </div>
  );
}
