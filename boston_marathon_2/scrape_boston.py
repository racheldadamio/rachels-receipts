#!/usr/bin/env python3
"""
Scrape Boston Marathon results from boston.r.mikatiming.com

Uses the site's internal POST endpoint (no browser / Selenium needed).

Usage:
    python scrape_boston.py --year 2024
    python scrape_boston.py --year 2024 2023 2022
    python scrape_boston.py --year 2024 --event W --output ./data
"""

import argparse
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://boston.r.mikatiming.com/{year}/"
RESULTS_PER_PAGE = 1000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://boston.r.mikatiming.com/",
}


def fetch_page(year, event, page, retries=5):
    """Fetch one page of results, retrying with backoff on timeout."""
    for attempt in range(retries):
        try:
            session = requests.Session()
            resp = session.post(
                BASE_URL.format(year=year),
                data={
                    "content": "list",
                    "event": event,
                    "num_results": RESULTS_PER_PAGE,
                    "page": page,
                },
                headers=HEADERS,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.text
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            wait = 5 * 2 ** attempt  # 5s, 10s, 20s, 40s, 80s
            print(f" timeout (attempt {attempt + 1}/{retries}), retrying in {wait}s...", end="", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch page {page} after {retries} attempts")


def parse_total(soup):
    span = soup.find("span", class_="str_num")
    if span:
        m = re.search(r"([\d,]+)", span.text)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def parse_result_item(li):
    """Extract fields from a single <li> result row."""
    row = {}

    # Place fields: [0]=Overall, [1]=Gender, [2]=Division
    places = li.find_all("div", class_="type-place")
    labels = ["place_overall", "place_gender", "place_division"]
    for i, div in enumerate(places[:3]):
        row[labels[i]] = div.get_text(strip=True)

    # Name + individual ID
    name_tag = li.find("h4", class_="type-fullname")
    if name_tag:
        row["name"] = name_tag.get_text(strip=True)
        a = name_tag.find("a")
        if a:
            m = re.search(r"idp=([^&]+)", a.get("href", ""))
            row["idp"] = m.group(1) if m else ""

    # Team + BIB — both are type-field divs; BIB has numeric text, team has dashes or a name
    field_divs = li.find_all("div", class_="type-field")
    for div in field_divs:
        label_div = div.find("div", class_="list-label")
        label = label_div.get_text(strip=True).upper() if label_div else ""
        # Remove the label text to get the value
        if label_div:
            label_div.extract()
        value = div.get_text(strip=True)
        if label == "TEAM":
            row["team"] = value
        elif label == "BIB":
            row["bib"] = value
        # Fallback: no labels on wide screens, use position
    if "team" not in row or "bib" not in row:
        for i, div in enumerate(field_divs[:2]):
            value = div.get_text(strip=True)
            if i == 0 and "team" not in row:
                row["team"] = value
            elif i == 1 and "bib" not in row:
                row["bib"] = value

    # Time splits: label inside each div tells us which split it is
    for split_div in li.find_all("div", class_="type-time"):
        label_div = split_div.find("div", class_="list-label")
        label = label_div.get_text(strip=True) if label_div else ""
        if label_div:
            label_div.extract()
        value = split_div.get_text(strip=True)
        key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_") if label else f"time_{len(row)}"
        row[key] = value

    return row


def scrape_year(year, event="R", output_dir=".", delay=2.0):
    all_rows = []
    page = 0
    total = None

    print(f"\nScraping {year} (event={event})...")

    while True:
        print(f"  page {page} ...", end="", flush=True)
        html = fetch_page(year, event, page)
        soup = BeautifulSoup(html, "html.parser")

        if total is None:
            total = parse_total(soup)
            if total:
                pages_needed = -(-total // RESULTS_PER_PAGE)  # ceiling div
                print(f" [{total:,} total results, ~{pages_needed} pages]")

        result_lis = [
            li for li in soup.find_all("li", class_=lambda c: c and "list-group-item" in c and "row" in c)
            if "list-group-header" not in (li.get("class") or [])
        ]

        if not result_lis:
            print(" no results, stopping.")
            break

        for li in result_lis:
            all_rows.append(parse_result_item(li))

        print(f" {len(result_lis)} rows (total so far: {len(all_rows):,})")

        if total and len(all_rows) >= total:
            break
        if len(result_lis) < RESULTS_PER_PAGE:
            break

        page += 1
        time.sleep(delay)

    if not all_rows:
        print("  No results found.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["idp"]).reset_index(drop=True)
    out_path = Path(output_dir) / f"results_{year}.csv"
    df.to_csv(out_path, index=False)
    print(f"  Saved {len(df):,} rows -> {out_path}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Boston Marathon results")
    parser.add_argument("--year", nargs="+", type=int, default=[2024])
    parser.add_argument("--event", default="R", choices=["R", "W", "H"],
                        help="R=Runners, W=Wheelchairs, H=Handcycles")
    parser.add_argument("--output", default=".", help="Output directory")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between page requests (default: 2.0)")
    args = parser.parse_args()

    Path(args.output).mkdir(parents=True, exist_ok=True)
    for year in args.year:
        scrape_year(year, event=args.event, output_dir=args.output, delay=args.delay)
