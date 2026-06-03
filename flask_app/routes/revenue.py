"""
Enterprise Retail Analytics Engine — Revenue Route
"""
import logging
from flask import Blueprint, render_template, jsonify, request
from services.snowflake_service import snowflake_service

log = logging.getLogger(__name__)
revenue_bp = Blueprint("revenue", __name__)


@revenue_bp.route("/")
def revenue_page():
    try:
        # Daily data for trend chart (last 365 days)
        sql = """
        SELECT ORDER_DATE, ROUND(NET_REVENUE,0) AS NET_REVENUE,
               ROUND(GROSS_PROFIT,0) AS GROSS_PROFIT,
               NUM_ORDERS, ROUND(MARGIN_PCT,2) AS MARGIN_PCT
        FROM ANALYTICS.DAILY_REVENUE_TRENDS
        ORDER BY ORDER_DATE
        """
        df = snowflake_service.query(sql)
        chart_data = {
            "labels":   df["ORDER_DATE"].astype(str).tolist() if len(df) else [],
            "revenue":  df["NET_REVENUE"].tolist() if len(df) else [],
            "profit":   df["GROSS_PROFIT"].tolist() if len(df) else [],
            "orders":   df["NUM_ORDERS"].tolist() if len(df) else [],
        }
    except Exception as e:
        log.error("Revenue page error: %s", e)
        chart_data = {"labels": [], "revenue": [], "profit": [], "orders": []}

    return render_template("revenue.html", chart_data=chart_data,
                           active_page="revenue",
                           is_demo=not snowflake_service.is_connected())


@revenue_bp.route("/api/monthly")
def monthly_api():
    """AJAX endpoint: monthly revenue breakdown."""
    try:
        sql = """
        SELECT MONTH_NAME, MONTH, ROUND(MONTHLY_REVENUE,0) AS MONTHLY_REVENUE,
               MONTHLY_ORDERS, ROUND(AVG_MARGIN_PCT,2) AS AVG_MARGIN_PCT,
               ROUND(MOM_GROWTH_PCT,2) AS MOM_GROWTH_PCT
        FROM ANALYTICS.DAILY_REVENUE_TRENDS
        GROUP BY MONTH_NAME, MONTH, MONTHLY_REVENUE, MONTHLY_ORDERS,
                 AVG_MARGIN_PCT, MOM_GROWTH_PCT
        ORDER BY MONTH
        """
        df = snowflake_service.query(sql)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
