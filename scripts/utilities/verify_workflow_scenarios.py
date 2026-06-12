import os
import tempfile
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Document, GovernanceReport, EscalationItem, WorkflowStatus
from backend.app.migrations import run_sqlite_migrations

def run_scenarios():
    print("======================================================================")
    print("         Manual Workflow Verification Scenarios (Phase 1)             ")
    print("======================================================================")

    # 1. Setup temporary database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    run_sqlite_migrations(engine)
    
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionTest()
    
    # Seed mock user & initial data
    doc = Document(filename="mock_doc.txt", type="txt", status=WorkflowStatus.PENDING_REVIEW)
    db.add(doc)
    db.commit()
    
    report = GovernanceReport(
        document_id=doc.id,
        summary="Audit summary text",
        executive_summary="Executive narrative text",
        confidence_score=0.95,
        model_version="mock",
        review_status="pending_review",
        processing_time_seconds=1.0,
        tokens_used=100,
        provider_name="mock",
        version=1,
        is_latest=True,
        status="PENDING_MANAGER_REVIEW",
        assigned_to="Manager"
    )
    db.add(report)
    db.commit()
    
    esc = EscalationItem(
        report_id=report.id,
        description="Vendor billing discrepancy",
        severity="high",
        status="open",
        confidence_score=0.90
    )
    db.add(esc)
    db.commit()
    
    report_id = report.id
    esc_id = esc.id
    db.close()
    
    # Dependency Override
    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    tc = TestClient(app)
    
    # ----------------------------------------------------
    # SCENARIO 1: Role = Analyst tries to Approve Report
    # ----------------------------------------------------
    print("\nScenario 1: Role = Analyst tries to Approve Report")
    response_s1 = tc.patch(
        f"/api/governance/reports/{report_id}/review",
        json={
            "reviewer": "analyst_user",
            "review_status": "approved",
            "review_notes": "Attempting unauthorized approval"
        },
        headers={"X-User-Role": "Analyst"}
    )
    print(f"-> Response Status Code: {response_s1.status_code}")
    print(f"-> Response Body: {response_s1.json()}")
    assert response_s1.status_code == 403, "Scenario 1 failed!"
    print("Result: [PASS] Analyst was successfully blocked (403 Forbidden).")
    
    # ----------------------------------------------------
    # SCENARIO 2: Role = Manager tries to Close Escalation
    # ----------------------------------------------------
    print("\nScenario 2: Role = Manager tries to Close Escalation")
    response_s2 = tc.patch(
        f"/api/governance/escalations/{esc_id}/close",
        headers={"X-User-Role": "Manager"}
    )
    print(f"-> Response Status Code: {response_s2.status_code}")
    print(f"-> Response Body: {response_s2.json()}")
    assert response_s2.status_code == 403, "Scenario 2 failed!"
    print("Result: [PASS] Manager was successfully blocked (403 Forbidden).")
    
    # ----------------------------------------------------
    # SCENARIO 3: Role = Governance Lead tries to Close Escalation
    # ----------------------------------------------------
    print("\nScenario 3: Role = Governance Lead tries to Close Escalation")
    response_s3 = tc.patch(
        f"/api/governance/escalations/{esc_id}/close",
        headers={"X-User-Role": "Governance Lead"}
    )
    print(f"-> Response Status Code: {response_s3.status_code}")
    print(f"-> Response Body: {response_s3.json()}")
    assert response_s3.status_code == 200, "Scenario 3 failed!"
    print("Result: [PASS] Governance Lead successfully closed escalation (200 OK).")
    
    # ----------------------------------------------------
    # SCENARIO 4: Verify initial report status & assignment details
    # ----------------------------------------------------
    print("\nScenario 4: Verify initial report status & assignment details")
    response_s4 = tc.get(f"/api/governance/reports/{report_id}")
    report_data = response_s4.json()
    print(f"-> Report Status: {report_data['status']}")
    print(f"-> Assigned To: {report_data['assigned_to']}")
    assert report_data["status"] == "PENDING_MANAGER_REVIEW", "Scenario 4 status check failed!"
    assert report_data["assigned_to"] == "Manager", "Scenario 4 assignment check failed!"
    print("Result: [PASS] Initial status is PENDING_MANAGER_REVIEW and assigned to Manager.")
    
    # ----------------------------------------------------
    # SCENARIO 5: Escalate a report and verify status changes
    # ----------------------------------------------------
    print("\nScenario 5: Escalate a report as Manager")
    response_s5 = tc.patch(
        f"/api/governance/reports/{report_id}/escalate",
        headers={"X-User-Role": "Manager"}
    )
    print(f"-> Response Status Code: {response_s5.status_code}")
    report_data_esc = response_s5.json()
    print(f"-> Escalated Report Status: {report_data_esc['status']}")
    print(f"-> Escalated Report Assigned To: {report_data_esc['assigned_to']}")
    assert report_data_esc["status"] == "ESCALATED", "Scenario 5 report status failed!"
    assert report_data_esc["assigned_to"] == "Governance Lead", "Scenario 5 report assignment failed!"
    
    # Verify associated escalations are assigned to Governance Lead
    response_esc_list = tc.get("/api/governance/escalations")
    escalation_items = response_esc_list.json()
    associated_esc = [e for e in escalation_items if e["report_id"] == report_id][0]
    print(f"-> Associated Escalation Status: {associated_esc['status']}")
    print(f"-> Associated Escalation Assigned To: {associated_esc['assigned_to']}")
    assert associated_esc["status"] == "ASSIGNED", "Scenario 5 escalation status check failed!"
    assert associated_esc["assigned_to"] == "Governance Lead", "Scenario 5 escalation assignment failed!"
    print("Result: [PASS] Report and associated escalations correctly transitioned to ESCALATED/ASSIGNED and routed to Governance Lead.")

    # Clean up
    app.dependency_overrides.clear()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
            
    print("\n======================================================================")
    print("             Workflow Verification Scenarios completed: 5/5 PASS      ")
    print("======================================================================")

if __name__ == "__main__":
    run_scenarios()
