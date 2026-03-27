import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = "onboarding@resend.dev"


def send_or_mock(to_email: str, subject: str, body: str, use_mock: bool = False) -> dict:
    if use_mock or os.getenv("MOCK_EMAIL", "false").lower() == "true":
        print(f"MOCK EMAIL to {to_email}: {subject}")
        return {"success": True, "message_id": f"mock_{hash(to_email)}", "status": "mock_sent"}

    try:
        response = resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": to_email,
            "subject": subject,
            "text": body,
        })
        return {"success": True, "message_id": response["id"], "status": "sent"}
    except Exception as e:
        return {"success": False, "error": str(e), "status": "failed"}


def send_email(to_email: str, subject: str, body: str) -> dict:
    return send_or_mock(to_email, subject, body)


def create_draft(to_email: str, subject: str, body: str) -> dict:
    return {"success": True, "draft_id": "resend_no_drafts", "status": "draft_created"}


def mock_send_email(to_email: str, subject: str, body: str) -> dict:
    return send_or_mock(to_email, subject, body, use_mock=True)
