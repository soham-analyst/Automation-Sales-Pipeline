"""
validation.py
-------------
Stage 2 of the pipeline: separate records that pass quality checks from
those that don't, writing rejected rows to data/rejected/ for review.

Full line-by-line explanation arrives in Part 6 (Data Validation).
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Columns that must not be null/empty for a record to be valid.
REQUIRED_NON_NULL = ["Order_ID", "Customer_ID", "Product_ID", "Product_Name"]

# Numeric columns that must be > 0.
POSITIVE_NUMERIC = ["Sales", "Quantity"]


def validate_records(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate *df* and split into (valid_df, rejected_df).

    Each rejected row gets a ``rejection_reason`` column describing why it
    was quarantined.  Records may fail multiple checks; all reasons are
    joined with " | ".

    Args:
        df: Raw or partially processed DataFrame.

    Returns:
        A 2-tuple ``(valid_df, rejected_df)``.
    """
    df = df.copy()
    reasons: dict[int, list[str]] = {i: [] for i in df.index}

    # --- 1. Required non-null fields ------------------------------------------
    for col in REQUIRED_NON_NULL:
        if col not in df.columns:
            continue
        mask = df[col].isna() | (df[col].astype(str).str.strip() == "")
        for idx in df[mask].index:
            reasons[idx].append(f"Missing {col}")

    # --- 2. Positive numeric fields -------------------------------------------
    for col in POSITIVE_NUMERIC:
        if col not in df.columns:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        mask = numeric.isna() | (numeric <= 0)
        for idx in df[mask].index:
            reasons[idx].append(f"Invalid {col} ({df.loc[idx, col]!r})")

    # --- 3. Split -----------------------------------------------------------
    rejected_idx = [i for i, r in reasons.items() if r]
    valid_idx = [i for i, r in reasons.items() if not r]

    rejected_df = df.loc[rejected_idx].copy()
    rejected_df["rejection_reason"] = [
        " | ".join(reasons[i]) for i in rejected_idx
    ]
    valid_df = df.loc[valid_idx].copy()

    logger.info(
        "Validation: %d valid, %d rejected (of %d total)",
        len(valid_df), len(rejected_df), len(df),
    )
    return valid_df, rejected_df
