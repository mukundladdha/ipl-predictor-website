#!/usr/bin/env python3
"""
fetch_results.py
Fetches latest completed IPL 2026 match results from ESPNcricinfo
(with Cricbuzz fallback) and appends new rows to data/results.csv.

Run: python scripts/fetch_results.py
"""

import csv
import json
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RESULTS_CSV = ROOT / "data" / "results.csv"
LOGS_DIR = ROOT / "logs"
FETCH_LOG = LOGS_DIR / "fetch_log.txt"

# ── ESPNcricinfo ───────────────────────────────────────────────────────
ESPN_SERIES_ID = "1510719"
ESPN_API = (
    "https://hs-consumer-api.espncricinfo.com/v1/pages/series/schedule"
    f"?lang=en&seriesId={ESPN_SERIES_ID}"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# ── Team name normalisation ────────────────────────────────────────────
TEAM_MAP = {
    # RCB variations
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Royal Challengers Bengaluru": "Royal Challengers Bengaluru",
    "RCB": "Royal Challengers Bengaluru",
    # MI
    "Mumbai Indians": "Mumbai Indians",
    "MI": "Mumbai Indians",
    # KKR
    "Kolkata Knight Riders": "Kolkata Knight Riders",
    "KKR": "Kolkata Knight Riders",
    # CSK
    "Chennai Super Kings": "Chennai Super Kings",
    "CSK": "Chennai Super Kings",
    # SRH
    "Sunrisers Hyderabad": "Sunrisers Hyderabad",
    "SRH": "Sunrisers Hyderabad",
    # RR
    "Rajasthan Royals": "Rajasthan Royals",
    "RR": "Rajasthan Royals",
    # DC
    "Delhi Capitals": "Delhi Capitals",
    "DC": "Delhi Capitals",
    "Delhi Daredevils": "Delhi Capitals",
    # PBKS
    "Punjab Kings": "Punjab Kings",
    "PBKS": "Punjab Kings",
    "Kings XI Punjab": "Punjab Kings",
    "Kings XI Punjab ": "Punjab Kings",
    # GT
    "Gujarat Titans": "Gujarat Titans",
    "GT": "Gujarat Titans",
    # LSG
    "Lucknow Super Giants": "Lucknow Super Giants",
    "LSG": "Lucknow Super Giants",
}

CANONICAL_TEAMS = set(TEAM_MAP.values())

CSV_COLUMNS = ["date", "team1", "team2", "winner", "margin", "venue"]


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        handlers=[
            logging.FileHandler(FETCH_LOG, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def normalise(name: str) -> str:
    name = name.strip()
    return TEAM_MAP.get(name, name)


def load_existing_keys() -> set:
    """Return set of (date, team1, team2) tuples already in CSV."""
    if not RESULTS_CSV.exists():
        return set()
    keys = set()
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys.add((row["date"], row["team1"], row["team2"]))
    return keys


def append_rows(rows: list[dict]) -> int:
    """Append rows to CSV. Returns number of rows written."""
    if not rows:
        return 0
    write_header = not RESULTS_CSV.exists() or RESULTS_CSV.stat().st_size == 0
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# ── ESPNcricinfo fetcher ───────────────────────────────────────────────

def fetch_espn() -> list[dict]:
    """Fetch completed matches from ESPNcricinfo consumer API."""
    resp = requests.get(ESPN_API, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    matches_raw = (
        data.get("content", {}).get("matches", [])
        or data.get("matches", [])
    )

    results = []
    for m in matches_raw:
        # Only process completed matches
        status = (m.get("status") or m.get("matchStatus") or "").lower()
        if status not in ("complete", "result", "finished"):
            continue

        # Date
        raw_date = m.get("startDate") or m.get("date") or ""
        try:
            match_date = raw_date[:10]  # YYYY-MM-DD
        except Exception:
            continue

        # Teams
        teams_list = m.get("teams", [])
        if len(teams_list) < 2:
            continue
        t1_name = normalise(
            teams_list[0].get("team", {}).get("name", "")
            or teams_list[0].get("name", "")
        )
        t2_name = normalise(
            teams_list[1].get("team", {}).get("name", "")
            or teams_list[1].get("name", "")
        )

        # Skip if team not recognised
        if t1_name not in CANONICAL_TEAMS or t2_name not in CANONICAL_TEAMS:
            continue

        # Winner + margin
        status_text = m.get("statusText") or m.get("result", {}).get("resultString", "") or ""
        winner, margin = parse_result_text(status_text, t1_name, t2_name)

        # Venue
        venue = (
            m.get("ground", {}).get("name", "")
            or m.get("venue", {}).get("name", "")
            or ""
        )

        results.append({
            "date": match_date,
            "team1": t1_name,
            "team2": t2_name,
            "winner": winner,
            "margin": margin,
            "venue": venue,
        })

    return results


def parse_result_text(text: str, t1: str, t2: str) -> tuple[str, str]:
    """
    Parse strings like:
      'Royal Challengers Bengaluru won by 6 wickets'
      'Sunrisers Hyderabad won by 25 runs'
      'Match abandoned'  →  winner='no_result'
    Returns (winner_name, margin).
    """
    text = text.strip()
    tl = text.lower()

    if not text or "abandon" in tl or "no result" in tl or "cancelled" in tl:
        return "no_result", "no_result"

    # Try to identify winner by checking which team name appears before 'won'
    for team in [t1, t2]:
        if team.lower() in tl and "won" in tl:
            # Extract margin: everything after 'by'
            if " by " in tl:
                margin = text.split(" by ", 1)[1].strip().rstrip(".")
            else:
                margin = ""
            return team, margin

    # Super over marker — still parse winner
    if "super over" in tl:
        for team in [t1, t2]:
            if team.lower() in tl:
                margin = "super over"
                return team, margin

    return "no_result", text  # unknown


# ── Cricbuzz fallback ──────────────────────────────────────────────────

CRICBUZZ_URL = (
    "https://www.cricbuzz.com/cricket-series/9237/"
    "indian-premier-league-2026/matches"
)


def fetch_cricbuzz() -> list[dict]:
    """Minimal Cricbuzz HTML scraper as fallback."""
    resp = requests.get(
        CRICBUZZ_URL,
        headers={"User-Agent": HEADERS["User-Agent"]},
        timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    # Cricbuzz match rows typically have class 'cb-series-matches'
    for row in soup.select(".cb-series-matches"):
        try:
            result_span = row.select_one(".cb-text-complete")
            if not result_span:
                continue
            result_text = result_span.get_text(strip=True)

            teams = row.select(".cb-hmscg-tm-nm")
            if len(teams) < 2:
                continue
            t1 = normalise(teams[0].get_text(strip=True))
            t2 = normalise(teams[1].get_text(strip=True))
            if t1 not in CANONICAL_TEAMS or t2 not in CANONICAL_TEAMS:
                continue

            date_el = row.select_one(".schedule-date")
            date_str = date_el.get("ng-if", "") if date_el else ""
            # Fallback: just use today
            match_date = datetime.today().strftime("%Y-%m-%d")

            winner, margin = parse_result_text(result_text, t1, t2)
            venue_el = row.select_one(".text-gray")
            venue = venue_el.get_text(strip=True) if venue_el else ""

            results.append({
                "date": match_date,
                "team1": t1,
                "team2": t2,
                "winner": winner,
                "margin": margin,
                "venue": venue,
            })
        except Exception:
            continue

    return results


# ── Main ───────────────────────────────────────────────────────────────

def main():
    setup_logging()
    log = logging.getLogger(__name__)
    log.info("=== fetch_results.py start ===")

    # Ensure data dir + CSV exist
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not RESULTS_CSV.exists():
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()

    existing_keys = load_existing_keys()
    log.info(f"Existing rows in CSV: {len(existing_keys)}")

    # Try ESPN first
    fetched = []
    try:
        fetched = fetch_espn()
        log.info(f"ESPN returned {len(fetched)} completed matches")
    except Exception as e:
        log.warning(f"ESPNcricinfo fetch failed: {e}")
        # Fallback: Cricbuzz
        try:
            fetched = fetch_cricbuzz()
            log.info(f"Cricbuzz fallback returned {len(fetched)} matches")
        except Exception as e2:
            log.error(f"Cricbuzz fallback also failed: {e2}")
            log.error("No new data fetched. Exiting without modifying CSV.")
            sys.exit(0)  # Graceful exit — don't fail the GH Actions run

    # Deduplicate
    new_rows = []
    for row in fetched:
        key = (row["date"], row["team1"], row["team2"])
        if key not in existing_keys:
            new_rows.append(row)
            existing_keys.add(key)

    n_written = append_rows(new_rows)
    log.info(f"New matches added: {n_written}")
    log.info("=== fetch_results.py done ===\n")


if __name__ == "__main__":
    main()
