import React from "react";
import { useSelector } from "react-redux";

export default function RiskAssessmentPanel() {
  const { aiStatus, aiResult, aiError, activeComplaint } = useSelector((s) => s.complaints);

  if (!activeComplaint) {
    return (
      <div className="card empty-state">
        AI Copilot Risk Assessment will appear here once you submit a complaint.
      </div>
    );
  }

  return (
    <div className="card">
      <div className="copilot-header">
        <span className="dot" />
        <h3>AI Copilot — Risk Assessment</h3>
      </div>
      <p style={{ color: "#6b7280", fontSize: 13, marginTop: 0 }}>
        {activeComplaint.complaint_number}
      </p>

      {aiStatus === "loading" && <p>Running LangGraph agents on Groq (gemma2-9b-it / llama-3.3-70b)…</p>}
      {aiStatus === "failed" && <p className="error-text">{aiError}</p>}

      {aiResult && (
        <>
          <div className="section-title">Completeness</div>
          <div className="metric-row">
            <span>{aiResult.completeness_score}% complete</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${aiResult.completeness_score}%` }} />
          </div>
          {aiResult.missing_fields.length > 0 && (
            <p style={{ fontSize: 12.5, color: "#6b7280", marginTop: 6 }}>
              Missing: {aiResult.missing_fields.join(", ")}
            </p>
          )}

          <div className="section-title">Risk Classification</div>
          <span className={`badge ${aiResult.risk_level}`}>{aiResult.risk_level}</span>
          <p style={{ fontSize: 13.5, marginTop: 8 }}>{aiResult.risk_rationale}</p>

          <div className="section-title">Summary</div>
          <p style={{ fontSize: 13.5 }}>{aiResult.summary}</p>

          <div className="section-title">Root Cause Recommendations</div>
          <ul className="ai-list">
            {aiResult.root_cause_suggestions.map((r, i) => <li key={i}>{r}</li>)}
          </ul>

          <div className="section-title">CAPA Recommendations</div>
          <ul className="ai-list">
            {aiResult.capa_suggestions.map((r, i) => <li key={i}>{r}</li>)}
          </ul>

          <div className="section-title">Duplicate Detection</div>
          {aiResult.duplicate_of ? (
            <p style={{ fontSize: 13.5 }}>
              Possible duplicate of complaint <strong>{aiResult.duplicate_of}</strong>{" "}
              (similarity {Math.round((aiResult.duplicate_score || 0) * 100)}%)
            </p>
          ) : (
            <p style={{ fontSize: 13.5, color: "#6b7280" }}>No likely duplicate found.</p>
          )}
        </>
      )}
    </div>
  );
}
