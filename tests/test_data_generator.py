"""
test_data_generator.py
Validates sample data generator constants, rules, and generated datasets.
Compatible with both pytest and standard unittest.
"""

import csv
import unittest
from scripts import generate_sample_data
from config import config

EXPECTED_COLUMNS = {
    "Order_ID",
    "Order_Date",
    "Customer_ID",
    "Customer_Name",
    "Product_ID",
    "Product_Name",
    "Category",
    "Sub_Category",
    "Region",
    "State",
    "City",
    "Sales",
    "Quantity",
    "Discount",
    "Cost",
    "Profit",
    "Payment_Method",
}


class TestDataGenerator(unittest.TestCase):
    def test_generator_constants(self):
        """Verify generator reference structures."""
        self.assertGreaterEqual(len(generate_sample_data.CATEGORY_MAP), 5)
        self.assertIn("Electronics", generate_sample_data.CATEGORY_MAP)
        self.assertIn("North", generate_sample_data.REGION_STATE_CITY)
        self.assertIn("Credit Card", generate_sample_data.PAYMENT_METHODS)

    def test_raw_sample_files_exist(self):
        """Verify that the expected raw data files exist in data/raw."""
        expected_files = [
            "sales_january.xlsx",
            "sales_february.csv",
            "sales_march.xlsx",
            "sales_april.csv",
        ]
        for filename in expected_files:
            filepath = config.RAW_DATA_DIR / filename
            self.assertTrue(filepath.exists(), f"Expected raw file {filename} does not exist")
            self.assertGreater(filepath.stat().st_size, 0, f"File {filename} is empty")

    def test_csv_file_headers(self):
        """Verify that generated CSV files contain expected columns."""
        csv_files = list(config.RAW_DATA_DIR.glob("*.csv"))
        self.assertGreater(len(csv_files), 0, "No CSV files found in data/raw")

        for csv_file in csv_files:
            with open(csv_file, mode="r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                headers = next(reader)
                header_set = set(headers)
                missing = EXPECTED_COLUMNS - header_set
                self.assertFalse(missing, f"{csv_file.name} is missing expected columns: {missing}")


if __name__ == "__main__":
    unittest.main()
