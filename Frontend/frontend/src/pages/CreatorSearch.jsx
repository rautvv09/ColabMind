import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCreatorByUsername } from "../services/api";
import { RiSearchLine, RiUserLine, RiArrowRightLine } from "react-icons/ri";

export default function CreatorSearch() {

  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {

      const res = await getCreatorByUsername(query.trim().toLowerCase());

      const data = res.data.data;

      const flat = data.profile ? { ...data, ...data.profile } : data;

      setResult(flat);

    } catch (err) {

      setError(
        err.response?.data?.message ||
        "Creator not found in database."
      );

    } finally {
      setLoading(false);
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
          />

          <button className="btn-cm" type="submit">

            {loading ? "Searching..." : (
              <>
                <RiSearchLine /> Search
              </>
            )}

          </button>

        </form>

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

              <h4>{result.full_name || result.username}</h4>
              <span>@{result.username}</span>

              {result.is_verified && (
                <span style={{
                  marginLeft: 8,
                  color: "#00d4aa"
                }}>
                  ✓ Verified
                </span>
              )}

            </div>

          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3,1fr)",
            gap: 12
          }}>

            <div className="stat-card">
              <b>{((result.follower_count || 0) / 1e6).toFixed(2)}M</b>
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
              onClick={() => navigate(`/creator/${result._id}`)}
            >
              View Profile <RiArrowRightLine />
            </button>

          </div>

        </div>

      )}

    </div>
  );
}