import pytest
from app.services.rejection_classifier import (
    classify_rejection_reason,
    get_category_display_name,
    get_safe_category_summary,
    AUTO_ELIGIBLE_CATEGORIES,
    SENSITIVE_CATEGORIES,
)


class TestClassifyRejectionReason:
    def test_skills_gap_detection(self):
        notes = "Good profile but weak SQL depth and limited Python experience"
        category, auto = classify_rejection_reason(notes)
        assert category == "skills_gap"
        assert auto is True

    def test_level_mismatch_detection(self):
        notes = "Candidate is too junior for the senior level scope required"
        category, auto = classify_rejection_reason(notes)
        assert category == "level_mismatch"
        assert auto is True

    def test_communication_concerns_not_auto(self):
        notes = "Communication style did not meet stakeholder expectations"
        category, auto = classify_rejection_reason(notes)
        assert category == "communication_concerns"
        assert auto is False

    def test_stronger_candidate_detection(self):
        notes = "Moved forward with a stronger candidate from the competitive process"
        category, auto = classify_rejection_reason(notes)
        assert category == "stronger_candidate"
        assert auto is True

    def test_domain_experience_detection(self):
        notes = "Limited domain experience in fintech and financial services sector"
        category, auto = classify_rejection_reason(notes)
        assert category == "domain_experience"
        assert auto is True

    def test_logistics_mismatch_not_auto(self):
        notes = "Visa and work authorisation requirements not met for this location"
        category, auto = classify_rejection_reason(notes)
        assert category == "logistics_mismatch"
        assert auto is False

    def test_empty_notes_returns_default(self):
        category, auto = classify_rejection_reason("")
        assert category == "role_fit"
        assert auto is False

    def test_none_notes_returns_default(self):
        category, auto = classify_rejection_reason(None)
        assert category == "role_fit"
        assert auto is False

    def test_unrecognised_notes_returns_role_fit(self):
        notes = "The quick brown fox jumps over the lazy dog"
        category, auto = classify_rejection_reason(notes)
        assert category == "role_fit"

    def test_auto_eligible_categories_are_correct(self):
        assert "skills_gap" in AUTO_ELIGIBLE_CATEGORIES
        assert "communication_concerns" not in AUTO_ELIGIBLE_CATEGORIES
        assert "logistics_mismatch" not in AUTO_ELIGIBLE_CATEGORIES

    def test_sensitive_categories_not_auto(self):
        for cat in SENSITIVE_CATEGORIES:
            assert cat not in AUTO_ELIGIBLE_CATEGORIES


class TestDisplayNames:
    def test_display_name_formatting(self):
        assert get_category_display_name("skills_gap") == "Skills Gap"
        assert get_category_display_name("level_mismatch") == "Level Mismatch"
        assert get_category_display_name("logistics_mismatch") == "Logistics or Work Authorisation Mismatch"

    def test_unknown_category_falls_back(self):
        result = get_category_display_name("unknown_category")
        assert result == "Unknown Category"


class TestSafeCategorySummary:
    def test_summary_contains_role(self):
        summary = get_safe_category_summary("skills_gap", "Data Analyst")
        assert "Data Analyst" in summary

    def test_summary_no_protected_characteristics(self):
        sensitive_terms = ["age", "gender", "race", "nationality", "religion", "disability"]
        for cat in ["skills_gap", "level_mismatch", "role_fit", "communication_concerns"]:
            summary = get_safe_category_summary(cat, "Engineer")
            for term in sensitive_terms:
                assert term not in summary.lower()

    def test_all_categories_have_summary(self):
        categories = [
            "skills_gap", "level_mismatch", "role_fit",
            "communication_concerns", "domain_experience",
            "stronger_candidate", "logistics_mismatch",
        ]
        for cat in categories:
            summary = get_safe_category_summary(cat, "Test Role")
            assert len(summary) > 10
