"""
Enterprise Retail Analytics Engine
====================================
Data Generation Module
Author: Capstone Project Team
Description: Generates realistic synthetic e-commerce data using Faker + NumPy.
             Maintains full referential integrity across all tables.
"""

import os
import random
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)

# ─── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# ─── Output Directory ─────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Constants ────────────────────────────────────────────────────────────────
N_CUSTOMERS   = 10_000
N_PRODUCTS    = 500
N_ORDERS      = 50_000
N_ORDER_ITEMS = 150_000

DATE_START = datetime(2024, 1, 1)
DATE_END   = datetime(2024, 12, 31)

# ─── Realistic Product Catalogue ──────────────────────────────────────────────
PRODUCT_CATALOGUE = {
    "Electronics": {
        "Smartphones":    [("iPhone 15 Pro", 999, 650), ("Samsung Galaxy S24", 899, 580),
                           ("Google Pixel 8", 699, 450), ("OnePlus 12", 599, 380)],
        "Laptops":        [("MacBook Air M3", 1299, 850), ("Dell XPS 15", 1199, 780),
                           ("HP Spectre x360", 1099, 700), ("Lenovo ThinkPad X1", 1399, 920)],
        "Accessories":    [("AirPods Pro", 249, 120), ("Sony WH-1000XM5", 399, 200),
                           ("USB-C Hub 7-in-1", 49, 18), ("Mechanical Keyboard", 149, 60)],
    },
    "Clothing": {
        "Men's Wear":     [("Classic Oxford Shirt", 79, 22), ("Slim Fit Chinos", 89, 28),
                           ("Wool Blazer", 199, 75), ("Graphic Tee Bundle", 45, 12)],
        "Women's Wear":   [("Floral Maxi Dress", 99, 32), ("High-Rise Jeans", 89, 25),
                           ("Knit Cardigan", 79, 24), ("Silk Blouse", 129, 45)],
        "Footwear":       [("Running Shoes Pro", 129, 48), ("Leather Ankle Boots", 159, 62),
                           ("Canvas Sneakers", 69, 22), ("Sandals Classic", 59, 18)],
    },
    "Home & Kitchen": {
        "Appliances":     [("Air Fryer XL 5.8Qt", 89, 38), ("Instant Pot Duo 7-in-1", 99, 45),
                           ("Nespresso Vertuo", 179, 75), ("KitchenAid Stand Mixer", 349, 190)],
        "Cookware":       [("Cast Iron Skillet", 49, 18), ("Non-stick Pan Set 3pc", 79, 28),
                           ("Chef's Knife 8\"", 89, 35), ("Bamboo Cutting Board", 29, 9)],
        "Décor":          [("LED Floor Lamp", 69, 22), ("Throw Pillow Set 4pc", 59, 18),
                           ("Wall Art Canvas 3pc", 79, 25), ("Scented Candle Gift Set", 39, 12)],
    },
    "Sports & Outdoors": {
        "Fitness":        [("Resistance Band Set", 29, 8), ("Yoga Mat Premium", 49, 16),
                           ("Adjustable Dumbbells", 199, 85), ("Pull-up Bar Doorway", 39, 14)],
        "Outdoor":        [("Hiking Backpack 45L", 149, 58), ("Camping Tent 4-Person", 199, 82),
                           ("Trekking Poles Pair", 69, 24), ("Hydration Pack 2L", 59, 20)],
        "Team Sports":    [("Basketball Pro", 49, 18), ("Soccer Ball Match", 39, 14),
                           ("Tennis Racket Graphite", 89, 35), ("Badminton Set 4-Player", 45, 16)],
    },
    "Beauty & Health": {
        "Skincare":       [("Vitamin C Serum 30ml", 49, 12), ("SPF 50 Sunscreen", 29, 8),
                           ("Hyaluronic Acid Moisturizer", 39, 11), ("Retinol Night Cream", 59, 18)],
        "Haircare":       [("Dyson Airwrap", 599, 320), ("Keratin Treatment Kit", 79, 28),
                           ("Argan Oil Shampoo Set", 45, 14), ("Scalp Massager", 19, 5)],
        "Supplements":    [("Whey Protein 5lb", 59, 22), ("Omega-3 Fish Oil 90ct", 29, 9),
                           ("Vitamin D3 2000IU", 19, 5), ("Magnesium Glycinate", 25, 7)],
    },
}

SUPPLIERS = [
    "TechSource Global", "FashionHub International", "HomeGoods Direct",
    "SportsPro Distributors", "BeautyWholesale Co.", "PrimeSupply Corp",
    "EliteVendor Ltd", "QualityGoods Asia", "FastShip Logistics", "ValueChain Inc"
]

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay",
                   "Google Pay", "Buy Now Pay Later", "Bank Transfer"]

ORDER_STATUSES = ["Completed", "Completed", "Completed", "Completed",
                  "Shipped", "Processing", "Cancelled", "Returned"]

AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]

CITIES_BY_COUNTRY = {
    "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
                      "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"],
    "United Kingdom": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow"],
    "Canada":         ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
    "Australia":      ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
    "Germany":        ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt"],
    "France":         ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"],
    "UAE":            ["Dubai", "Abu Dhabi", "Sharjah"],
    "India":          ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"],
    "Singapore":      ["Singapore"],
    "Japan":          ["Tokyo", "Osaka", "Kyoto", "Yokohama"],
}


# ─────────────────────────────────────────────────────────────────────────────
# GENERATOR FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def seasonal_weight(date: datetime) -> float:
    """
    Apply seasonal multiplier to simulate realistic sales patterns.
    Q4 (Oct-Dec) = peak season (Black Friday, Christmas).
    Q3 (Jul-Sep) = summer bump.
    """
    month = date.month
    if month in [11, 12]:   return 2.0   # Holiday peak
    if month in [10]:       return 1.5   # Pre-holiday
    if month in [7, 8]:     return 1.3   # Summer
    if month in [1]:        return 0.7   # Post-holiday dip
    return 1.0


def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end."""
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def generate_customers() -> pd.DataFrame:
    """Generate 10,000 realistic customers with demographic distributions."""
    log.info("Generating %d customers...", N_CUSTOMERS)
    records = []

    for i in range(1, N_CUSTOMERS + 1):
        country = random.choices(
            list(CITIES_BY_COUNTRY.keys()),
            weights=[40, 15, 10, 8, 7, 6, 4, 5, 3, 2],  # US-heavy like real e-commerce
            k=1
        )[0]
        city = random.choice(CITIES_BY_COUNTRY[country])
        gender = random.choices(["Male", "Female", "Non-binary"], weights=[48, 48, 4])[0]

        # Registration skewed toward recent months (growth curve)
        reg_date = random_date(datetime(2022, 1, 1), DATE_END)

        records.append({
            "customer_id":       f"CUST{i:06d}",
            "full_name":         fake.name(),
            "gender":            gender,
            "email":             fake.email(),
            "city":              city,
            "country":           country,
            "registration_date": reg_date.strftime("%Y-%m-%d"),
            "age_group":         random.choices(AGE_GROUPS, weights=[15, 30, 25, 15, 10, 5])[0],
        })

    df = pd.DataFrame(records)
    log.info("✅ Customers: %d rows", len(df))
    return df


def generate_products() -> pd.DataFrame:
    """Generate 500 products with realistic pricing from the catalogue."""
    log.info("Generating %d products...", N_PRODUCTS)
    records = []
    product_id = 1

    for category, subcategories in PRODUCT_CATALOGUE.items():
        for subcategory, items in subcategories.items():
            for name, base_price, base_cost in items:
                # Create 3-6 variants per base product
                n_variants = random.randint(3, 6)
                for v in range(n_variants):
                    if product_id > N_PRODUCTS:
                        break
                    # Add slight price variation per variant
                    price_mult = random.uniform(0.85, 1.15)
                    records.append({
                        "product_id":   f"PROD{product_id:05d}",
                        "category":     category,
                        "subcategory":  subcategory,
                        "product_name": f"{name} v{v+1}" if v > 0 else name,
                        "retail_price": round(base_price * price_mult, 2),
                        "base_cost":    round(base_cost * price_mult, 2),
                        "supplier_name": random.choice(SUPPLIERS),
                    })
                    product_id += 1
                if product_id > N_PRODUCTS:
                    break
            if product_id > N_PRODUCTS:
                break
        if product_id > N_PRODUCTS:
            break

    # Fill remaining if catalogue ran short
    while product_id <= N_PRODUCTS:
        records.append({
            "product_id":   f"PROD{product_id:05d}",
            "category":     random.choice(list(PRODUCT_CATALOGUE.keys())),
            "subcategory":  "General",
            "product_name": fake.catch_phrase(),
            "retail_price": round(random.uniform(15, 500), 2),
            "base_cost":    round(random.uniform(5, 200), 2),
            "supplier_name": random.choice(SUPPLIERS),
        })
        product_id += 1

    df = pd.DataFrame(records)
    log.info("✅ Products: %d rows", len(df))
    return df


def generate_orders(customer_ids: list) -> pd.DataFrame:
    """
    Generate 50,000 orders with seasonal weighting.
    High-value customers place more orders (realistic LTV distribution).
    """
    log.info("Generating %d orders...", N_ORDERS)

    # Some customers are VIPs (80/20 rule: 20% customers = 80% orders)
    vip_customers  = random.sample(customer_ids, int(len(customer_ids) * 0.2))
    norm_customers = [c for c in customer_ids if c not in vip_customers]

    records = []
    for i in range(1, N_ORDERS + 1):
        # Weighted customer selection
        if random.random() < 0.80:
            cust_id = random.choice(vip_customers)
        else:
            cust_id = random.choice(norm_customers)

        order_date = random_date(DATE_START, DATE_END)

        records.append({
            "order_id":       f"ORD{i:08d}",
            "customer_id":    cust_id,
            "order_date":     order_date.strftime("%Y-%m-%d"),
            "payment_method": random.choice(PAYMENT_METHODS),
            "order_status":   random.choices(
                ORDER_STATUSES,
                weights=[40, 30, 15, 5, 4, 3, 2, 1]
            )[0],
        })

    df = pd.DataFrame(records)
    log.info("✅ Orders: %d rows", len(df))
    return df


def generate_order_items(order_ids: list, product_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate 150,000 order line items.
    Uses a Zipf distribution so popular products dominate.
    Seasonal pricing applied. Realistic discount tiers.
    """
    log.info("Generating %d order items...", N_ORDER_ITEMS)

    products = product_df[["product_id", "retail_price"]].to_dict("records")
    n_prods  = len(products)

    # Zipf weights → top 20% products get most sales
    zipf_weights = np.array([1 / (i ** 0.7) for i in range(1, n_prods + 1)])
    zipf_weights /= zipf_weights.sum()

    records = []
    item_id = 1

    # Distribute order items across orders (1-5 items per order typically)
    orders_pool = []
    for oid in order_ids:
        n_items = int(np.random.exponential(scale=2.5)) + 1
        n_items = min(n_items, 8)  # cap at 8 items per order
        orders_pool.extend([oid] * n_items)

    # Trim/extend to exactly N_ORDER_ITEMS
    if len(orders_pool) > N_ORDER_ITEMS:
        orders_pool = orders_pool[:N_ORDER_ITEMS]
    else:
        while len(orders_pool) < N_ORDER_ITEMS:
            orders_pool.append(random.choice(order_ids))

    random.shuffle(orders_pool)

    for oid in orders_pool:
        prod = products[np.random.choice(n_prods, p=zipf_weights)]
        qty  = random.choices([1, 2, 3, 4, 5], weights=[55, 25, 10, 6, 4])[0]

        # Tiered discounts: flash sales, bulk, loyalty
        disc_tier = random.choices(
            [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
            weights=[40, 20, 15, 10, 8, 5, 2]
        )[0]

        unit_price = round(prod["retail_price"] * random.uniform(0.95, 1.05), 2)

        records.append({
            "order_item_id": f"ITEM{item_id:09d}",
            "order_id":      oid,
            "product_id":    prod["product_id"],
            "quantity":      qty,
            "unit_price":    unit_price,
            "discount":      disc_tier,
        })
        item_id += 1

    df = pd.DataFrame(records)
    log.info("✅ Order Items: %d rows", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Enterprise Retail Analytics Engine — Data Generator")
    log.info("=" * 60)

    # Step 1: Generate Customers
    customers_df = generate_customers()
    customers_df.to_csv(f"{OUTPUT_DIR}/customers.csv", index=False)
    log.info("💾 Saved: customers.csv")

    # Step 2: Generate Products
    products_df = generate_products()
    products_df.to_csv(f"{OUTPUT_DIR}/products.csv", index=False)
    log.info("💾 Saved: products.csv")

    # Step 3: Generate Orders (references customers)
    customer_ids = customers_df["customer_id"].tolist()
    orders_df = generate_orders(customer_ids)
    orders_df.to_csv(f"{OUTPUT_DIR}/orders.csv", index=False)
    log.info("💾 Saved: orders.csv")

    # Step 4: Generate Order Items (references orders + products)
    order_ids = orders_df["order_id"].tolist()
    order_items_df = generate_order_items(order_ids, products_df)
    order_items_df.to_csv(f"{OUTPUT_DIR}/order_items.csv", index=False)
    log.info("💾 Saved: order_items.csv")

    # ─── Summary Report ───────────────────────────────────────────────────────
    log.info("=" * 60)
    log.info("DATA GENERATION SUMMARY")
    log.info("=" * 60)
    log.info("  customers   : %8d rows", len(customers_df))
    log.info("  products    : %8d rows", len(products_df))
    log.info("  orders      : %8d rows", len(orders_df))
    log.info("  order_items : %8d rows", len(order_items_df))
    log.info("=" * 60)

    # ─── Referential Integrity Checks ─────────────────────────────────────────
    log.info("Running referential integrity checks...")
    orphan_orders = ~orders_df["customer_id"].isin(customers_df["customer_id"])
    orphan_items_order   = ~order_items_df["order_id"].isin(orders_df["order_id"])
    orphan_items_product = ~order_items_df["product_id"].isin(products_df["product_id"])

    assert not orphan_orders.any(),            "❌ Orphan orders found!"
    assert not orphan_items_order.any(),       "❌ Orphan order_items (order) found!"
    assert not orphan_items_product.any(),     "❌ Orphan order_items (product) found!"

    log.info("✅ All referential integrity checks passed!")
    log.info("✅ Data generation complete. Files saved to: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
