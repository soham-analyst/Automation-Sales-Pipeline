"""
database.py
-----------
Low-level, reusable database helpers used by loader.py.
"""

import logging

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def table_exists(engine: Engine, table_name: str) -> bool:
    """Return True if table_name exists in the connected database."""
    return inspect(engine).has_table(table_name)


def get_existing_keys(
    engine: Engine,
    table_name: str,
    key_column: str,
) -> set:
    """Return existing key values from a target table."""
    if not table_exists(engine, table_name):
        logger.warning(
            "Table '%s' doesn't exist yet - has sql/create_tables.sql been run? "
            "Treating as 'no existing keys'.",
            table_name,
        )
        return set()

    query = text(
        f"SELECT DISTINCT [{key_column}] FROM [{table_name}]"
    )

    with engine.connect() as conn:
        result = conn.execute(query)
        return {row[0] for row in result}


def insert_new_rows(
    engine: Engine,
    df: pd.DataFrame,
    table_name: str,
    key_column: str,
) -> int:
    """
    Insert only rows whose key_column is not already in the target table.
    """

    if df.empty:
        return 0

    existing = get_existing_keys(
        engine,
        table_name,
        key_column,
    )

    new_rows = df.loc[
        ~df[key_column].isin(existing)
    ].copy()

    if new_rows.empty:
        logger.info(
            "No new rows for '%s' - already up to date "
            "(%d candidate rows, 0 new).",
            table_name,
            len(df),
        )
        return 0

    # Convert pandas nullable string values into ordinary Python values.
    for column in new_rows.columns:
        if pd.api.types.is_string_dtype(new_rows[column]):
            new_rows[column] = new_rows[column].astype(object)
            new_rows[column] = new_rows[column].where(
                new_rows[column].notna(),
                None,
            )

    # Insert in smaller batches to avoid pyodbc buffer-size problems.
    new_rows.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
        method=None,
    )

    logger.info(
        "Inserted %d new row(s) into '%s' (%d already existed).",
        len(new_rows),
        table_name,
        len(df) - len(new_rows),
    )

    return len(new_rows)