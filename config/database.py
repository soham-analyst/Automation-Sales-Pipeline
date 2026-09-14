import os
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Anchor to project root so .env is found regardless of launch directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

DB_SERVER = os.getenv("DB_SERVER", r"(LocalDB)\MSSQLLocalDB")
DB_NAME = os.getenv("DB_NAME", "automated_sales_pipeline")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

# LocalDB uses Windows Authentication — no username/password required.
_conn_str = (
    f"DRIVER={{{DB_DRIVER}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
)

DATABASE_URL = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(_conn_str)
engine = create_engine(DATABASE_URL, fast_executemany=True)