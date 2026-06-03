# Entity Relationship Diagram — Enterprise Retail Analytics Engine

## Star Schema Overview

The data warehouse follows a **classic star schema** — one central fact table surrounded by denormalized dimension tables. This design optimises for analytical read performance (OLAP) over transactional write performance (OLTP).

---

## Mermaid ERD

```mermaid
erDiagram

    %% ── Staging Tables (Raw Layer) ──────────────────────────────
    STG_CUSTOMERS {
        VARCHAR CUSTOMER_ID PK
        VARCHAR FULL_NAME
        VARCHAR GENDER
        VARCHAR EMAIL
        VARCHAR CITY
        VARCHAR COUNTRY
        DATE    REGISTRATION_DATE
        VARCHAR AGE_GROUP
    }

    STG_PRODUCTS {
        VARCHAR PRODUCT_ID PK
        VARCHAR CATEGORY
        VARCHAR SUBCATEGORY
        VARCHAR PRODUCT_NAME
        NUMBER  RETAIL_PRICE
        NUMBER  BASE_COST
        VARCHAR SUPPLIER_NAME
    }

    STG_ORDERS {
        VARCHAR ORDER_ID PK
        VARCHAR CUSTOMER_ID FK
        DATE    ORDER_DATE
        VARCHAR PAYMENT_METHOD
        VARCHAR ORDER_STATUS
    }

    STG_ORDER_ITEMS {
        VARCHAR ORDER_ITEM_ID PK
        VARCHAR ORDER_ID FK
        VARCHAR PRODUCT_ID FK
        NUMBER  QUANTITY
        NUMBER  UNIT_PRICE
        NUMBER  DISCOUNT
    }

    STG_COMPETITOR_PRICES {
        VARCHAR PRODUCT_NAME
        NUMBER  COMPETITOR_PRICE
        VARCHAR CATEGORY
        VARCHAR STOCK_STATUS
    }

    %% ── Dimension Tables (Analytics Layer) ─────────────────────
    DIM_CUSTOMER {
        VARCHAR CUSTOMER_SK PK
        VARCHAR CUSTOMER_ID
        VARCHAR FULL_NAME
        VARCHAR GENDER
        VARCHAR EMAIL
        VARCHAR CITY
        VARCHAR COUNTRY
        VARCHAR AGE_GROUP
        DATE    REGISTRATION_DATE
    }

    DIM_PRODUCT {
        VARCHAR PRODUCT_SK PK
        VARCHAR PRODUCT_ID
        VARCHAR CATEGORY
        VARCHAR SUBCATEGORY
        VARCHAR PRODUCT_NAME
        NUMBER  RETAIL_PRICE
        NUMBER  BASE_COST
        NUMBER  GROSS_MARGIN_PCT
        VARCHAR PRICE_TIER
        NUMBER  COMPETITOR_PRICE
        VARCHAR PRICE_VS_COMPETITOR
        VARCHAR SUPPLIER_NAME
    }

    DIM_DATE {
        NUMBER  DATE_SK PK
        DATE    DATE_ACTUAL
        NUMBER  YEAR
        NUMBER  QUARTER_OF_YEAR
        NUMBER  MONTH_OF_YEAR
        VARCHAR MONTH_NAME
        NUMBER  DAY_OF_MONTH
        VARCHAR DAY_NAME
        BOOLEAN IS_WEEKEND
        BOOLEAN IS_WEEKDAY
        VARCHAR YEAR_MONTH
        VARCHAR QUARTER_LABEL
    }

    %% ── Fact Table (Central Grain) ──────────────────────────────
    FCT_SALES {
        VARCHAR SALE_SK PK
        VARCHAR CUSTOMER_SK FK
        VARCHAR PRODUCT_SK FK
        NUMBER  DATE_SK FK
        VARCHAR ORDER_ID
        VARCHAR ORDER_ITEM_ID
        VARCHAR PAYMENT_METHOD
        VARCHAR ORDER_STATUS
        NUMBER  QUANTITY
        NUMBER  UNIT_PRICE
        NUMBER  DISCOUNT_AMOUNT
        NUMBER  GROSS_REVENUE
        NUMBER  NET_REVENUE
        NUMBER  COGS
        NUMBER  GROSS_PROFIT
        NUMBER  MARGIN_PCT
        NUMBER  COMPETITOR_PRICE
        NUMBER  COMPETITOR_PRICE_DELTA
    }

    %% ── Relationships ────────────────────────────────────────────
    STG_ORDERS      ||--o{ STG_ORDER_ITEMS  : "contains"
    STG_CUSTOMERS   ||--o{ STG_ORDERS       : "places"
    STG_PRODUCTS    ||--o{ STG_ORDER_ITEMS  : "included_in"

    DIM_CUSTOMER    ||--o{ FCT_SALES        : "purchases"
    DIM_PRODUCT     ||--o{ FCT_SALES        : "sold_via"
    DIM_DATE        ||--o{ FCT_SALES        : "on_date"
```

---

## Relationship Explanations

| Relationship | Cardinality | Description |
|---|---|---|
| `DIM_CUSTOMER → FCT_SALES` | 1 : Many | One customer can have many sales transactions |
| `DIM_PRODUCT → FCT_SALES` | 1 : Many | One product can appear in many order items |
| `DIM_DATE → FCT_SALES` | 1 : Many | One date can have many transactions |
| `STG_CUSTOMERS → STG_ORDERS` | 1 : Many | One customer places many orders |
| `STG_ORDERS → STG_ORDER_ITEMS` | 1 : Many | One order contains many line items |
| `STG_PRODUCTS → STG_ORDER_ITEMS` | 1 : Many | One product appears in many order items |

---

## Key Design Decisions

### Primary Keys
- **Surrogate Keys** (SK): Used in dimension and fact tables. Generated via `dbt_utils.generate_surrogate_key()` — hash of natural key columns. This decouples the warehouse from source system IDs.
- **Natural Keys** (ID): Original source system identifiers preserved alongside surrogate keys.

### Foreign Keys
- All FK relationships in `FCT_SALES` reference dimension surrogate keys.
- This enables `JOIN` operations without needing source system knowledge.

### Why Star Schema?
1. **Query Performance**: Fewer JOINs than 3NF (normalised) models
2. **BI Tool Compatibility**: Tools like Tableau, Power BI, Metabase expect star schemas
3. **Understandability**: Business users can navigate the model intuitively
4. **Snowflake Optimised**: Columnar storage benefits from wide dimension tables

### Grain
- **FCT_SALES grain**: One row per **order line item** (not per order)
- This allows product-level analysis (margin per product, discount per item)

---

## Competitor Price Integration

The `COMPETITOR_PRICE` and `COMPETITOR_PRICE_DELTA` columns in `FCT_SALES` and `DIM_PRODUCT` come from the web-scraped `STG_COMPETITOR_PRICES` table, joined on product name fuzzy matching during the `DIM_PRODUCT` transformation. This enables price competitiveness analysis directly in the fact table.
