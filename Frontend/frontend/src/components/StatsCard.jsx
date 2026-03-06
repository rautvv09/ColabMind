import React from "react";

export default function StatsCard({ label, value, icon, color = "var(--accent)" }) {
  return (
    <div className="stat-card">
      {icon && (
        <div style={{ fontSize: "1.6rem", marginBottom: 8, color }}>{icon}</div>
      )}
      <div className="stat-value">{value ?? "—"}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
