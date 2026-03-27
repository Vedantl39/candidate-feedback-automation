import csv
import io
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.models import Candidate
from app.services.rejection_classifier import classify_rejection_reason

REQUIRED_COLUMNS = {"name", "email", "role_applied"}

OPTIONAL_COLUMNS = {
    "stage_reached",
    "rejection_reason_raw",
    "interviewer_notes",
    "recruiter_notes",
}


def parse_csv_candidates(file_content: str) -> Tuple[List[dict], List[str]]:
    """
    Parse CSV content into a list of candidate dicts.
    Returns (candidates, errors).
    """
    candidates = []
    errors = []

    try:
        reader = csv.DictReader(io.StringIO(file_content))
    except Exception as e:
        return [], [f"Failed to parse CSV: {str(e)}"]

    headers = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - {h.strip().lower() for h in headers}
    if missing:
        return [], [f"Missing required columns: {', '.join(missing)}"]

    # Normalise headers
    fieldnames_map = {h.strip().lower(): h for h in (reader.fieldnames or [])}

    for i, row in enumerate(reader, start=2):
        normalised_row = {k.strip().lower(): v.strip() for k, v in row.items()}

        if not normalised_row.get("name") or not normalised_row.get("email"):
            errors.append(f"Row {i}: missing name or email — skipped")
            continue

        if "@" not in normalised_row.get("email", ""):
            errors.append(f"Row {i}: invalid email '{normalised_row['email']}' — skipped")
            continue

        candidates.append({
            "name": normalised_row["name"],
            "email": normalised_row["email"],
            "role_applied": normalised_row.get("role_applied", "Unknown Role"),
            "stage_reached": normalised_row.get("stage_reached"),
            "rejection_reason_raw": normalised_row.get("rejection_reason_raw"),
            "interviewer_notes": normalised_row.get("interviewer_notes"),
            "recruiter_notes": normalised_row.get("recruiter_notes"),
        })

    return candidates, errors


def import_candidates_from_csv(file_content: str, db: Session) -> dict:
    """
    Parse CSV and save candidates to the database.
    Runs rejection classification on import.
    Returns summary dict.
    """
    candidates, parse_errors = parse_csv_candidates(file_content)

    saved = 0
    save_errors = []

    for candidate_data in candidates:
        try:
            raw_notes = " ".join(filter(None, [
                candidate_data.get("rejection_reason_raw"),
                candidate_data.get("interviewer_notes"),
                candidate_data.get("recruiter_notes"),
            ]))

            category, _ = classify_rejection_reason(raw_notes)

            db_candidate = Candidate(
                name=candidate_data["name"],
                email=candidate_data["email"],
                role_applied=candidate_data["role_applied"],
                stage_reached=candidate_data.get("stage_reached"),
                rejection_reason_raw=candidate_data.get("rejection_reason_raw"),
                rejection_category=category,
                interviewer_notes=candidate_data.get("interviewer_notes"),
                recruiter_notes=candidate_data.get("recruiter_notes"),
            )
            db.add(db_candidate)
            db.commit()
            saved += 1

        except Exception as e:
            save_errors.append(f"Failed to save {candidate_data.get('name', 'unknown')}: {str(e)}")

    return {
        "total_rows": len(candidates) + len(parse_errors),
        "successful": saved,
        "failed": len(parse_errors) + len(save_errors),
        "errors": parse_errors + save_errors,
    }
