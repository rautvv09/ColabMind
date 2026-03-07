import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCollaborations, deleteCollaboration } from "../services/api";
import "./CollaborationHistory.css";

export default function CollaborationHistory() {
  const navigate = useNavigate();
  const [collabs, setCollabs] = useState([]);

  useEffect(() => {
    loadCollaborations();
  }, []);

  const loadCollaborations = async () => {
    try {
      const res = await getCollaborations();
      // Adjust res.data.data based on your actual API response structure
      setCollabs(res.data.data || []);
    } catch (err) {
      console.error("Error fetching collaborations:", err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this collaboration?")) return;

    try {
      await deleteCollaboration(id);
      setCollabs((prev) => prev.filter((c) => c._id !== id));
    } catch (err) {
      console.error("Error deleting collaboration:", err);
    }
  };

  return (
    <div className="collab-container">
      <h1 className="page-title">Collaboration List</h1>

      {/* HEADER SECTION */}
      <div className="collab-header">
        <span>Deal</span>
        <span>Price</span>
        <span>Status</span>
        <span>Deadline</span>
        <span className="actions-header">Actions</span>
      </div>

      {/* LIST SECTION */}
      {collabs.length > 0 ? (
        collabs.map((c) => (
          <div key={c._id} className="collab-row">
            {/* Deal Type */}
            <span className="deal-name">{c.deal_type}</span>

            {/* Price */}
            <span className="price-amount">
              ₹{c.agreed_price ? c.agreed_price.toLocaleString() : "0"}
            </span>

            {/* Status Column (Fix for the 'pending' length issue) */}
            <span className="status-column">
              <span className={`status ${c.status?.toLowerCase()}`}>
                {c.status}
              </span>
            </span>

            {/* Deadline */}
            <span className="deadline-date">
              {c.deadline 
                ? new Date(c.deadline).toLocaleDateString() 
                : "-"
              }
            </span>

            {/* Action Buttons */}
            <div className="actions">
              <button
                className="btn-update"
                onClick={() => navigate(`/update-collaboration/${c._id}`)}
              >
                Update
              </button>
              <button
                className="btn-delete"
                onClick={() => handleDelete(c._id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))
      ) : (
        <p style={{ color: "#8a94a7", textAlign: "center", marginTop: "20px" }}>
          No collaborations found.
        </p>
      )}
    </div>
  );
}