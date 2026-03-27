import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            token_data = json.load(f)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(f"credentials.json not found at {CREDENTIALS_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def build_mime_message(to_email, subject, body):
    sender = SENDER_EMAIL
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to_email
    message.attach(MIMEText(body, "plain"))
    return message


def send_email(to_email, subject, body):
    try:
        service = get_gmail_service()
        mime_message = build_mime_message(to_email, subject, body)
        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"success": True, "message_id": result.get("id"), "status": "sent"}
    except HttpError as e:
        return {"success": False, "error": str(e), "status": "failed"}
    except Exception as e:
        return {"success": False, "error": str(e), "status": "error"}


def create_draft(to_email, subject, body):
    try:
        service = get_gmail_service()
        mime_message = build_mime_message(to_email, subject, body)
        raw = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        result = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        return {"success": True, "draft_id": result.get("id"), "status": "draft_created"}
    except Exception as e:
        return {"success": False, "error": str(e), "status": "failed"}


def mock_send_email(to_email, subject, body):
    print(f"\n--- MOCK EMAIL ---")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print(f"-----------------\n")
    return {"success": True, "message_id": f"mock_{hash(to_email+subject)}", "status": "mock_sent"}


def send_or_mock(to_email, subject, body, use_mock=False):
    if use_mock or os.getenv("MOCK_EMAIL", "false").lower() == "true":
        return mock_send_email(to_email, subject, body)
    return send_email(to_email, subject, body)
