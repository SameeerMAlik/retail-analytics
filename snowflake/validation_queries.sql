-- ============================================================
-- Enterprise Retail Analytics Engine
-- Snowflake Validation Queries
-- ============================================================
-- Run these after data load to verify ingestion quality.
-- ============================================================

USE DATABASE RETAIL_ANALYTICS_DB;

-- ============================================================
-- SECTION 1: ROW COUNT VALIDATION
-- Expected: customers=10000, products=500, orders=50000, items=150000
-- ============================================================

SELECT 'STAGING.STG_CUSTOMERS'      AS table_name, COUNT(*) AS row_count, 10000  AS expected FROM STAGING.STG_CUSTOMERS
UNION ALL
SELECT 'STAGING.STG_PRODUCTS',                      COUNT(*),              500    FROM STAGING.STG_PRODUCTS
UNION ALL
SELECT 'STAGING.STG_ORDERS',                        COUNT(*),              50000  FROM STAGING.STG_ORDERS
UNION ALL
SELECT 'STAGING.STG_ORDER_ITEMS',                   COUNT(*),              150000 FROM STAGING.STG_ORDER_ITEMS
UNION ALL
SELECT 'STAGING.STG_COMPETITOR_PRICES',             COUNT(*),              35     FROM STAGING.STG_COMPETITOR_PRICES
ORDER BY table_name;

-- ============================================================
-- SECTION 2: NULL CHECK — CRITICAL COLUMNS
-- ============================================================

-- Customers: no nulls in key fields
SELECT
    SUM(CASE WHEN CUSTOMER_ID    IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN FULL_NAME      IS NULL THEN 1 ELSE 0 END) AS null_full_name,
    SUM(CASE WHEN EMAIL          IS NULL THEN 1 ELSE 0 END) AS null_email,
    SUM(CASE WHEN COUNTRY        IS NULL THEN 1 ELSE 0 END) AS null_country,
    COUNT(*)                                                  AS total_rows
FROM STAGING.STG_CUSTOMERS;

-- Products: no nulls in key fields
SELECT
    SUM(CASE WHEN PRODUCT_ID    IS NULL THEN 1 ELSE 0 END) AS null_product_id,
    SUM(CASE WHEN PRODUCT_NAME  IS NULL THEN 1 ELSE 0 END) AS null_product_name,
    SUM(CASE WHEN RETAIL_PRICE  IS NULL THEN 1 ELSE 0 END) AS null_retail_price,
    SUM(CASE WHEN BASE_COST     IS NULL THEN 1 ELSE 0 END) AS null_base_cost,
    COUNT(*)                                                 AS total_rows
FROM STAGING.STG_PRODUCTS;

-- ============================================================
-- SECTION 3: UNIQUENESS CHECKS — PRIMARY KEYS
-- ============================================================

-- Check for duplicate customer IDs
SELECT CUSTOMER_ID, COUNT(*) AS cnt
FROM STAGING.STG_CUSTOMERS
GROUP BY CUSTOMER_ID
HAVING cnt > 1
LIMIT 10;

-- Check for duplicate product IDs
SELECT PRODUCT_ID, COUNT(*) AS cnt
FROM STAGING.STG_PRODUCTS
GROUP BY PRODUCT_ID
HAVING cnt > 1
LIMIT 10;

-- Check for duplicate order IDs
SELECT ORDER_ID, COUNT(*) AS cnt
FROM STAGING.STG_ORDERS
GROUP BY ORDER_ID
HAVING cnt > 1
LIMIT 10;

-- Check for duplicate order item IDs
SELECT ORDER_ITEM_ID, COUNT(*) AS cnt
FROM STAGING.STG_ORDER_ITEMS
GROUP BY ORDER_ITEM_ID
HAVING cnt > 1
LIMIT 10;

-- ============================================================
-- SECTION 4: REFERENTIAL INTEGRITY
-- ============================================================

-- Orders with invalid customer_id
SELECT COUNT(*) AS orphan_orders
FROM STAGING.STG_ORDERS o
LEFT JOIN STAGING.STG_CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
WHERE c.CUSTOMER_ID IS NULL;

-- Order items with invalid order_id
SELECT COUNT(*) AS orphan_items_orders
FROM STAGING.STG_ORDER_ITEMS oi
LEFT JOIN STAGING.STG_ORDERS o ON oi.ORDER_ID = o.ORDER_ID
WHERE o.ORDER_ID IS NULL;

