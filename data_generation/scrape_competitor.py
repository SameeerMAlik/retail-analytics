"""
Enterprise Retail Analytics Engine
====================================
Competitor Price Scraper
Description: Scrapes the local competitor_site.html using BeautifulSoup
             and saves structured data to competitor_prices.csv
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "generated_data"
HTML_FILE  = BASE_DIR / "competitor_site.html"


def parse_price(price_str: str) -> float:
    """
    Convert price string like '$1,249.00' to float 1249.0.
    Handles currency symbols, commas, whitespace.
    """
    cleaned = re.sub(r"[^\d.]", "", price_str.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        log.warning("Could not parse price: %s", price_str)
        return 0.0


def scrape_competitor_prices(html_path: Path) -> pd.DataFrame:
    """
    Parse all product tables from the competitor HTML file.
    Returns a DataFrame with columns:
      - product_name
      - category
      - competitor_price
      - stock_status
      - scraped_at
    """
    log.info("📄 Reading competitor HTML: %s", html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Section headers (h2 tags) map to table sections
    section_map = {}
    for h2 in soup.find_all("h2"):
        table = h2.find_next_sibling("table")
        if table:
            section_map[h2.text.strip()] = table

    log.info("Found %d product sections: %s", len(section_map), list(section_map.keys()))

    records = []
    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for section_name, table in section_map.items():
        rows = table.find("tbody").find_all("tr")
        log.info("  Section '%s': %d products", section_name, len(rows))

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue  # Skip malformed rows

            product_name   = cols[0].text.strip()
            category_text  = cols[1].text.strip()
            price_text     = cols[2].text.strip()
            stock_status   = cols[3].text.strip() if len(cols) > 3 else "Unknown"

            competitor_price = parse_price(price_text)

            records.append({
                "product_name":      product_name,
                "category":          category_text,
                "section":           section_name,
                "competitor_price":  competitor_price,
                "stock_status":      stock_status,
                "scraped_at":        scraped_at,
                "source":            "CompeteX Store",
            })

    df = pd.DataFrame(records)
    return df


def validate_scrape(df: pd.DataFrame) -> bool:
    """Basic validation: ensure prices are positive and no empty names."""
    issues = []
    if df["product_name"].str.strip().eq("").any():
        issues.append("Empty product names found")
    if (df["competitor_price"] <= 0).any():
        issues.append("Non-positive prices found")
    if df.duplicated(subset=["product_name", "category"]).any():
        issues.append("Duplicate entries found")

    if issues:
        for issue in issues:
            log.warning("⚠️  Validation issue: %s", issue)
        return False

    log.info("✅ Validation passed: %d products scraped cleanly", len(df))
    return True


def main():
    log.info("=" * 60)
    log.info("Competitor Price Scraper — Starting")
    log.info("=" * 60)

    if not HTML_FILE.exists():
        log.error("❌ HTML file not found: %s", HTML_FILE)
        raise FileNotFoundError(f"competitor_site.html not found at {HTML_FILE}")

    # Scrape
    df = scrape_competitor_prices(HTML_FILE)
    log.info("Scraped %d total products", len(df))

    # Validate
    validate_scrape(df)

    # Save
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "competitor_prices.csv"
    df.to_csv(output_path, index=False)
    log.info("💾 Saved: %s", output_path)

    # Preview
    log.info("\nSample scraped data:")
    print(df[["product_name", "section", "competitor_price", "stock_status"]].head(10).to_string(index=False))

    log.info("=" * 60)
    log.info("✅ Scraping complete. %d competitor prices saved.", len(df))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
