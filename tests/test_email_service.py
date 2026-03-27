import pytest
from unittest.mock import patch, MagicMock
from app.services.email_service import mock_send_email, send_or_mock, build_mime_message


class TestMockSendEmail:
    def test_mock_send_returns_success(self):
        result = mock_send_email("test@example.com", "Test Subject", "Test body")
        assert result["success"] is True
        assert result["status"] == "mock_sent"
        assert "message_id" in result

    def test_mock_send_returns_message_id(self):
        result = mock_send_email("a@b.com", "Subject", "Body")
        assert result["message_id"] is not None

    def test_mock_send_different_emails_different_ids(self):
        r1 = mock_send_email("one@example.com", "Subject", "Body")
        r2 = mock_send_email("two@example.com", "Subject", "Body")
        assert r1["message_id"] != r2["message_id"]


class TestBuildMimeMessage:
    def test_mime_message_has_correct_headers(self):
        msg = build_mime_message(
            to_email="candidate@example.com",
            subject="Update on your application",
            body="Hi Sarah, thank you for your time.",
            from_email="hr@company.com",
        )
        assert msg["To"] == "candidate@example.com"
        assert msg["Subject"] == "Update on your application"
        assert msg["From"] == "hr@company.com"

    def test_mime_message_body_is_attached(self):
        body_text = "Hi Sarah, thank you for your time."
        msg = build_mime_message("a@b.com", "Subject", body_text, "hr@co.com")
        payloads = msg.get_payload()
        assert any(body_text in p.get_payload() for p in payloads)


class TestSendOrMock:
    def test_routes_to_mock_when_flag_set(self):
        result = send_or_mock("a@b.com", "Subject", "Body", use_mock=True)
        assert result["success"] is True
        assert result["status"] == "mock_sent"

    @patch.dict("os.environ", {"MOCK_EMAIL": "true"})
    def test_routes_to_mock_via_env_var(self):
        result = send_or_mock("a@b.com", "Subject", "Body")
        assert result["status"] == "mock_sent"

    @patch("app.services.email_service.send_email")
    @patch.dict("os.environ", {"MOCK_EMAIL": "false"})
    def test_routes_to_real_send_when_not_mocked(self, mock_send):
        mock_send.return_value = {"success": True, "message_id": "abc123", "status": "sent"}
        result = send_or_mock("a@b.com", "Subject", "Body", use_mock=False)
        mock_send.assert_called_once()
        assert result["status"] == "sent"
