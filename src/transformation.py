"""
transformation.py
Data Transformation Layer:
Recomputes financial metrics (Profit = Sales - Cost, Profit Margin, Unit Price),
generates date/time dimensions, and detects extreme sales outliers using IQR.
"""

import logging
from typing import Any, Dict
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def flag_outliers_iqr(df: pd.DataFrame, column: str = "Sales", factor: float = 3.0) -> pd.Series:
    """Flag extreme outliers using the Interquartile Range (IQR) method per category.

    Args:
        df: DataFrame containing the category and target numeric column.
        column: Column name to detect outliers on (default: 'Sales').
        factor: Multiplier for IQR (default: 3.0 for extreme outliers).

    Returns:
        Boolean Series indicating whether each record is an outlier.
    """
    if column not in df.columns or "Category" not in df.columns:
        return pd.Series(False, index=df.index)

    outlier_mask = pd.Series(False, index=df.index)

    for category, group in df.groupby("Category"):
        values = group[column].dropna()
        if len(values) < 4:
            continue
        q25 = np.percentile(values, 25)
        q75 = np.percentile(values, 75)
        iqr = q75 - q25
        upper_limit = q75 + (factor * iqr)
        # Any value above extreme threshold
        group_outliers = group[group[column] > upper_limit].index
        outlier_mask.loc[group_outliers] = True

    return outlier_mask


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Execute business transformations, metrics calculation, and dimension enrichment.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Transformed DataFrame enriched with calculated columns and dimension metrics.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to transform_data.")
        return df.copy()

    logger.info("Starting transformations on %d records...", len(df))
    trans_df = df.copy()

    # 1. Recompute True Profit (correcting source data discrepancies)
    if "Cost" in trans_df.columns and "Sales" in trans_df.columns:
        trans_df["Profit"] = (trans_df["Sales"] - trans_df["Cost"]).round(2)

    # 2. Financial Metrics: Unit Price & Profit Margin %
    if "Sales" in trans_df.columns and "Quantity" in trans_df.columns:
        trans_df["Unit_Price"] = (
            trans_df["Sales"] / trans_df["Quantity"].replace(0, np.nan)
        ).round(2)

    if "Profit" in trans_df.columns and "Sales" in trans_df.columns:
        trans_df["Profit_Margin_Pct"] = (
            (trans_df["Profit"] / trans_df["Sales"].replace(0, np.nan)) * 100
        ).round(2)

    # 3. Calendar & Time Dimensions
    if "Order_Date" in trans_df.columns:
        date_series = pd.to_datetime(trans_df["Order_Date"])
        trans_df["Order_Year"] = date_series.dt.year
        trans_df["Order_Month"] = date_series.dt.month
        trans_df["Order_Month_Name"] = date_series.dt.strftime("%B")
        trans_df["Order_Quarter"] = "Q" + date_series.dt.quarter.astype(str)
        trans_df["Order_Day_Of_Week"] = date_series.dt.dayofweek
        trans_df["Order_Day_Name"] = date_series.dt.strftime("%A")

    # 4. Outlier Detection
    trans_df["is_sales_outlier"] = flag_outliers_iqr(trans_df, column="Sales", factor=3.0)
    outlier_count = int(trans_df["is_sales_outlier"].sum())
    logger.info(
        "Outlier detection: flagged %d extreme sales transactions (%.2f%%)",
        outlier_count,
        (outlier_count / len(trans_df) * 100) if len(trans_df) > 0 else 0,
    )

    logger.info("Transformations complete.")
    return trans_df


def generate_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate business KPI and summary metrics from transformed DataFrame.

    Args:
        df: Transformed DataFrame.

    Returns:
        Dictionary of aggregate KPIs.
    """
    if df.empty:
        return {"total_records": 0, "total_sales": 0.0, "total_profit": 0.0}

    total_sales = float(df["Sales"].sum()) if "Sales" in df.columns else 0.0
    total_profit = float(df["Profit"].sum()) if "Profit" in df.columns else 0.0
    total_orders = len(df)
    unique_customers = df["Customer_ID"].nunique() if "Customer_ID" in df.columns else 0
    unique_products = df["Product_ID"].nunique() if "Product_ID" in df.columns else 0
    avg_order_value = round(total_sales / total_orders, 2) if total_orders > 0 else 0.0
    overall_margin = round((total_profit / total_sales) * 100, 2) if total_sales > 0 else 0.0

    return {
        "total_records": total_orders,
        "unique_customers": unique_customers,
        "unique_products": unique_products,
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "overall_margin_pct": overall_margin,
        "average_order_value": avg_order_value,
        "outlier_count": (
            int(df["is_sales_outlier"].sum()) if "is_sales_outlier" in df.columns else 0
        ),
    }
