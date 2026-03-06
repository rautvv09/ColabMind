/**
 * ContentPie  — Doughnut chart: Reels/Videos vs Images/Carousels
 * Matches screenshot 2: green slice for videos, purple for images,
 * percentage labels on slices, custom legend with right-aligned % values.
 *
 * Props:
 *   videoCount – number of video/reel posts
 *   imageCount – number of image/carousel posts
 *   height     – container px (default 280)
 */
import React from "react";
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
} from "chart.js";
import { Doughnut } from "react-chartjs-2";

ChartJS.register(ArcElement, Tooltip, Legend);

export default function ContentPie({ videoCount = 0, imageCount = 0, height = 280 }) {
  const total = (videoCount || 0) + (imageCount || 0);

  if (total === 0) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No content data available.</p>
      </div>
    );
  }

  const videoPct = Math.round((videoCount / total) * 100);
  const imagePct = 100 - videoPct;

  const chartData = {
    labels: ["Reels / Videos", "Images / Carousels"],
    datasets: [{
      data: [videoCount, imageCount],
      backgroundColor: ["rgba(0,212,170,0.88)", "rgba(108,99,255,0.88)"],
      borderColor:     ["#00d4aa", "#6c63ff"],
      borderWidth: 1.5,
      hoverOffset: 5,
    }],
  };

  // Inline canvas plugin to draw % labels on each slice
  const labelPlugin = {
    id: "sliceLabels",
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(0);
      meta.data.forEach((arc, i) => {
        const { x, y, startAngle, endAngle, innerRadius, outerRadius } = arc.getProps(
          ["x", "y", "startAngle", "endAngle", "innerRadius", "outerRadius"], true
        );
        const angle  = (startAngle + endAngle) / 2;
        const r      = innerRadius + (outerRadius - innerRadius) * 0.58;
        const px     = x + Math.cos(angle) * r;
        const py     = y + Math.sin(angle) * r;
        const pct    = i === 0 ? videoPct : imagePct;
        if (pct < 5) return;
        ctx.save();
        ctx.font         = "bold 13px 'DM Sans',sans-serif";
        ctx.fillStyle    = "#fff";
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`${pct}%`, px, py);
        ctx.restore();
      });
    },
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "62%",
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          color: "#8892a4",
          font: { family: "'DM Sans',sans-serif", size: 12 },
          padding: 20,
          usePointStyle: true,
          pointStyleWidth: 10,
          // Append right-aligned % to each label
          generateLabels: (chart) => {
            const ds   = chart.data.datasets[0];
            const pcts = [videoPct, imagePct];
            return chart.data.labels.map((lbl, i) => ({
              text:        `${lbl}   ${pcts[i]}%`,
              fillStyle:   ds.backgroundColor[i],
              strokeStyle: ds.borderColor[i],
              lineWidth:   1,
              pointStyle:  "circle",
              hidden:      false,
              index:       i,
            }));
          },
        },
      },
      tooltip: {
        backgroundColor: "#161d2e",
        titleColor: "#eef0f8",
        bodyColor: "#7a82a0",
        borderColor: "#1e2740",
        borderWidth: 1,
        callbacks: {
          label: ctx => {
            const pct = Math.round((ctx.raw / total) * 100);
            return ` ${ctx.label}: ${ctx.raw} posts (${pct}%)`;
          },
        },
      },
    },
  };

  return (
    <div style={{ height }}>
      <Doughnut data={chartData} options={options} plugins={[labelPlugin]} />
    </div>
  );
}