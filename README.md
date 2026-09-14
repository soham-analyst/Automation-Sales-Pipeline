# Automated Sales Data Pipeline

An end-to-end Python project for ingesting, validating, cleaning, transforming, and analyzing sales data from CSV and Excel files.

The project is designed as a practical data-engineering and analytics workflow. It preserves raw source values during ingestion, applies controlled data-quality rules during cleaning, creates analytical fields during transformation, flags numerical outliers, and prepares processed data for database loading.

## Project Overview

The pipeline follows this workflow:

```text
CSV / Excel Files
       ↓
Data Ingestion
       ↓
Data Validation and Cleaning
       ↓
Deduplication
       ↓
Transformation and Feature Engineering
       ↓
Outlier Detection
       ↓
Database Loading
       ↓
SQL Analysis / Power BI
```

## Main Features

- Automatic discovery of CSV and Excel files in `data/raw/`
- Support for `.csv`, `.xlsx`, and `.xls` files
- Standardization of inconsistent source column names
- Preservation of raw values during ingestion
- Metadata tracking using source filename and ingestion timestamp
- Duplicate-record removal
- Date and numeric-value cleaning
- Category normalization
- Handling of invalid quantities and sales values
- Detection of missing critical fields
- Recalculation of profit from sales and cost
- Category-based numerical outlier detection
- Automated tests using Pytest
- Configuration through environment variables
- CI workflow configuration through GitHub Actions

## Technology Stack

- **Python 3.10+**
- **Pandas** – data ingestion, cleaning, and transformation
- **NumPy** – numerical processing
- **OpenPyXL** – Excel file support
- **SQLAlchemy** – database connectivity
- **PyODBC** – SQL Server connectivity
- **python-dotenv** – environment-variable management
- **Pytest** – automated testing
- **Ruff** – linting
- **Black** – code formatting
- **Pyright** – static type checking
- **Power BI** – intended reporting and visualization layer

## Project Structure

