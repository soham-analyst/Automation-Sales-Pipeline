-- validation_queries.sql
-- Run these against automated_sales_pipeline AFTER a pipeline load to sanity
-- check what actually landed in the warehouse. This is data-quality
-- validation at the SQL layer - a second, independent check on top of the
-- Python-side validation in src/validation.py / src/cleaning.py.
--
-- Every query below should return ZERO rows on a healthy load, except #8
-- which is a summary you're meant to read.

USE automated_sales_pipeline;
GO

-- 1. Duplicate Order_ID
-- Should be structurally impossible (Order_ID is the PRIMARY KEY), but
-- useful to run during development before the constraint existed, or if
-- the loader is ever changed.
SELECT Order_ID, COUNT(*) AS occurrences
FROM dbo.fact_sales
GROUP BY Order_ID
HAVING COUNT(*) > 1;
GO

-- 2. Orphan Customer_ID - a fact row referencing a customer that was never
-- loaded into dim_customer (would indicate the loader inserted the fact
-- row before the dimension row - a load-order bug).
SELECT f.Order_ID, f.Customer_ID
FROM dbo.fact_sales f
LEFT JOIN dbo.dim_customer c ON f.Customer_ID = c.Customer_ID
WHERE c.Customer_ID IS NULL;
GO

-- 3. Orphan Product_ID
SELECT f.Order_ID, f.Product_ID
FROM dbo.fact_sales f
LEFT JOIN dbo.dim_product p ON f.Product_ID = p.Product_ID
WHERE p.Product_ID IS NULL;
GO

-- 4. Orphan Region_Key
SELECT f.Order_ID, f.Region_Key
FROM dbo.fact_sales f
LEFT JOIN dbo.dim_region r ON f.Region_Key = r.Region_Key
WHERE r.Region_Key IS NULL;
GO

-- 5. Non-positive Sales or Quantity
-- Should be structurally impossible (CHECK constraints on fact_sales block
-- this at insert time) - this query proves those constraints are working.
SELECT Order_ID, Sales, Quantity
FROM dbo.fact_sales
WHERE Sales <= 0 OR Quantity <= 0;
GO

-- 6. Profit that doesn't match Sales - Cost (within 1 paisa)
-- Catches a regression in transformation.py's Profit recompute if this
-- ever returns rows.
SELECT Order_ID, Sales, Cost, Profit, (Sales - Cost) AS Expected_Profit
FROM dbo.fact_sales
WHERE ABS(Profit - (Sales - Cost)) > 0.01;
GO

-- 7. Fact rows whose date falls outside the populated dim_date range
-- (would indicate dim_date needs to be regenerated for a wider range).
SELECT f.Order_ID, f.Order_Date
FROM dbo.fact_sales f
LEFT JOIN dbo.dim_date d ON f.Order_Date = d.Date_Key
WHERE d.Date_Key IS NULL;
GO

-- 8. Health summary - read this one, don't expect zero rows.
SELECT 'fact_sales' AS table_name, COUNT(*) AS row_count FROM dbo.fact_sales
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dbo.dim_customer
UNION ALL SELECT 'dim_product',  COUNT(*) FROM dbo.dim_product
UNION ALL SELECT 'dim_region',   COUNT(*) FROM dbo.dim_region
UNION ALL SELECT 'dim_date',     COUNT(*) FROM dbo.dim_date;
GO
