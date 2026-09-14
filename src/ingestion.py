"""
ingestion.py
------------
Stage 1 of the pipeline: discover monthly sales files in data/raw/,
read them regardless of extension (.csv / .xlsx / .xls), standardize
their column names, and combine them into a single DataFrame - tagging
every row with which file it came from and when it was ingested.

Design decision: every column is read in as TEXT (dtype=str), even
numeric-looking ones. This is deliberate - it preserves exactly what's
in the source file (including "N/A", "five", blanks) so the validation
stage (Part 6) can inspect and report on raw problems before anything
gets silently coerced or lost. Numeric casting happens in cleaning.py
(Part 7), where we control exactly how conversion failures are handled.

Standalone test:
    python src/ingestion.py

Used inside the full pipeline:
    from src.ingestion import run_ingestion
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Maps common column-name variations (extra spaces, different casing/
# separators) seen across real-world exports onto our canonical schema.
# Extend this dict as new source systems get added to the pipeline.
COLUMN_RENAME_MAP = {
    "order id": "Order_ID", "orderid": "Order_ID", "order_id": "Order_ID",
    "order date": "Order_Date", "orderdate": "Order_Date", "order_date": "Order_Date",
    "customer id": "Customer_ID", "customerid": "Customer_ID", "customer_id": "Customer_ID",
    "customer name": "Customer_Name", "customername": "Customer_Name", "customer_name": "Customer_Name",
    "product id": "Product_ID", "productid": "Product_ID", "product_id": "Product_ID",
    "product name": "Product_Name", "productname": "Product_Name", "product_name": "Product_Name",
    "category": "Category",
    "sub category": "Sub_Category", "subcategory": "Sub_Category", "sub_category": "Sub_Category",
    "region": "Region", "state": "State", "city": "City",
    "sales": "Sales", "quantity": "Quantity", "discount": "Discount",
    "cost": "Cost", "profit": "Profit",
    "payment method": "Payment_Method", "paymentmethod": "Payment_Method", "payment_method": "Payment_Method",
}

REQUIRED_COLUMNS = [
    "Order_ID", "Order_Date", "Customer_ID", "Customer_Name",
    "Product_ID", "Product_Name", "Category", "Sub_Category",
    "Region", "State", "City", "Sales", "Quantity", "Discount",
    "Cost", "Profit", "Payment_Method",
]


def discover_files(raw_dir: Path = RAW_DATA_DIR) -> list:
    """Return every supported sales file found in raw_dir, sorted by name
    so files are always processed in a predictable order. Excel's own
    lock files (~$sales_january.xlsx, created while the file is open)
    are explicitly skipped - they're not real data files."""
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data folder not found: {raw_dir}")

    files = sorted(
        p for p in raw_dir.iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_EXTENSIONS
        and not p.name.startswith("~$")
    )
    logger.info("Discovered %d file(s) in %s", len(files), raw_dir)
    return files


def read_file(path: Path) -> pd.DataFrame:
    """Read a single CSV or Excel file into a DataFrame, entirely as text.
    Raises (and logs) a clear error for unsupported extensions or files
    that fail to parse, rather than failing silently."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            df = pd.read_csv(path, dtype=str, keep_default_na=True)
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(path, dtype=str)
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")
    except Exception as exc:
        logger.error("Failed to read %s: %s", path.name, exc)
        raise

    logger.info("Read %s -> %d rows, %d columns", path.name, len(df), df.shape[1])
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names so files from different sources/exports line
    up on one schema. Strips whitespace, then maps known variants
    (case-insensitive) onto the canonical names. Columns that don't match
    anything known are left as-is but logged, rather than dropped -
    dropping data silently is worse than surfacing an unexpected column."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    renamed = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in COLUMN_RENAME_MAP:
            renamed[col] = COLUMN_RENAME_MAP[key]
    df = df.rename(columns=renamed)

    unexpected = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    if unexpected:
        logger.warning("Unexpected column(s) kept as-is: %s", unexpected)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        logger.warning("Expected column(s) missing from this file: %s", missing)

    return df


def add_metadata(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Tag every row with which file it came from and when it was ingested.
    Essential for traceability, debugging, and the incremental-loading
    logic built in Part 12 (so we can tell which file a loaded row
    originated from)."""
    df = df.copy()
    df["source_file"] = source_file
    df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
    return df


def run_ingestion(raw_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Main ingestion entry point: discover -> read -> standardize -> tag ->
    combine every file in raw_dir into one DataFrame. Returns an empty,
    correctly-shaped DataFrame (not None) when there's nothing to ingest,
    so downstream code never has to special-case None."""
    files = discover_files(raw_dir)
    if not files:
        logger.warning("No files found in %s - nothing to ingest.", raw_dir)
        return pd.DataFrame(columns=REQUIRED_COLUMNS + ["source_file", "ingestion_timestamp"])

    frames = []
    summary = []
    for path in files:
        df = read_file(path)
        df = standardize_columns(df)
        df = add_metadata(df, path.name)
        frames.append(df)
        summary.append((path.name, len(df)))

    combined = pd.concat(frames, ignore_index=True, sort=False)

    logger.info("Ingestion summary:")
    for name, count in summary:
        logger.info("  %-25s %6d rows", name, count)
    logger.info("  %-25s %6d rows (combined)", "TOTAL", len(combined))

    return combined


# Anchor for resolving relative paths: the project root (parent of src/).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_raw_data(file_path: str) -> pd.DataFrame:
    """Read and standardize a single raw sales file.

    Convenience wrapper used by ``main.py`` when a specific file path is
    already known.  Relative paths are resolved against the **project
    root** (the directory containing ``src/``), so the pipeline works
    correctly regardless of which directory it is launched from.

    Args:
        file_path: Relative or absolute path to a ``.csv``, ``.xlsx``,
                   or ``.xls`` file (e.g. ``"data/raw/sales_january.csv"``).

    Returns:
        A standardized :class:`pandas.DataFrame` with columns mapped to
        the canonical schema (see ``COLUMN_RENAME_MAP``).
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    df = read_file(path)
    df = standardize_columns(df)
    df = add_metadata(df, path.name)
    return df



if __name__ == "__main__":
    # Standalone test run: `python src/ingestion.py`
    # (The full pipeline configures logging centrally in Part 13/15 -
    # this basicConfig call only applies when running this file directly.)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = run_ingestion()
    print("\nCombined shape:", result.shape)
    print(result.head())
