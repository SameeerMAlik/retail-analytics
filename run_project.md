# Run Project Guide — Enterprise Retail Analytics Engine

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| pip | latest | `pip --version` |
| Git | any | `git --version` |
| Snowflake account | free trial OK | [Sign up](https://signup.snowflake.com/) |
| Gemini API key | free | [Get key](https://aistudio.google.com/app/apikey) |

> 💡 **No Snowflake?** The app runs in full **demo mode** without any credentials. All dashboard pages, charts, and the AI SQL feature work with synthetic data.

---

## Step 1 — Clone & Install

```bash
# Clone the project
git clone <your-repo-url>
cd enterprise-retail-analytics-engine

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 2 — Configure Environment

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env with your values
nano .env       # or use VS Code: code .env
```

**Minimum required for demo mode (no Snowflake):**
```env
FLASK_SECRET_KEY=any_random_string_here
FLASK_DEBUG=True
```

**Full configuration (with Snowflake + Gemini):**
```env
SF_ACCOUNT=xy12345.us-east-1
SF_USER=your_username
SF_PASSWORD=your_password
SF_WAREHOUSE=COMPUTE_WH
SF_DATABASE=RETAIL_ANALYTICS_DB
SF_SCHEMA=ANALYTICS
SF_ROLE=SYSADMIN
GEMINI_API_KEY=AIzaSy...your_key
FLASK_SECRET_KEY=change_this_to_something_random
FLASK_DEBUG=False
```

---

## Step 3 — Generate Synthetic Data

```bash
cd data_generation
python generate_data.py
```

**Expected output:**
```
✅ Customers: 10,000 rows → generated_data/customers.csv
✅ Products:     500 rows → generated_data/products.csv
✅ Orders:    50,000 rows → generated_data/orders.csv
✅ Order Items: 150,000 rows → generated_data/order_items.csv
✅ All referential integrity checks passed.
```

---

## Step 4 — Scrape Competitor Prices

```bash
python scrape_competitor.py
```

**Expected output:**
```
✅ Scraped 35 products → generated_data/competitor_prices.csv
```

---

## Step 5 — Snowflake Setup (Skip if demo mode)

```bash
cd ../snowflake

# Run the DDL to create database, schemas, and staging tables
# Option A: Run manually in Snowflake Web UI (Worksheets)
#   → Copy/paste content of ddl/staging_tables.sql

# Option B: Use SnowSQL CLI
snowsql -a $SF_ACCOUNT -u $SF_USER -f ddl/staging_tables.sql

# Load all CSVs into Snowflake
python load_to_snowflake.py
```

**Expected output:**
```
✅ CUSTOMERS loaded: 10,000 rows
✅ PRODUCTS loaded: 500 rows
✅ ORDERS loaded: 50,000 rows
✅ ORDER_ITEMS loaded: 150,000 rows
✅ COMPETITOR_PRICES loaded: 35 rows
```

### Validate Loads

```bash
# Run validation queries in Snowflake Web UI
# Copy/paste from: snowflake/validation_queries.sql
```

---

## Step 6 — dbt Transformations (Skip if demo mode)

```bash
cd ../dbt_project

# Set up dbt profile
# Copy profiles.yml to ~/.dbt/profiles.yml
cp profiles.yml ~/.dbt/profiles.yml

# Verify connection
dbt debug

# Install dbt packages
dbt deps

# Run all models
dbt run

# Run data quality tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve    # Opens at http://localhost:8080
```

**Expected dbt run output:**
```
Running with dbt=1.8.5
Found 11 models, 25 tests

01:23:45  Concurrency: 4 threads

01:23:46  1 of 11 START sql view model DBT_DEV.stg_customers ........... [RUN]
01:23:47  1 of 11 OK created sql view model DBT_DEV.stg_customers ....... [CREATE VIEW in 0.82s]
...
01:24:12  11 of 11 OK created sql table model ANALYTICS.customer_lifetime_value [TABLE in 4.21s]

Finished running 11 models in 27.3s
Completed successfully
```

---

## Step 7 — Run the Flask Dashboard

```bash
cd ../flask_app
python app.py
```

**Expected output:**
```
INFO  - Enterprise Retail Analytics Engine starting...
INFO  - Snowflake: CONNECTED (or DEMO MODE if no credentials)
INFO  - Gemini AI: READY (or DEMO MODE if no API key)
INFO  - Dashboard available at: http://localhost:5000
 * Running on http://127.0.0.1:5000
```

Open browser: **http://localhost:5000**

---

## Quick Start (Demo Mode Only — 2 minutes)

```bash
# Install dependencies
pip install flask python-dotenv

# Run directly
cd flask_app
FLASK_SECRET_KEY=demo FLASK_DEBUG=True python app.py

# Open: http://localhost:5000
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'snowflake'`
```bash
pip install snowflake-connector-python
```

### `dbt debug` fails — profile not found
```bash
# Ensure profiles.yml is in the right location
cp dbt_project/profiles.yml ~/.dbt/profiles.yml
# Then export your .env vars:
export SF_ACCOUNT=... SF_USER=... SF_PASSWORD=...
```

### Flask app shows blank charts
- Check browser console (F12 → Console) for JavaScript errors
- Ensure the `/api/data` endpoint returns valid JSON: `curl http://localhost:5000/revenue/api/data`

### Gemini API returns errors
- Verify `GEMINI_API_KEY` is set in `.env`
- Check quota at https://aistudio.google.com
- The app falls back to demo SQL patterns automatically

### Snowflake connection timeout
- Verify `SF_ACCOUNT` format: `xy12345.us-east-1` (no `https://`, no `.snowflakecomputing.com`)
- Check your IP is not blocked by Snowflake network policy

---

## Project Structure Recap

```
enterprise-retail-analytics-engine/
├── data_generation/     ← Step 3 & 4 (run these first)
├── snowflake/           ← Step 5 (optional — for real Snowflake)
├── dbt_project/         ← Step 6 (optional — for real Snowflake)
├── flask_app/           ← Step 7 (always run this)
├── docs/                ← Architecture, ERD, Viva prep
├── video_demo_script/   ← Recording guide
├── .env.example         ← Copy to .env and fill in
├── requirements.txt     ← pip install -r requirements.txt
└── run_project.md       ← You are here
```
