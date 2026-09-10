"""
config.py
Loads DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD from environment
variables (.env). Provides pipeline path constants and database configuration.
"""

import os
from pathlib import Path

# Try importing dotenv if available
try:
    from dotenv import load_dotenv

    # Base directory is project root (parent of config/)
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Project Paths
PROJECT_ROOT = BASE_DIR
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARCHIVE_DATA_DIR = DATA_DIR / "archive"
REJECTED_DATA_DIR = DATA_DIR / "rejected"
LOGS_DIR = BASE_DIR / "logs"
SQL_DIR = BASE_DIR / "sql"

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "sales_dw")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Environment Settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def get_database_url() -> str:
    """Generate SQLAlchemy connection URL for MySQL."""
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
