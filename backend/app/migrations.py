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


def run_sqlite_migrations(engine: Engine) -> None:
    """Apply idempotent SQLite migrations required by the governance refactor."""
    if engine.dialect.name != "sqlite":
        logger.info("Skipping SQLite migrations for non-SQLite database dialect: %s", engine.dialect.name)
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    with engine.begin() as conn:
        logger.info("Ensuring organizations table exists")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER NOT NULL,
                    name VARCHAR NOT NULL UNIQUE,
                    created_at DATETIME NOT NULL,
                    slack_webhook_url VARCHAR,
                    teams_webhook_url VARCHAR,
                    PRIMARY KEY (id)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_organizations_id ON organizations (id)"))

        # Seed default tenants if not exist
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO organizations (id, name, created_at)
                VALUES 
                (1, 'Default Tenant', '2026-01-01 00:00:00'),
                (2, 'Acme Corporation', '2026-01-01 00:00:00'),
                (3, 'Globex Corporation', '2026-01-01 00:00:00')
                """
            )
        )

        if "governance_reports" in table_names:
            existing_columns = {
                column["name"]
                for column in inspector.get_columns("governance_reports")
            }
            for column_name, column_type in GOVERNANCE_REPORT_REQUIRED_COLUMNS.items():
                if column_name not in existing_columns:
                    logger.info("Adding missing column governance_reports.%s", column_name)
                    conn.execute(
                        text(f"ALTER TABLE governance_reports ADD COLUMN {column_name} {column_type}")
                    )

        # Apply new workflow alterations across all tables
        for table_name, columns in WORKFLOW_TABLES_COLUMNS.items():
            if table_name in table_names:
                existing_columns = {
                    column["name"]
                    for column in inspector.get_columns(table_name)
                }
                for column_name, column_type in columns.items():
                    if column_name not in existing_columns:
                        logger.info("Adding workflow column %s.%s", table_name, column_name)
                        conn.execute(
                            text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                        )

        logger.info("Ensuring meeting_actions table exists")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS meeting_actions (
                    id INTEGER NOT NULL,
                    report_id INTEGER NOT NULL,
                    owner VARCHAR NOT NULL,
                    task TEXT NOT NULL,
                    due_date VARCHAR,
                    created_at DATETIME NOT NULL,
                    tenant_id INTEGER DEFAULT 1,
                    PRIMARY KEY (id),
                    FOREIGN KEY(report_id) REFERENCES governance_reports (id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_meeting_actions_id ON meeting_actions (id)"))

        logger.info("Ensuring mitigation_tasks table exists")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS mitigation_tasks (
                    id INTEGER NOT NULL,
                    title VARCHAR NOT NULL,
                    description TEXT,
                    related_raid_item_id INTEGER NOT NULL,
                    related_escalation_id INTEGER,
                    owner_role VARCHAR NOT NULL,
                    owner_name VARCHAR,
                    priority VARCHAR NOT NULL,
                    risk_score INTEGER NOT NULL,
                    target_date VARCHAR,
                    sla_status VARCHAR NOT NULL DEFAULT 'ON_TRACK',
                    status VARCHAR NOT NULL DEFAULT 'PLANNED',
                    completion_percentage INTEGER NOT NULL DEFAULT 0,
                    effectiveness INTEGER NOT NULL DEFAULT 20,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    verified_at DATETIME,
                    tenant_id INTEGER DEFAULT 1,
                    PRIMARY KEY (id),
                    FOREIGN KEY(related_raid_item_id) REFERENCES raid_items (id) ON DELETE CASCADE,
                    FOREIGN KEY(related_escalation_id) REFERENCES escalation_items (id) ON DELETE SET NULL
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mitigation_tasks_id ON mitigation_tasks (id)"))

        logger.info("Ensuring notifications table exists")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER NOT NULL,
                    severity VARCHAR NOT NULL,
                    notification_type VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    message TEXT NOT NULL,
                    recipient_role VARCHAR NOT NULL,
                    related_entity_type VARCHAR,
                    related_entity_id INTEGER,
                    read_status BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL,
                    tenant_id INTEGER DEFAULT 1,
                    PRIMARY KEY (id)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications (id)"))

        logger.info("Ensuring governance_trend_snapshots table exists")
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS governance_trend_snapshots (
                    id INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    health_score INTEGER NOT NULL,
                    maturity_score INTEGER NOT NULL,
                    risk_exposure INTEGER NOT NULL,
                    mitigation_effectiveness_pct FLOAT NOT NULL,
                    sla_breaches INTEGER NOT NULL,
                    open_escalations INTEGER NOT NULL,
                    verified_mitigations INTEGER NOT NULL,
                    critical_risks INTEGER NOT NULL,
                    notification_volume INTEGER NOT NULL,
                    tenant_id INTEGER DEFAULT 1,
                    PRIMARY KEY (id)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_governance_trend_snapshots_id ON governance_trend_snapshots (id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_governance_trend_snapshots_timestamp ON governance_trend_snapshots (timestamp)"))



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
    return "no such column:" in str(error).lower() or "no such table:" in str(error).lower()
