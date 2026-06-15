import logging
import re

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("governance_copilot.database.migrations")

GOVERNANCE_REPORT_REQUIRED_COLUMNS = {
    "document_type": "VARCHAR",
    "classification_confidence": "FLOAT",
    "governance_relevance": "VARCHAR",
}

# New workflow columns to alter dynamically
WORKFLOW_TABLES_COLUMNS = {
    "organizations": {
        "slack_webhook_url": "VARCHAR",
        "teams_webhook_url": "VARCHAR",
    },
    "users": {
        "tenant_id": "INTEGER DEFAULT 1",
        "password_hash": "VARCHAR",
    },
    "documents": {
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "workflow_jobs": {
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "governance_reports": {
        "created_by": "VARCHAR DEFAULT 'Analyst'",
        "assigned_to": "VARCHAR DEFAULT 'Manager'",
        "approved_by": "VARCHAR",
        "status": "VARCHAR DEFAULT 'PENDING_MANAGER_REVIEW'",
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "escalation_items": {
        "raised_by": "VARCHAR",
        "assigned_to": "VARCHAR",
        "resolved_by": "VARCHAR",
        "remediation_plan": "TEXT",
        "expected_risk_reduction": "VARCHAR",
        "priority": "VARCHAR",
        "suggested_owner_role": "VARCHAR",
        "risk_score": "INTEGER DEFAULT 0",
        "explainability_trace": "TEXT",
        "explain_why": "TEXT",
        "suggested_actions": "TEXT",
        "estimated_impact": "TEXT",
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "raid_items": {
        "recommended_mitigations": "TEXT",
        "implementation_effort": "VARCHAR",
        "expected_risk_reduction": "VARCHAR",
        "recommended_priority": "VARCHAR",
        "suggested_owner_role": "VARCHAR",
        "priority": "VARCHAR",
        "risk_score": "INTEGER DEFAULT 0",
        "current_risk_score": "INTEGER DEFAULT 0",
        "explainability_trace": "TEXT",
        "explain_why": "TEXT",
        "suggested_actions": "TEXT",
        "estimated_impact": "TEXT",
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "meeting_actions": {
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "mitigation_tasks": {
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "audit_logs": {
        "user_role": "VARCHAR DEFAULT 'Analyst'",
        "action": "VARCHAR DEFAULT 'event'",
        "entity_type": "VARCHAR",
        "entity_id": "INTEGER",
        "tenant_id": "INTEGER DEFAULT 1",
    },
    "notifications": {
        "tenant_id": "INTEGER DEFAULT 1",
    }
}

REQUIRED_TABLES = {"organizations", "meeting_actions", "audit_logs", "governance_reports", "escalation_items", "raid_items", "mitigation_tasks", "notifications", "governance_trend_snapshots"}


class DatabaseSchemaMismatchError(RuntimeError):
    """Raised when the database schema does not match the SQLAlchemy models."""


def _is_postgres(engine: Engine) -> bool:
    return engine.dialect.name == "postgresql"


def _datetime_type(engine: Engine) -> str:
    return "TIMESTAMP" if _is_postgres(engine) else "DATETIME"


def _bool_default_false(engine: Engine) -> str:
    return "BOOLEAN NOT NULL DEFAULT FALSE" if _is_postgres(engine) else "BOOLEAN NOT NULL DEFAULT 0"


def _serial_pk(engine: Engine) -> str:
    return "SERIAL PRIMARY KEY" if _is_postgres(engine) else "INTEGER NOT NULL PRIMARY KEY"


def _insert_ignore_organizations(engine: Engine) -> str:
    """Return the dialect-appropriate INSERT-if-not-exists for seed tenants."""
    if _is_postgres(engine):
        return """
            INSERT INTO organizations (id, name, created_at)
            VALUES 
            (1, 'Default Tenant', '2026-01-01 00:00:00'),
            (2, 'Acme Corporation', '2026-01-01 00:00:00'),
            (3, 'Globex Corporation', '2026-01-01 00:00:00')
            ON CONFLICT (id) DO NOTHING
        """
    else:
        return """
            INSERT OR IGNORE INTO organizations (id, name, created_at)
            VALUES 
            (1, 'Default Tenant', '2026-01-01 00:00:00'),
            (2, 'Acme Corporation', '2026-01-01 00:00:00'),
            (3, 'Globex Corporation', '2026-01-01 00:00:00')
        """


def _add_column_if_missing(conn, inspector, table_name: str, column_name: str, column_type: str, is_pg: bool) -> None:
    """Add a column to a table if it doesn't already exist, dialect-aware."""
    existing_columns = {
        column["name"]
        for column in inspector.get_columns(table_name)
    }
    if column_name not in existing_columns:
        logger.info("Adding column %s.%s (%s)", table_name, column_name, column_type)
        if is_pg:
            # PostgreSQL: wrap in DO block to gracefully handle race conditions
            conn.execute(text(
                f"""
                DO $$
                BEGIN
                    ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};
                EXCEPTION
                    WHEN duplicate_column THEN
                        NULL;
                END $$;
                """
            ))
        else:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))


def run_migrations(engine: Engine) -> None:
    """Apply database migrations programmatically via Alembic."""
    logger.info("Running database migrations programmatically via Alembic...")
    from alembic.config import Config
    from alembic import command
    from pathlib import Path
    
    # Instantiate Alembic Config programmatically without an ini file
    alembic_cfg = Config()
    
    # Locate alembic directory relative to this file
    alembic_dir = Path(__file__).resolve().parent.parent / "alembic"
    
    # Set config options programmatically
    alembic_cfg.set_main_option("script_location", str(alembic_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations completed successfully.")


def stamp_migrations(engine: Engine) -> None:
    """Stamp the database schema to the latest Alembic revision."""
    logger.info("Stamping database schema version to head...")
    from alembic.config import Config
    from alembic import command
    from pathlib import Path
    
    alembic_cfg = Config()
    alembic_dir = Path(__file__).resolve().parent.parent / "alembic"
    alembic_cfg.set_main_option("script_location", str(alembic_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    
    command.stamp(alembic_cfg, "head")
    logger.info("Database stamped to head successfully.")


# Legacy alias for backward compatibility
def run_sqlite_migrations(engine: Engine) -> None:
    """Legacy wrapper — delegates to the dialect-aware run_migrations."""
    run_migrations(engine)



def validate_database_schema(engine: Engine) -> None:
    """Validate the tables and columns required by current application queries."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    missing_tables = sorted(REQUIRED_TABLES - table_names)

    missing_columns = []
    if "governance_reports" in table_names:
        governance_columns = {
            column["name"]
            for column in inspector.get_columns("governance_reports")
        }
        for column_name in GOVERNANCE_REPORT_REQUIRED_COLUMNS:
            if column_name not in governance_columns:
                missing_columns.append(f"governance_reports.{column_name}")

    # Validate workflow columns
    for table_name, columns in WORKFLOW_TABLES_COLUMNS.items():
        if table_name in table_names:
            table_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }
            for column_name in columns:
                if column_name not in table_columns:
                    missing_columns.append(f"{table_name}.{column_name}")

    if missing_tables or missing_columns:
        logger.error("Database schema is outdated.")
        logger.error("Migration required.")
        details = []
        if missing_tables:
            details.append(f"Missing tables: {', '.join(missing_tables)}")
        if missing_columns:
            details.append(f"Missing columns: {', '.join(missing_columns)}")
        raise DatabaseSchemaMismatchError("; ".join(details))


def schema_mismatch_response_detail(error: Exception) -> str:
    """Convert low-level DB schema errors into an operator-friendly API message."""
    message = str(error)
    column_match = re.search(r"no such column:\s*([\w.]+)", message)
    expected_column = column_match.group(1) if column_match else "unknown"
    return (
        "Database schema mismatch detected.\n"
        "Expected column:\n"
        f"{expected_column}\n\n"
        "Please run database migration."
    )


def is_schema_mismatch_error(error: Exception) -> bool:
    msg = str(error).lower()
    return "no such column:" in msg or "no such table:" in msg or "does not exist" in msg
