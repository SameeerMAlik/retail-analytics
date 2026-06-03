-- ============================================================
-- dbt Analytics: customer_lifetime_value
-- CLV calculation + RFM segmentation
-- ============================================================

{{ config(materialized='table', schema='analytics') }}

WITH sales AS (
    SELECT * FROM {{ ref('fct_sales') }}
    WHERE IS_REVENUE_ORDER = TRUE
),

customer_agg AS (
    SELECT
        CUSTOMER_SK,
        COUNT(DISTINCT ORDER_ID)                    AS TOTAL_ORDERS,
        COUNT(ORDER_ITEM_ID)                        AS TOTAL_ITEMS,
        SUM(NET_REVENUE)                            AS TOTAL_REVENUE,
        SUM(GROSS_PROFIT)                           AS TOTAL_PROFIT,
        MIN(ORDER_DATE)                             AS FIRST_ORDER_DATE,
        MAX(ORDER_DATE)                             AS LAST_ORDER_DATE,
        DATEDIFF('day', MIN(ORDER_DATE), MAX(ORDER_DATE)) AS ACTIVE_DAYS,
        DATEDIFF('day', MAX(ORDER_DATE), '2024-12-31'::DATE) AS DAYS_SINCE_LAST_ORDER,
        ROUND(AVG(NET_REVENUE), 2)                  AS AVG_ITEM_VALUE

    FROM sales
    GROUP BY CUSTOMER_SK
),

-- RFM Scoring
rfm AS (
    SELECT
        *,
        -- Recency: lower = better (recent buyer)
        NTILE(5) OVER (ORDER BY DAYS_SINCE_LAST_ORDER ASC)  AS RECENCY_SCORE,
        -- Frequency: higher = better
        NTILE(5) OVER (ORDER BY TOTAL_ORDERS DESC)           AS FREQUENCY_SCORE,
        -- Monetary: higher = better
        NTILE(5) OVER (ORDER BY TOTAL_REVENUE DESC)          AS MONETARY_SCORE

    FROM customer_agg
)

SELECT
    r.CUSTOMER_SK,
    c.CUSTOMER_ID,
    c.FULL_NAME,
    c.EMAIL,
    c.CITY,
    c.COUNTRY,
    c.REGION,
    c.AGE_GROUP,
    c.CUSTOMER_SEGMENT,

    -- CLV metrics
    r.TOTAL_ORDERS,
    r.TOTAL_ITEMS,
    ROUND(r.TOTAL_REVENUE, 2)           AS TOTAL_REVENUE,
    ROUND(r.TOTAL_PROFIT, 2)            AS TOTAL_PROFIT,
    r.FIRST_ORDER_DATE,
    r.LAST_ORDER_DATE,
    r.ACTIVE_DAYS,
    r.DAYS_SINCE_LAST_ORDER,
    r.AVG_ITEM_VALUE,

    -- RFM
    r.RECENCY_SCORE,
    r.FREQUENCY_SCORE,
    r.MONETARY_SCORE,
    (r.RECENCY_SCORE + r.FREQUENCY_SCORE + r.MONETARY_SCORE) AS RFM_TOTAL,

    -- Customer tier based on RFM
    CASE
        WHEN (r.RECENCY_SCORE + r.FREQUENCY_SCORE + r.MONETARY_SCORE) >= 13 THEN 'Champions'
        WHEN (r.RECENCY_SCORE + r.FREQUENCY_SCORE + r.MONETARY_SCORE) >= 10 THEN 'Loyal'
        WHEN (r.RECENCY_SCORE + r.FREQUENCY_SCORE + r.MONETARY_SCORE) >= 7  THEN 'Potential Loyal'
        WHEN r.RECENCY_SCORE >= 4 THEN 'Recent'
        WHEN r.FREQUENCY_SCORE >= 4 OR r.MONETARY_SCORE >= 4 THEN 'At Risk'
        ELSE 'Hibernating'
    END                                 AS CLV_TIER

FROM rfm r
JOIN {{ ref('dim_customer') }} c ON r.CUSTOMER_SK = c.CUSTOMER_SK
ORDER BY r.TOTAL_REVENUE DESC
