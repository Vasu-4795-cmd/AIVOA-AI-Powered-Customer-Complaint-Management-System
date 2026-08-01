import React from "react";
import { Link } from "react-router-dom";
import ComplaintList from "../components/ComplaintList";

export default function Dashboard() {
  return (
    <div className="main">
      <div className="page-header">
        <div>
          <h1>Customer Complaints</h1>
          <p>Pharmaceutical QMS — Customer Complaint Management</p>
        </div>
        <Link to="/new" className="btn">+ Log New Complaint</Link>
      </div>
      <ComplaintList />
    </div>
  );
}
