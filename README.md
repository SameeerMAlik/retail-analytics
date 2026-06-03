# 🏪 Enterprise Retail Analytics Engine

> A production-style end-to-end data engineering capstone project — from synthetic data generation to an AI-powered analytics dashboard, built on Snowflake, dbt, and Flask.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Snowflake](https://img.shields.io/badge/Snowflake-Cloud_DW-29B5E8?style=flat&logo=snowflake&logoColor=white)](https://snowflake.com)
[![dbt](https://img.shields.io/badge/dbt-Core_1.8-FF694B?style=flat&logo=dbt&logoColor=white)](https://getdbt.com)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=flat&logo=bootstrap&logoColor=white)](https://getbootstrap.com)

---

## 📋 Project Overview

The **Enterprise Retail Analytics Engine** is a complete data engineering pipeline that simulates a real-world retail analytics platform. It demonstrates proficiency across the modern data stack:

- **Data Ingestion**: 215,500 synthetic records generated with realistic distributions
- **Cloud Warehouse**: Snowflake multi-layer schema (staging → analytics → star schema)
- **Transformation**: dbt Core with 11 models, star schema, and 25+ data quality tests
- **Analytics Dashboard**: Flask with Chart.js, DataTables, and PivotTable.js
- **AI Feature**: Natural language to SQL using Google Gemini API

The entire project runs in **demo mode** without any cloud credentials — every dashboard page, chart, and AI feature works immediately after `pip install`.

---

## 🏗️ Architecture

```
┌──────────────────┐     ┌───────────────┐     ┌──────────────────────┐
│   Data Sources   │────▶│  Snowflake    │────▶│    dbt Core          │
│  Faker | BS4     │     │  Staging      │     │  Staging → Marts →   │
│  10K customers   │     │  Schema       │     │  Analytics           │
│  500 products    │     │               │     │  Star Schema         │
│  50K orders      │     │               │     │  + Quality Tests     │
└──────────────────┘     └───────────────┘     └──────────┬───────────┘
                                                           │
                         ┌─────────────────────────────────▼───────────┐
                         │            Flask Analytics Dashboard          │
                         │   Dashboard | Revenue | Products | Customers  │
                         │   Pivot Analysis | Ask Your Data (AI SQL)     │
                         │   Bootstrap 5 | Chart.js | PivotTable.js     │
                         └─────────────────────────────────────────────┘
```

**Full architecture diagram:** [`docs/architecture.md`](docs/architecture.md)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.11+ | Core development language |
| **Data Generation** | Faker + NumPy + Pandas | 215K realistic synthetic records |
| **Web Scraping** | BeautifulSoup4 | Competitor price extraction |
| **Cloud Warehouse** | Snowflake | Columnar OLAP data warehouse |
| **Transformation** | dbt Core 1.8 | SQL-first ELT with testing |
| **Web Framework** | Flask 3.0 | Lightweight Python web server |
| **Frontend** | Bootstrap 5 + Chart.js | Responsive dark-theme UI |
| **Pivot Analytics** | PivotTable.js | Drag-and-drop OLAP explorer |
| **Tables** | DataTables | Sortable, searchable data tables |
| **AI Integration** | Google Gemini API | Natural language to SQL |
| **Config** | python-dotenv | Environment variable management |

---

## 📁 Project Structure

```
enterprise-retail-analytics-engine/
│
├── data_generation/
│   ├── generate_data.py          # Synthetic data with Faker + NumPy
│   ├── scrape_competitor.py      # BeautifulSoup4 price scraper
│   ├── competitor_site.html      # Sample competitor HTML page
│   └── generated_data/           # Output CSVs (git-ignored)
│
├── snowflake/
│   ├── ddl/
│   │   └── staging_tables.sql    # Database/schema/table DDL
│   ├── load_to_snowflake.py      # Automated CSV → Snowflake loader
│   └── validation_queries.sql    # Post-load data quality checks
│
├── dbt_project/
│   ├── models/
│   │   ├── staging/              # stg_customers, stg_products, stg_orders, stg_order_items
│   │   ├── marts/                # dim_customer, dim_product, dim_date, fct_sales
│   │   └── analytics/            # daily_revenue_trends, top_product_categories, customer_lifetime_value
│   ├── dbt_project.yml           # dbt project configuration
│   ├── schema.yml                # Column tests: unique, not_null, relationships
│   └── profiles.yml              # Snowflake connection (copy to ~/.dbt/)
│
├── flask_app/
│   ├── app.py                    # Application factory + blueprint registration
│   ├── routes/                   # dashboard, revenue, products, customers, pivot, ai_sql
│   ├── services/                 # snowflake_service.py (TTL cache), gemini_service.py
│   └── templates/                # Jinja2 HTML templates (dark cyber theme)
│
├── docs/
│   ├── architecture.md           # Full system architecture with ASCII diagrams
│   ├── ERD.md                    # Mermaid ERD + relationship explanations
│   └── viva_questions.md         # 30+ viva Q&A covering all major concepts
│
├── video_demo_script/
│   └── demo_script.md            # Timestamped 2-3 min recording script
│
├── .env.example                  # Environment variable template
├── requirements.txt              # All Python dependencies with versions
├── run_project.md                # Step-by-step execution guide
└── README.md                     # This file
```

---

## ⚡ Quick Start (Demo Mode — No Cloud Required)

```bash
# 1. Clone and navigate
git clone <your-repo-url>
cd enterprise-retail-analytics-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set minimum environment
cp .env.example .env
# Edit .env: set FLASK_SECRET_KEY=any_string

# 4. Launch dashboard
cd flask_app
python app.py

# 5. Open browser
# http://localhost:5000
```

> The app detects missing Snowflake credentials and activates **demo mode** automatically — all 6 dashboard pages, all charts, and the AI SQL feature serve high-quality synthetic data.

---

## 🔧 Full Installation (With Snowflake)

### 1. Prerequisites

- Python 3.11+
- Snowflake account ([free 30-day trial](https://signup.snowflake.com/))
- Google Gemini API key ([free tier](https://aistudio.google.com/app/apikey))

### 2. Python Environment

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env`:
```env
SF_ACCOUNT=your_account.region
SF_USER=your_username
SF_PASSWORD=your_password
SF_WAREHOUSE=COMPUTE_WH
SF_DATABASE=RETAIL_ANALYTICS_DB
SF_SCHEMA=ANALYTICS
SF_ROLE=SYSADMIN
GEMINI_API_KEY=your_gemini_key
FLASK_SECRET_KEY=your_random_secret
```

### 4. Snowflake Setup

```bash
# Generate data
cd data_generation
python generate_data.py
python scrape_competitor.py

# Load to Snowflake
cd ../snowflake
python load_to_snowflake.py
```

### 5. dbt Setup

```bash
# Copy profile to dbt's expected location
cp dbt_project/profiles.yml ~/.dbt/profiles.yml

cd dbt_project
dbt debug        # Verify connection
dbt run          # Build all 11 models
dbt test         # Run 25+ quality tests
```

### 6. Launch Dashboard

```bash
cd ../flask_app
python app.py
# → http://localhost:5000
```

---

## 📊 Dashboard Pages

| Page | URL | Description |
|---|---|---|
| **Dashboard** | `/` | KPI cards, revenue sparklines, top products summary |
| **Revenue Analytics** | `/revenue` | 12-month trend, MoM growth, payment method breakdown |
| **Product Analytics** | `/products` | Category revenue, margin radar, competitor scatter plot |
| **Customer Insights** | `/customers` | CLV segmentation, age group analysis, registration trend |
| **Pivot Analysis** | `/pivot` | PivotTable.js drag-drop OLAP explorer with CSV/JSON export |
| **Ask Your Data** | `/ai-sql` | Natural language → Gemini API → Snowflake SQL → results |

---

## 🤖 AI SQL Feature

The **Ask Your Data** page converts plain English questions into validated Snowflake SQL using the Google Gemini API.

**Example questions:**
- *"Show top 5 customers by total revenue"*
- *"What are the highest margin products in Electronics?"*
- *"Monthly revenue trend for last 6 months"*
- *"Which payment method generates the most orders?"*

**Security measures:**
- Only `SELECT` queries are permitted
- Blocks: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `CREATE`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, `EXECUTE`
- Generated SQL displayed to user before execution
- Results capped at 500 rows

---

## 🗂️ Star Schema

```
                    ┌──────────────┐
                    │  DIM_DATE    │
                    │  date_sk PK  │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────▼──────────────────────┐    ┌──────────────┐
│ DIM_CUSTOMER │    │         FCT_SALES             │    │ DIM_PRODUCT  │
│ customer_sk  │◄───│ sale_sk        PK            │───▶│ product_sk   │
│ full_name    │    │ customer_sk    FK            │    │ category     │
│ city         │    │ product_sk     FK            │    │ retail_price │
│ age_group    │    │ date_sk        FK            │    │ margin_pct   │
└──────────────┘    │ net_revenue    measure       │    │ competitor_$ │
                    │ gross_profit   measure       │    └──────────────┘
                    │ margin_pct     measure       │
                    │ quantity       measure       │
                    └──────────────────────────────┘
```

**Grain:** One row per order line item

---

## 🧪 Data Quality Tests

dbt schema tests defined in `schema.yml`:

```yaml
# Example: fct_sales tests
- name: sale_sk
  tests: [unique, not_null]
- name: customer_sk
  tests:
    - relationships:
        to: ref('dim_customer')
        field: customer_sk
- name: net_revenue
  tests: [not_null]
- name: order_status
  tests:
    - accepted_values:
        values: [completed, cancelled, returned, processing]
```

Run tests: `dbt test --project-dir dbt_project`

---

## 📸 Screenshots

*Place screenshots in `docs/screenshots/` after recording your demo.*

| Screenshot | Description |
|---|---|
| `01_dashboard.png` | Main dashboard with KPI cards and summary charts |
| `02_revenue.png` | Revenue analytics with 12-month trend line |
| `03_products.png` | Product analytics with competitor scatter plot |
| `04_customers.png` | Customer CLV segmentation chart |
| `05_pivot.png` | PivotTable.js drag-and-drop explorer |
| `06_ai_sql.png` | Ask Your Data with generated SQL and results |

---

## 🔍 Validation

```bash
# Validate CSV generation
cd data_generation
python -c "
import pandas as pd
c = pd.read_csv('generated_data/customers.csv')
o = pd.read_csv('generated_data/orders.csv')
oi = pd.read_csv('generated_data/order_items.csv')
assert len(c) == 10000,  f'Customers: {len(c)}'
assert len(o) == 50000,  f'Orders: {len(o)}'
assert len(oi) == 150000, f'Items: {len(oi)}'
assert set(o.customer_id).issubset(set(c.customer_id)), 'FK violation: orders.customer_id'
assert set(oi.order_id).issubset(set(o.order_id)), 'FK violation: order_items.order_id'
print('✅ All integrity checks passed')
"

# Validate Flask APIs
curl http://localhost:5000/revenue/api/data | python -m json.tool | head -30
curl http://localhost:5000/products/api/data | python -m json.tool | head -30
```

---

## 🚀 Future Enhancements

- [ ] Incremental dbt models for daily data refresh
- [ ] Snowflake row-level security for multi-tenant access
- [ ] User authentication with Flask-Login
- [ ] Redis cache layer for multi-worker deployments
- [ ] CI/CD: GitHub Actions runs `dbt test` on every PR
- [ ] Email/Slack alerts when KPIs drop below thresholds
- [ ] Export dashboard to PDF (pdfkit/WeasyPrint)
- [ ] Real-time streaming with Snowflake Streams + Tasks

---

## 📚 References

- [Snowflake Documentation](https://docs.snowflake.com)
- [dbt Core Documentation](https://docs.getdbt.com)
- [Flask Documentation](https://flask.palletsprojects.com)
- [Google Gemini API](https://ai.google.dev)
- [PivotTable.js Documentation](https://pivottable.js.org)
- [The Data Warehouse Toolkit — Ralph Kimball](https://www.kimballgroup.com)

---

## 👥 Team Members

| Name | Role |
|---|---|
| *[Your Name]* | Lead Data Engineer — Pipeline, dbt, Snowflake |
| *[Member 2]* | Frontend Engineer — Flask, Charts, UI |
| *[Member 3]* | Data Analyst — Analytics models, Viva prep |

---

## 📄 License

This project was developed as a university capstone submission. All synthetic data is generated and contains no real personal information.

---

*Built with ❤️ using Python, Snowflake, dbt, and Flask*
