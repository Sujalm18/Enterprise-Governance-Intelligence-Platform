import logging
import sys
from pathlib import Path

def setup_logging():
    # Make sure logs directory exists
    log_dir = Path(__file__).resolve().parent.parent.parent / "data" / "logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / "app.log"
    
    # Configure logging formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    
    # Root Logger Config
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Suppress verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger("governance_copilot")
    logger.info("Structured logging initialized. Logs written to %s", log_file)

setup_logging()
