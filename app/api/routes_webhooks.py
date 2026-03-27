from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import Candidate
from app.services.rejection_classifier import classify_rejection_reason
import os

router = APIRouter()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


class ATSWebhookPayload(BaseModel):
    candidate_name: str
    candidate_email: str
    role: str
    stage: Optional[str] = None
    rejection_reason: Optional[str] = None
    interviewer_notes: Optional[str] = None
    recruiter_notes: Optional[str] = None
    source: Optional[str] = "ats_webhook"


@router.post("/ats-rejection")
def receive_ats_rejection(
    payload: ATSWebhookPayload,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None),
):
    """
    Receive a rejection event from an ATS (Greenhouse, Lever, etc.)
    or from n8n workflow automation.
    """
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    raw_notes = " ".join(filter(None, [
        payload.rejection_reason,
        payload.interviewer_notes,
        payload.recruiter_notes,
    ]))

    category, _ = classify_rejection_reason(raw_notes)

    existing = db.query(Candidate).filter(
        Candidate.email == payload.candidate_email,
        Candidate.role_applied == payload.role,
    ).first()

    if existing:
        return {
            "message": "Candidate already exists",
            "candidate_id": existing.id,
            "action": "skipped",
        }

    candidate = Candidate(
        name=payload.candidate_name,
        email=payload.candidate_email,
        role_applied=payload.role,
        stage_reached=payload.stage,
        rejection_reason_raw=payload.rejection_reason,
        rejection_category=category,
        interviewer_notes=payload.interviewer_notes,
        recruiter_notes=payload.recruiter_notes,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "message": "Candidate created from webhook",
        "candidate_id": candidate.id,
        "rejection_category": category,
        "action": "created",
    }
