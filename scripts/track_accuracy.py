#!/usr/bin/env python3
"""
track_accuracy.py
After each match, compares model prediction to actual result.
Appends to public/data/accuracy.json (never overwrites).

Run: python scripts/track_accuracy.py
"""
import csv, json, logging
from datetime import date as dt_date
from pathlib import Path

ROOT          = Path(__file__).parent.parent
RESULTS_CSV   = ROOT / "data" / "results.csv"
PROJ_PREV     = ROOT / "data" / "projections_previous.json"
PROJ_CURR     = ROOT / "public" / "data" / "projections.json"
ACCURACY_JSON = ROOT / "public" / "data" / "accuracy.json"
LOG_PATH      = ROOT / "logs" / "accuracy_log.txt"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

SHORT_FULL = {
    "RCB": "Royal Challengers Bengaluru", "MI": "Mumbai Indians",
    "KKR": "Kolkata Knight Riders", "GT": "Gujarat Titans",
    "CSK": "Chennai Super Kings", "SRH": "Sunrisers Hyderabad",
    "PBKS": "Punjab Kings", "RR": "Rajasthan Royals",
    "DC": "Delhi Capitals", "LSG": "Lucknow Super Giants",
}
FULL_SHORT = {v: k for k, v in SHORT_FULL.items()}


def load_json(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_elo_pct(proj, short):
    for t in proj["teams"]:
        if t["short"] == short:
            return t["models"]["elo"]["playoff_pct"]
    return 50.0


def head_to_head_prob(proj, t1_short, t2_short):
    """
    Derive match win probability from Elo scores stored in projections.
    P(t1 wins) = 1 / (1 + 10^((elo_t2 - elo_t1)/400))
    """
    elo = {}
    for t in proj["teams"]:
        if t["short"] in (t1_short, t2_short):
            elo[t["short"]] = t.get("factors", {}).get("elo_score", 1500)
    e1 = elo.get(t1_short, 1500)
    e2 = elo.get(t2_short, 1500)
    return round(1 / (1 + 10 ** ((e2 - e1) / 400)), 4)


def calibration_bucket(prob):
    if prob >= 0.80: return "80_plus"
    if prob >= 0.70: return "70_80"
    if prob >= 0.60: return "60_70"
    return "50_60"


def load_results():
    rows = []
    with open(RESULTS_CSV, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return [r for r in rows if r.get("date", "").startswith("2026")]


def build_empty_accuracy():
    return {
        "total_predictions": 0,
        "correct": 0,
        "accuracy_pct": 0.0,
        "predictions": [],
        "calibration": {
            "50_60": {"predictions": 0, "correct": 0},
            "60_70": {"predictions": 0, "correct": 0},
            "70_80": {"predictions": 0, "correct": 0},
            "80_plus": {"predictions": 0, "correct": 0},
        },
        "by_model": {
            "elo":  {"correct": 0, "total": 0},
            "form": {"correct": 0, "total": 0},
        },
    }


def main():
    log.info("=== track_accuracy.py start ===")

    results = load_results()
    if not results:
        log.warning("No 2026 results found — nothing to track")
        return

    acc = load_json(ACCURACY_JSON) or build_empty_accuracy()

    # Build set of already-tracked matches
    tracked = set(p["match_key"] for p in acc.get("predictions", []))

    # We need the pre-match projections to get predictions
    # Since projections_previous.json holds the state BEFORE the latest match,
    # we compare last result against it.
    if not PROJ_PREV.exists():
        log.warning("projections_previous.json not found — using current for Elo lookup")
        proj_for_pred = load_json(PROJ_CURR)
    else:
        proj_for_pred = load_json(PROJ_PREV)

    new_entries = 0
    for r in results:
        t1_full = r["team1"]; t2_full = r["team2"]
        t1 = FULL_SHORT.get(t1_full, t1_full[:3].upper())
        t2 = FULL_SHORT.get(t2_full, t2_full[:3].upper())
        winner_full = r["winner"]
        winner = FULL_SHORT.get(winner_full, winner_full[:3].upper())
        match_key = f"{r['date']}_{t1}_{t2}"

        if match_key in tracked:
            continue

        # Elo win probability for t1
        elo_prob = head_to_head_prob(proj_for_pred, t1, t2)
        # Form: use same Elo prob as proxy (form win-prob calculation
        # needs full BBB, not available here — Elo is the primary model)
        form_prob = elo_prob

        elo_pred  = t1 if elo_prob  >= 0.5 else t2
        form_pred = t1 if form_prob >= 0.5 else t2

        elo_correct  = (elo_pred  == winner)
        form_correct = (form_pred == winner)
        bucket = calibration_bucket(max(elo_prob, 1 - elo_prob))

        entry = {
            "match_key": match_key,
            "date": r["date"],
            "match": f"{t1} vs {t2}",
            "predicted_winner_elo":  elo_pred,
            "predicted_probability": elo_prob,
            "actual_winner": winner,
            "correct_elo":  elo_correct,
            "correct_form": form_correct,
        }
        acc["predictions"].append(entry)
        acc["calibration"][bucket]["predictions"] += 1
        if elo_correct:
            acc["calibration"][bucket]["correct"] += 1
        acc["by_model"]["elo"]["total"]  += 1
        acc["by_model"]["form"]["total"] += 1
        if elo_correct:  acc["by_model"]["elo"]["correct"]  += 1
        if form_correct: acc["by_model"]["form"]["correct"] += 1
        tracked.add(match_key)
        new_entries += 1
        log.info(f"  {match_key}: Elo pred={elo_pred} actual={winner} correct={elo_correct}")

    # Recompute totals
    preds = acc["predictions"]
    acc["total_predictions"] = len(preds)
    acc["correct"] = sum(1 for p in preds if p.get("correct_elo"))
    acc["accuracy_pct"] = round(
        acc["correct"] / acc["total_predictions"] * 100, 1
    ) if acc["total_predictions"] > 0 else 0.0

    ACCURACY_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(ACCURACY_JSON, "w", encoding="utf-8") as f:
        json.dump(acc, f, indent=2, ensure_ascii=False)

    log.info(f"accuracy.json: {acc['correct']}/{acc['total_predictions']} correct "
             f"({acc['accuracy_pct']}%) — {new_entries} new entries")
    log.info("=== track_accuracy.py done ===")


if __name__ == "__main__":
    main()
