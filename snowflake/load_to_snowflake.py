"""
Enterprise Retail Analytics Engine
====================================
Snowflake Data Loader
Description: Loads all CSV files into Snowflake staging schema.
             Uses snowflake-connector-python with write_pandas for efficiency.
Usage: python load_to_snowflake.py
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

# ─── Load Environment Variables ───────────────────────────────────────────────
load_dotenv(Path(__file__).parent.parent / ".env")

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"snowflake_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
log = logging.getLogger(__name__)

# ─── Data Directory ───────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data_generation" / "generated_data"

# ─── Table Configurations ─────────────────────────────────────────────────────
# Maps: CSV filename → (Snowflake table name, schema, expected row count)
TABLE_CONFIG = {
    "customers.csv":         ("STG_CUSTOMERS",        "STAGING",  10_000),
    "products.csv":          ("STG_PRODUCTS",          "STAGING",  500),
    "orders.csv":            ("STG_ORDERS",            "STAGING",  50_000),
    "order_items.csv":       ("STG_ORDER_ITEMS",       "STAGING",  150_000),
    "competitor_prices.csv": ("STG_COMPETITOR_PRICES", "STAGING",  None),
}

# Column name mapping: lowercase CSV → uppercase Snowflake convention
COLUMN_MAP = {
    "customer_id":       "CUSTOMER_ID",
    "full_name":         "FULL_NAME",
    "gender":            "GENDER",
    "email":             "EMAIL",
    "city":              "CITY",
    "country":           "COUNTRY",
    "registration_date": "REGISTRATION_DATE",
    "age_group":         "AGE_GROUP",
    "product_id":        "PRODUCT_ID",
    "category":          "CATEGORY",
    "subcategory":       "SUBCATEGORY",
    "product_name":      "PRODUCT_NAME",
    "retail_price":      "RETAIL_PRICE",
    "base_cost":         "BASE_COST",
    "supplier_name":     "SUPPLIER_NAME",
    "order_id":          "ORDER_ID",
    "order_date":        "ORDER_DATE",
    "payment_method":    "PAYMENT_METHOD",
    "order_status":      "ORDER_STATUS",
    "order_item_id":     "ORDER_ITEM_ID",
    "quantity":          "QUANTITY",
    "unit_price":        "UNIT_PRICE",
    "discount":          "DISCOUNT",
    "competitor_price":  "COMPETITOR_PRICE",
    "stock_status":      "STOCK_STATUS",
    "scraped_at":        "SCRAPED_AT",
    "source":            "SOURCE",
    "section":           "SECTION",
}


def get_snowflake_connection():
    """
    Create and return a Snowflake connection using environment variables.
    Required env vars: SF_ACCOUNT, SF_USER, SF_PASSWORD, SF_WAREHOUSE,
                       SF_DATABASE, SF_ROLE
    """
    required = ["SF_ACCOUNT", "SF_USER", "SF_PASSWORD", "SF_WAREHOUSE",
                "SF_DATABASE", "SF_ROLE"]

    missing = [v for v in required if not os.getenv(v)]
    if missing:
        log.error("❌ Missing environment variables: %s", missing)
        log.error("Please configure your .env file — see .env.example")
        sys.exit(1)

    log.info("Connecting to Snowflake: account=%s, db=%s",
             os.getenv("SF_ACCOUNT"), os.getenv("SF_DATABASE"))

    conn = snowflake.connector.connect(
        account=os.getenv("SF_ACCOUNT"),
        user=os.getenv("SF_USER"),
        password=os.getenv("SF_PASSWORD"),
        warehouse=os.getenv("SF_WAREHOUSE"),
        database=os.getenv("SF_DATABASE"),
        role=os.getenv("SF_ROLE"),
        session_parameters={"QUERY_TAG": "RETAIL_ANALYTICS_ETL"}
    )
    log.info("✅ Snowflake connection established")
    return conn


def truncate_table(conn, schema: str, table: str):
    """Truncate a staging table before reload (idempotent loads)."""
    sql = f"TRUNCATE TABLE IF EXISTS {schema}.{table}"
    cur = conn.cursor()
    cur.execute(sql)
    log.info("  Truncated: %s.%s", schema, table)


def validate_row_count(conn, schema: str, table: str, expected: int) -> bool:
    """Verify actual loaded rows match expected count."""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
    actual = cur.fetchone()[0]

    if expected and actual != expected:
        log.warning("  ⚠️  %s.%s: expected=%d, actual=%d", schema, table, expected, actual)
        return False
    log.info("  ✅ %s.%s: %d rows loaded", schema, table, actual)
    return True


def load_csv_to_snowflake(conn, csv_file: Path, table: str, schema: str,
                           expected_rows: int = None) -> dict:
    """
    Load a single CSV file into a Snowflake table.
    Returns a result dict with status and stats.
    """
    result = {
        "file":    csv_file.name,
        "table":   f"{schema}.{table}",
        "status":  "FAILED",
        "rows":    0,
        "elapsed": 0,
    }

    if not csv_file.exists():
        log.error("❌ File not found: %s", csv_file)
        return result

    start_time = datetime.now()
    log.info("\n📂 Loading: %s → %s.%s", csv_file.name, schema, table)

    try:
        # Read CSV
        df = pd.read_csv(csv_file, low_memory=False)
        log.info("  Read %d rows × %d columns", len(df), len(df.columns))

        # Rename columns to uppercase for Snowflake compatibility
        df.rename(columns={col: COLUMN_MAP.get(col, col.upper()) for col in df.columns},
                  inplace=True)

        # Clean up: convert date columns
        for col in df.columns:
            if "DATE" in col and df[col].dtype == object:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

        # Set target schema
        conn.cursor().execute(f"USE SCHEMA {schema}")

        # Truncate existing data
        truncate_table(conn, schema, table)

        # Write using write_pandas (chunked, efficient)
        success, nchunks, nrows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table,
            schema=schema,
            chunk_size=10_000,
            auto_create_table=False,
            overwrite=False,
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if success:
            result["status"]  = "SUCCESS"
            result["rows"]    = nrows
            result["elapsed"] = round(elapsed, 2)
            log.info("  ✅ Loaded %d rows in %.1fs (%d chunks)", nrows, elapsed, nchunks)

            # Validate count
            validate_row_count(conn, schema, table, expected_rows)
        else:
            log.error("  ❌ write_pandas returned failure for %s", table)

    except Exception as e:
        log.exception("  ❌ Error loading %s: %s", csv_file.name, str(e))
        result["error"] = str(e)

    return result


def run_post_load_sql(conn):
    """
    Execute basic post-load verification and analytics.
    Creates the date dimension if not exists via SQL.
    """
    log.info("\n🔧 Running post-load SQL procedures...")

    date_dim_sql = """
    INSERT INTO ANALYTICS.DIM_DATE
    SELECT
        TO_NUMBER(TO_CHAR(d.DATE_VALUE, 'YYYYMMDD'))      AS DATE_SK,
        d.DATE_VALUE                                        AS FULL_DATE,
        YEAR(d.DATE_VALUE)                                  AS YEAR,
        QUARTER(d.DATE_VALUE)                               AS QUARTER,
        MONTH(d.DATE_VALUE)                                 AS MONTH,
        MONTHNAME(d.DATE_VALUE)                             AS MONTH_NAME,
        WEEKOFYEAR(d.DATE_VALUE)                            AS WEEK,
        DAYOFWEEK(d.DATE_VALUE)                             AS DAY_OF_WEEK,
        DAYNAME(d.DATE_VALUE)                               AS DAY_NAME,
        CASE WHEN DAYOFWEEK(d.DATE_VALUE) IN (1, 7) THEN TRUE ELSE FALSE END AS IS_WEEKEND,
        FALSE                                               AS IS_HOLIDAY,
        CASE
            WHEN MONTH(d.DATE_VALUE) IN (12, 1, 2)  THEN 'Winter'
            WHEN MONTH(d.DATE_VALUE) IN (3, 4, 5)   THEN 'Spring'
            WHEN MONTH(d.DATE_VALUE) IN (6, 7, 8)   THEN 'Summer'
            ELSE 'Fall'
        END                                                 AS SEASON,
        'Q' || QUARTER(d.DATE_VALUE) || ' ' || YEAR(d.DATE_VALUE) AS FISCAL_QUARTER
    FROM (
        SELECT DATEADD(DAY, SEQ4(), '2022-01-01'::DATE) AS DATE_VALUE
        FROM TABLE(GENERATOR(ROWCOUNT => 1461))   -- 4 years: 2022-2025
    ) d
    WHERE NOT EXISTS (
        SELECT 1 FROM ANALYTICS.DIM_DATE WHERE DATE_SK = TO_NUMBER(TO_CHAR(d.DATE_VALUE, 'YYYYMMDD'))
    )
    """

    try:
        conn.cursor().execute("TRUNCATE TABLE ANALYTICS.DIM_DATE")
        conn.cursor().execute(date_dim_sql)
        log.info("  ✅ DIM_DATE populated (2022-2025)")
    except Exception as e:
        log.warning("  ⚠️  DIM_DATE: %s (may already be populated)", str(e))


def print_summary(results: list):
    """Print a formatted summary table of all load operations."""
    log.info("\n" + "=" * 65)
    log.info("SNOWFLAKE LOAD SUMMARY")
    log.info("=" * 65)
    log.info("%-35s %-10s %10s %8s", "TABLE", "STATUS", "ROWS", "SECS")
    log.info("-" * 65)

    total_rows = 0
    success_count = 0
    for r in results:
        status_icon = "✅" if r["status"] == "SUCCESS" else "❌"
        log.info("%-35s %s %-7s %10d %8.1f",
                 r["table"], status_icon, r["status"], r["rows"], r["elapsed"])
        total_rows += r["rows"]
        if r["status"] == "SUCCESS":
            success_count += 1

    log.info("-" * 65)
    log.info("TOTAL ROWS LOADED: %d | SUCCESS: %d/%d",
             total_rows, success_count, len(results))
    log.info("=" * 65)


def main():
    log.info("=" * 65)
    log.info("Enterprise Retail Analytics Engine — Snowflake Loader")
    log.info("Started: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("=" * 65)

    # Establish connection
    conn = get_snowflake_connection()

    results = []
    try:
        # Load each CSV file
        for csv_name, (table, schema, expected_rows) in TABLE_CONFIG.items():
            csv_path = DATA_DIR / csv_name
            result = load_csv_to_snowflake(conn, csv_path, table, schema, expected_rows)
            results.append(result)

        # Post-load: populate date dimension
        run_post_load_sql(conn)

    finally:
        conn.close()
        log.info("Snowflake connection closed.")

    # Summary
    print_summary(results)

    failed = [r for r in results if r["status"] == "FAILED"]
    if failed:
        log.error("❌ %d table(s) failed to load!", len(failed))
        sys.exit(1)
    else:
        log.info("✅ All tables loaded successfully!")


if __name__ == "__main__":
    main()
