#!/usr/bin/env python3
"""
generate_match_story.py
Calls Gemini to write a data-backed match story after each new result.
Appends to public/data/stories.json (never overwrites).

Run: python scripts/generate_match_story.py
"""
import csv, json, logging, os, sys
from datetime import datetime
from pathlib import Path

ROOT         = Path(__file__).parent.parent
RESULTS_CSV  = ROOT / "data" / "results.csv"
PREV_PROJ    = ROOT / "data" / "projections_previous.json"
CURR_PROJ    = ROOT / "public" / "data" / "projections.json"
PLAYER_STATS = ROOT / "public" / "data" / "player_stats.json"
STORIES_JSON = ROOT / "public" / "data" / "stories.json"
LOG_PATH     = ROOT / "logs" / "story_log.txt"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

FULL_SHORT = {
    "Royal Challengers Bengaluru": "RCB", "Royal Challengers Bangalore": "RCB",
    "Mumbai Indians": "MI", "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK", "Sunrisers Hyderabad": "SRH",
    "Rajasthan Royals": "RR", "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS", "Gujarat Titans": "GT",
    "Lucknow Super Giants": "LSG",
}


def load_json(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_elo_pct(proj, short):
    for t in proj["teams"]:
        if t["short"] == short:
            return round(t["models"]["elo"]["playoff_pct"], 1)
    return 0.0


def load_results():
    rows = []
    with open(RESULTS_CSV, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return [r for r in rows if r.get("date", "").startswith("2026")]


def already_in_stories(match_id, stories):
    return any(s["match_id"] == match_id for s in stories)


def format_odds_changes(changes):
    lines = []
    for short, c in sorted(changes.items(), key=lambda x: -abs(x[1]["delta"])):
        sign = "+" if c["delta"] >= 0 else ""
        lines.append(
            f"  {short}: {c['before']}% → {c['after']}% ({sign}{c['delta']:+.1f}%)"
        )
    return "\n".join(lines)


def get_top_performers(player_stats, team1, team2):
    if not player_stats:
        return "No player data available.", "No player data available."
    teams = {team1, team2}
    batters = [
        p for p in player_stats.get("players", [])
        if p["team"] in teams and p.get("season_stats") and p["season_stats"]["balls_faced"] >= 3
    ]
    bowlers = [
        p for p in player_stats.get("players", [])
        if p["team"] in teams and p.get("bowling_stats") and p["bowling_stats"]["balls"] >= 6
    ]
    batters_sorted = sorted(batters, key=lambda p: p["season_stats"]["runs"], reverse=True)[:3]
    bowlers_sorted = sorted(bowlers, key=lambda p: (
        -p["bowling_stats"]["wickets"], p["bowling_stats"]["economy"]
    ))[:3]

    bat_str = ", ".join(
        f"{p['name']} ({p['team']}) {p['season_stats']['runs']}"
        f"({p['season_stats']['balls_faced']}) SR {p['season_stats']['strike_rate']}"
        for p in batters_sorted
    ) or "No batting data"

    bowl_str = ", ".join(
        f"{p['name']} ({p['team']}) {p['bowling_stats']['wickets']}"
        f"/{p['bowling_stats']['runs_conceded']} econ {p['bowling_stats']['economy']}"
        for p in bowlers_sorted
    ) or "No bowling data"

    return bat_str, bowl_str


def fallback_story(match, winner_short, loser_short, delta, new_pct, loser_pct, n):
    return (
        f"{match['winner']} beat "
        f"{match['team2'] if match['winner'] == match['team1'] else match['team1']} "
        f"in match {n} of IPL 2026. "
        f"The result shifted {winner_short}'s playoff probability by "
        f"+{delta:.1f}% to {new_pct:.1f}%. "
        f"{loser_short} drop to {loser_pct:.1f}% after the defeat. "
        f"Full analysis updating shortly."
    )


def call_gemini(prompt, api_key):
    """Call Gemini via REST API directly — no SDK, no versioning issues."""
    import requests as req
    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = req.post(url, json=payload, timeout=30)
    log.info(f"  Gemini HTTP {resp.status_code}")
    if resp.status_code != 200:
        log.error(f"  Gemini error body: {resp.text[:500]}")
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def main():
    log.info("=== generate_match_story.py start ===")

    # Load API key — from env (GitHub Actions) or .env file
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
            api_key = os.environ.get("GEMINI_API_KEY")
        except ImportError:
            pass

    use_gemini = bool(api_key)
    if not use_gemini:
        log.warning("GEMINI_API_KEY not set — will use fallback templates")

    results = load_results()
    if not results:
        log.info("No 2026 results — nothing to write")
        return

    stories_data = load_json(STORIES_JSON) or {"stories": []}
    stories = stories_data["stories"]

    prev_proj = load_json(PREV_PROJ)
    curr_proj = load_json(CURR_PROJ)
    player_stats = load_json(PLAYER_STATS)

    new_count = 0
    for i, r in enumerate(results):
        t1_full = r["team1"]; t2_full = r["team2"]
        t1 = FULL_SHORT.get(t1_full, t1_full[:3].upper())
        t2 = FULL_SHORT.get(t2_full, t2_full[:3].upper())
        winner_full = r["winner"]
        winner = FULL_SHORT.get(winner_full, winner_full[:3].upper())
        loser = t2 if winner == t1 else t1

        match_id = f"{t1.lower()}_vs_{t2.lower()}_{r['date'].replace('-','')}"
        if already_in_stories(match_id, stories):
            log.info(f"  Skipping {match_id} — already stored")
            continue

        # Odds changes
        if prev_proj and curr_proj:
            odds_changes = {}
            for team in curr_proj["teams"]:
                short = team["short"]
                before = get_elo_pct(prev_proj, short)
                after  = get_elo_pct(curr_proj, short)
                odds_changes[short] = {
                    "before": before, "after": after,
                    "delta": round(after - before, 1),
                }
            biggest_winner = max(odds_changes, key=lambda t: odds_changes[t]["delta"])
            biggest_loser  = min(odds_changes, key=lambda t: odds_changes[t]["delta"])
        else:
            odds_changes = {t1: {"before": 0, "after": 0, "delta": 0},
                           t2: {"before": 0, "after": 0, "delta": 0}}
            biggest_winner = winner; biggest_loser = loser

        winner_delta  = odds_changes.get(winner, {}).get("delta", 0)
        winner_new    = odds_changes.get(winner, {}).get("after", 0)
        loser_pct_new = odds_changes.get(loser,  {}).get("after", 0)

        bat_str, bowl_str = get_top_performers(player_stats, t1, t2)

        # Top performers for output
        top_perf = {}
        if player_stats:
            tp = player_stats.get("team_performers", {})
            t1_top = tp.get(t1, {})
            t2_top = tp.get(t2, {})
            batter_name = None; bowler_name = None
            for team_tp in [t1_top, t2_top]:
                if team_tp.get("top_batter") and not batter_name:
                    batter_name = team_tp["top_batter"]["name"]
                if team_tp.get("top_bowler") and not bowler_name:
                    bowler_name = team_tp["top_bowler"]["name"]
            top_perf = {"batter": batter_name, "bowler": bowler_name}

        # Generate story
        body = ""
        headline = ""

        if use_gemini:
            try:
                story_prompt = f"""You are a data journalist covering IPL 2026 for Duckworth — a playoff probability forecasting site.

Match: {t1_full} vs {t2_full}
Date: {r['date']}
Venue: {r.get('venue', 'TBD')}
Result: {winner_full} won by {r.get('margin', 'unknown margin')}

Playoff odds movement:
{format_odds_changes(odds_changes)}

Top performers:
Batting: {bat_str}
Bowling: {bowl_str}

Write a match story in exactly 3 paragraphs, maximum 160 words total.

Paragraph 1 (50 words max):
Lead with the single most surprising data point from the odds movement or player performance. Not the result — everyone knows the result. The data angle.

Paragraph 2 (60 words max):
Explain specifically how the playoff picture changed. Use exact percentages. Name the teams most affected. Be direct.

Paragraph 3 (50 words max):
One forward-looking observation. What does this mean for the next match or the wider season race? End with a specific question the model raises.

Rules:
- Every sentence must contain a number or %
- No cricket clichés (thriller, clinical, dominant)
- Conversational not formal
- Active voice only
- Return plain text, no markdown, no headers
"""
                body = call_gemini(story_prompt, api_key)
                log.info(f"  Gemini story generated ({len(body.split())} words)")

                headline_prompt = f"""Write one headline for this IPL match story.
Max 10 words. Must contain a specific number or %.
Punchy, data-led, not generic.
Story: {body}
Return the headline only, no punctuation at end."""
                headline = call_gemini(headline_prompt, api_key)
                log.info(f"  Headline: {headline}")

            except Exception as e:
                log.error(f"  Gemini failed: {e}")
                use_gemini_this = False
                body = ""

        if not body:
            body = fallback_story(r, winner, loser, winner_delta,
                                  winner_new, loser_pct_new, i + 1)
            headline = (f"{winner} {'+' if winner_delta >= 0 else ''}"
                        f"{winner_delta:.1f}% after match {i+1}")

        story = {
            "match_id": match_id,
            "date": r["date"],
            "teams": [t1, t2],
            "result": f"{winner_full} won by {r.get('margin', 'unknown')}",
            "headline": headline,
            "body": body,
            "odds_changes": odds_changes,
            "top_performers": top_perf,
            "generated_at": datetime.utcnow().isoformat(),
            "type": "match",
        }
        stories.append(story)
        new_count += 1
        log.info(f"  Appended story: {match_id}")

    stories_data["stories"] = stories
    STORIES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(STORIES_JSON, "w", encoding="utf-8") as f:
        json.dump(stories_data, f, indent=2, ensure_ascii=False)

    log.info(f"stories.json updated — {new_count} new stories")
    log.info("=== generate_match_story.py done ===")


if __name__ == "__main__":
    main()
