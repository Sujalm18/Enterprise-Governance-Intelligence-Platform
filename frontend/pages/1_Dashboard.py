"""
Page 1 — Dashboard
=====================
Operational KPIs, confidence metrics, processing stats,
and live audit log feed from the governance backend.
"""

import streamlit as st
import requests
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_api_endpoint, make_api_request

st.set_page_config(page_title="Dashboard | AI Governance", page_icon="📊", layout="wide")

st.markdown("""
<div class="main-header" style="
    background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    border: 1px solid #2d4a7a; box-shadow: 0 6px 24px rgba(0,0,0,0.2);">
    <h1 style="color:#e8f0fe; margin:0; font-size:1.6rem;">📊 Governance Dashboard</h1>
    <p style="color:#8ba4c4; margin:0.2rem 0 0; font-size:0.9rem;">
        Real-time operational metrics and audit trail
    </p>
</div>
""", unsafe_allow_html=True)


def confidence_badge(score: float) -> str:
    if score >= 0.8:
        return f'<span class="badge-high">HIGH {score:.0%}</span>'
    elif score >= 0.5:
        return f'<span class="badge-medium">MEDIUM {score:.0%}</span>'
    else:
        return f'<span class="badge-low">LOW {score:.0%}</span>'


def fetch_dashboard():
    return make_api_request("GET", "api/governance/dashboard/stats")


# ─── Refresh Button ───────────────────────────────────────────────────────────
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh Data", key="refresh_dashboard"):
        st.rerun()

with st.spinner("Fetching dashboard data..."):
    data = fetch_dashboard()

if data:
    # ─── KPI Row 1: Document & Report Metrics ─────────────────────────────────
    st.markdown("### 📈 Key Performance Indicators")
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("📄 Total Documents", data["total_documents"])
    k2.metric("⏳ Pending Reviews", data["pending_reviews"])
    k3.metric("✅ Approved Reports", data["approved_reports"])
    k4.metric("❌ Failed Jobs", data["failed_jobs"])

    # ─── KPI Row 2: AI & Performance Metrics ──────────────────────────────────
    k5, k6, k7, k8 = st.columns(4)

    avg_conf = data["average_confidence"]
    k5.metric("🎯 Avg Confidence", f"{avg_conf:.0%}")
    k6.metric("⏱️ Avg Processing", f"{data['average_processing_time']:.1f}s")
    k7.metric("🔢 Tokens Consumed", f"{data['total_tokens_consumed']:,}")
    k8.metric("🚨 Open Escalations", f"{data['open_escalations']} / {data['total_escalations']}")

    # ─── Confidence Score Visual ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎯 Confidence Score")
    st.progress(min(avg_conf, 1.0))
    st.markdown(confidence_badge(avg_conf), unsafe_allow_html=True)

    # ─── Audit Trail ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📜 Recent Audit Trail")

    if data["recent_logs"]:
        audit_df = pd.DataFrame(data["recent_logs"])
        display_cols = ["timestamp", "event", "user", "details", "document_id"]
        available_cols = [c for c in display_cols if c in audit_df.columns]
        audit_df = audit_df[available_cols]

        if "timestamp" in audit_df.columns:
            audit_df["timestamp"] = pd.to_datetime(audit_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")

        st.dataframe(
            audit_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
                "event": st.column_config.TextColumn("Event", width="medium"),
                "user": st.column_config.TextColumn("Actor", width="small"),
                "details": st.column_config.TextColumn("Details", width="large"),
                "document_id": st.column_config.NumberColumn("Doc ID", width="small"),
            }
        )
    else:
        st.info("No audit log entries yet. Upload a document to begin.", icon="📭")
else:
    st.warning("Dashboard data unavailable. Ensure the backend API is running.", icon="⚠️")
