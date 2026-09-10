"""
main.py
CLI Entry Point for the Automated Sales Data Pipeline.
Wires Ingestion -> Validation -> Cleaning -> Transformation -> Reporting.

Usage:
    python main.py
    python main.py --raw-dir data/raw --export-dir data/processed
"""

import argparse
import sys
from pathlib import Path
from src.pipeline import run_pipeline


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Automated Sales Data Engineering Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Path to raw source files (.csv, .xlsx)",
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default=None,
        help="Path to processed output directory",
    )
    parser.add_argument(
        "--rejected-dir",
        type=str,
        default=None,
        help="Path to quarantined rejected records directory",
    )
    return parser.parse_args()


def print_banner():
    print("""
========================================================================
             AUTOMATED SALES DATA PIPELINE (ETL RUNNER)
========================================================================
    """)


def print_summary(summary: dict):
    metrics = summary.get("pipeline_metrics", {})
    kpis = summary.get("kpis", {})
    print(f"""
------------------------------------------------------------------------
Pipeline Execution Summary:
------------------------------------------------------------------------
  Status:                   {summary.get('status')}
  Execution Time:           {summary.get('duration_seconds')}s
  Raw Records Ingested:     {metrics.get('raw_records_ingested', 0):,}
  Validation Passed:        {metrics.get('records_passed_validation', 0):,}
  Records Quarantined:      {metrics.get('records_rejected', 0):,}
  Duplicates Dropped:       {metrics.get('duplicate_records_removed', 0):,}
  Final Clean Records:      {metrics.get('final_processed_records', 0):,}

Key Business Performance Metrics:
------------------------------------------------------------------------
  Total Revenue:            INR {kpis.get('total_sales', 0):,.2f}
  Total Profit:             INR {kpis.get('total_profit', 0):,.2f}
  Overall Profit Margin:    {kpis.get('overall_margin_pct', 0)}%
  Average Order Value:      INR {kpis.get('average_order_value', 0):,.2f}
  Unique Customers:         {kpis.get('unique_customers', 0):,}
  Unique Products:          {kpis.get('unique_products', 0):,}
  Flagged Outlier Orders:   {kpis.get('outlier_count', 0):,}

Output Files:
------------------------------------------------------------------------
  Transformed Data:         {summary.get('artifacts', {}).get('processed_file')}
  Quarantine Logs:          {summary.get('artifacts', {}).get('rejected_directory')}
========================================================================
    """)


def main():
    print_banner()
    args = parse_arguments()

    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    export_dir = Path(args.export_dir) if args.export_dir else None
    rejected_dir = Path(args.rejected_dir) if args.rejected_dir else None

    result = run_pipeline(
        raw_dir=raw_dir,
        processed_dir=export_dir,
        rejected_dir=rejected_dir,
    )

    if result.get("status") == "SUCCESS":
        print_summary(result)
        sys.exit(0)
    else:
        print(f"[ERROR] Pipeline execution failed: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
