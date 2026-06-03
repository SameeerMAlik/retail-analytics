-- ============================================================
-- dbt Staging Model: stg_products
-- Source: STAGING.STG_PRODUCTS
-- ============================================================

{{ config(materialized='view', schema='staging') }}

WITH source AS (
    SELECT * FROM {{ source('staging', 'STG_PRODUCTS') }}
),

cleaned AS (
    SELECT
        PRODUCT_ID,
        TRIM(CATEGORY)                      AS CATEGORY,
        TRIM(SUBCATEGORY)                   AS SUBCATEGORY,
        TRIM(PRODUCT_NAME)                  AS PRODUCT_NAME,
        RETAIL_PRICE::FLOAT                 AS RETAIL_PRICE,
        BASE_COST::FLOAT                    AS BASE_COST,
        TRIM(SUPPLIER_NAME)                 AS SUPPLIER_NAME,

        -- Derived: Gross margin percentage
        CASE
            WHEN RETAIL_PRICE > 0
            THEN ROUND((RETAIL_PRICE - BASE_COST) / RETAIL_PRICE * 100, 2)
            ELSE 0
        END                                 AS GROSS_MARGIN_PCT,

        -- Derived: Price tier for segmentation
        CASE
            WHEN RETAIL_PRICE < 50   THEN 'Budget'
            WHEN RETAIL_PRICE < 200  THEN 'Mid-range'
            WHEN RETAIL_PRICE < 500  THEN 'Premium'
            ELSE 'Luxury'
        END                                 AS PRICE_TIER,

        _LOADED_AT

    FROM source
    WHERE PRODUCT_ID IS NOT NULL
      AND RETAIL_PRICE > 0
      AND BASE_COST > 0
)

SELECT * FROM cleaned
