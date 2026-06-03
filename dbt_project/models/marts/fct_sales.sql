-- ============================================================
-- dbt Mart: fct_sales
-- Central Fact Table — grain: one order line item
-- Star Schema Measures + Foreign Keys to all dimensions
-- ============================================================

{{ config(
    materialized='table',
    schema='analytics',
    cluster_by=['ORDER_DATE_SK', 'PRODUCT_SK']
) }}

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

dim_customer AS (
    SELECT CUSTOMER_SK, CUSTOMER_ID FROM {{ ref('dim_customer') }}
),

dim_product AS (
    SELECT
        PRODUCT_SK,
        PRODUCT_ID,
        BASE_COST,
        AVG_COMPETITOR_PRICE
    FROM {{ ref('dim_product') }}
),

-- Join everything together
sales_base AS (
    SELECT
        oi.ORDER_ITEM_ID,
        oi.ORDER_ID,
        o.ORDER_DATE,
        o.CUSTOMER_ID,
        oi.PRODUCT_ID,
        o.PAYMENT_METHOD,
        o.ORDER_STATUS,
        o.IS_REVENUE_ORDER,

        -- Measures from order items
        oi.QUANTITY,
        oi.UNIT_PRICE,
        oi.DISCOUNT,
        oi.GROSS_REVENUE,
        oi.NET_REVENUE,

        -- Compute COGS and profit using product cost
        ROUND(oi.QUANTITY * p.BASE_COST, 2)                 AS COGS,
        ROUND(oi.NET_REVENUE - (oi.QUANTITY * p.BASE_COST), 2) AS GROSS_PROFIT,

        -- Margin %
        CASE
            WHEN oi.NET_REVENUE > 0
            THEN ROUND((oi.NET_REVENUE - (oi.QUANTITY * p.BASE_COST)) / oi.NET_REVENUE * 100, 2)
            ELSE 0
        END                                                     AS MARGIN_PCT,

        -- Competitor price delta
        p.AVG_COMPETITOR_PRICE                                  AS COMPETITOR_PRICE,
        CASE
            WHEN p.AVG_COMPETITOR_PRICE IS NOT NULL
            THEN ROUND(oi.UNIT_PRICE - p.AVG_COMPETITOR_PRICE, 2)
            ELSE NULL
        END                                                     AS PRICE_DELTA,

        -- Surrogate keys for dimensions
        dc.CUSTOMER_SK,
        p.PRODUCT_SK

    FROM order_items oi
    JOIN orders o ON oi.ORDER_ID = o.ORDER_ID
    JOIN dim_customer dc ON o.CUSTOMER_ID = dc.CUSTOMER_ID
    JOIN dim_product p ON oi.PRODUCT_ID = p.PRODUCT_ID
),

-- Add date surrogate key: YYYYMMDD integer
final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['ORDER_ITEM_ID']) }} AS SALE_SK,
        ORDER_ITEM_ID,
        ORDER_ID,
        TO_NUMBER(TO_CHAR(ORDER_DATE, 'YYYYMMDD'))  AS ORDER_DATE_SK,
        ORDER_DATE,
        CUSTOMER_SK,
        PRODUCT_SK,
        PAYMENT_METHOD,
        ORDER_STATUS,
        IS_REVENUE_ORDER,
        QUANTITY,
        UNIT_PRICE,
        DISCOUNT,
        GROSS_REVENUE,
        NET_REVENUE,
        COGS,
        GROSS_PROFIT,
        MARGIN_PCT,
        COMPETITOR_PRICE,
        PRICE_DELTA,
        CURRENT_TIMESTAMP()                         AS LOADED_AT

    FROM sales_base
)

SELECT * FROM final
