from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class FeedbackStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    REJECTED = "rejected"


class WorkflowMode(str, enum.Enum):
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    AUTO = "auto"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    role_applied = Column(String(255), nullable=False)
    stage_reached = Column(String(100))
    rejection_reason_raw = Column(Text)
    rejection_category = Column(String(100))
    interviewer_notes = Column(Text)
    recruiter_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FeedbackDraft(Base):
    __tablename__ = "feedback_drafts"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True, nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default=FeedbackStatus.PENDING)
    is_auto_eligible = Column(Boolean, default=False)
    approved_by = Column(String(255))
    approved_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True, nullable=False)
    feedback_draft_id = Column(Integer, index=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(255))
    original_rejection_reason = Column(Text)
    normalised_category = Column(String(100))
    generated_draft = Column(Text)
    final_approved_version = Column(Text)
    email_delivery_status = Column(String(50))
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
