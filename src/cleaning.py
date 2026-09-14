"""
cleaning.py

Stage 3 of the pipeline:
- Deduplicate records
- Standardize dates and categories
- Coerce numeric columns
- Fill sensible defaults
- Quarantine invalid records
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# File paths and constants
# ---------------------------------------------------------------------

REJECTED_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "rejected" / "rejected_records.csv"
)

# Canonical date format
_ISO_DATE = "%Y-%m-%d"

# Recognized date formats
_DATE_FORMATS = [
    "%Y-%m-%d",  # 2025-01-14
    "%d/%m/%Y",  # 14/01/2025
    "%m-%d-%Y",  # 01-14-2025
    "%d-%b-%Y",  # 14-Jan-2025
    "%d %B %Y",  # 14 January 2025
]

# Word-number mapping for Quantity values
_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

# Standard category names
CATEGORY_MAP = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "furniture": "Furniture",
    "furnitures": "Furniture",
    "clothing": "Clothing",
    "cloths": "Clothing",
    "apparel": "Clothing",
    "grocery": "Groceries",
    "groceries": "Groceries",
    "office supplies": "Office Supplies",
    "office-supplies": "Office Supplies",
    "officesupplies": "Office Supplies",
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------


def _parse_date(value) -> str | None:
    """
    Try every known date format.

    Return the date in YYYY-MM-DD format.
    Return None if the value cannot be parsed.
    """

    if pd.isna(value):
        return None

    raw = str(value).strip()

    for date_format in _DATE_FORMATS:
        try:
            return pd.to_datetime(
                raw,
                format=date_format,
            ).strftime(_ISO_DATE)

        except (ValueError, TypeError):
            continue

    # Last resort: let pandas infer the date format
    try:
        return pd.to_datetime(
            raw,
            format="mixed",
        ).strftime(_ISO_DATE)

    except Exception:
        return None


def _coerce_quantity(value) -> int | None:
    """
    Convert Quantity values to integers.

    Supports:
    - Numeric values
    - Numeric strings
    - Word numbers such as 'two' or 'five'

    Return None if conversion fails.
    """

    if pd.isna(value):
        return None

    value_as_string = str(value).strip().lower()

    if value_as_string in _WORD_NUMBERS:
        return _WORD_NUMBERS[value_as_string]

    try:
        return int(float(value_as_string))

    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------
# Main cleaning function
# ---------------------------------------------------------------------


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the input DataFrame.

    Cleaning steps:
    1. Deduplicate using Order_ID.
    2. Standardize Order_Date.
    3. Standardize Category values.
    4. Convert Quantity into integers.
    5. Quarantine invalid Quantity values.
    6. Convert Sales, Cost, and Profit into numeric values.
    7. Quarantine invalid Sales values.
    8. Fill missing Discount values with 0.0.
    9. Quarantine rows missing critical fields.
    10. Append rejected rows to the rejection CSV file.

    Returns:
        Cleaned pandas DataFrame.
    """

    df = df.copy()

    before_count = len(df)

    # Stores rejected records for this pipeline run
    rejected_frames: list[pd.DataFrame] = []

    # -----------------------------------------------------------------
    # 1. Deduplicate records
    # -----------------------------------------------------------------

    if "Order_ID" in df.columns:
        df = df.drop_duplicates(
            subset=["Order_ID"],
            keep="first",
        )

        logger.info(
            "Deduplication: %d → %d rows",
            before_count,
            len(df),
        )

    # -----------------------------------------------------------------
    # 2. Standardize dates
    # -----------------------------------------------------------------

    if "Order_Date" in df.columns:
        df["Order_Date"] = df["Order_Date"].apply(_parse_date)

    # -----------------------------------------------------------------
    # 3. Standardize category names
    # -----------------------------------------------------------------

    if "Category" in df.columns:

        # Normalize values before mapping:
        # " ELECTRONICS " -> "electronics"
        category_keys = df["Category"].astype("string").str.strip().str.lower()

        # Apply the canonical category mapping
        mapped_categories = category_keys.map(CATEGORY_MAP)

        # Identify values not found in the mapping
        unmapped = mapped_categories.isna() & df["Category"].notna()

        if unmapped.any():
            logger.warning(
                "Category value(s) not in CATEGORY_MAP, " "title-cased as fallback: %s",
                sorted(
                    df.loc[
                        unmapped,
                        "Category",
                    ]
                    .astype(str)
                    .unique()
                ),
            )

        # Use mapped values where available.
        # Otherwise, use a title-cased fallback.
        fallback_categories = df["Category"].astype("string").str.strip().str.title()

        df["Category"] = mapped_categories.fillna(fallback_categories)

    # -----------------------------------------------------------------
    # 4. Coerce Quantity and quarantine invalid values
    # -----------------------------------------------------------------

    if "Quantity" in df.columns:

        df["Quantity"] = df["Quantity"].apply(_coerce_quantity)

        bad_quantity = df["Quantity"].isna() | (df["Quantity"] <= 0)

        if bad_quantity.any():

            rejected_quantity = df.loc[bad_quantity].copy()

            rejected_quantity["rejection_reason"] = "Invalid Quantity"

            rejected_frames.append(rejected_quantity)

            logger.warning(
                "Quarantining %d row(s): invalid Quantity",
                bad_quantity.sum(),
            )

        # Keep only valid Quantity records
        df = df.loc[~bad_quantity].copy()

        df["Quantity"] = df["Quantity"].astype(int)

    # -----------------------------------------------------------------
    # 5. Convert numeric columns
    # -----------------------------------------------------------------

    for column in ("Sales", "Cost", "Profit"):

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # -----------------------------------------------------------------
    # 6. Quarantine invalid Sales values
    # -----------------------------------------------------------------

    if "Sales" in df.columns:

        bad_sales = df["Sales"].isna() | (df["Sales"] <= 0)

        if bad_sales.any():

            rejected_sales = df.loc[bad_sales].copy()

            rejected_sales["rejection_reason"] = "Invalid Sales"

            rejected_frames.append(rejected_sales)

            logger.warning(
                "Quarantining %d row(s): invalid Sales",
                bad_sales.sum(),
            )

        # Keep only valid Sales records
        df = df.loc[~bad_sales].copy()

    # -----------------------------------------------------------------
    # 7. Fill missing Discount values
    # -----------------------------------------------------------------

    if "Discount" in df.columns:

        df["Discount"] = pd.to_numeric(
            df["Discount"],
            errors="coerce",
        ).fillna(0.0)

    # -----------------------------------------------------------------
    # 8. Quarantine rows missing critical fields
    # -----------------------------------------------------------------

    critical_columns = [
        column
        for column in (
            "Order_ID",
            "Customer_ID",
            "Customer_Name",
            "Product_ID",
            "Product_Name",
            "Sales",
        )
        if column in df.columns
    ]

    if critical_columns:

        missing_values = df[critical_columns].isna()

        bad_critical = missing_values.any(axis=1)

        if bad_critical.any():

            rejected_critical = df.loc[bad_critical].copy()

            rejected_critical["rejection_reason"] = [
                "Missing "
                + ", ".join(
                    column for column in critical_columns if missing_values.loc[index, column]
                )
                for index in rejected_critical.index
            ]

            rejected_frames.append(rejected_critical)

            logger.warning(
                "Quarantining %d row(s): " "missing critical field(s)",
                bad_critical.sum(),
            )

        # Keep only rows with all critical fields present
        df = df.loc[~bad_critical].copy()

    # -----------------------------------------------------------------
    # 9. Save rejected records
    # -----------------------------------------------------------------

    current_rejected_count = sum(len(frame) for frame in rejected_frames)

    if rejected_frames:

        rejected_df = pd.concat(
            rejected_frames,
            ignore_index=True,
        )

        REJECTED_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_header = not REJECTED_PATH.exists()

        rejected_df.to_csv(
            REJECTED_PATH,
            mode="a",
            index=False,
            header=write_header,
        )

        logger.warning(
            "Quarantined %d row(s) total → %s",
            len(rejected_df),
            REJECTED_PATH,
        )

    # -----------------------------------------------------------------
    # 10. Return cleaned data
    # -----------------------------------------------------------------

    logger.info(
        "Cleaning complete: %d rows retained",
        len(df),
    )

    # Make the current rejection count available to main.py
    clean_data.last_rejected_count = current_rejected_count

    return df.reset_index(drop=True)
