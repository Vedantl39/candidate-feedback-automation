# Quick Start Guide

Get the system running in under 10 minutes.

---

## What you need

- Python 3.11 or newer (or Docker)
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)
- A Gmail account for the HR inbox (optional for first run — mock mode works without it)

---

## Option A: Run locally with Python

### 1. Clone and enter the project

```bash
git clone https://github.com/yourorg/candidate-feedback-automation.git
cd candidate-feedback-automation
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your environment

```bash
cp .env.example .env
```

Open `.env` and set:

```
ANTHROPIC_API_KEY=your_key_here
MOCK_EMAIL=true
```

Leave everything else as default for the first run.

### 4. Start the API

```bash
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### 5. Start the HR dashboard

In a new terminal window:

```bash
streamlit run dashboard/hr_review_app.py
```

The dashboard opens at `http://localhost:8501`

---

## Option B: Run with Docker

```bash
cp .env.example .env
# Edit .env to add ANTHROPIC_API_KEY
docker-compose up --build
```

- API: `http://localhost:8000`
- Dashboard: `http://localhost:8501`

---

## Your first workflow

### Step 1: Upload candidates

1. Open the dashboard at `http://localhost:8501`
2. Go to **Upload Candidates**
3. Download the sample CSV to see the format
4. Upload your CSV of rejected candidates

### Step 2: Generate feedback

1. Go to **Pending Review**
2. Click **Generate feedback for all new candidates**
3. Wait a few seconds — drafts will appear

### Step 3: Review and send

1. Review each draft
2. Edit the subject or body if needed
3. Enter your name as approver
4. Click **Approve & Send**

With `MOCK_EMAIL=true`, emails print to the terminal. Set `MOCK_EMAIL=false` and follow the Gmail setup guide to send real emails.

---

## CSV format reference

| Column | Required | Description |
|---|---|---|
| `name` | ✅ | Candidate full name |
| `email` | ✅ | Candidate email address |
| `role_applied` | ✅ | Job title they applied for |
| `stage_reached` | Optional | e.g. Final Interview |
| `rejection_reason_raw` | Optional | Brief internal reason |
| `interviewer_notes` | Optional | Interviewer scorecard notes |
| `recruiter_notes` | Optional | Recruiter summary |

---

## Running tests

```bash
pytest
```

---

## Next steps

- [Connect Gmail](./email_setup_guide.md)
- [System design](../docs/system_design.md)
- [Privacy and compliance](../docs/privacy_and_compliance.md)
