from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.database import Base, engine


def _sqlite_path_from_url(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("reset_database.py only supports sqlite:/// database URLs.")
    return Path(database_url.replace("sqlite:///", "", 1))


def main() -> None:
    import backend.app.models  # noqa: F401

    db_path = _sqlite_path_from_url(settings.DATABASE_URL)
    if db_path.exists():
        db_path.unlink()

    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")
    print("All tables recreated successfully.")


if __name__ == "__main__":
    main()
