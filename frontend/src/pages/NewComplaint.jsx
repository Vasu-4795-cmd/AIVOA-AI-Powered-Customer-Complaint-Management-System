import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import FileUpload from "../components/FileUpload";
import ComplaintForm from "../components/ComplaintForm";
import RiskAssessmentPanel from "../components/RiskAssessmentPanel";
import { resetDraft } from "../store/complaintsSlice";

export default function NewComplaint() {
  const dispatch = useDispatch();
  useEffect(() => () => dispatch(resetDraft()), [dispatch]);

  return (
    <div className="main">
      <div className="page-header">
        <div>
          <h1>Log Customer Complaint</h1>
          <p>Upload a complaint document or enter details manually — AI Copilot assists throughout.</p>
        </div>
      </div>

      <FileUpload />

      <div className="grid-2">
        <ComplaintForm />
        <RiskAssessmentPanel />
      </div>
    </div>
  );
}
