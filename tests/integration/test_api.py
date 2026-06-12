import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Document, GovernanceReport, EscalationItem, WorkflowStatus

@pytest.fixture(name="client")
def fixture_client():
    """Sets up a TestClient with a temporary SQLite database override."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # Close file descriptor immediately to release Windows file lock
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionTest()
    
    # Seed mock user
    db.add(User(username="test_reviewer", role="reviewer"))
    db.commit()
    db.close()
    
    # Define dependency override — yield a new session each time
    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    # Instantiate client
    tc = TestClient(app)
    
    test_session = SessionTest()
    yield tc, test_session
    test_session.close()
    
    # Tear down
    app.dependency_overrides.clear()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

def test_read_root(client):
    tc, _ = client
    response = tc.get("/")
    assert response.status_code == 200
    assert "app_name" in response.json()

def test_health_check(client):
    tc, _ = client
    response = tc.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_stats(client):
    tc, db = client
    
    # Add dummy document and report to verify stats compilation
    doc = Document(filename="test.txt", type="txt", status=WorkflowStatus.PENDING_REVIEW)
    db.add(doc)
    db.commit()
    
    report = GovernanceReport(
        document_id=doc.id,
        summary="Summary test",
        executive_summary="Exec summary test",
        confidence_score=0.92,
        model_version="mock",
        review_status="pending_review",
        processing_time_seconds=1.2,
        tokens_used=120,
        provider_name="mock",
        version=1,
        is_latest=True
    )
    db.add(report)
    db.commit()
    
    response = tc.get("/api/governance/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_documents"] == 1
    assert data["pending_reviews"] == 1
    assert data["average_confidence"] == 0.92

def test_route_escalation(client):
    tc, db = client
    
    doc = Document(filename="test.txt", type="txt", status=WorkflowStatus.PENDING_REVIEW)
    db.add(doc)
    db.commit()
    
    report = GovernanceReport(
        document_id=doc.id,
        summary="Summary test",
        executive_summary="Exec summary test",
        confidence_score=0.90,
        model_version="mock",
        review_status="pending_review",
        processing_time_seconds=1.2,
        tokens_used=120,
        provider_name="mock",
        version=1,
        is_latest=True
    )
    db.add(report)
    db.commit()
    
    esc = EscalationItem(
        report_id=report.id,
        description="Oracle contract dispute",
        severity="high",
        status="open",
        confidence_score=0.88
    )
    db.add(esc)
    db.commit()
    
    # Execute routing post request with Manager role header
    response = tc.post(
        f"/api/governance/escalations/{esc.id}/route",
        json={"routing_target": "Legal Counsel"},
        headers={"X-User-Role": "Manager"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ASSIGNED"
    assert data["routing_target"] == "Legal Counsel"

def test_review_report(client):
    tc, db = client
    
    doc = Document(filename="test.txt", type="txt", status=WorkflowStatus.PENDING_REVIEW)
    db.add(doc)
    db.commit()
    
    report = GovernanceReport(
        document_id=doc.id,
        summary="Summary test",
        executive_summary="Exec summary test",
        confidence_score=0.90,
        model_version="mock",
        review_status="pending_review",
        processing_time_seconds=1.2,
        tokens_used=120,
        provider_name="mock",
        version=1,
        is_latest=True
    )
    db.add(report)
    db.commit()
    
    # Patch report review status to approved with Manager role header
    response = tc.patch(
        f"/api/governance/reports/{report.id}/review",
        json={
            "reviewer": "test_reviewer",
            "review_status": "approved",
            "review_notes": "Looks solid, ready to publish."
        },
        headers={"X-User-Role": "Manager"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "approved"
    assert data["reviewer"] == "test_reviewer"
    
    # Document state should update to PUBLISHED
    # Re-query since endpoint uses a separate session context
    refreshed_doc = db.query(Document).filter(Document.id == doc.id).first()
    assert refreshed_doc.status == WorkflowStatus.PUBLISHED
