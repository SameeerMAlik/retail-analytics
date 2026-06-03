-- ============================================================
-- dbt Staging Model: stg_orders
-- Source: STAGING.STG_ORDERS
-- ============================================================

{{ config(materialized='view', schema='staging') }}

WITH source AS (
    SELECT * FROM {{ source('staging', 'STG_ORDERS') }}
),

cleaned AS (
    SELECT
        ORDER_ID,
        CUSTOMER_ID,
        ORDER_DATE::DATE                    AS ORDER_DATE,
        TRIM(PAYMENT_METHOD)                AS PAYMENT_METHOD,
        TRIM(ORDER_STATUS)                  AS ORDER_STATUS,

        -- Derived: is this order revenue-generating?
        CASE
            WHEN ORDER_STATUS IN ('Completed', 'Shipped') THEN TRUE
            ELSE FALSE
        END                                 AS IS_REVENUE_ORDER,

        -- Derived: date parts for partitioning
        YEAR(ORDER_DATE::DATE)              AS ORDER_YEAR,
        MONTH(ORDER_DATE::DATE)             AS ORDER_MONTH,
        QUARTER(ORDER_DATE::DATE)           AS ORDER_QUARTER,

        _LOADED_AT

    FROM source
    WHERE ORDER_ID IS NOT NULL
      AND CUSTOMER_ID IS NOT NULL
      AND ORDER_DATE IS NOT NULL
)

SELECT * FROM cleaned
