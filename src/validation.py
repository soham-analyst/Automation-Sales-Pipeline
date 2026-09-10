"""
validation.py
Data Validation Layer:
Evaluates raw records against business constraints, primary key rules,
and data quality requirements. Separates clean/valid records from rejected
records and logs quarantine reasons for auditing.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import List, Optional, Set, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

# Canonical Allow-Lists defined in Data Dictionary
VALID_REGIONS: Set[str] = {"North", "South", "East", "West"}
VALID_PAYMENT_METHODS: Set[str] = {
    "Credit Card",
    "Debit Card",
    "UPI",
    "Net Banking",
    "Cash on Delivery",
}


def _check_numeric_positive(value) -> Tuple[bool, Optional[float]]:
    """Helper to check if a value can be converted to a positive float."""
    if pd.isna(value) or str(value).strip().lower() in ("nan", "none", "", "n/a", "unknown", "-"):
        return False, None
    try:
        num = float(value)
        return num > 0, num
    except (ValueError, TypeError):
        return False, None


def validate_records(
    df: pd.DataFrame, rejected_dir: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Validate DataFrame records against data quality and business rules.

    Args:
        df: Ingested raw DataFrame.
        rejected_dir: Optional directory path to save rejected records.

    Returns:
        A tuple of (valid_df, rejected_df).
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to validation.")
        return df.copy(), pd.DataFrame()

    logger.info("Validating %d records...", len(df))
    records_reasons: List[List[str]] = [[] for _ in range(len(df))]

    # 1. Mandatory Identifier Checks
    for idx, (order_id, cust_id, prod_id) in enumerate(
        zip(df["Order_ID"], df["Customer_ID"], df["Product_ID"])
    ):
        # Order_ID check
        if pd.isna(order_id) or not str(order_id).strip():
            records_reasons[idx].append("Missing Order_ID")
        elif not str(order_id).startswith("ORD"):
            records_reasons[idx].append("Invalid Order_ID format")

        # Customer_ID check
        if pd.isna(cust_id) or not str(cust_id).strip():
            records_reasons[idx].append("Missing Customer_ID")
        elif not str(cust_id).startswith("CUST"):
            records_reasons[idx].append("Invalid Customer_ID format")

        # Product_ID check
        if pd.isna(prod_id) or not str(prod_id).strip():
            records_reasons[idx].append("Missing Product_ID")
        elif not str(prod_id).startswith("PROD"):
            records_reasons[idx].append("Invalid Product_ID format")

    # 2. Categorical & Domain Allow-List Checks
    if "Region" in df.columns:
        for idx, region in enumerate(df["Region"]):
            if pd.notna(region) and str(region).strip() not in VALID_REGIONS:
                records_reasons[idx].append(f"Invalid Region: {region}")

    if "Payment_Method" in df.columns:
        for idx, payment in enumerate(df["Payment_Method"]):
            if pd.notna(payment) and str(payment).strip() not in VALID_PAYMENT_METHODS:
                records_reasons[idx].append(f"Invalid Payment_Method: {payment}")

    # 3. Numeric Validity Checks (Sales & Quantity)
    word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}

    if "Sales" in df.columns:
        for idx, sales_val in enumerate(df["Sales"]):
            is_valid, num = _check_numeric_positive(sales_val)
            if not is_valid:
                records_reasons[idx].append(f"Invalid/Non-positive Sales: {sales_val}")

    if "Quantity" in df.columns:
        for idx, qty_val in enumerate(df["Quantity"]):
            # Check if it's a word number or numeric
            str_qty = str(qty_val).strip().lower() if pd.notna(qty_val) else ""
            if str_qty in word_to_num:
                continue
            is_valid, num = _check_numeric_positive(qty_val)
            if not is_valid:
                records_reasons[idx].append(f"Invalid/Non-positive Quantity: {qty_val}")

    # Segregate valid from rejected
    rejection_strings = ["; ".join(reasons) for reasons in records_reasons]
    is_rejected = [bool(reasons) for reasons in records_reasons]

    df_copy = df.copy()
    df_copy["rejection_reason"] = rejection_strings

    valid_mask = [not r for r in is_rejected]
    rejected_mask = is_rejected

    valid_df = df_copy[valid_mask].drop(columns=["rejection_reason"]).reset_index(drop=True)
    rejected_df = df_copy[rejected_mask].reset_index(drop=True)

    logger.info(
        "Validation complete: %d records passed, %d records rejected (%.2f%%)",
        len(valid_df),
        len(rejected_df),
        (len(rejected_df) / len(df) * 100) if len(df) > 0 else 0,
    )

    # Export rejected records if directory is specified
    if rejected_dir and not rejected_df.empty:
        rej_path = Path(rejected_dir)
        rej_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        export_file = rej_path / f"rejected_records_{timestamp}.csv"
        rejected_df.to_csv(export_file, index=False)
        logger.info("Saved %d rejected records to: %s", len(rejected_df), export_file)

    return valid_df, rejected_df
