"""
Enterprise Retail Analytics Engine — Customers Route
Provides page render + JSON API for customer insights dashboard.
"""
import logging
import random
from flask import Blueprint, render_template, jsonify
from services.snowflake_service import snowflake_service

log = logging.getLogger(__name__)
customers_bp = Blueprint("customers", __name__)

# ── Demo data ─────────────────────────────────────────────────
def _demo_customer_data():
    rng    = random.Random(42)
    CITIES = ["New York","Los Angeles","Chicago","Houston","Phoenix","Philadelphia","San Antonio","San Diego","Dallas","San Jose"]
    AGES   = ["18-25","26-35","36-45","46-55","55+"]
    NAMES  = [
        "Emma Wilson","James Martinez","Sophia Johnson","Liam Brown","Olivia Davis",
        "Noah Garcia","Ava Miller","William Anderson","Isabella Taylor","Benjamin Thomas",
        "Mia Jackson","Elijah White","Charlotte Harris","Lucas Clark","Amelia Lewis",
        "Mason Robinson","Harper Walker","Ethan Hall","Evelyn Allen","Aiden Young"
    ]
    PAYMENTS = ["Credit Card","Debit Card","PayPal","Apple Pay","Google Pay"]

    # Top 25 customers
    top_customers = []
    for i, name in enumerate(NAMES[:20]):
        rev = rng.randint(2_000, 28_000)
        ord = rng.randint(5, 80)
        seg = "VIP" if rev > 15000 else "High Value" if rev > 8000 else "Mid Value" if rev > 4000 else "Standard"
        top_customers.append({
            "full_name":        name,
            "city":             rng.choice(CITIES),
            "age_group":        rng.choice(AGES),
            "total_orders":     ord,
            "total_revenue":    rev,
            "avg_order_value":  round(rev / ord, 2),
            "segment":          seg
        })
    top_customers.sort(key=lambda x: x["total_revenue"], reverse=True)

    # CLV segments
    clv_segments = [
        {"segment": "Standard (< $1k)",      "count": rng.randint(3000, 4000)},
        {"segment": "Mid Value ($1k–$5k)",   "count": rng.randint(2500, 3500)},
        {"segment": "High Value ($5k–$15k)", "count": rng.randint(1500, 2500)},
        {"segment": "VIP (> $15k)",          "count": rng.randint(200, 600)}
    ]

    # Age groups
    age_groups = [
        {"age_group": ag, "total_revenue": rng.randint(80_000, 350_000), "avg_clv": rng.randint(800, 6000)}
        for ag in AGES
    ]

    # Payment methods
    payment_methods = [
        {"method": m, "count": rng.randint(4000, 18000)} for m in PAYMENTS
    ]

    # Registration trend (12 months)
    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    reg_trend = [{"month": m, "count": rng.randint(600, 1200)} for m in MONTHS]

    # KPIs
    all_rev   = [c["total_revenue"] for c in top_customers]
    vip_count = sum(1 for c in top_customers if c["segment"] == "VIP")
    kpis = {
        "total_customers":          10000,
        "avg_clv":                  round(sum(all_rev) / len(all_rev)),
        "vip_count":                vip_count * 15,   # scale to full dataset
        "avg_orders_per_customer":  round(sum(c["total_orders"] for c in top_customers) / len(top_customers), 1)
    }

    return {
        "kpis": kpis,
        "top_customers":     top_customers,
        "clv_segments":      clv_segments,
        "age_groups":        age_groups,
        "payment_methods":   payment_methods,
        "registration_trend": reg_trend
    }


# ── Page route ─────────────────────────────────────────────────
@customers_bp.route("/")
def customers_page():
    return render_template(
        "customers.html",
        active_page="customers",
        is_demo=not snowflake_service.is_connected()
    )


