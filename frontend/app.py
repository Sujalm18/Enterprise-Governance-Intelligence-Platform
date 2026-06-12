"""
Enterprise AI Governance & Operations Copilot — Frontend
=========================================================
Main entry point for the Streamlit multi-page application.
Provides the sidebar navigation, global configuration, and
visual identity (dark/steel-blue enterprise theme).
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent))
from config import get_backend_display_info

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Governance Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS Theme ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* === FONTS === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1724 0%, #1a2640 50%, #1e3050 100%);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #c8d6e5 !important;
    }

    /* === METRIC CARDS === */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2640 0%, #243556 100%);
        border: 1px solid #2d4a7a;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    [data-testid="stMetric"] label {
        color: #8ba4c4 !important;
        font-weight: 500;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e8f0fe !important;
        font-weight: 700;
    }

    /* === BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.5);
        transform: translateY(-1px);
    }

    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background-color: #1a2640 !important;
        border-radius: 8px;
        color: #c8d6e5 !important;
    }

    /* === TABLES === */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* === TAB STYLING === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }

    /* === CONFIDENCE BADGES === */
    .badge-high {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white; padding: 4px 12px; border-radius: 20px;
        font-weight: 600; font-size: 0.78rem;
        display: inline-block;
    }
    .badge-medium {
        background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        color: white; padding: 4px 12px; border-radius: 20px;
        font-weight: 600; font-size: 0.78rem;
        display: inline-block;
    }
    .badge-low {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        color: white; padding: 4px 12px; border-radius: 20px;
        font-weight: 600; font-size: 0.78rem;
        display: inline-block;
    }

    /* === STATUS BADGES === */
    .status-approved {
        background: #059669; color: white; padding: 3px 10px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    }
    .status-pending {
        background: #d97706; color: white; padding: 3px 10px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    }
    .status-failed {
        background: #dc2626; color: white; padding: 3px 10px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    }
    .status-processing {
        background: #2563eb; color: white; padding: 3px 10px;
        border-radius: 20px; font-size: 0.75rem; font-weight: 600;
    }

    /* === HEADER === */
    .main-header {
        background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid #2d4a7a;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    }
    .main-header h1 {
        color: #e8f0fe !important;
        margin-bottom: 0.3rem;
        font-size: 1.8rem;
    }
    .main-header p {
        color: #8ba4c4;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar Branding ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <span style="font-size: 2.5rem;">🛡️</span>
        <h2 style="margin:0.3rem 0 0; font-weight:700; letter-spacing:-0.5px;">
            AI Governance
        </h2>
        <p style="margin:0; font-size:0.85rem; color:#6b8ab8;">
            Operations Copilot
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Role selector
    st.markdown("##### 👤 Active Role")
    role = st.radio(
        "Select your role:",
        ["analyst", "reviewer"],
        index=0,
        label_visibility="collapsed",
        key="global_role"
    )
    st.caption(f"Operating as **{role.upper()}**")
    st.divider()

    st.markdown("""
    <div style="padding: 0.8rem; background: rgba(37,99,235,0.1); border-radius: 8px;
                border-left: 3px solid #2563eb; margin-top: 0.5rem;">
        <p style="margin:0; font-size: 0.78rem; color: #8ba4c4;">
            📡 Backend: <code>""" + get_backend_display_info() + """</code><br>
            🔧 Mode: Mock AI Provider
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─── Main Page ─────────────────────────────────────────────────────────────────
st.info("""
**Legacy MVP Interface**

This interface represents the original Streamlit-based prototype used during the early development of the platform. 
The primary platform is now the React + FastAPI application.
""", icon="ℹ️")

st.markdown("""
<div class="main-header">
    <h1>🛡️ Enterprise Governance Intelligence Platform</h1>
    <p>
        Automated document ingestion, RAID extraction, escalation routing,
        and governance reporting — powered by AI with human-in-the-loop oversight.
    </p>
</div>
""", unsafe_allow_html=True)

row1c1, row1c2, row1c3 = st.columns(3)
with row1c1:
    st.markdown("""
    #### 📊 Dashboard
    Real-time KPIs — confidence scores, processing metrics,
    token usage, and audit trail activity.
    """)

with row1c2:
    st.markdown("""
    #### 📤 Upload Center
    Drag-and-drop document ingestion with configurable
    chunk size, overlap, and RAG toggle.
    """)

with row1c3:
    st.markdown("""
    #### ⚙️ Workflow Tracker
    Monitor ingestion pipelines, job status and logs.
    """)

row2c1, row2c2, row2c3 = st.columns(3)
with row2c1:
    st.markdown("""
    #### 📋 Governance Reports
    Browse AI-generated reports with versioning and RAID details.
    """)

with row2c2:
    st.markdown("""
    #### 🧾 Review Queue
    Approve or request changes on pending reports.
    """)

with row2c3:
    st.markdown("""
    #### 🚨 Escalations
    Route critical items to stakeholders with audit trail.
    """)

st.info("👈 **Navigate** using the sidebar pages to access each module.", icon="💡")
