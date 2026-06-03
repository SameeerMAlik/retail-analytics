-- ============================================================
-- dbt Mart: dim_customer
-- Star Schema Dimension
-- ============================================================

{{ config(materialized='table', schema='analytics') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

-- Add surrogate key using ROW_NUMBER (deterministic ordering by customer_id)
final AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY CUSTOMER_ID)    AS CUSTOMER_SK,
        CUSTOMER_ID,
        FULL_NAME,
        GENDER,
        EMAIL,
        CITY,
        COUNTRY,
        REGISTRATION_DATE,
        REGISTRATION_YEAR,
        AGE_GROUP,
        TENURE_DAYS,

        -- Segmentation flags
        CASE WHEN TENURE_DAYS > 365 THEN 'Loyal'
             WHEN TENURE_DAYS > 90  THEN 'Regular'
             ELSE 'New'
        END                                         AS CUSTOMER_SEGMENT,

        -- Geographic region
        CASE COUNTRY
            WHEN 'United States'  THEN 'North America'
            WHEN 'Canada'         THEN 'North America'
            WHEN 'United Kingdom' THEN 'Europe'
            WHEN 'Germany'        THEN 'Europe'
            WHEN 'France'         THEN 'Europe'
            WHEN 'Australia'      THEN 'APAC'
            WHEN 'Japan'          THEN 'APAC'
            WHEN 'Singapore'      THEN 'APAC'
            WHEN 'India'          THEN 'APAC'
            WHEN 'UAE'            THEN 'Middle East'
            ELSE 'Other'
        END                                         AS REGION,

        CURRENT_TIMESTAMP()                         AS UPDATED_AT

    FROM stg
)

SELECT * FROM final
