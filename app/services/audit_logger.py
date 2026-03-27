from sqlalchemy.orm import Session
from app.models.models import AuditLog
from datetime import datetime, timezone


def log_action(
    db: Session,
    candidate_id: int,
    action: str,
    actor: str = None,
    feedback_draft_id: int = None,
    original_rejection_reason: str = None,
    normalised_category: str = None,
    generated_draft: str = None,
    final_approved_version: str = None,
    email_delivery_status: str = None,
    notes: str = None,
) -> AuditLog:
    """Write a structured audit log entry."""
    entry = AuditLog(
        candidate_id=candidate_id,
        feedback_draft_id=feedback_draft_id,
        action=action,
        actor=actor,
        original_rejection_reason=original_rejection_reason,
        normalised_category=normalised_category,
        generated_draft=generated_draft,
        final_approved_version=final_approved_version,
        email_delivery_status=email_delivery_status,
        notes=notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_trail(db: Session, candidate_id: int) -> list:
    """Return all audit entries for a given candidate."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.candidate_id == candidate_id)
        .order_by(AuditLog.timestamp.asc())
        .all()
    )


def get_recent_actions(db: Session, limit: int = 50) -> list:
    """Return the most recent audit actions across all candidates."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .all()
    )
