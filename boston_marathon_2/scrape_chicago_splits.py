"""
Fetches half-marathon split times for a stratified random sample of Chicago
Marathon runners, one detail-page request per runner.

Chicago's list API does not include split times. This script reads the
chicago_results_YYYY.csv files produced by scrape_chicago.py and adds a
`half` column by hitting each runner's detail page.

Sample size: 600 runners per year, stratified across the full finish-time
distribution (sorted by finish time, every Nth runner). This gives a
margin of error of ≈ ±2 pp at the 95% confidence level for a ~5% rate.

Output: chicago_splits_YYYY.csv  (same columns as chicago_results + `half`)
"""

import csv
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://chicago-history.r.mikatiming.com/2024/"
SAMPLE_PER_YEAR = 600


def fetch_half(idp: str, event_code: str, session: requests.Session) -> str:
    """Return the elapsed half-marathon time (HH:MM:SS) or '' on failure."""
    for attempt in range(3):
        try:
            resp = session.get(
                BASE,
                params={
                    "content": "detail",
                    "pid": "list",
                    "idp": idp,
                    "event": event_code,
                    "lang": "EN_CAP",
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if cells and cells[0].get_text(strip=True) == "HALF":
                    # cells: [HALF, elapsed_time, ...]
                    return cells[1].get_text(strip=True) if len(cells) > 1 else ""
            return ""
        except Exception:
            time.sleep(2 * (attempt + 1))
    return ""


def scrape_splits_for_year(year: int) -> None:
    in_path = Path(f"chicago_results_{year}.csv")
    out_path = Path(f"chicago_splits_{year}.csv")

    if out_path.exists():
        print(f"{year}: splits already exist, skipping.")
        return
    if not in_path.exists():
        print(f"{year}: chicago_results_{year}.csv not found — run scrape_chicago.py first.")
        return

    with open(in_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Stratified sample: sort by finish_net, pick every Nth runner
    rows_sorted = sorted(rows, key=lambda r: r["finish_net"])
    n = len(rows_sorted)
    step = max(1, n // SAMPLE_PER_YEAR)
    sample = rows_sorted[::step][:SAMPLE_PER_YEAR]
    print(f"{year}: sampling {len(sample)} runners from {n:,} (step={step})")

    session = requests.Session()
    results = []
    for i, row in enumerate(sample):
        half = fetch_half(row["idp"], row["event_code"], session)
        results.append({**row, "half": half})
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(sample)}")
        time.sleep(0.25)

    fieldnames = list(results[0].keys()) if results else []
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    fetched = sum(1 for r in results if r["half"])
    print(f"  Saved {len(results)} rows ({fetched} with half split) → {out_path}")


if __name__ == "__main__":
    import sys

    years = [2018, 2019, 2021, 2022, 2023, 2024]
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]

    for yr in years:
        scrape_splits_for_year(yr)
        time.sleep(1)
