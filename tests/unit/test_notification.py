import os
import tempfile
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Document, GovernanceReport, RaidItem, MitigationTask, EscalationItem, WorkflowStatus, Notification, AuditLog


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


def test_notifications_crud_and_read_endpoints(client, db_session):
    # Seed notifications for different roles
    n1 = Notification(
        severity="MEDIUM",
        notification_type="REPORT_PENDING_REVIEW",
        title="Report pending",
        message="A report is pending.",
        recipient_role="Manager",
        read_status=False,
        created_at=datetime.utcnow()
    )
    n2 = Notification(
        severity="HIGH",
        notification_type="ESCALATION_ASSIGNED",
        title="Escalation assigned",
        message="An escalation is assigned.",
        recipient_role="Governance Lead",
        read_status=False,
        created_at=datetime.utcnow()
    )
    n3 = Notification(
        severity="LOW",
        notification_type="MITIGATION_ASSIGNED",
        title="Mitigation assigned",
        message="A mitigation task is assigned.",
        recipient_role="Analyst",
        read_status=False,
        created_at=datetime.utcnow()
    )
    db_session.add_all([n1, n2, n3])
    db_session.commit()

    # 1. Test listing notifications as Manager
    response = client.get("/api/notifications", headers={"X-User-Role": "Manager"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["notification_type"] == "REPORT_PENDING_REVIEW"
    assert data[0]["read_status"] is False

    # 2. Test marking notification as read
    response = client.put(
        f"/api/notifications/{n1.id}/read",
        json={"read_status": True},
        headers={"X-User-Role": "Manager"}
    )
    assert response.status_code == 200
    assert response.json()["read_status"] is True

    # Refresh DB session and verify
    db_session.refresh(n1)
    assert n1.read_status is True

    # 3. Test mark all as read
    # Add another unread notification for Manager
    n4 = Notification(
        severity="LOW",
        notification_type="GOVERNANCE_ALERT",
        title="Alert",
        message="Alert message",
        recipient_role="Manager",
        read_status=False,
        created_at=datetime.utcnow()
    )
    db_session.add(n4)
    db_session.commit()

    response = client.put("/api/notifications/read-all", headers={"X-User-Role": "Manager"})
    assert response.status_code == 200
    assert response.json()["message"] == "All notifications marked as read."

    # Verify n4 is now read
    db_session.refresh(n4)
    assert n4.read_status is True


def test_inbox_aggregation(client, db_session):
    # Setup document, report, raid item, and escalation
    doc = Document(filename="test.pdf", type="pdf", status=WorkflowStatus.PENDING_REVIEW)
    db_session.add(doc)
    db_session.commit()

    report = GovernanceReport(
        document_id=doc.id,
        summary="Summary",
        executive_summary="Executive",
        confidence_score=0.9,
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
    db_session.add(report)
    db_session.commit()

    raid = RaidItem(
        report_id=report.id,
        type="risk",
        description="Major risk",
        severity="high",
        risk_score=80
    )
    db_session.add(raid)
    db_session.commit()

    esc = EscalationItem(
        report_id=report.id,
        description="Escalation 1",
        severity="high",
        status="ASSIGNED",
        assigned_to="Governance Lead"
    )
    db_session.add(esc)
    db_session.commit()

    mit = MitigationTask(
        title="Mitigate risk",
        related_raid_item_id=raid.id,
        owner_role="Analyst",
        priority="P2",
        risk_score=80,
        status="IN_PROGRESS",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(mit)
    db_session.commit()

    # 1. Test inbox for Manager (should see pending manager review report)
    response = client.get("/api/inbox", headers={"X-User-Role": "Manager"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["pending_reviews"]) == 1
    assert data["pending_reviews"][0]["id"] == report.id
    assert len(data["assigned_escalations"]) == 0
    assert len(data["assigned_mitigations"]) == 0

    # 2. Test inbox for Governance Lead (should see assigned escalation)
    response = client.get("/api/inbox", headers={"X-User-Role": "Governance Lead"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["pending_reviews"]) == 0
    assert len(data["assigned_escalations"]) == 1
    assert data["assigned_escalations"][0]["id"] == esc.id

    # 3. Test inbox for Analyst (should see assigned mitigation task)
    response = client.get("/api/inbox", headers={"X-User-Role": "Analyst"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["assigned_mitigations"]) == 1
    assert data["assigned_mitigations"][0]["id"] == mit.id


def test_dynamic_sla_alerts(client, db_session):
    # Setup task that is overdue
    doc = Document(filename="test.pdf", type="pdf", status=WorkflowStatus.PUBLISHED)
    db_session.add(doc)
    db_session.commit()

    report = GovernanceReport(document_id=doc.id, summary="S", executive_summary="E", confidence_score=0.9, review_status="approved", processing_time_seconds=1.0, tokens_used=100, provider_name="m", version=1, is_latest=True)
    db_session.add(report)
    db_session.commit()

    raid = RaidItem(report_id=report.id, type="risk", description="R", severity="critical", risk_score=90)
    db_session.add(raid)
    db_session.commit()

    overdue_task = MitigationTask(
        title="Overdue remediation",
        related_raid_item_id=raid.id,
        owner_role="Analyst",
        priority="P1",
        risk_score=90,
        status="IN_PROGRESS",
        target_date=(datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d"), # overdue
        created_at=datetime.utcnow() - timedelta(days=10),
        updated_at=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(overdue_task)
    db_session.commit()

    # Call /api/notifications to trigger check_dynamic_sla_notifications pull check
    response = client.get("/api/notifications", headers={"X-User-Role": "Analyst"})
    assert response.status_code == 200
    
    # Query database notifications
    notifs = db_session.query(Notification).all()
    # Should have overdue notification for Analyst and SLA breach notifications for Manager and Governance Lead
    assert len(notifs) >= 3
    
    types = [n.notification_type for n in notifs]
    assert "MITIGATION_OVERDUE" in types
    assert "SLA_BREACH" in types


def test_demo_data_seeder(client, db_session):
    # Generate small demo dataset
    response = client.post("/api/demo-data/generate", json={"size": "small"})
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == "small"
    assert "generated small demo dataset" in data["message"].lower()

    # Verify seeded database counts
    assert db_session.query(Document).count() == 3
    assert db_session.query(GovernanceReport).count() == 3
    assert db_session.query(RaidItem).count() > 0
    assert db_session.query(EscalationItem).count() > 0
    assert db_session.query(MitigationTask).count() > 0
    assert db_session.query(Notification).count() > 0
    assert db_session.query(AuditLog).count() > 0
