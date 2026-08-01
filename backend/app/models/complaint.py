import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComplaintStatus(str, enum.Enum):
    pending_triage = "pending_triage"
    ready_to_commit = "ready_to_commit"
    committed = "committed"


class Severity(str, enum.Enum):
    minor = "Minor"
    major = "Major"
    critical = "Critical"


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Complaint(Base):
    """
    Maps 1:1 to the 'Log Customer Complaint' form sections shown in the
    reference UI:
      1. Origin & Customer Details
      2. Product & Batch Identification
      3. Facility & Material Impact
      4. Defect Analysis + AI Copilot Risk Assessment
    """
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    complaint_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # 1. Origin & Customer Details
    complaint_source: Mapped[str] = mapped_column(String(64), nullable=True)   # Email / Pharmacy / Phone / Portal
    customer_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # 2. Product & Batch Identification
    product_name: Mapped[str] = mapped_column(String(255), nullable=True)
    product_strength: Mapped[str] = mapped_column(String(64), nullable=True)
    batch_number: Mapped[str] = mapped_column(String(64), nullable=True)
    affected_quantity: Mapped[str] = mapped_column(String(64), nullable=True)
    manufacturing_date: Mapped[str] = mapped_column(String(32), nullable=True)
    expiry_date: Mapped[str] = mapped_column(String(32), nullable=True)

    # 3. Facility & Material Impact
    originating_site_block: Mapped[str] = mapped_column(String(64), nullable=True)  # Manufacturing / Packaging / Warehouse / QC Lab
    impacted_npm: Mapped[str] = mapped_column(String(255), nullable=True)           # Non-Product Materials

    # 4. Defect Analysis
    complaint_category: Mapped[str] = mapped_column(String(128), nullable=True)
    complaint_description: Mapped[str] = mapped_column(Text, nullable=True)

    # AI Copilot Risk Assessment
    ai_severity: Mapped[str] = mapped_column(Enum(Severity), nullable=True)
    ai_suggested_next_action: Mapped[str] = mapped_column(String(255), nullable=True)
    ai_initial_risk_assessment: Mapped[str] = mapped_column(Text, nullable=True)

    # Bonus AI fields
    ai_completeness_score: Mapped[int] = mapped_column(nullable=True)      # 0-100
    ai_duplicate_of: Mapped[str] = mapped_column(String(36), nullable=True)
    ai_capa_recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(Enum(ComplaintStatus), default=ComplaintStatus.pending_triage)

    source_raw_text: Mapped[str] = mapped_column(Text, nullable=True)   # original pasted/parsed text, for audit trail
    source_filename: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
