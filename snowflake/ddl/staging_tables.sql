-- ============================================================
-- Enterprise Retail Analytics Engine
-- Snowflake DDL — Staging Schema
-- ============================================================
-- Run this FIRST to set up all staging tables in Snowflake.
-- Execute using: snowsql -f staging_tables.sql
-- ============================================================

-- 1. Create Database & Schemas
-- ============================================================
CREATE DATABASE IF NOT EXISTS RETAIL_ANALYTICS_DB
    DATA_RETENTION_TIME_IN_DAYS = 7
    COMMENT = 'Enterprise Retail Analytics — Capstone Project';

USE DATABASE RETAIL_ANALYTICS_DB;

CREATE SCHEMA IF NOT EXISTS STAGING
    DATA_RETENTION_TIME_IN_DAYS = 1
    COMMENT = 'Raw staging layer — source data as-is';

CREATE SCHEMA IF NOT EXISTS ANALYTICS
    DATA_RETENTION_TIME_IN_DAYS = 7
    COMMENT = 'Analytics layer — star schema and aggregates';

CREATE SCHEMA IF NOT EXISTS DBT_DEV
    DATA_RETENTION_TIME_IN_DAYS = 7
    COMMENT = 'dbt development target schema';

-- ============================================================
-- 2. Staging Tables — CUSTOMERS
-- ============================================================
USE SCHEMA STAGING;

CREATE OR REPLACE TABLE STG_CUSTOMERS (
    CUSTOMER_ID         VARCHAR(20)     NOT NULL COMMENT 'Primary key — format: CUST000001',
    FULL_NAME           VARCHAR(200)    NOT NULL COMMENT 'Full display name',
    GENDER              VARCHAR(20)     COMMENT 'Male / Female / Non-binary',
    EMAIL               VARCHAR(255)    NOT NULL COMMENT 'Customer email address',
    CITY                VARCHAR(100)    COMMENT 'City of residence',
    COUNTRY             VARCHAR(100)    COMMENT 'Country of residence',
    REGISTRATION_DATE   DATE            COMMENT 'Date customer registered',
    AGE_GROUP           VARCHAR(20)     COMMENT 'Age bracket: 18-24, 25-34, etc.',
    _LOADED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP() COMMENT 'ETL load timestamp'
)
COMMENT = 'Staging: raw customer records from data generation'
;

