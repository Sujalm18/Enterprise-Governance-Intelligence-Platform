import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import settings
from backend.app.migrations import run_migrations, validate_database_schema

logger = logging.getLogger("governance_copilot.database")

engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database, creates tables, and seeds initial users."""
    from backend.app.models import User
    
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    validate_database_schema(engine)
    
    db = SessionLocal()
    try:
        # Check if users already exist, if not seed them
        if db.query(User).count() == 0:
            logger.info("Seeding database with default analyst and reviewer roles...")
            analyst = User(username="analyst_user", role="analyst")
            reviewer = User(username="reviewer_user", role="reviewer")
            db.add(analyst)
            db.add(reviewer)
            db.commit()
            logger.info("Seed users added successfully.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
