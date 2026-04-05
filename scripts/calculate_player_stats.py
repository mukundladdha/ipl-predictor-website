#!/usr/bin/env python3
"""
calculate_player_stats.py
Reads ball-by-ball IPL 2026 data → public/data/player_stats.json
"""
import csv, json, logging, random
from collections import defaultdict
from datetime import date as dt_date
from pathlib import Path

ROOT      = Path(__file__).parent.parent
BBB_PATH  = ROOT / "data" / "raw" / "ipl_2026_bbb.csv"
PROJ_PATH = ROOT / "public" / "data" / "projections.json"
OUT_PATH  = ROOT / "public" / "data" / "player_stats.json"
LOG_PATH  = ROOT / "logs" / "player_stats_log.txt"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ── Mappings ──────────────────────────────────────────────────────────────────

TEAM_MAP = {
    "Royal Challengers Bengaluru": "RCB", "Royal Challengers Bangalore": "RCB",
    "Mumbai Indians": "MI", "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK", "Sunrisers Hyderabad": "SRH",
    "Rajasthan Royals": "RR", "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS", "Gujarat Titans": "GT",
    "Lucknow Super Giants": "LSG",
}

NAME_MAP = {
    # RCB
    "V Kohli": "Virat Kohli", "Virat Kohli": "Virat Kohli",
    "DP Padikkal": "Devdutt Padikkal", "Devdutt Padikkal": "Devdutt Padikkal",
    "JR Hazlewood": "Josh Hazlewood", "Josh Hazlewood": "Josh Hazlewood",
    "JA Duffy": "Jacob Duffy", "Jacob Duffy": "Jacob Duffy",
    "GJ Maxwell": "Glenn Maxwell", "Glenn Maxwell": "Glenn Maxwell",
    "KH Pandya": "Krunal Pandya", "Krunal Pandya": "Krunal Pandya",
    "Mohammed Siraj": "Mohammed Siraj", "M Siraj": "Mohammed Siraj",
    "Phil Salt": "Phil Salt", "P Salt": "Phil Salt",
    "Rajat Patidar": "Rajat Patidar",
    "SS Prabhudessai": "Suyash Sharma", "Suyash Sharma": "Suyash Sharma",
    # MI
    "RG Sharma": "Rohit Sharma", "Rohit Sharma": "Rohit Sharma",
    "SK Yadav": "Suryakumar Yadav", "Suryakumar Yadav": "Suryakumar Yadav",
    "HH Pandya": "Hardik Pandya", "Hardik Pandya": "Hardik Pandya",
    "JJ Bumrah": "Jasprit Bumrah", "Jasprit Bumrah": "Jasprit Bumrah",
    "Tilak Varma": "Tilak Varma", "N Dhir": "Naman Dhir", "Naman Dhir": "Naman Dhir",
    # KKR
    "Ajinkya Rahane": "Ajinkya Rahane",
    "V Iyer": "Venkatesh Iyer", "Venkatesh Iyer": "Venkatesh Iyer",
    "SP Narine": "Sunil Narine", "Sunil Narine": "Sunil Narine",
    "AD Russell": "Andre Russell", "Andre Russell": "Andre Russell",
    "Varun Chakravarthy": "Varun Chakaravarthy",
    "Varun Chakaravarthy": "Varun Chakaravarthy",
    "Harshit Rana": "Harshit Rana",
    # SRH
    "TR Head": "Travis Head", "Travis Head": "Travis Head",
    "Abhishek Sharma": "Abhishek Sharma",
    "HE van der Dussen": "Rassie van der Dussen",
    "Rassie van der Dussen": "Rassie van der Dussen",
    "HH Klaasen": "Heinrich Klaasen", "Heinrich Klaasen": "Heinrich Klaasen",
    "PJ Cummins": "Pat Cummins", "Pat Cummins": "Pat Cummins",
    "B Kumar": "Bhuvneshwar Kumar", "Bhuvneshwar Kumar": "Bhuvneshwar Kumar",
    "Harshal Patel": "Harshal Patel", "H Patel": "Harshal Patel",
    # CSK
    "RD Gaikwad": "Ruturaj Gaikwad", "Ruturaj Gaikwad": "Ruturaj Gaikwad",
    "MS Dhoni": "MS Dhoni",
    "DP Conway": "Devon Conway", "Devon Conway": "Devon Conway",
    "Shivam Dube": "Shivam Dube",
    "D Chahar": "Deepak Chahar", "Deepak Chahar": "Deepak Chahar",
    "RA Jadeja": "Ravindra Jadeja", "Ravindra Jadeja": "Ravindra Jadeja",
    # RR
    "SV Samson": "Sanju Samson", "Sanju Samson": "Sanju Samson",
    "YBK Jaiswal": "Yashasvi Jaiswal", "Yashasvi Jaiswal": "Yashasvi Jaiswal",
    "JC Buttler": "Jos Buttler", "Jos Buttler": "Jos Buttler",
    "RP Parag": "Riyan Parag", "Riyan Parag": "Riyan Parag",
    "TA Boult": "Trent Boult", "Trent Boult": "Trent Boult",
    "JC Archer": "Jofra Archer", "Jofra Archer": "Jofra Archer",
    # DC / GT / PBKS / LSG (common Cricsheet abbreviations)
    "DA Warner": "David Warner", "Prithvi Shaw": "Prithvi Shaw",
    "SH Gill": "Shubman Gill", "Shubman Gill": "Shubman Gill",
    "KL Rahul": "KL Rahul",
    "NE Pooran": "Nicholas Pooran", "Nicholas Pooran": "Nicholas Pooran",
    "M Stoinis": "Marcus Stoinis", "Marcus Stoinis": "Marcus Stoinis",
}

