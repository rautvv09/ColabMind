import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { lookupCreator } from "../services/api";
import { RiSearchLine, RiUserLine, RiArrowRightLine, RiLoader4Line, RiRadarLine, RiSparklingLine } from "react-icons/ri";

export default function CreatorSearch() {

  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("idle"); // "idle"|"checking"|"scraping"
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    setLoadingStage("checking");
    setError("");
    setResult(null);

    try {

      // lookupCreator → GET /api/creator/lookup/<username>
      // 1. Backend checks `profiles` collection (same as pricing)
      // 2. If missing → scrapes SearchAPI → stores → re-fetches from DB
      // 3. Returns { ...profileDoc, scraped_fresh: true|false }
      const res = await lookupCreator(query.trim().toLowerCase());

      const data = res.data.data;

      // Show scraping banner if backend had to scrape
      if (data.scraped_fresh) setLoadingStage("scraping");

      // Flatten nested profile doc (profile.py stores as { profile: {...}, posts: [...] })
      const flat = data.profile ? { ...data, ...data.profile } : data;

      setResult({ ...flat, scraped_fresh: data.scraped_fresh });

    } catch (err) {

      setError(
        err.response?.data?.message ||
        "Creator not found. Make sure the username is correct."
      );

    } finally {
      setLoading(false);
      setLoadingStage("idle");
    }
  };

  return (
    <div>

      <h1 className="page-title">Search Creator</h1>
      <p className="page-subtitle">
        Find a creator by their Instagram username
      </p>

      <div className="cm-card" style={{ maxWidth: 600, marginBottom: 32 }}>

        <form onSubmit={handleSearch} style={{ display: "flex", gap: 12 }}>

          <input
            className="cm-input"
            placeholder="Enter Instagram username e.g. leomessi"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />

          <button className="btn-cm" type="submit" disabled={loading}
            style={{ display: "flex", alignItems: "center", gap: 6, opacity: loading ? 0.65 : 1 }}>
            {loading
              ? <RiLoader4Line style={{ animation: "searchSpin .8s linear infinite" }} />
              : <RiSearchLine />
            }
            {loading
              ? (loadingStage === "scraping" ? "Scraping…" : "Checking…")
              : "Search"
            }
          </button>

        </form>

        {/* Scraping banner — shown only when backend is scraping a new profile */}
        {loading && loadingStage === "scraping" && (
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            marginTop: 14, padding: "11px 14px",
            background: "rgba(108,99,255,0.07)",
            border: "1px solid rgba(108,99,255,0.18)",
            borderRadius: 10, fontSize: "0.83rem",
            color: "rgba(160,150,255,0.90)",
          }}>
            <RiRadarLine style={{ flexShrink: 0, fontSize: "1.1rem" }} />
            <span>
              New profile detected — scraping Instagram data and storing to database.
              This may take a few seconds…
            </span>
          </div>
        )}

        {error && (
          <div style={{
            marginTop: 16,
            padding: "12px 16px",
            borderRadius: 10,
            background: "rgba(255,107,107,0.1)",
            color: "#ff6b6b"
          }}>
            {error}
          </div>
        )}

      </div>

      {result && (

        <div className="cm-card" style={{ maxWidth: 600 }}>

          {/* Fresh-scrape badge */}
          {result.scraped_fresh && (
            <div style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              fontSize: "0.70rem", fontWeight: 600, letterSpacing: "0.08em",
              textTransform: "uppercase", padding: "3px 12px", borderRadius: 20,
              marginBottom: 16,
              background: "rgba(0,212,170,0.10)",
              border: "1px solid rgba(0,212,170,0.22)",
              color: "#00d4aa",
            }}>
              <RiSparklingLine /> Freshly scraped from Instagram
            </div>
          )}

          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 20
          }}>

            <div style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "linear-gradient(135deg,#6c63ff,#00d4aa)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <RiUserLine size={28} color="white" />
            </div>

            <div>

              <h4 style={{ margin: 0 }}>{result.full_name || result.username}</h4>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.88rem" }}>
                @{result.username}
              </span>

              {result.is_verified && (
                <span style={{ marginLeft: 8, color: "#00d4aa" }}>
                  ✓ Verified
                </span>
              )}

              {result.category && (
                <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: 2 }}>
                  {result.category}
                </div>
              )}

            </div>

          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3,1fr)",
            gap: 12
          }}>

            <div className="stat-card">
              <b>{
                result.follower_count >= 1e6
                  ? `${(result.follower_count / 1e6).toFixed(2)}M`
                  : result.follower_count >= 1e3
                  ? `${(result.follower_count / 1e3).toFixed(1)}K`
                  : result.follower_count || 0
              }</b>
              <p>Followers</p>
            </div>

            <div className="stat-card">
              <b>{((result.engagement_rate || 0) * 100).toFixed(2)}%</b>
              <p>Engagement</p>
            </div>

            <div className="stat-card">
              <b>{result.post_count || 0}</b>
              <p>Posts</p>
            </div>

          </div>

          <div style={{ marginTop: 20 }}>

            <button
              className="btn-cm"
              onClick={() => navigate(`/creator/${result.username}`)}
              style={{ display: "flex", alignItems: "center", gap: 6 }}
            >
              View Profile <RiArrowRightLine />
            </button>

          </div>

        </div>

      )}

      <style>{`
        @keyframes searchSpin { to { transform: rotate(360deg); } }
      `}</style>

    </div>
  );
}