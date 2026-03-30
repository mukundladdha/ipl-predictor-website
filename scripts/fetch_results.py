#!/usr/bin/env python3
"""
fetch_results.py
Fetches completed IPL 2026 match results from Cricbuzz mobile
(series 9241) and appends new rows to data/results.csv.

Strategy:
  1. Fetch the IPL 2026 series matches page (mobile UA — Cricbuzz blocks desktop).
  2. Collect all "Complete" match IDs + slugs from the page.
  3. Fetch each completed match's live-scores page to extract the result text.
  4. Cross-reference team names against our fixture list for the date.
  5. Append only genuinely new rows (dedup by date+team1+team2).

Run: python scripts/fetch_results.py
"""

import csv
import json
import logging
import re
import sys
import time
from datetime import datetime, date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent.parent
RESULTS_CSV  = ROOT / "data" / "results.csv"
FIXTURES_JSON = ROOT / "public" / "data" / "fixtures.json"
LOGS_DIR     = ROOT / "logs"
FETCH_LOG    = LOGS_DIR / "fetch_log.txt"

# ── Cricbuzz mobile ────────────────────────────────────────────────────────────
CB_SERIES_ID   = "9241"          # IPL 2026 on Cricbuzz
CB_SERIES_URL  = f"https://m.cricbuzz.com/cricket-series/{CB_SERIES_ID}/ipl-2026/matches"
CB_SCORES_BASE = "https://m.cricbuzz.com/live-cricket-scores"