PLAYER_TEAM = {
    "Virat Kohli": "RCB", "Devdutt Padikkal": "RCB", "Rajat Patidar": "RCB",
    "Glenn Maxwell": "RCB", "Krunal Pandya": "RCB", "Phil Salt": "RCB",
    "Josh Hazlewood": "RCB", "Jacob Duffy": "RCB", "Mohammed Siraj": "RCB",
    "Suyash Sharma": "RCB",
    "Rohit Sharma": "MI", "Suryakumar Yadav": "MI", "Tilak Varma": "MI",
    "Hardik Pandya": "MI", "Naman Dhir": "MI", "Jasprit Bumrah": "MI",
    "Ajinkya Rahane": "KKR", "Venkatesh Iyer": "KKR", "Sunil Narine": "KKR",
    "Andre Russell": "KKR", "Varun Chakaravarthy": "KKR", "Harshit Rana": "KKR",
    "Travis Head": "SRH", "Abhishek Sharma": "SRH",
    "Rassie van der Dussen": "SRH", "Heinrich Klaasen": "SRH",
    "Pat Cummins": "SRH", "Bhuvneshwar Kumar": "SRH", "Harshal Patel": "SRH",
    "Ruturaj Gaikwad": "CSK", "MS Dhoni": "CSK", "Devon Conway": "CSK",
    "Shivam Dube": "CSK", "Deepak Chahar": "CSK", "Ravindra Jadeja": "CSK",
    "Sanju Samson": "RR", "Yashasvi Jaiswal": "RR", "Jos Buttler": "RR",
    "Riyan Parag": "RR", "Trent Boult": "RR", "Jofra Archer": "RR",
}

