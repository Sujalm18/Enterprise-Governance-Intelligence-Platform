"""
Page 6 — Escalations
========================
View open escalations and route them to target stakeholders.
"""

import streamlit as st
import requests
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Escalations | AI Governance", page_icon="🚨", layout="wide")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    border: 1px solid #2d4a7a; box-shadow: 0 6px 24px rgba(0,0,0,0.2);">
    <h1 style="color:#e8f0fe; margin:0; font-size:1.6rem;">🚨 Escalation Management</h1>
    <p style="color:#8ba4c4; margin:0.2rem 0 0; font-size:0.9rem;">
        Route flagged escalations to appropriate stakeholders
    </p>
</div>
""", unsafe_allow_html=True)


# ─── Filters ──────────────────────────────────────────────────────────────────
col_f1, col_f2, _ = st.columns([2, 2, 2])
with col_f1:
    esc_status_filter = st.selectbox(
        "Filter by status",
        ["All", "open", "routed"],
        index=0
    )
with col_f2:
    if st.button("🔄 Refresh"):
        st.rerun()

# ─── Fetch Escalations ───────────────────────────────────────────────────────
try:
    params = {}
    if esc_status_filter != "All":
        params["status"] = esc_status_filter

    resp = requests.get(f"{API_BASE}/governance/escalations", params=params, timeout=10)
    resp.raise_for_status()
    escalations = resp.json()
except requests.exceptions.ConnectionError:
    st.error("⚠️ Cannot connect to backend.")
    escalations = []
except Exception as e:
    st.error(f"Error: {e}")
    escalations = []

# ─── Summary ──────────────────────────────────────────────────────────────────
open_count = sum(1 for e in escalations if e.get("status") == "open")
routed_count = sum(1 for e in escalations if e.get("status") == "routed")

s1, s2, s3 = st.columns(3)
s1.metric("📊 Total Escalations", len(escalations))
s2.metric("🔴 Open", open_count)
s3.metric("✅ Routed", routed_count)

st.markdown("---")

if not escalations:
    st.info("No escalations found. Process documents to generate escalations.", icon="📭")
else:
    for esc in escalations:
        severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        icon = severity_icons.get(esc.get("severity", ""), "⚪")
        is_open = esc["status"] == "open"

        filename = esc.get("filename", "")
        filename_display = f" | {filename}" if filename else ""
        with st.expander(
            f"{icon} Escalation #{esc['id']} — {esc['description'][:80]}... | "
            f"Status: {esc['status'].upper()}{filename_display}",
            expanded=is_open
        ):
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**Severity:** `{esc.get('severity', 'N/A')}`")
            c2.markdown(f"**Status:** `{esc['status']}`")
            c3.markdown(f"**Report ID:** `{esc['report_id']}`")
            c4.markdown(f"**Filename:** `{filename}`")

            st.markdown(f"**Description:** {esc['description']}")

            if esc.get("source_excerpt"):
                st.caption(f"📎 Source: _{esc['source_excerpt']}_")

            if esc.get("routing_target"):
                st.success(f"📨 Routed to: **{esc['routing_target']}**")

            st.caption(f"Created: {esc['created_at'][:19]}")

            # ─── Route Form (only for open escalations) ──────────────────────
            if is_open:
                st.markdown("---")
                st.markdown("##### 📨 Route This Escalation")

                routing_target = st.text_input(
                    "Routing Target",
                    placeholder="e.g., Legal Counsel, CTO, Steering Committee",
                    key=f"route_target_{esc['id']}"
                )

                if st.button(
                    f"🚀 Route Escalation #{esc['id']}",
                    key=f"route_btn_{esc['id']}",
                    type="primary"
                ):
                    if not routing_target.strip():
                        st.error("Please enter a routing target.")
                    else:
                        try:
                            resp = requests.post(
                                f"{API_BASE}/governance/escalations/{esc['id']}/route",
                                json={"routing_target": routing_target.strip()},
                                timeout=10
                            )
                            resp.raise_for_status()
                            st.success(f"✅ Escalation routed to **{routing_target}**!", icon="📨")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error routing: {e}")
