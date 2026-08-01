import React from "react";
import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <div className="sidebar">
      <div className="brand">AIVOA<span>.AI</span></div>
      <nav>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Dashboard</NavLink>
        <NavLink to="/new" className={({ isActive }) => (isActive ? "active" : "")}>Log Complaint</NavLink>
      </nav>
    </div>
  );
}