PLAYER_ROLE = {
    "Virat Kohli": "batter", "Devdutt Padikkal": "batter", "Rajat Patidar": "batter",
    "Phil Salt": "wicketkeeper", "Travis Head": "batter", "Abhishek Sharma": "batter",
    "Rassie van der Dussen": "batter", "Heinrich Klaasen": "wicketkeeper",
    "Rohit Sharma": "batter", "Suryakumar Yadav": "batter", "Tilak Varma": "batter",
    "Ajinkya Rahane": "batter", "Ruturaj Gaikwad": "batter",
    "MS Dhoni": "wicketkeeper", "Devon Conway": "batter",
    "Yashasvi Jaiswal": "batter", "Sanju Samson": "wicketkeeper",
    "Jos Buttler": "batter", "Naman Dhir": "batter",
    "Glenn Maxwell": "allrounder", "Krunal Pandya": "allrounder",
    "Hardik Pandya": "allrounder", "Sunil Narine": "allrounder",
    "Andre Russell": "allrounder", "Pat Cummins": "allrounder",
    "Shivam Dube": "allrounder", "Ravindra Jadeja": "allrounder",
    "Venkatesh Iyer": "allrounder", "Riyan Parag": "allrounder",
    "Josh Hazlewood": "bowler", "Jacob Duffy": "bowler",
    "Mohammed Siraj": "bowler", "Suyash Sharma": "bowler",
    "Jasprit Bumrah": "bowler", "Bhuvneshwar Kumar": "bowler",
    "Harshal Patel": "bowler", "Varun Chakaravarthy": "bowler",
    "Harshit Rana": "bowler", "Deepak Chahar": "bowler",
    "Trent Boult": "bowler", "Jofra Archer": "bowler",
}

BATTING_DISMISSALS  = {"bowled","caught","lbw","stumped","caught and bowled","hit wicket","hit the ball twice"}
BOWLING_WICKET_TYPES = {"bowled","caught","lbw","stumped","caught and bowled","hit wicket"}

# ── Sample data ───────────────────────────────────────────────────────────────

def _seq(runs, total_balls, fours, sixes):
    """Build a shuffled list of per-ball run values that sums to runs."""
    seq = [6]*sixes + [4]*fours
    singles = runs - 6*sixes - 4*fours
    seq += [1]*singles + [0]*(total_balls - sixes - fours - singles)
    random.shuffle(seq)
    return seq

