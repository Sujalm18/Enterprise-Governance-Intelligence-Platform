import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Ensure data and uploads directories exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
UPLOADS_DIR.mkdir(exist_ok=True, parents=True)
PROMPTS_DIR.mkdir(exist_ok=True, parents=True)

DEFAULT_CORS_ORIGINS = (
    "https://radiant-intuition-production-3a80.up.railway.app",
    "http://localhost:5173",
    "http://localhost:3000",
)

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "Enterprise AI Governance & Operations Copilot"
    DEBUG: bool = True
    FRONTEND_ORIGIN: str = "https://radiant-intuition-production-3a80.up.railway.app"
    CORS_ORIGINS: str = ",".join(DEFAULT_CORS_ORIGINS)
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # DB & File Storage Settings
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/governance.db"
    UPLOAD_DIR: str = str(UPLOADS_DIR)
    
    # RAG Ingestion Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    USE_RAG: bool = True
    
    # AI Settings
    ANTHROPIC_API_KEY: str = ""
    # Defaults to mock if key is empty
    USE_MOCK_MODE: bool = True
    AI_PROVIDER: str = "mock"  # "anthropic" or "mock"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

    def model_post_init(self, __context) -> None:
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

        # Check environment for Anthropic API Key directly if not set by pydantic settings
        api_key = os.environ.get("ANTHROPIC_API_KEY", self.ANTHROPIC_API_KEY)
        if api_key:
            self.ANTHROPIC_API_KEY = api_key
            self.USE_MOCK_MODE = False
            self.AI_PROVIDER = "anthropic"
        else:
            self.USE_MOCK_MODE = True
            self.AI_PROVIDER = "mock"

    @property
    def cors_origins(self) -> list[str]:
        origins = set(DEFAULT_CORS_ORIGINS)
        origins.update({
            origin.strip().rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        })
        if self.FRONTEND_ORIGIN.strip():
            origins.add(self.FRONTEND_ORIGIN.strip().rstrip("/"))
        return sorted(origins) or ["http://localhost:5173"]

settings = Settings()
