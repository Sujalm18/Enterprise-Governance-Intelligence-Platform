import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.database import Base, engine
from backend.app.migrations import run_sqlite_migrations, validate_database_schema


def main() -> None:
    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    run_sqlite_migrations(engine)
    validate_database_schema(engine)
    print("Database migration complete.")


if __name__ == "__main__":
    main()
