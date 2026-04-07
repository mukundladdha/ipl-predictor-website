#!/usr/bin/env python3
"""
calculate_player_stats.py
Scrapes real IPL 2026 player stats from Cricbuzz → public/data/player_stats.json

Batting:  mostRuns embedded JSON from Cricbuzz series stats page
Bowling:  individual match scorecards (scorecard-bowl-grid divs)
"""
import json, logging, re, time
from collections import defaultdict
from datetime import date as dt_date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT     = Path(__file__).parent.parent
OUT_PATH = ROOT / "public" / "data" / "player_stats.json"
LOG_PATH = ROOT / "logs" / "player_stats_log.txt"
PROJ_PATH = ROOT / "public" / "data" / "projections.json"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ── Cricbuzz ───────────────────────────────────────────────────────────────────
CB_SERIES_ID  = "9241"
CB_STATS_URL  = f"https://m.cricbuzz.com/cricket-series/{CB_SERIES_ID}/ipl-2026/stats"
CB_MATCHES_URL = f"https://m.cricbuzz.com/cricket-series/{CB_SERIES_ID}/ipl-2026/matches"
CB_SCORECARD  = "https://m.cricbuzz.com/live-cricket-scorecard"

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
REQUEST_DELAY = 1.5

# ── Team / Role mappings ───────────────────────────────────────────────────────

TEAM_COLORS = {
    "RCB": "#D4001A", "MI": "#004BA0", "KKR": "#3B2172", "CSK": "#F9CD05",
    "SRH": "#F26522", "RR": "#E83673", "DC": "#00008B", "PBKS": "#ED1F27",
    "GT": "#1B2133", "LSG": "#A0522D",
}

PLAYER_TEAM = {
    # RCB
    "Virat Kohli": "RCB", "Devdutt Padikkal": "RCB", "Rajat Patidar": "RCB",
    "Glenn Maxwell": "RCB", "Krunal Pandya": "RCB", "Phil Salt": "RCB",
    "Josh Hazlewood": "RCB", "Jacob Duffy": "RCB", "Mohammed Siraj": "RCB",
    "Suyash Sharma": "RCB", "Liam Livingstone": "RCB",
    # MI
    "Rohit Sharma": "MI", "Suryakumar Yadav": "MI", "Tilak Varma": "MI",
    "Hardik Pandya": "MI", "Naman Dhir": "MI", "Jasprit Bumrah": "MI",
    "Ryan Rickelton": "MI", "Will Jacks": "MI",
    # KKR
    "Ajinkya Rahane": "KKR", "Venkatesh Iyer": "KKR", "Sunil Narine": "KKR",
    "Andre Russell": "KKR", "Varun Chakaravarthy": "KKR", "Harshit Rana": "KKR",
    "Angkrish Raghuvanshi": "KKR", "Quinton de Kock": "KKR",
    # SRH
    "Travis Head": "SRH", "Abhishek Sharma": "SRH",
    "Rassie van der Dussen": "SRH", "Heinrich Klaasen": "SRH",
    "Pat Cummins": "SRH", "Bhuvneshwar Kumar": "SRH", "Harshal Patel": "SRH",
    "Nitish Kumar Reddy": "SRH", "Ishan Kishan": "SRH",
    # CSK
    "Ruturaj Gaikwad": "CSK", "MS Dhoni": "CSK", "Devon Conway": "CSK",
    "Shivam Dube": "CSK", "Deepak Chahar": "CSK", "Ravindra Jadeja": "CSK",
    "Matheesha Pathirana": "CSK",
    # RR
    "Sanju Samson": "RR", "Yashasvi Jaiswal": "RR", "Jos Buttler": "RR",
    "Riyan Parag": "RR", "Trent Boult": "RR", "Jofra Archer": "RR",
    "Dhruv Jurel": "RR",
    # DC
    "David Warner": "DC", "Axar Patel": "DC", "Kuldeep Yadav": "DC",
    "Tristan Stubbs": "DC", "KL Rahul": "DC", "Jake Fraser-McGurk": "DC",
    "Faf du Plessis": "DC",
    # PBKS
    "Prabhsimran Singh": "PBKS", "Shashank Singh": "PBKS",
    "Arshdeep Singh": "PBKS", "Sam Curran": "PBKS",
    "Sameer Rizvi": "PBKS", "Harnoor Pannu": "PBKS",
    # GT
    "Shubman Gill": "GT", "Sai Sudharsan": "GT", "Rashid Khan": "GT",
    "Kagiso Rabada": "GT", "Mohammed Shami": "GT",
    "Prasidh Krishna": "GT", "Kumar Kushagra": "GT",
    "Noor Ahmad": "GT",
    # LSG
    "Nicholas Pooran": "LSG", "Ravi Bishnoi": "LSG",
    "Mohsin Khan": "LSG", "Avesh Khan": "LSG",
    "Sarfaraz Khan": "LSG", "Cooper Connolly": "LSG",
    "David Miller": "LSG", "Jaydev Unadkat": "LSG",
    # RR
    "Vaibhav Sooryavanshi": "RR", "Kartik Tyagi": "RR",
    "Yuzvendra Chahal": "RR",
    # KKR
    "Nandre Burger": "KKR",
    # MI
    "Naman Dhir": "MI", "Robin Minz": "MI", "Hardik Pandya": "MI",
    # CSK
    "Lungi Ngidi": "CSK", "Matheesha Pathirana": "CSK",
    # PBKS
    "Vijaykumar Vyshak": "PBKS",
}

