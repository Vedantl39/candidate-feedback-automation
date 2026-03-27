# Privacy and Compliance Guide

## Overview

This system processes personally identifiable information (PII) related to employment decisions. All teams using this system must follow the guidelines below to remain compliant with applicable employment law and data protection regulations including GDPR, CCPA, and relevant local employment legislation.

---

## Data Classification

| Data type | Classification | Retention |
|---|---|---|
| Candidate name and email | PII | 12 months post-rejection |
| Interviewer notes (raw) | Internal — confidential | 6 months |
| Generated feedback emails | Internal — candidate-facing | 24 months |
| Audit log entries | Compliance record | 36 months |
| Rejection category labels | Operational | 24 months |

---

## What the System Will Never Do

The system is designed with strict constraints to prevent the following:

- **Mention protected characteristics** — age, gender, race, nationality, religion, disability status, pregnancy, marital status, or sexual orientation are never referenced in candidate-facing output.
- **Invent rejection reasons** — the feedback generator only works from structured context derived from actual interviewer notes. It does not add reasons not present in the source data.
- **Produce legal-risk language** — phrases such as "you failed", "you were rejected because", or direct comparisons to other candidates are excluded by system prompt guardrails.
- **Send without a human review option** — even in auto-send mode, the system supports manual override and full audit logging.

---

## Prompt Guardrails

All LLM prompts include the following explicit constraints:

1. Do not mention protected characteristics
2. Do not invent reasons not present in provided context
3. Do not use language that could create legal liability
4. Use only respectful, professional, non-discriminatory language
5. Do not reference other candidates directly
6. Keep all output within the scope of HR tone guidelines

These constraints are applied at the system prompt level and cannot be overridden by user input at runtime.

---

## Audit Trail

Every feedback action creates a structured audit log entry containing:

- Who triggered the action (recruiter or system)
- Original raw rejection reason as submitted by interviewer
- Normalised rejection category assigned by the classifier
- AI-generated draft (before any HR edits)
- Final approved version (after HR review and any edits)
- Timestamp of approval and sending
- Email delivery status

The original source notes are always stored separately from the candidate-facing version. This ensures there is a verifiable chain of custody between internal deliberations and what was communicated to the candidate.

---

## Data Access Controls

Recommended access controls for production deployment:

- HR admin role: full read and write access to dashboard and audit logs
- Recruiter role: read access to candidate records, write access to rejection reason fields only
- API access: protected by authentication tokens or webhook secrets
- Database: restrict direct access to infrastructure team only

---

## Candidate Data Requests

Under GDPR and similar regulations, candidates may request:

- **Access** to what personal data is held about them
- **Deletion** of their personal data
- **Correction** of inaccurate information

The audit log should be preserved for compliance purposes even if candidate PII is anonymised following a deletion request. Consult your legal or DPO team before implementing automated deletion workflows.

---

## Risk Flags for Manual Review

The following rejection categories are flagged for mandatory manual HR review before sending:

- `communication_concerns` — risk of implying language or cultural bias
- `logistics_mismatch` — may involve visa or work authorisation status
- `role_fit` — reason is broad and requires careful framing

The following categories are eligible for semi-automated or auto-send modes:

- `skills_gap`
- `level_mismatch`
- `domain_experience`
- `stronger_candidate`

---

## Disclaimer

This system is designed to assist HR teams in drafting feedback. It does not constitute legal advice. All rejection decisions and communications remain the responsibility of the employing organisation. Teams should consult their legal or HR compliance function before enabling auto-send mode or making changes to prompt templates.
