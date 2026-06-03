# Architecture — Enterprise Retail Analytics Engine

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ENTERPRISE RETAIL ANALYTICS ENGINE                  │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│   DATA SOURCES   │    │  DATA INGESTION  │    │  CLOUD WAREHOUSE     │
│                  │    │                  │    │                      │
│  Faker Library   │───▶│  generate_data   │───▶│  Snowflake           │
│  (10K customers  │    │  .py             │    │  RETAIL_ANALYTICS_DB │
│   500 products   │    │                  │    │                      │
│   50K orders     │    │  load_to_        │    │  ┌──────────────┐   │
│   150K items)    │    │  snowflake.py    │    │  │   STAGING    │   │
│                  │    │                  │    │  │  schema      │   │
│  competitor_     │───▶│  scrape_         │    │  └──────┬───────┘   │
│  site.html       │    │  competitor.py   │    │         │            │
│  (BS4 scraper)   │    │                  │    │  ┌──────▼───────┐   │
└──────────────────┘    └──────────────────┘    │  │  ANALYTICS   │   │
                                                │  │  schema      │   │
                                                │  └──────┬───────┘   │
                                                └─────────┼────────────┘
                                                          │
                        ┌─────────────────────────────────▼────────────┐
                        │              dbt TRANSFORMATION LAYER         │
                        │                                               │
                        │  staging/          marts/        analytics/   │
                        │  stg_customers     dim_customer  daily_rev    │
                        │  stg_products  ──▶ dim_product ──top_cats     │
                        │  stg_orders        dim_date      cust_ltv     │
                        │  stg_order_items   fct_sales                  │
                        │                                               │
                        │  Tests: unique, not_null, relationships       │
                        └─────────────────────────────────┬────────────┘
                                                          │
                        ┌─────────────────────────────────▼────────────┐
                        │              FLASK ANALYTICS DASHBOARD        │
                        │                                               │
                        │  ┌──────────────┐    ┌──────────────────┐   │
                        │  │  Snowflake   │    │  Gemini AI API   │   │
                        │  │  Service     │    │  (NL → SQL)      │   │
                        │  │  (TTL cache) │    │                  │   │
                        │  └──────┬───────┘    └────────┬─────────┘   │
                        │         │                      │              │
                        │  ┌──────▼──────────────────────▼──────────┐  │
                        │  │           Flask Routes / Blueprints     │  │
                        │  │  /dashboard  /revenue  /products        │  │
                        │  │  /customers  /pivot    /ai-sql          │  │
                        │  └──────────────────────┬──────────────────┘  │
                        │                          │                     │
                        │  ┌───────────────────────▼──────────────────┐ │
                        │  │              Jinja2 Templates             │ │
                        │  │  Bootstrap 5 | Chart.js | PivotTable.js  │ │
                        │  │  DataTables | Dark Cyber Theme            │ │
                        │  └──────────────────────────────────────────┘ │
                        └──────────────────────────────────────────────┘
```

---

## Data Flow — Step by Step

### Phase 1: Data Acquisition
1. `generate_data.py` uses **Faker + NumPy** to create 4 interlinked CSVs with realistic distributions
2. `scrape_competitor.py` parses `competitor_site.html` with **BeautifulSoup4** → `competitor_prices.csv`

### Phase 2: Snowflake Ingestion
3. `load_to_snowflake.py` connects via `snowflake-connector-python`
4. Creates database, schemas, and staging tables using DDL from `staging_tables.sql`
5. Loads all 5 CSVs using `pandas.write_pandas()` (bulk insert)
6. Validates row counts and logs success/failure per table

### Phase 3: dbt Transformations
7. **Staging models** (`stg_*`): Clean column names, cast data types, deduplicate — materialised as **views** (always fresh, zero storage cost)
8. **Mart models** (`dim_*`, `fct_*`): Build the star schema with surrogate keys — materialised as **tables** (pre-computed for fast dashboard queries)
9. **Analytics models**: Pre-aggregate for specific dashboard cards — materialised as **tables**
10. **dbt test** validates data quality: unique keys, non-null constraints, referential integrity

### Phase 4: Flask Dashboard
11. `app.py` initialises Flask with 6 blueprints
12. Each page route calls `snowflake_service.query()` which checks an in-memory TTL cache before hitting Snowflake
13. JSON API endpoints return data to Chart.js and PivotTable.js via fetch()
14. **Demo mode** activates automatically if Snowflake credentials are absent

### Phase 5: AI SQL Feature
15. User enters natural language question in the UI
16. `gemini_service.py` constructs a system prompt containing the full star schema DDL context
17. Gemini API returns a SQL query
18. Security layer blocks any non-SELECT keywords
19. Query executes against Snowflake (or demo data) and results render in the UI

---

## Technology Choices — Rationale

| Technology | Chosen For | Alternative Considered |
|---|---|---|
| **Snowflake** | Serverless, auto-scaling, columnar storage, SQL-native | Redshift, BigQuery |
| **dbt Core** | SQL-first transformations, version control, built-in tests | Spark, custom SQL scripts |
| **Flask** | Lightweight, Python-native, easy to extend | Django (heavier), FastAPI |
| **Gemini API** | Free tier available, strong SQL generation | OpenAI GPT-4, Claude |
| **PivotTable.js** | Zero-dependency drag-drop pivot in browser | Ag-Grid, Pivot Excel |
| **Chart.js** | Lightweight, no backend required, responsive | D3.js (complex), Plotly |

---

## Security Considerations

- All credentials stored in `.env` — never committed to git
- SQL injection protection: parameterised queries + SELECT-only validation
- Gemini-generated SQL blocked if it contains: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `CREATE`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `EXECUTE`, `EXEC`
- Rate limiting on AI SQL endpoint (Gemini API quota)
- No raw user input passed directly to Snowflake — always sanitised through service layer

---

## Scalability Notes

- Snowflake's **virtual warehouse** can scale up/down independently of storage
- dbt models are **incremental-ready** — can be converted from `table` to `incremental` materialisation for large datasets
- Flask service layer uses **in-memory TTL cache** (300s default) to reduce Snowflake query costs
- For production: replace Flask dev server with **Gunicorn** behind Nginx
