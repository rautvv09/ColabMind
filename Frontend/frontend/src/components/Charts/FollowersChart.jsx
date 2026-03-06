/**
 * FollowersChart  — repurposed as TopicRadar
 * Radar chart showing AI-detected content topic distribution.
 * Matches screenshot 1: 8-axis radar with purple fill.
 * Kept as FollowersChart.jsx so existing imports don't break.
 *
 * Props:
 *   topicScores – { fitness:0.4, travel:0.1, food:0, … }  (values 0-1)
 *   height      – container px (default 280)
 *
 * Note: also exported as TopicRadar alias for new imports.
 */
import React from "react";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Radar } from "react-chartjs-2";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const AXES   = ["fitness", "travel", "food", "fashion", "tech", "comedy", "sports", "lifestyle"];
const LABELS = ["Fitness", "Travel", "Food", "Fashion", "Tech", "Comedy", "Sports", "Lifestyle"];

function TopicRadar({ topicScores = {}, height = 280 }) {
  const scores = AXES.map(k => Number((topicScores[k] || 0).toFixed(3)));
  const allZero = scores.every(s => s === 0);

  if (allZero) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          No topic data available.
        </p>
      </div>
    );
  }

  const chartData = {
    labels: LABELS,
    datasets: [{
      label: "Topic Score",
      data: scores,
      borderColor: "#6c63ff",
      backgroundColor: "rgba(108,99,255,0.20)",
      borderWidth: 2,
      pointBackgroundColor: "#6c63ff",
      pointBorderColor: "#6c63ff",
      pointRadius: 3,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: "#fff",
    }],
  };

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
          label: ctx => ` Score: ${(ctx.raw * 100).toFixed(0)}%`,
        },
      },
    },
    scales: {
      r: {
        min: 0,
        max: 1,
        ticks: { display: false, stepSize: 0.25 },
        grid: { color: "#1e2740", lineWidth: 1 },
        angleLines: { color: "#1e2740" },
        pointLabels: {
          color: "#8892a4",
          font: { family: "'DM Sans',sans-serif", size: 11 },
        },
      },
    },
  };

  return (
    <div style={{ height }}>
      <Radar data={chartData} options={options} />
    </div>
  );
}

export default TopicRadar;