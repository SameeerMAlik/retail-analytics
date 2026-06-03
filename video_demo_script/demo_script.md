# Video Demo Script — Enterprise Retail Analytics Engine
**Duration:** 2–3 minutes | **Format:** Screen recording with voiceover

---

## Pre-Recording Checklist
- [ ] Open terminal in project root
- [ ] Flask app running: `python flask_app/app.py`
- [ ] Browser open at `http://localhost:5000`
- [ ] Screen recording software ready (OBS / Loom)
- [ ] Clear browser history / use incognito for clean demo
- [ ] Zoom browser to 110% for readability

---

## Script

---

### [0:00–0:15] — Title Card / Intro

> **"Welcome to the Enterprise Retail Analytics Engine — a full end-to-end data engineering capstone project. In the next two and a half minutes, I'll walk you through how we built a complete retail analytics pipeline from raw data generation all the way to an AI-powered dashboard."**

*[Show the README.md or architecture diagram briefly]*

---

### [0:15–0:45] — Phase 1: Data Generation

*[Switch to VS Code or terminal, show `data_generation/` folder]*

> **"The pipeline starts with synthetic data generation. Using Python's Faker library and NumPy, we generated 10,000 customers, 500 products, 50,000 orders, and 150,000 order items — all with referential integrity and realistic distributions. Notice the seasonal weighting: Q4 peaks at double the normal volume, simulating real-world holiday sales patterns."**

*[Briefly show `generate_data.py` — highlight the seasonal weight array and Zipf distribution for products]*

> **"We also built a web scraper using BeautifulSoup4 that extracts competitor pricing from this static HTML page — giving us price intelligence data."**

*[Show `competitor_site.html` in browser, then `scrape_competitor.py` briefly]*

---

### [0:45–1:10] — Phase 2: Snowflake + dbt

*[Show `snowflake/` folder briefly, then switch to dbt folder]*

> **"Once data is generated, our Python loader pushes all five CSVs into Snowflake's staging schema using the native connector. From there, dbt takes over."**

*[Show `dbt_project/models/` folder structure in VS Code]*

> **"We built a three-layer dbt architecture. Staging models clean raw data and are materialised as views. Mart models build a classic star schema — one fact table called fct_sales surrounded by three dimension tables — materialised as tables for fast query performance. Analytics models pre-aggregate key metrics. All models have schema.yml tests for uniqueness, nulls, and referential integrity."**

*[Show `dbt_project/models/marts/fct_sales.sql` briefly]*

---

### [1:10–1:35] — Phase 3: Flask Dashboard

*[Switch to browser at http://localhost:5000]*

> **"The Flask dashboard has six pages, all powered by JSON APIs connected to Snowflake — or in demo mode, high-quality synthetic data."**

*[Click through: Dashboard → Revenue → Products → Customers]*

> **"The dashboard home shows live KPIs: total revenue, orders, customers, and average order value. The revenue page shows a 12-month trend with month-over-month growth rates."**

*[Click Revenue page — point to the trend chart]*

> **"The products page has a competitor price intelligence scatter plot — you can see which of our products are priced below and above competitor prices."**

*[Click Products page — point to the scatter chart]*

> **"Customer insights shows CLV segmentation — breaking our 10,000 customers into Standard, Mid Value, High Value, and VIP tiers."**

---

### [1:35–1:55] — Pivot Analysis

*[Click Pivot Analysis page]*

> **"The pivot analysis page uses PivotTable.js for drag-and-drop multidimensional exploration. I'll click Load Data and select a preset."**

*[Click Load/Refresh Data, choose "Revenue by Category × Month" from the dropdown]*

> **"You can see revenue broken down by category and month. And because this is a fully interactive pivot table, you can drag any field into rows or columns, change the aggregator to Average or Count, and explore the data however you need."**

---

### [1:55–2:25] — AI SQL Feature

*[Click "Ask Your Data" in the sidebar]*

> **"Now the highlight of the project — natural language to SQL using Google Gemini. The system takes a plain English question, builds a prompt with the full star schema context, sends it to the Gemini API, validates the returned SQL for safety — blocking any destructive keywords — and executes it."**

*[Type in the question box: "Show me the top 5 customers by total revenue"]*

*[Click Submit, watch the result appear]*

> **"Gemini generated a SELECT query joining our fact and dimension tables, and here are the results. The generated SQL is shown transparently so users can learn from it or copy it."**

*[Point to the "Generated SQL" section showing the SQL code block]*

---

### [2:25–2:45] — Wrap Up

*[Return to the Dashboard page]*

> **"To summarise: this project demonstrates a complete enterprise data pipeline — from data generation and web scraping, through Snowflake ingestion, dbt star schema transformations with quality tests, to a professional Flask dashboard with interactive charts, pivot analytics, and an AI-powered SQL interface."**

> **"The stack is fully documented, the project runs end-to-end locally in demo mode without any cloud credentials, and all code follows production engineering practices — modular blueprints, environment-variable secrets, in-memory caching, and comprehensive error handling."**

> **"Thank you."**

---

## Recording Tips
- Speak at 80% of your natural speed — recordings always sound faster
- Keep the cursor moving smoothly — jerky mouse movements are distracting
- If you make a mistake, pause 3 seconds and redo that sentence — easy to cut in editing
- Record in 1920×1080 minimum
- Use a headset microphone — laptop mic picks up keyboard noise
