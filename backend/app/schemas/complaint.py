from typing import Optional
from pydantic import BaseModel


class ExtractedFields(BaseModel):
    """What the LangGraph extraction node returns / what populates the form."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    affected_quantity: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    originating_site_block: Optional[str] = None
    impacted_npm: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None


class RiskAssessment(BaseModel):
    ai_severity: Optional[str] = None
    ai_suggested_next_action: Optional[str] = None
    ai_initial_risk_assessment: Optional[str] = None


class BonusInsights(BaseModel):
    ai_completeness_score: Optional[int] = None
    ai_duplicate_of: Optional[str] = None
    ai_capa_recommendation: Optional[str] = None
    ai_summary: Optional[str] = None


class CopilotParseResponse(BaseModel):
    reply: str
    fields: ExtractedFields
    risk: RiskAssessment
    bonus: BonusInsights


class CopilotChatRequest(BaseModel):
    message: str
    current_fields: ExtractedFields


class CopilotChatResponse(BaseModel):
    reply: str
    updated_fields: ExtractedFields
    changed_keys: list[str] = []


class ComplaintCommitRequest(ExtractedFields):
    ai_severity: Optional[str] = None
    ai_suggested_next_action: Optional[str] = None
    ai_initial_risk_assessment: Optional[str] = None
    ai_completeness_score: Optional[int] = None
    ai_capa_recommendation: Optional[str] = None
    ai_summary: Optional[str] = None
    source_raw_text: Optional[str] = None
    source_filename: Optional[str] = None


class ComplaintOut(ComplaintCommitRequest):
    id: str
    complaint_ref: str
    status: str

    class Config:
        from_attributes = True