PLAYER_ROLE = {
    "Virat Kohli": "batter", "Devdutt Padikkal": "batter", "Rajat Patidar": "batter",
    "Phil Salt": "wicketkeeper", "Travis Head": "batter", "Abhishek Sharma": "batter",
    "Rassie van der Dussen": "batter", "Heinrich Klaasen": "wicketkeeper",
    "Rohit Sharma": "batter", "Suryakumar Yadav": "batter", "Tilak Varma": "batter",
    "Ajinkya Rahane": "batter", "Ruturaj Gaikwad": "batter", "Devon Conway": "batter",
    "MS Dhoni": "wicketkeeper", "Yashasvi Jaiswal": "batter",
    "Sanju Samson": "wicketkeeper", "Jos Buttler": "batter", "Naman Dhir": "batter",
    "Glenn Maxwell": "allrounder", "Krunal Pandya": "allrounder",
    "Hardik Pandya": "allrounder", "Sunil Narine": "allrounder",
    "Andre Russell": "allrounder", "Pat Cummins": "allrounder",
    "Shivam Dube": "allrounder", "Ravindra Jadeja": "allrounder",
    "Venkatesh Iyer": "allrounder", "Riyan Parag": "allrounder",
    "Axar Patel": "allrounder", "Nitish Kumar Reddy": "allrounder",
    "Sameer Rizvi": "batter", "Angkrish Raghuvanshi": "batter",
    "Ryan Rickelton": "batter", "Dhruv Jurel": "wicketkeeper",
    "Sai Sudharsan": "batter", "Shubman Gill": "batter",
    "Nicholas Pooran": "wicketkeeper", "KL Rahul": "wicketkeeper",
    "Ishan Kishan": "wicketkeeper",
    "Josh Hazlewood": "bowler", "Jacob Duffy": "bowler",
    "Mohammed Siraj": "bowler", "Suyash Sharma": "bowler",
    "Jasprit Bumrah": "bowler", "Bhuvneshwar Kumar": "bowler",
    "Harshal Patel": "bowler", "Varun Chakaravarthy": "bowler",
    "Harshit Rana": "bowler", "Deepak Chahar": "bowler",
    "Trent Boult": "bowler", "Jofra Archer": "bowler",
    "Rashid Khan": "bowler", "Kuldeep Yadav": "bowler",
    "Kagiso Rabada": "bowler", "Mohammed Shami": "bowler",
    "Prasidh Krishna": "bowler", "Arshdeep Singh": "bowler",
    "Sam Curran": "allrounder", "Ravi Bishnoi": "bowler",
    "Mohsin Khan": "bowler", "Avesh Khan": "bowler",
    "Matheesha Pathirana": "bowler",
}

# ── HTTP helper ────────────────────────────────────────────────────────────────

def get(session, url, **kwargs):
    try:
        resp = session.get(url, headers=HEADERS, timeout=15, **kwargs)
        resp.raise_for_status()
        return resp
    except Exception as e:
        log.warning(f"  GET failed {url}: {e}")
        return None

# ── Batting stats from Cricbuzz stats page ─────────────────────────────────────

