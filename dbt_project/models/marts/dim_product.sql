-- ============================================================
-- dbt Mart: dim_product
-- Star Schema Dimension
-- ============================================================

{{ config(materialized='table', schema='analytics') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_products') }}
),

-- Optional: join competitor prices for price intelligence
comp AS (
    SELECT
        UPPER(TRIM(PRODUCT_NAME))   AS COMP_PRODUCT_NAME,
        AVG(COMPETITOR_PRICE)       AS AVG_COMPETITOR_PRICE
    FROM {{ source('staging', 'STG_COMPETITOR_PRICES') }}
    GROUP BY 1
),

final AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY s.PRODUCT_ID)   AS PRODUCT_SK,
        s.PRODUCT_ID,
        s.CATEGORY,
        s.SUBCATEGORY,
        s.PRODUCT_NAME,
        s.RETAIL_PRICE,
        s.BASE_COST,
        s.GROSS_MARGIN_PCT,
        s.SUPPLIER_NAME,
        s.PRICE_TIER,

        -- Competitor intelligence
        c.AVG_COMPETITOR_PRICE,
        CASE
            WHEN c.AVG_COMPETITOR_PRICE IS NOT NULL
            THEN ROUND(s.RETAIL_PRICE - c.AVG_COMPETITOR_PRICE, 2)
            ELSE NULL
        END                                         AS PRICE_VS_COMPETITOR,

        CURRENT_TIMESTAMP()                         AS UPDATED_AT

    FROM stg s
    LEFT JOIN comp c
        ON UPPER(TRIM(s.PRODUCT_NAME)) = c.COMP_PRODUCT_NAME
)

SELECT * FROM final
