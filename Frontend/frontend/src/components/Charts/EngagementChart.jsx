import React from "react";
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: "#7a82a0", font: { family: "'DM Sans', sans-serif" } }
    },
    tooltip: {
      backgroundColor: "#161d2e",
      titleColor: "#eef0f8",
      bodyColor: "#7a82a0",
      borderColor: "#1e2740",
      borderWidth: 1,
      callbacks: {
        label: ctx => ` ${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString()}`,
      },
    },
  },
  scales: {
    x: {
      ticks: { color: "#7a82a0", font: { family: "'DM Sans', sans-serif" } },
      grid:  { color: "#1e2740" },
    },
    y: {
      ticks: {
        color: "#7a82a0",
        font: { family: "'DM Sans', sans-serif" },
        callback: v => v >= 1e6 ? `${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `${(v/1e3).toFixed(0)}K` : v,
      },
      grid: { color: "#1e2740" },
    },
  },
};

/**
 * EngagementChart
 * Props:
 *   creator  – creator object (flat or with profile nested)
 *   height   – container height in px (default 260)
 */
export default function EngagementChart({ creator, height = 260 }) {
  if (!creator) return null;
  const c = creator.profile ? { ...creator, ...creator.profile } : creator;

  const data = {
    labels: ["Avg Likes", "Avg Comments", "Avg Views"],
    datasets: [
      {
        label: "Engagement",
        data: [
          c.like_count_avg    ?? 0,
          c.comment_count_avg ?? 0,
          c.view_count_avg    ?? 0,
        ],
        backgroundColor: [
          "rgba(108,99,255,0.75)",
          "rgba(0,212,170,0.75)",
          "rgba(255,107,107,0.75)",
        ],
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  return (
    <div style={{ height }}>
      <Bar data={data} options={options} />
    </div>
  );
}
