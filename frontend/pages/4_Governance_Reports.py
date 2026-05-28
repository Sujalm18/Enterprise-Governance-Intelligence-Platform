"""
Page 4 — Governance Reports
==============================
Browse, filter, and inspect AI-generated governance reports.
Includes version switching and confidence badges.
"""

import streamlit as st
import requests
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_api_endpoint

st.set_page_config(page_title="Reports | AI Governance", page_icon="📋", layout="wide")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    border: 1px solid #2d4a7a; box-shadow: 0 6px 24px rgba(0,0,0,0.2);">
    <h1 style="color:#e8f0fe; margin:0; font-size:1.6rem;">📋 Governance Reports</h1>
    <p style="color:#8ba4c4; margin:0.2rem 0 0; font-size:0.9rem;">
        Browse AI-generated reports with version tracking and RAID details
    </p>
</div>
""", unsafe_allow_html=True)


def confidence_badge(score: float) -> str:
    if score >= 0.8:
        return f'<span style="background:linear-gradient(135deg,#059669,#10b981);color:white;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">HIGH {score:.0%}</span>'
    elif score >= 0.5:
        return f'<span style="background:linear-gradient(135deg,#d97706,#f59e0b);color:white;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">MEDIUM {score:.0%}</span>'
    else:
        return f'<span style="background:linear-gradient(135deg,#dc2626,#ef4444);color:white;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">LOW {score:.0%}</span>'


def status_badge(status: str) -> str:
    colors = {
        "approved": "#059669",
        "pending_review": "#d97706",
        "changes_requested": "#dc2626",
    }
    bg = colors.get(status, "#6b7280")
    label = status.replace("_", " ").title()
    return f'<span style="background:{bg};color:white;padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">{label}</span>'


def quality_label(report: dict) -> str:
    confidence = report.get("confidence_score", 0)
    raid_count = len(report.get("raid_items", []))
    escalation_count = len(report.get("escalation_items", []))
    if confidence >= 0.85 and raid_count <= 20:
        return "High quality extraction"
    if confidence >= 0.65:
        return "Review recommended"
    if escalation_count > 0:
        return "Escalation review required"
    return "Low confidence review"


def raid_summary_frame(items: list) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["type", "count", "avg_confidence"])
    frame = pd.DataFrame(items)
    return (
        frame.groupby("type")
        .agg(count=("type", "size"), avg_confidence=("confidence_score", "mean"))
        .reset_index()
        .sort_values(["count", "type"], ascending=[False, True])
    )


def ownership_frame(actions: list) -> pd.DataFrame:
    rows = []
    for action in actions or []:
        rows.append({
            "owner": action.get("owner", "Unassigned"),
            "action": action.get("task") or action.get("action"),
            "due_date": action.get("due_date") or "Not specified",
            "confidence": action.get("confidence", 0),
        })
    return pd.DataFrame(rows)


def explain_item(item: dict, item_kind: str) -> list:
    text = f"{item.get('description', '')} {item.get('source_excerpt', '')} {item.get('task', '')}".lower()
    reasons = []
    if item_kind == "escalation":
        reasons.append("Active escalation language or executive intervention context detected.")
        if "executive" in text or "cio" in text or "steering committee" in text:
            reasons.append("Authority-level stakeholder is referenced.")
        if "requires" in text or "escalated" in text or "initiated" in text:
            reasons.append("Source text indicates a required escalation action.")
    elif item_kind == "action":
        reasons.append("Executable task language detected.")
        if item.get("owner") and item.get("owner") != "Unassigned":
            reasons.append("Explicit accountable owner is present.")
        if item.get("due_date"):
            reasons.append("Future-oriented due date is present.")
    else:
        reasons.append("Mapped through governance ontology into RAID output.")
        if any(term in text for term in ["delay", "blocked", "unstable", "failure"]):
            reasons.append("Delivery-impact condition detected.")
        if any(term in text for term in ["owner", "due", "mitigation", "approval"]):
            reasons.append("Structured governance metadata is attached.")
    return reasons or ["No additional trace available."]


# ─── Filters ──────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
with col_f1:
    show_latest_only = st.checkbox("Show latest versions only", value=True)
with col_f2:
    filter_status = st.selectbox(
        "Filter by status:",
        ["All", "pending_review", "approved", "changes_requested"],
        index=0
    )
with col_f3:
    if st.button("🔄 Refresh"):
        st.rerun()

# ─── Fetch Reports ───────────────────────────────────────────────────────────
try:
    params = {"is_latest": show_latest_only}
    if filter_status != "All":
        params["review_status"] = filter_status

    resp = requests.get(get_api_endpoint("api/governance/reports"), params=params, timeout=10)
    resp.raise_for_status()
    reports = resp.json()
except requests.exceptions.ConnectionError:
    st.error("⚠️ Cannot connect to backend. Is the server running?")
    reports = []
except Exception as e:
    st.error(f"Error: {e}")
    reports = []

if not reports:
    st.info("No reports found. Upload and process a document to generate reports.", icon="📭")
else:
    st.markdown(f"**{len(reports)}** report(s) found")

    for report in reports:
        title = f"{report.get('filename','Report')} | Report #{report['id']} | {report['review_status'].replace('_', ' ').title()}"
        with st.expander(title, expanded=len(reports) == 1):
            # Header row
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**Confidence:** {confidence_badge(report['confidence_score'])}", unsafe_allow_html=True)
            c2.markdown(f"**Status:** {status_badge(report['review_status'])}", unsafe_allow_html=True)
            c3.metric("Version", f"V{report['version']}")
            c4.metric("Latest", "✅" if report['is_latest'] else "❌")

            st.markdown("---")

            # Executive Summary
            st.markdown("##### 📝 Executive Summary")
            st.markdown(f"> {report['executive_summary']}")

            # Detailed Summary
            st.markdown("##### 📄 Detailed Summary")
            st.markdown(report["summary"])

            # Processing Metrics
            st.markdown("---")
            st.markdown("##### ⚡ Processing Metrics")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⏱️ Processing Time", f"{report['processing_time_seconds']:.2f}s")
            m2.metric("🔢 Tokens Used", f"{report['tokens_used']:,}")
            m3.metric("🤖 Provider", report["provider_name"])
            m4.metric("📐 Prompt", report["prompt_version"]) 

            st.markdown("---")
            st.markdown("##### Extraction Quality")
            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Quality", quality_label(report))
            q2.metric("RAID", len(report.get("raid_items", [])))
            q3.metric("Escalations", len(report.get("escalation_items", [])))
            q4.metric("Actions", len(report.get("meeting_actions", [])))

            raid_summary = raid_summary_frame(report.get("raid_items", []))
            if not raid_summary.empty:
                st.markdown("##### RAID Summary")
                st.dataframe(
                    raid_summary,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "type": st.column_config.TextColumn("Type"),
                        "count": st.column_config.NumberColumn("Count"),
                        "avg_confidence": st.column_config.ProgressColumn(
                            "Avg Confidence",
                            min_value=0,
                            max_value=1,
                            format="%.0f%%",
                        ),
                    },
                )
                heatmap_df = pd.DataFrame(report.get("raid_items", []))
                if {"type", "severity"}.issubset(heatmap_df.columns):
                    st.markdown("##### Risk Heatmap")
                    st.dataframe(pd.crosstab(heatmap_df["severity"], heatmap_df["type"]), use_container_width=True)

            actions_df = ownership_frame(report.get("meeting_actions", []))
            if not actions_df.empty:
                st.markdown("##### Action Ownership")
                st.dataframe(
                    actions_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "owner": st.column_config.TextColumn("Owner", width="medium"),
                        "action": st.column_config.TextColumn("Action", width="large"),
                        "due_date": st.column_config.TextColumn("Due Date", width="small"),
                        "confidence": st.column_config.ProgressColumn(
                            "Confidence",
                            min_value=0,
                            max_value=1,
                            format="%.0f%%",
                        ),
                    },
                )

            # RAID Items
            if report.get("raid_items"):
                st.markdown("---")
                st.markdown(f"##### 🎯 RAID Items ({len(report['raid_items'])})")
                for item in report["raid_items"]:
                    severity_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                    icon = severity_colors.get(item["severity"], "⚪")
                    st.markdown(
                        f"{icon} **[{item['type'].upper()}]** {item['description']}  \n"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;Severity: `{item['severity']}` | "
                        f"Confidence: {confidence_badge(item['confidence_score'])}",
                        unsafe_allow_html=True
                    )
                    if item.get("source_excerpt"):
                        st.caption(f"📎 Source: _{item['source_excerpt']}_")
                    with st.expander("Why this was extracted", expanded=False):
                        for reason in explain_item(item, "raid"):
                            st.markdown(f"- {reason}")

            # Escalations
            if report.get("escalation_items"):
                st.markdown("---")
                st.markdown(f"##### 🚨 Escalations ({len(report['escalation_items'])})")
                for esc in report["escalation_items"]:
                    st.warning(f"**{esc['description']}**  \nSeverity: `{esc['severity']}` | Status: `{esc['status']}`")
                    with st.expander("Escalation rationale", expanded=False):
                        for reason in explain_item(esc, "escalation"):
                            st.markdown(f"- {reason}")

            # Metadata
            st.markdown("---")
            st.caption(
                f"Created: {report['created_at'][:19]} | "
                f"Updated: {report['updated_at'][:19]} | "
                f"Model: {report['model_version']} | "
                f"Reviewer: {report.get('reviewer') or 'Pending'}"
            )
            # Quick navigation: open full report details
            if st.button("Open Report Details", key=f"open_report_{report['id']}"):
                try:
                    st.experimental_set_query_params(page="Workflow Tracker", report_id=report['id'])
                except Exception:
                    pass
                st.experimental_rerun()
