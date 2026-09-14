"""
outliers.py
-----------
Stage 5 of the pipeline: flag statistically unusual Sales/Cost/Profit
values using the IQR method - WITHOUT deleting anything. Flagging vs.
deleting matters: a genuinely huge order is valuable business signal,
not bad data, and only a human (or a much richer rule set than "is this
number big") can tell the difference reliably.

Design note - why per-category, not global:
An early version of this ran IQR across the whole dataset at once. That
badly over-flagged normal orders: Electronics/Furniture items in this
catalog cost 10-40x what Grocery/Clothing items do, so a perfectly
ordinary ₹40,000 laptop order looked like a wild outlier only because it
was being compared against cheap grocery items, not other electronics.
Computing IQR separately within each Category fixes this - a value is
now only flagged if it's unusual relative to similar products.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Numeric columns checked for outliers via the IQR method.
NUMERIC_COLS = ["Sales", "Quantity", "Discount", "Cost", "Profit"]


def detect_outliers(df: pd.DataFrame, cols: list[str] = NUMERIC_COLS) -> pd.DataFrame:
    """Flag rows where any value in *cols* falls outside 1.5 x IQR,
    computed SEPARATELY within each Category (falls back to a single
    global IQR pass if Category isn't present).

    Adds an ``is_outlier`` boolean column and logs a summary. Flagged
    rows are kept, not dropped, so downstream analysis - and the Data
    Quality dashboard in Part 20 - can decide what to do with them.
    """
    df = df.copy()
    df["is_outlier"] = False

    if "Category" not in df.columns:
        logger.warning("'Category' column not found - falling back to a single global IQR pass.")
        groups = [(None, df)]
    else:
        groups = list(df.groupby("Category"))

    for category, group in groups:
        for col in cols:
            if col not in group.columns:
                continue

            numeric = pd.to_numeric(group[col], errors="coerce")
            q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0 or pd.isna(iqr):
                continue  # not enough spread in this category/column to define an outlier

            mask = (numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)
            flagged_idx = group.index[mask]
            df.loc[flagged_idx, "is_outlier"] = True

            if category is not None and mask.sum():
                logger.info("Outliers in '%s' within category '%s': %d row(s)", col, category, mask.sum())

    total = df["is_outlier"].sum()
    logger.info("Total outlier rows flagged: %d / %d (%.1f%%)", total, len(df), 100 * total / max(len(df), 1))
    return df
