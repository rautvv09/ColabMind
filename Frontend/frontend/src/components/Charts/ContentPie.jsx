import React from "react";
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend
} from "chart.js";
import { Doughnut } from "react-chartjs-2";

ChartJS.register(ArcElement, Tooltip, Legend);

const options = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: "68%",
  plugins: {
    legend: {
      position: "bottom",
      labels: {
        color: "#7a82a0",
        font:  { family: "'DM Sans', sans-serif", size: 12 },
        padding: 16,
        usePointStyle: true,
        pointStyleWidth: 10,
      },
    },
    tooltip: {
      backgroundColor: "#161d2e",
      titleColor: "#eef0f8",
      bodyColor: "#7a82a0",
      borderColor: "#1e2740",
      borderWidth: 1,
      callbacks: {
        label: ctx => ` ${ctx.label}: ${ctx.raw} (${ctx.parsed.toFixed(1)}%)`,
      },
    },
  },
};

/**
 * ContentPie
 * Shows the split between Videos, Images, and Other content.
 * Props:
 *   creator  – creator object (flat or nested)
 *   height   – container height (default 240)
 */
export default function ContentPie({ creator, height = 240 }) {
  if (!creator) return null;
  const c = creator.profile ? { ...creator, ...creator.profile } : creator;

  const videos = c.video_count ?? 0;
  const images = c.image_count ?? 0;
  const total  = c.post_count  ?? (videos + images);
  const other  = Math.max(0, total - videos - images);

  // No data fallback
  if (videos === 0 && images === 0 && other === 0) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)" }}>No content data available.</p>
      </div>
    );
  }

  const data = {
    labels:   ["Videos", "Images", ...(other > 0 ? ["Other"] : [])],
    datasets: [
      {
        data:            [videos, images, ...(other > 0 ? [other] : [])],
        backgroundColor: ["rgba(108,99,255,0.85)", "rgba(0,212,170,0.85)", "rgba(255,193,7,0.85)"],
        borderColor:     ["#6c63ff", "#00d4aa", "#ffc107"],
        borderWidth: 1,
        hoverOffset: 6,
      },
    ],
  };

  // Centre text plugin (inline)
  const videoRatio = ((videos / (total || 1)) * 100).toFixed(0);

  return (
    <div style={{ position: "relative" }}>
      <div style={{ height }}>
        <Doughnut data={data} options={options} />
      </div>

      {/* Centre label */}
      <div style={{
        position: "absolute",
        top: "42%", left: "50%", transform: "translate(-50%,-50%)",
        textAlign: "center", pointerEvents: "none"
      }}>
        <div style={{
          fontFamily: "'Syne',sans-serif", fontWeight: 800, fontSize: "1.4rem",
          background: "var(--gradient)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent"
        }}>
          {videoRatio}%
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "0.65rem", marginTop: 2 }}>
          VIDEO
        </div>
      </div>
    </div>
  );
}
