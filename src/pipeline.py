"""
pipeline.py
Pipeline Orchestrator:
Coordinates the end-to-end execution of the sales data pipeline:
Ingestion -> Validation -> Cleaning -> Transformation -> Persistence & Reporting.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional

from config import config
from src.cleaning import clean_data
from src.ingestion import ingest_all_raw_files
from src.transformation import generate_kpi_summary, transform_data
from src.validation import validate_records

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("SalesPipeline")


def run_pipeline(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    rejected_dir: Optional[Path] = None,
    logs_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the complete 5-stage ETL sales data pipeline.

    Args:
        raw_dir: Directory containing raw input files (default: config.RAW_DATA_DIR).
        processed_dir: Directory to save transformed data (default: config.PROCESSED_DATA_DIR).
        rejected_dir: Directory to save quarantined records (default: config.REJECTED_DATA_DIR).
        logs_dir: Directory to save run logs and summary reports (default: config.LOGS_DIR).

    Returns:
        Dict containing execution metrics, KPIs, and output artifact paths.
    """
    start_time = time.time()
    run_timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("==================================================")
    logger.info(" Starting Automated Sales Data Pipeline Run")
    logger.info(" Timestamp: %s", run_timestamp)
    logger.info("==================================================")

    raw_path = Path(raw_dir) if raw_dir else config.RAW_DATA_DIR
    proc_path = Path(processed_dir) if processed_dir else config.PROCESSED_DATA_DIR
    rej_path = Path(rejected_dir) if rejected_dir else config.REJECTED_DATA_DIR
    log_path = Path(logs_dir) if logs_dir else config.LOGS_DIR

    # Ensure output directories exist
    proc_path.mkdir(parents=True, exist_ok=True)
    rej_path.mkdir(parents=True, exist_ok=True)
    log_path.mkdir(parents=True, exist_ok=True)

    # 1. INGESTION STAGE
    logger.info("--- Stage 1: Data Ingestion ---")
    raw_df = ingest_all_raw_files(raw_path)
    total_raw = len(raw_df)
    if total_raw == 0:
        logger.error("No data ingested. Halting pipeline.")
        return {"status": "FAILED", "error": "No raw files found or ingested."}

    # 2. VALIDATION STAGE
    logger.info("--- Stage 2: Data Validation ---")
    valid_df, rejected_df = validate_records(raw_df, rejected_dir=rej_path)
    valid_count = len(valid_df)
    rejected_count = len(rejected_df)

    # 3. CLEANING STAGE
    logger.info("--- Stage 3: Data Cleaning ---")
    clean_df = clean_data(valid_df)
    cleaned_count = len(clean_df)
    duplicates_removed = valid_count - cleaned_count

    # 4. TRANSFORMATION STAGE
    logger.info("--- Stage 4: Data Transformation ---")
    transformed_df = transform_data(clean_df)
    final_count = len(transformed_df)

    # 5. STORAGE & EXPORT STAGE
    logger.info("--- Stage 5: Export & Storage ---")
    output_filename = "sales_transformed.csv"
    output_file = proc_path / output_filename
    transformed_df.to_csv(output_file, index=False)
    logger.info("Saved final transformed dataset to: %s", output_file)

    # Compute KPIs
    kpis = generate_kpi_summary(transformed_df)
    duration_seconds = round(time.time() - start_time, 2)

    run_summary: Dict[str, Any] = {
        "status": "SUCCESS",
        "run_timestamp": run_timestamp,
        "duration_seconds": duration_seconds,
        "pipeline_metrics": {
            "raw_records_ingested": total_raw,
            "records_passed_validation": valid_count,
            "records_rejected": rejected_count,
            "duplicate_records_removed": duplicates_removed,
            "final_processed_records": final_count,
        },
        "kpis": kpis,
        "artifacts": {
            "processed_file": str(output_file),
            "rejected_directory": str(rej_path),
        },
    }

    # Save summary report
    summary_file = log_path / "pipeline_summary.json"
    with open(summary_file, mode="w", encoding="utf-8") as f:
        json.dump(run_summary, f, indent=2)

    logger.info("==================================================")
    logger.info(" Pipeline Run Completed Successfully in %.2fs", duration_seconds)
    logger.info(
        " Total Revenue: INR %s | Total Profit: INR %s",
        f"{kpis['total_sales']:,}",
        f"{kpis['total_profit']:,}",
    )
    logger.info(" Clean Records: %d | Rejections: %d", final_count, rejected_count)
    logger.info("==================================================")

    return run_summary
