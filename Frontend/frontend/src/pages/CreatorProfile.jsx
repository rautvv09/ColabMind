import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCreatorByUsername } from "../services/api";
import StatsCard from "../components/StatsCard";
import {
  RiUserLine, RiHeartLine, RiChat1Line, RiVideoLine,
  RiLineChartLine, RiMoneyDollarCircleLine, RiArrowLeftLine
} from "react-icons/ri";

export default function CreatorProfile() {

  const { username } = useParams();
  const navigate = useNavigate();

  const [creator, setCreator] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {

    getCreatorByUsername(username)
      .then(r => {

        const d = r.data.data;
        setCreator(d.profile ? { ...d, ...d.profile } : d);

      })
      .catch(() => setError("Creator not found."))
      .finally(() => setLoading(false));

  }, [username]);

  if (loading) return <div className="cm-spinner" />;
  if (error) return <p style={{ color: "#ff6b6b" }}>{error}</p>;
  if (!creator) return null;

  const c = creator;

  return (

    <div>

      <button
        className="btn-outline-cm"
        style={{ marginBottom: 24, padding: "8px 16px", fontSize: "0.85rem" }}
        onClick={() => navigate(-1)}
      >
        <RiArrowLeftLine /> Back
      </button>

      <div className="cm-card" style={{ marginBottom: 24 }}>

        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>

          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: "50%",
              background: "linear-gradient(135deg,#6c63ff,#00d4aa)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}
          >
            <RiUserLine size={36} color="white" />
          </div>

          <div style={{ flex: 1 }}>

            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h2 style={{ margin: 0 }}>{c.full_name || c.username}</h2>
              {c.is_verified && <span style={{ color: "var(--accent2)" }}>✓</span>}
            </div>

            <p style={{ color: "var(--text-muted)", margin: "4px 0 0" }}>
              @{c.username} · {c.category}
            </p>

          </div>

          <div style={{ display: "flex", gap: 10 }}>

            <button
              className="btn-cm"
              onClick={() => navigate(`/analytics/${c._id}`)}
            >
              <RiLineChartLine /> Analytics
            </button>

            <button
              className="btn-outline-cm"
              onClick={() => navigate(`/price-predictor?username=${c.username}`)}
            >
              <RiMoneyDollarCircleLine /> Price
            </button>

          </div>

        </div>

      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4,1fr)",
          gap: 16,
          marginBottom: 24
        }}
      >

        <StatsCard
          label="Followers"
          value={((c.follower_count || 0) / 1e6).toFixed(2) + "M"}
          icon={<RiUserLine />}
        />

        <StatsCard
          label="Avg Likes"
          value={((c.like_count_avg || 0) / 1e3).toFixed(1) + "K"}
          icon={<RiHeartLine />}
        />

        <StatsCard
          label="Avg Comments"
          value={((c.comment_count_avg || 0) / 1e3).toFixed(1) + "K"}
          icon={<RiChat1Line />}
        />

        <StatsCard
          label="Avg Views"
          value={((c.view_count_avg || 0) / 1e3).toFixed(1) + "K"}
          icon={<RiVideoLine />}
        />

      </div>

    </div>
  );
}