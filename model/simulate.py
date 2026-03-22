"""
IPL 2026 Forecast — Elo + Form Monte Carlo Simulator
Reads Cricsheet ball-by-ball CSVs, derives match results,
runs 100,000 simulations of the remaining IPL 2026 season.
Outputs: public/data/projections.json, public/data/fixtures.json
"""

import os, glob, json, math, random
from collections import defaultdict
from datetime import date, datetime

random.seed(42)

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(BASE, "data", "raw")
OUT_DIR   = os.path.join(BASE, "public", "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Team config ──────────────────────────────────────────────────────────────
TEAM_META = {
    "Mumbai Indians":                {"short": "MI",   "color": "#004BA0"},
    "Kolkata Knight Riders":         {"short": "KKR",  "color": "#3A225D"},
    "Royal Challengers Bengaluru":   {"short": "RCB",  "color": "#EC1C24"},
    "Royal Challengers Bangalore":   {"short": "RCB",  "color": "#EC1C24"},  # old name alias
    "Punjab Kings":                  {"short": "PBKS", "color": "#ED1B24"},
    "Kings XI Punjab":               {"short": "PBKS", "color": "#ED1B24"},  # old name alias
    "Gujarat Titans":                {"short": "GT",   "color": "#1C4F9C"},
    "Lucknow Super Giants":          {"short": "LSG",  "color": "#A72056"},
    "Chennai Super Kings":           {"short": "CSK",  "color": "#FDB913"},
    "Sunrisers Hyderabad":           {"short": "SRH",  "color": "#FF822A"},
    "Delhi Capitals":                {"short": "DC",   "color": "#0078BC"},
    "Delhi Daredevils":              {"short": "DC",   "color": "#0078BC"},  # old name alias
    "Rajasthan Royals":              {"short": "RR",   "color": "#EA1A7F"},
    # defunct / merged teams — keep for Elo continuity but exclude from 2026
    "Deccan Chargers":               {"short": "DC2",  "color": "#888888"},
    "Pune Warriors":                 {"short": "PW",   "color": "#888888"},
    "Kochi Tuskers Kerala":          {"short": "KTK",  "color": "#888888"},
    "Rising Pune Supergiant":        {"short": "RPS",  "color": "#888888"},
    "Rising Pune Supergiants":       {"short": "RPS",  "color": "#888888"},
    "Gujarat Lions":                 {"short": "GL",   "color": "#888888"},
    "Pune Warriors India":           {"short": "PW",   "color": "#888888"},
}

CURRENT_TEAMS = {
    "Mumbai Indians", "Kolkata Knight Riders",
    "Royal Challengers Bengaluru", "Royal Challengers Bangalore",
    "Punjab Kings", "Gujarat Titans", "Lucknow Super Giants",
    "Chennai Super Kings", "Sunrisers Hyderabad",
    "Delhi Capitals", "Rajasthan Royals",
}

# Canonical names (merge old aliases)
CANONICAL = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Kings XI Punjab": "Punjab Kings",
    "Delhi Daredevils": "Delhi Capitals",
}

def canonical(name):
    return CANONICAL.get(name, name)

# ─── Parse match results from info CSVs ───────────────────────────────────────
def parse_matches():
    """Return list of match dicts from Cricsheet info CSVs."""
    matches = []
    info_files = sorted(glob.glob(os.path.join(RAW_DIR, "*_info.csv")))

    for fpath in info_files:
        info = {}
        teams = []
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Use csv-safe split: handle quoted values
                import csv as _csv
                row = next(_csv.reader([line]))
                if len(row) < 2:
                    continue
                # Format: type, key [, value]
                # e.g. "info,team,Sunrisers Hyderabad" or "version,2.1.0"
                if row[0] != "info":
                    continue
                key = row[1]
                val = row[2].strip() if len(row) > 2 else ""

                if key == "team":
                    teams.append(canonical(val))
                elif key == "winner":
                    info["winner"] = canonical(val)
                elif key == "date":
                    info["date"] = val
                elif key == "season":
                    info["season"] = val
                elif key == "outcome":
                    if val in ("no result", "tie"):
                        info["skip"] = True

        if info.get("skip"):
            continue
        if "winner" not in info or len(teams) < 2:
            continue
        if not all(t in TEAM_META for t in teams):
            continue

        raw_date = info["date"]
        try:
            # Cricsheet uses YYYY/MM/DD in some files, YYYY-MM-DD in others
            match_date = datetime.strptime(raw_date, "%Y/%m/%d").date()
        except ValueError:
            try:
                match_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                continue

        matches.append({
            "date":   match_date,
            "team1":  teams[0],
            "team2":  teams[1],
            "winner": info["winner"],
            "season": info.get("season", ""),
        })

    matches.sort(key=lambda m: m["date"])
    return matches

