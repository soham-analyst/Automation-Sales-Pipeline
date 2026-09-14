"""
config.py
---------
Central configuration module. Exposes:
  - Directory paths (PROJECT_ROOT, RAW_DATA_DIR, etc.)
  - DB connection helpers (get_db_config, get_connection_string, get_database_url)

No other module should read os.environ directly — import from here so
there's exactly one source of truth.

Usage:
    from config import config

    engine = create_engine(config.get_database_url())
    df.to_csv(config.PROCESSED_DATA_DIR / "output.csv")
"""

import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
ARCHIVE_DATA_DIR = PROJECT_ROOT / "data" / "archive"
REJECTED_DATA_DIR = PROJECT_ROOT / "data" / "rejected"
LOGS_DIR = PROJECT_ROOT / "logs"
SQL_DIR = PROJECT_ROOT / "sql"

# ---------------------------------------------------------------------------
# Database settings (SQL Server LocalDB via Windows Authentication)
# ---------------------------------------------------------------------------
DB_SERVER = os.getenv("DB_SERVER", r"(LocalDB)\MSSQLLocalDB")
DB_NAME = os.getenv("DB_NAME", "automated_sales_pipeline")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

# Legacy MySQL vars kept as empty strings so any code that reads them doesn't crash.
DB_HOST = DB_SERVER  # alias for backward-compat
DB_PORT = ""
DB_USER = ""
DB_PASSWORD = ""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_db_config() -> dict:
    """Return a dict of all resolved DB settings."""
    return {
        "DB_SERVER": DB_SERVER,
        "DB_NAME": DB_NAME,
        "DB_DRIVER": DB_DRIVER,
    }


def get_connection_string() -> str:
    """Build a SQLAlchemy connection URL for SQL Server via pyodbc."""
    odbc = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        "Trusted_Connection=yes;"
    )
    return "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc)


# Alias used by tests
get_database_url = get_connection_string
