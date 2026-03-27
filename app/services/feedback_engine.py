import os
from anthropic import Anthropic
from app.services.rejection_classifier import get_safe_category_summary, get_category_display_name
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

SYSTEM_PROMPT = """You are an HR communications assistant. Your only job is to write professional, 
respectful, and constructive rejection feedback emails for job candidates.

STRICT RULES — you must follow all of these without exception:
1. Never invent reasons not present in the context provided to you.
2. Never mention, imply, or reference protected characteristics (age, gender, race, nationality, 
   religion, disability, pregnancy, marital status, sexual orientation).
3. Never use language that could create legal liability (e.g. "you failed", "you were rejected", 
   "you were not good enough").
4. Always use respectful, encouraging, and professional language.
5. Keep feedback specific enough to be useful, but not so specific it reveals confidential 
   internal deliberations.
6. Do not mention other candidates by name or compare directly.
7. Keep the email concise: opening, one or two feedback sentences, optional improvement tip, close.
8. Use the candidate's first name only.
9. Do not fabricate compliments or positives not indicated in the context.
10. Output only the email body text — no subject line, no markdown, no extra commentary.
"""


def generate_feedback_email(
    candidate_name: str,
    role: str,
    rejection_category: str,
    stage_reached: str = None,
    tone: str = "professional",
) -> dict:
    """
    Generate a candidate-friendly feedback email using Claude.
    Returns dict with subject and body.
    """
    first_name = candidate_name.split()[0]
    category_summary = get_safe_category_summary(rejection_category, role)
    stage_context = f"The candidate reached the {stage_reached} stage." if stage_reached else ""

    user_prompt = f"""Write a rejection feedback email for the following candidate:

Candidate first name: {first_name}
Role applied for: {role}
{stage_context}
Rejection reason (internal summary): {category_summary}
Tone: {tone}

Write a warm, professional rejection email. Include:
- A brief thank you for their time
- A respectful explanation aligned to the rejection reason above
- One optional development suggestion (only if it feels natural)
- A positive close wishing them well

Remember: output only the email body text, starting with "Hi {first_name},"."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    body = message.content[0].text.strip()
    subject = generate_subject_line(first_name, role)

    return {
        "subject": subject,
        "body": body,
    }


def generate_subject_line(candidate_name: str, role: str) -> str:
    """Generate a neutral, professional subject line."""
    return f"Update on your application for {role}"


def generate_feedback_batch(candidates: list) -> list:
    """
    Generate feedback for a list of candidates.
    Each candidate dict should have: name, role_applied, rejection_category, stage_reached.
    Returns list of dicts with candidate_id, subject, body.
    """
    results = []
    for candidate in candidates:
        try:
            feedback = generate_feedback_email(
                candidate_name=candidate["name"],
                role=candidate["role_applied"],
                rejection_category=candidate["rejection_category"],
                stage_reached=candidate.get("stage_reached"),
            )
            results.append({
                "candidate_id": candidate["id"],
                "subject": feedback["subject"],
                "body": feedback["body"],
                "success": True,
            })
        except Exception as e:
            results.append({
                "candidate_id": candidate["id"],
                "error": str(e),
                "success": False,
            })
    return results
