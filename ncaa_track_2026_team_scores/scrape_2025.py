import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

BASE_URL = "https://flashresults.ncaa.com/Outdoor/2025/"

# (event_id, event_name, gender, round_candidates, is_relay, category)
# round_candidates: ordered list of round numbers to try; first with data wins
EVENTS = [
    # Men's track
    ("001", "100M",     "M", [2, 1], False, "sprint"),
    ("002", "200M",     "M", [2, 1], False, "sprint"),
    ("003", "400M",     "M", [2, 1], False, "sprint"),
    ("004", "800M",     "M", [2, 1], False, "mid_distance"),
    ("005", "1500M",    "M", [2, 1], False, "mid_distance"),
    ("006", "3000SC",   "M", [2, 1], False, "distance"),
    ("007", "5000M",    "M", [1],    False, "distance"),
    ("008", "10000M",   "M", [1],    False, "distance"),
    ("009", "110MH",    "M", [2, 1], False, "sprint"),
    ("010", "400MH",    "M", [2, 1], False, "sprint"),
    ("011", "4x100M",   "M", [2, 1], True,  "relay"),
    ("012", "4x400M",   "M", [2, 1], True,  "relay"),
    # Men's field
    ("013", "High Jump",    "M", [1], False, "jump"),
    ("014", "Pole Vault",   "M", [1], False, "jump"),
    ("015", "Long Jump",    "M", [1], False, "jump"),
    ("016", "Triple Jump",  "M", [1], False, "jump"),
    ("017", "Shot Put",     "M", [1], False, "throw"),
    ("018", "Discus",       "M", [1], False, "throw"),
    ("019", "Hammer",       "M", [1], False, "throw"),
    ("020", "Javelin",      "M", [1], False, "throw"),
    # Men's multi
    ("041", "Decathlon",    "M", [1], False, "multi"),
    # Women's track
    ("021", "100M",     "W", [2, 1], False, "sprint"),
    ("022", "200M",     "W", [2, 1], False, "sprint"),
    ("023", "400M",     "W", [2, 1], False, "sprint"),
    ("024", "800M",     "W", [2, 1], False, "mid_distance"),
    ("025", "1500M",    "W", [2, 1], False, "mid_distance"),
    ("026", "3000SC",   "W", [2, 1], False, "distance"),
    ("027", "5000M",    "W", [1],    False, "distance"),
    ("028", "10000M",   "W", [1],    False, "distance"),
    ("029", "100MH",    "W", [2, 1], False, "sprint"),
    ("030", "400MH",    "W", [2, 1], False, "sprint"),
    ("031", "4x100M",   "W", [2, 1], True,  "relay"),
    ("032", "4x400M",   "W", [2, 1], True,  "relay"),
    # Women's field
    ("033", "High Jump",    "W", [1], False, "jump"),
    ("034", "Pole Vault",   "W", [1], False, "jump"),
    ("035", "Long Jump",    "W", [1], False, "jump"),
    ("036", "Triple Jump",  "W", [1], False, "jump"),
    ("037", "Shot Put",     "W", [1], False, "throw"),
    ("038", "Discus",       "W", [1], False, "throw"),
    ("039", "Hammer",       "W", [1], False, "throw"),
    ("040", "Javelin",      "W", [1], False, "throw"),
    # Women's multi
    ("042", "Heptathlon",   "W", [1], False, "multi"),
]

NCAA_POINTS  = [10, 8, 6, 5, 4, 3, 2, 1]
RELAY_POINTS = [10, 8, 6, 5, 4, 3, 2, 1]  # same scale as individual events


def get_points(place, is_relay):
    pts = RELAY_POINTS if is_relay else NCAA_POINTS
    try:
        p = int(place)
        if 1 <= p <= 8:
            return pts[p - 1]
    except (TypeError, ValueError):
        pass
    return 0


def parse_logo_cell(cell):
    """Extract school abbreviation from the logo cell (cols[1])."""
    img = cell.find("image") or cell.find("img")
    if img and img.get("src"):
        m = re.search(r'logos/(\w+)\.(?:png|gif|jpg)', img["src"], re.I)
        if m:
            return m.group(1).upper()
    return None


