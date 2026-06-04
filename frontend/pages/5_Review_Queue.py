"""
Page 5 — Review Queue
========================
Reviewer workspace: inspect AI-generated reports, approve
or request changes, and add review notes.
"""

import streamlit as st
import requests
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_api_endpoint, make_api_request

st.set_page_config(page_title="Review Queue | AI Governance", page_icon="✅", layout="wide")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    border: 1px solid #2d4a7a; box-shadow: 0 6px 24px rgba(0,0,0,0.2);">
    <h1 style="color:#e8f0fe; margin:0; font-size:1.6rem;">✅ Review Queue</h1>
    <p style="color:#8ba4c4; margin:0.2rem 0 0; font-size:0.9rem;">
        Approve or request changes on pending governance reports
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


# ─── Fetch Pending Reports ───────────────────────────────────────────────────
col_r, _ = st.columns([1, 5])
with col_r:
    if st.button("🔄 Refresh Queue"):
        st.rerun()

with st.spinner("Loading review queue..."):
    pending_reports = make_api_request(
        "GET",
        "api/governance/reports",
        params={"is_latest": True, "review_status": "pending_review"}
    ) or []

if not pending_reports:
    st.success("🎉 Review queue is empty — no pending reports!", icon="✅")
else:
    st.markdown(f"**{len(pending_reports)}** report(s) awaiting review")
    st.markdown("---")

    for report in pending_reports:
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a2640 0%, #243556 100%);
                        border: 1px solid #2d4a7a; border-radius: 14px; padding: 1.5rem;
                        margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="color:#e8f0fe; margin:0;">
                        📄 {report.get('filename', 'Report')} — Report #{report['id']}
                    </h3>
                    <span>V{report['version']} &nbsp; {confidence_badge(report['confidence_score'])}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Report Content Tabs
            tab_summary, tab_raid, tab_escalation, tab_metrics = st.tabs([
                "📝 Summary", "🎯 RAID Items", "🚨 Escalations", "⚡ Metrics"
            ])

            with tab_summary:
                st.markdown("**Executive Summary:**")
                st.info(report["executive_summary"])
                st.markdown("**Detailed Summary:**")
                st.markdown(report["summary"])

            with tab_raid:
                if report.get("raid_items"):
                    for item in report["raid_items"]:
                        severity_colors = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                        icon = severity_colors.get(item["severity"], "⚪")
                        st.markdown(
                            f"{icon} **[{item['type'].upper()}]** {item['description']}  \n"
                            f"Severity: `{item['severity']}` | "
                            f"Confidence: {confidence_badge(item['confidence_score'])}",
                            unsafe_allow_html=True
                        )
                        if item.get("source_excerpt"):
                            st.caption(f"📎 _{item['source_excerpt']}_")
                        st.markdown("---")
                else:
                    st.info("No RAID items extracted.")

            with tab_escalation:
                if report.get("escalation_items"):
                    for esc in report["escalation_items"]:
                        st.warning(
                            f"**{esc['description']}**  \n"
                            f"Severity: `{esc['severity']}` | Status: `{esc['status']}`"
                        )
                else:
                    st.info("No escalations flagged.")

            with tab_metrics:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("⏱️ Processing", f"{report['processing_time_seconds']:.2f}s")
                m2.metric("🔢 Tokens", f"{report['tokens_used']:,}")
                m3.metric("🤖 Provider", report["provider_name"])
                m4.metric("📐 Prompt", report["prompt_version"])

            # ─── Review Form ──────────────────────────────────────────────────
            st.markdown("#### ✍️ Review Action")

            review_col1, review_col2 = st.columns([3, 2])

            with review_col1:
                reviewer_name = st.text_input(
                    "Reviewer Name",
                    value=st.session_state.get("global_role", "reviewer"),
                    key=f"reviewer_{report['id']}"
                )
                review_notes = st.text_area(
                    "Review Notes",
                    placeholder="Add your review comments here...",
                    key=f"notes_{report['id']}"
                )

            with review_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                action = st.radio(
                    "Decision",
                    ["approved", "changes_requested"],
                    format_func=lambda x: "✅ Approve" if x == "approved" else "🔄 Request Changes",
                    key=f"action_{report['id']}"
                )

            if st.button(
                "Submit Review",
                key=f"submit_{report['id']}",
                type="primary",
                use_container_width=True
            ):
                if not reviewer_name.strip():
                    st.error("Please enter a reviewer name.")
                else:
                    payload = {
                        "reviewer": reviewer_name.strip(),
                        "review_status": action,
                        "review_notes": review_notes
                    }
                    result = make_api_request(
                        "PATCH",
                        f"api/governance/reports/{report['id']}/review",
                        json=payload
                    )

                    if result:
                        if action == "approved":
                            st.success(f"✅ Report #{report['id']} approved successfully!", icon="🎉")
                        else:
                            st.warning(f"🔄 Changes requested for Report #{report['id']}.")

                        st.rerun()

            st.markdown("---")