# ─── Elo model ────────────────────────────────────────────────────────────────
ELO_K   = 32
ELO_BASE = 1000

def expected(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 400))

def update_elo(ratings, winner, loser):
    ea = expected(ratings[winner], ratings[loser])
    ratings[winner] += ELO_K * (1 - ea)
    ratings[loser]  += ELO_K * (0 - (1 - ea))

def build_elo(matches):
    ratings = defaultdict(lambda: ELO_BASE)
    for m in matches:
        update_elo(ratings, m["winner"],
                   m["team2"] if m["winner"] == m["team1"] else m["team1"])
    return dict(ratings)

# ─── Form model ───────────────────────────────────────────────────────────────
DECAY = [0.75 ** i for i in range(12)]  # most recent = index 0, last 12 matches

def build_form(matches, as_of=None):
    """Return form score ∈ [0,1] per team from last 12 matches."""
    recent = defaultdict(list)  # team -> list of 1/0 (win/loss), most recent first
    relevant = [m for m in matches if as_of is None or m["date"] <= as_of]

    for m in reversed(relevant):
        w, l = m["winner"], (m["team2"] if m["winner"] == m["team1"] else m["team1"])
        if len(recent[w]) < 12:
            recent[w].append(1)
        if len(recent[l]) < 12:
            recent[l].append(0)

    scores = {}
    for team, results in recent.items():
        w_sum = sum(DECAY[i] * r for i, r in enumerate(results))
        d_sum = sum(DECAY[i] for i in range(len(results)))
        scores[team] = round(w_sum / d_sum, 4) if d_sum else 0.5

    return scores

