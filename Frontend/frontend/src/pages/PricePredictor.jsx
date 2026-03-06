import React, { useState } from "react";
import {
  predictAll,
  predictCreatorScoreFromFeatures,
} from "../services/api";
import {
  RiMoneyDollarCircleLine,
  RiStarLine,
  RiShieldLine,
  RiSearchLine,
  RiLoader4Line,
  RiErrorWarningLine,
} from "react-icons/ri";

/* ─────────────────────────────────────────────────────────────────────────────
   Colour helpers
───────────────────────────────────────────────────────────────────────────── */
const riskColour = (label = "") => {
  const l = label.toLowerCase();
  if (l.includes("low"))    return "#00d4aa";
  if (l.includes("medium")) return "#f59e0b";
  if (l.includes("high"))   return "#ef4444";
  return "var(--text-muted)";
};

const scoreColour = (s = 0) =>
  s >= 7 ? "#00d4aa" : s >= 4 ? "#f59e0b" : "#ef4444";

const scoreTier = (s = 0) =>
  s >= 7 ? "Top Creator" : s >= 4 ? "Growing Creator" : "Emerging Creator";

/* ─────────────────────────────────────────────────────────────────────────────
   Shared UI primitives
───────────────────────────────────────────────────────────────────────────── */
const MetaRow = ({ label, value, accent }) => (
  <div style={{
    display: "flex", justifyContent: "space-between",
    padding: "9px 0", borderBottom: "1px solid var(--border)",
  }}>
    <span style={{ color: "var(--text-muted)", fontSize: "0.87rem" }}>{label}</span>
    <strong style={accent ? { color: accent } : {}}>{value ?? "—"}</strong>
  </div>
);

const ProbBar = ({ label, pct }) => {
  const colour = riskColour(label);
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", marginBottom: 3 }}>
        <span>{label}</span>
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

/* Circular score ring using SVG */
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
          {score.toFixed(1)}
        </text>
      </svg>
    </div>
  );
};

const ErrorBanner = ({ msg }) => (
  <div style={{
    display: "flex", alignItems: "center", gap: 8,
    color: "#ef4444", margin: "12px 0",
    padding: "10px 14px", background: "rgba(239,68,68,.08)", borderRadius: 8,
  }}>
    <RiErrorWarningLine /> {msg}
  </div>
);

