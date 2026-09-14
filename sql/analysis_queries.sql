-- analysis_queries.sql
-- Placeholder. Filled in during Part 10 (MySQL Database Design)
-- and Part 16 (SQL Analysis).
-- 1. Total sales and profit by category
SELECT
    p.Category,
    SUM(f.Sales) AS total_sales,
    SUM(f.Profit) AS total_profit,
    AVG(f.Profit_Margin) AS average_profit_margin
FROM fact_sales f
JOIN dim_product p
    ON f.Product_ID = p.Product_ID
GROUP BY p.Category
ORDER BY total_sales DESC;


-- 2. Monthly sales and profit
SELECT
    YEAR(Order_Date) AS sales_year,
    MONTH(Order_Date) AS sales_month,
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit
FROM fact_sales
GROUP BY
    YEAR(Order_Date),
    MONTH(Order_Date)
ORDER BY
    sales_year,
    sales_month;


-- 3. Regional performance
SELECT
    r.State,
    SUM(f.Sales) AS total_sales,
    SUM(f.Profit) AS total_profit,
    COUNT(*) AS order_count,
    AVG(f.Profit_Margin) AS average_profit_margin
FROM fact_sales f
JOIN dim_region r
    ON f.Region_Key = r.Region_Key
GROUP BY r.State
ORDER BY total_sales DESC;


-- 4. Most profitable states
SELECT
    r.State,
    SUM(f.Profit) AS total_profit
FROM fact_sales f
JOIN dim_region r
    ON f.Region_Key = r.Region_Key
GROUP BY r.State
ORDER BY total_profit DESC;


-- 5. Top 10 customers by sales
SELECT TOP 10
    c.Customer_ID,
    c.Customer_Name,
    SUM(f.Sales) AS total_sales,
    SUM(f.Profit) AS total_profit
FROM fact_sales f
JOIN dim_customer c
    ON f.Customer_ID = c.Customer_ID
GROUP BY
    c.Customer_ID,
    c.Customer_Name
ORDER BY total_sales DESC;


-- 6. Outlier analysis
SELECT
    Is_Outlier,
    COUNT(*) AS row_count,
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit
FROM fact_sales
GROUP BY Is_Outlier;