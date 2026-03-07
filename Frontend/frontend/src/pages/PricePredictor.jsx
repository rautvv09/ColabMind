import React, { useState } from "react";
import {
  predictAll
  // predictCreatorScoreFromFeatures,
} from "../services/api";
import {
  RiMoneyDollarCircleLine,
  RiStarLine,
  RiShieldLine,
  RiSearchLine,
  RiLoader4Line,
  RiErrorWarningLine,
  RiSparklingLine,
} from "react-icons/ri";
import "./PricePredictor.css";

/* ─── Colour helpers ─────────────────────────────────────── */
const riskColour = (label = "") => {
  const l = label.toLowerCase();
  if (l.includes("low"))    return "#00d4aa";
  if (l.includes("medium")) return "#f59e0b";
  if (l.includes("high"))   return "#ef4444";
  return "var(--text-secondary)";
};

const scoreColour = (s = 0) =>
  s >= 7 ? "#00d4aa" : s >= 4 ? "#f59e0b" : "#ef4444";

const scoreTier = (s = 0) =>
  s >= 7 ? "Top Creator" : s >= 4 ? "Growing Creator" : "Emerging Creator";

/* ─── Shared UI primitives ───────────────────────────────── */
const MetaRow = ({ label, value, accent }) => (
  <div style={{
    display: "flex", justifyContent: "space-between",
    padding: "9px 0", borderBottom: "1px solid var(--border)",
  }}>
    <span style={{ color: "var(--text-secondary)", fontSize: "0.87rem" }}>{label}</span>
    <strong style={accent ? { color: accent } : {}}>{value ?? "—"}</strong>
  </div>
);

const ProbBar = ({ label, pct }) => {
  const colour = riskColour(label);
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", marginBottom: 3 }}>
        <span style={{ color: "var(--text-secondary)" }}>{label} Risk</span>
        <span style={{ color: colour, fontWeight: 600 }}>{pct}%</span>
      </div>
      <div style={{ background: "var(--border)", borderRadius: 6, height: 6, overflow: "hidden" }}>
        <div style={{
          width: `${pct}%`, height: "100%", background: colour,
          borderRadius: 6, transition: "width .6s ease",
        }} />
      </div>
    </div>
  );
};

/* SVG circular score ring */
const ScoreRing = ({ score = 0 }) => {
  const r      = 40;
  const circ   = 2 * Math.PI * r;
  const pct    = Math.round((Math.min(10, Math.max(0, score)) / 10) * 100);
  const colour = scoreColour(score);
  return (
    <div style={{ display: "flex", justifyContent: "center", margin: "14px 0" }}>
      <svg width={100} height={100} viewBox="0 0 100 100">
        <circle cx={50} cy={50} r={r} fill="none" stroke="var(--border)" strokeWidth={8} />
        <circle
          cx={50} cy={50} r={r} fill="none"
          stroke={colour} strokeWidth={8}
          strokeDasharray={circ}
          strokeDashoffset={circ - (pct / 100) * circ}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset .8s ease" }}
        />
        <text x={50} y={50} textAnchor="middle" dominantBaseline="central"
          style={{ fill: colour, fontSize: 18, fontWeight: 700 }}>
          {Number(score).toFixed(1)}
        </text>
      </svg>
    </div>
  );
};

const ErrorBanner = ({ msg }) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 8,
    color: "#ef4444", margin: "12px 0",
    padding: "10px 14px", background: "rgba(239,68,68,.08)",
    borderRadius: 8, fontSize: "0.88rem",
  }}>
    <RiErrorWarningLine /> {msg}
  </div>
);

const LoadingBanner = ({ stage }) => (
  <div className="cm-loading-banner">
    <div className="cm-spinner" style={{ width: 16, height: 16, margin: 0, flexShrink: 0, borderWidth: 2, borderTopColor: "var(--accent)" }} />
    <span>
      {stage === "scraping"
        ? "New profile detected — scraping Instagram data, this may take a moment…"
        : "Running ML models…"
      }
    </span>
  </div>
);

