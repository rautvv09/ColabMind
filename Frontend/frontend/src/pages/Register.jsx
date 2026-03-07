import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registerBrand } from "../services/api";
import "./Auth.css";

export default function Register() {

  const navigate = useNavigate();
  const [form, setForm] = useState({ brand_name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await registerBrand(form);
      alert("Registration successful. Please login.");
      navigate("/login");
    } catch (err) {
      console.error(err);
      alert("Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      {/* ══ LEFT HERO ══ */}
      <div className="auth-hero">

        <div className="auth-logo">
          <div className="auth-logo-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <rect x="2"  y="2"  width="9" height="9" rx="2" fill="white" opacity="0.95"/>
              <rect x="13" y="2"  width="9" height="9" rx="2" fill="white" opacity="0.65"/>
              <rect x="2"  y="13" width="9" height="9" rx="2" fill="white" opacity="0.65"/>
              <rect x="13" y="13" width="9" height="9" rx="2" fill="white" opacity="0.35"/>
            </svg>
          </div>
          CollabMind
        </div>

        <div className="hero-content">
          <h1>
            Connect with <span>top creators.</span><br />
            Grow faster.
          </h1>
          <p>
            The AI-powered platform that matches brands with
            the right influencers — with predictive pricing and risk
            intelligence.
          </p>
        </div>

        <div className="auth-stats">
          <div>
            <h3>12K+</h3>
            <span>CREATORS</span>
          </div>
          <div>
            <h3>98%</h3>
            <span>MATCH RATE</span>
          </div>
          <div>
            <h3>3.2x</h3>
            <span>AVG. ROI</span>
          </div>
        </div>

      </div>

      {/* ══ RIGHT FORM ══ */}
      <div className="auth-form-area">
        <div className="auth-card">

          <p className="portal">BRAND PORTAL</p>
          <h2>Create Account</h2>
          <p className="switch">
            Already have an account?{" "}
            <span onClick={() => navigate("/login")}>Sign in</span>
          </p>

          <form onSubmit={handleSubmit}>
            <label>BRAND NAME</label>
            <input
              type="text"
              name="brand_name"
              placeholder="Nike"
              value={form.brand_name}
              onChange={handleChange}
              required
            />

            <label>EMAIL ADDRESS</label>
            <input
              type="email"
              name="email"
              placeholder="brand@company.com"
              value={form.email}
              onChange={handleChange}
              required
            />

            <label>PASSWORD</label>
            <input
              type="password"
              name="password"
              placeholder="Create password"
              value={form.password}
              onChange={handleChange}
              required
            />

            <button className="auth-btn" disabled={loading}>
              {loading ? "Creating account..." : "Sign up"}
            </button>
          </form>

        </div>
      </div>

    </div>
  );
}