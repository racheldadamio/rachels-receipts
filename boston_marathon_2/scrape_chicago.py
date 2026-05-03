"""
Chicago Marathon historical results scraper.

Uses chicago-history.r.mikatiming.com POST API.
Year is selected via the `event_main_group` parameter.
Items are filtered to marathon-only by the `event-MAR_*` CSS class.

Half splits are NOT available in the list view; a separate sample scraper
is provided in scrape_chicago_splits.py for negative-split analysis.

Output: chicago_results_YYYY.csv with columns:
  place_overall, place_gender, name, idp, bib, age_bracket, finish_net, event_code
"""

import csv
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://chicago-history.r.mikatiming.com/2024/"
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://chicago-history.r.mikatiming.com/2024/",
}
RESULTS_PER_PAGE = 1000


def fetch_page(year: int, page: int, retries: int = 6) -> str:
    for attempt in range(retries):
        try:
            session = requests.Session()
            resp = session.get(
                BASE,
                params={
                    "content": "list",
                    "event": "R",
                    "event_main_group": str(year),
                    "num_results": RESULTS_PER_PAGE,
                    "page": page,
                    "lang": "EN_CAP",
                    "pid": "list",
                },
                headers=HEADERS,
                timeout=90,
            )
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.exceptions.ConnectionError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.text
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.ChunkedEncodingError) as e:
            wait = 10 * 2 ** attempt
            print(f"  Retry {attempt + 1} after {wait}s... ({e})")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch page {page} for year {year} after {retries} attempts")


def parse_items(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for li in soup.find_all("li"):
        cls = li.get("class", [])
        if (
            "list-group-item" not in cls
            or "row" not in cls
            or "list-group-header" in cls
        ):
            continue
        # Marathon runners only
        if not any(c.startswith("event-MAR") for c in cls):
            continue

        event_code = next(
            (c.replace("event-", "") for c in cls if c.startswith("event-")), ""
        )

        a = li.find("a")
        if not a:
            continue
        name = a.text.strip()
        href = a.get("href", "")
        p = dict(urllib.parse.parse_qsl(href.split("?", 1)[-1]))
        idp = p.get("idp", "")

        places = li.find_all("div", class_="type-place")
        place_overall = places[0].get_text(strip=True) if places else ""
        place_gender = places[1].get_text(strip=True) if len(places) > 1 else ""

        bib_div = li.find("div", class_="type-field")
        bib = bib_div.get_text(strip=True) if bib_div else ""

        age_div = li.find("div", class_="type-age_class")
        age_bracket = age_div.get_text(strip=True) if age_div else ""

        time_divs = li.find_all("div", class_="type-time")
        finish_net = time_divs[-1].get_text(strip=True) if time_divs else ""

        rows.append(
            {
                "place_overall": place_overall,
                "place_gender": place_gender,
                "name": name,
                "idp": idp,
                "bib": bib,
                "age_bracket": age_bracket,
                "finish_net": finish_net,
                "event_code": event_code,
            }
        )
    return rows


def get_total_count(html: str) -> int:
    import re
    soup = BeautifulSoup(html, "html.parser")
    info = soup.find("ul", class_="list-info")
    if not info:
        return 0
    m = re.search(r"([\d,]+)\s+Results", info.get_text())
    return int(m.group(1).replace(",", "")) if m else 0


def scrape_year(year: int) -> None:
    out_path = Path(f"chicago_results_{year}.csv")
    if out_path.exists():
        print(f"{year}: already exists, skipping.")
        return

    print(f"Scraping {year}...")
    html = fetch_page(year, 1)
    total = get_total_count(html)
    total_pages = (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    print(f"  Total results: {total:,}, pages: {total_pages}")

    all_rows = parse_items(html)
    for page in range(2, total_pages + 1):
        if page % 10 == 0:
            print(f"  Page {page}/{total_pages}, rows so far: {len(all_rows):,}")
        html = fetch_page(year, page)
        all_rows.extend(parse_items(html))
        time.sleep(2)

    # Dedup by idp (last pagination page overlaps)
    seen: set[str] = set()
    deduped = []
    for row in all_rows:
        if row["idp"] not in seen:
            seen.add(row["idp"])
            deduped.append(row)

    print(f"  {len(deduped):,} unique marathon runners after dedup")

    if deduped:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(deduped[0].keys()))
            writer.writeheader()
            writer.writerows(deduped)
        print(f"  Saved → {out_path}")


BASE_2025 = "https://results.chicagomarathon.com/2025/"


def fetch_page_2025(page: int, retries: int = 6) -> str:
    for attempt in range(retries):
        try:
            session = requests.Session()
            resp = session.get(
                BASE_2025,
                params={
                    "content": "list",
                    "event": "MAR",
                    "num_results": RESULTS_PER_PAGE,
                    "page": page,
                    "lang": "EN_CAP",
                    "pid": "list",
                },
                headers=HEADERS,
                timeout=90,
            )
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.exceptions.ConnectionError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.text
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.ChunkedEncodingError) as e:
            wait = 10 * 2 ** attempt
            print(f"  Retry {attempt + 1} after {wait}s... ({e})")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch 2025 page {page} after {retries} attempts")


