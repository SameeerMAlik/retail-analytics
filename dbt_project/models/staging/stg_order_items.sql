-- ============================================================
-- dbt Staging Model: stg_order_items
-- Source: STAGING.STG_ORDER_ITEMS
-- ============================================================

{{ config(materialized='view', schema='staging') }}

WITH source AS (
    SELECT * FROM {{ source('staging', 'STG_ORDER_ITEMS') }}
),

cleaned AS (
    SELECT
        ORDER_ITEM_ID,
        ORDER_ID,
        PRODUCT_ID,
        QUANTITY::INTEGER                   AS QUANTITY,
        UNIT_PRICE::FLOAT                   AS UNIT_PRICE,

        -- Clamp discount to valid range [0, 1]
        GREATEST(0, LEAST(1, COALESCE(DISCOUNT::FLOAT, 0))) AS DISCOUNT,

        -- Derived revenue metrics
        ROUND(QUANTITY * UNIT_PRICE, 2)     AS GROSS_REVENUE,
        ROUND(QUANTITY * UNIT_PRICE * (1 - COALESCE(DISCOUNT, 0)), 2) AS NET_REVENUE,

        _LOADED_AT

    FROM source
    WHERE ORDER_ITEM_ID IS NOT NULL
      AND ORDER_ID IS NOT NULL
      AND PRODUCT_ID IS NOT NULL
      AND QUANTITY > 0
      AND UNIT_PRICE > 0
)

SELECT * FROM cleaned
