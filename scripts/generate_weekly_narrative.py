#!/usr/bin/env python3
"""
generate_weekly_narrative.py
Runs every Monday. Generates a 'state of the season' editorial via Gemini.
Appends to public/data/stories.json as type: "weekly".

Run: python scripts/generate_weekly_narrative.py
"""
import csv, json, logging, os
from datetime import date as dt_date, timedelta
from pathlib import Path

ROOT         = Path(__file__).parent.parent
PROJ         = ROOT / "public" / "data" / "projections.json"
STORIES_JSON = ROOT / "public" / "data" / "stories.json"
PLAYER_STATS = ROOT / "public" / "data" / "player_stats.json"
LOG_PATH     = ROOT / "logs" / "weekly_log.txt"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)


def load_json(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def week_label(today=None):
    today = today or dt_date.today()
    # IPL 2026 starts Mar 28
    season_start = dt_date(2026, 3, 28)
    week_n = max(1, ((today - season_start).days // 7) + 1)
    # Week date range
    week_start = season_start + timedelta(weeks=week_n - 1)
    week_end   = week_start + timedelta(days=6)
    return (f"WEEK {week_n} · "
            f"{week_start.strftime('%b %d').upper()} – "
            f"{week_end.strftime('%b %d').upper()}")


def get_weekly_movers(proj):
    """Return biggest riser and faller based on history arrays."""
    movers = {}
    for t in proj["teams"]:
        hist = t.get("history", {}).get("elo", [])
        if len(hist) >= 2:
            movers[t["short"]] = hist[-1] - hist[-2]
        elif len(hist) == 1:
            movers[t["short"]] = 0
    if not movers:
        return None, None, {}, {}
    riser = max(movers, key=lambda t: movers[t])
    faller = min(movers, key=lambda t: movers[t])
    return riser, faller, movers, {t["short"]: movers.get(t["short"], 0)
                                   for t in proj["teams"]}


def top4_summary(proj, model="elo"):
    sorted_teams = sorted(
        proj["teams"],
        key=lambda t: t["models"][model]["playoff_pct"],
        reverse=True,
    )[:4]
    return ", ".join(
        f"{t['short']} {t['models'][model]['playoff_pct']:.1f}%"
        for t in sorted_teams
    )


def recent_stories(stories_data, days=7):
    cutoff = (dt_date.today() - timedelta(days=days)).isoformat()
    return [s for s in stories_data.get("stories", [])
            if s.get("date", "") >= cutoff and s.get("type", "match") == "match"]


def week_already_written(stories_data, label):
    return any(
        s.get("week_label") == label
        for s in stories_data.get("stories", [])
        if s.get("type") == "weekly"
    )


def call_gemini(prompt, api_key):
    """Call Gemini via REST API directly — no SDK, no versioning issues."""
    import requests as req
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = req.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def main():
    log.info("=== generate_weekly_narrative.py start ===")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
            api_key = os.environ.get("GEMINI_API_KEY")
        except ImportError:
            pass

    proj         = load_json(PROJ)
    stories_data = load_json(STORIES_JSON) or {"stories": []}
    player_stats = load_json(PLAYER_STATS)

    if not proj:
        log.warning("projections.json not found — exiting")
        return

    label = week_label()
    if week_already_written(stories_data, label):
        log.info(f"Weekly narrative for '{label}' already exists — skipping")
        return

    riser, faller, movers, _ = get_weekly_movers(proj)
    top4 = top4_summary(proj)

    recent = recent_stories(stories_data)
    n_matches = len(recent)

    # Closest battle: two teams within 3% of each other near cutoff
    sorted_by_pct = sorted(
        proj["teams"],
        key=lambda t: t["models"]["elo"]["playoff_pct"],
        reverse=True,
    )
    closest = ""
    for i in range(len(sorted_by_pct) - 1):
        gap = abs(sorted_by_pct[i]["models"]["elo"]["playoff_pct"] -
                  sorted_by_pct[i+1]["models"]["elo"]["playoff_pct"])
        if gap < 5:
            closest = (f"{sorted_by_pct[i]['short']} "
                       f"({sorted_by_pct[i]['models']['elo']['playoff_pct']:.1f}%) vs "
                       f"{sorted_by_pct[i+1]['short']} "
                       f"({sorted_by_pct[i+1]['models']['elo']['playoff_pct']:.1f}%)")
            break

    rise_pct = movers.get(riser, 0) if riser else 0
    fall_pct = movers.get(faller, 0) if faller else 0

    body = ""
    if api_key and (riser or n_matches > 0):
        try:
            prompt = f"""Write a 'state of the season' paragraph for IPL 2026 playoff forecasting site Duckworth.

Week in numbers:
- Matches played this week: {n_matches}
- Biggest odds gainer: {riser} +{rise_pct:.1f}%
- Biggest odds loser: {faller} {fall_pct:+.1f}%
- Current top 4: {top4}
- Closest battle: {closest or 'tight across the board'}

Write 80 words maximum. Lead with the week's defining data story. End with the key question heading into next week. Plain text only. No markdown. No headers.
"""
            body = call_gemini(prompt, api_key)
            log.info(f"Gemini weekly narrative generated ({len(body.split())} words)")
        except Exception as e:
            log.error(f"Gemini failed: {e}")

    if not body:
        body = (
            f"IPL 2026 Week {label.split()[1]}: {n_matches} matches played. "
            f"{riser} gained the most ground this week (+{rise_pct:.1f}%), "
            f"while {faller} slipped ({fall_pct:+.1f}%). "
            f"Current top 4: {top4}. "
            f"{closest and f'The cutoff fight between {closest} is the race to watch.' or ''} "
            f"Full projections updated after every match."
        )

    weekly_entry = {
        "match_id": f"weekly_{label.replace(' ', '_').replace('·', '').replace('–','_').lower()}",
        "date": dt_date.today().isoformat(),
        "week_label": label,
        "type": "weekly",
        "headline": f"{label}",
        "body": body,
        "top4": top4,
        "biggest_mover": {"riser": riser, "rise": rise_pct,
                          "faller": faller, "fall": fall_pct},
        "generated_at": dt_date.today().isoformat(),
    }

    stories_data["stories"].append(weekly_entry)
    STORIES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(STORIES_JSON, "w", encoding="utf-8") as f:
        json.dump(stories_data, f, indent=2, ensure_ascii=False)

    log.info(f"Weekly narrative appended: {label}")
    log.info("=== generate_weekly_narrative.py done ===")


if __name__ == "__main__":
    main()
