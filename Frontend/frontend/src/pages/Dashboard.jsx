import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getAllCreators } from "../services/api";
import StatsCard from "../components/StatsCard";
import {
  RiUserLine,
  RiSearchLine,
  RiArrowRightLine,
  RiVerifiedBadgeLine,
  RiBriefcaseLine
} from "react-icons/ri";

export default function Dashboard() {
  const [creators, setCreators] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getAllCreators()
      .then(r => setCreators(r.data.data || []))
      .catch(() => setCreators([]))
      .finally(() => setLoading(false));
  }, []);

  /* ------------------------------
     TOTAL FOLLOWERS
  ------------------------------ */

  const totalFollowers = creators.reduce((sum, c) => {
    return sum + (c.followers || 0);
  }, 0);

  /* format number to K / M / B */
  const fmtNum = n => {
    if (!n) return "—";
    if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
    if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
    return n.toLocaleString();
  };

  /* ------------------------------
     AVG ENGAGEMENT
  ------------------------------ */

  const avgEngagement = creators.length
    ? (
        creators.reduce((sum, c) => {
          return sum + (c.engagement_rate || 0);
        }, 0) /
        creators.length *
        100
      ).toFixed(2)
    : 0;

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">Overview of all creators in your database</p>

      {/* ------------------------------
          STATS CARDS
      ------------------------------ */}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3,1fr)",
          gap: 16,
          marginBottom: 32
        }}
      >
        <StatsCard
          label="Total Creators"
          value={creators.length}
          icon={<RiUserLine />}
        />

        <StatsCard
          label="Total Followers"
          value={fmtNum(totalFollowers)}
          icon={<RiVerifiedBadgeLine />}
        />

        <StatsCard
          label="Avg Engagement"
          value={`${avgEngagement}%`}
          icon={<RiBriefcaseLine />}
        />
      </div>

      {/* ------------------------------
          CREATOR TABLE
      ------------------------------ */}

      <div className="cm-card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 20
          }}
        >
          <h5 style={{ margin: 0 }}>All Creators</h5>

          <button className="btn-cm" onClick={() => navigate("/search")}>
            <RiSearchLine /> Search Creator
          </button>
        </div>

        {loading ? (
          <div className="cm-spinner" />
        ) : creators.length === 0 ? (
          <p
            style={{
              color: "var(--text-muted)",
              textAlign: "center",
              padding: 32
            }}
          >
            No creators found. Search and add one!
          </p>
        ) : (
          <table className="cm-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Category</th>
                <th>Followers</th>
                <th>Engagement</th>
                <th>Score</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              {creators.map(c => (
                <tr key={c.creator_id}>
                  <td>
                    <strong>@{c.username}</strong>
                  </td>

                  <td style={{ color: "var(--text-muted)" }}>
                    {c.category || "—"}
                  </td>

                  <td>
                    {fmtNum(c.followers || 0)}
                  </td>

                  <td>
                    {((c.engagement_rate || 0) * 100).toFixed(2)}%
                  </td>

                  <td>
                    <span
                      style={{
                        color: "var(--accent2)",
                        fontWeight: 700
                      }}
                    >
                      {(c.creator_score || 0).toFixed(1)}
                    </span>
                  </td>

                  <td>
                    <button
                      className="btn-outline-cm"
                      style={{
                        padding: "6px 14px",
                        fontSize: "0.8rem"
                      }}
                      onClick={() =>
                        navigate(`/creator/${c.username}`)
                      }
                    >
                      View <RiArrowRightLine />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}