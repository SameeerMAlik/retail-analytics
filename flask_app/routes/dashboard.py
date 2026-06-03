"""
Enterprise Retail Analytics Engine
====================================
Flask Routes - Dashboard (Home Page)
"""

import logging
import random
from flask import Blueprint, render_template
from services.snowflake_service import snowflake_service

log = logging.getLogger(__name__)
dashboard_bp = Blueprint("dashboard", __name__)


def _demo_dashboard_data():
    """Complete demo data for dashboard when Snowflake unavailable."""
    rng = random.Random(42)

    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # Seasonal pattern: Q4 peak, Jan dip
    base = [38, 41, 52, 58, 61, 65, 68, 71, 74, 92, 110, 98]
    monthly_values = [v * 1000 + rng.randint(-2000, 2000) for v in base]

    kpi = {
        "total_revenue":    "$11,420,000",
        "total_orders":     "48,250",
        "active_customers": "8,910",
        "avg_margin":       "33.8%",
        "aov":              "$237.50",
    }
    monthly_chart = {
        "labels":  MONTHS,
        "revenue": monthly_values,
    }
    category_chart = {
        "labels":  ["Electronics", "Clothing", "Home & Kitchen", "Sports & Outdoors", "Beauty & Health"],
        "revenue": [4250000, 2890000, 1950000, 1340000, 980000],
    }
    top_products = [
        {"name": "ProMax Laptop 15\"",    "category": "Electronics",    "revenue": 892000},
        {"name": "UltraPhone X",           "category": "Electronics",    "revenue": 654000},
        {"name": "Running Shoes Pro",      "category": "Sports",         "revenue": 423000},
        {"name": "Coffee Maker Deluxe",    "category": "Home & Kitchen", "revenue": 318000},
        {"name": "Vitamin C 1000mg",       "category": "Beauty & Health","revenue": 241000},
    ]
    return kpi, monthly_chart, category_chart, top_products


@dashboard_bp.route("/")
def home():
    """Dashboard home - KPI cards + summary charts."""
    is_demo = not snowflake_service.is_connected()

    if is_demo:
        kpi, monthly_chart, category_chart, top_products = _demo_dashboard_data()
    else:
        try:
            kpi_sql = """
            SELECT
                ROUND(SUM(NET_REVENUE), 0)                                          AS TOTAL_REVENUE,
                COUNT(DISTINCT ORDER_ID)                                             AS TOTAL_ORDERS,
                COUNT(DISTINCT CUSTOMER_SK)                                          AS ACTIVE_CUSTOMERS,
                ROUND(AVG(MARGIN_PCT), 2)                                           AS AVG_MARGIN_PCT,
                ROUND(SUM(NET_REVENUE) / NULLIF(COUNT(DISTINCT ORDER_ID), 0), 2)   AS AOV
            FROM ANALYTICS.FCT_SALES
            """
            monthly_sql = """
            SELECT
                TO_CHAR(DATE_TRUNC('month', ORDER_DATE), 'Mon') AS MONTH_NAME,
                MONTH(ORDER_DATE)                               AS MONTH_NUM,
                ROUND(SUM(NET_REVENUE), 0)                      AS MONTHLY_REVENUE
            FROM ANALYTICS.FCT_SALES
            GROUP BY DATE_TRUNC('month', ORDER_DATE), MONTH(ORDER_DATE)
            ORDER BY MONTH_NUM
            LIMIT 12
            """
            category_sql = """
            SELECT CATEGORY, ROUND(SUM(NET_REVENUE), 0) AS TOTAL_REVENUE
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_PRODUCT dp ON fs.PRODUCT_SK = dp.PRODUCT_SK
            GROUP BY CATEGORY
            ORDER BY TOTAL_REVENUE DESC
            LIMIT 5
            """
            top_sql = """
            SELECT dp.PRODUCT_NAME AS name, dp.CATEGORY AS category,
                   ROUND(SUM(fs.NET_REVENUE), 0) AS revenue
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_PRODUCT dp ON fs.PRODUCT_SK = dp.PRODUCT_SK
            GROUP BY dp.PRODUCT_NAME, dp.CATEGORY
            ORDER BY revenue DESC
            LIMIT 5
            """

            kpi_df      = snowflake_service.query(kpi_sql)
            monthly_df  = snowflake_service.query(monthly_sql)
            cat_df      = snowflake_service.query(category_sql)
            top_df      = snowflake_service.query(top_sql)

            kpi = {
                "total_revenue":    f"${kpi_df['TOTAL_REVENUE'].iloc[0]:,.0f}"    if len(kpi_df) else "$0",
                "total_orders":     f"{kpi_df['TOTAL_ORDERS'].iloc[0]:,}"         if len(kpi_df) else "0",
                "active_customers": f"{kpi_df['ACTIVE_CUSTOMERS'].iloc[0]:,}"     if len(kpi_df) else "0",
                "avg_margin":       f"{kpi_df['AVG_MARGIN_PCT'].iloc[0]:.1f}%"    if len(kpi_df) else "0%",
                "aov":              f"${kpi_df['AOV'].iloc[0]:,.2f}"              if len(kpi_df) else "$0",
            }
            monthly_chart = {
                "labels":  monthly_df["MONTH_NAME"].tolist()       if len(monthly_df) else [],
                "revenue": monthly_df["MONTHLY_REVENUE"].tolist()  if len(monthly_df) else [],
            }
            category_chart = {
                "labels":  cat_df["CATEGORY"].tolist()      if len(cat_df) else [],
                "revenue": cat_df["TOTAL_REVENUE"].tolist() if len(cat_df) else [],
            }
            top_products = top_df.to_dict(orient="records") if len(top_df) else []

        except Exception as e:
            log.error("Dashboard Snowflake error: %s", str(e))
            kpi, monthly_chart, category_chart, top_products = _demo_dashboard_data()
            is_demo = True

    return render_template(
        "dashboard.html",
        kpi=kpi,
        monthly_chart=monthly_chart,
        category_chart=category_chart,
        top_products=top_products,
        is_demo=is_demo,
        active_page="dashboard"
    )