# ─── IPL 2026 schedule (Phase 1 announced) ───────────────────────────────────
IPL_2026_FIXTURES_ALL = [
    # Phase 1 fixtures (announced)
    {"id":  1, "team1": "Royal Challengers Bengaluru", "team2": "Sunrisers Hyderabad",  "date": "2026-03-28", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id":  2, "team1": "Mumbai Indians",              "team2": "Kolkata Knight Riders", "date": "2026-03-29", "venue": "Wankhede Stadium, Mumbai"},
    {"id":  3, "team1": "Rajasthan Royals",            "team2": "Chennai Super Kings",   "date": "2026-03-30", "venue": "Barsapara Cricket Stadium, Guwahati"},
    {"id":  4, "team1": "Punjab Kings",                "team2": "Gujarat Titans",        "date": "2026-03-31", "venue": "PCA Stadium, New Chandigarh"},
    {"id":  5, "team1": "Lucknow Super Giants",        "team2": "Delhi Capitals",        "date": "2026-03-31", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id":  6, "team1": "Kolkata Knight Riders",       "team2": "Sunrisers Hyderabad",   "date": "2026-04-01", "venue": "Eden Gardens, Kolkata"},
    {"id":  7, "team1": "Chennai Super Kings",         "team2": "Royal Challengers Bengaluru", "date": "2026-04-02", "venue": "Barsapara Cricket Stadium, Guwahati"},
    {"id":  8, "team1": "Mumbai Indians",              "team2": "Punjab Kings",          "date": "2026-04-03", "venue": "Wankhede Stadium, Mumbai"},
    {"id":  9, "team1": "Delhi Capitals",              "team2": "Mumbai Indians",        "date": "2026-04-04", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 10, "team1": "Gujarat Titans",              "team2": "Rajasthan Royals",      "date": "2026-04-04", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 11, "team1": "Lucknow Super Giants",        "team2": "Kolkata Knight Riders", "date": "2026-04-05", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id": 12, "team1": "Sunrisers Hyderabad",         "team2": "Chennai Super Kings",   "date": "2026-04-06", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
    {"id": 13, "team1": "Royal Challengers Bengaluru", "team2": "Gujarat Titans",        "date": "2026-04-07", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 14, "team1": "Punjab Kings",                "team2": "Rajasthan Royals",      "date": "2026-04-08", "venue": "PCA Stadium, New Chandigarh"},
    {"id": 15, "team1": "Delhi Capitals",              "team2": "Lucknow Super Giants",  "date": "2026-04-09", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 16, "team1": "Mumbai Indians",              "team2": "Sunrisers Hyderabad",   "date": "2026-04-10", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 17, "team1": "Kolkata Knight Riders",       "team2": "Chennai Super Kings",   "date": "2026-04-11", "venue": "Eden Gardens, Kolkata"},
    {"id": 18, "team1": "Royal Challengers Bengaluru", "team2": "Punjab Kings",          "date": "2026-04-12", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    # Phase 2+ (estimated based on round-robin pattern)
    {"id": 19, "team1": "Gujarat Titans",              "team2": "Mumbai Indians",        "date": "2026-04-14", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 20, "team1": "Rajasthan Royals",            "team2": "Kolkata Knight Riders", "date": "2026-04-15", "venue": "Sawai Mansingh Stadium, Jaipur"},
    {"id": 21, "team1": "Chennai Super Kings",         "team2": "Delhi Capitals",        "date": "2026-04-16", "venue": "MA Chidambaram Stadium, Chennai"},
    {"id": 22, "team1": "Lucknow Super Giants",        "team2": "Punjab Kings",          "date": "2026-04-17", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id": 23, "team1": "Sunrisers Hyderabad",         "team2": "Rajasthan Royals",      "date": "2026-04-18", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
    {"id": 24, "team1": "Mumbai Indians",              "team2": "Royal Challengers Bengaluru", "date": "2026-04-19", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 25, "team1": "Kolkata Knight Riders",       "team2": "Gujarat Titans",        "date": "2026-04-20", "venue": "Eden Gardens, Kolkata"},
    {"id": 26, "team1": "Delhi Capitals",              "team2": "Chennai Super Kings",   "date": "2026-04-21", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 27, "team1": "Punjab Kings",                "team2": "Sunrisers Hyderabad",   "date": "2026-04-22", "venue": "PCA Stadium, New Chandigarh"},
    {"id": 28, "team1": "Rajasthan Royals",            "team2": "Lucknow Super Giants",  "date": "2026-04-23", "venue": "Sawai Mansingh Stadium, Jaipur"},
    {"id": 29, "team1": "Royal Challengers Bengaluru", "team2": "Kolkata Knight Riders", "date": "2026-04-24", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 30, "team1": "Mumbai Indians",              "team2": "Gujarat Titans",        "date": "2026-04-25", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 31, "team1": "Chennai Super Kings",         "team2": "Punjab Kings",          "date": "2026-04-26", "venue": "MA Chidambaram Stadium, Chennai"},
    {"id": 32, "team1": "Sunrisers Hyderabad",         "team2": "Delhi Capitals",        "date": "2026-04-27", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
    {"id": 33, "team1": "Kolkata Knight Riders",       "team2": "Lucknow Super Giants",  "date": "2026-04-28", "venue": "Eden Gardens, Kolkata"},
    {"id": 34, "team1": "Gujarat Titans",              "team2": "Chennai Super Kings",   "date": "2026-04-29", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 35, "team1": "Mumbai Indians",              "team2": "Rajasthan Royals",      "date": "2026-04-30", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 36, "team1": "Royal Challengers Bengaluru", "team2": "Delhi Capitals",        "date": "2026-05-01", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 37, "team1": "Punjab Kings",                "team2": "Kolkata Knight Riders", "date": "2026-05-02", "venue": "PCA Stadium, New Chandigarh"},
    {"id": 38, "team1": "Lucknow Super Giants",        "team2": "Sunrisers Hyderabad",   "date": "2026-05-03", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id": 39, "team1": "Rajasthan Royals",            "team2": "Royal Challengers Bengaluru", "date": "2026-05-04", "venue": "Sawai Mansingh Stadium, Jaipur"},
    {"id": 40, "team1": "Chennai Super Kings",         "team2": "Mumbai Indians",        "date": "2026-05-05", "venue": "MA Chidambaram Stadium, Chennai"},
    {"id": 41, "team1": "Delhi Capitals",              "team2": "Gujarat Titans",        "date": "2026-05-06", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 42, "team1": "Sunrisers Hyderabad",         "team2": "Punjab Kings",          "date": "2026-05-07", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
    {"id": 43, "team1": "Kolkata Knight Riders",       "team2": "Rajasthan Royals",      "date": "2026-05-08", "venue": "Eden Gardens, Kolkata"},
    {"id": 44, "team1": "Lucknow Super Giants",        "team2": "Royal Challengers Bengaluru", "date": "2026-05-09", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id": 45, "team1": "Gujarat Titans",              "team2": "Punjab Kings",          "date": "2026-05-10", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 46, "team1": "Mumbai Indians",              "team2": "Delhi Capitals",        "date": "2026-05-11", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 47, "team1": "Chennai Super Kings",         "team2": "Sunrisers Hyderabad",   "date": "2026-05-12", "venue": "MA Chidambaram Stadium, Chennai"},
    {"id": 48, "team1": "Royal Challengers Bengaluru", "team2": "Lucknow Super Giants",  "date": "2026-05-13", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 49, "team1": "Rajasthan Royals",            "team2": "Gujarat Titans",        "date": "2026-05-14", "venue": "Sawai Mansingh Stadium, Jaipur"},
    {"id": 50, "team1": "Kolkata Knight Riders",       "team2": "Mumbai Indians",        "date": "2026-05-15", "venue": "Eden Gardens, Kolkata"},
    {"id": 51, "team1": "Delhi Capitals",              "team2": "Punjab Kings",          "date": "2026-05-16", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 52, "team1": "Sunrisers Hyderabad",         "team2": "Lucknow Super Giants",  "date": "2026-05-17", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
    {"id": 53, "team1": "Chennai Super Kings",         "team2": "Rajasthan Royals",      "date": "2026-05-18", "venue": "MA Chidambaram Stadium, Chennai"},
    {"id": 54, "team1": "Royal Challengers Bengaluru", "team2": "Mumbai Indians",        "date": "2026-05-19", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 55, "team1": "Gujarat Titans",              "team2": "Kolkata Knight Riders", "date": "2026-05-20", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 56, "team1": "Punjab Kings",                "team2": "Delhi Capitals",        "date": "2026-05-21", "venue": "PCA Stadium, New Chandigarh"},
    {"id": 57, "team1": "Lucknow Super Giants",        "team2": "Chennai Super Kings",   "date": "2026-05-22", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id": 58, "team1": "Sunrisers Hyderabad",         "team2": "Royal Challengers Bengaluru", "date": "2026-05-23", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
    {"id": 59, "team1": "Rajasthan Royals",            "team2": "Mumbai Indians",        "date": "2026-05-24", "venue": "Sawai Mansingh Stadium, Jaipur"},
    {"id": 60, "team1": "Gujarat Titans",              "team2": "Delhi Capitals",        "date": "2026-05-25", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 61, "team1": "Kolkata Knight Riders",       "team2": "Punjab Kings",          "date": "2026-05-26", "venue": "Eden Gardens, Kolkata"},
    {"id": 62, "team1": "Chennai Super Kings",         "team2": "Lucknow Super Giants",  "date": "2026-05-27", "venue": "MA Chidambaram Stadium, Chennai"},
    {"id": 63, "team1": "Mumbai Indians",              "team2": "Sunrisers Hyderabad",   "date": "2026-05-27", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 64, "team1": "Delhi Capitals",              "team2": "Rajasthan Royals",      "date": "2026-05-28", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 65, "team1": "Royal Challengers Bengaluru", "team2": "Chennai Super Kings",   "date": "2026-05-28", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 66, "team1": "Punjab Kings",                "team2": "Lucknow Super Giants",  "date": "2026-05-29", "venue": "PCA Stadium, New Chandigarh"},
    {"id": 67, "team1": "Gujarat Titans",              "team2": "Sunrisers Hyderabad",   "date": "2026-05-29", "venue": "Narendra Modi Stadium, Ahmedabad"},
    {"id": 68, "team1": "Kolkata Knight Riders",       "team2": "Delhi Capitals",        "date": "2026-05-30", "venue": "Eden Gardens, Kolkata"},
    {"id": 69, "team1": "Rajasthan Royals",            "team2": "Punjab Kings",          "date": "2026-05-30", "venue": "Sawai Mansingh Stadium, Jaipur"},
    {"id": 70, "team1": "Mumbai Indians",              "team2": "Chennai Super Kings",   "date": "2026-05-31", "venue": "Wankhede Stadium, Mumbai"},
    {"id": 71, "team1": "Royal Challengers Bengaluru", "team2": "Gujarat Titans",        "date": "2026-05-31", "venue": "M. Chinnaswamy Stadium, Bengaluru"},
    {"id": 72, "team1": "Lucknow Super Giants",        "team2": "Rajasthan Royals",      "date": "2026-06-01", "venue": "BRSABV Ekana Cricket Stadium, Lucknow"},
    {"id": 73, "team1": "Delhi Capitals",              "team2": "Kolkata Knight Riders", "date": "2026-06-01", "venue": "Arun Jaitley Stadium, Delhi"},
    {"id": 74, "team1": "Sunrisers Hyderabad",         "team2": "Mumbai Indians",        "date": "2026-06-02", "venue": "Rajiv Gandhi Intl. Stadium, Hyderabad"},
]

CURRENT_TEAM_NAMES = [
    "Mumbai Indians", "Kolkata Knight Riders", "Royal Challengers Bengaluru",
    "Punjab Kings", "Gujarat Titans", "Lucknow Super Giants",
    "Chennai Super Kings", "Sunrisers Hyderabad", "Delhi Capitals", "Rajasthan Royals",
]

# NRR estimates from IPL 2025 final standings (seed for 2026)
NRR_SEED = {
    "Punjab Kings": 0.55, "Royal Challengers Bengaluru": 0.48,
    "Gujarat Titans": 0.87, "Mumbai Indians": 0.23,
    "Delhi Capitals": 0.12, "Sunrisers Hyderabad": 0.05,
    "Lucknow Super Giants": -0.10, "Kolkata Knight Riders": -0.18,
    "Rajasthan Royals": -0.52, "Chennai Super Kings": -0.71,
}

HOME_ADVANTAGE = 0.04  # ~4% boost for home team

VENUE_HOME = {
    "Wankhede Stadium, Mumbai": "Mumbai Indians",
    "Eden Gardens, Kolkata": "Kolkata Knight Riders",
    "M. Chinnaswamy Stadium, Bengaluru": "Royal Challengers Bengaluru",
    "PCA Stadium, New Chandigarh": "Punjab Kings",
    "Narendra Modi Stadium, Ahmedabad": "Gujarat Titans",
    "BRSABV Ekana Cricket Stadium, Lucknow": "Lucknow Super Giants",
    "MA Chidambaram Stadium, Chennai": "Chennai Super Kings",
    "Rajiv Gandhi Intl. Stadium, Hyderabad": "Sunrisers Hyderabad",
    "Arun Jaitley Stadium, Delhi": "Delhi Capitals",
    "Sawai Mansingh Stadium, Jaipur": "Rajasthan Royals",
    "Barsapara Cricket Stadium, Guwahati": None,
}

# ─── Monte Carlo simulation ────────────────────────────────────────────────────
N_SIMS = 100_000

def win_prob_elo(elo_ratings, t1, t2, venue):
    r1 = elo_ratings.get(t1, ELO_BASE)
    r2 = elo_ratings.get(t2, ELO_BASE)
    home = VENUE_HOME.get(venue)
    if home == t1:
        r1 += 30
    elif home == t2:
        r2 += 30
    return expected(r1, r2)

def win_prob_form(form_scores, t1, t2, venue):
    s1 = form_scores.get(t1, 0.5)
    s2 = form_scores.get(t2, 0.5)
    home = VENUE_HOME.get(venue)
    if home == t1:
        s1 += HOME_ADVANTAGE
    elif home == t2:
        s2 += HOME_ADVANTAGE
    total = s1 + s2
    return s1 / total if total > 0 else 0.5

def simulate_season(win_probs, played_pts, remaining_fixtures):
    """One simulation run. Returns final points dict."""
    pts = dict(played_pts)
    for fix in remaining_fixtures:
        p = win_probs[fix["id"]]
        if random.random() < p:
            pts[fix["team1"]] = pts.get(fix["team1"], 0) + 2
        else:
            pts[fix["team2"]] = pts.get(fix["team2"], 0) + 2
    return pts

def run_monte_carlo(win_probs, played_pts, remaining_fixtures, teams):
    playoff_counts = defaultdict(int)
    rank_counts    = defaultdict(lambda: defaultdict(int))

    for _ in range(N_SIMS):
        pts = simulate_season(win_probs, played_pts, remaining_fixtures)
        ranked = sorted(teams, key=lambda t: (pts.get(t, 0), NRR_SEED.get(t, 0)), reverse=True)
        for i, t in enumerate(ranked):
            rank_counts[t][i] += 1
        for t in ranked[:4]:
            playoff_counts[t] += 1

    playoff_pct = {t: round(playoff_counts[t] / N_SIMS * 100) for t in teams}
    rank_probs  = {
        t: [round(rank_counts[t][i] / N_SIMS * 100) for i in range(10)]
        for t in teams
    }
    return playoff_pct, rank_probs

# ─── Compute historical playoff % snapshots for BumpsChart ───────────────────
SNAPSHOT_DATES = [
    # (label, cutoff_date_inclusive)
    ("Pre-season",   date(2026, 3, 27)),
    ("MD 3",         date(2026, 4,  2)),
    ("MD 6",         date(2026, 4,  9)),
    ("MD 9",         date(2026, 4, 16)),
    ("MD 12",        date(2026, 4, 22)),
    ("MD 14",        date(2026, 4, 28)),
]

def compute_history(all_matches, fixtures_all, teams):
    """Pre-season only for now (no 2026 matches yet).
    Returns dict: team -> {"elo": [vals], "form": [vals]}"""
    history_elo  = defaultdict(list)
    history_form = defaultdict(list)

    today = date.today()
    ipl_2025_end = date(2025, 6, 3)

    for label, cutoff in SNAPSHOT_DATES:
        cutoff_actual = min(cutoff, today)
        hist_matches = [m for m in all_matches if m["date"] <= cutoff_actual]

        # Elo as of cutoff
        elo  = build_elo(hist_matches)
        form = build_form(hist_matches, as_of=cutoff_actual)

        # Remaining fixtures after cutoff
        remaining = [f for f in fixtures_all
                     if datetime.strptime(f["date"], "%Y-%m-%d").date() > cutoff_actual]

        # Win probs at this snapshot
        wp_elo  = {f["id"]: win_prob_elo(elo, f["team1"], f["team2"], f["venue"])
                   for f in fixtures_all}
        wp_form = {f["id"]: win_prob_form(form, f["team1"], f["team2"], f["venue"])
                   for f in fixtures_all}

        played_pts = {t: 0 for t in teams}  # pre-season: 0 pts played

        pp_elo,  _ = run_monte_carlo(wp_elo,  played_pts, remaining, teams)
        pp_form, _ = run_monte_carlo(wp_form, played_pts, remaining, teams)

        for t in teams:
            history_elo[t].append(pp_elo.get(t, 0))
            history_form[t].append(pp_form.get(t, 0))

        if cutoff >= today:
            break  # don't project past today

    return {t: {"elo": history_elo[t], "form": history_form[t]} for t in teams}

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("Parsing match results from Cricsheet...")
    all_matches = parse_matches()
    ipl_matches = [m for m in all_matches
                   if m["team1"] in TEAM_META and m["team2"] in TEAM_META]
    print(f"  Loaded {len(ipl_matches)} IPL matches")

    # Build current Elo and Form (as of today, using all historical data)
    print("Building Elo ratings...")
    elo = build_elo(ipl_matches)
    print("Building Form scores...")
    form = build_form(ipl_matches)

    # Current season: 0 games played (season starts Mar 28)
    played_pts = {t: 0 for t in CURRENT_TEAM_NAMES}
    remaining  = IPL_2026_FIXTURES_ALL  # all fixtures are remaining

    # Win probability tables
    print("Computing win probabilities...")
    wp_elo  = {f["id"]: win_prob_elo(elo,  f["team1"], f["team2"], f["venue"])
               for f in IPL_2026_FIXTURES_ALL}
    wp_form = {f["id"]: win_prob_form(form, f["team1"], f["team2"], f["venue"])
               for f in IPL_2026_FIXTURES_ALL}

    # Monte Carlo — Elo
    print(f"Running {N_SIMS:,} Elo simulations...")
    pp_elo, rp_elo = run_monte_carlo(wp_elo, played_pts, remaining, CURRENT_TEAM_NAMES)

    # Monte Carlo — Form
    print(f"Running {N_SIMS:,} Form simulations...")
    pp_form, rp_form = run_monte_carlo(wp_form, played_pts, remaining, CURRENT_TEAM_NAMES)

    # Historical snapshots
    print("Computing historical snapshots (pre-season only)...")
    history = compute_history(ipl_matches, IPL_2026_FIXTURES_ALL, CURRENT_TEAM_NAMES)

    # ── Build projections.json ────────────────────────────────────────────────
    teams_out = []
    for name in CURRENT_TEAM_NAMES:
        meta  = TEAM_META[name]
        short = meta["short"]
        teams_out.append({
            "name":   name,
            "short":  short,
            "color":  meta["color"],
            "played": 0,
            "won":    0,
            "lost":   0,
            "nr":     0,
            "points": 0,
            "nrr":    NRR_SEED.get(name, 0.0),
            "models": {
                "elo":  {
                    "playoff_pct": pp_elo.get(name, 0),
                    "rank_probs":  rp_elo.get(name, [0]*10),
                },
                "form": {
                    "playoff_pct": pp_form.get(name, 0),
                    "rank_probs":  rp_form.get(name, [0]*10),
                },
            },
            "factors": {
                "elo_score":            round(elo.get(name, ELO_BASE)),
                "form_score":           round(form.get(name, 0.5), 3),
                "home_games_remaining": sum(
                    1 for f in IPL_2026_FIXTURES_ALL
                    if VENUE_HOME.get(f["venue"]) == name
                ),
                "nrr": NRR_SEED.get(name, 0.0),
            },
            "history": history[name],
            "key_players": {
                "Mumbai Indians":              "Rohit Sharma, Jasprit Bumrah, Suryakumar Yadav",
                "Kolkata Knight Riders":       "Cameron Green, Matheesha Pathirana, Rinku Singh",
                "Royal Challengers Bengaluru": "Virat Kohli, Phil Salt, Josh Hazlewood",
                "Punjab Kings":                "Arshdeep Singh, Shashank Singh, Lockie Ferguson",
                "Gujarat Titans":              "Shubman Gill, Jos Buttler, Rashid Khan",
                "Lucknow Super Giants":        "Mohammed Shami, Wanindu Hasaranga, Josh Inglis",
                "Chennai Super Kings":         "MS Dhoni, Sanju Samson, Ravindra Jadeja",
                "Sunrisers Hyderabad":         "Pat Cummins, Travis Head, Liam Livingstone",
                "Delhi Capitals":              "Axar Patel, Kuldeep Yadav, David Miller",
                "Rajasthan Royals":            "Vaibhav Suryavanshi, Ravi Bishnoi, Adam Milne",
            }.get(name, ""),
        })

    projections = {
        "last_updated":       str(date.today()),
        "season_complete":    False,
        "edition":            "IPL 2026 (19th edition)",
        "defending_champion": "Royal Challengers Bengaluru",
        "season_start":       "2026-03-28",
        "teams":              teams_out,
    }

    # ── Build fixtures.json (next 5 upcoming) ────────────────────────────────
    today_str = str(date.today())
    upcoming = [f for f in IPL_2026_FIXTURES_ALL if f["date"] >= today_str][:5]
    fixtures_out = {"fixtures": [
        {
            "id":    f["id"],
            "teamA": TEAM_META[f["team1"]]["short"],
            "teamB": TEAM_META[f["team2"]]["short"],
            "team1": f["team1"],
            "team2": f["team2"],
            "date":  f["date"],
            "venue": f["venue"],
        }
        for f in upcoming
    ]}

    # ── Write output ──────────────────────────────────────────────────────────
    proj_path = os.path.join(OUT_DIR, "projections.json")
    fix_path  = os.path.join(OUT_DIR, "fixtures.json")

    with open(proj_path, "w") as fh:
        json.dump(projections, fh, indent=2)
    with open(fix_path, "w") as fh:
        json.dump(fixtures_out, fh, indent=2)

    print(f"\n✓ Written {proj_path}")
    print(f"✓ Written {fix_path}")
    print("\nElo playoff odds:")
    for t in sorted(CURRENT_TEAM_NAMES, key=lambda x: -pp_elo.get(x, 0)):
        short = TEAM_META[t]["short"]
        print(f"  {short:5} elo={pp_elo.get(t,0):3}%  form={pp_form.get(t,0):3}%  "
              f"elo_rating={elo.get(t, ELO_BASE):.0f}  form={form.get(t, 0.5):.3f}")

if __name__ == "__main__":
    main()
