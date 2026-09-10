"""
test_pipeline_stages.py
Unit and integration tests for each stage of the ETL pipeline:
Ingestion -> Validation -> Cleaning -> Transformation -> Full Orchestration.
"""

import unittest
from pathlib import Path
import pandas as pd

from config import config
from src.cleaning import clean_data
from src.ingestion import ingest_file
from src.pipeline import run_pipeline
from src.transformation import transform_data
from src.validation import validate_records


class TestPipelineStages(unittest.TestCase):
    def setUp(self):
        """Create sample test dataframe with deliberate quality issues."""
        self.sample_raw_df = pd.DataFrame(
            [
                {
                    "Order_ID": "ORD0000001",
                    "Order_Date": "2025-01-14",
                    "Customer_ID": "CUST00001",
                    "Customer_Name": "Aarav Sharma",
                    "Product_ID": "PROD0001",
                    "Product_Name": "Laptop Item 1",
                    "Category": "electronics",  # lowercase variant
                    "Sub_Category": "Laptops",
                    "Region": "North",
                    "State": "Delhi",
                    "City": "New Delhi",
                    "Sales": "50000",
                    "Quantity": "two",  # text number
                    "Discount": None,  # missing discount
                    "Cost": "35000",
                    "Profit": "99999",  # deliberately wrong profit
                    "Payment_Method": "Credit Card",
                },
                {
                    # Duplicate of ORD0000001
                    "Order_ID": "ORD0000001",
                    "Order_Date": "14/01/2025",
                    "Customer_ID": "CUST00001",
                    "Customer_Name": "Aarav Sharma",
                    "Product_ID": "PROD0001",
                    "Product_Name": "Laptop Item 1",
                    "Category": "ELECTRONICS",
                    "Sub_Category": "Laptops",
                    "Region": "North",
                    "State": "Delhi",
                    "City": "New Delhi",
                    "Sales": "50000",
                    "Quantity": 2,
                    "Discount": 0.0,
                    "Cost": "35000",
                    "Profit": "15000",
                    "Payment_Method": "Credit Card",
                },
                {
                    # Invalid record (missing Customer_ID, negative Sales)
                    "Order_ID": "ORD0000002",
                    "Order_Date": "2025-01-15",
                    "Customer_ID": None,
                    "Customer_Name": "Unknown",
                    "Product_ID": "PROD0002",
                    "Product_Name": "Chair",
                    "Category": "Furniture",
                    "Sub_Category": "Chairs",
                    "Region": "South",
                    "State": "Karnataka",
                    "City": "Bengaluru",
                    "Sales": "-500",
                    "Quantity": 1,
                    "Discount": 0.05,
                    "Cost": "400",
                    "Profit": "50",
                    "Payment_Method": "UPI",
                },
            ]
        )

    def test_ingestion_adds_metadata(self):
        """Verify ingestion attaches source_file and timestamp metadata."""
        sample_csv = config.RAW_DATA_DIR / "sales_february.csv"
        if sample_csv.exists():
            df = ingest_file(sample_csv)
            self.assertIn("source_file", df.columns)
            self.assertIn("ingestion_timestamp", df.columns)
            self.assertEqual(df["source_file"].iloc[0], "sales_february.csv")

    def test_validation_quarantines_invalid_records(self):
        """Verify validation separates clean records from invalid ones."""
        valid_df, rejected_df = validate_records(self.sample_raw_df)
        self.assertEqual(len(valid_df), 2)
        self.assertEqual(len(rejected_df), 1)
        self.assertEqual(rejected_df["Order_ID"].iloc[0], "ORD0000002")
        self.assertIn("Missing Customer_ID", rejected_df["rejection_reason"].iloc[0])

    def test_cleaning_deduplication_and_standardization(self):
        """Verify cleaning deduplicates and normalizes dates, categories, and numbers."""
        valid_df, _ = validate_records(self.sample_raw_df)
        clean_df = clean_data(valid_df)

        # Should drop 1 duplicate order
        self.assertEqual(len(clean_df), 1)
        # Quantity "two" -> integer 2
        self.assertEqual(clean_df["Quantity"].iloc[0], 2)
        # Category "electronics" -> "Electronics"
        self.assertEqual(clean_df["Category"].iloc[0], "Electronics")
        # Missing discount filled with 0.0
        self.assertEqual(clean_df["Discount"].iloc[0], 0.0)
        # Standardized date format
        self.assertEqual(clean_df["Order_Date"].iloc[0], "2025-01-14")

    def test_transformation_recomputes_profit_and_metrics(self):
        """Verify transformation fixes profit and derives financial & calendar dimensions."""
        valid_df, _ = validate_records(self.sample_raw_df)
        clean_df = clean_data(valid_df)
        trans_df = transform_data(clean_df)

        # Sales 50000 - Cost 35000 = Profit 15000
        self.assertEqual(trans_df["Profit"].iloc[0], 15000.0)
        # Unit Price: 50000 / 2 = 25000
        self.assertEqual(trans_df["Unit_Price"].iloc[0], 25000.0)
        # Calendar dimensions
        self.assertEqual(trans_df["Order_Year"].iloc[0], 2025)
        self.assertEqual(trans_df["Order_Month"].iloc[0], 1)
        self.assertEqual(trans_df["Order_Quarter"].iloc[0], "Q1")
        self.assertIn("is_sales_outlier", trans_df.columns)

    def test_full_pipeline_run(self):
        """Verify end-to-end pipeline execution creates processed and summary outputs."""
        summary = run_pipeline()
        self.assertEqual(summary["status"], "SUCCESS")
        metrics = summary["pipeline_metrics"]
        self.assertGreater(metrics["raw_records_ingested"], 10000)
        self.assertGreater(metrics["final_processed_records"], 10000)
        self.assertGreater(summary["kpis"]["total_sales"], 0)

        processed_file = Path(summary["artifacts"]["processed_file"])
        self.assertTrue(processed_file.exists())
        self.assertGreater(processed_file.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