def parse_items_2025(html: str) -> list[dict]:
    """Parse 2025 items — same structure but includes half split in list view."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for li in soup.find_all("li"):
        cls = li.get("class", [])
        if "list-group-item" not in cls or "row" not in cls or "list-group-header" in cls:
            continue

        a = li.find("a")
        if not a:
            continue
        name = a.text.strip()
        href = a.get("href", "")
        p = dict(urllib.parse.parse_qsl(href.split("?", 1)[-1]))
        idp = p.get("idp", "")

        places = li.find_all("div", class_="type-place")
        place_overall = places[0].get_text(strip=True) if places else ""
        place_gender = places[1].get_text(strip=True) if len(places) > 1 else ""

        bib_div = li.find("div", class_="type-field")
        bib = bib_div.get_text(strip=True) if bib_div else ""

        age_div = li.find("div", class_="type-age_class")
        age_bracket = age_div.get_text(strip=True) if age_div else ""

        time_divs = li.find_all("div", class_="type-time")
        half = time_divs[0].get_text(strip=True) if len(time_divs) >= 2 else ""
        finish_net = time_divs[-1].get_text(strip=True) if time_divs else ""

        rows.append(
            {
                "place_overall": place_overall,
                "place_gender": place_gender,
                "name": name,
                "idp": idp,
                "bib": bib,
                "age_bracket": age_bracket,
                "half": half,
                "finish_net": finish_net,
                "event_code": "MAR",
            }
        )
    return rows


def get_total_pages_2025(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    pag = soup.find("ul", class_="pagination")
    if not pag:
        return 1
    page_nums = [int(a.text.strip()) for a in pag.find_all("a") if a.text.strip().isdigit()]
    return max(page_nums) if page_nums else 1


def scrape_year_2025() -> None:
    out_path = Path("chicago_results_2025.csv")
    if out_path.exists():
        print("2025: already exists, skipping.")
        return

    print("Scraping 2025 (results.chicagomarathon.com)...")
    html = fetch_page_2025(1)
    total_pages = get_total_pages_2025(html)
    print(f"  Total pages: {total_pages}")

    all_rows = parse_items_2025(html)
    for page in range(2, total_pages + 1):
        if page % 10 == 0:
            print(f"  Page {page}/{total_pages}, rows so far: {len(all_rows):,}")
        html = fetch_page_2025(page)
        all_rows.extend(parse_items_2025(html))
        time.sleep(2)

    seen: set[str] = set()
    deduped = []
    for row in all_rows:
        if row["idp"] not in seen:
            seen.add(row["idp"])
            deduped.append(row)

    print(f"  {len(deduped):,} unique marathon runners after dedup")

    if deduped:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(deduped[0].keys()))
            writer.writeheader()
            writer.writerows(deduped)
        print(f"  Saved → {out_path}")


if __name__ == "__main__":
    import sys

    years = [2018, 2019, 2021, 2022, 2023, 2024]
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]

    for yr in years:
        if yr == 2025:
            scrape_year_2025()
        else:
            scrape_year(yr)
        time.sleep(2)
