import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class ComplaintCreate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None
    manufacturing_site: Optional[str] = None
    source_channel: str = "manual"
    raw_text: Optional[str] = None
    original_filename: Optional[str] = None


class ComplaintUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None
    manufacturing_site: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    complaint_number: Optional[str]
    source_channel: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    product_name: Optional[str]
    batch_lot_number: Optional[str]
    complaint_category: Optional[str]
    complaint_description: Optional[str]
    manufacturing_site: Optional[str]
    date_of_complaint: Optional[dt.datetime]
    status: str
    priority: str

    ai_completeness_score: Optional[float] = None
    ai_missing_fields: Optional[str] = None
    ai_risk_level: Optional[str] = None
    ai_risk_rationale: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_root_cause_suggestions: Optional[str] = None
    ai_capa_suggestions: Optional[str] = None
    ai_duplicate_of: Optional[str] = None
    ai_duplicate_score: Optional[float] = None

    created_at: dt.datetime
    updated_at: dt.datetime


class ExtractResponse(BaseModel):
    """What the /ai/extract endpoint returns after parsing an uploaded
    PDF/email/image + running the LangGraph extraction node - this is what
    auto-populates the 'Log Customer Complaint' form fields in the UI."""
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None
    manufacturing_site: Optional[str] = None
    raw_text: str


class AnalyzeRequest(BaseModel):
    complaint_id: str


class AnalyzeResponse(BaseModel):
    completeness_score: float
    missing_fields: List[str]
    risk_level: str
    risk_rationale: str
    summary: str
    root_cause_suggestions: List[str]
    capa_suggestions: List[str]
    duplicate_of: Optional[str] = None
    duplicate_score: Optional[float] = None
