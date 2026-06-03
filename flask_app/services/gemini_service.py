"""
Enterprise Retail Analytics Engine
====================================
Gemini AI Service - Natural Language to SQL
Uses direct HTTP requests to Gemini API v1 (no SDK dependency issues).
"""

import os
import re
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

# ── Schema Context ─────────────────────────────────────────────────────────────
SCHEMA_CONTEXT = """
You are an expert Snowflake SQL writer for an e-commerce analytics platform.

DATABASE: RETAIL_ANALYTICS_DB
SCHEMA: ANALYTICS

STAR SCHEMA TABLES:

1. FCT_SALES (Fact Table - grain: one order line item)
   - ORDER_ITEM_ID, ORDER_ID, ORDER_DATE DATE
   - CUSTOMER_SK (FK to DIM_CUSTOMER)
   - PRODUCT_SK  (FK to DIM_PRODUCT)
   - PAYMENT_METHOD, ORDER_STATUS
   - QUANTITY, UNIT_PRICE, DISCOUNT
   - GROSS_REVENUE, NET_REVENUE, COGS, GROSS_PROFIT, MARGIN_PCT
   - COMPETITOR_PRICE, PRICE_DELTA

2. DIM_CUSTOMER (Dimension)
   - CUSTOMER_SK, CUSTOMER_ID, FULL_NAME, EMAIL
   - CITY, COUNTRY, AGE_GROUP, GENDER
   - REGISTRATION_DATE

3. DIM_PRODUCT (Dimension)
   - PRODUCT_SK, PRODUCT_ID, PRODUCT_NAME
   - CATEGORY, SUBCATEGORY, SUPPLIER_NAME
   - RETAIL_PRICE, BASE_COST, GROSS_MARGIN_PCT
   - PRICE_TIER, COMPETITOR_PRICE, PRICE_VS_COMPETITOR

4. DIM_DATE (Dimension)
   - DATE_SK, DATE_ACTUAL, YEAR, QUARTER_OF_YEAR
   - MONTH_OF_YEAR, MONTH_NAME, DAY_OF_MONTH
   - DAY_NAME, IS_WEEKEND, YEAR_MONTH

5. DAILY_REVENUE_TRENDS (Pre-aggregated analytics view)
   - MONTH_NAME, MONTH, MONTHLY_REVENUE, NUM_ORDERS, MOM_GROWTH_PCT

6. TOP_PRODUCT_CATEGORIES (Pre-aggregated)
   - CATEGORY, TOTAL_REVENUE, TOTAL_PROFIT, NUM_ORDERS
   - AVG_MARGIN_PCT, REVENUE_SHARE_PCT, REVENUE_RANK

RULES:
- Always use ANALYTICS. schema prefix
- Use proper JOINs via _SK foreign keys
- Return ONLY the SQL query - no explanation, no markdown, no backticks
- Only write SELECT statements
"""

# Working Gemini models to try in order
MODELS_TO_TRY = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
]