def fetch_batting_stats(session):
    """Returns list of dicts: name, matches, innings, runs, avg, sr, fours, sixes"""
    log.info("Fetching batting stats (mostRuns)…")
    resp = get(session, CB_STATS_URL)
    if not resp:
        return []

    html = resp.text
    # mostRuns data is embedded as escaped JSON in the HTML
    # Quotes appear as \" in the raw HTML string
    # Format: {\"values\":[\"player_id\",\"name\",\"matches\",\"innings\",\"runs\",\"avg\",\"sr\",\"4s\",\"6s\"]}
    pattern = r'\\\"values\\\":\[\\\"(\d+)\\\",\\\"([^\\\"]+)\\\",\\\"(\d+)\\\",\\\"(\d+)\\\",\\\"(\d+)\\\",\\\"([\d.]+|--)\\\",\\\"([\d.]+|--)\\\",\\\"(\d+)\\\",\\\"(\d+)\\\"'
    rows = re.findall(pattern, html)

    if not rows:
        log.warning("  No batting rows found in stats page")
        return []

    results = []
    for pid, name, matches, innings, runs, avg, sr, fours, sixes in rows:
        results.append({
            "name": name,
            "matches": int(matches),
            "innings": int(innings),
            "runs": int(runs),
            "average": float(avg) if avg not in ("--", "-") else 0.0,
            "strike_rate": float(sr) if sr not in ("--", "-") else 0.0,
            "fours": int(fours),
            "sixes": int(sixes),
        })

    log.info(f"  Found {len(results)} batters")
    return results

# ── Match IDs from series page ─────────────────────────────────────────────────

def find_match_ids(session):
    """Returns list of (match_id, slug) for completed IPL 2026 matches.

    We seed with known match IDs (pattern: first match 149618, +11 each).
    Then extend dynamically from the series page for any newer matches.
    """
    log.info("Finding completed match IDs…")

    # Known completed matches — update as season progresses
    # Format: (cricbuzz_match_id, slug)
    KNOWN_MATCHES = [
        ("149618", "rcb-vs-srh-1st-match-ipl-2026"),
        ("149629", "mi-vs-kkr-2nd-match-ipl-2026"),
        ("149640", "rr-vs-csk-3rd-match-ipl-2026"),
        ("149651", "pbks-vs-gt-4th-match-ipl-2026"),
        ("149662", "lsg-vs-dc-5th-match-ipl-2026"),
        ("149673", "kkr-vs-srh-6th-match-ipl-2026"),
        ("149684", "csk-vs-pbks-7th-match-ipl-2026"),
        ("149695", "dc-vs-mi-8th-match-ipl-2026"),
        ("149699", "gt-vs-rr-9th-match-ipl-2026"),
        ("149710", "srh-vs-lsg-10th-match-ipl-2026"),
        ("149721", "rcb-vs-csk-11th-match-ipl-2026"),
    ]

    seen = {mid: slug for mid, slug in KNOWN_MATCHES}

    # Extend with any newer matches from the series page
    resp = get(session, CB_MATCHES_URL)
    if resp:
        html = resp.text
        raw = re.findall(
            r'/live-cricket-(?:scores|scorecard)/(\d+)/([a-z0-9-]+(?:ipl-2026|indian-premier-league-2026)[a-z0-9-]*)',
            html
        )
        for mid, slug in raw:
            if mid not in seen:
                seen[mid] = slug
                log.info(f"  New match found on series page: {mid}/{slug[:40]}")

    match_ids = sorted(seen.items(), key=lambda x: int(x[0]))
    log.info(f"  Total IPL matches: {len(match_ids)}")
    return match_ids

# ── Bowling stats from individual scorecards ───────────────────────────────────

