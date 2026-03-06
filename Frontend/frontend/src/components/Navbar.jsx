import React from "react";
import { NavLink } from "react-router-dom";
import {
  RiDashboardLine,
  RiSearchLine,
  RiMoneyDollarCircleLine,
  RiTeamLine
} from "react-icons/ri";

export default function Navbar() {

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
      name: "Collaborations",
      path: "/create-collaboration",
      icon: <RiTeamLine size={20}/>
    }
  ];

  return (

    <aside className="sidebar">

      {/* Logo */}

      <div style={{
        fontSize: "1.4rem",
        fontWeight: 800,
        marginBottom: "40px",
        fontFamily: "'Syne',sans-serif"
      }}>
        Creator<span className="gradient-text">AI</span>
      </div>

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

      {/* Footer */}

      <div style={{
        marginTop: "auto",
        fontSize: "0.75rem",
        color: "var(--text-muted)",
        textAlign: "center"
      }}>
        Creator Analytics Platform
      </div>

    </aside>

  );
}