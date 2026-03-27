from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class CandidateCreate(BaseModel):
    name: str
    email: str
    role_applied: str
    stage_reached: Optional[str] = None
    rejection_reason_raw: Optional[str] = None
    interviewer_notes: Optional[str] = None
    recruiter_notes: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    role_applied: str
    stage_reached: Optional[str]
    rejection_category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackDraftResponse(BaseModel):
    id: int
    candidate_id: int
    subject: str
    body: str
    status: str
    is_auto_eligible: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackApprovalRequest(BaseModel):
    approved_by: str
    edited_body: Optional[str] = None
    edited_subject: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    candidate_id: int
    action: str
    actor: Optional[str]
    normalised_category: Optional[str]
    email_delivery_status: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class CSVUploadResult(BaseModel):
    total_rows: int
    successful: int
    failed: int
    errors: list[str]