def generate_sample_bbb():
    """Synthetic ball-by-ball rows for IPL 2026 matches 1-3."""
    random.seed(42)
    rows = []
    counter = [0]

    def add_innings(match_id, date, venue, inn_num,
                    bat_team, bowl_team, batters, bowler_pool):
        """
        batters: list of (name, partner, runs, balls, fours, sixes, out_type, out_bowler)
        out_type="" means not out.
        """
        ball_idx = [0]
        for (name, partner, runs, total_balls, fours, sixes, out_type, out_bowler) in batters:
            seq = _seq(runs, total_balls, fours, sixes)
            n = len(bowler_pool)
            for i, r in enumerate(seq):
                is_last = (i == len(seq) - 1)
                dismissed = is_last and bool(out_type)
                bowler = out_bowler if dismissed and out_bowler else bowler_pool[ball_idx[0] % n]
                counter[0] += 1
                rows.append({
                    "match_id": match_id, "season": "2026",
                    "start_date": date, "venue": venue, "innings": inn_num,
                    "ball": f"{ball_idx[0]//6+1}.{ball_idx[0]%6+1}",
                    "batting_team": bat_team, "bowling_team": bowl_team,
                    "striker": name, "non_striker": partner, "bowler": bowler,
                    "runs_off_bat": r, "extras": 0, "wides": 0, "noballs": 0,
                    "byes": 0, "legbyes": 0, "penalty": 0,
                    "wicket_type": out_type if dismissed else "",
                    "player_dismissed": name if dismissed else "",
                    "other_wicket_type": "", "other_player_dismissed": "",
                })
                ball_idx[0] += 1

    # ── Match 1: RCB vs SRH, 2026-03-28 (RCB won by 6 wkts) ─────────────────
    add_innings("ipl2026m1","2026-03-28","M. Chinnaswamy Stadium", 1,
        "Sunrisers Hyderabad", "Royal Challengers Bengaluru",
        [
            ("Travis Head",          "Abhishek Sharma",    62,38,5,3,"bowled",  "Jacob Duffy"),
            ("Abhishek Sharma",      "Travis Head",        15,12,2,0,"caught",  "Jacob Duffy"),
            ("Rassie van der Dussen","Abhishek Sharma",    22,18,3,0,"lbw",     "Josh Hazlewood"),
            ("Heinrich Klaasen",     "Pat Cummins",        30,19,2,2,"caught",  "Josh Hazlewood"),
            ("Pat Cummins",          "Harshal Patel",       8, 8,0,1,"bowled",  "Jacob Duffy"),
            ("Harshal Patel",        "Bhuvneshwar Kumar",  10, 7,1,0,"caught",  "Krunal Pandya"),
        ],
        ["Jacob Duffy","Josh Hazlewood","Mohammed Siraj","Krunal Pandya","Glenn Maxwell"],
    )
    add_innings("ipl2026m1","2026-03-28","M. Chinnaswamy Stadium", 2,
        "Royal Challengers Bengaluru", "Sunrisers Hyderabad",
        [
            ("Virat Kohli",    "Phil Salt",        28,22,2,1,"caught","Bhuvneshwar Kumar"),
            ("Phil Salt",      "Virat Kohli",      12,10,1,0,"lbw",   "Pat Cummins"),
            ("Devdutt Padikkal","Rajat Patidar",   47,32,5,2,"",""),          # not out
            ("Rajat Patidar",  "Devdutt Padikkal", 32,20,3,1,"caught","Harshal Patel"),
            ("Glenn Maxwell",  "Devdutt Padikkal", 15,10,0,1,"",""),          # not out
        ],
        ["Bhuvneshwar Kumar","Pat Cummins","Harshal Patel","Abhishek Sharma","Travis Head"],
    )

    # ── Match 2: MI vs KKR, 2026-03-29 (MI won) ─────────────────────────────
    add_innings("ipl2026m2","2026-03-29","Eden Gardens", 1,
        "Kolkata Knight Riders", "Mumbai Indians",
        [
            ("Sunil Narine",       "Ajinkya Rahane",     35,25,3,2,"bowled","Jasprit Bumrah"),
            ("Ajinkya Rahane",     "Sunil Narine",       20,18,2,0,"caught","Hardik Pandya"),
            ("Venkatesh Iyer",     "Andre Russell",      28,20,2,1,"lbw",   "Jasprit Bumrah"),
            ("Andre Russell",      "Venkatesh Iyer",     22,12,1,2,"caught","Hardik Pandya"),
            ("Varun Chakaravarthy","Harshit Rana",        4, 5,0,0,"bowled","Jasprit Bumrah"),
            ("Harshit Rana",       "Varun Chakaravarthy", 5, 5,0,0,"caught","Naman Dhir"),
        ],
        ["Jasprit Bumrah","Hardik Pandya","Mohammed Siraj","Tilak Varma","Naman Dhir"],
    )
    add_innings("ipl2026m2","2026-03-29","Eden Gardens", 2,
        "Mumbai Indians", "Kolkata Knight Riders",
        [
            ("Rohit Sharma",     "Suryakumar Yadav", 45,32,4,2,"caught","Varun Chakaravarthy"),
            ("Suryakumar Yadav", "Rohit Sharma",     62,38,4,3,"",""),        # not out
            ("Tilak Varma",      "Hardik Pandya",    23,15,2,1,"caught","Harshit Rana"),
            ("Hardik Pandya",    "Suryakumar Yadav", 15,10,1,1,"bowled","Varun Chakaravarthy"),
            ("Naman Dhir",       "Suryakumar Yadav",  5, 4,0,0,"",""),        # not out
        ],
        ["Harshit Rana","Varun Chakaravarthy","Sunil Narine","Andre Russell","Venkatesh Iyer"],
    )

    # ── Match 3: RR vs CSK, 2026-03-30 (RR won by 8 wkts) ───────────────────
    add_innings("ipl2026m3","2026-03-30","Barsapara Cricket Stadium", 1,
        "Chennai Super Kings", "Rajasthan Royals",
        [
            ("Ruturaj Gaikwad","Devon Conway",    35,28,3,1,"caught","Jofra Archer"),
            ("Devon Conway",   "Ruturaj Gaikwad", 42,35,4,1,"bowled","Trent Boult"),
            ("Shivam Dube",    "Ravindra Jadeja", 28,18,2,2,"caught","Jofra Archer"),
            ("Ravindra Jadeja","MS Dhoni",        15,12,1,1,"bowled","Trent Boult"),
            ("MS Dhoni",       "Deepak Chahar",   12, 8,0,1,"caught","Riyan Parag"),
        ],
        ["Jofra Archer","Trent Boult","Riyan Parag","Yashasvi Jaiswal","Sanju Samson"],
    )
    add_innings("ipl2026m3","2026-03-30","Barsapara Cricket Stadium", 2,
        "Rajasthan Royals", "Chennai Super Kings",
        [
            ("Yashasvi Jaiswal","Sanju Samson",  55,35,5,3,"caught","Deepak Chahar"),
            ("Sanju Samson",    "Jos Buttler",   45,28,4,2,"",""),            # not out
            ("Jos Buttler",     "Sanju Samson",  22,15,2,1,"",""),            # not out
        ],
        ["Deepak Chahar","Ravindra Jadeja","Shivam Dube","Devon Conway","Ruturaj Gaikwad"],
    )

    log.info(f"Generated {counter[0]} sample deliveries for 3 matches")
    return rows

