"""
test_db_connection.py
----------------------
Standalone sanity check: confirms Python can reach MySQL using the
credentials in .env, before you trust any pipeline code with it.

Run from the project root:
    python scripts/test_db_connection.py
"""

import sys
from pathlib import Path

# Allow running this script directly (python scripts/test_db_connection.py)
# by adding the project root to sys.path.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text

from config.config import get_connection_string, get_db_config


def main():
    cfg = get_db_config()
    print(f"Connecting to MySQL at {cfg['DB_HOST']}:{cfg['DB_PORT']}/{cfg['DB_NAME']} "
          f"as user '{cfg['DB_USER']}' ...")

    engine = create_engine(get_connection_string())

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION();"))
            version = result.scalar()
            print(f"SUCCESS: connected. MySQL server version: {version}")
    except Exception as exc:
        print(f"FAILED to connect: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
