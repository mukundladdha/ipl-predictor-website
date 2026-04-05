#!/usr/bin/env python3
"""
generate_why_changed.py
Pure-template (no LLM) explanations for each team's odds change.
Writes "why_changed" field into each team entry in projections.json.
Reads projections_previous.json (snapshot) vs projections.json (current).

Run: python scripts/generate_why_changed.py
"""
import csv, json, logging
from datetime import date as dt_date
from pathlib import Path

ROOT         = Path(__file__).parent.parent
PROJ         = ROOT / "public" / "data" / "projections.json"
PREV_PROJ    = ROOT / "data" / "projections_previous.json"
RESULTS_CSV  = ROOT / "data" / "results.csv"
FIXTURES_JSON = ROOT / "public" / "data" / "fixtures.json"
LOG_PATH     = ROOT / "logs" / "why_changed_log.txt"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

SHORT_TO_FULL = {
    "RCB": "Royal Challengers Bengaluru", "MI": "Mumbai Indians",
    "KKR": "Kolkata Knight Riders", "GT": "Gujarat Titans",
    "CSK": "Chennai Super Kings", "SRH": "Sunrisers Hyderabad",
    "PBKS": "Punjab Kings", "RR": "Rajasthan Royals",
    "DC": "Delhi Capitals", "LSG": "Lucknow Super Giants",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_elo_pct(proj, short):
    for t in proj["teams"]:
        if t["short"] == short:
            return t["models"]["elo"]["playoff_pct"]
    return 0.0


def get_elo_score(proj, short):
    for t in proj["teams"]:
        if t["short"] == short:
            return t.get("factors", {}).get("elo_score", 1500)
    return 1500


def load_results():
    rows = []
    with open(RESULTS_CSV, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def next_fixture(short, fixtures_data):
    """Return opponent short code for next upcoming fixture."""
    full = SHORT_TO_FULL.get(short, short)
    for fix in fixtures_data.get("fixtures", []):
        if fix.get("team1") == short or fix.get("team2") == short:
            opp = fix["team2"] if fix["team1"] == short else fix["team1"]
            d = fix.get("date", "")
            return opp, d
    return None, None


def full_to_short(full_name):
    inv = {v: k for k, v in SHORT_TO_FULL.items()}
    return inv.get(full_name, full_name[:3].upper())


def generate_explanation(short, pre_pct, post_pct, elo_before, elo_after,
                         last_match, opp_short, next_opp, next_date):
    delta = round(post_pct - pre_pct, 1)
    direction = "up" if delta > 0 else "down"
    sign = "+" if delta > 0 else ""

    if last_match:
        won = last_match.get("winner_short") == short
        verb = "Won" if won else "Lost"
        result_part = f"{verb} vs {opp_short}"
        elo_part = f"Elo {elo_before:.0f}→{elo_after:.0f}"
        odds_part = f"odds {sign}{delta}% to {post_pct:.1f}%"
    else:
        result_part = "Did not play"
        opp1 = last_match["team1_short"] if last_match else "—"
        opp2 = last_match["team2_short"] if last_match else "—"
        elo_part = f"Elo unchanged at {elo_after:.0f}"
        odds_part = f"odds shifted {sign}{delta}% (ripple from other result)"

    next_part = f"Next: vs {next_opp} ({next_date})" if next_opp else "Next fixture TBD"
    return f"{result_part} · {elo_part} · {odds_part} · {next_part}"


def main():
    log.info("=== generate_why_changed.py start ===")

    if not PREV_PROJ.exists():
        log.warning("projections_previous.json not found — skipping why_changed")
        return

    pre  = load_json(PREV_PROJ)
    post = load_json(PROJ)

    results = load_results()
    fixtures_data = load_json(FIXTURES_JSON) if FIXTURES_JSON.exists() else {"fixtures": []}

    # Get the most recent match
    results_2026 = [r for r in results if r.get("date", "").startswith("2026")]
    last = results_2026[-1] if results_2026 else None

    last_t1_short = full_to_short(last["team1"]) if last else None
    last_t2_short = full_to_short(last["team2"]) if last else None
    last_winner_short = full_to_short(last["winner"]) if last else None

    for team in post["teams"]:
        short = team["short"]
        pre_pct  = get_elo_pct(pre, short)
        post_pct = get_elo_pct(post, short)

        # Elo score before/after
        elo_before = get_elo_score(pre, short)
        elo_after  = get_elo_score(post, short)

        # Did this team play in the last match?
        played = last and short in (last_t1_short, last_t2_short)

        if played:
            opp = last_t2_short if short == last_t1_short else last_t1_short
            last_match_info = {"winner_short": last_winner_short}
        else:
            opp = None
            last_match_info = ({"team1_short": last_t1_short,
                                 "team2_short": last_t2_short}
                               if last else None)

        next_opp, next_date = next_fixture(short, fixtures_data)

        explanation = generate_explanation(
            short, pre_pct, post_pct, elo_before, elo_after,
            last_match_info if last else None,
            opp, next_opp, next_date
        )
        team["why_changed"] = explanation
        log.info(f"  {short}: {explanation}")

    with open(PROJ, "w", encoding="utf-8") as f:
        json.dump(post, f, indent=2, ensure_ascii=False)
    log.info(f"projections.json updated with why_changed fields")
    log.info("=== generate_why_changed.py done ===")


if __name__ == "__main__":
    main()
