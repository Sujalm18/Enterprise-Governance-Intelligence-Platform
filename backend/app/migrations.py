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

REQUIRED_TABLES = {"meeting_actions"}


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
                    PRIMARY KEY (id),
                    FOREIGN KEY(report_id) REFERENCES governance_reports (id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_meeting_actions_id ON meeting_actions (id)"))


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