```text
sales-data-pipeline/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
│
├── config/
│   ├── __init__.py
│   ├── config.py
│   └── database.py
│
├── data/
│   ├── raw/                 # Input CSV and Excel files
│   ├── processed/           # Transformed output files
│   ├── rejected/            # Rejected or quarantined records
│   └── archive/             # Archived source files
│
├── docs/
│   └── data_dictionary.md   # Source-column definitions and quality issues
│
├── logs/
│   └── pipeline_summary.json
│
├── powerbi/                 # Power BI-related project files
│
├── scripts/
│   ├── generate_sample_data.py
│   ├── test_db_connection.py
│   ├── push_to_github.ps1
│   └── push_to_github.bat
│
├── sql/
│   ├── create_tables.sql
│   ├── validation_queries.sql
│   └── analysis_queries.sql
│
├── src/
│   ├── ingestion.py
│   ├── cleaning.py
│   ├── transformation.py
│   ├── validation.py
│   ├── outliers.py
│   ├── loader.py
│   ├── database.py
│   └── pipeline.py
│
├── tests/
│   ├── test_smoke.py
│   ├── test_pipeline_stages.py
│   └── test_data_generator.py
│
├── .env.example
├── .gitignore
├── main.py
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## Input Data

The sample data is stored in:

```text
data/raw/
```

The repository includes monthly sales files such as:

- `sales_january.xlsx`
- `sales_february.csv`
- `sales_march.xlsx`
- `sales_april.csv`

The ingestion stage supports both CSV and Excel formats and processes files in a predictable, sorted order.

## Expected Source Columns

The canonical sales schema includes:

- `Order_ID`
- `Order_Date`
- `Customer_ID`
- `Customer_Name`
- `Product_ID`
- `Product_Name`
- `Category`
- `Sub_Category`
- `Region`
- `State`
- `City`
- `Sales`
- `Quantity`
- `Discount`
- `Cost`
- `Profit`
- `Payment_Method`

Additional ingestion metadata fields are added:

- `source_file`
- `ingestion_timestamp`

## Pipeline Stages

### 1. Ingestion

`src/ingestion.py`

The ingestion stage:

1. Discovers supported files in `data/raw/`
2. Reads CSV and Excel files
3. Loads source values as text to avoid premature data loss
4. Standardizes column names
5. Adds source-file metadata
6. Combines all files into one Pandas DataFrame

This approach allows later stages to identify values such as `N/A`, `unknown`, blank strings, and text-based numbers before conversion.

### 2. Validation and Cleaning

`src/validation.py` and `src/cleaning.py`

The cleaning process is responsible for:

- Removing duplicate `Order_ID` records
- Standardizing dates
- Normalizing category values
- Converting numeric fields
- Identifying invalid quantities
- Identifying invalid or non-positive sales
- Detecting missing critical fields
- Applying business rules for missing discounts
- Rejecting invalid records into `data/rejected/`

Rejected records are retained separately for traceability and quality review.

### 3. Transformation

`src/transformation.py`

The transformation stage prepares the cleaned data for analysis and feature engineering.

The project documentation specifies that profit should be recalculated using:

```text
Profit = Sales - Cost
```

This prevents incorrect source-system profit values from being trusted without verification.

### 4. Outlier Detection

`src/outliers.py`

The outlier stage identifies unusual numerical values using the Interquartile Range (IQR) method.

The default IQR rule is:

```text
Lower bound = Q1 - 1.5 × IQR
Upper bound = Q3 + 1.5 × IQR
```

The implementation flags outlier rows rather than deleting them, allowing downstream analysis to decide how they should be handled.

### 5. Database Loading

`src/loader.py` and `config/database.py`

The project contains database-connection and loading components for writing processed data to a relational database through SQLAlchemy.

Database configuration is managed through environment variables. Review `.env.example` before configuring a local database connection.

## Data Quality

The sample data is intentionally designed to contain realistic quality problems, including:

- Duplicate order IDs
- Inconsistent date formats
- Missing customer fields
- Missing product names
- Inconsistent category spelling and capitalization
- Text values in numeric columns
- Negative or zero sales
- Invalid quantities
- Missing discounts
- Incorrect reported profit values
- Extreme numerical values that may be outliers

A detailed description of the fields and known issues is available in:

```text
docs/data_dictionary.md
```

## Configuration

Create a local `.env` file based on:

```text
.env.example
```

Do not commit secrets, passwords, connection strings, or local environment files to source control.

The database configuration should be checked before running the full pipeline because the repository contains database-related modules and scripts that depend on the local database setup.

## Installation

Open a terminal in the project root and create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For development and testing tools, install:

```powershell
pip install -r requirements-dev.txt
```

## Running the Pipeline

From the project root, run:

```powershell
python main.py
```

The pipeline reads files from `data/raw/` and processes them through the ingestion, cleaning, transformation, outlier-detection, and loading stages.

## Running Tests

Run the test suite with:

```powershell
python -m pytest tests -v
```

The tests cover pipeline behavior and supporting functionality.

## Code Quality Checks

### Ruff

```powershell
ruff check .
```

### Black

```powershell
black --check .
```

### Pyright

```powershell
pyright
```

## Sample Data Generation

The project includes a sample-data generator:

```powershell
python scripts/generate_sample_data.py
```

Review the script before running it if you want to preserve the existing files in `data/raw/`.

## Database Connection Test

To test the configured database connection:

```powershell
python scripts/test_db_connection.py
```

Make sure the required database server, driver, credentials, and environment variables are configured first.

## SQL Files

The `sql/` directory contains SQL scripts for:

- Table creation
- Data validation
- Analytical queries

Before using these scripts, verify that the SQL dialect and database configuration match the database server configured for the project.

## Reporting and Power BI

The `powerbi/` directory is reserved for Power BI project assets and reporting work.

The processed data can be used to build reports showing:

- Sales performance
- Profit performance
- Regional performance
- Product and category performance
- Monthly trends
- Data-quality and outlier information

## Development Practices

The repository includes configuration for:

- Automated CI workflows
- Unit and smoke testing
- Linting
- Code formatting
- Static type checking
- Dependency management
- Release workflow automation

## Important Repository Notes

The uploaded project contains several placeholder or evolving components, particularly in parts of the database and SQL layers. Before presenting the project as production-ready, verify that:

1. The database type in the documentation matches the actual configured database.
2. The SQL scripts contain the final table definitions and analytical queries.
3. The loader and database modules use the same schema and table names.
4. The Power BI folder contains the final report or documentation.
5. The full pipeline and test suite run successfully in a clean virtual environment.

## Future Improvements

- Complete and document the final database schema
- Add a formal incremental-loading strategy
- Add stronger schema validation before cleaning
- Add pipeline run identifiers and audit tables
- Add data-quality metrics to the reporting layer
- Add automated data-quality reports
- Add database integration tests
- Add screenshots or a published Power BI report
- Add deployment and scheduling instructions

## Author

**Soham Indulkar**
