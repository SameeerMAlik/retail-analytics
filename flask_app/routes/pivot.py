"""
Enterprise Retail Analytics Engine — Pivot Route
Provides the PivotTable.js page and flat JSON rows API.
"""
import logging
import random
from flask import Blueprint, render_template, jsonify, request
from services.snowflake_service import snowflake_service

log = logging.getLogger(__name__)
pivot_bp = Blueprint("pivot", __name__)

# ── Demo flat row generator ───────────────────────────────────
def _demo_pivot_rows(limit: int = 500):
    """Returns flat rows that PivotTable.js can slice and dice."""
    rng        = random.Random(42)
    CATEGORIES = ["Electronics","Clothing","Home & Kitchen","Sports & Outdoors","Beauty & Health"]
    SUBCATS    = {
        "Electronics":       ["Laptops","Phones","Tablets","Accessories"],
        "Clothing":          ["Shirts","Pants","Shoes","Jackets"],
        "Home & Kitchen":    ["Cookware","Furniture","Decor","Appliances"],
        "Sports & Outdoors": ["Fitness","Camping","Cycling","Water Sports"],
        "Beauty & Health":   ["Skincare","Haircare","Supplements","Wellness"],
    }
    PAYMENTS   = ["Credit Card","Debit Card","PayPal","Apple Pay","Google Pay"]
    STATUSES   = ["completed","completed","completed","returned","cancelled"]
    AGE_GROUPS = ["18-25","26-35","36-45","46-55","55+"]
    CITIES     = ["New York","LA","Chicago","Houston","Phoenix","Dallas","Seattle","Miami","Denver","Boston"]
    MONTHS     = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    QUARTERS   = {m: f"Q{(i//3)+1}" for i, m in enumerate(MONTHS)}

    rows = []
    n    = min(limit, 5000) if limit > 0 else 500
    for _ in range(n):
        cat  = rng.choice(CATEGORIES)
        sub  = rng.choice(SUBCATS[cat])
        mon  = rng.choice(MONTHS)
        qty  = rng.randint(1, 5)
        price= round(rng.uniform(10, 500), 2)
        disc = round(rng.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20]), 2)
        net  = round(price * qty * (1 - disc), 2)
        cogs = round(net * rng.uniform(0.35, 0.65), 2)
        rows.append({
            "category":             cat,
            "subcategory":          sub,
            "payment_method":       rng.choice(PAYMENTS),
            "order_status":         rng.choice(STATUSES),
            "age_group":            rng.choice(AGE_GROUPS),
            "city":                 rng.choice(CITIES),
            "country":              "USA",
            "supplier_name":        f"Supplier {rng.randint(1,20):02d}",
            "order_month":          mon,
            "order_quarter":        QUARTERS[mon],
            "order_year":           rng.choice(["2023","2024"]),
            "quantity":             qty,
            "unit_price":           price,
            "net_revenue":          net,
            "gross_profit":         round(net - cogs, 2),
            "margin_pct":           round((net - cogs) / net * 100, 1) if net else 0,
            "competitor_price_delta": round(rng.uniform(-50, 80), 2)
        })
    return rows


# ── Page route ─────────────────────────────────────────────────
@pivot_bp.route("/")
def pivot_page():
    return render_template(
        "pivot.html",
        active_page="pivot",
        is_demo=not snowflake_service.is_connected()
    )


# ── JSON API — flat rows for PivotTable.js ─────────────────────
@pivot_bp.route("/api/data")
def pivot_api():
    try:
        limit = int(request.args.get("limit", 500))

        if not snowflake_service.is_connected():
            return jsonify({"rows": _demo_pivot_rows(limit)})

        limit_clause = f"LIMIT {limit}" if limit > 0 else ""
        sql = f"""
            SELECT
                dp.CATEGORY            AS category,
                dp.SUBCATEGORY         AS subcategory,
                dp.SUPPLIER_NAME       AS supplier_name,
                dc.AGE_GROUP           AS age_group,
                dc.CITY                AS city,
                dc.COUNTRY             AS country,
                fs.PAYMENT_METHOD      AS payment_method,
                fs.ORDER_STATUS        AS order_status,
                TO_CHAR(dd.DATE_ACTUAL, 'Mon')                    AS order_month,
                'Q' || CEIL(dd.MONTH_OF_YEAR/3.0)::INT           AS order_quarter,
                dd.YEAR::VARCHAR                                  AS order_year,
                fs.QUANTITY            AS quantity,
                ROUND(fs.UNIT_PRICE,2) AS unit_price,
                ROUND(fs.NET_REVENUE,2)AS net_revenue,
                ROUND(fs.GROSS_PROFIT,2)              AS gross_profit,
                ROUND(fs.MARGIN_PCT,1) AS margin_pct,
                ROUND(fs.COMPETITOR_PRICE_DELTA,2)    AS competitor_price_delta
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_PRODUCT  dp ON fs.PRODUCT_SK  = dp.PRODUCT_SK
            JOIN ANALYTICS.DIM_CUSTOMER dc ON fs.CUSTOMER_SK = dc.CUSTOMER_SK
            JOIN ANALYTICS.DIM_DATE     dd ON fs.DATE_SK      = dd.DATE_SK
            {limit_clause}
        """
        df   = snowflake_service.query(sql)
        rows = df.to_dict(orient="records")
        return jsonify({"rows": rows})

    except Exception as e:
        log.error("Pivot API error: %s", e)
        return jsonify({"rows": _demo_pivot_rows(500)})
