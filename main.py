"""main.py

Entry point: python -m main
Wires ingestion -> cleaning -> transformation -> outlier detection -> database load.
"""

import logging

from config.database import engine
from src.cleaning import clean_data
from src.data_quality_report import generate_data_quality_report
from src.ingestion import run_ingestion
from src.loader import load_to_db
from src.outliers import detect_outliers
from src.transformation import transform_sales_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_pipeline():
    logging.info("Starting Sales Data Pipeline...")

    # Step 1: Automated Ingestion
    df_raw = run_ingestion()

    if df_raw.empty:
        logging.warning("No data found to process. Exiting pipeline.")
        return

    # Step 2: Data Cleaning
    df_clean = clean_data(df_raw)
    current_rejected_rows = getattr(clean_data, "last_rejected_count", 0)
    current_rejected_rows = getattr(
        clean_data,
        "last_rejected_count",
        0,
    )

    # Step 3: Transformation & Feature Engineering
    df_transformed = transform_sales_data(df_clean)

    # Step 4: Outlier Detection
    df_final = detect_outliers(df_transformed)

    # Step 5: Load to SQL Server
    load_summary = load_to_db(df_final, engine)

    logging.info("Rows inserted this run: %s", load_summary)

    # Step 6: Generate Data-Quality Report
    report_path = generate_data_quality_report(
        raw_df=df_raw,
        clean_df=df_clean,
        final_df=df_final,
        load_summary=load_summary,
        current_rejected_rows=current_rejected_rows,
    )

    logging.info("Data-quality report saved to: %s", report_path)
    logging.info("Pipeline executed successfully!")


if __name__ == "__main__":
    run_pipeline()
