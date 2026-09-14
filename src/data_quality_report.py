"""Data-quality reporting utilities."""

from datetime import datetime
from pathlib import Path
import json

import pandas as pd

REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_data_quality_report(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    final_df: pd.DataFrame,
    load_summary: dict,
    current_rejected_rows: int,
) -> Path:
    """Generate and save a JSON data-quality report."""

    outlier_count = 0

    for column in (
        "Is_Outlier",
        "is_outlier",
        "outlier_flag",
        "Outlier_Flag",
    ):
        if column in final_df.columns:
            outlier_count = int(final_df[column].fillna(False).astype(bool).sum())
            break

    report = {
        "report_generated_at": datetime.now().isoformat(timespec="seconds"),
        "pipeline_summary": {
            "raw_rows": int(len(raw_df)),
            "clean_rows": int(len(clean_df)),
            "final_rows": int(len(final_df)),
            "rejected_rows_current_run": int(current_rejected_rows),
            "outlier_rows": int(outlier_count),
        },
        "database_load_summary": {key: int(value) for key, value in load_summary.items()},
        "quality_checks": {
            "raw_data_available": not raw_df.empty,
            "clean_data_available": not clean_df.empty,
            "final_data_available": not final_df.empty,
            "null_values_in_final_data": int(final_df.isna().sum().sum()),
            "duplicate_rows_in_final_data": int(final_df.duplicated().sum()),
        },
    }

    report_path = REPORTS_DIR / "data_quality_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return report_path
