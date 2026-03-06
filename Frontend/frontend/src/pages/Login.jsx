import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginBrand } from "../services/api";
import "./Auth.css";

export default function Login() {

  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res  = await loginBrand(form);
      const data = res.data.data;
      sessionStorage.setItem("token",      data.token);
      sessionStorage.setItem("brand_id",   data.brand_id);
      sessionStorage.setItem("brand_name", data.brand_name);
      window.location.href = "/dashboard";
    } catch (err) {
      console.error(err);
      alert(err?.response?.data?.message || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      {/* ══ LEFT HERO ══ */}
      <div className="auth-hero">

        {/* Top: Logo */}
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

        {/* Middle: Headline + description */}
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

        {/* Bottom: Stats */}
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
          <h2>Welcome back</h2>
          <p className="switch">
            Don't have an account?{" "}
            <span onClick={() => navigate("/register")}>Sign up free</span>
          </p>

          <form onSubmit={handleSubmit}>
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
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              required
            />

            <button className="auth-btn" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

        </div>
      </div>

    </div>
  );
}
