/**
 * EngagementChart  — Area (Line+fill) chart
 * Shows Likes & Comments per post (P1…Pn) from real scraped data.
 * Matches screenshot 3: green filled area for likes, purple for comments.
 *
 * Props:
 *   perPost – [{ label:"P1", likes:45000, comments:800 }, …]
 *   height  – container px (default 260)
 */
import React from "react";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,
  PointElement, LineElement,
  Filler, Tooltip, Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale, LinearScale,
  PointElement, LineElement,
  Filler, Tooltip, Legend
);

const fmtY = v =>
  v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` :
  v >= 1e3 ? `${(v / 1e3).toFixed(0)}K` : String(v);

export default function EngagementChart({ perPost = [], height = 260 }) {
  if (!perPost || perPost.length === 0) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No post data available.</p>
      </div>
    );
  }

  const chartData = {
    labels: perPost.map(p => p.label),
    datasets: [
      {
        label: "Likes",
        data: perPost.map(p => p.likes || 0),
        borderColor: "#00d4aa",
        backgroundColor: "rgba(0,212,170,0.15)",
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#00d4aa",
        pointHoverBorderColor: "#fff",
        pointHoverBorderWidth: 2,
      },
      {
        label: "Comments",
        data: perPost.map(p => p.comments || 0),
        borderColor: "#6c63ff",
        backgroundColor: "rgba(108,99,255,0.10)",
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: "#6c63ff",
        pointHoverBorderColor: "#fff",
        pointHoverBorderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "top",
        align: "end",
        labels: {
          color: "#7a82a0",
          font: { family: "'DM Sans',sans-serif", size: 12 },
          usePointStyle: true,
          pointStyleWidth: 8,
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: "#161d2e",
        titleColor: "#8892a4",
        bodyColor: "#f0f4ff",
        borderColor: "#1e2740",
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: ctx =>
            ` ${ctx.dataset.label}: ${Number(ctx.raw).toLocaleString()}`,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: "#7a82a0",
          font: { family: "'DM Sans',sans-serif", size: 11 },
          maxTicksLimit: 12,
          maxRotation: 0,
        },
        grid: { color: "rgba(30,39,64,0.7)", drawBorder: false },
      },
      y: {
        ticks: {
          color: "#7a82a0",
          font: { family: "'DM Sans',sans-serif", size: 11 },
          callback: fmtY,
        },
        grid: { color: "rgba(30,39,64,0.7)", drawBorder: false },
      },
    },
  };

  return (
    <div style={{ height }}>
      <Line data={chartData} options={options} />
    </div>
  );
}