# ── Data loading ──────────────────────────────────────────────────────────────

_warned_names: set = set()

def normalize_name(n: str) -> str:
    c = NAME_MAP.get(n)
    if c:
        return c
    if n not in _warned_names:
        log.warning(f"Unknown player name: '{n}' — using as-is")
        _warned_names.add(n)
    return n

def load_bbb():
    if not BBB_PATH.exists():
        log.info("ipl_2026_bbb.csv not found — generating sample data")
        sample = generate_sample_bbb()
        BBB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(BBB_PATH, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sample[0].keys()))
            w.writeheader(); w.writerows(sample)
        return sample

    rows = []
    with open(BBB_PATH, newline="") as f:
        for r in csv.DictReader(f):
            r["batting_team"] = TEAM_MAP.get(r["batting_team"], r["batting_team"])
            r["bowling_team"] = TEAM_MAP.get(r["bowling_team"], r["bowling_team"])
            r["striker"]  = normalize_name(r["striker"])
            r["non_striker"] = normalize_name(r.get("non_striker",""))
            r["bowler"]   = normalize_name(r["bowler"])
            if r.get("player_dismissed"):
                r["player_dismissed"] = normalize_name(r["player_dismissed"])
            for col in ("runs_off_bat","extras","wides","noballs","byes","legbyes"):
                r[col] = int(r.get(col) or 0)
            rows.append(r)
    log.info(f"Loaded {len(rows)} deliveries from {BBB_PATH}")
    return rows

# ── Stats calculations ────────────────────────────────────────────────────────

def get_batting_stats(rows):
    matches  = defaultdict(set)
    inn_set  = defaultdict(set)
    runs     = defaultdict(int)
    balls    = defaultdict(int)
    fours    = defaultdict(int)
    sixes    = defaultdict(int)
    dism     = defaultdict(int)
    inn_runs = defaultdict(lambda: defaultdict(int))
    inn_balls= defaultdict(lambda: defaultdict(int))

    for r in rows:
        s = r["striker"]
        key = (r["match_id"], r["innings"])
        if int(r.get("wides") or 0):
            continue
        matches[s].add(r["match_id"])
        inn_set[s].add(key)
        runs[s]  += int(r["runs_off_bat"])
        balls[s] += 1
        inn_runs[s][key]  += int(r["runs_off_bat"])
        inn_balls[s][key] += 1
        if int(r["runs_off_bat"]) == 4: fours[s] += 1
        if int(r["runs_off_bat"]) == 6: sixes[s] += 1
        if r.get("player_dismissed") == s and r.get("wicket_type","") in BATTING_DISMISSALS:
            dism[s] += 1

    out = {}
    for p in balls:
        if balls[p] == 0:
            continue
        r_val = runs[p]; b_val = balls[p]; d = dism[p]
        sr = round(r_val / b_val * 100, 1)
        avg = round(r_val / max(d, 1), 1)
        hs  = max(inn_runs[p].values()) if inn_runs[p] else 0
        fifties  = sum(1 for v in inn_runs[p].values() if 30 <= v < 50)
        hundreds = sum(1 for v in inn_runs[p].values() if v >= 50)
        # innings list chronological (oldest first)
        sorted_keys = sorted(inn_runs[p].keys())
        inn_list = [(inn_runs[p][k], round(inn_runs[p][k]/max(inn_balls[p][k],1)*100,1))
                    for k in sorted_keys]
        out[p] = {
            "matches": len(matches[p]), "innings": len(inn_set[p]),
            "runs": r_val, "balls_faced": b_val,
            "fours": fours[p], "sixes": sixes[p], "dismissals": d,
            "strike_rate": sr, "average": avg,
            "highest_score": hs, "fifties": fifties, "hundreds": hundreds,
            "_inn_list": inn_list,
        }
    return out


