import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    Document, WorkflowJob, WorkflowStatus, GovernanceReport, AuditLog, User
)
from backend.app.services import workflow as workflow_module
from backend.app import database as database_module

@pytest.fixture(name="test_db")
def fixture_test_db():
    """Creates a temporary database file for integration testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # Release Windows file lock immediately
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionTest()

    # Seed default users
    db.add(User(username="analyst_user", role="analyst"))
    db.add(User(username="reviewer_user", role="reviewer"))
    db.commit()

    yield db

    db.close()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_workflow_pipeline_execution(test_db, monkeypatch):
    """Simulates uploading and processing a text document through the pipeline."""

    # Get the engine from the test session and create a proper factory
    test_engine = test_db.get_bind()
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Override SessionLocal so the pipeline creates its own session from the same engine
    monkeypatch.setattr(database_module, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(workflow_module, "SessionLocal", TestSessionLocal)

    # Create a temp text file as the source document
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write(
            "Project Apollo status update. Critical Action: Analyst to finish code by Monday. "
            "Risk: API environment delays may impact integration timeline. "
            "Escalation: Vendor billing dispute requires executive attention."
        )
        temp_path = f.name

    try:
        # Create Document + WorkflowJob in test DB
        doc = Document(filename=temp_path, type="txt", status=WorkflowStatus.UPLOADED)
        test_db.add(doc)
        test_db.commit()

        job = WorkflowJob(document_id=doc.id, status=WorkflowStatus.UPLOADED, logs="")
        test_db.add(job)
        test_db.commit()

        doc_id = doc.id
        job_id = job.id

        # Execute pipeline (this will create and close its own session)
        await workflow_module.process_document_pipeline(document_id=doc_id, job_id=job_id)

        # Use a fresh session to query results (pipeline closed its own session)
        verify_db = TestSessionLocal()
        try:
            updated_doc = verify_db.query(Document).filter(Document.id == doc_id).first()
            updated_job = verify_db.query(WorkflowJob).filter(WorkflowJob.id == job_id).first()

            assert updated_doc.status == WorkflowStatus.PENDING_REVIEW
            assert updated_job.status == WorkflowStatus.PENDING_REVIEW
            assert "Awaiting reviewer action" in updated_job.logs

            # Verify report was created with correct versioning
            report = verify_db.query(GovernanceReport).filter(GovernanceReport.document_id == doc_id).first()
            assert report is not None
            assert report.version == 1
            assert report.is_latest is True

            # Verify audit trail was written
            audit_events = [log.event for log in verify_db.query(AuditLog).all()]
            assert "Processed" in audit_events
            assert "Review Pending" in audit_events
        finally:
            verify_db.close()

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

