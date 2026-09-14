"""
transformation.py
------------------
Stage 4 of the pipeline: turn cleaned data into analysis-ready data by
adding row-level business calculations.

Design note - row-level vs aggregate transformations:
The project brief asks for "Customer Revenue", "Product Revenue", and
"Regional Revenue" as transformations. Those are deliberately NOT added
as columns here. Aggregate values should be calculated through SQL GROUP BY
queries or Power BI DAX measures.

Row-level calculations performed here:
    - Profit
    - Unit_Price
    - Profit_Margin
    - Gross_Revenue
    - Order_Month
    - Order_Year
    - Order_YearMonth
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def transform_sales_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform cleaned sales data into analysis-ready data.

    Steps
    -----
    1. Parse Order_Date into a datetime.
    2. Recompute Profit as Sales - Cost.
    3. Calculate Unit_Price as Sales / Quantity.
    4. Calculate Profit_Margin as Profit / Sales.
    5. Calculate Gross_Revenue before discounts.
    6. Add Order_Year, Order_Month, and Order_YearMonth.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned sales DataFrame.

    Returns
    -------
    pd.DataFrame
        Transformed DataFrame.
    """

    # Avoid modifying the original DataFrame.
    df = df.copy()

    # ------------------------------------------------------------------
    # 1. Parse Order_Date
    # ------------------------------------------------------------------
    if "Order_Date" in df.columns:
        df["Order_Date"] = pd.to_datetime(
            df["Order_Date"],
            format="%Y-%m-%d",
            errors="coerce",
        )

        invalid_dates = df["Order_Date"].isna().sum()

        if invalid_dates:
            logger.warning(
                "%d row(s) have an unparseable Order_Date.",
                invalid_dates,
            )

    # ------------------------------------------------------------------
    # 2. Recompute Profit
    # ------------------------------------------------------------------
    if {"Sales", "Cost"}.issubset(df.columns):
        df["Profit"] = (df["Sales"] - df["Cost"]).round(2)

    # ------------------------------------------------------------------
    # 3. Calculate Unit_Price
    # ------------------------------------------------------------------
    if {"Sales", "Quantity"}.issubset(df.columns):
        safe_quantity = df["Quantity"].replace(0, np.nan)

        df["Unit_Price"] = (df["Sales"] / safe_quantity).round(2)

    # ------------------------------------------------------------------
    # 4. Calculate Profit_Margin
    # ------------------------------------------------------------------
    if {"Profit", "Sales"}.issubset(df.columns):
        df["Profit_Margin"] = np.where(
            df["Sales"] > 0,
            (df["Profit"] / df["Sales"]).round(4),
            np.nan,
        )

    # ------------------------------------------------------------------
    # 5. Calculate Gross_Revenue
    # ------------------------------------------------------------------
    if {"Sales", "Discount"}.issubset(df.columns):
        safe_discount_factor = (1 - df["Discount"]).replace(0, np.nan)

        df["Gross_Revenue"] = (df["Sales"] / safe_discount_factor).round(2)

        # If Discount is 100%, avoid leaving Gross_Revenue as NaN.
        df["Gross_Revenue"] = df["Gross_Revenue"].fillna(df["Sales"])

    # ------------------------------------------------------------------
    # 6. Add date-based columns
    # ------------------------------------------------------------------
    if "Order_Date" in df.columns:
        df["Order_Year"] = df["Order_Date"].dt.year.astype("Int64")

        df["Order_Month"] = df["Order_Date"].dt.month.astype("Int64")

        df["Order_YearMonth"] = df["Order_Date"].dt.strftime("%Y-%m")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    logger.info(
        "Transformation complete: %d rows. "
        "Added row-level business metrics and date dimensions.",
        len(df),
    )

    return df
