"""
Page 2 — Upload Center
========================
File upload with configurable ingestion parameters.
Supports PDF, DOCX, TXT.
"""

import streamlit as st
import requests
import time
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Upload Center | AI Governance", page_icon="📤", layout="wide")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #0f1724 0%, #1a2640 60%, #1e3050 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    border: 1px solid #2d4a7a; box-shadow: 0 6px 24px rgba(0,0,0,0.2);">
    <h1 style="color:#e8f0fe; margin:0; font-size:1.6rem;">📤 Document Upload Center</h1>
    <p style="color:#8ba4c4; margin:0.2rem 0 0; font-size:0.9rem;">
        Ingest governance documents for AI-powered RAID extraction and analysis
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Upload Form ──────────────────────────────────────────────────────────────
col_upload, col_config = st.columns([3, 2])

with col_upload:
    st.markdown("### 📁 Select Document")
    uploaded_file = st.file_uploader(
        "Drag and drop or browse",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX, TXT",
        key="doc_uploader"
    )

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        st.markdown(f"""
        <div style="background: rgba(37,99,235,0.1); border: 1px solid #2d4a7a;
                    border-radius: 10px; padding: 1rem; margin-top: 0.5rem;">
            <strong style="color:#e8f0fe;">📄 {uploaded_file.name}</strong><br>
            <span style="color:#8ba4c4; font-size:0.85rem;">
                Type: <code>{uploaded_file.type}</code> &nbsp;|&nbsp;
                Size: <code>{file_size_kb:.1f} KB</code>
            </span>
        </div>
        """, unsafe_allow_html=True)

