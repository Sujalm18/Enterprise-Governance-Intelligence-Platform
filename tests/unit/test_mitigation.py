import os
import tempfile
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Document, GovernanceReport, RaidItem, MitigationTask, EscalationItem, WorkflowStatus
from backend.app.api.endpoints import calculate_sla_status

@pytest.fixture(name="db_setup")
def fixture_db_setup():
    """Sets up a temporary SQLite database on disk for test execution."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # Close file descriptor immediately to release Windows file lock
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionTest, db_path
    
    # Tear down
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

@pytest.fixture(name="db_session")
def fixture_db_session(db_setup):
    SessionTest, _ = db_setup
    db = SessionTest()
    yield db
    db.close()

@pytest.fixture(name="client")
def fixture_client(db_setup, db_session):
    """Sets up a TestClient with overridden get_db dependency."""
    SessionTest, _ = db_setup
    
    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    tc = TestClient(app)
    yield tc
    app.dependency_overrides.clear()

def test_sla_status_calculation():
    # If completed or verified, must be ON_TRACK
    assert calculate_sla_status("COMPLETED", "2020-01-01") == "ON_TRACK"
    assert calculate_sla_status("VERIFIED", "2020-01-01") == "ON_TRACK"
    
    # If no target date, must be ON_TRACK
    assert calculate_sla_status("PLANNED", None) == "ON_TRACK"
    
    # If overdue (target date < today)
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert calculate_sla_status("PLANNED", yesterday) == "OVERDUE"
    
    # If within 3 days (e.g. today or in 2 days)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    in_two_days = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
    assert calculate_sla_status("PLANNED", today) == "AT_RISK"
    assert calculate_sla_status("PLANNED", in_two_days) == "AT_RISK"
    
    # If far in the future
    future = (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d")
    assert calculate_sla_status("PLANNED", future) == "ON_TRACK"

def test_mitigation_crud_endpoints(client, db_session):
    # Setup prerequisite document, report, and RAID item
    doc = Document(filename="test_doc.pdf", type="pdf", status=WorkflowStatus.PENDING_REVIEW)
    db_session.add(doc)
    db_session.commit()
    
    report = GovernanceReport(
        document_id=doc.id,
        summary="Test summary",
        executive_summary="Exec summary",
        confidence_score=0.9,
        model_version="mock",
        review_status="approved",
        processing_time_seconds=1.0,
        tokens_used=100,
        provider_name="mock",
        version=1,
        is_latest=True
    )
    db_session.add(report)
    db_session.commit()
    
    raid_item = RaidItem(
        report_id=report.id,
        type="risk",
        description="Major security gap detected",
        severity="critical",
        confidence_score=0.9,
        risk_score=90,
        current_risk_score=90,
        suggested_owner_role="Manager",
        priority="P1"
    )
    db_session.add(raid_item)
    db_session.commit()
    
    # Create mitigation tasks
    task1 = MitigationTask(
        title="Implement MFA",
        description="Enable multi-factor auth",
        related_raid_item_id=raid_item.id,
        owner_role="Manager",
        priority="P1",
        risk_score=90,
        target_date=(datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d"),
        status="PLANNED",
        completion_percentage=0,
        effectiveness=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    task2 = MitigationTask(
        title="Audit access logs",
        description="Review access logs monthly",
        related_raid_item_id=raid_item.id,
        owner_role="Analyst",
        priority="P2",
        risk_score=90,
        target_date=(datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"), # overdue
        status="PLANNED",
        completion_percentage=0,
        effectiveness=20,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([task1, task2])
    db_session.commit()
    
    # 1. Test listing mitigations
    response = client.get("/api/mitigations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Verify SLA status is calculated dynamically
    t1_data = next(t for t in data if t["id"] == task1.id)
    t2_data = next(t for t in data if t["id"] == task2.id)
    assert t1_data["sla_status"] == "ON_TRACK"
    assert t2_data["sla_status"] == "OVERDUE"
    
    # 2. Test get mitigation by id
    response = client.get(f"/api/mitigations/{task1.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Implement MFA"
    
    # 3. Test listing filters
    response = client.get("/api/mitigations?owner_role=Analyst")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Audit access logs"

def test_role_based_permissions(client, db_session):
    # Setup data
    doc = Document(filename="doc.pdf", type="pdf", status=WorkflowStatus.PENDING_REVIEW)
    db_session.add(doc)
    db_session.commit()
    report = GovernanceReport(document_id=doc.id, summary="S", executive_summary="E", confidence_score=0.9, review_status="approved", processing_time_seconds=1.0, tokens_used=100, provider_name="m", version=1, is_latest=True)
    db_session.add(report)
    db_session.commit()
    raid_item = RaidItem(report_id=report.id, type="risk", description="D", severity="high", risk_score=80, current_risk_score=80)
    db_session.add(raid_item)
    db_session.commit()
    
    task = MitigationTask(
        title="Task 1",
        related_raid_item_id=raid_item.id,
        owner_role="Analyst",
        priority="P2",
        risk_score=80,
        status="PLANNED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task)
    db_session.commit()
    
    # Analyst Role Switcher simulated via X-User-Role
    headers_analyst = {"X-User-Role": "Analyst"}
    headers_manager = {"X-User-Role": "Manager"}
    headers_gov_lead = {"X-User-Role": "Governance Lead"}
    
    # 1. Analyst tries to mark COMPLETED -> Should fail (403)
    response = client.put(f"/api/mitigations/{task.id}", json={"status": "COMPLETED"}, headers=headers_analyst)
    assert response.status_code == 403
    
    # 2. Analyst tries to mark VERIFIED -> Should fail (403)
    response = client.put(f"/api/mitigations/{task.id}", json={"status": "VERIFIED"}, headers=headers_analyst)
    assert response.status_code == 403
    
    # 3. Manager tries to mark VERIFIED -> Should fail (403)
    response = client.put(f"/api/mitigations/{task.id}", json={"status": "VERIFIED"}, headers=headers_manager)
    assert response.status_code == 403
    
    # 4. Manager marks COMPLETED -> Should succeed (200)
    response = client.put(f"/api/mitigations/{task.id}", json={"status": "COMPLETED"}, headers=headers_manager)
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    
    # Refresh task from DB
    db_session.refresh(task)
    assert task.status == "COMPLETED"
    
    # 5. Analyst tries to edit completed task -> Should fail (403)
    response = client.put(f"/api/mitigations/{task.id}", json={"title": "Changed Title"}, headers=headers_analyst)
    assert response.status_code == 403
    
    # 6. Gov Lead verifies -> Should succeed (200)
    response = client.post(f"/api/mitigations/{task.id}/verify", headers=headers_gov_lead)
    assert response.status_code == 200
    assert response.json()["status"] == "VERIFIED"
    
    # Refresh task
    db_session.refresh(task)
    assert task.status == "VERIFIED"
    
    # 7. Manager tries to edit verified task -> Should fail (403)
    response = client.put(f"/api/mitigations/{task.id}", json={"title": "Manager Change"}, headers=headers_manager)
    assert response.status_code == 403
    
    # 8. Gov Lead reopens task -> Should succeed (200)
    response = client.post(f"/api/mitigations/{task.id}/reopen", headers=headers_gov_lead)
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"

def test_dynamic_risk_recalculation(client, db_session):
    # Setup data
    doc = Document(filename="doc.pdf", type="pdf", status=WorkflowStatus.PENDING_REVIEW)
    db_session.add(doc)
    db_session.commit()
    report = GovernanceReport(document_id=doc.id, summary="S", executive_summary="E", confidence_score=0.9, review_status="approved", processing_time_seconds=1.0, tokens_used=100, provider_name="m", version=1, is_latest=True)
    db_session.add(report)
    db_session.commit()
    
    # Original Risk score is 80
    raid_item = RaidItem(report_id=report.id, type="risk", description="D", severity="high", risk_score=80, current_risk_score=80)
    db_session.add(raid_item)
    db_session.commit()
    
    # Add two mitigation tasks
    task1 = MitigationTask(
        title="Mitigation A",
        related_raid_item_id=raid_item.id,
        owner_role="Manager",
        priority="P1",
        risk_score=80,
        status="PLANNED",
        effectiveness=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    task2 = MitigationTask(
        title="Mitigation B",
        related_raid_item_id=raid_item.id,
        owner_role="Manager",
        priority="P2",
        risk_score=80,
        status="PLANNED",
        effectiveness=60, # 30 + 60 = 90% potential effectiveness
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add_all([task1, task2])
    db_session.commit()
    
    headers_gov_lead = {"X-User-Role": "Governance Lead"}
    
    # 1. Verify task1 -> effectiveness = 30%. Risk reduced by 30%.
    # Expected: residual_mult = 1.0 - 0.3 = 0.7. current_risk_score = 80 * 0.7 = 56.
    client.post(f"/api/mitigations/{task1.id}/verify", headers=headers_gov_lead)
    
    db_session.refresh(raid_item)
    assert raid_item.current_risk_score == 56
    
    # 2. Verify task2 -> effectiveness = 60%. Cumulative = 30 + 60 = 90%, capped at 80% (0.80).
    # Expected: residual_mult = 1.0 - 0.8 = 0.2. current_risk_score = 80 * 0.2 = 16.
    client.post(f"/api/mitigations/{task2.id}/verify", headers=headers_gov_lead)
    
    db_session.refresh(raid_item)
    assert raid_item.current_risk_score == 16
    
    # 3. Reopen task1 -> Only task2 is verified (effectiveness = 60%).
    # Expected: residual_mult = 1.0 - 0.6 = 0.4. current_risk_score = 80 * 0.4 = 32.
    client.post(f"/api/mitigations/{task1.id}/reopen", headers=headers_gov_lead)
    
    db_session.refresh(raid_item)
    assert raid_item.current_risk_score == 32

def test_governance_health_score(client, db_session):
    # Setup data
    doc = Document(filename="doc.pdf", type="pdf", status=WorkflowStatus.PENDING_REVIEW)
    db_session.add(doc)
    db_session.commit()
    
    report = GovernanceReport(document_id=doc.id, summary="S", executive_summary="E", confidence_score=0.9, review_status="approved", processing_time_seconds=1.0, tokens_used=100, provider_name="m", version=1, is_latest=True)
    db_session.add(report)
    db_session.commit()
    
    # 1. Test clean system: health score = 100
    response = client.get("/api/governance/dashboard/stats")
    assert response.status_code == 200
    assert response.json()["governance_health_score"] == 100
    
    # 2. Add an open critical/high risk: severity = critical, current_risk_score = 80
    # Expected deduction: -5
    raid_item = RaidItem(report_id=report.id, type="risk", description="Critical Risk", severity="critical", risk_score=80, current_risk_score=80)
    db_session.add(raid_item)
    db_session.commit()
    
    response = client.get("/api/governance/dashboard/stats")
    assert response.json()["governance_health_score"] == 95
    
    # 3. Add an open escalation: status = ASSIGNED
    # Expected deduction: -8
    esc = EscalationItem(report_id=report.id, description="Escalation desc", severity="high", status="ASSIGNED")
    db_session.add(esc)
    db_session.commit()
    
    response = client.get("/api/governance/dashboard/stats")
    assert response.json()["governance_health_score"] == 87
    
    # 4. Add an overdue mitigation task
    # Expected deduction: -4
    task = MitigationTask(
        title="Task Overdue",
        related_raid_item_id=raid_item.id,
        owner_role="Manager",
        priority="P1",
        risk_score=80,
        status="PLANNED",
        target_date="2020-01-01", # overdue
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task)
    db_session.commit()
    
    response = client.get("/api/governance/dashboard/stats")
    assert response.json()["governance_health_score"] == 83
    
    # 5. Add verified mitigation task: status = VERIFIED
    # Expected bonus: +2
    task_verified = MitigationTask(
        title="Task Verified",
        related_raid_item_id=raid_item.id,
        owner_role="Manager",
        priority="P2",
        risk_score=80,
        status="VERIFIED",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task_verified)
    db_session.commit()
    
    response = client.get("/api/governance/dashboard/stats")
    assert response.json()["governance_health_score"] == 85
