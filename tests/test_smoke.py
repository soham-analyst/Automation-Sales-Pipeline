"""
test_smoke.py

Basic sanity and smoke tests to ensure repository structure,
configuration loading, and key pipeline components are properly configured.

Compatible with both pytest and standard unittest.
"""

import unittest
from urllib.parse import unquote

from config import config


class TestSmoke(unittest.TestCase):

    def test_project_root_structure(self):
        """Verify that all essential directories exist in the project."""

        self.assertTrue(
            config.PROJECT_ROOT.exists(),
            "Project root directory does not exist",
        )

        self.assertTrue(
            config.RAW_DATA_DIR.exists(),
            "Raw data directory does not exist",
        )

        self.assertTrue(
            config.PROCESSED_DATA_DIR.exists(),
            "Processed data directory does not exist",
        )

        self.assertTrue(
            config.ARCHIVE_DATA_DIR.exists(),
            "Archive data directory does not exist",
        )

        self.assertTrue(
            config.REJECTED_DATA_DIR.exists(),
            "Rejected data directory does not exist",
        )

        self.assertTrue(
            config.LOGS_DIR.exists(),
            "Logs directory does not exist",
        )

        self.assertTrue(
            config.SQL_DIR.exists(),
            "SQL directory does not exist",
        )

    def test_env_example_matches_config(self):
        """Verify that .env.example contains expected environment variables."""

        env_example_path = config.PROJECT_ROOT / ".env.example"

        self.assertTrue(
            env_example_path.exists(),
            ".env.example is missing",
        )

        content = env_example_path.read_text(encoding="utf-8")

        expected_keys = [
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "ENVIRONMENT",
        ]

        for key in expected_keys:
            self.assertIn(
                key,
                content,
                f"Key '{key}' missing from .env.example",
            )

    def test_database_url_formatting(self):
        """Verify SQL Server LocalDB URL generation."""

        url = config.get_database_url()
        decoded_url = unquote(url)

        self.assertTrue(
            url.startswith("mssql+pyodbc://"),
            "Database URL must use the mssql+pyodbc dialect",
        )

        self.assertIn(
            config.DB_HOST,
            decoded_url,
            "Database host is missing from the decoded URL",
        )

        self.assertIn(
            config.DB_NAME,
            decoded_url,
            "Database name is missing from the decoded URL",
        )

        # SQL Server LocalDB uses a named instance and normally does not
        # require a separate port in the connection string.
        if config.DB_PORT:
            self.assertTrue(
                str(config.DB_PORT) == "3306"
                or str(config.DB_PORT) in decoded_url
                or "LocalDB" in config.DB_HOST,
                "Database port configuration is inconsistent",
            )

    def test_documentation_and_sql_files_exist(self):
        """Verify documentation and SQL schema files exist."""

        data_dict = config.PROJECT_ROOT / "docs" / "data_dictionary.md"

        self.assertTrue(
            data_dict.exists(),
            "docs/data_dictionary.md is missing",
        )

        create_tables = config.SQL_DIR / "create_tables.sql"

        self.assertTrue(
            create_tables.exists(),
            "sql/create_tables.sql is missing",
        )


if __name__ == "__main__":
    unittest.main()
