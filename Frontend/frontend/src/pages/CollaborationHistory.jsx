import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCollaborations } from "../services/api";
import "./CollaborationHistory.css";
import {
  RiArrowLeftLine,
  RiTeamLine,
  RiMoneyDollarCircleLine
} from "react-icons/ri";

const STATUS_COLORS = {
  completed: "badge-low",
  active: "badge-medium",
  pending: "badge-medium",
  cancelled: "badge-high",
};

export default function CollaborationHistory() {

  const { id } = useParams();
  const navigate = useNavigate();

  const [collabs, setCollabs] = useState([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {

    setLoading(true);

    getCollaborations(id, filter || undefined)
      .then((r) => setCollabs(r.data.data || []))
      .catch(() => setCollabs([]))
      .finally(() => setLoading(false));

  }, [id, filter]);

  const totalEarned = collabs
    .filter((c) => c.payment_status === "paid")
    .reduce((sum, c) => sum + (c.agreed_price || 0), 0);

  return (
    <div>

      {/* Back Button */}

      <button
        className="btn-outline-cm"
        style={{ marginBottom: 24 }}
        onClick={() => navigate(-1)}
      >
        <RiArrowLeftLine /> Back
      </button>

      <h1 className="page-title">Collaboration History</h1>
      <p className="page-subtitle">Brand deals and partnership records</p>

      {/* Stats */}

      <div className="stats-grid">

        <div className="stat-card">
          <RiTeamLine size={22} />
          <div className="stat-value">{collabs.length}</div>
          <div className="stat-label">Total Deals</div>
        </div>

        <div className="stat-card">
          <RiMoneyDollarCircleLine size={22} />
          <div className="stat-value">
            ₹{totalEarned.toLocaleString()}
          </div>
          <div className="stat-label">Total Earned</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">
            {collabs.filter((c) => c.status === "completed").length}
          </div>
          <div className="stat-label">Completed</div>
        </div>

      </div>

      {/* Filter Buttons */}

      <div className="cm-card">

        <div className="filter-row">

          {["", "pending", "active", "completed", "cancelled"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`filter-btn ${filter === status ? "active" : ""}`}
            >
              {status || "All"}
            </button>
          ))}

        </div>

        {/* Loading */}

        {loading ? (

          <div className="cm-spinner" />

        ) : collabs.length === 0 ? (

          <div className="empty-state">
            <RiTeamLine size={44} />
            <p>No collaborations found.</p>
          </div>

        ) : (

          <table className="cm-table">

            <thead>
              <tr>
                <th>Brand</th>
                <th>Deal</th>
                <th>Price</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Deadline</th>
              </tr>
            </thead>

            <tbody>

              {collabs.map((c) => (

                <tr key={c._id}>

                  <td>{c.brand_id || "—"}</td>

                  <td>{c.deal_type || "—"}</td>

                  <td className="price">
                    ₹{(c.agreed_price || 0).toLocaleString()}
                  </td>

                  <td>
                    <span className={`cm-badge ${STATUS_COLORS[c.status]}`}>
                      {c.status}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`cm-badge ${
                        c.payment_status === "paid"
                          ? "badge-low"
                          : "badge-medium"
                      }`}
                    >
                      {c.payment_status}
                    </span>
                  </td>

                  <td>
                    {c.deadline
                      ? new Date(c.deadline).toLocaleDateString()
                      : "—"}
                  </td>

                </tr>

              ))}

            </tbody>

          </table>

        )}

      </div>

    </div>
  );
}