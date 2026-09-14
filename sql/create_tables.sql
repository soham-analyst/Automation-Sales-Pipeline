-- create_tables.sql
-- Star schema for the Automated Sales Data Pipeline.
-- Target: SQL Server / LocalDB (matches config/database.py: mssql+pyodbc)
--
-- Run this ONCE against the "automated_sales_pipeline" database before the
-- first pipeline load. Safe to re-run during development - it drops and
-- recreates every table.
--
-- Run it via: sqlcmd -S "(LocalDB)\MSSQLLocalDB" -d automated_sales_pipeline -i sql\create_tables.sql
-- or open it in SQL Server Management Studio / Azure Data Studio and hit Execute.

USE automated_sales_pipeline;
GO

-- ============================================================
-- Drop existing objects (children before parents, FK-safe order)
-- ============================================================
IF OBJECT_ID('dbo.fact_sales', 'U') IS NOT NULL DROP TABLE dbo.fact_sales;
IF OBJECT_ID('dbo.dim_customer', 'U') IS NOT NULL DROP TABLE dbo.dim_customer;
IF OBJECT_ID('dbo.dim_product', 'U') IS NOT NULL DROP TABLE dbo.dim_product;
IF OBJECT_ID('dbo.dim_region', 'U') IS NOT NULL DROP TABLE dbo.dim_region;
IF OBJECT_ID('dbo.dim_date', 'U') IS NOT NULL DROP TABLE dbo.dim_date;
GO

-- ============================================================
-- dim_date - one row per calendar day, 2024-01-01 .. 2026-12-31.
-- Populated once below by this script - the Python loader never
-- touches this table, since it doesn't change when new sales files
-- arrive.
-- ============================================================
CREATE TABLE dbo.dim_date (
    Date_Key    DATE          NOT NULL PRIMARY KEY,
    [Year]      SMALLINT      NOT NULL,
    [Quarter]   TINYINT       NOT NULL,
    [Month]     TINYINT       NOT NULL,
    MonthName   VARCHAR(10)   NOT NULL,
    [Day]       TINYINT       NOT NULL,
    DayName     VARCHAR(10)   NOT NULL,
    YearMonth   CHAR(7)       NOT NULL,   -- e.g. '2025-04', used for monthly trend visuals
    IsWeekend   BIT           NOT NULL
);
GO

-- ============================================================
-- dim_customer - populated by the Python loader from distinct
-- (Customer_ID, Customer_Name) pairs seen in the source data.
-- ============================================================
CREATE TABLE dbo.dim_customer (
    Customer_ID     VARCHAR(20)   NOT NULL PRIMARY KEY,
    Customer_Name   VARCHAR(150)  NOT NULL
);
GO

-- ============================================================
-- dim_product - populated by the Python loader from distinct
-- (Product_ID, Product_Name, Category, Sub_Category) rows.
-- ============================================================
CREATE TABLE dbo.dim_product (
    Product_ID      VARCHAR(20)   NOT NULL PRIMARY KEY,
    Product_Name    VARCHAR(150)  NOT NULL,
    Category        VARCHAR(50)   NOT NULL,
    Sub_Category    VARCHAR(50)   NOT NULL
);
GO

-- ============================================================
-- dim_region - surrogate key, since Region/State/City has no
-- natural single-column key. Populated by the Python loader.
-- ============================================================
CREATE TABLE dbo.dim_region (
    Region_Key  INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    Region      VARCHAR(20)       NOT NULL,
    [State]     VARCHAR(50)       NOT NULL,
    City        VARCHAR(50)       NOT NULL,
    CONSTRAINT UQ_dim_region UNIQUE (Region, [State], City)
);
GO

-- ============================================================
-- fact_sales - one row per order line item (the grain defined in
-- docs/data_dictionary.md). Populated incrementally by the Python
-- loader (Part 11/12) - only new Order_IDs get inserted on each run.
-- ============================================================
CREATE TABLE dbo.fact_sales (
    Order_ID VARCHAR(20) NOT NULL PRIMARY KEY,
    Order_Date DATE NOT NULL,
    Customer_ID VARCHAR(20) NOT NULL,
    Product_ID VARCHAR(20) NOT NULL,
    Region_Key INT NOT NULL,
    Payment_Method VARCHAR(30) NOT NULL,
    Sales DECIMAL(12,2) NOT NULL,
    Quantity INT NOT NULL,
    Discount DECIMAL(4,2) NOT NULL,
    Cost DECIMAL(12,2) NOT NULL,
    Profit DECIMAL(12,2) NOT NULL,
    Profit_Margin DECIMAL(6,4) NULL,
    Gross_Revenue DECIMAL(12,2) NOT NULL,
    Is_Outlier BIT NOT NULL DEFAULT 0,
    Source_File VARCHAR(100) NOT NULL,
    Ingestion_Timestamp DATETIME2 NOT NULL,

    CONSTRAINT FK_fact_sales_date     FOREIGN KEY (Order_Date)  REFERENCES dbo.dim_date     (Date_Key),
    CONSTRAINT FK_fact_sales_customer FOREIGN KEY (Customer_ID) REFERENCES dbo.dim_customer (Customer_ID),
    CONSTRAINT FK_fact_sales_product  FOREIGN KEY (Product_ID)  REFERENCES dbo.dim_product  (Product_ID),
    CONSTRAINT FK_fact_sales_region   FOREIGN KEY (Region_Key)  REFERENCES dbo.dim_region   (Region_Key),

    CONSTRAINT CK_fact_sales_sales_positive    CHECK (Sales > 0),
    CONSTRAINT CK_fact_sales_quantity_positive CHECK (Quantity > 0),
    CONSTRAINT CK_fact_sales_discount_range    CHECK (Discount >= 0 AND Discount <= 1)
);
GO

-- Indexes to speed up the most common Power BI / analysis query patterns
CREATE INDEX IX_fact_sales_order_date  ON dbo.fact_sales (Order_Date);
CREATE INDEX IX_fact_sales_customer_id ON dbo.fact_sales (Customer_ID);
CREATE INDEX IX_fact_sales_product_id  ON dbo.fact_sales (Product_ID);
CREATE INDEX IX_fact_sales_region_key  ON dbo.fact_sales (Region_Key);
GO

-- ============================================================
-- Populate dim_date for a fixed 3-year range. SQL Server has no
-- built-in "generate a date series" function before 2022, so a
-- recursive CTE is the standard way to do this.
-- ============================================================
DECLARE @StartDate DATE = '2024-01-01';
DECLARE @EndDate   DATE = '2026-12-31';

;WITH DateSeries AS (
    SELECT @StartDate AS DateValue
    UNION ALL
    SELECT DATEADD(DAY, 1, DateValue)
    FROM DateSeries
    WHERE DateValue < @EndDate
)
INSERT INTO dbo.dim_date (Date_Key, [Year], [Quarter], [Month], MonthName, [Day], DayName, YearMonth, IsWeekend)
SELECT
    DateValue,
    YEAR(DateValue),
    DATEPART(QUARTER, DateValue),
    MONTH(DateValue),
    DATENAME(MONTH, DateValue),
    DAY(DateValue),
    DATENAME(WEEKDAY, DateValue),
    FORMAT(DateValue, 'yyyy-MM'),
    CASE WHEN DATENAME(WEEKDAY, DateValue) IN ('Saturday', 'Sunday') THEN 1 ELSE 0 END
FROM DateSeries
OPTION (MAXRECURSION 1100);
GO

PRINT 'Schema created. dim_date populated for 2024-01-01 through 2026-12-31.';
