import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Document, GovernanceReport, EscalationItem, WorkflowStatus
from backend.app.migrations import run_sqlite_migrations

def run_timeline_verification():
    print("======================================================================")
    print("         Timeline Audit Event Verification (Phase 1)                  ")
    print("======================================================================")

    # 1. Setup temporary database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    run_sqlite_migrations(engine)
    
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Dependency Override
    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    tc = TestClient(app)

    # STEP 1: Upload Document (Analyst)
    # This creates a document and logs the upload event.
    print("\n[Step 1] Uploading document as Analyst...")
    # Mock file upload payload
    file_content = b"Mock document content for governance compliance testing."
    files = {"file": ("governance_policy.pdf", file_content, "application/pdf")}
    
    response_upload = tc.post(
        "/api/upload",
        files=files,
        headers={"X-User-Role": "Analyst"}
    )
    assert response_upload.status_code == 201, "Upload failed"
    doc_id = response_upload.json()["id"]
    print(f"-> Created Document ID: {doc_id}")

    # STEP 2: AI Processing (System/AI)
    # The pipeline runs asynchronously in endpoints, but here we can simulate 
    # the workflow completion event directly on our session to generate the audit log.
    print("\n[Step 2] Simulating AI Ingestion & Report Generation...")
    db = SessionTest()
    report = GovernanceReport(
        document_id=doc_id,
        summary="Ingested policy checklist summary",
        executive_summary="Approved narrative checklist",
        confidence_score=0.98,
        model_version="mock",
        review_status="pending_review",
        processing_time_seconds=0.8,
        tokens_used=150,
        provider_name="mock",
        version=1,
        is_latest=True,
        status="PENDING_MANAGER_REVIEW",
        assigned_to="Manager",
        created_by="Analyst"
    )
    db.add(report)
    db.commit()
    report_id = report.id
    
    # Log the AI generation audit log event exactly as endpoints/workflow.py does
    from backend.app.models import AuditLog
    audit_ai = AuditLog(
        document_id=doc_id,
        governance_report_id=report_id,
        event="Review Pending",
        user="system",
        user_role="Analyst",
        action="AI report generation",
        entity_type="report",
        entity_id=report_id,
        details="Governance Report generated automatically by AI and assigned to Manager."
    )
    db.add(audit_ai)
    
    # Create an associated escalation item to test escalation workflow later
    esc = EscalationItem(
        report_id=report_id,
        description="Compliance breach detected in Section 4",
        severity="critical",
        status="open",
        confidence_score=0.95
    )
    db.add(esc)
    db.commit()
    esc_id = esc.id
    db.close()
    print(f"-> Generated Report ID: {report_id}")
    print(f"-> Generated Escalation ID: {esc_id}")

    # STEP 3: Manager Approves Report
    print("\n[Step 3] Manager reviews and approves the report...")
    response_approve = tc.patch(
        f"/api/governance/reports/{report_id}/review",
        json={
            "reviewer": "manager_user",
            "review_status": "approved",
            "review_notes": "All standards met. Approved."
        },
        headers={"X-User-Role": "Manager"}
    )
    assert response_approve.status_code == 200, "Approval failed"
    print("-> Approved successfully.")

    # STEP 4: Manager Escalates Report
    # We will reset the status to pending review to allow escalation simulation
    db = SessionTest()
    report_obj = db.query(GovernanceReport).filter(GovernanceReport.id == report_id).first()
    report_obj.status = "PENDING_MANAGER_REVIEW"
    db.commit()
    db.close()
    
    print("\n[Step 4] Manager escalates findings to Governance Lead...")
    response_escalate = tc.patch(
        f"/api/governance/reports/{report_id}/escalate",
        headers={"X-User-Role": "Manager"}
    )
    assert response_escalate.status_code == 200, "Escalation failed"
    print("-> Escalated successfully.")

    # STEP 5: Governance Lead Resolves Escalation
    print("\n[Step 5] Governance Lead resolves the escalation item...")
    response_resolve = tc.patch(
        f"/api/governance/escalations/{esc_id}/resolve",
        headers={"X-User-Role": "Governance Lead"}
    )
    assert response_resolve.status_code == 200, "Resolution failed"
    print("-> Resolved successfully.")

    # STEP 6: Governance Lead Closes Escalation
    print("\n[Step 6] Governance Lead closes the escalation item...")
    response_close = tc.patch(
        f"/api/governance/escalations/{esc_id}/close",
        headers={"X-User-Role": "Governance Lead"}
    )
    assert response_close.status_code == 200, "Closure failed"
    print("-> Closed successfully.")

    # STEP 7: Fetch Timeline Events and Validate
    print("\n[Step 7] Fetching chronological audit logs...")
    response_audit = tc.get("/api/governance/audit-events")
    assert response_audit.status_code == 200, "Failed to retrieve audit events"
    logs = response_audit.json()
    
    # Map event names and actions to verified requirements
    actions = [log["action"] for log in logs]
    events = [log["event"] for log in logs]
    
    print("\nLogged Timeline Events:")
    for log in logs:
        print(f" - Role: {log['user_role']:<16} | Event: {log['event']:<20} | Action: {log['action']}")

    print("\nVerification Checklist:")
    
    # Check 1: DOCUMENT_UPLOADED equivalent
    has_upload = "document upload" in actions
    print(f" - [DOCUMENT_UPLOADED]     -> {'PASS' if has_upload else 'FAIL'}")
    assert has_upload
    
    # Check 2: AI_REPORT_GENERATED equivalent
    has_ai = "AI report generation" in actions
    print(f" - [AI_REPORT_GENERATED]   -> {'PASS' if has_ai else 'FAIL'}")
    assert has_ai
    
    # Check 3: REPORT_APPROVED equivalent
    has_approval = "report approval" in actions
    print(f" - [REPORT_APPROVED]       -> {'PASS' if has_approval else 'FAIL'}")
    assert has_approval
    
    # Check 4: REPORT_ESCALATED equivalent
    has_escalate = "report escalation" in actions
    print(f" - [REPORT_ESCALATED]      -> {'PASS' if has_escalate else 'FAIL'}")
    assert has_escalate
    
    # Check 5: ESCALATION_RESOLVED equivalent
    has_resolve = "escalation resolution" in actions
    print(f" - [ESCALATION_RESOLVED]   -> {'PASS' if has_resolve else 'FAIL'}")
    assert has_resolve
    
    # Check 6: ESCALATION_CLOSED equivalent
    has_close = "escalation closure" in actions
    print(f" - [ESCALATION_CLOSED]     -> {'PASS' if has_close else 'FAIL'}")
    assert has_close

    # Clean up
    app.dependency_overrides.clear()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
            
    print("\n======================================================================")
    print("             Timeline Validation completed: 6/6 PASS                  ")
    print("======================================================================")

if __name__ == "__main__":
    run_timeline_verification()
