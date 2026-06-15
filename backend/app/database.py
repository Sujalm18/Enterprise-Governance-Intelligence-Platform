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
    import time
    from sqlalchemy.exc import OperationalError
    from sqlalchemy import inspect
    from backend.app.models import User, Organization
    
    logger.info("Initializing database tables...")
    
    # Retry database connection to handle database startup lag (common in multi-container / cloud environments)
    max_retries = 6
    retry_interval = 5
    inspector = None
    existing_tables = []
    
    for attempt in range(1, max_retries + 1):
        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            break
        except OperationalError as e:
            if attempt == max_retries:
                logger.error("Could not connect to database after %s attempts. Exiting.", max_retries)
                raise e
            logger.warning(
                "Database not ready yet. Retrying in %ss... (Attempt %s/%s)",
                retry_interval, attempt, max_retries
            )
            time.sleep(retry_interval)
            
    if not existing_tables:
        # Completely fresh database -> run migrations directly to create tables and set version
        run_migrations(engine)
    else:
        # Tables exist (either pre-existing database or created via test harness setup)
        Base.metadata.create_all(bind=engine)
        if "alembic_version" not in existing_tables:
            from backend.app.migrations import stamp_migrations
            stamp_migrations(engine)
            
    from backend.app.migrations import auto_repair_schema
    auto_repair_schema(engine)
    validate_database_schema(engine)
    
    db = SessionLocal()
    try:
        # Seed default organizations (required to prevent foreign key constraints on seeded users)
        if db.query(Organization).count() == 0:
            logger.info("Seeding database with default tenant organizations...")
            org1 = Organization(id=1, name="Default Tenant")
            org2 = Organization(id=2, name="Acme Corporation")
            org3 = Organization(id=3, name="Globex Corporation")
            db.add(org1)
            db.add(org2)
            db.add(org3)
            db.commit()
            logger.info("Seed organizations added successfully.")
            
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
