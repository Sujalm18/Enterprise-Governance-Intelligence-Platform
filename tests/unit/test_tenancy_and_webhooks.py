import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Organization, GovernanceReport, RaidItem, EscalationItem, Document
from backend.app.api.endpoints import get_current_tenant


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
    # Seed default organizations for tenancy checks
    org1 = Organization(id=1, name="Default Tenant")
    org2 = Organization(id=2, name="Acme Corp")
    db.add_all([org1, org2])
    db.commit()
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


def test_get_current_tenant_helper():
    # Test valid parsing
    assert get_current_tenant("1") == 1
    assert get_current_tenant("42") == 42
    # Test invalid string fallbacks
    assert get_current_tenant("invalid") == 1
    assert get_current_tenant(None) == 1


def test_integration_settings_endpoints(client, db_session):
    # Test default empty URLs
    response = client.get("/api/governance/integrations", headers={"X-Tenant-ID": "2"})
    assert response.status_code == 200
    assert response.json()["slack_webhook_url"] is None
    assert response.json()["teams_webhook_url"] is None

    # Test update webhooks URL
    payload = {
        "slack_webhook_url": "https://hooks.slack.com/services/test1",
        "teams_webhook_url": "https://outlook.office.com/webhook/test2"
    }
    response = client.post("/api/governance/integrations", json=payload, headers={"X-Tenant-ID": "2"})
    assert response.status_code == 200
    data = response.json()
    assert data["slack_webhook_url"] == "https://hooks.slack.com/services/test1"
    assert data["teams_webhook_url"] == "https://outlook.office.com/webhook/test2"

    # Verify state inside database for tenant 2
    org2 = db_session.query(Organization).filter(Organization.id == 2).first()
    assert org2.slack_webhook_url == "https://hooks.slack.com/services/test1"
    assert org2.teams_webhook_url == "https://outlook.office.com/webhook/test2"

    # Verify tenant 1 remains empty/unaffected (isolation check)
    org1 = db_session.query(Organization).filter(Organization.id == 1).first()
    assert org1.slack_webhook_url is None
    assert org1.teams_webhook_url is None


def test_tenant_data_isolation(client, db_session):
    # Seed documents
    doc1 = Document(id=1, filename="doc1.pdf", type="pdf", tenant_id=1)
    doc2 = Document(id=2, filename="doc2.pdf", type="pdf", tenant_id=2)
    db_session.add_all([doc1, doc2])
    db_session.commit()

    # Seed report and raid items for Tenant 1
    r1 = GovernanceReport(
        id=101,
        document_id=1,
        summary="Tenant 1 Report",
        executive_summary="Tenant 1 Executive Summary",
        is_latest=True,
        review_status="draft",
        tenant_id=1
    )
    # Seed report and raid items for Tenant 2
    r2 = GovernanceReport(
        id=102,
        document_id=2,
        summary="Tenant 2 Report",
        executive_summary="Tenant 2 Executive Summary",
        is_latest=True,
        review_status="draft",
        tenant_id=2
    )
    db_session.add_all([r1, r2])
    db_session.commit()


    # Query with tenant 1 header
    response = client.get("/api/governance/reports", headers={"X-Tenant-ID": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 101

    # Query with tenant 2 header
    response = client.get("/api/governance/reports", headers={"X-Tenant-ID": "2"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 102


@patch("backend.app.services.integrations.requests.post")
def test_webhook_alerts_dispatch(mock_post):
    from backend.app.services.integrations import send_slack_alert, send_teams_alert
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_return = mock_response
    mock_post.return_value = mock_response

    # Test slack trigger
    success_slack = send_slack_alert(
        webhook_url="https://hooks.slack.com/services/dummy",
        title="Critical Alert",
        message="Compliance Failure",
        severity="critical"
    )
    assert success_slack is True
    mock_post.assert_called_once()
    
    # Test teams trigger
    mock_post.reset_mock()
    mock_response.status_code = 201
    success_teams = send_teams_alert(
        webhook_url="https://outlook.office.com/webhook/dummy",
        title="SLA Breach Alert",
        message="Mitigation is overdue",
        severity="high"
    )
    assert success_teams is True
    mock_post.assert_called_once()
