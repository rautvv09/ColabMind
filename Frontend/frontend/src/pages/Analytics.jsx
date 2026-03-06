import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getDashboard, getEngagement, getDealsSummary } from "../services/api";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  Title, Tooltip, Legend, ArcElement
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import StatsCard from "../components/StatsCard";
import { RiArrowLeftLine, RiMoneyDollarCircleLine } from "react-icons/ri";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

const chartOptions = {
  responsive: true,
  plugins: { legend: { labels: { color: "#7a82a0" } } },
  scales: {
    x: { ticks: { color: "#7a82a0" }, grid: { color: "#1e2740" } },
    y: { ticks: { color: "#7a82a0" }, grid: { color: "#1e2740" } },
  },
};

export default function Analytics() {
  const { id } = useParams();
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
      if (d.status === "fulfilled") setDash(d.value.data.data);
      if (e.status === "fulfilled") setEngage(e.value.data.data);
      if (dl.status === "fulfilled") setDeals(dl.value.data.data);
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="cm-spinner" />;

  const engageBarData = engage ? {
    labels: ["Avg Likes", "Avg Comments", "Avg Views"],
    datasets: [{
      label: "Engagement Metrics",
      data: [engage.avg_likes||0, engage.avg_comments||0, engage.avg_reel_views||0],
      backgroundColor: ["rgba(108,99,255,0.7)", "rgba(0,212,170,0.7)", "rgba(255,107,107,0.7)"],
      borderRadius: 6,
    }],
  } : null;

  const dealsStatusData = deals?.by_status?.length ? {
    labels: deals.by_status.map(d => d._id || "Unknown"),
    datasets: [{
      data: deals.by_status.map(d => d.count),
      backgroundColor: ["rgba(108,99,255,0.8)", "rgba(0,212,170,0.8)", "rgba(255,107,107,0.8)", "rgba(255,193,7,0.8)"],
    }],
  } : null;

  return (
    <div>
      <button className="btn-outline-cm" style={{ marginBottom: 24, padding: "8px 16px", fontSize: "0.85rem" }}
        onClick={() => navigate(-1)}>
        <RiArrowLeftLine /> Back
      </button>

      <h1 className="page-title">Analytics</h1>
      <p className="page-subtitle">
        {dash?.username ? `@${dash.username}` : "Creator"} performance overview
      </p>

      {/* Summary stats */}
      {dash && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 28 }}>
          <StatsCard label="Followers"       value={((dash.followers||0)/1e6).toFixed(2)+"M"} />
          <StatsCard label="Engagement Rate" value={((dash.engagement_rate||0)*100).toFixed(2)+"%"} />
          <StatsCard label="Total Deals"     value={dash.total_collaborations} />
          <StatsCard label="Total Earned"    value={"₹"+(dash.total_earned||0).toLocaleString()} icon={<RiMoneyDollarCircleLine />} />
        </div>
      )}

      {/* Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20, marginBottom: 24 }}>
        <div className="cm-card">
          <h5 style={{ marginBottom: 16 }}>Engagement Metrics</h5>
          {engageBarData
            ? <Bar data={engageBarData} options={chartOptions} />
            : <p style={{ color: "var(--text-muted)" }}>No engagement data available.</p>
          }
        </div>

        <div className="cm-card">
          <h5 style={{ marginBottom: 16 }}>Deals by Status</h5>
          {dealsStatusData
            ? <Doughnut data={dealsStatusData} options={{ plugins: { legend: { labels: { color: "#7a82a0" } } } }} />
            : <p style={{ color: "var(--text-muted)" }}>No deals data yet.</p>
          }
        </div>
      </div>

      {/* Top brands */}
      {deals?.top_brands?.length > 0 && (
        <div className="cm-card">
          <h5 style={{ marginBottom: 16 }}>Top Brands by Revenue</h5>
          <table className="cm-table">
            <thead>
              <tr>
                <th>Brand ID</th>
                <th>Deals</th>
                <th>Total Paid</th>
              </tr>
            </thead>
            <tbody>
              {deals.top_brands.map((b, i) => (
                <tr key={i}>
                  <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{b._id}</td>
                  <td>{b.deal_count}</td>
                  <td style={{ color: "var(--accent2)", fontWeight: 700 }}>₹{b.total_paid?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
