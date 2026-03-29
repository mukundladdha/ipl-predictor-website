#!/usr/bin/env python3
"""
manual_add_result.py
Manually add a match result to data/results.csv and re-run simulation.

Usage:
  python scripts/manual_add_result.py \\
    --date 2026-03-28 \\
    --team1 "Royal Challengers Bengaluru" \\
    --team2 "Sunrisers Hyderabad" \\
    --winner "Royal Challengers Bengaluru" \\
    --margin "6 wickets" \\
    --venue "M. Chinnaswamy Stadium"
"""

import argparse
import csv
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
RESULTS_CSV = ROOT / "data" / "results.csv"
LOGS_DIR = ROOT / "logs"
FETCH_LOG = LOGS_DIR / "fetch_log.txt"

CANONICAL_TEAMS = [
    "Mumbai Indians",
    "Royal Challengers Bengaluru",
    "Kolkata Knight Riders",
    "Gujarat Titans",
    "Chennai Super Kings",
    "Sunrisers Hyderabad",
    "Punjab Kings",
    "Rajasthan Royals",
    "Delhi Capitals",
    "Lucknow Super Giants",
]

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


def load_existing_keys() -> set:
    if not RESULTS_CSV.exists():
        return set()
    keys = set()
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys.add((row["date"], row["team1"], row["team2"]))
    return keys


def append_row(row: dict):
    write_header = not RESULTS_CSV.exists() or RESULTS_CSV.stat().st_size == 0
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main():
    setup_logging()
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Manually add a match result.")
    parser.add_argument("--date",   required=True, help="Match date YYYY-MM-DD")
    parser.add_argument("--team1",  required=True, help="Home team (canonical name)")
    parser.add_argument("--team2",  required=True, help="Away team (canonical name)")
    parser.add_argument("--winner", required=True, help="Winning team name or 'no_result'")
    parser.add_argument("--margin", default="",    help="e.g. '6 wickets' or '25 runs'")
    parser.add_argument("--venue",  default="",    help="Venue name")
    args = parser.parse_args()

    # Validate date
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        log.error(f"Invalid date format: {args.date}  (expected YYYY-MM-DD)")
        sys.exit(1)

    # Validate team names
    for field, val in [("team1", args.team1), ("team2", args.team2)]:
        if val not in CANONICAL_TEAMS:
            log.error(
                f"Unknown team for {field}: '{val}'\n"
                f"Valid teams: {CANONICAL_TEAMS}"
            )
            sys.exit(1)

    if args.winner != "no_result" and args.winner not in CANONICAL_TEAMS:
        log.error(
            f"Winner '{args.winner}' not recognised. "
            f"Must be a canonical team name or 'no_result'."
        )
        sys.exit(1)

    if args.winner not in ("no_result", args.team1, args.team2):
        log.error(f"Winner '{args.winner}' must be one of team1/team2 or 'no_result'.")
        sys.exit(1)

    # Duplicate check
    existing = load_existing_keys()
    key = (args.date, args.team1, args.team2)
    if key in existing:
        log.warning(f"Result already exists for {args.date} {args.team1} vs {args.team2}. Skipping.")
        sys.exit(0)

    row = {
        "date":   args.date,
        "team1":  args.team1,
        "team2":  args.team2,
        "winner": args.winner,
        "margin": args.margin,
        "venue":  args.venue,
    }
    append_row(row)
    log.info(f"[MANUAL] Added result: {args.date}  {args.team1} vs {args.team2}  → {args.winner} ({args.margin})")

    # Auto-run simulation
    log.info("Running update_projections.py ...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "update_projections.py")],
        capture_output=False,
    )
    if result.returncode != 0:
        log.error("update_projections.py exited with errors.")
        sys.exit(result.returncode)

    log.info("Done.")


if __name__ == "__main__":
    main()
