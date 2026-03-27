from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models.models import Candidate, FeedbackDraft, FeedbackStatus
from app.models.schemas import FeedbackDraftResponse, FeedbackApprovalRequest
from app.services.feedback_engine import generate_feedback_email
from app.services.rejection_classifier import classify_rejection_reason
from app.services.email_service import send_or_mock
from app.services.audit_logger import log_action
from typing import List
import os

router = APIRouter()

WORKFLOW_MODE = os.getenv("WORKFLOW_MODE", "manual")


@router.post("/generate/{candidate_id}", response_model=FeedbackDraftResponse)
def generate_feedback(candidate_id: int, db: Session = Depends(get_db)):
    """Generate a feedback draft for a specific candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    existing = db.query(FeedbackDraft).filter(
        FeedbackDraft.candidate_id == candidate_id,
        FeedbackDraft.status == FeedbackStatus.PENDING,
    ).first()
    if existing:
        return existing

    raw_notes = " ".join(filter(None, [
        candidate.rejection_reason_raw,
        candidate.interviewer_notes,
        candidate.recruiter_notes,
    ]))
    category, is_auto_eligible = classify_rejection_reason(raw_notes)

    if not candidate.rejection_category:
        candidate.rejection_category = category
        db.commit()

    feedback = generate_feedback_email(
        candidate_name=candidate.name,
        role=candidate.role_applied,
        rejection_category=category,
        stage_reached=candidate.stage_reached,
    )

    draft = FeedbackDraft(
        candidate_id=candidate_id,
        subject=feedback["subject"],
        body=feedback["body"],
        status=FeedbackStatus.PENDING,
        is_auto_eligible=is_auto_eligible,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    log_action(
        db=db,
        candidate_id=candidate_id,
        feedback_draft_id=draft.id,
        action="feedback_generated",
        original_rejection_reason=raw_notes,
        normalised_category=category,
        generated_draft=feedback["body"],
    )

    return draft


@router.post("/generate-all")
def generate_feedback_for_all_pending(db: Session = Depends(get_db)):
    """Generate feedback drafts for all candidates without one."""
    candidates = db.query(Candidate).all()
    drafted_ids = {d.candidate_id for d in db.query(FeedbackDraft).all()}
    pending = [c for c in candidates if c.id not in drafted_ids]

    results = {"generated": 0, "failed": 0, "errors": []}
    for candidate in pending:
        try:
            raw_notes = " ".join(filter(None, [
                candidate.rejection_reason_raw,
                candidate.interviewer_notes,
                candidate.recruiter_notes,
            ]))
            category, is_auto_eligible = classify_rejection_reason(raw_notes)
            feedback = generate_feedback_email(
                candidate_name=candidate.name,
                role=candidate.role_applied,
                rejection_category=category,
                stage_reached=candidate.stage_reached,
            )
            draft = FeedbackDraft(
                candidate_id=candidate.id,
                subject=feedback["subject"],
                body=feedback["body"],
                status=FeedbackStatus.PENDING,
                is_auto_eligible=is_auto_eligible,
            )
            db.add(draft)
            db.commit()
            results["generated"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Candidate {candidate.id}: {str(e)}")

    return results


@router.get("/pending", response_model=List[FeedbackDraftResponse])
def list_pending_feedback(db: Session = Depends(get_db)):
    """List all feedback drafts awaiting HR approval."""
    return db.query(FeedbackDraft).filter(
        FeedbackDraft.status == FeedbackStatus.PENDING
    ).all()


@router.get("/all", response_model=List[FeedbackDraftResponse])
def list_all_feedback(db: Session = Depends(get_db)):
    """List all feedback drafts across all statuses."""
    return db.query(FeedbackDraft).order_by(FeedbackDraft.created_at.desc()).all()


@router.get("/{draft_id}", response_model=FeedbackDraftResponse)
def get_feedback_draft(draft_id: int, db: Session = Depends(get_db)):
    """Get a specific feedback draft."""
    draft = db.query(FeedbackDraft).filter(FeedbackDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Feedback draft not found")
    return draft


@router.post("/{draft_id}/approve", response_model=FeedbackDraftResponse)
def approve_and_send_feedback(
    draft_id: int,
    approval: FeedbackApprovalRequest,
    db: Session = Depends(get_db),
):
    """HR approves and triggers sending of a feedback email."""
    draft = db.query(FeedbackDraft).filter(FeedbackDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft.status == FeedbackStatus.SENT:
        raise HTTPException(status_code=400, detail="This feedback has already been sent")

    if approval.edited_body:
        draft.body = approval.edited_body
    if approval.edited_subject:
        draft.subject = approval.edited_subject

    draft.approved_by = approval.approved_by
    draft.approved_at = datetime.now(timezone.utc)

    candidate = db.query(Candidate).filter(Candidate.id == draft.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    email_result = send_or_mock(
        to_email=candidate.email,
        subject=draft.subject,
        body=draft.body,
    )

    if email_result["success"]:
        draft.status = FeedbackStatus.SENT
        draft.sent_at = datetime.now(timezone.utc)
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Email sending failed: {email_result.get('error', 'Unknown error')}",
        )

    db.commit()
    db.refresh(draft)

    log_action(
        db=db,
        candidate_id=draft.candidate_id,
        feedback_draft_id=draft.id,
        action="feedback_sent",
        actor=approval.approved_by,
        final_approved_version=draft.body,
        email_delivery_status=email_result["status"],
    )

    return draft


@router.post("/{draft_id}/reject")
def reject_feedback_draft(draft_id: int, db: Session = Depends(get_db)):
    """Mark a draft as rejected so it can be regenerated."""
    draft = db.query(FeedbackDraft).filter(FeedbackDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.status = FeedbackStatus.REJECTED
    db.commit()
    return {"message": "Draft marked as rejected"}
