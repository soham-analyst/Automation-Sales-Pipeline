"""
cleaning.py
Data Cleaning Layer:
Deduplicates records on primary keys, standardizes inconsistent date formats,
normalizes categorical spellings/casing, handles missing values, and casts
columns to strict, clean data types.
"""

import logging
from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)

# Canonical Category mapping
CATEGORY_STANDARDIZATION_MAP: Dict[str, str] = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "elec": "Electronics",
    "furniture": "Furniture",
    "furn": "Furniture",
    "clothing": "Clothing",
    "clothes": "Clothing",
    "apparel": "Clothing",
    "grocery": "Grocery",
    "groceries": "Grocery",
    "office supplies": "Office Supplies",
    "office supply": "Office Supplies",
    "office": "Office Supplies",
}

WORD_TO_NUMBER: Dict[str, int] = {
    "zero": 0,
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


def _parse_quantity(val) -> int:
    """Parse integer quantity from string, word, or float."""
    if pd.isna(val):
        return 1
    s = str(val).strip().lower()
    if s in WORD_TO_NUMBER:
        return WORD_TO_NUMBER[s]
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 1


def _standardize_category(val) -> str:
    """Standardize category string against known canonical names."""
    if pd.isna(val):
        return "Unknown"
    cleaned = str(val).strip()
    lowered = cleaned.lower()
    return CATEGORY_STANDARDIZATION_MAP.get(lowered, cleaned.title())


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Execute complete data cleaning transformation on validated DataFrame.

    Args:
        df: Validated DataFrame.

    Returns:
        Cleaned, deduplicated, and type-cast DataFrame.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to clean_data.")
        return df.copy()

    initial_count = len(df)
    logger.info("Starting cleaning for %d records...", initial_count)
    clean_df = df.copy()

    # 1. Deduplication by Order_ID
    clean_df = clean_df.drop_duplicates(subset=["Order_ID"], keep="first").reset_index(drop=True)
    deduped_count = len(clean_df)
    dupes_removed = initial_count - deduped_count
    logger.info(
        "Deduplication complete: removed %d duplicate rows (%d remaining)",
        dupes_removed,
        deduped_count,
    )

    # 2. Text Normalization: Strip leading/trailing whitespace
    string_cols = clean_df.select_dtypes(include=["object"]).columns
    for col in string_cols:
        clean_df[col] = clean_df[col].apply(lambda x: str(x).strip() if pd.notna(x) else x)

    # 3. Handle Missing Values
    if "Customer_Name" in clean_df.columns:
        clean_df["Customer_Name"] = clean_df["Customer_Name"].fillna("Unknown Customer")
    if "Product_Name" in clean_df.columns:
        clean_df["Product_Name"] = clean_df["Product_Name"].fillna("Unknown Product")
    if "Discount" in clean_df.columns:
        clean_df["Discount"] = clean_df["Discount"].fillna(0.0)

    # 4. Standardize Categories
    if "Category" in clean_df.columns:
        clean_df["Category"] = clean_df["Category"].apply(_standardize_category)

    # 5. Standardize Order_Date to YYYY-MM-DD
    if "Order_Date" in clean_df.columns:
        clean_df["Order_Date"] = pd.to_datetime(clean_df["Order_Date"], format="mixed").dt.strftime(
            "%Y-%m-%d"
        )

    # 6. Strict Type Casting
    clean_df["Quantity"] = clean_df["Quantity"].apply(_parse_quantity)
    clean_df["Sales"] = pd.to_numeric(clean_df["Sales"], errors="coerce").round(2)
    clean_df["Discount"] = pd.to_numeric(clean_df["Discount"], errors="coerce").fillna(0.0).round(2)

    if "Cost" in clean_df.columns:
        clean_df["Cost"] = pd.to_numeric(clean_df["Cost"], errors="coerce").round(2)
    if "Profit" in clean_df.columns:
        clean_df["Profit"] = pd.to_numeric(clean_df["Profit"], errors="coerce").round(2)

    logger.info("Data cleaning completed successfully on %d records.", len(clean_df))
    return clean_df
