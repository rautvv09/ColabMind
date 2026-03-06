import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAllCreators, createCollaboration } from "../services/api";
import "./CreateCollaboration.css";

export default function CreateCollaboration() {

  const navigate = useNavigate();

  const [creators, setCreators] = useState([]);

  const [form, setForm] = useState({
    creator_id: "",
    campaign_name: "",
    agreed_price: "",
    deadline: "",
    status: "pending"
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [type, setType] = useState("");

  /* -----------------------------
     Load creators
  ----------------------------- */

  useEffect(() => {
    loadCreators();
  }, []);

  const loadCreators = async () => {

    try {

      const res = await getAllCreators();

      if (res.data && res.data.data) {
        setCreators(res.data.data);
      } else {
        setCreators([]);
      }

    } catch (err) {

      console.error("Failed loading creators:", err);

    }

  };

  /* -----------------------------
     Handle form change
  ----------------------------- */

  const handleChange = (e) => {

    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: name === "agreed_price" ? Number(value) : value
    }));

  };

  /* -----------------------------
     Submit collaboration
  ----------------------------- */

  const handleSubmit = async (e) => {

    e.preventDefault();

    try {

      setLoading(true);
      setMessage("");

      if (!form.creator_id) {
        setType("error");
        setMessage("Please select a creator.");
        return;
      }

      const payload = {

        creator_id: form.creator_id,

        deal_type: "sponsored_post",

        agreed_price: Number(form.agreed_price),

        currency: "INR",

        deadline: form.deadline,

        status: form.status || "pending",

        notes: form.campaign_name,

        deliverables: [
          "1 Instagram Post",
          "1 Instagram Story"
        ]

      };

      console.log("Submitting payload:", payload);

      await createCollaboration(payload);

      setType("success");
      setMessage("Collaboration created successfully!");

      setTimeout(() => {
        navigate(`/collaborations/${form.creator_id}`);
      }, 1200);

    } catch (err) {

      console.error("Create collaboration error:", err.response?.data || err);

      setType("error");
      setMessage(
        err.response?.data?.message ||
        "Failed to create collaboration."
      );

    } finally {

      setLoading(false);

    }

  };

  return (

    <div className="create-collab-container">

      <div className="cm-card create-collab-card">

        <h1 className="page-title">Create Collaboration</h1>

        <p className="page-subtitle">
          Start a creator partnership deal
        </p>

        {message && (
          <div className={`collab-alert ${type}`}>
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="collab-form">

          {/* Creator */}

          <div className="collab-field">

            <label>Creator</label>

            <select
              name="creator_id"
              value={form.creator_id}
              onChange={handleChange}
              className="cm-input"
              required
            >

              <option value="">Select Creator</option>

              {creators.map((creator, index) => (

                <option
                  key={creator.creator_id || index}
                  value={creator.creator_id}
                >
                  {creator.username}
                </option>

              ))}

            </select>

          </div>

          {/* Campaign */}

          <div className="collab-field">

            <label>Campaign Name</label>

            <input
              type="text"
              name="campaign_name"
              value={form.campaign_name}
              onChange={handleChange}
              placeholder="Example: Fitness Promotion"
              className="cm-input"
              required
            />

          </div>

          {/* Price */}

          <div className="collab-field">

            <label>Agreed Price (₹)</label>

            <input
              type="number"
              name="agreed_price"
              value={form.agreed_price}
              onChange={handleChange}
              className="cm-input"
              required
            />

          </div>

          {/* Deadline */}

          <div className="collab-field">

            <label>Deadline</label>

            <input
              type="date"
              name="deadline"
              value={form.deadline}
              onChange={handleChange}
              className="cm-input"
              required
            />

          </div>

          {/* Status */}

          <div className="collab-field">

            <label>Status</label>

            <select
              name="status"
              value={form.status}
              onChange={handleChange}
              className="cm-input"
            >

              <option value="pending">Pending</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>

            </select>

          </div>

          {/* Submit */}

          <button
            type="submit"
            className="btn-cm create-btn"
            disabled={loading}
          >

            {loading
              ? "Creating Collaboration..."
              : "Create Collaboration"}

          </button>

        </form>

      </div>

    </div>

  );

}