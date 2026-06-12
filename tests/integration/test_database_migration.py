import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.migrations import run_sqlite_migrations, validate_database_schema
from backend.app.models import Document, GovernanceReport, MeetingAction, WorkflowStatus


def _temp_engine():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return engine, db_path


def test_fresh_database_initializes_successfully():
    engine, db_path = _temp_engine()
    try:
        Base.metadata.create_all(bind=engine)
        run_sqlite_migrations(engine)
        validate_database_schema(engine)
    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)


def test_existing_database_upgrades_successfully():
    engine, db_path = _temp_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE governance_reports (id INTEGER PRIMARY KEY, summary TEXT NOT NULL)"))
            conn.execute(text("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE escalation_items (id INTEGER PRIMARY KEY)"))
            conn.execute(text("CREATE TABLE raid_items (id INTEGER PRIMARY KEY)"))

        run_sqlite_migrations(engine)
        validate_database_schema(engine)

        with engine.connect() as conn:
            columns = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(governance_reports)")).fetchall()
            }
            tables = {
                row[0]
                for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            }

        assert "document_type" in columns
        assert "classification_confidence" in columns
        assert "governance_relevance" in columns
        assert "meeting_actions" in tables
    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)


def test_governance_report_fields_and_meeting_actions_persist():
    engine, db_path = _temp_engine()
    try:
        Base.metadata.create_all(bind=engine)
        run_sqlite_migrations(engine)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = Session()

        doc = Document(filename="status.txt", type="txt", status=WorkflowStatus.PENDING_REVIEW)
        db.add(doc)
        db.commit()

        report = GovernanceReport(
            document_id=doc.id,
            summary="Summary",
            executive_summary="Executive summary",
            confidence_score=0.91,
            model_version="mock",
            prompt_version="v1",
            document_type="project_status_report",
            classification_confidence=0.86,
            governance_relevance="high",
            review_status="pending_review",
            processing_time_seconds=1.0,
            tokens_used=42,
            provider_name="mock",
            version=1,
            is_latest=True,
        )
        db.add(report)
        db.commit()

        action = MeetingAction(report_id=report.id, owner="Alex", task="Send RAID update", due_date="2026-06-01")
        db.add(action)
        db.commit()

        saved_report = db.query(GovernanceReport).filter(GovernanceReport.id == report.id).first()
        saved_action = db.query(MeetingAction).filter(MeetingAction.report_id == report.id).first()

        assert saved_report.document_type == "project_status_report"
        assert saved_report.classification_confidence == 0.86
        assert saved_report.governance_relevance == "high"
        assert saved_action.owner == "Alex"
        assert saved_action.task == "Send RAID update"
    finally:
        try:
            db.close()
        except UnboundLocalError:
            pass
        engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)