/* ─── Tab 1 — Lookup by username ─────────────────────────── */
function UsernameTab() {
  const [username,     setUsername]     = useState("");
  const [result,       setResult]       = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [loadingStage, setLoadingStage] = useState("idle");
  const [error,        setError]        = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) return;

    setLoading(true);
    setLoadingStage("predicting");
    setError("");
    setResult(null);

    try {
      const data = await predictAll(username.trim().toLowerCase());

      if (data.scraped_fresh) setLoadingStage("scraping");

      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.message ||
        "Prediction failed — check that the username exists or the SearchAPI key is set."
      );
    } finally {
      setLoading(false);
      setLoadingStage("idle");
    }
  };

  return (
    <>
      {/* Search bar */}
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 10, marginBottom: 8 }}>
        <input
          type="text"
          placeholder="Instagram username  e.g. leomessi"
          value={username}
          onChange={e => setUsername(e.target.value)}
          disabled={loading}
          style={{
            flex: 1, padding: "12px 16px", borderRadius: 10,
            border: "1px solid var(--border)",
            background: "var(--bg-surface)", color: "inherit",
            fontSize: "0.95rem", outline: "none",
          }}
          onFocus={e => e.target.style.borderColor = "var(--accent)"}
          onBlur={e  => e.target.style.borderColor = "var(--border)"}
        />
        <button
          type="submit"
          className="btn-cm"
          disabled={loading}
          style={{ display: "flex", alignItems: "center", gap: 6, padding: "12px 24px", opacity: loading ? 0.6 : 1 }}
        >
          {loading ? <RiLoader4Line className="cm-spin" /> : <RiSearchLine />}
          {loading ? "Working…" : "Predict"}
        </button>
      </form>

      {loading && <LoadingBanner stage={loadingStage} />}
      {error   && <ErrorBanner msg={error} />}

      {/* Results — 3-column grid */}
      {result && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 20, marginTop: 24,
        }}>

          {/* ── Price card ── */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <RiMoneyDollarCircleLine size={20} color="var(--accent)" />
              <h5 style={{ margin: 0 }}>Collaboration Price</h5>
            </div>

            {result.scraped_fresh && (
              <div style={{
                display: "inline-flex", alignItems: "center", gap: 5,
                fontSize: "0.68rem", fontWeight: 600, letterSpacing: "0.08em",
                textTransform: "uppercase", padding: "3px 10px", borderRadius: 20,
                background: "rgba(0,212,170,0.10)", border: "1px solid rgba(0,212,170,0.22)",
                color: "#00d4aa", marginBottom: 12,
              }}>
                <RiSparklingLine /> Freshly scraped
              </div>
            )}

            <div style={{ textAlign: "center", padding: "6px 0 14px" }}>
              <div style={{ fontSize: "2.2rem", fontWeight: 800, color: "var(--accent)" }}>
                ₹{Number(result.price?.predicted_price).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </div>
              <div style={{ color: "var(--text-secondary)", marginTop: 4, fontSize: "0.88rem" }}>
                Range: {result.price?.price_band}
              </div>
            </div>

            <MetaRow label="Followers"
              value={Number(result.price?.features_used?.followers ?? 0).toLocaleString("en-IN")} />
            <MetaRow label="Avg Likes"
              value={Number(result.price?.features_used?.avg_likes ?? 0).toLocaleString("en-IN")} />
            <MetaRow label="Avg Comments"
              value={Number(result.price?.features_used?.avg_comments ?? 0).toLocaleString("en-IN")} />
            <MetaRow label="Engagement Rate"
              value={`${((result.price?.features_used?.engagement_rate ?? 0) * 100).toFixed(2)}%`} />
            <MetaRow label="Creator Score used"
              value={(result.price?.creator_score ?? 0).toFixed(2)}
              accent="var(--accent-2)" />
          </div>

          {/* ── Creator Score card ── */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <RiStarLine size={20} color="#00d4aa" />
              <h5 style={{ margin: 0 }}>Creator Score</h5>
            </div>

            <ScoreRing score={result.score?.creator_score ?? result.price?.creator_score ?? 0} />

            <div style={{ textAlign: "center", marginBottom: 12 }}>
              {(() => {
                const s = result.score?.creator_score ?? result.price?.creator_score ?? 0;
                return (
                  <span style={{
                    padding: "4px 14px", borderRadius: 20,
                    fontSize: "0.82rem", fontWeight: 600,
                    background: `${scoreColour(s)}20`, color: scoreColour(s),
                  }}>
                    {scoreTier(s)}
                  </span>
                );
              })()}
            </div>

            <MetaRow label="Score (out of 10)"
              value={(result.score?.creator_score ?? result.price?.creator_score ?? 0).toFixed(4)}
              accent={scoreColour(result.score?.creator_score ?? result.price?.creator_score ?? 0)} />
          </div>

          {/* ── Risk card ── */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <RiShieldLine size={20} color={riskColour(result.risk?.risk_label)} />
              <h5 style={{ margin: 0 }}>Brand Risk</h5>
            </div>

            <div style={{ textAlign: "center", padding: "6px 0 14px" }}>
              <div style={{ fontSize: "1.9rem", fontWeight: 800, color: riskColour(result.risk?.risk_label) }}>
                {result.risk?.risk_label}
              </div>
              <div style={{ color: "var(--text-secondary)", marginTop: 4, fontSize: "0.88rem" }}>
                P(High Risk): {((result.risk?.risk_score ?? 0) * 100).toFixed(1)}%
              </div>
            </div>

            {result.risk?.probabilities
              ? Object.entries(result.risk.probabilities).map(([k, v]) => (
                  <ProbBar key={k} label={k} pct={Math.round(v * 100)} />
                ))
              : result.risk && (() => {
                  const score = result.risk.risk_score ?? 0;
                  const label = result.risk.risk_label ?? "";
                  const main  = Math.round(score * 100);
                  const rest  = 100 - main;
                  const bars  = label === "High"
                    ? [["High", main], ["Medium", Math.round(rest * 0.6)], ["Low", Math.round(rest * 0.4)]]
                    : label === "Low"
                    ? [["Low",  main], ["Medium", Math.round(rest * 0.6)], ["High", Math.round(rest * 0.4)]]
                    : [["Medium", main], ["High", Math.round(rest * 0.4)], ["Low", Math.round(rest * 0.6)]];
                  return bars.map(([k, v]) => <ProbBar key={k} label={k} pct={v} />);
                })()
            }
          </div>

        </div>
      )}
    </>
  );
}

