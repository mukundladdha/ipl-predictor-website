#!/usr/bin/env python3
"""
update_projections.py
Reads data/results.csv, recalculates Elo + Form ratings,
runs 100,000-iteration Monte Carlo simulation, and writes
public/data/projections.json + public/data/fixtures.json.

Run: python scripts/update_projections.py
"""

import csv
import json
import logging
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RESULTS_CSV = ROOT / "data" / "results.csv"
PROJECTIONS_JSON = ROOT / "public" / "data" / "projections.json"
FIXTURES_JSON = ROOT / "public" / "data" / "fixtures.json"
LOGS_DIR = ROOT / "logs"
SIM_LOG = LOGS_DIR / "simulation_log.txt"

# ── Constants ──────────────────────────────────────────────────────────
ELO_BASE = 1500
ELO_K = 32
FORM_WINDOW = 12
FORM_DECAY = [0.75 ** i for i in range(FORM_WINDOW)]
# Bayesian prior strength for form smoothing.
# Equivalent to ~4 "phantom" games at 50% win rate.
# Calibrated to match the decay-weight sum of a full 12-game window (~3.9),
# so the prior fades naturally as real results accumulate.
# Prevents 0%/100% extremes for teams with only 1–2 results.
FORM_PRIOR = 4.0
N_SIM = 100_000
SEASON_YEAR = "2026"

# Pre-season calibrated Elo baselines (sum = 15,000 → avg 1500).
# Derived from historical IPL performance, squad strength for 2026.
# All results in data/results.csv are applied on top of these values.
ELO_INITIAL = {
    "Mumbai Indians":               1545,
    "Royal Challengers Bengaluru":  1540,
    "Punjab Kings":                 1530,
    "Gujarat Titans":               1520,
    "Kolkata Knight Riders":        1510,
    "Chennai Super Kings":          1505,
    "Sunrisers Hyderabad":          1495,
    "Rajasthan Royals":             1480,
    "Delhi Capitals":               1465,
    "Lucknow Super Giants":         1410,
}

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

# Short codes for JSON output (matched by canonical name)
SHORT_MAP = {
    "Mumbai Indians": "MI",
    "Royal Challengers Bengaluru": "RCB",
    "Kolkata Knight Riders": "KKR",
    "Gujarat Titans": "GT",
    "Chennai Super Kings": "CSK",
    "Sunrisers Hyderabad": "SRH",
    "Punjab Kings": "PBKS",
    "Rajasthan Royals": "RR",
    "Delhi Capitals": "DC",
    "Lucknow Super Giants": "LSG",
}

