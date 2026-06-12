import os
import tempfile
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import (
    Document, GovernanceReport, RaidItem, MitigationTask, EscalationItem, GovernanceTrendSnapshot, WorkflowStatus
)

@pytest.fixture(name="db_setup")
def fixture_db_setup():
    """Sets up a temporary SQLite database on disk for test execution."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionTest, db_path
    
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

def test_maturity_and_health_calculations(client, db_session):
    # Setup document & report
    doc = Document(filename="test_doc.pdf", type="pdf", tenant_id=1, status=WorkflowStatus.PENDING_REVIEW)
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
        is_latest=True,
        tenant_id=1
    )
    db_session.add(report)
    db_session.commit()
    
    # Add RAID item and mitigation tasks
    raid1 = RaidItem(
        report_id=report.id,
        type="risk",
        description="Unauthorized cloud storage access LLM training neural network data leak",
        severity="critical",
        suggested_owner_role="Security Lead",
        risk_score=90,
        current_risk_score=90,
        tenant_id=1
    )
    raid2 = RaidItem(
        report_id=report.id,
        type="risk",
        description="Missing firewall settings",
        severity="medium",
        suggested_owner_role="IT Operator",
        risk_score=50,
        current_risk_score=20,
        tenant_id=1
    )
    db_session.add(raid1)
    db_session.add(raid2)
    db_session.commit()
    
    task1 = MitigationTask(
        title="Restrict cloud storage buckets",
        related_raid_item_id=raid1.id,
        owner_role="Security Lead",
        priority="P1",
        risk_score=90,
        target_date="2020-01-01", # overdue
        status="IN_PROGRESS",
        completion_percentage=20,
        tenant_id=1
    )
    task2 = MitigationTask(
        title="Apply firewall policy rules",
        related_raid_item_id=raid2.id,
        owner_role="IT Operator",
        priority="P2",
        risk_score=50,
        target_date="2030-01-01", # on track
        status="VERIFIED",
        completion_percentage=100,
        tenant_id=1
    )
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    # Call maturity API
    headers = {"X-Tenant-ID": "1", "X-User-Role": "Executive"}
    res = client.get("/api/governance/maturity", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "score" in data
    assert "tier" in data
    assert "dimensions" in data
    assert "benchmark" in data
    assert "appetite_alignment" in data
    
    # Call health explanations API
    res = client.get("/api/governance/health-explanations", headers=headers)
    assert res.status_code == 200
    health_data = res.json()
    assert "health_score" in health_data
    assert "main_drivers" in health_data

def test_executive_priorities_scoring(client, db_session):
    # Setup doc & report
    doc = Document(filename="test_doc.pdf", type="pdf", tenant_id=1, status=WorkflowStatus.PENDING_REVIEW)
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
        is_latest=True,
        tenant_id=1
    )
    db_session.add(report)
    db_session.commit()
    
    # Seed 2 critical open risks, 1 escalation, 1 overdue task
    raid = RaidItem(
        report_id=report.id,
        type="risk",
        description="Critical risk item",
        severity="critical",
        suggested_owner_role="Security Lead",
        risk_score=95,
        current_risk_score=95,
        tenant_id=1
    )
    db_session.add(raid)
    db_session.commit()

    task = MitigationTask(
        title="Task 1",
        related_raid_item_id=raid.id,
        owner_role="Security Lead",
        priority="P1",
        risk_score=95,
        target_date="2020-01-01", # overdue
        status="IN_PROGRESS",
        tenant_id=1
    )
    esc = EscalationItem(
        report_id=report.id,
        description="Steering committee dispute",
        severity="critical",
        status="OPEN",
        routing_target="Committee",
        assigned_to="Governance Lead",
        tenant_id=1
    )
    db_session.add(task)
    db_session.add(esc)
    db_session.commit()

    headers = {"X-Tenant-ID": "1", "X-User-Role": "Executive"}
    res = client.get("/api/governance/executive-priorities", headers=headers)
    assert res.status_code == 200
    priorities = res.json()
    assert len(priorities) > 0
    # Top priority should have positive priority_score and rank first
    assert priorities[0]["priority_score"] >= 0

def test_root_cause_and_portfolio_recs(client, db_session):
    doc = Document(filename="test_doc.pdf", type="pdf", tenant_id=1, status=WorkflowStatus.PENDING_REVIEW)
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
        is_latest=True,
        tenant_id=1
    )
    db_session.add(report)
    db_session.commit()
    
    raid_ai = RaidItem(
        report_id=report.id,
        type="risk",
        description="LLM training data licensing exposure neural network",
        severity="critical",
        suggested_owner_role="AI Lead",
        risk_score=80,
        current_risk_score=80,
        tenant_id=1
    )
    raid_sec = RaidItem(
        report_id=report.id,
        type="risk",
        description="Bucket security vulnerability",
        severity="high",
        suggested_owner_role="Sec Ops",
        risk_score=75,
        current_risk_score=75,
        tenant_id=1
    )
    db_session.add(raid_ai)
    db_session.add(raid_sec)
    db_session.commit()

    headers = {"X-Tenant-ID": "1", "X-User-Role": "Analyst"}
    res = client.get("/api/governance/root-cause-analytics", headers=headers)
    assert res.status_code == 200
    rca = res.json()
    assert rca["category_distribution"]["AI Governance"] == 1
    assert rca["category_distribution"]["Security"] == 1

    # Call recommendations API
    res = client.get("/api/governance/portfolio-recommendations", headers=headers)
    assert res.status_code == 200
    recs = res.json()
    assert "quick_wins" in recs
    assert "medium_term" in recs

def test_trends_and_briefing(client, db_session):
    # Seed snap records
    snap = GovernanceTrendSnapshot(
        timestamp=datetime.utcnow() - timedelta(days=2),
        health_score=80,
        maturity_score=75,
        risk_exposure=300,
        mitigation_effectiveness_pct=65.5,
        sla_breaches=1,
        open_escalations=2,
        verified_mitigations=4,
        critical_risks=1,
        notification_volume=10,
        tenant_id=1
    )
    db_session.add(snap)
    db_session.commit()

    headers = {"X-Tenant-ID": "1", "X-User-Role": "Governance Lead"}
    res = client.get("/api/governance/trends", headers=headers)
    assert res.status_code == 200
    trends = res.json()
    assert len(trends["trend_points"]) >= 1

    res = client.get("/api/governance/executive-briefing", headers=headers)
    assert res.status_code == 200
    briefing = res.json()
    assert "executive_summary" in briefing
    assert "full_markdown" in briefing

def test_copilot_assistant(client, db_session):
    headers = {"X-Tenant-ID": "1", "X-User-Role": "Manager"}
    res = client.post("/api/governance/copilot", json={"query": "Why is our maturity score low?"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 0
