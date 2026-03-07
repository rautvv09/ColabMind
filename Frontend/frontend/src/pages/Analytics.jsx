/**
 * Analytics.jsx — Creator Analytics Dashboard
 *
 * Shows real scraped data from the backend:
 *   • Summary stats (followers, avg likes, avg comments, engagement rate)
 *   • Engagement Overview  — area chart: likes & comments per post
 *   • Content Mix          — doughnut: reels vs images
 *   • Content Topics       — radar: AI-detected topic distribution
 *   • Deals summary        — status breakdown + top brands table
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getDashboard, getEngagement, getDealsSummary } from "../services/api";
import StatsCard       from "../components/StatsCard";
import EngagementChart from "../components/Charts/EngagementChart";
import ContentPie      from "../components/Charts/ContentPie";
import TopicRadar      from "../components/Charts/FollowersChart";   // radar reuse
import {
  RiArrowLeftLine,
  RiUserLine,
  RiHeartLine,
  RiChat1Line,
  RiLineChartLine,
} from "react-icons/ri";

// ── number formatter ──────────────────────────────────────────────────────────
const fmt = n => {
  if (n == null || n === "" || isNaN(n)) return "—";
  const v = Number(n);
  if (v >= 1e9) return (v / 1e9).toFixed(2) + "B";
  if (v >= 1e6) return (v / 1e6).toFixed(2) + "M";
  if (v >= 1e3) return (v / 1e3).toFixed(1) + "K";
  return v.toLocaleString();
};

export default function Analytics() {
  const { id }   = useParams();
  const navigate = useNavigate();

  const [dash,    setDash]    = useState(null);
  const [engage,  setEngage]  = useState(null);
  const [deals,   setDeals]   = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      getDashboard(id),
      getEngagement(id),
      getDealsSummary(id),
    ]).then(([d, e, dl]) => {
      if (d.status  === "fulfilled") setDash(d.value.data.data);
      if (e.status  === "fulfilled") setEngage(e.value.data.data);
      if (dl.status === "fulfilled") setDeals(dl.value.data.data);
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="cm-spinner" />;

  // ── derived values ──────────────────────────────────────────────────────────
  const username = dash?.username || engage?.username || "Creator";
  const followers     = dash?.followers     || engage?.followers     || 0;
  const avgLikes      = dash?.avg_likes     || engage?.avg_likes     || 0;
  const avgComments   = dash?.avg_comments  || engage?.avg_comments  || 0;
  const engagementPct = ((dash?.engagement_rate || engage?.engagement_rate || 0) * 100).toFixed(2);

  const perPost     = engage?.per_post    || [];
  const topicScores = engage?.topic_scores || {};
  const videoCount  = engage?.video_count  ?? dash?.video_count  ?? 0;
  const imageCount  = engage?.image_count  ?? dash?.image_count  ?? 0;

  const dealsRows     = deals?.by_status  || [];
  const topBrands     = deals?.top_brands || [];

  return (
    <div>
      {/* ── Back button ───────────────────────────────────────────── */}
      <button
        className="btn-outline-cm"
        style={{ marginBottom: 24, padding: "8px 16px", fontSize: "0.85rem" }}
        onClick={() => navigate(-1)}
      >
        <RiArrowLeftLine /> Back
      </button>

      <h1 className="page-title">Analytics</h1>
      <p className="page-subtitle">@{username} — performance overview</p>

      {/* ── Summary stat cards ────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 28 }}>
        <StatsCard label="Followers"       value={fmt(followers)}    icon={<RiUserLine />} />
        <StatsCard label="Avg Likes"       value={fmt(avgLikes)}     icon={<RiHeartLine />} />
        <StatsCard label="Avg Comments"    value={fmt(avgComments)}  icon={<RiChat1Line />} />
        <StatsCard label="Engagement Rate" value={`${engagementPct}%`} icon={<RiLineChartLine />} />
      </div>

      {/* ── Row 1: Engagement Overview (full width) ───────────────── */}
      <div className="cm-card" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 4 }}>
          <h5 style={{ margin: 0 }}>Engagement Overview</h5>
          <p style={{ color: "var(--text-muted)", fontSize: "0.78rem", marginTop: 4 }}>
            Likes &amp; Comments per post
          </p>
        </div>
        <EngagementChart perPost={perPost} height={260} />
      </div>

      {/* ── Row 2: Content Mix + Topic Radar ─────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

        <div className="cm-card">
          <div style={{ marginBottom: 4 }}>
            <h5 style={{ margin: 0 }}>Content Mix</h5>
            <p style={{ color: "var(--text-muted)", fontSize: "0.78rem", marginTop: 4 }}>
              Reels vs Static posts
            </p>
          </div>
          <ContentPie videoCount={videoCount} imageCount={imageCount} height={280} />
        </div>

        <div className="cm-card">
          <div style={{ marginBottom: 4 }}>
            <h5 style={{ margin: 0 }}>Content Topics</h5>
            <p style={{ color: "var(--text-muted)", fontSize: "0.78rem", marginTop: 4 }}>
              AI-detected topic distribution
            </p>
          </div>
          <TopicRadar topicScores={topicScores} height={280} />
        </div>

      </div>

      {/* ── Row 4: Deals by status + Top brands ──────────────────── */}
      {(dealsRows.length > 0 || topBrands.length > 0) && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

          {dealsRows.length > 0 && (
            <div className="cm-card">
              <h5 style={{ marginBottom: 16 }}>Deals by Status</h5>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {dealsRows.map((s, i) => (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "10px 14px",
                    background: "rgba(255,255,255,0.03)",
                    borderRadius: 8, border: "1px solid var(--border)",
                  }}>
                    <span style={{ textTransform: "capitalize", color: "var(--text-muted)" }}>
                      {s._id || "Unknown"}
                    </span>
                    <span style={{ fontWeight: 700, color: "var(--accent-2)" }}>
                      {s.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {topBrands.length > 0 && (
            <div className="cm-card">
              <h5 style={{ marginBottom: 16 }}>Top Brands by Revenue</h5>
              <table className="cm-table">
                <thead>
                  <tr>
                    <th>Brand</th>
                    <th>Deals</th>
                    <th>Total Paid</th>
                  </tr>
                </thead>
                <tbody>
                  {topBrands.map((b, i) => (
                    <tr key={i}>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{b._id || "—"}</td>
                      <td>{b.deal_count}</td>
                      <td style={{ color: "var(--accent-2)", fontWeight: 700 }}>
                        ₹{(b.total_paid || 0).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

        </div>
      )}

      {/* ── Avg views callout if non-zero ─────────────────────────── */}
      {(engage?.avg_views > 0) && (
        <div className="cm-card" style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h5 style={{ margin: 0 }}>Average Reel Views</h5>
              <p style={{ color: "var(--text-muted)", fontSize: "0.78rem", margin: "4px 0 0" }}>
                Across {engage?.posts_count || 0} analysed posts
              </p>
            </div>
            <span style={{
              fontSize: "2rem", fontWeight: 800,
              background: "var(--gradient)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>
              {fmt(engage.avg_views)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}