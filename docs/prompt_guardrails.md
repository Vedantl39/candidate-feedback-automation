# Prompt Guardrails

## Overview

The feedback generation system uses Claude with a carefully designed system prompt to ensure all candidate-facing output is safe, professional, and legally appropriate.

---

## System Prompt Design Principles

The system prompt enforces the following non-negotiable constraints:

### 1. No protected characteristics
The model is explicitly instructed never to mention, imply, or reference:
- Age
- Gender or gender identity
- Race or ethnicity
- Nationality or national origin
- Religion or belief
- Disability status
- Pregnancy or parental status
- Marital or family status
- Sexual orientation

### 2. No invented content
The model only works from the structured context summary it is given. It cannot add reasons, suggest implied problems, or speculate about the candidate's profile beyond what is explicitly included in the prompt.

### 3. No legally risky language
Phrases such as the following are prohibited:
- "you failed"
- "you were rejected because"
- "you were not good enough"
- "another candidate beat you"
- Direct comparisons to other candidates by name or implication

### 4. Constrained output scope
The model outputs only an email body starting with the candidate's first name. It does not include:
- Subject lines (generated separately by a deterministic function)
- Markdown formatting
- Internal notes or labels
- Commentary outside the email

---

## Context Design

The model is never given raw interviewer notes directly. Instead, a `get_safe_category_summary()` function produces a pre-approved, neutral summary sentence per rejection category and role. This summary is the only rejection context the model receives.

Example:

| Raw notes (internal) | Safe context passed to model |
|---|---|
| "weak SQL, can't do window functions" | "The candidate did not demonstrate sufficient technical depth required for the Data Analyst role." |
| "too junior, would need 2 more years" | "The experience level of the candidate did not match what the Senior Engineer role requires." |

This design means:
- Specific technical criticisms are never exposed to the model
- The model cannot accidentally reproduce internal language in the output
- All candidate-facing output is generated from policy-approved framing

---

## Tone Configuration

The system supports tone settings that can be configured per team or per role:

- **Professional** (default) — formal and neutral
- **Warm** — slightly more conversational and encouraging

Tone is passed as a parameter to the prompt, not as free text from the user, so it cannot be used to inject instructions.

---

## What the Model Is Not Given

The following inputs are deliberately withheld from the LLM:

- The candidate's email address
- The names of interviewers
- Specific scores or ratings
- Names of other candidates
- Compensation or offer details
- Full raw interviewer scorecards

---

## Testing Guardrails

The test suite in `tests/test_rejection_classifier.py` includes checks that:
- Sensitive categories are not flagged as auto-eligible
- Category summaries do not contain protected characteristic language
- All seven categories produce a non-empty, role-specific summary

For production use, consider adding an output evaluation layer that scans generated emails for flagged terms before they reach the HR dashboard.