/* ─── Tab 2 — Manual feature input ──────────────────────── */
// const FIELDS = [
//   { key: "followers",          label: "Followers",            ph: "50000" },
//   { key: "following",          label: "Following",            ph: "400"   },
//   { key: "posts",              label: "Total Posts",          ph: "200"   },
//   { key: "engagement_percent", label: "Engagement % (0-100)", ph: "3.5"   },
//   { key: "avg_likes",          label: "Avg Likes / Post",     ph: "1800"  },
//   { key: "avg_comments",       label: "Avg Comments / Post",  ph: "90"    },
//   { key: "posting_frequency",  label: "Posts / Week",         ph: "4"     },
//   { key: "video_ratio",        label: "Video Ratio (0–1)",    ph: "0.4"   },
//   { key: "image_ratio",        label: "Image Ratio (0–1)",    ph: "0.6"   },
// ];

// function ManualTab() {
//   const init = Object.fromEntries(FIELDS.map(f => [f.key, ""]));
//   const [form,    setForm]    = useState(init);
//   const [result,  setResult]  = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [error,   setError]   = useState("");

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setLoading(true);
//     setError("");

//     const payload = Object.fromEntries(
//       Object.entries(form).map(([k, v]) => [k, parseFloat(v) || 0])
//     );

//     try {
//       const res = await predictCreatorScoreFromFeatures(payload);
//       setResult(res.data.data);
//     } catch (err) {
//       setError(err.response?.data?.message || "Prediction failed. Check your inputs.");
//     } finally { setLoading(false); }
//   };

//   return (
//     <>
//       <form onSubmit={handleSubmit} style={{
//         display: "grid",
//         gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
//         gap: 14,
//       }}>
//         {FIELDS.map(f => (
//           <div key={f.key}>
//             <label style={{ display: "block", fontSize: "0.80rem", color: "var(--text-secondary)", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.06em" }}>
//               {f.label}
//             </label>
//             <input
//               type="number" step="any" placeholder={f.ph}
//               value={form[f.key]}
//               onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
//               style={{
//                 width: "100%", padding: "10px 12px", borderRadius: 8,
//                 border: "1px solid var(--border)",
//                 background: "var(--bg-surface)", color: "inherit",
//                 fontSize: "0.9rem", boxSizing: "border-box", outline: "none",
//               }}
//               onFocus={e => e.target.style.borderColor = "var(--accent)"}
//               onBlur={e  => e.target.style.borderColor = "var(--border)"}
//             />
//           </div>
//         ))}

