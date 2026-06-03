-- ============================================================
-- dbt Staging Model: stg_customers
-- Source: STAGING.STG_CUSTOMERS
-- Materialization: View (always fresh)
-- Purpose: Clean & standardize raw customer data
-- ============================================================

{{ config(materialized='view', schema='staging') }}

WITH source AS (
    -- Pull directly from Snowflake staging table
    SELECT * FROM {{ source('staging', 'STG_CUSTOMERS') }}
),

cleaned AS (
    SELECT
        -- Primary Key
        CUSTOMER_ID,

        -- Clean text fields: trim whitespace, standardize case
        TRIM(FULL_NAME)                         AS FULL_NAME,
        UPPER(TRIM(GENDER))                     AS GENDER,
        LOWER(TRIM(EMAIL))                      AS EMAIL,
        TRIM(CITY)                              AS CITY,
        TRIM(COUNTRY)                           AS COUNTRY,

        -- Date fields
        REGISTRATION_DATE::DATE                 AS REGISTRATION_DATE,
        YEAR(REGISTRATION_DATE::DATE)           AS REGISTRATION_YEAR,

        -- Age group standardization
        TRIM(AGE_GROUP)                         AS AGE_GROUP,

        -- Derived: Customer tenure days (as of 2024-12-31)
        DATEDIFF('day', REGISTRATION_DATE::DATE, '2024-12-31'::DATE) AS TENURE_DAYS,

        -- Load metadata
        _LOADED_AT

    FROM source

    -- Basic data quality filter: must have valid ID and email
    WHERE CUSTOMER_ID IS NOT NULL
      AND EMAIL IS NOT NULL
      AND REGISTRATION_DATE IS NOT NULL
)

SELECT * FROM cleaned