class GeminiService:

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = None
        self._model_checked = False

    def _ensure_model(self):
        """Resolve model on first use — avoids slow API probes during serverless cold start."""
        if self._model_checked:
            return
        self._model_checked = True
        if not self.api_key:
            return
        if os.getenv("VERCEL"):
            self.model_name = MODELS_TO_TRY[0]
            log.info("Vercel deploy: using Gemini model %s (no startup probe)", self.model_name)
            return
        self._find_working_model()

    def _find_working_model(self):
        """Try each model until one works."""
        if not self.api_key:
            log.warning("GEMINI_API_KEY not set. Running in demo mode.")
            return

        for model in MODELS_TO_TRY:
            url = (
                f"https://generativelanguage.googleapis.com/v1/models/"
                f"{model}:generateContent?key={self.api_key}"
            )
            try:
                resp = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": "Say OK"}]}]},
                    timeout=10
                )
                if resp.status_code == 200:
                    self.model_name = model
                    log.info("Gemini AI ready - using model: %s", model)
                    return
                else:
                    log.debug("Model %s returned %d - trying next", model, resp.status_code)
            except Exception as e:
                log.debug("Model %s error: %s - trying next", model, str(e))

        log.warning("No working Gemini model found. Running in demo mode.")

    def is_available(self) -> bool:
        self._ensure_model()
        return self.model_name is not None

    def generate_sql(self, user_question: str) -> tuple:
        if not user_question or not user_question.strip():
            return "", "Please provide a question"

        self._ensure_model()
        if not self.is_available():
            return self._demo_sql(user_question), None

        prompt = f"""{SCHEMA_CONTEXT}

User Question: "{user_question}"

Write a single Snowflake SQL SELECT query that answers this question.
Return ONLY the raw SQL - no markdown, no backticks, no explanation.
"""
        try:
            log.info("Sending to Gemini (%s): %s", self.model_name, user_question[:80])
            url = (
                f"https://generativelanguage.googleapis.com/v1/models/"
                f"{self.model_name}:generateContent?key={self.api_key}"
            )
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30
            )

            if resp.status_code == 429:
                return "", "Rate limit hit — please wait 1 minute and try again."

            if resp.status_code != 200:
                # Try refreshing the model on 404
                if resp.status_code == 404:
                    self.model_name = None
                    self._find_working_model()
                    if self.model_name:
                        return self.generate_sql(user_question)
                return "", f"AI service error: HTTP {resp.status_code} — {resp.text[:200]}"

            data     = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            sql      = self._extract_sql(raw_text)

            if not sql:
                return "", "Could not extract valid SQL from AI response"

            log.info("Generated SQL: %s...", sql[:100])
            return sql, None

        except Exception as e:
            log.error("Gemini error: %s", str(e))
            return "", f"AI service error: {str(e)}"

    def _extract_sql(self, text: str) -> str:
        text = re.sub(r"```(?:sql)?\n?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```", "", text).strip()
        match = re.search(r"(SELECT\s.+)", text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            sql = sql.split(";")[0].strip() + ";"
            return sql
        if text.upper().strip().startswith("SELECT"):
            return text.strip()
        return ""

    def _demo_sql(self, question: str) -> str:
        q = question.lower()
        if "customer" in q:
            return """SELECT
    c.FULL_NAME, c.CITY, c.AGE_GROUP,
    SUM(f.NET_REVENUE)           AS TOTAL_REVENUE,
    COUNT(DISTINCT f.ORDER_ID)   AS TOTAL_ORDERS
FROM ANALYTICS.FCT_SALES f
JOIN ANALYTICS.DIM_CUSTOMER c ON f.CUSTOMER_SK = c.CUSTOMER_SK
GROUP BY c.FULL_NAME, c.CITY, c.AGE_GROUP
ORDER BY TOTAL_REVENUE DESC
LIMIT 10;"""
        if "revenue" in q or "month" in q:
            return """SELECT
    MONTH_NAME, MONTH,
    ROUND(MONTHLY_REVENUE, 2) AS MONTHLY_REVENUE,
    NUM_ORDERS,
    ROUND(MOM_GROWTH_PCT, 2)  AS MOM_GROWTH_PCT
FROM ANALYTICS.DAILY_REVENUE_TRENDS
ORDER BY MONTH;"""
        if "product" in q or "category" in q:
            return """SELECT
    CATEGORY,
    ROUND(TOTAL_REVENUE, 2)  AS TOTAL_REVENUE,
    ROUND(AVG_MARGIN_PCT, 1) AS AVG_MARGIN_PCT,
    NUM_ORDERS
FROM ANALYTICS.TOP_PRODUCT_CATEGORIES
ORDER BY REVENUE_RANK LIMIT 10;"""
        if "competitor" in q or "price" in q:
            return """SELECT
    PRODUCT_NAME, CATEGORY,
    RETAIL_PRICE, COMPETITOR_PRICE,
    PRICE_VS_COMPETITOR
FROM ANALYTICS.DIM_PRODUCT
WHERE COMPETITOR_PRICE IS NOT NULL
ORDER BY RETAIL_PRICE DESC LIMIT 20;"""
        return """SELECT
    MONTH_NAME,
    ROUND(SUM(NET_REVENUE), 2) AS TOTAL_REVENUE,
    COUNT(DISTINCT ORDER_ID)   AS TOTAL_ORDERS
FROM ANALYTICS.FCT_SALES
GROUP BY MONTH_NAME, MONTH(ORDER_DATE)
ORDER BY MONTH(ORDER_DATE);"""


gemini_service = GeminiService()
