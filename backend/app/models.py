import uuid
import datetime as dt

from sqlalchemy import (
    Column, String, Text, DateTime, Float, ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import CHAR, TypeDecorator

from app.database import Base


class GUID(TypeDecorator):
    """Platform-independent UUID type so the same model works on
    Postgres (native UUID) and MySQL (CHAR(36)) without code changes."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


def gen_uuid():
    return str(uuid.uuid4())


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(GUID(), primary_key=True, default=gen_uuid)
    complaint_number = Column(String(50), unique=True, index=True)

    # Source of complaint
    source_channel = Column(String(30), default="manual")  # manual, email, pdf_upload
    raw_text = Column(Text, nullable=True)          # extracted text from upload
    original_filename = Column(String(255), nullable=True)

    # Core QMS complaint fields (aligned with pharma CAPA/complaint modules)
    customer_name = Column(String(255))
    customer_email = Column(String(255), nullable=True)
    product_name = Column(String(255))
    batch_lot_number = Column(String(100), nullable=True)
    complaint_category = Column(String(100))   # e.g. Quality, Packaging, Adverse Event, Efficacy
    complaint_description = Column(Text)
    date_of_complaint = Column(DateTime, default=dt.datetime.utcnow)
    manufacturing_site = Column(String(255), nullable=True)

    status = Column(String(30), default="Open")  # Open, Under Investigation, CAPA Assigned, Closed
    priority = Column(String(20), default="Medium")

    # AI-derived fields (AI Copilot / Risk Assessment)
    ai_completeness_score = Column(Float, nullable=True)
    ai_missing_fields = Column(Text, nullable=True)      # JSON string list
    ai_risk_level = Column(String(20), nullable=True)    # Low, Medium, High, Critical
    ai_risk_rationale = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_root_cause_suggestions = Column(Text, nullable=True)   # JSON string list
    ai_capa_suggestions = Column(Text, nullable=True)         # JSON string list
    ai_duplicate_of = Column(GUID(), nullable=True)
    ai_duplicate_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    events = relationship("ComplaintEvent", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintEvent(Base):
    """Audit trail of the LangGraph agent steps run against a complaint -
    useful to show the end-to-end AI workflow during the demo walkthrough."""
    __tablename__ = "complaint_events"

    id = Column(GUID(), primary_key=True, default=gen_uuid)
    complaint_id = Column(GUID(), ForeignKey("complaints.id"))
    node_name = Column(String(100))     # e.g. completeness_checker, risk_classifier
    input_snapshot = Column(Text, nullable=True)
    output_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    complaint = relationship("Complaint", back_populates="events")
