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
    from sqlalchemy import inspect
    
    logger.info("Initializing database tables...")
    
    # Check if the database has any tables already
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        # Completely fresh database -> run migrations directly to create tables and set version
        run_migrations(engine)
    else:
        # Tables exist (either pre-existing database or created via test harness setup)
        Base.metadata.create_all(bind=engine)
        if "alembic_version" not in existing_tables:
            from backend.app.migrations import stamp_migrations
            stamp_migrations(engine)
            
    validate_database_schema(engine)

    
    db = SessionLocal()
    try:
        # Check if users already exist, if not seed them
        if db.query(User).count() == 0:
            logger.info("Seeding database with default analyst and reviewer roles...")
            from backend.app.auth import get_password_hash
            analyst = User(
                username="analyst_user",
                role="analyst",
                password_hash=get_password_hash("analyst123")
            )
            reviewer = User(
                username="reviewer_user",
                role="reviewer",
                password_hash=get_password_hash("reviewer123")
            )
            db.add(analyst)
            db.add(reviewer)
            db.commit()
            logger.info("Seed users added successfully.")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
