"""
Enterprise Retail Analytics Engine
====================================
Snowflake Service Layer
Description: Manages Snowflake connections, query execution, and caching.
             Uses connection pooling pattern for efficiency.
"""

import os
import logging
import hashlib
import time
from functools import lru_cache
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

# ─── In-memory cache (TTL-based) ──────────────────────────────────────────────
_CACHE: dict = {}
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL", 300))  # 5 minutes default


def _cache_key(sql: str, params: tuple = None) -> str:
    """Generate a hash-based cache key for a SQL query."""
    content = sql + str(params or "")
    return hashlib.md5(content.encode()).hexdigest()


def _get_cached(key: str) -> Optional[pd.DataFrame]:
    """Return cached result if not expired."""
    if key in _CACHE:
        data, timestamp = _CACHE[key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return data
        del _CACHE[key]
    return None


def _set_cache(key: str, data: pd.DataFrame):
    """Store result in cache with current timestamp."""
    _CACHE[key] = (data, time.time())


class SnowflakeService:
    """
    Manages Snowflake connectivity for the Flask application.
    Implements connection retry, query validation, and result caching.
    """

    def __init__(self):
        self._conn = None
        self._connect()

    def _connect(self):
        """Establish Snowflake connection. Gracefully handles missing credentials."""
        try:
            required_vars = ["SF_ACCOUNT", "SF_USER", "SF_PASSWORD", "SF_WAREHOUSE",
                             "SF_DATABASE", "SF_ROLE"]
            missing = [v for v in required_vars if not os.getenv(v)]

            if missing:
                log.warning("Snowflake credentials missing: %s. Running in DEMO MODE.", missing)
                self._conn = None
                return

            try:
                import snowflake.connector
            except ImportError:
                log.warning("snowflake-connector not installed. Running in DEMO MODE.")
                self._conn = None
                return

            self._conn = snowflake.connector.connect(
                account=os.getenv("SF_ACCOUNT"),
                user=os.getenv("SF_USER"),
                password=os.getenv("SF_PASSWORD"),
                warehouse=os.getenv("SF_WAREHOUSE"),
                database=os.getenv("SF_DATABASE"),
                schema=os.getenv("SF_SCHEMA", "ANALYTICS"),
                role=os.getenv("SF_ROLE"),
            )
            log.info("Snowflake connected: account=%s", os.getenv("SF_ACCOUNT"))

        except Exception as e:
            log.warning("Snowflake connection failed: %s. Running in DEMO MODE.", str(e))
            self._conn = None

    def is_connected(self) -> bool:
        """Check if Snowflake connection is active."""
        return self._conn is not None

    def query(self, sql: str, use_cache: bool = True) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.
        Uses in-memory caching to reduce repeated Snowflake calls.

        Args:
            sql: SELECT query string
            use_cache: Whether to use result cache

        Returns:
            pandas DataFrame with query results
        """
        # Check cache first
        cache_key = _cache_key(sql)
        if use_cache:
            cached = _get_cached(cache_key)
            if cached is not None:
                log.debug("Cache hit for query: %s...", sql[:60])
                return cached

        if not self.is_connected():
            # Return demo data when not connected to Snowflake
            log.debug("DEMO MODE: returning mock data for query")
            return self._get_demo_data(sql)

        try:
            cur = self._conn.cursor()
            cur.execute(sql)
            df = cur.fetch_pandas_all()
            cur.close()

            if use_cache:
                _set_cache(cache_key, df)

            log.debug("Query returned %d rows", len(df))
            return df

        except snowflake.connector.errors.ProgrammingError as e:
            log.error("SQL Error: %s | Query: %s...", str(e), sql[:100])
            raise

        except Exception as e:
            log.error("Unexpected error: %s", str(e))
            # Try reconnecting once
            self._connect()
            raise

    def execute_safe_query(self, sql: str) -> tuple[pd.DataFrame, str]:
        """
        Execute a user-provided SQL query with safety validation.
        Only SELECT queries are permitted (AI SQL feature).

        Returns:
            (DataFrame, error_message) — error_message is None on success
        """
        # Safety check: only allow SELECT statements
        sql_clean = sql.strip().upper()

        blocked_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE",
                            "ALTER", "TRUNCATE", "GRANT", "REVOKE", "EXECUTE",
                            "EXEC", "XP_", "SP_", "--", ";DROP", "UNION DROP"]

        for keyword in blocked_keywords:
            if keyword in sql_clean:
                log.warning("⚠️  Blocked SQL keyword detected: %s", keyword)
                return pd.DataFrame(), f"Query blocked: dangerous keyword '{keyword}' detected"

        if not sql_clean.startswith("SELECT"):
            return pd.DataFrame(), "Only SELECT queries are permitted"

        try:
            df = self.query(sql, use_cache=False)
            # Limit output to 500 rows for dashboard display
            if len(df) > 500:
                df = df.head(500)
                log.info("Result truncated to 500 rows for display")
            return df, None
        except Exception as e:
            return pd.DataFrame(), f"Query execution error: {str(e)}"

    def _get_demo_data(self, sql: str) -> pd.DataFrame:
        """
        Generate synthetic demo data when Snowflake is not available.
        Provides realistic preview data for the dashboard.
        """
        import numpy as np
        from datetime import datetime, timedelta
        import random

        sql_upper = sql.upper()

        # Revenue trend data
        if "REVENUE" in sql_upper and "DATE" in sql_upper:
            dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
            base = 45000
            return pd.DataFrame({
                "ORDER_DATE":    dates,
                "NET_REVENUE":   [base * (1 + 0.3 * np.sin(i/30) + 0.5 * (i/365)) + random.uniform(-2000, 2000)
                                  for i in range(len(dates))],
                "GROSS_PROFIT":  [base * 0.35 * (1 + 0.3 * np.sin(i/30)) for i in range(len(dates))],
                "NUM_ORDERS":    [random.randint(120, 280) for _ in dates],
                "MARGIN_PCT":    [random.uniform(28, 42) for _ in dates],
            })

        # Category data
        if "CATEGORY" in sql_upper:
            categories = ["Electronics", "Clothing", "Home & Kitchen", "Sports & Outdoors", "Beauty & Health"]
            return pd.DataFrame({
                "CATEGORY":         categories,
                "TOTAL_REVENUE":    [4250000, 2890000, 1950000, 1340000, 980000],
                "TOTAL_PROFIT":     [1487500, 867000, 682500, 469000, 343000],
                "NUM_ORDERS":       [18500, 14200, 9800, 6700, 4900],
                "AVG_MARGIN_PCT":   [35.0, 30.0, 35.0, 35.0, 35.0],
                "REVENUE_SHARE_PCT":[37.5, 25.5, 17.2, 11.8, 8.6],
            })

        # Customer data
        if "CUSTOMER" in sql_upper or "CLV" in sql_upper:
            return pd.DataFrame({
                "FULL_NAME":      ["Emma Johnson", "Liam Chen", "Sofia Martinez", "Noah Williams", "Ava Thompson"],
                "COUNTRY":        ["United States", "Singapore", "Spain", "Canada", "Australia"],
                "TOTAL_REVENUE":  [12500.50, 11200.00, 9800.75, 8950.25, 8200.00],
                "TOTAL_ORDERS":   [45, 38, 32, 29, 27],
                "CLV_TIER":       ["Champions", "Champions", "Loyal", "Loyal", "Potential Loyal"],
            })

        # Default empty DataFrame
        return pd.DataFrame({"MESSAGE": ["No demo data available for this query"]})

    def close(self):
        """Close the Snowflake connection."""
        if self._conn:
            self._conn.close()
            log.info("Snowflake connection closed")


# ─── Singleton Instance ───────────────────────────────────────────────────────
# Initialized once when the module is imported
snowflake_service = SnowflakeService()