with col_config:
    st.markdown("### ⚙️ Processing Configuration")
    # Auto-detect mode: compute suggested chunking and RAG based on file metadata
    def _detect_doc_type(name: str, content_bytes: bytes) -> str:
        n = (name or "").lower()
        if any(k in n for k in ("govern", "governance")):
            return "Governance Report"
        if "status" in n:
            return "Status Report"
        if "audit" in n:
            return "Audit Report"
        if any(k in n for k in ("minute", "meeting")):
            return "Meeting Minutes"
        # try to peek into bytes for simple markers (txt)
        try:
            t = content_bytes[:1024].decode("utf-8", errors="ignore").lower()
            if "attendance" in t or "minutes" in t:
                return "Meeting Minutes"
            if "audit" in t:
                return "Audit Report"
            if "status" in t or "progress" in t:
                return "Status Report"
        except Exception:
            pass
        return "Unknown"

    def _estimate_complexity(file_size_kb: float, pages: int = 0) -> str:
        # Heuristic: tiny files -> Small, moderate -> Medium, very large -> Large
        if file_size_kb < 200 and (pages == 0 or pages <= 3):
            return "Small"
        if file_size_kb < 2000 or (pages > 3 and pages <= 20):
            return "Medium"
        return "Large"

    def _auto_settings(file_size_kb: float, pages: int, doc_type: str):
        complexity = _estimate_complexity(file_size_kb, pages)
        if complexity == "Small":
            return {"chunk_size": 800, "chunk_overlap": 100, "use_rag": False, "complexity": complexity}
        if complexity == "Medium":
            return {"chunk_size": 1200, "chunk_overlap": 200, "use_rag": True, "complexity": complexity}
        return {"chunk_size": 2000, "chunk_overlap": 400, "use_rag": True, "complexity": complexity}

    # Default display values
    detected_type = "Unknown"
    detected_complexity = "Small"
    auto_chunk = 1000
    auto_overlap = 200
    auto_rag = True

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        # crude page estimate for PDFs: assume ~100KB per page if not available
        pages = 0
        if uploaded_file.name.lower().endswith('.pdf'):
            pages = max(1, int(file_size_kb / 100))
        elif uploaded_file.name.lower().endswith('.docx'):
            pages = max(1, int(file_size_kb / 60))
        else:
            pages = max(1, int(file_size_kb / 1000))

        detected_type = _detect_doc_type(uploaded_file.name, uploaded_file.getvalue())
        auto = _auto_settings(file_size_kb, pages, detected_type)
        auto_chunk = auto["chunk_size"]
        auto_overlap = auto["chunk_overlap"]
        auto_rag = auto["use_rag"]
        detected_complexity = auto["complexity"]

    st.markdown(f"""
    <div style="background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1;
                padding: 0.8rem; border-radius: 6px; margin-top: 0.2rem;">
        <strong>Analysis Mode:</strong> <span style="font-weight:700; color:#111827;">Auto</span>
        &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Detected Type:</strong> <span style="color:#374151;">{detected_type}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Estimated Complexity:</strong> <span style="color:#374151;">{detected_complexity}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: rgba(5,150,105,0.06); border: 1px solid #059669;
                border-radius: 8px; padding: 0.8rem; margin-top: 0.6rem;">
        <span style="font-size:0.9rem; color:#0f1724;">
            Suggested Chunks: <strong>{auto_chunk}</strong> chars &nbsp;|&nbsp;
            Overlap: <strong>{auto_overlap}</strong> chars &nbsp;|&nbsp;
            RAG: <strong>{'Enabled' if auto_rag else 'Disabled'}</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Advanced settings for power users
    with st.expander("Advanced Settings (override auto)", expanded=False):
        chunk_size = st.slider(
            "Chunk Size (characters)",
            min_value=200, max_value=4000, value=auto_chunk, step=100,
            help="Size of each text chunk for indexing"
        )
        chunk_overlap = st.slider(
            "Chunk Overlap (characters)",
            min_value=0, max_value=500, value=auto_overlap, step=50,
            help="Overlap between consecutive chunks"
        )
        use_rag = st.checkbox(
            "🔍 Enable RAG Retrieval",
            value=auto_rag,
            help="Use TF-IDF retrieval to supply context to AI"
        )
        st.markdown("<div style='margin-top:0.5rem; color:#6b7280; font-size:0.85rem;'>Tip: Advanced settings are optional; leave collapsed to use Auto mode.</div>", unsafe_allow_html=True)

    # If advanced expander not used, fall back to auto values
    try:
        # If chunk_size variable not defined because expander not interacted with
        chunk_size
    except NameError:
        chunk_size = auto_chunk
        chunk_overlap = auto_overlap
        use_rag = auto_rag

# ─── Submit Button ────────────────────────────────────────────────────────────
st.markdown("---")

if uploaded_file:
    if st.button("🚀 Upload & Process Document", type="primary", use_container_width=True):
        with st.spinner("Uploading document and initiating pipeline..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                params = {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "use_rag": use_rag
                }

                resp = requests.post(
                    f"{API_BASE}/upload",
                    files=files,
                    params=params,
                    timeout=30
                )
                resp.raise_for_status()
                result = resp.json()

                st.success(f"✅ Document uploaded successfully! Document ID: **{result['id']}**", icon="🎉")

                st.markdown(f"""
                <div style="background: rgba(5,150,105,0.1); border: 1px solid #059669;
                            border-radius: 10px; padding: 1.2rem; margin-top: 1rem;">
                    <h4 style="color:#10b981; margin:0 0 0.5rem;">Upload Confirmation</h4>
                    <table style="width:100%; color:#c8d6e5;">
                        <tr><td><strong>Document ID</strong></td><td>{result['id']}</td></tr>
                        <tr><td><strong>Filename</strong></td><td>{result['filename']}</td></tr>
                        <tr><td><strong>Type</strong></td><td>{result['type']}</td></tr>
                        <tr><td><strong>Status</strong></td><td>{result['status']}</td></tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                st.info("📡 Background pipeline is now processing.", icon="⏳")

                # Action buttons: View Workflow, View Report (if available), Auto-redirect option
                from streamlit import components as components

                a_col, b_col, c_col = st.columns([1, 1, 1])

                with a_col:
                    if st.button("🔎 View Workflow Progress", key=f"view_workflow_{result['id']}"):
                        try:
                            # Try to pass the job/document id via query params and rerun.
                            st.experimental_set_query_params(page="Workflow Tracker", job_id=result['id'])
                        except Exception:
                            pass
                        st.experimental_rerun()

                with b_col:
                    report_id = result.get('report_id') or result.get('generated_report_id')
                    if report_id:
                        if st.button("📄 View Generated Report", key=f"view_report_{result['id']}"):
                            try:
                                st.experimental_set_query_params(page="Governance Reports", report_id=report_id)
                            except Exception:
                                pass
                            st.experimental_rerun()

                with c_col:
                    auto_redirect = st.checkbox("Auto-redirect to Workflow Tracker after 3s", value=False, key=f"auto_redirect_{result['id']}")
                    if auto_redirect:
                        components.html(f"""<script>
                            setTimeout(()=>{{ window.location.href = window.location.pathname + '?page=Workflow Tracker'; }}, 3000);
                        </script>""", height=10)

                st.markdown("---")
                st.info("Tip: Use 'View Workflow Progress' to jump to the job and monitor ingestion stages.", icon="💡")

            except requests.exceptions.ConnectionError:
                st.error("⚠️ Cannot connect to backend at localhost:8000. Is the server running?")
            except requests.exceptions.HTTPError as e:
                st.error(f"❌ Upload failed: {e.response.text}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
else:
    st.info("👆 Select a document above to begin the upload process.", icon="📎")
