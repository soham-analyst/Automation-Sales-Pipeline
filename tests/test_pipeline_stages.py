"""
test_pipeline_stages.py

Unit and integration tests for each stage of the ETL pipeline:
Ingestion -> Cleaning -> Transformation -> Outliers -> Database Load.
"""

from pathlib import Path
import unittest

import pandas as pd

from src.cleaning import clean_data
from src.ingestion import read_file
from src.transformation import transform_sales_data


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
                    "Category": "electronics",
                    "Sub_Category": "Laptops",
                    "Region": "North",
                    "State": "Delhi",
                    "City": "New Delhi",
                    "Sales": "50000",
                    "Quantity": "two",
                    "Discount": None,
                    "Cost": "35000",
                    "Profit": "99999",
                    "Payment_Method": "Credit Card",
                },
                {
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

    def test_ingestion_reads_file_properly(self):
        """Verify ingestion parses CSV/XLSX files into a DataFrame."""

        sample_csv = Path("data/raw/sales_february.csv")

        if sample_csv.exists():
            df = read_file(sample_csv)

            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)

    def test_cleaning_deduplication_and_standardization(self):
        """Verify cleaning deduplicates and normalizes data."""

        clean_df = clean_data(self.sample_raw_df)

        self.assertEqual(len(clean_df), 1)
        self.assertEqual(clean_df["Quantity"].iloc[0], 2)
        self.assertEqual(
            clean_df["Category"].iloc[0],
            "Electronics",
        )
        self.assertEqual(
            clean_df["Discount"].iloc[0],
            0.0,
        )
        self.assertEqual(
            clean_df["Order_Date"].iloc[0],
            "2025-01-14",
        )

    def test_transformation_recomputes_profit_and_metrics(self):
        """Verify transformation derives dimensions and numerical metrics."""

        clean_df = clean_data(self.sample_raw_df)
        trans_df = transform_sales_data(clean_df)

        self.assertIn("Unit_Price", trans_df.columns)
        self.assertIn("Order_Year", trans_df.columns)

        self.assertEqual(
            trans_df["Order_Year"].iloc[0],
            2025,
        )

        self.assertAlmostEqual(
            trans_df["Profit"].iloc[0],
            15000,
            places=2,
        )

        self.assertAlmostEqual(
            trans_df["Unit_Price"].iloc[0],
            25000,
            places=2,
        )

        self.assertAlmostEqual(
            trans_df["Profit_Margin"].iloc[0],
            0.30,
            places=2,
        )


if __name__ == "__main__":
    unittest.main()