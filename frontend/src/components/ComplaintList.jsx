import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchComplaints } from "../store/complaintsSlice";

export default function ComplaintList() {
  const dispatch = useDispatch();
  const { items, listStatus } = useSelector((s) => s.complaints);

  useEffect(() => { dispatch(fetchComplaints()); }, [dispatch]);

  if (listStatus === "loading") return <p>Loading complaints…</p>;
  if (items.length === 0) return <div className="card empty-state">No complaints logged yet.</div>;

  return (
    <div className="card" style={{ padding: 0 }}>
      <table className="table">
        <thead>
          <tr>
            <th>Complaint #</th>
            <th>Product</th>
            <th>Category</th>
            <th>Risk</th>
            <th>Status</th>
            <th>Logged</th>
          </tr>
        </thead>
        <tbody>
          {items.map((c) => (
            <tr key={c.id}>
              <td>{c.complaint_number}</td>
              <td>{c.product_name}</td>
              <td>{c.complaint_category}</td>
              <td>{c.ai_risk_level ? <span className={`badge ${c.ai_risk_level}`}>{c.ai_risk_level}</span> : "—"}</td>
              <td>{c.status}</td>
              <td>{new Date(c.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
