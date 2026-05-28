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

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "Enterprise AI Governance & Operations Copilot"
    DEBUG: bool = True
    
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
        # Check environment for Anthropic API Key directly if not set by pydantic settings
        api_key = os.environ.get("ANTHROPIC_API_KEY", self.ANTHROPIC_API_KEY)
        if api_key:
            self.ANTHROPIC_API_KEY = api_key
            self.USE_MOCK_MODE = False
            self.AI_PROVIDER = "anthropic"
        else:
            self.USE_MOCK_MODE = True
            self.AI_PROVIDER = "mock"

settings = Settings()