# Mobile Safari UA — Cricbuzz blocks desktop requests with 403
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)
HEADERS = {
    "User-Agent": MOBILE_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_DELAY = 1.5   # seconds between match-page requests

# ── Team name normalisation ────────────────────────────────────────────────────
TEAM_MAP = {
    "Royal Challengers Bengaluru":  "Royal Challengers Bengaluru",
    "Royal Challengers Bangalore":  "Royal Challengers Bengaluru",
    "RCB":                          "Royal Challengers Bengaluru",
    "Mumbai Indians":               "Mumbai Indians",
    "MI":                           "Mumbai Indians",
    "Kolkata Knight Riders":        "Kolkata Knight Riders",
    "KKR":                          "Kolkata Knight Riders",
    "Chennai Super Kings":          "Chennai Super Kings",
    "CSK":                          "Chennai Super Kings",
    "Sunrisers Hyderabad":          "Sunrisers Hyderabad",
    "SRH":                          "Sunrisers Hyderabad",
    "Rajasthan Royals":             "Rajasthan Royals",
    "RR":                           "Rajasthan Royals",
    "Delhi Capitals":               "Delhi Capitals",
    "DC":                           "Delhi Capitals",
    "Delhi Daredevils":             "Delhi Capitals",
    "Punjab Kings":                 "Punjab Kings",
    "PBKS":                         "Punjab Kings",
    "Kings XI Punjab":              "Punjab Kings",
    "Gujarat Titans":               "Gujarat Titans",
    "GT":                           "Gujarat Titans",
    "Lucknow Super Giants":         "Lucknow Super Giants",
    "LSG":                          "Lucknow Super Giants",
}
CANONICAL = set(TEAM_MAP.values())
CSV_COLS  = ["date", "team1", "team2", "winner", "margin", "venue"]


# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        handlers=[
            logging.FileHandler(FETCH_LOG, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def norm(name: str) -> str:
    return TEAM_MAP.get(name.strip(), name.strip())


# ── Fixture date lookup ────────────────────────────────────────────────────────
def build_schedule() -> list[dict]:
    """
    Returns a chronologically sorted list of ALL IPL 2026 fixtures
    (both completed and remaining), each as:
      {"date": "YYYY-MM-DD", "team1": full_name, "team2": full_name, "venue": str}
    """
    schedule = []
    today_str = date.today().isoformat()

    # Completed results (authoritative dates)
    if RESULTS_CSV.exists():
        with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t1, t2 = norm(row["team1"]), norm(row["team2"])
                if t1 in CANONICAL and t2 in CANONICAL:
                    schedule.append({
                        "date":  row["date"],
                        "team1": t1,
                        "team2": t2,
                        "venue": row.get("venue", ""),
                    })

    # Remaining fixtures
    if FIXTURES_JSON.exists():
        with open(FIXTURES_JSON, encoding="utf-8") as f:
            raw = json.load(f)
        fixtures = raw if isinstance(raw, list) else raw.get("fixtures", [])
        for fx in fixtures:
            t1, t2 = norm(fx.get("team1", "")), norm(fx.get("team2", ""))
            if t1 in CANONICAL and t2 in CANONICAL:
                schedule.append({
                    "date":  fx.get("date", ""),
                    "team1": t1,
                    "team2": t2,
                    "venue": fx.get("venue", ""),
                })

    schedule.sort(key=lambda x: x["date"])
    return schedule


def find_fixture_date(schedule: list[dict], t1: str, t2: str) -> dict:
    """
    Given two canonical team names, return the schedule entry whose date is the
    most recent one on or before today.  Falls back to the earliest future date
    if no past date exists for this pair.
    Returns {"date": ..., "venue": ...} or {} if not found.
    """
    today_str = date.today().isoformat()
    pair = frozenset([t1, t2])
    candidates = [
        fx for fx in schedule
        if frozenset([fx["team1"], fx["team2"]]) == pair
    ]
    if not candidates:
        return {}
    # Prefer the latest date that is <= today
    past = [c for c in candidates if c["date"] <= today_str]
    if past:
        return past[-1]   # most recent completed/today
    return candidates[0]  # earliest future


# ── CSV helpers ────────────────────────────────────────────────────────────────
def load_existing_keys() -> set:
    if not RESULTS_CSV.exists():
        return set()
    keys = set()
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys.add((row["date"], norm(row["team1"]), norm(row["team2"])))
    return keys


def append_rows(rows: list[dict]) -> int:
    if not rows:
        return 0
    write_hdr = not RESULTS_CSV.exists() or RESULTS_CSV.stat().st_size == 0
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        if write_hdr:
            w.writeheader()
        w.writerows(rows)
    return len(rows)


# ── Cricbuzz scraping ──────────────────────────────────────────────────────────
def fetch_completed_match_ids(session: requests.Session) -> list[tuple[str, str]]:
    """
    Returns [(match_id, slug), ...] for IPL 2026 matches marked 'Complete'.
    """
    resp = session.get(CB_SERIES_URL, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    completed = []
    # Cricbuzz marks complete matches with title containing "Complete"
    for a in soup.find_all("a", title=re.compile(r"Complete", re.I)):
        href = a.get("href", "")
        # Only IPL 2026 match links
        m = re.search(r"/live-cricket-scores/(\d+)/([^/\"']+ipl-2026[^/\"']*)", href)
        if m:
            completed.append((m.group(1), m.group(2).rstrip("\\")))

    # Also catch IPL 2026 links in the sidebar nav (older completed matches).
    # Sidebar shows "SRH vs RCB - RCB won" style text (no "Complete" tag),
    # so we accept any nav link where surrounding context contains "won".
    all_ipl_links = re.findall(
        r"/live-cricket-scores/(\d+)/([^\"']+(?:ipl-2026|indian-premier-league-2026)[^\"']*)",
        resp.text,
    )
    for mid, slug in all_ipl_links:
        slug = slug.rstrip("\\")
        if any(m[0] == mid for m in completed):
            continue  # already captured
        ctx_start = resp.text.find(mid)
        ctx = resp.text[max(0, ctx_start - 300):ctx_start + 300]
        if "Complete" in ctx or re.search(r"\b(won|abandoned|no result)\b", ctx, re.I):
            completed.append((mid, slug))

    return list(dict.fromkeys(completed))  # deduplicate, preserve order


def parse_match_page(session: requests.Session, match_id: str, slug: str):
    """
    Fetches a Cricbuzz match page and returns a result dict or None.
    Result dict: {team1, team2, winner, margin, venue, h1}
    """
    url = f"{CB_SCORES_BASE}/{match_id}/{slug}"
    try:
        resp = session.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logging.warning(f"  Fetch failed for match {match_id}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # --- H1: "Team A vs Team B, Nth Match, Indian Premier League 2026" ---
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""

    # Parse two team names from H1
    teams_raw = []
    h1_match = re.match(r"^(.+?)\s+vs\s+(.+?),", h1_text)
    if h1_match:
        teams_raw = [h1_match.group(1).strip(), h1_match.group(2).strip()]

    team1 = norm(teams_raw[0]) if len(teams_raw) > 0 else None
    team2 = norm(teams_raw[1]) if len(teams_raw) > 1 else None

    if not team1 or not team2:
        logging.warning(f"  Could not parse teams from H1: {h1_text!r}")
        return None

    if team1 not in CANONICAL or team2 not in CANONICAL:
        logging.warning(f"  Unrecognised team(s): {team1!r} / {team2!r}")
        return None

    # --- Result text: "X won by Y wkts/runs" ---
    result_text = None

    # Primary: div.text-cbTextLink
    result_el = soup.find("div", class_="text-cbTextLink")
    if result_el:
        result_text = result_el.get_text(strip=True)

    # Fallback: search all divs for "won by"
    if not result_text or "won" not in result_text.lower():
        for el in soup.find_all(string=re.compile(r"won by \d+", re.I)):
            t = el.strip()
            if len(t) < 120:
                result_text = t
                break

    if not result_text:
        logging.warning(f"  No result text found for match {match_id}")
        return None

    winner, margin = parse_result_text(result_text, team1, team2)

    # --- Venue: look for stadium/ground names in full page text ---
    all_text = soup.get_text(" ", strip=True)
    venue = extract_venue(all_text)

    return {
        "team1":  team1,
        "team2":  team2,
        "winner": winner,
        "margin": margin,
        "venue":  venue,
    }


def parse_result_text(text: str, t1: str, t2: str) -> tuple[str, str]:
    """
    Parse strings like:
      "Royal Challengers Bengaluru won by 6 wkts"
      "Mumbai Indians won by 25 runs (DLS)"
      "Match abandoned"
    Returns (winner_canonical_name, margin_string).
    """
    tl = text.lower().strip()

    if not text or "abandon" in tl or "no result" in tl or "cancelled" in tl:
        return "no_result", "no_result"

    # Normalise abbreviations
    normalised = text
    normalised = re.sub(r"\bwkts?\b", "wickets", normalised, flags=re.I)
    normalised = re.sub(r"\bruns?\b", "runs", normalised, flags=re.I)

    for team in [t1, t2]:
        if team.lower() in normalised.lower() and "won" in normalised.lower():
            if " by " in normalised.lower():
                margin = normalised.split(" by ", 1)[1].strip().rstrip(".")
                # Strip score line that sometimes follows: "6 wicketsSRH201..."
                margin = re.split(r"[A-Z]{2,}", margin)[0].strip()
            else:
                margin = ""
            return team, margin

    if "super over" in tl:
        for team in [t1, t2]:
            if team.lower() in tl:
                return team, "super over"

    return "no_result", text


def extract_venue(text: str) -> str:
    """Pull the first recognisable stadium/ground name from full page text."""
    patterns = [
        r"([A-Z][A-Za-z\s]+(?:Stadium|Ground|Oval|Park|Arena))",
        r"((?:Wankhede|Eden Gardens|Chinnaswamy|Chepauk|Narendra Modi|"
        r"Arun Jaitley|Sawai Mansingh|DY Patil|JSCA|Holkar|"
        r"Brabourne|BRSABVP)[A-Za-z\s]*)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return ""


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    setup_logging()
    log = logging.getLogger(__name__)
    log.info("=== fetch_results.py start ===")

    # Ensure CSV + data dir exist
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if not RESULTS_CSV.exists():
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_COLS).writeheader()

    existing_keys = load_existing_keys()
    log.info(f"Existing rows in CSV: {len(existing_keys)}")

    schedule = build_schedule()
    log.info(f"Schedule entries loaded: {len(schedule)}")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: get completed IPL 2026 match IDs
    try:
        completed = fetch_completed_match_ids(session)
        log.info(f"Completed IPL 2026 matches on Cricbuzz: {len(completed)}")
    except Exception as e:
        log.error(f"Failed to fetch series page: {e}")
        log.error("Exiting without modifying CSV.")
        sys.exit(0)

    # Step 2: parse each match page
    new_rows: list[dict] = []
    for match_id, slug in completed:
        time.sleep(REQUEST_DELAY)
        log.info(f"Fetching match {match_id}: {slug}")
        parsed = parse_match_page(session, match_id, slug)
        if not parsed:
            continue

        t1, t2 = parsed["team1"], parsed["team2"]
        winner, margin = parsed["winner"], parsed["margin"]

        # Skip matches with no valid result yet (upcoming / parse failure)
        if winner == "no_result" and margin != "no_result":
            log.info(f"  Skipping {t1} vs {t2} — no valid result found (match not completed yet)")
            continue

        # Look up date from full schedule (prefers most-recent date <= today)
        fx_info = find_fixture_date(schedule, t1, t2)
        match_date = fx_info.get("date", "")
        if not match_date:
            log.warning(f"  No date found for {t1} vs {t2} — skipping")
            continue

        venue = parsed["venue"] or fx_info.get("venue", "")
        csv_key     = (match_date, t1, t2)
        csv_key_rev = (match_date, t2, t1)

        if csv_key in existing_keys or csv_key_rev in existing_keys:
            log.info(f"  Already recorded: {match_date} {t1} vs {t2}")
            continue

        row = {
            "date":   match_date,
            "team1":  t1,
            "team2":  t2,
            "winner": winner,
            "margin": margin,
            "venue":  venue,
        }
        log.info(f"  NEW: {match_date} {t1} vs {t2} → {winner} by {margin}")
        new_rows.append(row)
        existing_keys.add(csv_key)

    n = append_rows(new_rows)
    log.info(f"New matches added: {n}")
    log.info("=== fetch_results.py done ===\n")


if __name__ == "__main__":
    main()
