import React from "react";
import { NavLink } from "react-router-dom";

import {
  RiDashboardLine,
  RiSearchLine,
  RiMoneyDollarCircleLine,
  RiTeamLine,
  RiLogoutBoxLine
} from "react-icons/ri";

export default function Navbar() {

  const brandName = sessionStorage.getItem("brand_name");

  const handleLogout = () => {

    sessionStorage.clear();

    window.location.href = "/login";

  };

  const navItems = [

    {
      name: "Dashboard",
      path: "/dashboard",
      icon: <RiDashboardLine size={20}/>
    },

    {
      name: "Search Creators",
      path: "/search",
      icon: <RiSearchLine size={20}/>
    },

    {
      name: "Price Predictor",
      path: "/price-predictor",
      icon: <RiMoneyDollarCircleLine size={20}/>
    },

    {
      name: "Create Collaboration",
      path: "/create-collaboration",
      icon: <RiTeamLine size={20}/>
    },

    {
      name: "Collaboration List",
      path: "/collaborations",
      icon: <RiTeamLine size={20}/>
    }

  ];

  return (

    <aside className="sidebar">

      {/* Logo */}

      <div
        style={{
          fontSize: "1.4rem",
          fontWeight: 800,
          marginBottom: "20px",
          fontFamily: "'Syne',sans-serif"
        }}
      >
        Creator<span className="gradient-text">AI</span>
      </div>

      {/* Brand name */}

      {brandName && (
        <div
          style={{
            marginBottom: "30px",
            fontSize: "0.8rem",
            color: "var(--text-secondary)"
          }}
        >
          Logged in as
          <div style={{ fontWeight: 600 }}>
            {brandName}
          </div>
        </div>
      )}

      {/* Navigation */}

      <nav style={{ display: "flex", flexDirection: "column", gap: 6 }}>

        {navItems.map((item) => (

          <NavLink
            key={item.name}
            to={item.path}
            className={({isActive}) =>
              `nav-link ${isActive ? "active" : ""}`
            }
          >

            {item.icon}

            <span className="nav-label">
              {item.name}
            </span>

          </NavLink>

        ))}

      </nav>

      {/* Logout Button */}

      <button
        onClick={handleLogout}
        className="nav-link"
        style={{
          marginTop: "auto",
          border: "none",
          background: "transparent",
          cursor: "pointer"
        }}
      >

        <RiLogoutBoxLine size={20}/>

        <span className="nav-label">
          Logout
        </span>

      </button>

      {/* Footer */}

      <div
        style={{
          marginTop: "20px",
          fontSize: "0.75rem",
          color: "var(--text-muted)",
          textAlign: "center"
        }}
      >
        Creator Analytics Platform
      </div>

    </aside>

  );

}