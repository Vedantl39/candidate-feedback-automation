from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Candidate
from app.models.schemas import CandidateCreate, CandidateResponse, CSVUploadResult
from app.services.rejection_classifier import classify_rejection_reason
from app.services.csv_ingestor import import_candidates_from_csv
from typing import List

router = APIRouter()


@router.post("/", response_model=CandidateResponse)
def create_candidate(candidate: CandidateCreate, db: Session = Depends(get_db)):
    """Create a single candidate record and classify their rejection reason."""
    raw_notes = " ".join(filter(None, [
        candidate.rejection_reason_raw,
        candidate.interviewer_notes,
        candidate.recruiter_notes,
    ]))

    category, _ = classify_rejection_reason(raw_notes)

    db_candidate = Candidate(
        name=candidate.name,
        email=candidate.email,
        role_applied=candidate.role_applied,
        stage_reached=candidate.stage_reached,
        rejection_reason_raw=candidate.rejection_reason_raw,
        rejection_category=category,
        interviewer_notes=candidate.interviewer_notes,
        recruiter_notes=candidate.recruiter_notes,
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate


@router.get("/", response_model=List[CandidateResponse])
def list_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all candidate records."""
    return db.query(Candidate).offset(skip).limit(limit).all()


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get a single candidate by ID."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.post("/upload/csv", response_model=CSVUploadResult)
async def upload_candidates_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV file of rejected candidates.
    Required columns: name, email, role_applied
    Optional: stage_reached, rejection_reason_raw, interviewer_notes, recruiter_notes
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    result = import_candidates_from_csv(text, db)
    return result