-- ============================================================
-- 3. Staging Tables — PRODUCTS
-- ============================================================
CREATE OR REPLACE TABLE STG_PRODUCTS (
    PRODUCT_ID          VARCHAR(20)     NOT NULL COMMENT 'Primary key — format: PROD00001',
    CATEGORY            VARCHAR(100)    NOT NULL COMMENT 'Top-level product category',
    SUBCATEGORY         VARCHAR(100)    COMMENT 'Sub-level grouping',
    PRODUCT_NAME        VARCHAR(300)    NOT NULL COMMENT 'Full product display name',
    RETAIL_PRICE        NUMBER(10,2)    NOT NULL COMMENT 'Listed retail price (USD)',
    BASE_COST           NUMBER(10,2)    NOT NULL COMMENT 'Internal cost / COGS',
    SUPPLIER_NAME       VARCHAR(200)    COMMENT 'Primary supplier name',
    _LOADED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Staging: raw product catalog'
;

-- ============================================================
-- 4. Staging Tables — ORDERS
-- ============================================================
CREATE OR REPLACE TABLE STG_ORDERS (
    ORDER_ID            VARCHAR(20)     NOT NULL COMMENT 'Primary key — format: ORD00000001',
    CUSTOMER_ID         VARCHAR(20)     NOT NULL COMMENT 'FK → STG_CUSTOMERS.CUSTOMER_ID',
    ORDER_DATE          DATE            NOT NULL COMMENT 'Date order was placed',
    PAYMENT_METHOD      VARCHAR(50)     COMMENT 'Payment channel used',
    ORDER_STATUS        VARCHAR(30)     COMMENT 'Completed / Shipped / Processing / Cancelled / Returned',
    _LOADED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Staging: raw orders header table'
;

-- ============================================================
-- 5. Staging Tables — ORDER ITEMS
-- ============================================================
CREATE OR REPLACE TABLE STG_ORDER_ITEMS (
    ORDER_ITEM_ID       VARCHAR(25)     NOT NULL COMMENT 'Primary key — format: ITEM000000001',
    ORDER_ID            VARCHAR(20)     NOT NULL COMMENT 'FK → STG_ORDERS.ORDER_ID',
    PRODUCT_ID          VARCHAR(20)     NOT NULL COMMENT 'FK → STG_PRODUCTS.PRODUCT_ID',
    QUANTITY            NUMBER(5,0)     NOT NULL COMMENT 'Units ordered',
    UNIT_PRICE          NUMBER(10,2)    NOT NULL COMMENT 'Price per unit at time of order',
    DISCOUNT            NUMBER(5,4)     COMMENT 'Discount fraction (e.g. 0.10 = 10%)',
    _LOADED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Staging: raw order line items'
;

-- ============================================================
-- 6. Staging Tables — COMPETITOR PRICES
-- ============================================================
CREATE OR REPLACE TABLE STG_COMPETITOR_PRICES (
    PRODUCT_NAME        VARCHAR(300)    NOT NULL COMMENT 'Competitor product name (matched to our catalog)',
    CATEGORY            VARCHAR(100)    COMMENT 'Competitor category label',
    SECTION             VARCHAR(100)    COMMENT 'Page section scraped from',
    COMPETITOR_PRICE    NUMBER(10,2)    COMMENT 'Listed competitor price (USD)',
    STOCK_STATUS        VARCHAR(50)     COMMENT 'In Stock / Limited / Out of Stock',
    SCRAPED_AT          TIMESTAMP_NTZ   COMMENT 'Timestamp when data was scraped',
    SOURCE              VARCHAR(100)    COMMENT 'Competitor source identifier',
    _LOADED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Staging: competitor price intelligence data'
;

-- ============================================================
-- 7. File Formats for CSV Loading
-- ============================================================
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null', '', 'NA')
    EMPTY_FIELD_AS_NULL = TRUE
    DATE_FORMAT = 'YYYY-MM-DD'
    TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
    COMMENT = 'Standard CSV format for data loading'
;

-- ============================================================
-- 8. Internal Stage for CSV Files
-- ============================================================
CREATE OR REPLACE STAGE RETAIL_STAGE
    FILE_FORMAT = CSV_FORMAT
    COMMENT = 'Internal stage for uploading CSV data files'
;

-- ============================================================
-- 9. ANALYTICS Schema — Star Schema Tables
--    (populated by dbt transformations)
-- ============================================================
USE SCHEMA ANALYTICS;

-- Dimension: Customer
CREATE OR REPLACE TABLE DIM_CUSTOMER (
    CUSTOMER_SK         NUMBER AUTOINCREMENT PRIMARY KEY COMMENT 'Surrogate key',
    CUSTOMER_ID         VARCHAR(20)     NOT NULL COMMENT 'Natural key',
    FULL_NAME           VARCHAR(200),
    GENDER              VARCHAR(20),
    EMAIL               VARCHAR(255),
    CITY                VARCHAR(100),
    COUNTRY             VARCHAR(100),
    REGISTRATION_DATE   DATE,
    AGE_GROUP           VARCHAR(20),
    CUSTOMER_SINCE_YEAR NUMBER(4)       COMMENT 'Year of registration for cohort analysis',
    UPDATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Dimension: Customer attributes for star schema'
;

-- Dimension: Product
CREATE OR REPLACE TABLE DIM_PRODUCT (
    PRODUCT_SK          NUMBER AUTOINCREMENT PRIMARY KEY COMMENT 'Surrogate key',
    PRODUCT_ID          VARCHAR(20)     NOT NULL COMMENT 'Natural key',
    CATEGORY            VARCHAR(100),
    SUBCATEGORY         VARCHAR(100),
    PRODUCT_NAME        VARCHAR(300),
    RETAIL_PRICE        NUMBER(10,2),
    BASE_COST           NUMBER(10,2),
    GROSS_MARGIN_PCT    NUMBER(5,2)     COMMENT 'Pre-computed: (retail_price - base_cost)/retail_price * 100',
    SUPPLIER_NAME       VARCHAR(200),
    PRICE_TIER          VARCHAR(20)     COMMENT 'Budget / Mid-range / Premium / Luxury',
    UPDATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Dimension: Product catalog for star schema'
;

-- Dimension: Date
CREATE OR REPLACE TABLE DIM_DATE (
    DATE_SK             NUMBER          PRIMARY KEY COMMENT 'Surrogate key: YYYYMMDD',
    FULL_DATE           DATE            NOT NULL COMMENT 'Calendar date',
    YEAR                NUMBER(4),
    QUARTER             NUMBER(1),
    MONTH               NUMBER(2),
    MONTH_NAME          VARCHAR(20),
    WEEK                NUMBER(2),
    DAY_OF_WEEK         NUMBER(1)       COMMENT '1=Monday, 7=Sunday',
    DAY_NAME            VARCHAR(20),
    IS_WEEKEND          BOOLEAN,
    IS_HOLIDAY          BOOLEAN         DEFAULT FALSE,
    SEASON              VARCHAR(20)     COMMENT 'Winter / Spring / Summer / Fall',
    FISCAL_QUARTER      VARCHAR(10)     COMMENT 'Q1 2024, Q2 2024, etc.'
)
COMMENT = 'Date dimension spanning 2022-01-01 to 2025-12-31'
;

-- Fact: Sales
CREATE OR REPLACE TABLE FCT_SALES (
    SALE_SK             NUMBER AUTOINCREMENT PRIMARY KEY,
    ORDER_ITEM_ID       VARCHAR(25)     NOT NULL,
    ORDER_ID            VARCHAR(20)     NOT NULL,
    ORDER_DATE_SK       NUMBER          COMMENT 'FK → DIM_DATE.DATE_SK',
    CUSTOMER_SK         NUMBER          COMMENT 'FK → DIM_CUSTOMER.CUSTOMER_SK',
    PRODUCT_SK          NUMBER          COMMENT 'FK → DIM_PRODUCT.PRODUCT_SK',
    -- Measures
    QUANTITY            NUMBER(5,0),
    UNIT_PRICE          NUMBER(10,2),
    DISCOUNT            NUMBER(5,4),
    GROSS_REVENUE       NUMBER(12,2)    COMMENT 'quantity * unit_price',
    NET_REVENUE         NUMBER(12,2)    COMMENT 'gross_revenue * (1 - discount)',
    COGS                NUMBER(12,2)    COMMENT 'quantity * base_cost',
    GROSS_PROFIT        NUMBER(12,2)    COMMENT 'net_revenue - cogs',
    MARGIN_PCT          NUMBER(5,2)     COMMENT 'gross_profit / net_revenue * 100',
    COMPETITOR_PRICE    NUMBER(10,2)    COMMENT 'Matched competitor price (if available)',
    PRICE_DELTA         NUMBER(10,2)    COMMENT 'unit_price - competitor_price',
    ORDER_STATUS        VARCHAR(30),
    PAYMENT_METHOD      VARCHAR(50),
    LOADED_AT           TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Fact table: grain = one order line item'
;

-- ============================================================
-- Verification
-- ============================================================
SHOW TABLES IN SCHEMA STAGING;
SHOW TABLES IN SCHEMA ANALYTICS;