# ── Full IPL 2026 fixture list (70 matches) ────────────────────────────
# Source: https://www.espncricinfo.com/series/ipl-2026-1510719/
# Official schedule — verified against iplt20.com & cricketnews.com
FIXTURES_2026 = [
    # Matches 1–5 — March 28–April 1
    {"date": "2026-03-28", "team1": "Royal Challengers Bengaluru",  "team2": "Sunrisers Hyderabad",        "venue": "M. Chinnaswamy Stadium"},
    {"date": "2026-03-29", "team1": "Mumbai Indians",               "team2": "Kolkata Knight Riders",      "venue": "Wankhede Stadium"},
    {"date": "2026-03-30", "team1": "Rajasthan Royals",             "team2": "Chennai Super Kings",        "venue": "Barsapara Cricket Stadium"},
    {"date": "2026-03-31", "team1": "Punjab Kings",                 "team2": "Gujarat Titans",             "venue": "Punjab Cricket Association IS Bindra Stadium"},
    {"date": "2026-04-01", "team1": "Lucknow Super Giants",         "team2": "Delhi Capitals",             "venue": "BRSABV Ekana Cricket Stadium"},
    # Matches 6–12 — April 2–6
    {"date": "2026-04-02", "team1": "Kolkata Knight Riders",        "team2": "Sunrisers Hyderabad",        "venue": "Eden Gardens"},
    {"date": "2026-04-03", "team1": "Chennai Super Kings",          "team2": "Punjab Kings",               "venue": "MA Chidambaram Stadium"},
    {"date": "2026-04-04", "team1": "Delhi Capitals",               "team2": "Mumbai Indians",             "venue": "Arun Jaitley Stadium"},
    {"date": "2026-04-04", "team1": "Gujarat Titans",               "team2": "Rajasthan Royals",           "venue": "Narendra Modi Stadium"},
    {"date": "2026-04-05", "team1": "Sunrisers Hyderabad",          "team2": "Lucknow Super Giants",       "venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-04-05", "team1": "Royal Challengers Bengaluru",  "team2": "Chennai Super Kings",        "venue": "M. Chinnaswamy Stadium"},
    {"date": "2026-04-06", "team1": "Kolkata Knight Riders",        "team2": "Punjab Kings",               "venue": "Eden Gardens"},
    # Matches 13–20 — April 7–12
    {"date": "2026-04-07", "team1": "Rajasthan Royals",             "team2": "Mumbai Indians",             "venue": "Barsapara Cricket Stadium"},
    {"date": "2026-04-08", "team1": "Delhi Capitals",               "team2": "Gujarat Titans",             "venue": "Arun Jaitley Stadium"},
    {"date": "2026-04-09", "team1": "Kolkata Knight Riders",        "team2": "Lucknow Super Giants",       "venue": "Eden Gardens"},
    {"date": "2026-04-10", "team1": "Rajasthan Royals",             "team2": "Royal Challengers Bengaluru","venue": "Barsapara Cricket Stadium"},
    {"date": "2026-04-11", "team1": "Punjab Kings",                 "team2": "Sunrisers Hyderabad",        "venue": "Punjab Cricket Association IS Bindra Stadium"},
    {"date": "2026-04-11", "team1": "Chennai Super Kings",          "team2": "Delhi Capitals",             "venue": "MA Chidambaram Stadium"},
    {"date": "2026-04-12", "team1": "Lucknow Super Giants",         "team2": "Gujarat Titans",             "venue": "BRSABV Ekana Cricket Stadium"},
    {"date": "2026-04-12", "team1": "Mumbai Indians",               "team2": "Royal Challengers Bengaluru","venue": "Wankhede Stadium"},
    # Matches 21–30 — April 13–20
    {"date": "2026-04-13", "team1": "Sunrisers Hyderabad",          "team2": "Rajasthan Royals",           "venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-04-14", "team1": "Chennai Super Kings",          "team2": "Kolkata Knight Riders",      "venue": "MA Chidambaram Stadium"},
    {"date": "2026-04-15", "team1": "Royal Challengers Bengaluru",  "team2": "Lucknow Super Giants",       "venue": "M. Chinnaswamy Stadium"},
    {"date": "2026-04-16", "team1": "Mumbai Indians",               "team2": "Punjab Kings",               "venue": "Wankhede Stadium"},
    {"date": "2026-04-17", "team1": "Gujarat Titans",               "team2": "Kolkata Knight Riders",      "venue": "Narendra Modi Stadium"},
    {"date": "2026-04-18", "team1": "Royal Challengers Bengaluru",  "team2": "Delhi Capitals",             "venue": "M. Chinnaswamy Stadium"},
    {"date": "2026-04-18", "team1": "Sunrisers Hyderabad",          "team2": "Chennai Super Kings",        "venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-04-19", "team1": "Kolkata Knight Riders",        "team2": "Rajasthan Royals",           "venue": "Eden Gardens"},
    {"date": "2026-04-19", "team1": "Punjab Kings",                 "team2": "Lucknow Super Giants",       "venue": "Punjab Cricket Association IS Bindra Stadium"},
    {"date": "2026-04-20", "team1": "Gujarat Titans",               "team2": "Mumbai Indians",             "venue": "Narendra Modi Stadium"},
    # Matches 31–40 — April 21–28
    {"date": "2026-04-21", "team1": "Sunrisers Hyderabad",          "team2": "Delhi Capitals",             "venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-04-22", "team1": "Lucknow Super Giants",         "team2": "Rajasthan Royals",           "venue": "BRSABV Ekana Cricket Stadium"},
    {"date": "2026-04-23", "team1": "Mumbai Indians",               "team2": "Chennai Super Kings",        "venue": "Wankhede Stadium"},
    {"date": "2026-04-24", "team1": "Royal Challengers Bengaluru",  "team2": "Gujarat Titans",             "venue": "M. Chinnaswamy Stadium"},
    {"date": "2026-04-25", "team1": "Delhi Capitals",               "team2": "Punjab Kings",               "venue": "Arun Jaitley Stadium"},
    {"date": "2026-04-25", "team1": "Rajasthan Royals",             "team2": "Sunrisers Hyderabad",        "venue": "Sawai Mansingh Stadium"},
    {"date": "2026-04-26", "team1": "Gujarat Titans",               "team2": "Chennai Super Kings",        "venue": "Narendra Modi Stadium"},
    {"date": "2026-04-26", "team1": "Lucknow Super Giants",         "team2": "Kolkata Knight Riders",      "venue": "BRSABV Ekana Cricket Stadium"},
    {"date": "2026-04-27", "team1": "Delhi Capitals",               "team2": "Royal Challengers Bengaluru","venue": "Arun Jaitley Stadium"},
    {"date": "2026-04-28", "team1": "Punjab Kings",                 "team2": "Rajasthan Royals",           "venue": "Punjab Cricket Association IS Bindra Stadium"},
    # Matches 41–50 — April 29–May 7
    {"date": "2026-04-29", "team1": "Mumbai Indians",               "team2": "Sunrisers Hyderabad",        "venue": "Wankhede Stadium"},
    {"date": "2026-04-30", "team1": "Gujarat Titans",               "team2": "Royal Challengers Bengaluru","venue": "Narendra Modi Stadium"},
    {"date": "2026-05-01", "team1": "Rajasthan Royals",             "team2": "Delhi Capitals",             "venue": "Sawai Mansingh Stadium"},
    {"date": "2026-05-02", "team1": "Chennai Super Kings",          "team2": "Mumbai Indians",             "venue": "MA Chidambaram Stadium"},
    {"date": "2026-05-03", "team1": "Sunrisers Hyderabad",          "team2": "Kolkata Knight Riders",      "venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-05-03", "team1": "Gujarat Titans",               "team2": "Punjab Kings",               "venue": "Narendra Modi Stadium"},
    {"date": "2026-05-04", "team1": "Mumbai Indians",               "team2": "Lucknow Super Giants",       "venue": "Wankhede Stadium"},
    {"date": "2026-05-05", "team1": "Delhi Capitals",               "team2": "Chennai Super Kings",        "venue": "Arun Jaitley Stadium"},
    {"date": "2026-05-06", "team1": "Sunrisers Hyderabad",          "team2": "Punjab Kings",               "venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-05-07", "team1": "Lucknow Super Giants",         "team2": "Royal Challengers Bengaluru","venue": "BRSABV Ekana Cricket Stadium"},
    # Matches 51–60 — May 8–16
    {"date": "2026-05-08", "team1": "Delhi Capitals",               "team2": "Kolkata Knight Riders",      "venue": "Arun Jaitley Stadium"},
    {"date": "2026-05-09", "team1": "Rajasthan Royals",             "team2": "Gujarat Titans",             "venue": "Sawai Mansingh Stadium"},
    {"date": "2026-05-10", "team1": "Chennai Super Kings",          "team2": "Lucknow Super Giants",       "venue": "MA Chidambaram Stadium"},
    {"date": "2026-05-10", "team1": "Royal Challengers Bengaluru",  "team2": "Mumbai Indians",             "venue": "Shaheed Veer Narayan Singh International Stadium"},
    {"date": "2026-05-11", "team1": "Punjab Kings",                 "team2": "Delhi Capitals",             "venue": "HPCA Stadium"},
    {"date": "2026-05-12", "team1": "Gujarat Titans",               "team2": "Sunrisers Hyderabad",        "venue": "Narendra Modi Stadium"},
    {"date": "2026-05-13", "team1": "Royal Challengers Bengaluru",  "team2": "Kolkata Knight Riders",      "venue": "Shaheed Veer Narayan Singh International Stadium"},
    {"date": "2026-05-14", "team1": "Punjab Kings",                 "team2": "Mumbai Indians",             "venue": "HPCA Stadium"},
    {"date": "2026-05-15", "team1": "Lucknow Super Giants",         "team2": "Chennai Super Kings",        "venue": "BRSABV Ekana Cricket Stadium"},
    {"date": "2026-05-16", "team1": "Kolkata Knight Riders",        "team2": "Gujarat Titans",             "venue": "Eden Gardens"},
    # Matches 61–70 — May 17–24 (final round)
    {"date": "2026-05-17", "team1": "Punjab Kings",                 "team2": "Royal Challengers Bengaluru","venue": "HPCA Stadium"},
    {"date": "2026-05-17", "team1": "Delhi Capitals",               "team2": "Rajasthan Royals",           "venue": "Arun Jaitley Stadium"},
    {"date": "2026-05-18", "team1": "Chennai Super Kings",          "team2": "Sunrisers Hyderabad",        "venue": "MA Chidambaram Stadium"},
    {"date": "2026-05-19", "team1": "Rajasthan Royals",             "team2": "Lucknow Super Giants",       "venue": "Sawai Mansingh Stadium"},
    {"date": "2026-05-20", "team1": "Kolkata Knight Riders",        "team2": "Mumbai Indians",             "venue": "Eden Gardens"},
    {"date": "2026-05-21", "team1": "Chennai Super Kings",          "team2": "Gujarat Titans",             "venue": "MA Chidambaram Stadium"},
    {"date": "2026-05-22", "team1": "Sunrisers Hyderabad",          "team2": "Royal Challengers Bengaluru","venue": "Rajiv Gandhi International Stadium"},
    {"date": "2026-05-23", "team1": "Lucknow Super Giants",         "team2": "Punjab Kings",               "venue": "BRSABV Ekana Cricket Stadium"},
    {"date": "2026-05-24", "team1": "Mumbai Indians",               "team2": "Rajasthan Royals",           "venue": "Wankhede Stadium"},
    {"date": "2026-05-24", "team1": "Kolkata Knight Riders",        "team2": "Delhi Capitals",             "venue": "Eden Gardens"},
]


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        handlers=[
            logging.FileHandler(SIM_LOG, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_results() -> list[dict]:
    """Load results.csv sorted chronologically. Returns list of dicts."""
    if not RESULTS_CSV.exists():
        return []
    rows = []
    with open(RESULTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    rows.sort(key=lambda r: r["date"])
    return rows


def calculate_elo(results: list[dict]) -> dict[str, float]:
    """
    Process all results chronologically, updating Elo ratings.
    Starts all teams at ELO_BASE (1500).
    No-result matches skip Elo update.
    """
    elo = {t: float(ELO_INITIAL.get(t, ELO_BASE)) for t in CANONICAL_TEAMS}
    for r in results:
        t1, t2, winner = r["team1"], r["team2"], r["winner"]
        if winner == "no_result":
            continue
        if t1 not in elo or t2 not in elo:
            continue
        e1, e2 = elo[t1], elo[t2]
        expected1 = 1.0 / (1.0 + 10 ** ((e2 - e1) / 400))
        actual1 = 1.0 if winner == t1 else 0.0
        elo[t1] = e1 + ELO_K * (actual1 - expected1)
        elo[t2] = e2 + ELO_K * ((1 - actual1) - (1 - expected1))
    return elo


def calculate_form(results: list[dict]) -> dict[str, float]:
    """
    For each team, take last FORM_WINDOW valid results (no no_results),
    apply exponential decay weights, return form score in [0, 1].
    """
    # Collect last N results per team (most recent last → reverse for decay)
    team_results: dict[str, list[float]] = {t: [] for t in CANONICAL_TEAMS}
    for r in results:
        t1, t2, winner = r["team1"], r["team2"], r["winner"]
        if winner == "no_result":
            continue
        if t1 in team_results:
            team_results[t1].append(1.0 if winner == t1 else 0.0)
        if t2 in team_results:
            team_results[t2].append(1.0 if winner == t2 else 0.0)

    form = {}
    for team, res in team_results.items():
        recent = res[-FORM_WINDOW:]  # most recent at end
        recent = list(reversed(recent))  # i=0 = most recent
        if not recent:
            form[team] = 0.5  # neutral if no data
            continue
        weights = FORM_DECAY[: len(recent)]
        total_w = sum(weights)
        raw = sum(w * v for w, v in zip(weights, recent)) / total_w
        # Bayesian smoothing: blend with neutral 0.5 prior.
        # Prior fades as total_w grows (full 12-game window ≈ 3.9 weight).
        form[team] = (total_w * raw + FORM_PRIOR * 0.5) / (total_w + FORM_PRIOR)
    return form


def calculate_points_2026(results: list[dict]) -> dict[str, int]:
    """Points table for 2026 matches only."""
    pts = {t: 0 for t in CANONICAL_TEAMS}
    for r in results:
        if not r["date"].startswith(SEASON_YEAR):
            continue
        winner = r["winner"]
        if winner in pts:
            pts[winner] += 2
    return pts


def get_remaining_fixtures(results: list[dict]) -> list[dict]:
    """
    Return fixtures from FIXTURES_2026 not yet completed
    (not in results.csv for 2026).
    """
    completed = set()
    for r in results:
        if r["date"].startswith(SEASON_YEAR):
            completed.add((r["date"], r["team1"], r["team2"]))
            # Also add reversed (in case home/away swapped)
            completed.add((r["date"], r["team2"], r["team1"]))

    remaining = []
    for fix in FIXTURES_2026:
        key = (fix["date"], fix["team1"], fix["team2"])
        key_rev = (fix["date"], fix["team2"], fix["team1"])
        if key not in completed and key_rev not in completed:
            remaining.append(fix)
    return remaining


def elo_win_prob(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def form_win_prob(form_a: float, form_b: float) -> float:
    total = form_a + form_b
    if total == 0:
        return 0.5
    return form_a / total


def run_monte_carlo(
    team_names: list[str],
    fixtures: list[dict],
    pts_start: dict[str, int],
    elo: dict[str, float],
    form: dict[str, float],
    n_sim: int = N_SIM,
) -> dict:
    """
    Vectorised Monte Carlo simulation.
    Returns dict: team → {elo: {playoff_pct, rank_probs}, form: {...}}
    """
    n_teams = len(team_names)
    idx = {t: i for i, t in enumerate(team_names)}
    n_fix = len(fixtures)

    # Pre-compute win probabilities for each fixture (both models)
    probs_elo = np.zeros(n_fix, dtype=np.float32)
    probs_form = np.zeros(n_fix, dtype=np.float32)
    fix_t1_idx = np.zeros(n_fix, dtype=np.int32)
    fix_t2_idx = np.zeros(n_fix, dtype=np.int32)

    for j, fix in enumerate(fixtures):
        t1, t2 = fix["team1"], fix["team2"]
        fix_t1_idx[j] = idx[t1]
        fix_t2_idx[j] = idx[t2]
        probs_elo[j] = elo_win_prob(elo.get(t1, ELO_BASE), elo.get(t2, ELO_BASE))
        probs_form[j] = form_win_prob(form.get(t1, 0.5), form.get(t2, 0.5))

    pts_arr = np.array([pts_start.get(t, 0) for t in team_names], dtype=np.float32)

    results_by_model = {}

    for model_name, probs in [("elo", probs_elo), ("form", probs_form)]:
        # Draw all randoms at once: n_sim × n_fix
        rands = np.random.random((n_sim, n_fix)).astype(np.float32)

        # t1 wins where rand < prob
        t1_wins = rands < probs[np.newaxis, :]  # (n_sim, n_fix)

        pts = np.tile(pts_arr, (n_sim, 1))  # (n_sim, n_teams)

        for j in range(n_fix):
            t1i, t2i = fix_t1_idx[j], fix_t2_idx[j]
            pts[t1_wins[:, j], t1i] += 2
            pts[~t1_wins[:, j], t2i] += 2

        # Add small tiebreaker noise to avoid identical points
        pts += np.random.uniform(0, 0.001, pts.shape).astype(np.float32)

        # Rank: argsort descending → (n_sim, n_teams)
        ranks = np.argsort(-pts, axis=1)

        # Playoff appearances (top 4)
        playoff_counts = np.zeros(n_teams, dtype=np.int64)
        rank_counts = np.zeros((n_teams, n_teams), dtype=np.int64)

        for r in range(n_teams):
            teams_at_r = ranks[:, r]
            unique, counts = np.unique(teams_at_r, return_counts=True)
            rank_counts[unique, r] = counts
            if r < 4:
                playoff_counts[unique] += counts

        playoff_pct = {
            team_names[i]: round(float(playoff_counts[i]) / n_sim * 100, 1)
            for i in range(n_teams)
        }
        rank_probs = {
            team_names[i]: [
                round(float(rank_counts[i, r]) / n_sim * 100, 1)
                for r in range(n_teams)
            ]
            for i in range(n_teams)
        }

        results_by_model[model_name] = {
            "playoff_pct": playoff_pct,
            "rank_probs": rank_probs,
        }

    return results_by_model


def sanity_check(sim_results: dict) -> bool:
    """
    Returns True if results look valid:
    - All playoff_pct in [0, 100]
    - Sum of elo playoff_pct in [380, 420]
    """
    elo_sum = sum(
        sim_results["elo"]["playoff_pct"][t] for t in CANONICAL_TEAMS
    )
    for model in ("elo", "form"):
        for t in CANONICAL_TEAMS:
            pct = sim_results[model]["playoff_pct"][t]
            if not (0 <= pct <= 100):
                return False
    return 380 <= elo_sum <= 420


def update_fixtures_json(remaining: list[dict]):
    """Write remaining fixtures back to public/data/fixtures.json."""
    out = []
    for fix in remaining:
        out.append({
            "team1": SHORT_MAP.get(fix["team1"], fix["team1"]),
            "team2": SHORT_MAP.get(fix["team2"], fix["team2"]),
            "date": fix["date"],
            "venue": fix["venue"],
        })
    with open(FIXTURES_JSON, "w", encoding="utf-8") as f:
        json.dump({"fixtures": out}, f, indent=2)


def main():
    setup_logging()
    log = logging.getLogger(__name__)
    log.info("=== update_projections.py start ===")

    # Load existing projections (needed for colors, short codes, history)
    with open(PROJECTIONS_JSON, encoding="utf-8") as f:
        existing_proj = json.load(f)

    # Build lookup: canonical_name → existing team entry
    team_lookup = {t["name"]: t for t in existing_proj["teams"]}

    # Load results
    results = load_results()
    if not results:
        log.warning("results.csv is empty — no update performed.")
        sys.exit(0)

    log.info(f"Total rows in results.csv: {len(results)}")

    # Count 2026 completed matches
    results_2026 = [r for r in results if r["date"].startswith(SEASON_YEAR)]
    matches_played = len(results_2026)
    log.info(f"2026 matches completed: {matches_played}")

    # Elo + Form
    elo = calculate_elo(results)
    form = calculate_form(results)

    log.info("Current Elo ratings:")
    for team in sorted(elo, key=lambda t: -elo[t]):
        log.info(f"  {SHORT_MAP.get(team, team):5s}: {elo[team]:.1f}")

    # Points table
    pts = calculate_points_2026(results_2026)

    # Remaining fixtures
    remaining = get_remaining_fixtures(results)
    matches_remaining = len(remaining)
    log.info(f"Remaining fixtures: {matches_remaining}")

    # Simulation
    log.info(f"Running Monte Carlo ({N_SIM:,} iterations)...")
    sim = run_monte_carlo(CANONICAL_TEAMS, remaining, pts, elo, form)

    if not sanity_check(sim):
        log.error(
            "Sanity check FAILED — simulation output looks wrong. "
            "projections.json NOT updated."
        )
        sys.exit(1)

    log.info("Simulation complete. Playoff probabilities (Elo):")
    for team in sorted(CANONICAL_TEAMS, key=lambda t: -sim["elo"]["playoff_pct"][t]):
        log.info(
            f"  {SHORT_MAP.get(team, team):5s}: "
            f"Elo {sim['elo']['playoff_pct'][team]}%  "
            f"Form {sim['form']['playoff_pct'][team]}%"
        )

    # Build updated projections.json
    today = datetime.today().strftime("%Y-%m-%d")
    new_proj = deepcopy(existing_proj)
    new_proj["last_updated"] = today
    new_proj["matches_played"] = matches_played
    new_proj["matches_remaining"] = matches_remaining
    new_proj["pre_season"] = matches_played == 0
    new_proj["model_note"] = (
        f"Elo ratings calculated from all IPL results through {today}. "
        "Monte Carlo simulation uses 100,000 iterations per model."
    )

    for team_entry in new_proj["teams"]:
        name = team_entry["name"]
        if name not in CANONICAL_TEAMS:
            continue

        elo_pct = sim["elo"]["playoff_pct"][name]
        form_pct = sim["form"]["playoff_pct"][name]

        team_entry["played"] = sum(
            1 for r in results_2026
            if r["team1"] == name or r["team2"] == name
        )
        team_entry["won"] = sum(
            1 for r in results_2026
            if r["winner"] == name
        )
        team_entry["lost"] = team_entry["played"] - team_entry["won"]
        team_entry["points"] = pts.get(name, 0)

        team_entry["models"]["elo"]["playoff_pct"] = elo_pct
        team_entry["models"]["elo"]["rank_probs"] = sim["elo"]["rank_probs"][name]
        team_entry["models"]["form"]["playoff_pct"] = form_pct
        team_entry["models"]["form"]["rank_probs"] = sim["form"]["rank_probs"][name]

        team_entry["factors"]["elo_score"] = round(elo.get(name, ELO_BASE), 1)
        team_entry["factors"]["form_score"] = round(form.get(name, 0.5), 3)

        # Append to history — never overwrite
        hist_elo = team_entry.get("history", {}).get("elo", [])
        hist_form = team_entry.get("history", {}).get("form", [])
        hist_elo.append(elo_pct)
        hist_form.append(form_pct)
        team_entry["history"] = {"elo": hist_elo, "form": hist_form}

    # Write projections.json
    with open(PROJECTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(new_proj, f, indent=2, ensure_ascii=False)
    log.info(f"projections.json updated → {PROJECTIONS_JSON}")

    # Write fixtures.json
    update_fixtures_json(remaining)
    log.info(f"fixtures.json updated → {FIXTURES_JSON}")

    log.info("=== update_projections.py done ===\n")


if __name__ == "__main__":
    main()