/* ─────────────────────────────────────────────────────────────────────────────
   Tab 1 – Lookup by username (runs all 3 models in parallel)
───────────────────────────────────────────────────────────────────────────── */
function UsernameTab() {
  const [username, setUsername] = useState("");
  const [result,   setResult]   = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) { setError("Please enter a username"); return; }

    setLoading(true); setError(""); setResult(null);
    try {
      setResult(await predictAll(username.trim().toLowerCase()));
    } catch (err) {
      setError(
        err.response?.data?.message ||
        "Prediction failed — check that the username exists in the database."
      );
    } finally { setLoading(false); }
  };

  return (
    <>
      {/* Search bar */}
      <form onSubmit={handleSubmit}
        style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <input
          type="text"
          placeholder="Instagram username  e.g. leomessi"
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{
            flex: 1, padding: "10px 14px", borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--surface)", color: "inherit", fontSize: "0.95rem",
          }}
        />
        <button type="submit" className="btn-cm" disabled={loading}
          style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 20px" }}>
          {loading ? <RiLoader4Line className="cm-spin" /> : <RiSearchLine />}
          {loading ? "Running models…" : "Predict"}
        </button>
      </form>

      {error && <ErrorBanner msg={error} />}

      {/* Results – 3-column grid */}
      {result && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 20,
        }}>

          {/* ── Price card ────────────────────────────────────────── */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <RiMoneyDollarCircleLine size={20} color="var(--accent)" />
              <h5 style={{ margin: 0 }}>Collaboration Price</h5>
            </div>

            <div style={{ textAlign: "center", padding: "6px 0 14px" }}>
              <div style={{ fontSize: "2.2rem", fontWeight: 800, color: "var(--accent)" }}>
                ₹{Number(result.price?.predicted_price).toLocaleString()}
              </div>
              <div style={{ color: "var(--text-muted)", marginTop: 4, fontSize: "0.88rem" }}>
                Range: {result.price?.price_band}
              </div>
            </div>

            <MetaRow label="Followers"
              value={Number(result.price?.features_used?.followers).toLocaleString()} />
            <MetaRow label="Avg Likes"
              value={Number(result.price?.features_used?.avg_likes).toLocaleString()} />
            <MetaRow label="Avg Comments"
              value={Number(result.price?.features_used?.avg_comments).toLocaleString()} />
            <MetaRow label="Engagement Rate"
              value={`${((result.price?.features_used?.engagement_rate || 0) * 100).toFixed(2)}%`} />
            <MetaRow label="Creator Score used"
              value={(result.price?.creator_score ?? 0).toFixed(2)}
              accent="var(--accent2)" />
          </div>

          {/* ── Creator Score card ───────────────────────────────── */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <RiStarLine size={20} color="var(--accent2)" />
              <h5 style={{ margin: 0 }}>Creator Score</h5>
            </div>

            <ScoreRing score={result.score?.creator_score ?? 0} />

            <div style={{ textAlign: "center", marginBottom: 12 }}>
              <span style={{
                padding: "4px 14px", borderRadius: 20,
                fontSize: "0.82rem", fontWeight: 600,
                background: `${scoreColour(result.score?.creator_score)}20`,
                color: scoreColour(result.score?.creator_score),
              }}>
                {scoreTier(result.score?.creator_score)}
              </span>
            </div>

            <MetaRow label="Score (out of 10)"
              value={(result.score?.creator_score ?? 0).toFixed(4)}
              accent={scoreColour(result.score?.creator_score)} />
          </div>

          {/* ── Risk card ────────────────────────────────────────── */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <RiShieldLine size={20} color={riskColour(result.risk?.risk_label)} />
              <h5 style={{ margin: 0 }}>Brand Risk</h5>
            </div>

            <div style={{ textAlign: "center", padding: "6px 0 14px" }}>
              <div style={{
                fontSize: "1.9rem", fontWeight: 800,
                color: riskColour(result.risk?.risk_label),
              }}>
                {result.risk?.risk_label}
              </div>
              <div style={{ color: "var(--text-muted)", marginTop: 4, fontSize: "0.88rem" }}>
                P(High Risk): {((result.risk?.risk_score ?? 0) * 100).toFixed(1)}%
              </div>
            </div>

            {result.risk?.probabilities &&
              Object.entries(result.risk.probabilities).map(([k, v]) => (
                <ProbBar key={k} label={k} pct={Math.round(v * 100)} />
              ))
            }
          </div>

        </div>
      )}
    </>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Tab 2 – Manual feature input  (no DB needed)
───────────────────────────────────────────────────────────────────────────── */
const FIELDS = [
  { key: "followers",          label: "Followers",           ph: "50000"  },
  { key: "following",          label: "Following",           ph: "400"    },
  { key: "posts",              label: "Total Posts",         ph: "200"    },
  { key: "engagement_percent", label: "Engagement % (0-100)",ph: "3.5"    },
  { key: "avg_likes",          label: "Avg Likes / Post",    ph: "1800"   },
  { key: "avg_comments",       label: "Avg Comments / Post", ph: "90"     },
  { key: "posting_frequency",  label: "Posts / Week",        ph: "4"      },
  { key: "video_ratio",        label: "Video Ratio (0-1)",   ph: "0.4"    },
  { key: "image_ratio",        label: "Image Ratio (0-1)",   ph: "0.6"    },
];

function ManualTab() {
  const init = Object.fromEntries(FIELDS.map(f => [f.key, ""]));
  const [form,    setForm]    = useState(init);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(""); setResult(null);

    const payload = Object.fromEntries(
      Object.entries(form).map(([k, v]) => [k, parseFloat(v) || 0])
    );

    try {
      const res = await predictCreatorScoreFromFeatures(payload);
      setResult(res.data.data);
    } catch (err) {
      setError(err.response?.data?.message || "Prediction failed. Check your inputs.");
    } finally { setLoading(false); }
  };

  return (
    <>
      <form onSubmit={handleSubmit} style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: 14,
      }}>
        {FIELDS.map(f => (
          <div key={f.key}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: 4 }}>
              {f.label}
            </label>
            <input
              type="number" step="any" placeholder={f.ph}
              value={form[f.key]}
              onChange={e => setForm(p => ({ ...p, [f.key]: e.target.value }))}
              style={{
                width: "100%", padding: "9px 12px", borderRadius: 7,
                border: "1px solid var(--border)",
                background: "var(--surface)", color: "inherit",
                fontSize: "0.9rem", boxSizing: "border-box",
              }}
            />
          </div>
        ))}

        <div style={{ gridColumn: "1/-1", marginTop: 4 }}>
          <button type="submit" className="btn-cm" disabled={loading}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 24px" }}>
            {loading ? <RiLoader4Line className="cm-spin" /> : <RiStarLine />}
            {loading ? "Running models…" : "Run ML Models"}
          </button>
        </div>
      </form>

      {error && <ErrorBanner msg={error} />}

      {result && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: 20, marginTop: 24,
        }}>

          {/* Score */}
          <div className="cm-card" style={{ textAlign: "center" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 4 }}>
              <RiStarLine color="var(--accent2)" />
              <h5 style={{ margin: 0 }}>Creator Score</h5>
            </div>
            <ScoreRing score={result.creator_score ?? 0} />
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>out of 10</div>
            <div style={{ marginTop: 10 }}>
              <span style={{
                padding: "4px 14px", borderRadius: 20, fontSize: "0.82rem", fontWeight: 600,
                background: `${scoreColour(result.creator_score)}20`,
                color: scoreColour(result.creator_score),
              }}>
                {scoreTier(result.creator_score)}
              </span>
            </div>
          </div>

          {/* Risk */}
          <div className="cm-card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <RiShieldLine color={riskColour(result.risk_label)} />
              <h5 style={{ margin: 0 }}>Brand Risk</h5>
            </div>
            <div style={{ textAlign: "center", marginBottom: 14 }}>
              <div style={{ fontSize: "1.8rem", fontWeight: 800, color: riskColour(result.risk_label) }}>
                {result.risk_label}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 4 }}>
                P(High Risk): {((result.risk_score ?? 0) * 100).toFixed(1)}%
              </div>
            </div>
            {result.probabilities &&
              Object.entries(result.probabilities).map(([k, v]) => (
                <ProbBar key={k} label={k} pct={Math.round(v * 100)} />
              ))
            }
          </div>

        </div>
      )}
    </>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Page shell
───────────────────────────────────────────────────────────────────────────── */
export default function PricePredictor() {
  const [tab, setTab] = useState("username");

  return (
    <div>
      <h1 className="page-title">AI Prediction Suite</h1>
      <p className="page-subtitle">
        ML-powered pricing · creator scoring · brand risk analysis
      </p>

      {/* Tab bar */}
      <div style={{
        display: "flex", gap: 6, marginTop: 20, marginBottom: 28,
        background: "var(--surface)", borderRadius: 10, padding: 4,
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
            color:      tab === t.id ? "#fff"          : "var(--text-muted)",
            transition: "all .2s",
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "username" ? <UsernameTab /> : <ManualTab />}

      <style>{`
        .cm-spin { animation: _spin .8s linear infinite; display: inline-block; }
        @keyframes _spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