def parse_athlete_cell(cell, is_relay=False):
    """Extract (name, school, year) from the athlete/team cell (cols[2]).

    Layout for individual events:
      <b><a stats-name="Jordan Anthony|Arkansas">Jordan ANTHONY</a></b>
      <sup>lane</sup><br/><small>Arkansas [SO]</small>

    Layout for relay events:
      <b>AUBURN</b><sup>heat</sup><br/><small>Auburn</small>
    """
    name = ""
    school = ""
    year = ""

    if is_relay:
        b_tag = cell.find("b")
        name = b_tag.get_text(strip=True) if b_tag else ""
    else:
        a_tag = cell.find("a", attrs={"stats-name": True})
        if a_tag:
            stats = a_tag["stats-name"]
            parts = stats.split("|")
            name = parts[0].strip() if parts else ""
        else:
            b_tag = cell.find("b")
            name = b_tag.get_text(strip=True) if b_tag else ""

    small = cell.find("small")
    if small:
        small_text = small.get_text(strip=True)
        m_yr = re.search(r'\s*\[?(FR|SO|JR|SR|GR)\]?\s*$', small_text, re.I)
        if m_yr:
            year = m_yr.group(1).upper()
            school = small_text[:m_yr.start()].strip()
        else:
            school = small_text.strip()

    return name, school, year


def scrape_page(url, event_name, gender, is_relay, category):
    """Fetch one results page. Returns list of row dicts, or None on failure."""
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"    request error: {e}")
        return None

    table = soup.find("table", {"id": "events"})
    if table is None:
        table = soup.find("table", {"id": "multitotalscores"})
    if table is None:
        return None

    rows = table.find_all("tr")
    results = []
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue

        place_text = cols[0].get_text(strip=True).lstrip("*").strip()
        try:
            place = int(re.match(r'\d+', place_text).group())
        except (AttributeError, ValueError):
            place = None

        # cols[1] = logo, cols[2] = athlete, cols[3] = result
        school_abbr = parse_logo_cell(cols[1])
        name, school, year = parse_athlete_cell(cols[2], is_relay)

        result = ""
        if len(cols) > 3:
            result_text = cols[3].get_text(strip=True)
            result = result_text.split("\n")[0].strip()

        results.append({
            "event":        event_name,
            "gender":       gender,
            "category":     category,
            "place":        place,
            "name":         name,
            "school":       school,
            "school_abbr":  school_abbr,
            "year":         year,
            "result":       result,
            "points":       get_points(place, is_relay),
            "is_relay":     is_relay,
        })

    return results or None


def main():
    all_results = []

    for event_id, event_name, gender, rounds, is_relay, category in EVENTS:
        label = f"{gender} {event_name}"
        print(f"  {label:<20}", end=" ")

        if len(rounds) == 1:
            # Single-round event — scrape as before
            url = f"{BASE_URL}{event_id}-{rounds[0]}_compiled.htm"
            rows = scrape_page(url, event_name, gender, is_relay, category)
            if rows:
                for r in rows:
                    r['round'] = rounds[0]
                    r['is_final'] = True
                all_results.extend(rows)
                print(f"ok ({len(rows)} rows, round {rounds[0]})")
            else:
                print("MISSING")
        else:
            # Multi-round event: rounds[0] = final, rounds[-1] = prelim
            final_rnd, prelim_rnd = rounds[0], rounds[-1]

            final_url = f"{BASE_URL}{event_id}-{final_rnd}_compiled.htm"
            final_rows = scrape_page(final_url, event_name, gender, is_relay, category)

            if final_rows:
                for r in final_rows:
                    r['round'] = final_rnd
                    r['is_final'] = True
                all_results.extend(final_rows)
                print(f"final rnd{final_rnd} ({len(final_rows)} rows)", end="")

                time.sleep(0.2)
                prelim_url = f"{BASE_URL}{event_id}-{prelim_rnd}_compiled.htm"
                prelim_rows = scrape_page(prelim_url, event_name, gender, is_relay, category)
                if prelim_rows:
                    for r in prelim_rows:
                        r['round'] = prelim_rnd
                        r['is_final'] = False
                        r['points'] = 0
                    all_results.extend(prelim_rows)
                    print(f" + prelim ({len(prelim_rows)} rows)")
                else:
                    print(" (no prelim found)")
            else:
                # Fallback: use prelim as the final round
                time.sleep(0.2)
                prelim_url = f"{BASE_URL}{event_id}-{prelim_rnd}_compiled.htm"
                prelim_rows = scrape_page(prelim_url, event_name, gender, is_relay, category)
                if prelim_rows:
                    for r in prelim_rows:
                        r['round'] = prelim_rnd
                        r['is_final'] = True
                    all_results.extend(prelim_rows)
                    print(f"ok rnd{prelim_rnd} ({len(prelim_rows)} rows, used as final)")
                else:
                    print("MISSING")

        time.sleep(0.4)

    df = pd.DataFrame(all_results)
    out = "results_2025.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved {len(df)} rows to {out}")

    summary = (df[df['is_final']].groupby(["gender", "event"])["place"]
               .count().rename("n_finishers"))
    print(summary.to_string())


if __name__ == "__main__":
    main()
