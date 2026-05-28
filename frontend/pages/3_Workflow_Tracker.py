"""
Page 3 — Workflow Tracker (reordered)
=====================================
Shows recent workflow jobs in a table, lets users click a row to view details,
and displays a visual progression tracker for pipeline stages.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_api_endpoint

st.set_page_config(page_title="Workflow Tracker | AI Governance", page_icon="⚙️", layout="wide")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    border: 1px solid #2d4a7a; box-shadow: 0 6px 24px rgba(0,0,0,0.2);">
    <h1 style="color:#e8f0fe; margin:0; font-size:1.6rem;">⚙️ Workflow Tracker</h1>
    <p style="color:#8ba4c4; margin:0.2rem 0 0; font-size:0.9rem;">
        Track document processing pipelines and view execution logs
    </p>
</div>
""", unsafe_allow_html=True)


def status_badge_html(status: str) -> str:
    colors = {
        "uploaded": "#6b7280",
        "parsed": "#2563eb",
        "chunked": "#2563eb",
        "indexed": "#2563eb",
        "ai_extraction": "#2563eb",
        "report_generated": "#059669",
        "pending_review": "#d97706",
        "completed": "#059669",
        "failed": "#dc2626",
    }
    bg = colors.get(status, "#6b7280")
    label = status.replace("_", " ").upper()
    return f'<span style="background:{bg};color:white;padding:4px 14px;border-radius:20px;font-size:0.78rem;font-weight:600;letter-spacing:0.5px;">{label}</span>'


STAGES = [
    ("uploaded", "Uploaded"),
    ("parsed", "Parsed"),
    ("chunked", "Chunked"),
    ("indexed", "Indexed"),
    ("ai_extraction", "AI Extraction"),
    ("report_generated", "Report Generated"),
    ("pending_review", "Pending Review"),
    ("completed", "Completed"),
]


# ─── Recent Jobs Table ──────────────────────────────────────────────────────
st.markdown("### 🧾 Recent Processed Reports (used as workflow jobs)")

# Use existing backend reports endpoint (no backend changes required)
jobs = []
try:
    resp = requests.get(get_api_endpoint("api/governance/reports"), params={"is_latest": True}, timeout=10)
    resp.raise_for_status()
    jobs = resp.json()
except requests.exceptions.ConnectionError:
    st.error("⚠️ Cannot connect to backend. Is the server running?")
except Exception:
    jobs = []

if not jobs:
    st.info("No recent processed reports found. Upload and process a document to generate reports.", icon="📭")
