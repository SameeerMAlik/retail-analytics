-- ============================================================
-- dbt Analytics: top_product_categories
-- Category & subcategory performance metrics
-- ============================================================

{{ config(materialized='table', schema='analytics') }}

WITH sales AS (
    SELECT
        f.*,
        p.CATEGORY,
        p.SUBCATEGORY,
        p.PRODUCT_NAME,
        p.PRICE_TIER,
        p.GROSS_MARGIN_PCT AS PRODUCT_MARGIN_PCT
    FROM {{ ref('fct_sales') }} f
    JOIN {{ ref('dim_product') }} p ON f.PRODUCT_SK = p.PRODUCT_SK
    WHERE f.IS_REVENUE_ORDER = TRUE
)

SELECT
    CATEGORY,
    SUBCATEGORY,
    COUNT(DISTINCT PRODUCT_SK)              AS NUM_PRODUCTS,
    COUNT(DISTINCT ORDER_ID)                AS NUM_ORDERS,
    COUNT(ORDER_ITEM_ID)                    AS NUM_ITEMS_SOLD,
    SUM(QUANTITY)                           AS TOTAL_UNITS_SOLD,
    ROUND(SUM(NET_REVENUE), 2)              AS TOTAL_REVENUE,
    ROUND(SUM(GROSS_PROFIT), 2)             AS TOTAL_PROFIT,
    ROUND(AVG(MARGIN_PCT), 2)               AS AVG_MARGIN_PCT,
    ROUND(AVG(UNIT_PRICE), 2)               AS AVG_SELLING_PRICE,
    ROUND(SUM(NET_REVENUE) / NULLIF(COUNT(DISTINCT ORDER_ID), 0), 2) AS REVENUE_PER_ORDER,

    -- Rank within the dataset
    RANK() OVER (ORDER BY SUM(NET_REVENUE) DESC)   AS REVENUE_RANK,
    RANK() OVER (ORDER BY SUM(GROSS_PROFIT) DESC)  AS PROFIT_RANK,

    -- Revenue share
    ROUND(SUM(NET_REVENUE) / SUM(SUM(NET_REVENUE)) OVER () * 100, 2) AS REVENUE_SHARE_PCT

FROM sales
GROUP BY CATEGORY, SUBCATEGORY
ORDER BY TOTAL_REVENUE DESC
