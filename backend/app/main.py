import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging configuration before doing imports
from backend.app.logging_config import setup_logging
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.api.endpoints import router as api_router

logger = logging.getLogger("governance_copilot.main")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Governance & Operations Copilot - REST API Backend",
    version="1.0.0"
)

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev environments, streamline origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register routers
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def on_startup():
    logger.info("Starting Enterprise AI Governance & Operations Copilot API Backend...")
    # Setup database schemas and seed default users
    init_db()
    logger.info("Database initialized successfully.")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "active_provider": settings.AI_PROVIDER,
        "mock_mode_active": settings.USE_MOCK_MODE
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "governance-intelligence-api",
        "provider": settings.AI_PROVIDER,
        "mock_mode_active": settings.USE_MOCK_MODE
    }
