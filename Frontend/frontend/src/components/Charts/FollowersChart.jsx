import React from "react";
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Filler, Legend
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Filler, Legend
);

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "#161d2e",
      titleColor: "#eef0f8",
      bodyColor: "#7a82a0",
      borderColor: "#1e2740",
      borderWidth: 1,
      callbacks: {
        label: ctx => {
          const v = ctx.raw;
          return ` ${v >= 1e6 ? (v/1e6).toFixed(2)+"M" : v >= 1e3 ? (v/1e3).toFixed(1)+"K" : v} followers`;
        },
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
 * FollowersChart
 * Since we only have current follower_count (no historical data from Atlas),
 * this component builds a realistic-looking projected growth curve
 * based on posting frequency and engagement rate.
 *
 * Props:
 *   creator  – creator object
 *   height   – container height (default 260)
 */
export default function FollowersChart({ creator, height = 260 }) {
  if (!creator) return null;
  const c = creator.profile ? { ...creator, ...creator.profile } : creator;

  const current      = c.follower_count      ?? 0;
  const engRate      = c.engagement_rate     ?? 0.01;
  const postFreq     = c.posting_frequency_weekly ?? 3;

  // Simulate 6-month growth curve based on engagement + frequency
  const growthFactor = 1 + (engRate * 0.5 * (postFreq / 7));
  const months       = ["6M Ago", "5M Ago", "4M Ago", "3M Ago", "2M Ago", "1M Ago", "Now"];
  const points       = months.map((_, i) => {
    const monthsBack = months.length - 1 - i;
    return Math.round(current / Math.pow(growthFactor, monthsBack));
  });

  const data = {
    labels: months,
    datasets: [
      {
        label: "Followers",
        data: points,
        borderColor: "#6c63ff",
        backgroundColor: "rgba(108,99,255,0.12)",
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#6c63ff",
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  return (
    <div>
      <div style={{ height }}>
        <Line data={data} options={options} />
      </div>
      <div style={{
        marginTop: 8, fontSize: "0.72rem", color: "var(--text-muted)",
        textAlign: "center", fontStyle: "italic"
      }}>
        * Estimated growth curve based on current engagement rate & posting frequency
      </div>
    </div>
  );
}
