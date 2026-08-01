import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.utils.file_parser import extract_text
from app.ai_agents.graph import extract_graph, analyze_graph

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/extract", response_model=schemas.ExtractResponse)
async def extract_from_file(file: UploadFile = File(...)):
    """Step 1 of the demo workflow: user uploads a complaint PDF/email/image.
    We OCR/parse it to raw text, then run the LangGraph extraction node
    (Groq gemma2-9b-it) to pull structured fields that auto-populate the
    'Log Customer Complaint' form on the frontend."""
    file_bytes = await file.read()
    raw_text = extract_text(file.filename, file_bytes)
    if not raw_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from this file. Try a .txt/.eml/.pdf, "
                   "or paste the complaint text manually.",
        )

    result = extract_graph.invoke({"raw_text": raw_text})
    fields = result.get("fields", {})
    return schemas.ExtractResponse(raw_text=raw_text, **fields)


@router.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze_complaint(payload: schemas.AnalyzeRequest, db: Session = Depends(get_db)):
    """Step 2 of the demo workflow: once the complaint form is submitted /
    saved, run the full LangGraph AI Copilot pipeline (completeness check,
    risk classification, summary, root cause, CAPA, duplicate detection)
    and populate the AI Copilot / Risk Assessment panel."""
    complaint = db.query(models.Complaint).filter(models.Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    fields = {
        "customer_name": complaint.customer_name,
        "product_name": complaint.product_name,
        "batch_lot_number": complaint.batch_lot_number,
        "complaint_category": complaint.complaint_category,
        "complaint_description": complaint.complaint_description,
        "manufacturing_site": complaint.manufacturing_site,
    }

    # brief context of other complaints for duplicate detection
    others = (
        db.query(models.Complaint)
        .filter(models.Complaint.id != complaint.id)
        .limit(25)
        .all()
    )
    existing = [
        {
            "id": o.id,
            "product": o.product_name,
            "batch": o.batch_lot_number,
            "description": o.complaint_description,
        }
        for o in others
    ]

    result = analyze_graph.invoke({"fields": fields, "existing_complaints": existing})

    # persist AI results onto the complaint record
    complaint.ai_completeness_score = result.get("completeness_score")
    complaint.ai_missing_fields = json.dumps(result.get("missing_fields", []))
    complaint.ai_risk_level = result.get("risk_level")
    complaint.ai_risk_rationale = result.get("risk_rationale")
    complaint.ai_summary = result.get("summary")
    complaint.ai_root_cause_suggestions = json.dumps(result.get("root_cause_suggestions", []))
    complaint.ai_capa_suggestions = json.dumps(result.get("capa_suggestions", []))
    complaint.ai_duplicate_of = result.get("duplicate_of")
    complaint.ai_duplicate_score = result.get("duplicate_score")

    # priority follows AI risk unless a human already overrode it
    risk_to_priority = {"Low": "Low", "Medium": "Medium", "High": "High", "Critical": "Critical"}
    complaint.priority = risk_to_priority.get(result.get("risk_level"), complaint.priority)

    db.add(complaint)
    for step in result.get("trace", []):
        db.add(models.ComplaintEvent(
            complaint_id=complaint.id,
            node_name=step["node"],
            output_snapshot=json.dumps(step["output"], default=str),
        ))
    db.commit()

    return schemas.AnalyzeResponse(
        completeness_score=result.get("completeness_score", 0),
        missing_fields=result.get("missing_fields", []),
        risk_level=result.get("risk_level", "Medium"),
        risk_rationale=result.get("risk_rationale", ""),
        summary=result.get("summary", ""),
        root_cause_suggestions=result.get("root_cause_suggestions", []),
        capa_suggestions=result.get("capa_suggestions", []),
        duplicate_of=result.get("duplicate_of"),
        duplicate_score=result.get("duplicate_score"),
    )
