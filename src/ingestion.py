"""
ingestion.py
Data Ingestion Layer:
Loads raw sales files (.csv and .xlsx) from the raw directory,
attaches traceability metadata (source_file, ingestion_timestamp),
and returns consolidated DataFrames for downstream processing.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import List, Union
import pandas as pd

logger = logging.getLogger(__name__)


def ingest_file(file_path: Union[str, Path]) -> pd.DataFrame:
    """Ingest a single raw file (.csv or .xlsx) and attach provenance metadata.

    Args:
        file_path: Path to the target data file.

    Returns:
        pd.DataFrame containing the raw records with metadata columns.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    logger.info("Ingesting raw file: %s", path.name)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        # Read everything initially with dtype=str or automatic inference to preserve raw state
        df = pd.read_csv(path, dtype=object)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=object, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file format '{suffix}' for file: {path.name}")

    # Attach ingestion audit metadata
    df["source_file"] = path.name
    df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

    logger.info("Successfully ingested %d rows from %s", len(df), path.name)
    return df


def ingest_all_raw_files(raw_dir: Union[str, Path]) -> pd.DataFrame:
    """Ingest and concatenate all supported raw files found in raw_dir.

    Args:
        raw_dir: Directory path containing raw files.

    Returns:
        Consolidated pd.DataFrame of all ingested records.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw directory does not exist: {raw_path}")

    files: List[Path] = sorted(
        [f for f in raw_path.iterdir() if f.suffix.lower() in (".csv", ".xlsx", ".xls")]
    )

    if not files:
        logger.warning("No CSV or Excel files found in directory: %s", raw_path)
        return pd.DataFrame()

    dataframes = []
    for file in files:
        try:
            df = ingest_file(file)
            dataframes.append(df)
        except Exception as e:
            logger.error("Failed to ingest %s: %s", file.name, e)

    if not dataframes:
        return pd.DataFrame()

    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(
        "Ingested total of %d rows across %d files from %s",
        len(combined_df),
        len(dataframes),
        raw_path.name,
    )
    return combined_df
