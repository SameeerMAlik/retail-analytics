-- ============================================================
-- dbt Analytics: daily_revenue_trends
-- Aggregated daily and monthly revenue for dashboard charts
-- ============================================================

{{ config(materialized='table', schema='analytics') }}

WITH sales AS (
    SELECT * FROM {{ ref('fct_sales') }}
    WHERE IS_REVENUE_ORDER = TRUE
),

daily AS (
    SELECT
        ORDER_DATE,
        YEAR(ORDER_DATE)                                AS YEAR,
        MONTH(ORDER_DATE)                               AS MONTH,
        MONTHNAME(ORDER_DATE)                           AS MONTH_NAME,
        QUARTER(ORDER_DATE)                             AS QUARTER,
        DAYOFWEEK(ORDER_DATE)                           AS DOW,

        -- Revenue metrics
        COUNT(DISTINCT ORDER_ID)                        AS NUM_ORDERS,
        COUNT(ORDER_ITEM_ID)                            AS NUM_ITEMS,
        SUM(NET_REVENUE)                                AS NET_REVENUE,
        SUM(GROSS_REVENUE)                              AS GROSS_REVENUE,
        SUM(GROSS_PROFIT)                               AS GROSS_PROFIT,
        SUM(COGS)                                       AS TOTAL_COGS,

        -- Averages
        ROUND(AVG(NET_REVENUE), 2)                      AS AVG_ORDER_ITEM_VALUE,
        ROUND(SUM(GROSS_PROFIT) / NULLIF(SUM(NET_REVENUE), 0) * 100, 2) AS MARGIN_PCT,

        -- Running totals (window functions)
        SUM(SUM(NET_REVENUE)) OVER (
            PARTITION BY YEAR(ORDER_DATE)
            ORDER BY ORDER_DATE
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )                                               AS YTD_REVENUE

    FROM sales
    GROUP BY ORDER_DATE
),

-- Monthly rollup
monthly AS (
    SELECT
        YEAR,
        MONTH,
        MONTH_NAME,
        QUARTER,
        SUM(NET_REVENUE)                                AS MONTHLY_REVENUE,
        SUM(GROSS_PROFIT)                               AS MONTHLY_PROFIT,
        SUM(NUM_ORDERS)                                 AS MONTHLY_ORDERS,
        ROUND(AVG(MARGIN_PCT), 2)                       AS AVG_MARGIN_PCT,

        -- Month-over-month growth
        LAG(SUM(NET_REVENUE)) OVER (ORDER BY YEAR, MONTH) AS PREV_MONTH_REVENUE,
        ROUND(
            (SUM(NET_REVENUE) - LAG(SUM(NET_REVENUE)) OVER (ORDER BY YEAR, MONTH))
            / NULLIF(LAG(SUM(NET_REVENUE)) OVER (ORDER BY YEAR, MONTH), 0) * 100,
            2
        )                                               AS MOM_GROWTH_PCT

    FROM daily
    GROUP BY YEAR, MONTH, MONTH_NAME, QUARTER
)

SELECT
    d.ORDER_DATE,
    d.YEAR,
    d.MONTH,
    d.MONTH_NAME,
    d.QUARTER,
    d.NUM_ORDERS,
    d.NUM_ITEMS,
    ROUND(d.NET_REVENUE, 2)         AS NET_REVENUE,
    ROUND(d.GROSS_REVENUE, 2)       AS GROSS_REVENUE,
    ROUND(d.GROSS_PROFIT, 2)        AS GROSS_PROFIT,
    d.MARGIN_PCT,
    ROUND(d.YTD_REVENUE, 2)         AS YTD_REVENUE,
    m.MONTHLY_REVENUE,
    m.MONTHLY_ORDERS,
    m.MOM_GROWTH_PCT

FROM daily d
JOIN monthly m ON d.YEAR = m.YEAR AND d.MONTH = m.MONTH
ORDER BY d.ORDER_DATE
