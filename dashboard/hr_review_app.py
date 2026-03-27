import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="HR Feedback Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📋 HR Feedback Dashboard")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📥 Pending Review", "📤 Sent Feedback", "⬆️ Upload Candidates", "📊 Analytics"],
    )
    st.markdown("---")
    st.caption("Candidate Feedback Automation v1.0")


# ── Helper functions ─────────────────────────────────────────────────────────
def api_get(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path, json=None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=json, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def get_candidate(candidate_id):
    return api_get(f"/api/candidates/{candidate_id}")


# ── Pages ─────────────────────────────────────────────────────────────────────

if page == "📥 Pending Review":
    st.header("📥 Pending Feedback Review")
    st.caption("Review, edit, and approve feedback emails before they are sent to candidates.")

    col_refresh, col_generate = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col_generate:
        if st.button("⚡ Generate feedback for all new candidates", use_container_width=True):
            with st.spinner("Generating feedback drafts..."):
                result = api_post("/api/feedback/generate-all")
                if result:
                    st.success(f"Generated {result['generated']} drafts. Failed: {result['failed']}")

    drafts = api_get("/api/feedback/pending")
    if not drafts:
        st.info("No feedback drafts pending review. Upload candidates or generate feedback to get started.")
    else:
        st.markdown(f"**{len(drafts)} draft(s) awaiting approval**")
        st.markdown("---")

        for draft in drafts:
            candidate = get_candidate(draft["candidate_id"])
            candidate_name = candidate["name"] if candidate else f"Candidate #{draft['candidate_id']}"
            role = candidate["role_applied"] if candidate else "Unknown Role"
            category = candidate.get("rejection_category", "Unknown") if candidate else "Unknown"

            with st.expander(
                f"**{candidate_name}** — {role}  |  Category: `{category}`  |  Draft #{draft['id']}",
                expanded=True,
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("**Subject:**")
                    edited_subject = st.text_input(
                        "Subject",
                        value=draft["subject"],
                        key=f"subj_{draft['id']}",
                        label_visibility="collapsed",
                    )
                    st.markdown("**Email body:**")
                    edited_body = st.text_area(
                        "Body",
                        value=draft["body"],
                        height=280,
                        key=f"body_{draft['id']}",
                        label_visibility="collapsed",
                    )

                with col2:
                    st.markdown("**Candidate details:**")
                    if candidate:
                        st.markdown(f"📧 `{candidate['email']}`")
                        st.markdown(f"🎯 Stage: `{candidate.get('stage_reached', 'N/A')}`")
                        st.markdown(f"🏷️ Category: `{category}`")
                    st.markdown("---")
                    st.markdown("**Auto-eligible for sending?**")
                    auto = draft.get("is_auto_eligible", False)
                    st.markdown("✅ Yes" if auto else "⚠️ Manual review required")
                    st.markdown("---")

                    hr_name = st.text_input(
                        "Your name (approver)",
                        key=f"approver_{draft['id']}",
                        placeholder="e.g. Jane Smith",
                    )

                    col_approve, col_reject = st.columns(2)
                    with col_approve:
                        if st.button("✅ Approve & Send", key=f"approve_{draft['id']}", use_container_width=True, type="primary"):
                            if not hr_name:
                                st.warning("Please enter your name before approving.")
                            else:
                                with st.spinner("Sending..."):
                                    result = api_post(
                                        f"/api/feedback/{draft['id']}/approve",
                                        json={
                                            "approved_by": hr_name,
                                            "edited_body": edited_body,
                                            "edited_subject": edited_subject,
                                        },
                                    )
                                    if result:
                                        st.success(f"✅ Sent to {candidate['email'] if candidate else 'candidate'}")
                                        st.rerun()

                    with col_reject:
                        if st.button("🗑️ Discard", key=f"reject_{draft['id']}", use_container_width=True):
                            result = api_post(f"/api/feedback/{draft['id']}/reject")
                            if result:
                                st.info("Draft discarded.")
                                st.rerun()

elif page == "📤 Sent Feedback":
    st.header("📤 Sent Feedback History")

    drafts = api_get("/api/feedback/all")
    if not drafts:
        st.info("No feedback records found.")
    else:
        sent = [d for d in drafts if d["status"] == "sent"]
        st.markdown(f"**{len(sent)} emails sent**")

        rows = []
        for d in sent:
            candidate = get_candidate(d["candidate_id"])
            rows.append({
                "Candidate": candidate["name"] if candidate else f"#{d['candidate_id']}",
                "Email": candidate["email"] if candidate else "-",
                "Role": candidate["role_applied"] if candidate else "-",
                "Approved by": d.get("approved_by", "-"),
                "Sent at": d.get("sent_at", "-"),
                "Draft ID": d["id"],
            })

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "⬆️ Upload Candidates":
    st.header("⬆️ Upload Rejected Candidates")
    st.caption("Upload a CSV file of rejected candidates to generate feedback drafts.")

    with st.expander("📄 CSV format guide", expanded=False):
        st.markdown("""
**Required columns:**
- `name` — Candidate full name
- `email` — Candidate email address
- `role_applied` — Job title they applied for

**Optional columns:**
- `stage_reached` — e.g. Final Interview, Technical Screen
- `rejection_reason_raw` — Raw internal notes
- `interviewer_notes` — Interviewer scorecard notes
- `recruiter_notes` — Recruiter summary notes
        """)
        sample_df = pd.DataFrame([
            {
                "name": "Sarah Chen",
                "email": "sarah.chen@example.com",
                "role_applied": "Data Analyst",
                "stage_reached": "Final Interview",
                "rejection_reason_raw": "Good profile but weak SQL depth",
                "interviewer_notes": "Strong communication, limited hands-on SQL transformation experience",
                "recruiter_notes": "Enthusiastic candidate, not enough technical depth for this role",
            },
            {
                "name": "James Okafor",
                "email": "james.okafor@example.com",
                "role_applied": "Product Manager",
                "stage_reached": "Second Interview",
                "rejection_reason_raw": "Not enough stakeholder management for this level",
                "interviewer_notes": "Good product sense but limited senior stakeholder experience",
                "recruiter_notes": "Level mismatch — more junior than required",
            },
        ])
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

        csv_bytes = sample_df.to_csv(index=False).encode()
        st.download_button("⬇️ Download sample CSV", csv_bytes, "sample_candidates.csv", "text/csv")

    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded:
        if st.button("📤 Upload and process", type="primary"):
            with st.spinner("Processing CSV..."):
                files = {"file": (uploaded.name, uploaded.getvalue(), "text/csv")}
                try:
                    r = requests.post(f"{API_BASE}/api/candidates/upload/csv", files=files, timeout=30)
                    r.raise_for_status()
                    result = r.json()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total rows", result["total_rows"])
                    col2.metric("✅ Imported", result["successful"])
                    col3.metric("❌ Failed", result["failed"])

                    if result["errors"]:
                        st.warning("Some rows had issues:")
                        for err in result["errors"]:
                            st.caption(f"⚠️ {err}")

                    if result["successful"] > 0:
                        st.success(f"Successfully imported {result['successful']} candidates. Go to **Pending Review** to generate and send feedback.")

                except Exception as e:
                    st.error(f"Upload failed: {e}")

elif page == "📊 Analytics":
    st.header("📊 Rejection Analytics")

    candidates = api_get("/api/candidates/")
    drafts = api_get("/api/feedback/all")

    if candidates:
        col1, col2, col3, col4 = st.columns(4)
        sent_count = len([d for d in (drafts or []) if d["status"] == "sent"])
        pending_count = len([d for d in (drafts or []) if d["status"] == "pending"])
        col1.metric("Total candidates", len(candidates))
        col2.metric("Feedback sent", sent_count)
        col3.metric("Awaiting approval", pending_count)
        col4.metric("Coverage rate", f"{round(sent_count / len(candidates) * 100)}%" if candidates else "0%")

        st.markdown("---")
        st.subheader("Rejection categories")
        category_counts = {}
        for c in candidates:
            cat = c.get("rejection_category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts:
            cat_df = pd.DataFrame(
                [(k.replace("_", " ").title(), v) for k, v in sorted(category_counts.items(), key=lambda x: -x[1])],
                columns=["Category", "Count"],
            )
            st.bar_chart(cat_df.set_index("Category"))
    else:
        st.info("No data yet. Upload candidates to see analytics.")
