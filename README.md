# Candidate Feedback Automation

An end-to-end HR automation system that generates structured, personalised rejection feedback for candidates and manages the full workflow from interview outcome to email delivery.

---

## The problem

Most rejected candidates receive either no feedback or a generic rejection email. This creates a poor candidate experience and gives HR teams extra manual work when they want to provide thoughtful, consistent responses.

---

## What this system does

1. HR uploads a CSV of rejected candidates (or a webhook triggers from an ATS)
2. The system classifies each rejection into a standard category
3. Claude generates a respectful, constructive feedback email per candidate
4. HR reviews and edits drafts in a simple dashboard
5. Emails are sent through the connected Gmail account
6. Every action is logged for compliance and audit

---

## Features

- **Rejection reason classifier** — maps raw interviewer notes to 7 standard categories
- **AI feedback generator** — uses Claude with strict guardrails to draft candidate-friendly emails
- **HR review dashboard** — Streamlit interface for reviewing, editing, approving, and sending
- **Gmail integration** — sends emails or creates drafts in your HR inbox via Gmail API
- **CSV upload** — bulk import rejected candidates from a spreadsheet
- **Audit log** — stores original notes, generated draft, final approved version, and delivery status
- **Three workflow modes** — manual review, semi-automated, or auto-send
- **ATS webhook endpoint** — ready for Greenhouse, Lever, or n8n integration

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| HR Dashboard | Streamlit |
| Database | SQLite (local) / PostgreSQL (production) |
| AI Layer | Anthropic Claude API |
| Email | Gmail API (OAuth2) |
| Containerisation | Docker Compose |

---

## Quick start

```bash
git clone https://github.com/yourorg/candidate-feedback-automation.git
cd candidate-feedback-automation
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uvicorn app.main:app --reload
# In a new terminal:
streamlit run dashboard/hr_review_app.py
```

Full setup instructions: [onboarding/quick_start.md](onboarding/quick_start.md)

---

## Repository structure

```
candidate-feedback-automation/
│
├── app/
│   ├── api/
│   │   ├── routes_candidates.py     # CSV upload, candidate CRUD
│   │   ├── routes_feedback.py       # Generate, approve, send feedback
│   │   └── routes_webhooks.py       # ATS webhook receiver
│   ├── services/
│   │   ├── feedback_engine.py       # Claude API feedback generator
│   │   ├── rejection_classifier.py  # Keyword-based reason classifier
│   │   ├── email_service.py         # Gmail API integration
│   │   ├── csv_ingestor.py          # CSV parsing and import
│   │   └── audit_logger.py          # Compliance audit trail
│   ├── models/
│   │   ├── models.py                # SQLAlchemy database models
│   │   └── schemas.py               # Pydantic request/response schemas
│   ├── database.py                  # DB session and engine config
│   └── main.py                      # FastAPI application entry point
│
├── dashboard/
│   └── hr_review_app.py             # Streamlit HR dashboard
│
├── data/
│   └── sample_candidates.csv        # Sample data for testing
│
├── docs/
│   ├── system_design.md             # Architecture and schema docs
│   ├── privacy_and_compliance.md    # GDPR and employment law guidance
│   └── prompt_guardrails.md         # AI safety and prompt design
│
├── onboarding/
│   ├── quick_start.md               # Setup guide for HR teams
│   └── email_setup_guide.md         # Gmail OAuth2 walkthrough
│
├── tests/
│   ├── test_rejection_classifier.py
│   ├── test_csv_ingestor.py
│   └── test_email_service.py
│
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Dashboard pages

| Page | Description |
|---|---|
| Pending Review | View, edit, and approve feedback drafts |
| Sent Feedback | History of all sent emails |
| Upload Candidates | CSV upload with format guide and sample download |
| Analytics | Rejection volume, category breakdown, coverage rate |

---

## CSV format

| Column | Required | Description |
|---|---|---|
| `name` | ✅ | Candidate full name |
| `email` | ✅ | Candidate email address |
| `role_applied` | ✅ | Job title they applied for |
| `stage_reached` | Optional | e.g. Final Interview |
| `rejection_reason_raw` | Optional | Brief internal rejection reason |
| `interviewer_notes` | Optional | Interviewer scorecard text |
| `recruiter_notes` | Optional | Recruiter summary notes |

---

## Rejection categories

The classifier maps raw notes to one of seven standard categories:

| Category | Auto-send eligible |
|---|---|
| Skills Gap | ✅ |
| Level Mismatch | ✅ |
| Domain Experience | ✅ |
| Stronger Competing Candidate | ✅ |
| Role Fit | ⚠️ Manual review |
| Communication Concerns | ⚠️ Manual review |
| Logistics or Work Authorisation | ⚠️ Manual review |

---

## Prompt safety design

The feedback generator uses strict system prompt guardrails:

- Never mentions protected characteristics
- Never invents reasons not in the source notes
- Never uses legally risky language
- Always maintains HR tone — respectful, clear, constructive
- Keeps original interviewer notes separate from candidate-facing output

See [docs/privacy_and_compliance.md](docs/privacy_and_compliance.md) for the full compliance framework.

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/candidates/` | Create a single candidate |
| GET | `/api/candidates/` | List all candidates |
| POST | `/api/candidates/upload/csv` | Upload a CSV file |
| POST | `/api/feedback/generate/{id}` | Generate feedback for one candidate |
| POST | `/api/feedback/generate-all` | Generate for all candidates without drafts |
| GET | `/api/feedback/pending` | List pending drafts |
| POST | `/api/feedback/{id}/approve` | Approve and send a draft |
| POST | `/api/webhooks/ats-rejection` | Receive ATS rejection webhook |

Full interactive API docs: `http://localhost:8000/docs`

---

## Environment variables

See [.env.example](.env.example) for the full list. Key variables:

```
ANTHROPIC_API_KEY=        # Required — get from console.anthropic.com
MOCK_EMAIL=true           # Set to false to send real emails
WORKFLOW_MODE=manual      # manual | semi_auto | auto
DATABASE_URL=             # Defaults to SQLite for local dev
```

---

## Running tests

```bash
pytest
```

---

## Future extensions

- Greenhouse and Lever native integrations
- Multilingual feedback generation
- Candidate sentiment analysis on responses
- Feedback quality scoring and tone consistency checks
- Role-specific feedback templates
- Recruiter analytics dashboard
- Fairness monitoring across rejection categories

---

## Licence

MIT