-- Order items with invalid product_id
SELECT COUNT(*) AS orphan_items_products
FROM STAGING.STG_ORDER_ITEMS oi
LEFT JOIN STAGING.STG_PRODUCTS p ON oi.PRODUCT_ID = p.PRODUCT_ID
WHERE p.PRODUCT_ID IS NULL;

-- ============================================================
-- SECTION 5: DATA QUALITY — BUSINESS RULES
-- ============================================================

-- Products where cost >= retail (loss-making items = data error)
SELECT COUNT(*) AS cost_exceeds_retail
FROM STAGING.STG_PRODUCTS
WHERE BASE_COST >= RETAIL_PRICE;

-- Orders with dates outside 2024 window
SELECT COUNT(*) AS out_of_range_orders
FROM STAGING.STG_ORDERS
WHERE ORDER_DATE < '2024-01-01' OR ORDER_DATE > '2024-12-31';

-- Order items with zero or negative quantity
SELECT COUNT(*) AS invalid_quantity
FROM STAGING.STG_ORDER_ITEMS
WHERE QUANTITY <= 0;

-- Order items with negative discount or discount > 1 (>100%)
SELECT COUNT(*) AS invalid_discount
FROM STAGING.STG_ORDER_ITEMS
WHERE DISCOUNT < 0 OR DISCOUNT > 1;

-- ============================================================
-- SECTION 6: DISTRIBUTION ANALYSIS
-- ============================================================

-- Revenue by category (quick sanity check)
SELECT
    p.CATEGORY,
    COUNT(DISTINCT oi.ORDER_ID)          AS num_orders,
    SUM(oi.QUANTITY * oi.UNIT_PRICE)     AS gross_revenue,
    ROUND(AVG(oi.UNIT_PRICE), 2)         AS avg_unit_price
FROM STAGING.STG_ORDER_ITEMS oi
JOIN STAGING.STG_PRODUCTS p ON oi.PRODUCT_ID = p.PRODUCT_ID
GROUP BY p.CATEGORY
ORDER BY gross_revenue DESC;

-- Orders by month (seasonal pattern check)
SELECT
    MONTH(ORDER_DATE)   AS month_num,
    MONTHNAME(ORDER_DATE) AS month_name,
    COUNT(*)            AS order_count
FROM STAGING.STG_ORDERS
GROUP BY month_num, month_name
ORDER BY month_num;

-- Customer country distribution
SELECT COUNTRY, COUNT(*) AS num_customers
FROM STAGING.STG_CUSTOMERS
GROUP BY COUNTRY
ORDER BY num_customers DESC;

-- Payment method distribution
SELECT PAYMENT_METHOD, COUNT(*) AS num_orders, ROUND(COUNT(*)*100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM STAGING.STG_ORDERS
GROUP BY PAYMENT_METHOD
ORDER BY num_orders DESC;

-- Order status distribution
SELECT ORDER_STATUS, COUNT(*) AS num_orders
FROM STAGING.STG_ORDERS
GROUP BY ORDER_STATUS
ORDER BY num_orders DESC;

-- ============================================================
-- SECTION 7: ANALYTICS LAYER VALIDATION (post-dbt)
-- ============================================================

-- Fact table grain check
SELECT COUNT(*) AS fct_rows, COUNT(DISTINCT ORDER_ITEM_ID) AS unique_items
FROM ANALYTICS.FCT_SALES;

-- Total revenue sanity check
SELECT
    ROUND(SUM(NET_REVENUE), 2)    AS total_net_revenue,
    ROUND(AVG(NET_REVENUE), 2)    AS avg_order_item_revenue,
    ROUND(SUM(GROSS_PROFIT), 2)   AS total_gross_profit,
    ROUND(AVG(MARGIN_PCT), 2)     AS avg_margin_pct
FROM ANALYTICS.FCT_SALES
WHERE ORDER_STATUS = 'Completed';

-- Dimension coverage
SELECT
    (SELECT COUNT(DISTINCT CUSTOMER_SK) FROM ANALYTICS.FCT_SALES)  AS customers_in_fact,
    (SELECT COUNT(*) FROM ANALYTICS.DIM_CUSTOMER)                   AS total_dim_customers,
    (SELECT COUNT(DISTINCT PRODUCT_SK) FROM ANALYTICS.FCT_SALES)    AS products_in_fact,
    (SELECT COUNT(*) FROM ANALYTICS.DIM_PRODUCT)                    AS total_dim_products;

-- ============================================================
-- ALL VALIDATIONS COMPLETE
-- ============================================================
SELECT '✅ Validation queries executed successfully' AS status;