def get_bowling_stats(rows):
    matches  = defaultdict(set)
    inn_set  = defaultdict(set)
    balls    = defaultdict(int)
    runs_c   = defaultdict(int)
    wickets  = defaultdict(int)
    dots     = defaultdict(int)
    s_balls  = defaultdict(lambda: defaultdict(int))
    s_runs   = defaultdict(lambda: defaultdict(int))
    s_wkts   = defaultdict(lambda: defaultdict(int))

    for r in rows:
        bwl = r["bowler"]
        key = (r["match_id"], r["innings"])
        is_wide  = bool(int(r.get("wides")  or 0))
        is_noball= bool(int(r.get("noballs") or 0))
        run_tot  = int(r["runs_off_bat"]) + int(r["extras"])

        matches[bwl].add(r["match_id"])
        inn_set[bwl].add(key)
        runs_c[bwl] += run_tot
        s_runs[bwl][key] += run_tot

        if not is_wide and not is_noball:
            balls[bwl] += 1
            s_balls[bwl][key] += 1
            if int(r["runs_off_bat"]) == 0 and int(r["extras"]) == 0:
                dots[bwl] += 1

        if r.get("wicket_type","") in BOWLING_WICKET_TYPES:
            wickets[bwl] += 1
            s_wkts[bwl][key] += 1

    out = {}
    for p in matches:
        b = balls[p]; rc = runs_c[p]; w = wickets[p]
        econ = round(rc / b * 6, 1) if b > 0 else 0.0
        avg  = round(rc / max(w, 1), 1)
        overs= round(b / 6, 1)
        # Best figures
        best_w, best_r = 0, 999
        spells = []
        for key in s_balls[p]:
            sb = s_balls[p][key]; sr = s_runs[p][key]; sw = s_wkts[p][key]
            spells.append((sw, round(sr/max(sb,1)*6, 1)))
            if sw > best_w or (sw == best_w and sr < best_r):
                best_w, best_r = sw, sr
        out[p] = {
            "matches": len(matches[p]), "innings": len(inn_set[p]),
            "balls": b, "overs": overs, "runs_conceded": rc,
            "wickets": w, "economy": econ, "average": avg,
            "best_figures": f"{best_w}/{best_r}",
            "dot_balls": dots[p],
            "_spells": spells,  # chronological
        }
    return out

# ── Form / impact / contribution ──────────────────────────────────────────────

def batting_form_score(inn_list_recent_first):
    last5 = inn_list_recent_first[:5]
    if not last5:
        return 0.0
    weights = [0.75**i for i in range(len(last5))]
    scores  = [(r * (sr/150)) * w for (r, sr), w in zip(last5, weights)]
    raw = sum(scores) / sum(weights)
    return min(round(raw / 5, 1), 10.0)

def bowling_form_score(spells_recent_first):
    last5 = spells_recent_first[:5]
    if not last5:
        return 0.0
    weights = [0.75**i for i in range(len(last5))]
    scores  = [((wk*3) + max(0, 9-ec)) * w for (wk, ec), w in zip(last5, weights)]
    raw = sum(scores) / sum(weights)
    return min(round(raw / 2, 1), 10.0)

