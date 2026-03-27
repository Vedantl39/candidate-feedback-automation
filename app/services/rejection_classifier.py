import re
from typing import Tuple

REJECTION_CATEGORIES = {
    "skills_gap": [
        "sql", "python", "excel", "coding", "technical", "skill", "experience with",
        "proficiency", "hands-on", "lacks", "weak", "gap", "insufficient technical",
    ],
    "level_mismatch": [
        "level", "senior", "junior", "too junior", "too senior", "overqualified",
        "underqualified", "years of experience", "scope", "complexity",
    ],
    "role_fit": [
        "not a fit", "role fit", "culture fit", "team fit", "alignment", "not aligned",
        "different direction", "expectations", "requirements don't match",
    ],
    "communication_concerns": [
        "communication", "articulate", "presentation", "stakeholder", "clarity",
        "english", "language", "explain", "concise", "verbose",
    ],
    "domain_experience": [
        "domain", "industry", "sector", "fintech", "healthcare", "saas", "b2b",
        "background", "context", "vertical", "market knowledge",
    ],
    "stronger_candidate": [
        "stronger candidate", "more competitive", "stronger pool", "better fit",
        "another candidate", "moved forward with", "competitive process",
    ],
    "logistics_mismatch": [
        "visa", "work authorisation", "work authorization", "location", "remote",
        "relocation", "timezone", "availability", "start date", "salary", "compensation",
    ],
}

AUTO_ELIGIBLE_CATEGORIES = {
    "skills_gap",
    "level_mismatch",
    "domain_experience",
    "stronger_candidate",
}

SENSITIVE_CATEGORIES = {
    "communication_concerns",
    "logistics_mismatch",
    "role_fit",
}


def classify_rejection_reason(raw_notes: str) -> Tuple[str, bool]:
    """
    Classify raw rejection notes into a standard category.
    Returns (category, is_auto_eligible).
    """
    if not raw_notes:
        return "role_fit", False

    text = raw_notes.lower()
    scores = {category: 0 for category in REJECTION_CATEGORIES}

    for category, keywords in REJECTION_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text:
                scores[category] += 1

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        best_category = "role_fit"

    is_auto_eligible = best_category in AUTO_ELIGIBLE_CATEGORIES

    return best_category, is_auto_eligible


def get_category_display_name(category: str) -> str:
    display_names = {
        "skills_gap": "Skills Gap",
        "level_mismatch": "Level Mismatch",
        "role_fit": "Role Fit",
        "communication_concerns": "Communication Concerns",
        "domain_experience": "Limited Domain Experience",
        "stronger_candidate": "Stronger Competing Candidate",
        "logistics_mismatch": "Logistics or Work Authorisation Mismatch",
    }
    return display_names.get(category, category.replace("_", " ").title())


def get_safe_category_summary(category: str, role: str) -> str:
    """
    Returns a safe, HR-approved summary description per category.
    Used as input context for the LLM feedback generator.
    """
    summaries = {
        "skills_gap": f"The candidate did not demonstrate sufficient technical depth required for the {role} role.",
        "level_mismatch": f"The experience level of the candidate did not match what the {role} role requires.",
        "role_fit": f"After careful review, the team felt the candidate's profile was not the right match for the {role} role at this time.",
        "communication_concerns": f"The team felt there were aspects of communication and cross-functional presentation that did not meet the requirements for the {role} role.",
        "domain_experience": f"The candidate had limited domain experience in areas central to the {role} role.",
        "stronger_candidate": f"Following a competitive process, the team moved forward with a candidate whose profile more closely matched the requirements for the {role} role.",
        "logistics_mismatch": f"Unfortunately, there were logistical factors that prevented moving forward with the candidate for the {role} role.",
    }
    return summaries.get(category, summaries["role_fit"])
