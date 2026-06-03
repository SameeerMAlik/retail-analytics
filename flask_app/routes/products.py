"""
Enterprise Retail Analytics Engine — Products Route
Provides page render + JSON API for the products analytics dashboard.
"""
import logging
import random
from flask import Blueprint, render_template, jsonify
from services.snowflake_service import snowflake_service

log = logging.getLogger(__name__)
products_bp = Blueprint("products", __name__)

# ── Demo data generator ────────────────────────────────────────
def _demo_product_data():
    """Synthetic product analytics when Snowflake is unavailable."""
    CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Sports & Outdoors", "Beauty & Health"]
    SUBCATS     = {
        "Electronics":       ["Laptops","Phones","Tablets","Accessories"],
        "Clothing":          ["Shirts","Pants","Shoes","Jackets"],
        "Home & Kitchen":    ["Cookware","Furniture","Decor","Appliances"],
        "Sports & Outdoors": ["Fitness","Camping","Cycling","Water Sports"],
        "Beauty & Health":   ["Skincare","Haircare","Supplements","Wellness"],
    }
    PRODUCTS = [
        "ProMax Laptop 15\"","UltraPhone X","SmartTab Pro","Wireless Earbuds Elite",
        "Running Shoes Pro","Yoga Mat Premium","Coffee Maker Deluxe","Vitamin C 1000mg",
        "Winter Jacket XL","Cast Iron Skillet","Protein Powder Vanilla","Tent 4-Person",
        "Gaming Keyboard RGB","Moisturizer SPF50","Cycling Helmet MIPS","Standing Desk Converter",
        "Bluetooth Speaker 360","Trail Running Shorts","Air Purifier HEPA","Resistance Bands Set"
    ]
    rng = random.Random(42)

    # Categories summary
    cat_rev  = {c: rng.randint(180_000, 620_000) for c in CATEGORIES}
    cat_data = [
        {
            "category":  c,
            "revenue":   cat_rev[c],
            "units":     rng.randint(1500, 8000),
            "avg_margin": round(rng.uniform(22, 52), 1)
        }
        for c in CATEGORIES
    ]

    # Top 20 products
    top_products = []
    for p in PRODUCTS:
        cat = rng.choice(CATEGORIES)
        our_price  = round(rng.uniform(15, 450), 2)
        comp_price = round(our_price * rng.uniform(0.85, 1.20), 2)
        top_products.append({
            "product_name":      p,
            "category":          cat,
            "revenue":           rng.randint(8_000, 95_000),
            "units_sold":        rng.randint(50, 800),
            "avg_margin":        round(rng.uniform(18, 58), 1),
            "avg_price":         our_price,
            "competitor_price":  comp_price
        })
    top_products.sort(key=lambda x: x["revenue"], reverse=True)

    # Competitor scatter points
    competitor = [
        {"our_price": p["avg_price"], "competitor_price": p["competitor_price"], "category": p["category"]}
        for p in top_products
    ]

    # KPIs
    price_adv = sum(1 for p in top_products if p["avg_price"] < p["competitor_price"])
    kpis = {
        "total_products":      500,
        "avg_margin":          round(sum(c["avg_margin"] for c in cat_data) / len(cat_data), 1),
        "top_category":        max(cat_data, key=lambda x: x["revenue"])["category"],
        "price_advantage_count": price_adv
    }

    return {"kpis": kpis, "categories": cat_data, "top_products": top_products, "competitor": competitor}


# ── Page route ─────────────────────────────────────────────────
@products_bp.route("/")
def products_page():
    return render_template(
        "products.html",
        active_page="products",
        is_demo=not snowflake_service.is_connected()
    )


# ── JSON API ───────────────────────────────────────────────────
@products_bp.route("/api/data")
def products_api():
    try:
        if not snowflake_service.is_connected():
            return jsonify(_demo_product_data())

        # Category summary
        cat_sql = """
            SELECT
                dp.CATEGORY,
                ROUND(SUM(fs.NET_REVENUE), 0)     AS revenue,
                SUM(fs.QUANTITY)                  AS units,
                ROUND(AVG(fs.MARGIN_PCT), 1)      AS avg_margin
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_PRODUCT dp ON fs.PRODUCT_SK = dp.PRODUCT_SK
            GROUP BY dp.CATEGORY
            ORDER BY revenue DESC
        """
        cat_df = snowflake_service.query(cat_sql)

        # Top 20 products
        prod_sql = """
            SELECT
                dp.PRODUCT_NAME,
                dp.CATEGORY,
                ROUND(SUM(fs.NET_REVENUE), 0)           AS revenue,
                SUM(fs.QUANTITY)                        AS units_sold,
                ROUND(AVG(fs.MARGIN_PCT), 1)            AS avg_margin,
                ROUND(AVG(fs.UNIT_PRICE), 2)            AS avg_price,
                ROUND(AVG(dp.COMPETITOR_PRICE), 2)      AS competitor_price
            FROM ANALYTICS.FCT_SALES fs
            JOIN ANALYTICS.DIM_PRODUCT dp ON fs.PRODUCT_SK = dp.PRODUCT_SK
            GROUP BY dp.PRODUCT_NAME, dp.CATEGORY
            ORDER BY revenue DESC
            LIMIT 20
        """
        prod_df = snowflake_service.query(prod_sql)

        categories   = cat_df.to_dict(orient="records")
        top_products = prod_df.to_dict(orient="records")
        competitor   = [
            {"our_price": p["avg_price"], "competitor_price": p["competitor_price"], "category": p["category"]}
            for p in top_products if p.get("competitor_price")
        ]

        price_adv = sum(1 for p in top_products if p.get("avg_price") and p.get("competitor_price") and p["avg_price"] < p["competitor_price"])
        kpis = {
            "total_products":        500,
            "avg_margin":            round(sum(c["avg_margin"] for c in categories) / max(len(categories), 1), 1),
            "top_category":          categories[0]["category"] if categories else "N/A",
            "price_advantage_count": price_adv
        }

        return jsonify({"kpis": kpis, "categories": categories, "top_products": top_products, "competitor": competitor})

    except Exception as e:
        log.error("Products API error: %s", e)
        return jsonify(_demo_product_data())