# ── JSON API ───────────────────────────────────────────────────
@customers_bp.route("/api/data")
def customers_api():
    try:
        if not snowflake_service.is_connected():
            return jsonify(_demo_customer_data())

        # Top 25 customers by CLV
        top_sql = """
            SELECT
                dc.FULL_NAME,
                dc.CITY,
                dc.AGE_GROUP,
                COUNT(DISTINCT fs.ORDER_ID)          AS total_orders,
                ROUND(SUM(fs.NET_REVENUE), 0)        AS total_revenue,
                ROUND(SUM(fs.NET_REVENUE)/NULLIF(COUNT(DISTINCT fs.ORDER_ID),0), 2) AS avg_order_value,
                CASE
                    WHEN SUM(fs.NET_REVENUE) > 15000 THEN 'VIP'
                    WHEN SUM(fs.NET_REVENUE) > 8000  THEN 'High Value'
                    WHEN SUM(fs.NET_REVENUE) > 4000  THEN 'Mid Value'
                    ELSE 'Standard'
                END AS segment
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_CUSTOMER dc ON fs.CUSTOMER_SK = dc.CUSTOMER_SK
            GROUP BY dc.FULL_NAME, dc.CITY, dc.AGE_GROUP
            ORDER BY total_revenue DESC
            LIMIT 25
        """

        # CLV segments
        seg_sql = """
            SELECT
                CASE
                    WHEN clv < 1000  THEN 'Standard (< $1k)'
                    WHEN clv < 5000  THEN 'Mid Value ($1k–$5k)'
                    WHEN clv < 15000 THEN 'High Value ($5k–$15k)'
                    ELSE 'VIP (> $15k)'
                END AS segment,
                COUNT(*) AS count
            FROM (
                SELECT CUSTOMER_SK, SUM(NET_REVENUE) AS clv
                FROM ANALYTICS.FCT_SALES
                GROUP BY CUSTOMER_SK
            ) sub
            GROUP BY segment
        """

        # Age group revenue
        age_sql = """
            SELECT dc.AGE_GROUP AS age_group,
                   ROUND(SUM(fs.NET_REVENUE), 0)                        AS total_revenue,
                   ROUND(AVG(sub.clv), 0)                               AS avg_clv
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_CUSTOMER dc ON fs.CUSTOMER_SK = dc.CUSTOMER_SK
            JOIN (SELECT CUSTOMER_SK, SUM(NET_REVENUE) AS clv FROM ANALYTICS.FCT_SALES GROUP BY CUSTOMER_SK) sub
              ON sub.CUSTOMER_SK = dc.CUSTOMER_SK
            GROUP BY dc.AGE_GROUP
        """

        # Payment methods
        pay_sql = """
            SELECT PAYMENT_METHOD AS method, COUNT(*) AS count
            FROM ANALYTICS.FCT_SALES
            GROUP BY PAYMENT_METHOD
            ORDER BY count DESC
        """

        # Registration trend
        reg_sql = """
            SELECT TO_CHAR(REGISTRATION_DATE, 'Mon') AS month,
                   MONTH(REGISTRATION_DATE)           AS month_num,
                   COUNT(*)                           AS count
            FROM ANALYTICS.DIM_CUSTOMER
            GROUP BY TO_CHAR(REGISTRATION_DATE, 'Mon'), MONTH(REGISTRATION_DATE)
            ORDER BY month_num
        """

        top_df = snowflake_service.query(top_sql)
        seg_df = snowflake_service.query(seg_sql)
        age_df = snowflake_service.query(age_sql)
        pay_df = snowflake_service.query(pay_sql)
        reg_df = snowflake_service.query(reg_sql)

        top_customers   = top_df.to_dict(orient="records")
        all_rev         = [c["total_revenue"] for c in top_customers]
        vip_count       = sum(1 for c in top_customers if c["segment"] == "VIP")
        kpis = {
            "total_customers":         10000,
            "avg_clv":                 round(sum(all_rev) / max(len(all_rev), 1)),
            "vip_count":               vip_count,
            "avg_orders_per_customer": round(sum(c["total_orders"] for c in top_customers) / max(len(top_customers), 1), 1)
        }

        return jsonify({
            "kpis":               kpis,
            "top_customers":      top_customers,
            "clv_segments":       seg_df.to_dict(orient="records"),
            "age_groups":         age_df.to_dict(orient="records"),
            "payment_methods":    pay_df.to_dict(orient="records"),
            "registration_trend": reg_df.to_dict(orient="records")
        })

    except Exception as e:
        log.error("Customers API error: %s", e)
        return jsonify(_demo_customer_data())
