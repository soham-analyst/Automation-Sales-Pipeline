"""
generate_sample_data.py

Generates realistic monthly sales files (sales_january.xlsx, sales_february.csv,
sales_march.xlsx, sales_april.csv) for the Automated Sales Data Pipeline project.

These files intentionally contain real-world data-quality problems so the
cleaning/validation pipeline (Parts 6-7 of the project) has something genuine
to demonstrate:
    - duplicate records
    - missing customer values
    - missing product values
    - inconsistent date formats
    - incorrect data types in numeric columns
    - blank discount values
    - inconsistent category name casing/spelling
    - invalid (negative/zero) sales values
    - negative/invalid quantities
    - incorrect / inconsistent profit values
    - extreme outlier sales values

Run:
    python scripts/generate_sample_data.py

Output:
    data/raw/sales_january.xlsx
    data/raw/sales_february.csv
    data/raw/sales_march.xlsx
    data/raw/sales_april.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG_SEED = 42
rng = np.random.default_rng(RNG_SEED)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference / lookup data
# ---------------------------------------------------------------------------

CATEGORY_MAP = {
    "Electronics": ["Mobile Phones", "Laptops", "Televisions", "Headphones", "Cameras"],
    "Furniture": ["Chairs", "Tables", "Bookcases", "Sofas", "Storage Units"],
    "Clothing": ["Men's Wear", "Women's Wear", "Kids Wear", "Footwear", "Accessories"],
    "Grocery": ["Beverages", "Snacks", "Dairy", "Staples", "Personal Care"],
    "Office Supplies": ["Paper", "Binders", "Art Supplies", "Storage", "Appliances"],
}

# Rough unit-price bands per category so numbers stay believable
CATEGORY_PRICE_RANGE = {
    "Electronics": (1500, 60000),
    "Furniture": (800, 35000),
    "Clothing": (300, 4000),
    "Grocery": (50, 1200),
    "Office Supplies": (100, 6000),
}

REGION_STATE_CITY = {
    "North": {
        "Delhi": ["New Delhi", "Dwarka", "Rohini"],
        "Punjab": ["Ludhiana", "Amritsar"],
        "Haryana": ["Gurugram", "Faridabad"],
    },
    "South": {
        "Karnataka": ["Bengaluru", "Mysuru"],
        "Tamil Nadu": ["Chennai", "Coimbatore"],
        "Telangana": ["Hyderabad", "Warangal"],
    },
    "East": {
        "West Bengal": ["Kolkata", "Howrah"],
        "Odisha": ["Bhubaneswar", "Cuttack"],
        "Bihar": ["Patna", "Gaya"],
    },
    "West": {
        "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
        "Gujarat": ["Ahmedabad", "Surat"],
        "Rajasthan": ["Jaipur", "Udaipur"],
    },
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Cash on Delivery"]
PAYMENT_WEIGHTS = [0.28, 0.20, 0.32, 0.12, 0.08]

FIRST_NAMES = [
    "Aarav",
    "Vivaan",
    "Aditi",
    "Diya",
    "Ishaan",
    "Kabir",
    "Meera",
    "Rohan",
    "Saanvi",
    "Ananya",
    "Arjun",
    "Kavya",
    "Neha",
    "Rahul",
    "Priya",
    "Sanya",
    "Vikram",
    "Pooja",
    "Karan",
    "Riya",
    "Aryan",
    "Tanvi",
    "Manish",
    "Shreya",
    "Nikhil",
    "Divya",
    "Amit",
    "Sneha",
    "Rajesh",
    "Pallavi",
]
LAST_NAMES = [
    "Sharma",
    "Verma",
    "Patel",
    "Gupta",
    "Iyer",
    "Nair",
    "Reddy",
    "Khan",
    "Singh",
    "Kumar",
    "Das",
    "Mehta",
    "Joshi",
    "Chatterjee",
    "Rao",
    "Malhotra",
]

N_CUSTOMERS = 900
N_PRODUCTS_PER_SUBCAT = 4

# Build a fixed customer pool so the same Customer_ID appears across months (repeat customers)
customer_pool = []
for i in range(1, N_CUSTOMERS + 1):
    cid = f"CUST{i:05d}"
    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    customer_pool.append((cid, name))

# Build a fixed product catalog
product_pool = []
pid_counter = 1
for category, subcats in CATEGORY_MAP.items():
    for subcat in subcats:
        for _ in range(N_PRODUCTS_PER_SUBCAT):
            pid = f"PROD{pid_counter:04d}"
            low, high = CATEGORY_PRICE_RANGE[category]
            unit_price = round(rng.uniform(low, high), 2)
            unit_cost = round(unit_price * rng.uniform(0.55, 0.8), 2)  # cost is 55-80% of price
            pname = f"{subcat[:-1] if subcat.endswith('s') else subcat} Item {pid_counter}"
            product_pool.append(
                {
                    "Product_ID": pid,
                    "Product_Name": pname,
                    "Category": category,
                    "Sub_Category": subcat,
                    "unit_price": unit_price,
                    "unit_cost": unit_cost,
                }
            )
            pid_counter += 1
product_df = pd.DataFrame(product_pool)

# Flatten region/state/city for sampling
region_state_city_flat = []
for region, states in REGION_STATE_CITY.items():
    for state, cities in states.items():
        for city in cities:
            region_state_city_flat.append((region, state, city))

# Inconsistent category spelling variants used to inject messiness
CATEGORY_VARIANTS = {
    "Electronics": ["electronics", "ELECTRONICS", "Electronic", "Electronics "],
    "Furniture": ["furniture", "FURNITURE", "Furnitures", " Furniture"],
    "Clothing": ["clothing", "CLOTHING", "Cloths", "Apparel"],
    "Grocery": ["grocery", "GROCERY", "Groceries", "Grocery "],
    "Office Supplies": ["office supplies", "OFFICE SUPPLIES", "Office-Supplies", "OfficeSupplies"],
}

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y", "%d %B %Y"]


def make_month_data(month_name: str, month_num: int, year: int, n_rows: int, order_id_start: int):
    """Generate a clean base DataFrame for one month, then return it (issues injected later)."""
    days_in_month = pd.Period(f"{year}-{month_num:02d}").days_in_month

    rows = []
    for i in range(n_rows):
        order_id = order_id_start + i
        day = rng.integers(1, days_in_month + 1)
        order_date = pd.Timestamp(year=year, month=month_num, day=day)

        cust_id, cust_name = customer_pool[rng.integers(0, len(customer_pool))]
        product = product_df.iloc[rng.integers(0, len(product_df))]

        region, state, city = region_state_city_flat[rng.integers(0, len(region_state_city_flat))]

        quantity = int(rng.integers(1, 8))
        discount_pct = round(rng.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2, 0.25]), 2)

        unit_price = product["unit_price"]
        unit_cost = product["unit_cost"]

        gross_sales = unit_price * quantity
        sales = round(gross_sales * (1 - discount_pct), 2)
        cost = round(unit_cost * quantity, 2)
        profit = round(sales - cost, 2)

        payment_method = rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS)

        rows.append(
            {
                "Order_ID": f"ORD{order_id:07d}",
                "Order_Date": order_date,
                "Customer_ID": cust_id,
                "Customer_Name": cust_name,
                "Product_ID": product["Product_ID"],
                "Product_Name": product["Product_Name"],
                "Category": product["Category"],
                "Sub_Category": product["Sub_Category"],
                "Region": region,
                "State": state,
                "City": city,
                "Sales": sales,
                "Quantity": quantity,
                "Discount": discount_pct,
                "Cost": cost,
                "Profit": profit,
                "Payment_Method": payment_method,
            }
        )

    return pd.DataFrame(rows)


def inject_data_quality_issues(df: pd.DataFrame, month_label: str) -> pd.DataFrame:
    """Deliberately corrupt a controlled percentage of rows so the cleaning
    pipeline has realistic problems to detect and fix."""
    df = df.copy()
    n = len(df)

    # --- 1. Duplicate records (~1.5%): re-append exact copies of random existing rows
    dup_count = int(n * 0.015)
    dup_rows = df.sample(dup_count, random_state=rng.integers(0, 1_000_000))
    df = pd.concat([df, dup_rows], ignore_index=True)
    n = len(df)  # refresh after adding duplicates

    # --- 2. Missing customer values (~1%): blank out Customer_Name or Customer_ID
    idx = rng.choice(n, size=int(n * 0.01), replace=False)
    for i in idx:
        if rng.random() < 0.5:
            df.loc[i, "Customer_Name"] = np.nan
        else:
            df.loc[i, "Customer_ID"] = np.nan

    # --- 3. Missing product values (~0.8%)
    idx = rng.choice(n, size=int(n * 0.008), replace=False)
    df.loc[idx, "Product_Name"] = np.nan

    # --- 4. Inconsistent date formats (~15%): re-render Order_Date as text in various formats
    df["Order_Date"] = df["Order_Date"].astype(object)
    idx = rng.choice(n, size=int(n * 0.15), replace=False)
    for i in idx:
        fmt = DATE_FORMATS[rng.integers(0, len(DATE_FORMATS))]
        ts = pd.Timestamp(df.loc[i, "Order_Date"])
        df.loc[i, "Order_Date"] = ts.strftime(fmt)
    # remaining dates: keep as ISO text too, so the whole column is text (realistic for CSV/Excel export)
    remaining_mask = df["Order_Date"].apply(lambda v: isinstance(v, pd.Timestamp))
    df.loc[remaining_mask, "Order_Date"] = df.loc[remaining_mask, "Order_Date"].apply(
        lambda v: v.strftime("%Y-%m-%d")
    )

    # --- 5. Incorrect data types in numeric columns (~0.5%): inject text into Quantity/Sales
    idx = rng.choice(n, size=int(n * 0.005), replace=False)
    df["Quantity"] = df["Quantity"].astype(object)
    for i in idx:
        df.loc[i, "Quantity"] = rng.choice(["five", "N/A", "two", ""])

    idx = rng.choice(n, size=int(n * 0.004), replace=False)
    df["Sales"] = df["Sales"].astype(object)
    for i in idx:
        df.loc[i, "Sales"] = rng.choice(["N/A", "unknown", "-"])

    # --- 6. Blank discount values (~2%)
    df["Discount"] = df["Discount"].astype(object)
    idx = rng.choice(n, size=int(n * 0.02), replace=False)
    df.loc[idx, "Discount"] = np.nan

    # --- 7. Inconsistent category name casing/spelling (~10%)
    idx = rng.choice(n, size=int(n * 0.10), replace=False)
    for i in idx:
        cat = df.loc[i, "Category"]
        if cat in CATEGORY_VARIANTS:
            df.loc[i, "Category"] = rng.choice(CATEGORY_VARIANTS[cat])

    # --- 8. Invalid sales values: negative or zero (~0.5%)
    idx = rng.choice(n, size=int(n * 0.005), replace=False)
    for i in idx:
        cur = df.loc[i, "Sales"]
        try:
            val = float(cur)
            df.loc[i, "Sales"] = -abs(val) if rng.random() < 0.5 else 0
        except (ValueError, TypeError):
            pass

    # --- 9. Negative/invalid quantities (~0.5%)
    idx = rng.choice(n, size=int(n * 0.005), replace=False)
    for i in idx:
        cur = df.loc[i, "Quantity"]
        try:
            val = int(cur)
            df.loc[i, "Quantity"] = -abs(val) if val != 0 else -1
        except (ValueError, TypeError):
            pass

    # --- 10. Incorrect / inconsistent profit values (~3%): mismatched with Sales - Cost
    idx = rng.choice(n, size=int(n * 0.03), replace=False)
    for i in idx:
        df.loc[i, "Profit"] = round(df.loc[i, "Profit"] * rng.uniform(1.5, 3.0), 2)

    # --- 11. Extreme outlier sales values (~0.3%): unusually large orders
    idx = rng.choice(n, size=int(n * 0.003), replace=False)
    for i in idx:
        cur = df.loc[i, "Sales"]
        try:
            val = float(cur)
            df.loc[i, "Sales"] = round(val * rng.uniform(15, 40), 2)
        except (ValueError, TypeError):
            pass

    # Shuffle row order so issues aren't clustered at the bottom
    df = df.sample(frac=1, random_state=rng.integers(0, 1_000_000)).reset_index(drop=True)

    print(f"[{month_label}] rows generated (incl. injected duplicates): {len(df)}")
    return df


def main():
    months = [
        ("January", 1, 2025, 3200, "sales_january.xlsx"),
        ("February", 2, 2025, 3100, "sales_february.csv"),
        ("March", 3, 2025, 3400, "sales_march.xlsx"),
        ("April", 4, 2025, 3300, "sales_april.csv"),
    ]

    order_id_cursor = 1
    for month_name, month_num, year, n_rows, filename in months:
        base_df = make_month_data(month_name, month_num, year, n_rows, order_id_cursor)
        order_id_cursor += n_rows + 500  # gap so Order_IDs don't collide across months
        dirty_df = inject_data_quality_issues(base_df, month_name)

        out_path = OUTPUT_DIR / filename
        if filename.endswith(".xlsx"):
            dirty_df.to_excel(out_path, index=False, sheet_name="Sales")
        else:
            dirty_df.to_csv(out_path, index=False)
        print(f"  -> saved {out_path}")

    print("\nSample data generation complete.")


if __name__ == "__main__":
    main()
