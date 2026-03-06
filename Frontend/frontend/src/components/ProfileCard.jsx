import React from "react";
import { useNavigate } from "react-router-dom";
import {
  RiUserLine, RiVerifiedBadgeLine, RiBriefcaseLine,
  RiLineChartLine, RiMoneyDollarCircleLine, RiHandshakeLine
} from "react-icons/ri";

export default function ProfileCard({ creator, showActions = true }) {
  const navigate = useNavigate();

  if (!creator) return null;

  // Flatten nested profile if needed
  const c = creator.profile ? { ...creator, ...creator.profile } : creator;

  const followers   = c.follower_count  ?? 0;
  const engRate     = c.engagement_rate ?? 0;
  const engPercent  = c["engagement_%"] ?? (engRate * 100);
  const postCount   = c.post_count      ?? 0;
  const category    = c.category        ?? "—";

  const riskLevel = engPercent > 3 ? "High" : engPercent > 1 ? "Medium" : "Low";
  const riskColor = riskLevel === "High" ? "#00d4aa" : riskLevel === "Medium" ? "#ffc107" : "#ff6b6b";

  return (
    <div className="cm-card" style={{ position: "relative", overflow: "hidden" }}>

      {/* Background accent blob */}
      <div style={{
        position: "absolute", top: -40, right: -40,
        width: 160, height: 160, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(108,99,255,0.12) 0%, transparent 70%)",
        pointerEvents: "none"
      }} />

      {/* Avatar + name row */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <div style={{
          width: 64, height: 64, borderRadius: "50%", flexShrink: 0,
          background: "linear-gradient(135deg, #6c63ff, #00d4aa)",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 0 0 3px rgba(108,99,255,0.25)"
        }}>
          {c.profile_pic_url
            ? <img src={c.profile_pic_url} alt={c.username}
                style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }} />
            : <RiUserLine size={30} color="white" />
          }
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <h4 style={{ margin: 0, fontSize: "1.1rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {c.full_name || c.username}
            </h4>
            {c.is_verified && <RiVerifiedBadgeLine color="#00d4aa" title="Verified" />}
            {c.is_business && (
              <span style={{
                background: "rgba(108,99,255,0.15)", color: "var(--accent)",
                padding: "2px 8px", borderRadius: 20, fontSize: "0.7rem", fontWeight: 600
              }}>
                Business
              </span>
            )}
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 2 }}>
            @{c.username}
            {category !== "—" && (
              <span style={{ marginLeft: 8, color: "var(--accent2)" }}>· {category}</span>
            )}
          </div>
          {c.bio && (
            <div style={{
              fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 6,
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
            }}>
              {c.bio}
            </div>
          )}
        </div>
      </div>

      {/* Key metrics */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(3,1fr)",
        gap: 10, marginBottom: 20
      }}>
        {[
          { label: "Followers",   value: followers >= 1e6 ? `${(followers/1e6).toFixed(2)}M` : followers >= 1e3 ? `${(followers/1e3).toFixed(1)}K` : followers },
          { label: "Posts",       value: postCount.toLocaleString() },
          { label: "Engagement",  value: `${engPercent.toFixed(2)}%` },
        ].map(m => (
          <div key={m.label} style={{
            background: "var(--bg-dark)", borderRadius: 10, padding: "10px 8px", textAlign: "center"
          }}>
            <div style={{
              fontFamily: "'Syne',sans-serif", fontWeight: 800, fontSize: "1.1rem",
              background: "var(--gradient)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent"
            }}>
              {m.value}
            </div>
            <div style={{ color: "var(--text-muted)", fontSize: "0.7rem", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {m.label}
            </div>
          </div>
        ))}
      </div>

      {/* Engagement quality bar */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Engagement Quality
          </span>
          <span style={{ color: riskColor, fontSize: "0.75rem", fontWeight: 600 }}>{riskLevel}</span>
        </div>
        <div style={{ height: 6, background: "var(--bg-dark)", borderRadius: 3, overflow: "hidden" }}>
          <div style={{
            height: "100%", borderRadius: 3,
            width: `${Math.min(engPercent * 10, 100)}%`,
            background: `linear-gradient(90deg, ${riskColor}88, ${riskColor})`,
            transition: "width 0.6s ease"
          }} />
        </div>
      </div>

      {/* Additional info row */}
      <div style={{
        display: "flex", gap: 16, flexWrap: "wrap",
        paddingTop: 16, borderTop: "1px solid var(--border)", marginBottom: showActions ? 16 : 0
      }}>
        {[
          { label: "Following",       value: c.following_count?.toLocaleString() ?? "—" },
          { label: "Posts/Week",      value: c.posting_frequency_weekly ?? "—" },
          { label: "Avg Likes",       value: c.like_count_avg >= 1e3 ? `${(c.like_count_avg/1e3).toFixed(1)}K` : (c.like_count_avg ?? "—") },
          { label: "Follower Ratio",  value: c.follower_following_ratio ? c.follower_following_ratio.toFixed(0) : "—" },
        ].map(i => (
          <div key={i.label}>
            <div style={{ color: "var(--text-muted)", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {i.label}
            </div>
            <div style={{ fontWeight: 600, fontSize: "0.9rem", marginTop: 2 }}>{i.value}</div>
          </div>
        ))}
      </div>

      {/* Action buttons */}
      {showActions && (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn-cm"
            style={{ flex: 1, fontSize: "0.85rem", padding: "9px 16px" }}
            onClick={() => navigate(`/creator/${c.username}`)}>
            <RiLineChartLine /> Profile
          </button>
          <button className="btn-outline-cm"
            style={{ flex: 1, fontSize: "0.85rem", padding: "9px 16px" }}
            onClick={() => navigate(`/price-predictor?id=${creator._id}`)}>
            <RiMoneyDollarCircleLine /> Price
          </button>
          <button className="btn-outline-cm"
            style={{ flex: 1, fontSize: "0.85rem", padding: "9px 16px" }}
            onClick={() => navigate(`/collaborations/${creator._id}`)}>
            <RiHandshakeLine />
          </button>
        </div>
      )}
    </div>
  );
}
