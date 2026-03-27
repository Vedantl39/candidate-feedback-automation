import pytest
from unittest.mock import MagicMock, patch
from app.services.csv_ingestor import parse_csv_candidates, import_candidates_from_csv


VALID_CSV = """name,email,role_applied,stage_reached,rejection_reason_raw,interviewer_notes,recruiter_notes
Sarah Chen,sarah.chen@example.com,Data Analyst,Final Interview,Weak SQL depth,Limited hands-on SQL experience,Not enough technical depth
James Okafor,james.okafor@example.com,Product Manager,Second Interview,Level mismatch,Good instincts but junior scope,More mid-level than required
"""

MINIMAL_CSV = """name,email,role_applied
Tom Smith,tom@example.com,Engineer
"""

MISSING_REQUIRED_COLUMN_CSV = """name,email
Tom Smith,tom@example.com
"""

INVALID_EMAIL_CSV = """name,email,role_applied
Bad Person,not-an-email,Engineer
"""

EMPTY_ROW_CSV = """name,email,role_applied
,, 
Sarah Chen,sarah@example.com,Analyst
"""


class TestParseCsvCandidates:
    def test_valid_csv_parses_correctly(self):
        candidates, errors = parse_csv_candidates(VALID_CSV)
        assert len(candidates) == 2
        assert len(errors) == 0

    def test_candidate_fields_populated(self):
        candidates, _ = parse_csv_candidates(VALID_CSV)
        sarah = candidates[0]
        assert sarah["name"] == "Sarah Chen"
        assert sarah["email"] == "sarah.chen@example.com"
        assert sarah["role_applied"] == "Data Analyst"
        assert sarah["stage_reached"] == "Final Interview"
        assert "SQL" in sarah["rejection_reason_raw"]

    def test_minimal_csv_with_required_columns_only(self):
        candidates, errors = parse_csv_candidates(MINIMAL_CSV)
        assert len(candidates) == 1
        assert len(errors) == 0
        assert candidates[0]["stage_reached"] is None or candidates[0]["stage_reached"] == ""

    def test_missing_required_column_returns_error(self):
        candidates, errors = parse_csv_candidates(MISSING_REQUIRED_COLUMN_CSV)
        assert len(candidates) == 0
        assert len(errors) == 1
        assert "role_applied" in errors[0]

    def test_invalid_email_skipped_with_error(self):
        candidates, errors = parse_csv_candidates(INVALID_EMAIL_CSV)
        assert len(candidates) == 0
        assert any("invalid email" in e.lower() for e in errors)

    def test_empty_rows_skipped(self):
        candidates, errors = parse_csv_candidates(EMPTY_ROW_CSV)
        assert len(candidates) == 1
        assert candidates[0]["name"] == "Sarah Chen"

    def test_empty_string_returns_empty(self):
        candidates, errors = parse_csv_candidates("")
        assert candidates == [] or len(candidates) == 0

    def test_headers_are_case_insensitive(self):
        csv_upper = "NAME,EMAIL,ROLE_APPLIED\nJohn Doe,john@example.com,Engineer\n"
        candidates, errors = parse_csv_candidates(csv_upper)
        assert len(candidates) == 1
        assert candidates[0]["name"] == "John Doe"


class TestImportCandidatesFromCsv:
    def test_import_creates_db_records(self):
        mock_db = MagicMock()

        result = import_candidates_from_csv(VALID_CSV, mock_db)

        assert result["successful"] == 2
        assert result["failed"] == 0
        assert mock_db.add.call_count == 2
        assert mock_db.commit.call_count == 2

    def test_import_result_structure(self):
        mock_db = MagicMock()
        result = import_candidates_from_csv(VALID_CSV, mock_db)

        assert "total_rows" in result
        assert "successful" in result
        assert "failed" in result
        assert "errors" in result

    def test_import_handles_db_failure_gracefully(self):
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("DB connection lost")

        result = import_candidates_from_csv(VALID_CSV, mock_db)

        assert result["failed"] > 0
        assert len(result["errors"]) > 0

    def test_import_with_invalid_rows_counts_correctly(self):
        mixed_csv = VALID_CSV + ",,\n"
        mock_db = MagicMock()
        result = import_candidates_from_csv(mixed_csv, mock_db)

        assert result["successful"] == 2
