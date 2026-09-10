# Data Dictionary — Automated Sales Data Pipeline

Source: `data/raw/sales_<month>.xlsx / .csv`
Grain: **one row = one product line item within one order** (an order with 3 products
would appear as 3 rows sharing the same `Order_ID` in a real system — in this simplified
generator each `Order_ID` maps to a single line item, which is a common simplification
for a beginner-to-intermediate portfolio project).

| Column | Data Type (target, after cleaning) | Business Meaning | Expected Values | Notes / Known Data-Quality Issues |
|---|---|---|---|---|
| `Order_ID` | string (e.g. `ORD0000407`) | Unique identifier for the sales transaction. | `ORD` + 7-digit zero-padded number | **Primary key** for `fact_sales`. Duplicates exist in raw files (~1.5% of rows) and must be removed. |
| `Order_Date` | date (`YYYY-MM-DD`) | Date the order was placed. | Any date within the file's month | Stored as **text in inconsistent formats** in raw files (`2025-01-14`, `14/01/2025`, `01-14-2025`, `14-Jan-2025`, `14 January 2025`). Must be parsed and standardized. |
| `Customer_ID` | string (e.g. `CUST00152`) | Unique identifier for the customer. | `CUST` + 5-digit number | Foreign key to `dim_customer`. ~0.5% of rows have this blank. |
| `Customer_Name` | string | Customer's display name. | Free text | ~0.5% of rows have this blank (independently of `Customer_ID` being blank). Not unique — used for display only, never as a key. |
| `Product_ID` | string (e.g. `PROD0026`) | Unique identifier for the product. | `PROD` + 4-digit number | Foreign key to `dim_product`. |
| `Product_Name` | string | Product's display name. | Free text | ~0.8% of rows have this blank. |
| `Category` | string | Top-level product grouping. | `Electronics`, `Furniture`, `Clothing`, `Grocery`, `Office Supplies` | **Inconsistent casing/spelling injected** (`electronics`, `ELECTRONICS`, `Electronic`, trailing spaces, etc.) in ~10% of rows — must be standardized to a fixed set of 5 values during cleaning. |
| `Sub_Category` | string | Second-level product grouping. | e.g. `Laptops`, `Chairs`, `Men's Wear` | Depends on `Category`; used for the Product Analysis Power BI page. |
| `Region` | string | Sales region. | `North`, `South`, `East`, `West` | Clean in this dataset; still validated against an allow-list. |
| `State` | string | Indian state. | e.g. `Maharashtra`, `Karnataka` | Must roll up consistently to `Region`. |
| `City` | string | City. | e.g. `Mumbai`, `Chennai` | Lowest grain of geography. |
| `Sales` | decimal(12,2) | Revenue for this line item **after discount**. | Positive number, roughly ₹50 – ₹100,000 | Contains **text placeholders** (`N/A`, `unknown`, `-`) in ~0.4% of rows, **negative/zero values** in ~0.5%, and **extreme outliers** (15–40× normal) in ~0.3%. Must be cast to numeric and validated. |
| `Quantity` | integer | Number of units sold in this line item. | 1 – 7 | Contains **text values** (`"five"`, `"N/A"`, `""`) in ~0.5% of rows and **negative values** in ~0.5%. |
| `Discount` | decimal(4,2) | Discount applied, as a fraction (0.10 = 10%). | 0.0 – 0.25 | ~2% of rows are blank — business rule: treat missing discount as `0`, not as unknown, since "no promo applied" is the overwhelmingly likely case. |
| `Cost` | decimal(12,2) | Total cost of goods for this line item (`unit_cost × quantity`). | Positive number, always ≤ Sales in a healthy record | Generally clean; used to validate `Profit`. |
| `Profit` | decimal(12,2) | Reported profit for the line item. | Ideally `Sales − Cost` | **Deliberately wrong** in ~3% of rows (inflated 1.5×–3×) to simulate a source system computing profit incorrectly. The pipeline **recomputes** `Profit = Sales − Cost` during transformation rather than trusting this column blindly — see Part 8. |
| `Payment_Method` | string | How the customer paid. | `Credit Card`, `Debit Card`, `UPI`, `Net Banking`, `Cash on Delivery` | Clean in this dataset; still validated against an allow-list. |

## Derived / metadata columns added during ingestion (Part 5)

| Column | Meaning |
|---|---|
| `source_file` | Filename the row was loaded from (e.g. `sales_january.xlsx`) — enables tracing any row back to its origin file. |
| `ingestion_timestamp` | UTC timestamp when the ingestion step read the row. |

## Keys & relationships (used in Part 10 — MySQL schema)

- **`Order_ID`** → primary key of `fact_sales` (after de-duplication).
- **`Customer_ID`** → foreign key to `dim_customer(Customer_ID)`.
- **`Product_ID`** → foreign key to `dim_product(Product_ID)`.
- **`Order_Date`** → foreign key to `dim_date(date_key)` once standardized.
- **`Region` / `State` / `City`** → normalized into `dim_region` (or kept denormalized on `dim_customer`/order — decided explicitly in Part 10, with trade-offs explained).

## Summary of injected data-quality problems (this run, seed=42)

| File | Rows (incl. dupes) | Duplicate `Order_ID` | Missing customer field | Missing `Product_Name` | Category spelling variants |
|---|---|---|---|---|---|
| sales_january.xlsx | 3,248 | 48 | 32 | 25 | 25 |
| sales_february.csv | 3,146 | 46 | 31 | 25 | 25 |
| sales_march.xlsx | 3,451 | 51 | 34 | 27 | 25 |
| sales_april.csv | 3,349 | 49 | 33 | 26 | 25 |
| **Total** | **13,194** | | | | |

Plus (not easily row-counted with a one-liner, but present in every file): inconsistent
date-format text, text-instead-of-number values in `Quantity`/`Sales`, negative/zero
`Sales` and `Quantity`, mismatched `Profit`, and extreme outlier `Sales` values —
each at roughly the rates documented in `scripts/generate_sample_data.py`.
