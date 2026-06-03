/*
  dim_date.sql — Date Dimension Table
  ────────────────────────────────────
  Generates a complete date spine for the star schema.
  Covers the full 2-year order date range (2023-01-01 → 2024-12-31).

  Materialization: table  (rarely changes, queried often)
  Grain:           one row per calendar day
*/

{{ config(materialized='table', schema='ANALYTICS') }}

WITH date_spine AS (

    -- Generate one row per day using Snowflake's GENERATOR function
    SELECT
        DATEADD(day, seq4(), '2023-01-01'::DATE) AS date_actual
    FROM TABLE(GENERATOR(rowcount => 730))  -- 2 years = 730 days

)

SELECT
    -- Surrogate key: integer in YYYYMMDD format
    TO_NUMBER(TO_CHAR(date_actual, 'YYYYMMDD'))     AS date_sk,

    -- Full date
    date_actual                                      AS date_actual,

    -- Calendar attributes
    YEAR(date_actual)                                AS year,
    QUARTER(date_actual)                             AS quarter_of_year,
    MONTH(date_actual)                               AS month_of_year,
    MONTHNAME(date_actual)                           AS month_name,
    DAY(date_actual)                                 AS day_of_month,
    DAYOFWEEK(date_actual)                           AS day_of_week,
    DAYNAME(date_actual)                             AS day_name,
    DAYOFYEAR(date_actual)                           AS day_of_year,
    WEEKOFYEAR(date_actual)                          AS week_of_year,

    -- Formatted labels
    'Q' || QUARTER(date_actual)                      AS quarter_label,
    TO_CHAR(date_actual, 'Mon YYYY')                AS month_year_label,
    TO_CHAR(date_actual, 'YYYY-MM')                 AS year_month,

    -- Boolean flags
    CASE WHEN DAYOFWEEK(date_actual) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend,
    CASE WHEN DAYOFWEEK(date_actual) NOT IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekday,

    -- Fiscal year (assume Jan fiscal start)
    YEAR(date_actual)                                AS fiscal_year,
    QUARTER(date_actual)                             AS fiscal_quarter,

    -- Relative markers (useful for trend analysis)
    CASE
        WHEN date_actual = CURRENT_DATE()                    THEN 'Today'
        WHEN date_actual = CURRENT_DATE() - 1               THEN 'Yesterday'
        WHEN date_actual >= DATE_TRUNC('week', CURRENT_DATE()) THEN 'This Week'
        WHEN date_actual >= DATE_TRUNC('month', CURRENT_DATE()) THEN 'This Month'
        ELSE 'Prior'
    END AS relative_period

FROM date_spine
ORDER BY date_actual