else:
    # Normalize into DataFrame for a compact view
    df = pd.DataFrame(jobs)
    display_cols = []
    if "filename" in df.columns:
        display_cols.append("filename")
    if "review_status" in df.columns:
        display_cols.append("review_status")
    if "confidence_score" in df.columns:
        display_cols.append("confidence_score")
    if "created_at" in df.columns:
        display_cols.append("created_at")

    display_df = df[display_cols].copy()
    if "created_at" in display_df.columns:
        display_df["created_at"] = pd.to_datetime(display_df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    # Present a compact table using filename as primary identifier
    col_rename = {
        "filename": "Filename",
        "review_status": "Status",
        "confidence_score": "Confidence",
        "created_at": "Created Date"
    }
    st.dataframe(display_df.rename(columns=col_rename), use_container_width=True)

    st.markdown("---")

    st.markdown("#### Click a report to view details")
    for job in jobs:
        j_id = job.get("id")
        filename = job.get("filename") or f"Doc #{job.get('document_id')}"
        conf = job.get("confidence_score")
        status = job.get("review_status", "pending_review")
        created = job.get("created_at") or job.get("created")

        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        # Make the filename a clickable button to open details
        if c1.button(filename, key=f"view_job_{j_id}"):
            st.session_state["selected_report_id"] = j_id
            st.session_state["selected_report_obj"] = job
            st.experimental_rerun()
        c2.markdown(status_badge_html(status), unsafe_allow_html=True)
        c3.markdown(f"{(f'{conf:.0%}' if isinstance(conf, float) else (conf if conf is not None else '—'))}")
        c4.markdown(created if created else "—")

# ─── Selected Job Details ──────────────────────────────────────────────────
selected_report_id = st.session_state.get("selected_report_id")
selected_report = st.session_state.get("selected_report_obj")

if selected_report_id:
    st.markdown("---")
    st.markdown(f"### ⚙️ Report Details — #{selected_report_id}")

    # Fetch latest report detail
    try:
        resp = requests.get(get_api_endpoint(f"api/governance/reports/{selected_report_id}"), timeout=8)
        if resp.status_code == 200:
            selected_report = resp.json()
            st.session_state["selected_report_obj"] = selected_report
    except Exception:
        pass

    if selected_report:
        # Summary header
        st.markdown(f"**Document ID:** {selected_report.get('document_id')}")
        st.markdown(f"**Status:** {selected_report.get('review_status')}")
        st.markdown(f"**Created:** {selected_report.get('created_at')}")

        # Visual progress tracker (approximate using report status)
        # Map report review status to pipeline stages
        if selected_report.get('review_status') == 'pending_review':
            current_status = 'pending_review'
        elif selected_report.get('review_status') in ('approved', 'changes_requested'):
            current_status = 'completed'
        else:
            current_status = 'report_generated'
        stage_html = "<div style='display:flex; gap:12px; align-items:center; flex-wrap:wrap;'>"
        reached = False
        for key, label in STAGES:
            active = (not reached) or (key == current_status)
            if key == current_status:
                reached = True

            if active:
                stage_html += f"<div style='padding:8px 12px; border-radius:12px; background:#2563eb; color:white; font-weight:600;'>{label}</div>"
            else:
                stage_html += f"<div style='padding:8px 12px; border-radius:12px; background:#2d3748; color:#aab8d6;'>{label}</div>"

        stage_html += "</div>"
        st.markdown(stage_html, unsafe_allow_html=True)

        # Progress bar approximated by stage index
        try:
            idx = next(i for i, s in enumerate(STAGES) if s[0] == current_status)
            progress_val = (idx + 1) / len(STAGES)
        except StopIteration:
            progress_val = 0.1

        st.progress(progress_val)

        st.markdown("---")

        # Report content and processing metrics
        st.markdown("### 📝 Executive Summary")
        st.info(selected_report.get('executive_summary', 'No executive summary available.'))

        st.markdown("### 📄 Detailed Summary")
        st.markdown(selected_report.get('summary', 'No detailed summary available.'))

        st.markdown("---")
        st.markdown("### 🎯 RAID Items")
        if selected_report.get('raid_items'):
            for item in selected_report['raid_items']:
                severity_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                icon = severity_colors.get(item.get('severity'), "⚪")
                st.markdown(
                    f"{icon} **[{item.get('type','N/A').upper()}]** {item.get('description')}  \n"
                    f"Severity: `{item.get('severity')}` | Confidence: {item.get('confidence_score')}",
                    unsafe_allow_html=True
                )
                if item.get('source_excerpt'):
                    st.caption(f"📎 Source: _{item.get('source_excerpt')}_")
        else:
            st.info("No RAID items found for this report.")

        st.markdown("---")
        st.markdown("### 🚨 Escalations")
        if selected_report.get('escalation_items'):
            for esc in selected_report['escalation_items']:
                st.warning(f"**{esc.get('description')}**  \nSeverity: `{esc.get('severity')}` | Status: `{esc.get('status', 'open')}`")
        else:
            st.info("No escalations for this report.")

        st.markdown("---")
        st.markdown("### ⚡ Processing Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("⏱️ Processing Time", f"{selected_report.get('processing_time_seconds', 0):.2f}s")
        m2.metric("🔢 Tokens", f"{selected_report.get('tokens_used', 0):,}")
        m3.metric("🤖 Provider", selected_report.get('provider_name', 'unknown'))
        m4.metric("📐 Version", f"V{selected_report.get('version', 1)}")

        # Quick actions
        a1, a2 = st.columns([1, 1])
        with a1:
            if st.button("Refresh Report", key=f"refresh_report_{selected_report_id}"):
                try:
                    resp = requests.get(get_api_endpoint(f"api/governance/reports/{selected_report_id}"), timeout=8)
                    resp.raise_for_status()
                    st.session_state["selected_report_obj"] = resp.json()
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error refreshing report: {e}")
        with a2:
            if st.button("Open in Governance Reports", key=f"open_report_{selected_report_id}"):
                try:
                    st.experimental_set_query_params(page="Governance Reports", report_id=selected_report_id)
                except Exception:
                    pass
                st.experimental_rerun()