def parse_scorecard(session, match_id, slug):
    """Returns bowling_rows with team info from a scorecard page.

    Each innings section has a team header. We extract the bowling team
    for each section by reading the innings team label.
    Returns list of dicts: name, team, overs, maidens, runs, wickets, economy
    """
    url = f"{CB_SCORECARD}/{match_id}/{slug}"
    resp = get(session, url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    bowling = []

    # The page has 2 innings blocks. Each contains batting then bowling section.
    # Team names appear in the innings header: "RCB Innings (20.0 Ovs)" etc.
    # We walk top-level blocks and track which team is bowling.
    # Extract teams from slug: "rcb-vs-srh-1st-match-ipl-2026" → RCB, SRH
    # Inn1: team2 bats (team1 bowls); Inn2: team1 bats (team2 bowls)
    slug_teams = re.match(r'([a-z]+)-vs-([a-z]+)-', slug)
    inn_bowling = []
    if slug_teams:
        t1 = slug_teams.group(1).upper()
        t2 = slug_teams.group(2).upper()
        if t1 in TEAM_COLORS and t2 in TEAM_COLORS:
            inn_bowling = [t1, t2]  # inn1: t1 bowls; inn2: t2 bowls

    # Bowling rows — cells layout: [O, M, R, W, NB, WD, ECO] (no name in cells)
    all_bowl_grids = soup.find_all("div", class_=lambda c: c and "scorecard-bowl-grid" in c)
    # Cricbuzz renders each innings twice (mobile + desktop views) — take first half only
    bowl_grids = all_bowl_grids[:len(all_bowl_grids) // 2]

    # Split grids into two innings: first header → inn1, second header → inn2
    inn1_grids, inn2_grids = [], []
    separator_found = False
    header_count = 0
    for row in bowl_grids:
        if not row.find("a"):
            header_count += 1
            if header_count == 2:
                separator_found = True
            continue
        if separator_found:
            inn2_grids.append(row)
        else:
            inn1_grids.append(row)

    def extract_bowl(grids, bowling_team):
        entries = []
        for row in grids:
            link = row.find("a")
            if not link:
                continue
            name = link.get_text(strip=True).replace(" (c)", "").strip()
            cells = [d.get_text(strip=True) for d in row.find_all("div")]
            nums = []
            for c in cells:
                try:
                    nums.append(float(c))
                except ValueError:
                    pass
            if len(nums) >= 5:
                entries.append({
                    "name": name,
                    "inferred_team": bowling_team,
                    "overs": nums[0],
                    "maidens": int(nums[1]),
                    "runs": int(nums[2]),
                    "wickets": int(nums[3]),
                    "economy": nums[-1],
                })
        return entries

    t1 = inn_bowling[0] if len(inn_bowling) > 0 else None
    t2 = inn_bowling[1] if len(inn_bowling) > 1 else None
    bowling = extract_bowl(inn1_grids, t1) + extract_bowl(inn2_grids, t2)

    return bowling

# ── Aggregate all stats ────────────────────────────────────────────────────────

def aggregate_stats(batting_season, bowling_scorecards, team_lookup=None):
    """
    batting_season: list of {name, matches, innings, runs, avg, sr, fours, sixes}
                   from Cricbuzz mostRuns (aggregated, authoritative)
    bowling_scorecards: dict name → {matches, innings, overs, runs, wickets, economy}
                       from scraped scorecards
    Returns: list of player dicts for player_stats.json
    """
    players = []
    seen = set()

    # Batting players first
    lookup = team_lookup or PLAYER_TEAM
    for b in batting_season:
        name = b["name"]
        if name in seen:
            continue
        seen.add(name)
        team = lookup.get(name, PLAYER_TEAM.get(name, "UNK"))
        role = PLAYER_ROLE.get(name, "batter")

        # Look up bowling if they also bowl
        bowl = bowling_scorecards.get(name)

        entry = {
            "name": name,
            "team": team,
            "team_color": TEAM_COLORS.get(team, "#888"),
            "role": role,
            "season_stats": {
                "matches": b["matches"],
                "innings": b["innings"],
                "runs": b["runs"],
                "average": b["average"],
                "strike_rate": b["strike_rate"],
                "fours": b["fours"],
                "sixes": b["sixes"],
            },
            "bowling_stats": {
                "matches": bowl["matches"],
                "innings": bowl["innings"],
                "overs": bowl["overs"],
                "runs_conceded": bowl["runs"],
                "wickets": bowl["wickets"],
                "economy": bowl["economy"],
            } if bowl and bowl["wickets"] > 0 else None,
        }
        players.append(entry)

    # Bowlers not in batting list
    for name, bowl in bowling_scorecards.items():
        if name in seen or bowl["wickets"] == 0:
            continue
        seen.add(name)
        team = lookup.get(name, PLAYER_TEAM.get(name, "UNK"))
        role = PLAYER_ROLE.get(name, "bowler")
        players.append({
            "name": name,
            "team": team,
            "team_color": TEAM_COLORS.get(team, "#888"),
            "role": role,
            "season_stats": None,
            "bowling_stats": {
                "matches": bowl["matches"],
                "innings": bowl["innings"],
                "overs": bowl["overs"],
                "runs_conceded": bowl["runs"],
                "wickets": bowl["wickets"],
                "economy": bowl["economy"],
            },
        })

    return players

# ── Build leaderboards ─────────────────────────────────────────────────────────

def build_leaderboards(players):
    batters = [p for p in players if p["season_stats"] and p["season_stats"]["runs"] > 0]
    batters.sort(key=lambda p: p["season_stats"]["runs"], reverse=True)

    bowlers = [p for p in players if p["bowling_stats"] and p["bowling_stats"]["wickets"] > 0]
    bowlers.sort(key=lambda p: p["bowling_stats"]["wickets"], reverse=True)

    orange_cap = []
    for i, p in enumerate(batters[:15]):
        s = p["season_stats"]
        orange_cap.append({
            "rank": i + 1,
            "name": p["name"],
            "team": p["team"],
            "team_color": p["team_color"],
            "runs": s["runs"],
            "matches": s["matches"],
            "innings": s["innings"],
            "average": s["average"],
            "strike_rate": s["strike_rate"],
            "fours": s["fours"],
            "sixes": s["sixes"],
        })

    purple_cap = []
    for i, p in enumerate(bowlers[:15]):
        b = p["bowling_stats"]
        purple_cap.append({
            "rank": i + 1,
            "name": p["name"],
            "team": p["team"],
            "team_color": p["team_color"],
            "wickets": b["wickets"],
            "matches": b["matches"],
            "overs": b["overs"],
            "runs_conceded": b["runs_conceded"],
            "economy": b["economy"],
        })

    return {"orange_cap": orange_cap, "purple_cap": purple_cap}

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("=== calculate_player_stats.py start ===")
    session = requests.Session()

    # 1. Batting stats from Cricbuzz mostRuns
    batting_season = fetch_batting_stats(session)

    # 2. Find match IDs and scrape bowling scorecards
    match_ids = find_match_ids(session)

    bowling_scorecards = defaultdict(lambda: {
        "matches": 0, "innings": 0, "overs": 0.0, "runs": 0, "wickets": 0, "economy": 0.0
    })
    runs_sum = defaultdict(float)
    overs_sum = defaultdict(float)

    player_teams_inferred = {}  # learned from scorecard context

    for match_id, slug in match_ids:
        log.info(f"  Parsing scorecard {match_id}/{slug[:40]}…")
        bowling_rows = parse_scorecard(session, match_id, slug)
        log.info(f"    → {len(bowling_rows)} bowling entries")
        for b in bowling_rows:
            name = b["name"]
            bowl = bowling_scorecards[name]
            bowl["matches"] += 1
            bowl["innings"] += 1
            bowl["overs"] += b["overs"]
            bowl["runs"] += b["runs"]
            bowl["wickets"] += b["wickets"]
            runs_sum[name] += b["runs"]
            overs_sum[name] += b["overs"]
            # Learn team from scorecard if not already known
            if name not in PLAYER_TEAM and b.get("inferred_team"):
                player_teams_inferred[name] = b["inferred_team"]
        time.sleep(REQUEST_DELAY)

    # Compute season economy
    for name, bowl in bowling_scorecards.items():
        if overs_sum[name] > 0:
            bowl["economy"] = round(runs_sum[name] / overs_sum[name], 2)

    # 3. Aggregate (merge inferred teams into PLAYER_TEAM for this run)
    combined_team = {**player_teams_inferred, **PLAYER_TEAM}  # PLAYER_TEAM takes priority
    players = aggregate_stats(batting_season, bowling_scorecards, combined_team)

    # 4. Build leaderboards
    leaderboards = build_leaderboards(players)

    # 5. Get matches played from projections
    matches_played = 0
    try:
        with open(PROJ_PATH) as f:
            proj = json.load(f)
        matches_played = proj.get("matches_played", 0)
    except Exception:
        pass

    out = {
        "last_updated": str(dt_date.today()),
        "season": "2026",
        "matches_covered": len(match_ids),
        "matches_played": matches_played,
        "players": players,
        "leaderboards": leaderboards,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    log.info(f"player_stats.json: {len(players)} players, "
             f"{len(leaderboards['orange_cap'])} batters, "
             f"{len(leaderboards['purple_cap'])} bowlers")
    log.info("=== calculate_player_stats.py done ===")


if __name__ == "__main__":
    main()