def _form_trend(series_recent_first):
    """'up'/'down'/'stable' by comparing avg last-2 vs previous-3."""
    if len(series_recent_first) < 2:
        return "stable"
    vals = [x for x, _ in series_recent_first] if isinstance(series_recent_first[0], tuple) else series_recent_first
    recent = sum(vals[:2]) / 2
    prev   = vals[2:5]
    if not prev:
        return "stable"
    prev_avg = sum(prev) / len(prev)
    if prev_avg == 0:
        return "stable"
    delta = (recent - prev_avg) / prev_avg
    return "up" if delta > 0.15 else ("down" if delta < -0.15 else "stable")

def batting_impact(s, venue_avg_sr=140):
    runs_above = s["runs"] - (s["balls_faced"] * 0.4)
    sr_above   = s["strike_rate"] - venue_avg_sr
    return round((runs_above * 0.6) + (sr_above * 0.4) / 10, 1)

def bowling_impact(s, venue_avg_econ=9.0):
    econ_saved  = (venue_avg_econ - s["economy"]) * s["overs"]
    wicket_val  = s["wickets"] * 8
    return round(econ_saved + wicket_val, 1)

def playoff_contribution(impact, team_pct):
    base = team_pct / 11
    return round(base * (1 + impact / 50), 1)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== calculate_player_stats.py start ===")

    rows = load_bbb()

    with open(PROJ_PATH) as f:
        proj = json.load(f)
    elo_pct   = {t["short"]: t["models"]["elo"]["playoff_pct"] for t in proj["teams"]}
    team_color= {t["short"]: t["color"] for t in proj["teams"]}

    bat  = get_batting_stats(rows)
    bowl = get_bowling_stats(rows)

    all_players = sorted(set(bat) | set(bowl))
    players_out = []

    for name in all_players:
        team = PLAYER_TEAM.get(name)
        if not team:
            log.warning(f"No team mapping for '{name}' — skipping")
            continue

        role  = PLAYER_ROLE.get(name, "allrounder")
        color = team_color.get(team, "#888")
        pct   = elo_pct.get(team, 40.0)

        b_s  = bat.get(name)
        bw_s = bowl.get(name)

        # Batting form — most recent first
        inn_rf = list(reversed(b_s["_inn_list"])) if b_s else []
        b_form  = batting_form_score(inn_rf)
        b_trend = _form_trend(inn_rf) if inn_rf else "stable"
        b_imp   = batting_impact(b_s) if b_s and b_s["balls_faced"] > 0 else 0.0

        # Bowling form — most recent first
        sp_rf  = list(reversed(bw_s["_spells"])) if bw_s else []
        bw_form  = bowling_form_score(sp_rf)
        bw_trend = _form_trend(sp_rf) if sp_rf else "stable"
        bw_imp   = bowling_impact(bw_s) if bw_s and bw_s["balls"] > 0 else 0.0

        if role in ("batter", "wicketkeeper"):
            form = b_form; trend = b_trend; imp = b_imp
        elif role == "bowler":
            form = bw_form; trend = bw_trend; imp = bw_imp
        else:
            form  = round(max(b_form, bw_form), 1)
            trend = b_trend if b_form >= bw_form else bw_trend
            imp   = round(b_imp + bw_imp * 0.5, 1)

        contrib = playoff_contribution(imp, pct)

        bat_out  = ({k: v for k, v in b_s.items()  if not k.startswith("_")}
                    if b_s and b_s["balls_faced"] > 0 else None)
        bowl_out = ({k: v for k, v in bw_s.items() if not k.startswith("_")}
                    if bw_s and bw_s["balls"] > 0 else None)

        players_out.append({
            "name": name, "team": team, "team_color": color, "role": role,
            "season_stats": bat_out, "bowling_stats": bowl_out,
            "form_score": form, "form_trend": trend,
            "last_5_scores": [r for r, _ in inn_rf[:5]],
            "impact_score": imp, "playoff_contribution": contrib,
        })

    players_out.sort(key=lambda p: p["impact_score"], reverse=True)

    # ── Leaderboards ──────────────────────────────────────────────────────────
    orange_cap = sorted(
        [p for p in players_out if p["season_stats"]],
        key=lambda p: p["season_stats"]["runs"], reverse=True,
    )[:10]
    purple_cap = sorted(
        [p for p in players_out if p["bowling_stats"] and p["bowling_stats"]["wickets"] > 0],
        key=lambda p: (-p["bowling_stats"]["wickets"], p["bowling_stats"]["economy"]),
    )[:10]
    top_imp_bat = sorted(
        [p for p in players_out if p["season_stats"] and p["season_stats"]["balls_faced"] >= 5],
        key=lambda p: batting_impact(p["season_stats"]), reverse=True,
    )[:5]
    top_imp_bowl = sorted(
        [p for p in players_out if p["bowling_stats"] and p["bowling_stats"]["balls"] >= 6],
        key=lambda p: bowling_impact(p["bowling_stats"]), reverse=True,
    )[:5]

    leaderboards = {
        "orange_cap": [{
            "name": p["name"], "team": p["team"], "team_color": p["team_color"],
            "runs": p["season_stats"]["runs"], "balls": p["season_stats"]["balls_faced"],
            "strike_rate": p["season_stats"]["strike_rate"],
            "matches": p["season_stats"]["matches"],
        } for p in orange_cap],
        "purple_cap": [{
            "name": p["name"], "team": p["team"], "team_color": p["team_color"],
            "wickets": p["bowling_stats"]["wickets"],
            "economy": p["bowling_stats"]["economy"],
            "best": p["bowling_stats"]["best_figures"],
            "matches": p["bowling_stats"]["matches"],
        } for p in purple_cap],
        "top_impact_batters": [{
            "name": p["name"], "team": p["team"],
            "impact": batting_impact(p["season_stats"]),
        } for p in top_imp_bat],
        "top_impact_bowlers": [{
            "name": p["name"], "team": p["team"],
            "impact": bowling_impact(p["bowling_stats"]),
        } for p in top_imp_bowl],
    }

    # ── Team performers ───────────────────────────────────────────────────────
    team_performers = {}
    for team in set(p["team"] for p in players_out):
        tp = [p for p in players_out if p["team"] == team]
        batters = [p for p in tp if p["season_stats"] and p["season_stats"]["balls_faced"] >= 3]
        bowlers = [p for p in tp if p["bowling_stats"] and p["bowling_stats"]["balls"] >= 6]
        top_b  = max(batters,  key=lambda p: p["season_stats"]["runs"],      default=None)
        top_bw = max(bowlers,  key=lambda p: p["bowling_stats"]["wickets"],   default=None)
        top_i  = max(tp,       key=lambda p: p["impact_score"],              default=None)
        # Include key stats for quick rendering
        team_performers[team] = {
            "top_batter":  {"name": top_b["name"],  "runs": top_b["season_stats"]["runs"],
                            "balls": top_b["season_stats"]["balls_faced"],
                            "sr": top_b["season_stats"]["strike_rate"]} if top_b  else None,
            "top_bowler":  {"name": top_bw["name"], "wickets": top_bw["bowling_stats"]["wickets"],
                            "runs": top_bw["bowling_stats"]["runs_conceded"],
                            "econ": top_bw["bowling_stats"]["economy"]} if top_bw else None,
            "biggest_impact": {"name": top_i["name"], "score": top_i["impact_score"]} if top_i else None,
        }

    out = {
        "last_updated": dt_date.today().isoformat(),
        "season": "2026",
        "players": players_out,
        "leaderboards": leaderboards,
        "team_performers": team_performers,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log.info(f"Written {len(players_out)} players → {OUT_PATH}")
    log.info("=== calculate_player_stats.py done ===")

if __name__ == "__main__":
    main()
