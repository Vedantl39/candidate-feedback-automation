# System Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         HR Inputs                               │
│  CSV Upload │ Google Form │ ATS Webhook (Greenhouse / Lever)    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                                                                 │
│  ┌─────────────────┐   ┌──────────────────┐   ┌─────────────┐  │
│  │ CSV Ingestor     │   │ Rejection         │   │ Feedback    │  │
│  │                 │──▶│ Classifier        │──▶│ Engine      │  │
│  │ routes_candidates│   │ (keyword-based)   │   │ (Claude API)│  │
│  └─────────────────┘   └──────────────────┘   └──────┬──────┘  │
│                                                       │         │
│  ┌─────────────────┐   ┌──────────────────┐          │         │
│  │ Audit Logger    │◀──│ Approval Router  │◀─────────┘         │
│  │                 │   │ (manual/auto)    │                     │
│  └─────────────────┘   └──────────┬───────┘                    │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
   ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
   │  Streamlit        │  │  Gmail API       │  │  PostgreSQL      │
   │  HR Dashboard     │  │  (send / draft)  │  │  (SQLite local)  │
   └──────────────────┘  └─────────────────┘  └──────────────────┘
```

---

## Component Descriptions

### CSV Ingestor (`app/services/csv_ingestor.py`)
Parses uploaded CSV files of rejected candidates. Validates required fields, normalises headers, and writes records to the database. Triggers rejection classification at import time.

### Rejection Classifier (`app/services/rejection_classifier.py`)
Maps raw interviewer notes to one of seven standard rejection categories using keyword matching. Assigns auto-eligibility flags to determine whether manual HR review is required before sending.

### Feedback Engine (`app/services/feedback_engine.py`)
Calls the Claude API with a structured prompt and safe context summary to generate a candidate-friendly rejection email. Includes strict system prompt guardrails to prevent discriminatory, legally risky, or invented content.

### Approval Router (`app/api/routes_feedback.py`)
Handles the workflow decision logic. In manual mode, all drafts go to the HR dashboard. In semi-auto mode, auto-eligible categories can bypass review. In auto mode, template-safe feedback is dispatched immediately.

### Email Service (`app/services/email_service.py`)
Integrates with the Gmail API via OAuth2 to send emails or create drafts in the HR inbox. Includes a mock mode for local development that prints output to the console without requiring real credentials.

### Audit Logger (`app/services/audit_logger.py`)
Writes structured compliance records for every action in the workflow. Stores original source notes, generated drafts, final approved versions, approver identity, timestamps, and delivery status.

### HR Dashboard (`dashboard/hr_review_app.py`)
A Streamlit interface with four pages: Pending Review, Sent Feedback, Upload Candidates, and Analytics. HR staff can review and edit drafts, approve and send emails, upload CSV batches, and view rejection category breakdowns.

---

## Database Schema

### `candidates`
Stores candidate records created from CSV uploads or webhooks.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-increment |
| name | String | Candidate full name |
| email | String | Candidate email |
| role_applied | String | Job title |
| stage_reached | String | e.g. Final Interview |
| rejection_reason_raw | Text | Raw internal notes |
| rejection_category | String | Normalised category |
| interviewer_notes | Text | Interviewer scorecard text |
| recruiter_notes | Text | Recruiter summary |
| created_at | DateTime | Record creation timestamp |

### `feedback_drafts`
Stores generated and approved feedback email drafts.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-increment |
| candidate_id | Integer FK | References candidates |
| subject | String | Email subject line |
| body | Text | Email body (editable) |
| status | Enum | pending / approved / sent / rejected |
| is_auto_eligible | Boolean | Whether auto-send is permitted |
| approved_by | String | HR approver name |
| approved_at | DateTime | Approval timestamp |
| sent_at | DateTime | Send timestamp |

### `audit_logs`
Immutable compliance record of all system actions.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto-increment |
| candidate_id | Integer | References candidates |
| feedback_draft_id | Integer | References feedback_drafts |
| action | String | e.g. feedback_generated, feedback_sent |
| actor | String | User or system that performed action |
| original_rejection_reason | Text | Raw notes at time of action |
| normalised_category | String | Classifier output |
| generated_draft | Text | Original AI-generated version |
| final_approved_version | Text | Version actually sent |
| email_delivery_status | String | sent / mock_sent / failed |
| timestamp | DateTime | UTC timestamp |

---

## Workflow Modes

### Manual
Every draft is created and sits in the HR queue until a named approver clicks approve and send.

### Semi-auto
Drafts in auto-eligible categories (skills_gap, level_mismatch, domain_experience, stronger_candidate) are sent automatically. Sensitive categories (communication_concerns, logistics_mismatch, role_fit) always go to the HR queue.

### Auto
All template-safe feedback is dispatched immediately without HR review. This mode is only recommended for organisations with established, legally reviewed tone templates and high-volume pipelines.

---

## Local Development

Run with SQLite (default — no database setup required):

```bash
cp .env.example .env
# Edit .env to add your ANTHROPIC_API_KEY
# Set MOCK_EMAIL=true to skip Gmail setup
pip install -r requirements.txt
uvicorn app.main:app --reload
streamlit run dashboard/hr_review_app.py
```

Run with Docker (includes PostgreSQL):

```bash
cp .env.example .env
docker-compose up --build
```

API docs available at: `http://localhost:8000/docs`
Dashboard available at: `http://localhost:8501`