//         <div style={{ gridColumn: "1/-1", marginTop: 4 }}>
//           <button type="submit" className="btn-cm" disabled={loading}
//             style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 24px", opacity: loading ? 0.6 : 1 }}>
//             {loading ? <RiLoader4Line className="cm-spin" /> : <RiStarLine />}
//             {loading ? "Running models…" : "Run ML Models"}
//           </button>
//         </div>
//       </form>

//       {error && <ErrorBanner msg={error} />}

//       {result && (
//         <div style={{
//           display: "grid",
//           gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
//           gap: 20, marginTop: 24,
//         }}>
//           <div className="cm-card" style={{ textAlign: "center" }}>
//             <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 4 }}>
//               <RiStarLine color="#00d4aa" />
//               <h5 style={{ margin: 0 }}>Creator Score</h5>
//             </div>
//             <ScoreRing score={result.creator_score ?? 0} />
//             <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>out of 10</div>
//             <div style={{ marginTop: 10 }}>
//               <span style={{
//                 padding: "4px 14px", borderRadius: 20, fontSize: "0.82rem", fontWeight: 600,
//                 background: `${scoreColour(result.creator_score)}20`,
//                 color: scoreColour(result.creator_score),
//               }}>
//                 {scoreTier(result.creator_score)}
//               </span>
//             </div>
//           </div>

//           <div className="cm-card">
//             <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
//               <RiShieldLine color={riskColour(result.risk_label)} />
//               <h5 style={{ margin: 0 }}>Brand Risk</h5>
//             </div>
//             <div style={{ textAlign: "center", marginBottom: 14 }}>
//               <div style={{ fontSize: "1.8rem", fontWeight: 800, color: riskColour(result.risk_label) }}>
//                 {result.risk_label}
//               </div>
//               <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: 4 }}>
//                 P(High Risk): {((result.risk_score ?? 0) * 100).toFixed(1)}%
//               </div>
//             </div>
//             {result.probabilities &&
//               Object.entries(result.probabilities).map(([k, v]) => (
//                 <ProbBar key={k} label={k} pct={Math.round(v * 100)} />
//               ))
//             }
//           </div>
//         </div>
//       )}
//     </>
//   );
// }

/* ─── Page shell ─────────────────────────────────────────── */
export default function PricePredictor() {
  const [tab, setTab] = useState("username");

  return (
    <div>
      <h1 className="page-title">AI Prediction Suite</h1>
      <p className="page-subtitle">
        ML-powered pricing · creator scoring · brand risk analysis
      </p>

      {/* Tab bar */}
      {/* <div style={{
        display: "flex", gap: 4, marginTop: 20, marginBottom: 28,
        background: "var(--bg-surface)", borderRadius: 10, padding: 4,
        width: "fit-content",
      }}>
        {[
          { id: "username", label: "Lookup by Username" },
          { id: "manual",   label: "Manual Input"       },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{
            padding: "8px 18px", borderRadius: 8, border: "none",
            cursor: "pointer", fontWeight: 600, fontSize: "0.88rem",
            background: tab === t.id ? "var(--accent)" : "transparent",
            color:      tab === t.id ? "#fff"          : "var(--text-secondary)",
            transition: "all .2s",
          }}>
            {t.label}
          </button>
        ))}
      </div> */}

      {tab === "username" ? <UsernameTab /> : <ManualTab />}

      <style>{`
        .cm-spin { animation: _spin .8s linear infinite; display: inline-block; }
        @keyframes _spin { to { transform: rotate(360deg); } }
        .cm-loading-banner {
          display: flex; align-items: center; gap: 12px;
          margin: 0 0 16px; padding: 11px 16px;
          background: rgba(108,99,255,0.07);
          border: 1px solid rgba(108,99,255,0.18);
          border-radius: 10px; font-size: 0.83rem;
          color: rgba(160,150,255,0.90);
        }
        .page-title {
          font-family: 'Syne', sans-serif; font-weight: 800;
          font-size: clamp(1.8rem, 3.5vw, 2.4rem);
          color: var(--text-primary); letter-spacing: -0.02em; margin-bottom: 6px;
        }
        .page-subtitle {
          font-size: 0.84rem; color: var(--text-secondary); margin-bottom: 4px;
        }
      `}</style>
    </div>
  );
}