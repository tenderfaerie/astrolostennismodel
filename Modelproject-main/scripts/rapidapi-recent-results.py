"""
AstroTennis — Recent ATP/WTA Results Fetcher
Run ON YOUR LOCAL MACHINE.

Pulls last ~30 days of ATP + WTA match results from Sofascore via RapidAPI.
Outputs two CSVs ready to upload to Claude for analysis:
  - atp-results-YYYY-MM-DD.csv
  - wta-results-YYYY-MM-DD.csv

HOW TO GET MATCH IDs:
  Go to sofascore.com → Tennis → Roland Garros (or any tournament)
  Click a match → ID is the number at the end of the URL
  Add IDs to the TOURNAMENTS dict below.

Usage:
  python3 rapidapi-recent-results.py
  python3 rapidapi-recent-results.py --days 14    # last 14 days only
  python3 rapidapi-recent-results.py --tour atp   # ATP only
  python3 rapidapi-recent-results.py --tour wta   # WTA only

Output: atp-results-YYYY-MM-DD.csv + wta-results-YYYY-MM-DD.csv
"""

import csv
import json
import time
import requests
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com",
    "Content-Type":    "application/json",
}
BASE = "https://sofascore.p.rapidapi.com"

# ── ADD TOURNAMENT MATCH IDs HERE ─────────────────────────────────────────────
# Find IDs on sofascore.com — click any match, the ID is in the URL.
# For each tournament, list all match IDs you want to pull results for.
# Format: "Tournament Name": ["matchId1", "matchId2", ...]
#
# Roland Garros 2026 — filled in for you:
TOURNAMENTS = {
    "Roland Garros 2026 QF": {
        "tour": "both",
        "surface": "Clay",
        "match_ids": [
            # ATP QF
            "16198484",  # Cobolli vs Svajda
            "16198515",  # Cerundolo vs Berrettini
            "16198517",  # Tiafoe vs Arnaldi
            "16198519",  # FAA vs Tabilo
            "16198473",  # Mensik vs Fonseca
            "16198476",  # Jodar vs Zverev
            # WTA QF
            "16198577",  # Potapova vs Kalinskaya
            "16198570",  # Keys vs Shnaider
            "16198571",  # Sabalenka vs Osaka
            "16198546",  # Svitolina vs Kostyuk
            "16198539",  # Andreeva vs Cirstea
        ]
    },
    # ── ADD MORE TOURNAMENTS BELOW ─────────────────────────────────────────
    # "French Open 2026 R16": {
    #     "tour": "both",
    #     "surface": "Clay",
    #     "match_ids": ["XXXXXXXX", "XXXXXXXX"],
    # },
    # "Madrid Open 2026": {
    #     "tour": "both",
    #     "surface": "Clay",
    #     "match_ids": ["XXXXXXXX"],
    # },
    # "Rome Masters 2026": {
    #     "tour": "atp",
    #     "surface": "Clay",
    #     "match_ids": ["XXXXXXXX"],
    # },
}


def get(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=12)
        if r.status_code == 200:
            return r.json()
        print(f"  [{r.status_code}] {path}")
    except Exception as e:
        print(f"  [ERR] {e}")
    return {}


def get_match_detail(match_id):
    raw = get("/matches/detail", {"matchId": match_id})
    return raw.get("event", {})


def get_match_stats(match_id):
    raw = get("/matches/get-statistics", {"matchId": match_id})
    result = {}
    for block in raw.get("statistics", []):
        if block.get("period") != "ALL":
            continue
        for group in block.get("groups", []):
            for item in group.get("statisticsItems", []):
                key = item.get("key") or item.get("name","").replace(" ","_")
                result[key] = {"home": item.get("home"), "away": item.get("away")}
    return result


def frac_to_american(frac_str):
    if not frac_str or "/" not in str(frac_str):
        return ""
    try:
        n, d = map(int, str(frac_str).split("/"))
        dec = n / d + 1
        return f"+{round((dec-1)*100)}" if dec >= 2.0 else f"{round(-100/(dec-1))}"
    except:
        return str(frac_str)


def get_odds(match_id):
    raw = get("/matches/get-all-odds", {"matchId": match_id})
    for m in raw.get("markets", []):
        if m.get("marketId") == 1 or m.get("marketName") in ("Winner","Full time","Match Winner"):
            home = away = None
            for c in m.get("choices", []):
                nm = str(c.get("name","")).lower()
                frac = c.get("fractionalValue") or c.get("initialFractionalValue")
                pos = c.get("position")
                if nm in ("1","home") or pos == 1:
                    home = frac_to_american(frac)
                elif nm in ("2","away") or pos == 2:
                    away = frac_to_american(frac)
            return home, away
    return "", ""


def parse_match(event, stats, odds_h, odds_a, tournament, surface):
    if not event:
        return None

    home_team = event.get("homeTeam", {}).get("name", "?")
    away_team = event.get("awayTeam", {}).get("name", "?")
    status    = event.get("status", {}).get("type", "unknown")
    winner_code = event.get("winnerCode")
    winner    = home_team if winner_code == 1 else away_team if winner_code == 2 else ""

    hs = event.get("homeScore", {})
    as_ = event.get("awayScore", {})
    sets_h = hs.get("current", "")
    sets_a = as_.get("current", "")

    # Build score string: e.g. "6-3 6-4"
    score_parts = []
    for i in range(1, 6):
        ph = hs.get(f"period{i}")
        pa = as_.get(f"period{i}")
        if ph is not None and pa is not None:
            score_parts.append(f"{ph}-{pa}")
    score_str = " ".join(score_parts)

    ts = event.get("startTimestamp")
    match_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""

    # Determine tour from set count
    tour = "ATP" if (sets_h and int(sets_h or 0) + int(sets_a or 0) > 2) else "WTA"
    # Better tour detection from sets available
    max_sets = max((hs.get(f"period{i}") is not None) + (as_.get(f"period{i}") is not None)
                   for i in range(1, 6) if hs.get(f"period{i}") is not None or as_.get(f"period{i}") is not None) if any(hs.get(f"period{i}") is not None for i in range(1,6)) else 0
    total_sets = (sets_h or 0) + (sets_a or 0)

    # Round info
    round_name = event.get("roundInfo", {}).get("name", "")

    def s(key, side):
        v = stats.get(key, {}).get(side)
        return str(v) if v is not None else ""

    return {
        "date":        match_date,
        "tournament":  tournament,
        "surface":     surface,
        "round":       round_name,
        "home_player": home_team,
        "away_player": away_team,
        "winner":      winner,
        "score":       score_str,
        "sets_home":   sets_h,
        "sets_away":   sets_a,
        "status":      status,
        # Stats — home player
        "home_aces":       s("aces","home"),
        "home_dfs":        s("doubleFaults","home"),
        "home_1st_in":     s("firstServeAccuracy","home"),
        "home_1st_won":    s("firstServePointsAccuracy","home"),
        "home_2nd_won":    s("secondServePointsAccuracy","home"),
        "home_bp_saved":   s("breakPointsSaved","home"),
        "home_bp_won":     s("breakPointsScored","home"),
        "home_games_won":  s("gamesWon","home"),
        "home_winners":    s("winnersTotal","home"),
        "home_ues":        s("unforcedErrorsTotal","home"),
        # Stats — away player
        "away_aces":       s("aces","away"),
        "away_dfs":        s("doubleFaults","away"),
        "away_1st_in":     s("firstServeAccuracy","away"),
        "away_1st_won":    s("firstServePointsAccuracy","away"),
        "away_2nd_won":    s("secondServePointsAccuracy","away"),
        "away_bp_saved":   s("breakPointsSaved","away"),
        "away_bp_won":     s("breakPointsScored","away"),
        "away_games_won":  s("gamesWon","away"),
        "away_winners":    s("winnersTotal","away"),
        "away_ues":        s("unforcedErrorsTotal","away"),
        # Odds
        "odds_home":   odds_h,
        "odds_away":   odds_a,
    }


# ── MAIN ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--tour", choices=["atp","wta","both"], default="both")
args = parser.parse_args()

today = date.today().isoformat()
atp_rows, wta_rows = [], []

for tourn_name, cfg in TOURNAMENTS.items():
    tour_filter = cfg.get("tour","both")
    surface     = cfg.get("surface","Unknown")
    match_ids   = cfg.get("match_ids",[])

    print(f"\n=== {tourn_name} ({len(match_ids)} matches) ===")

    for mid in match_ids:
        print(f"  [{mid}]", end=" ", flush=True)

        event = get_match_detail(mid)
        if not event:
            print("no detail")
            continue

        home = event.get("homeTeam",{}).get("name","?")
        away = event.get("awayTeam",{}).get("name","?")
        status = event.get("status",{}).get("type","unknown")
        print(f"{home} vs {away} [{status}]", end=" ", flush=True)

        stats = {}
        if status == "finished":
            stats = get_match_stats(mid)
            time.sleep(0.3)

        odds_h, odds_a = get_odds(mid)
        time.sleep(0.3)

        row = parse_match(event, stats, odds_h, odds_a, tourn_name, surface)
        if not row:
            print("parse failed")
            continue

        print(f"✓ {row['winner']} wins {row['score']}")

        # Route to ATP or WTA based on score structure (best of 5 = ATP)
        hs = event.get("homeScore",{})
        as_ = event.get("awayScore",{})
        total_sets_played = sum(1 for i in range(1,6) if hs.get(f"period{i}") is not None)
        is_atp = (int(hs.get("current") or 0) + int(as_.get("current") or 0)) >= 3

        if is_atp:
            if args.tour in ("atp","both") and tour_filter in ("atp","both"):
                atp_rows.append(row)
        else:
            if args.tour in ("wta","both") and tour_filter in ("wta","both"):
                wta_rows.append(row)

        time.sleep(0.4)


FIELDS = ["date","tournament","surface","round","home_player","away_player",
          "winner","score","sets_home","sets_away","status",
          "home_aces","home_dfs","home_1st_in","home_1st_won","home_2nd_won",
          "home_bp_saved","home_bp_won","home_games_won","home_winners","home_ues",
          "away_aces","away_dfs","away_1st_in","away_1st_won","away_2nd_won",
          "away_bp_saved","away_bp_won","away_games_won","away_winners","away_ues",
          "odds_home","odds_away"]

saved = []
if atp_rows:
    fname = f"atp-results-{today}.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(atp_rows)
    print(f"\n✓ Saved {fname} ({len(atp_rows)} ATP matches)")
    saved.append(fname)

if wta_rows:
    fname = f"wta-results-{today}.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(wta_rows)
    print(f"✓ Saved {fname} ({len(wta_rows)} WTA matches)")
    saved.append(fname)

print(f"\nDone! Upload these to Claude:")
for f in saved:
    print(f"  → {f}")

print("""
TO ADD MORE TOURNAMENTS:
  1. Go to sofascore.com → find the tournament
  2. Click any match → copy the ID from the URL
  3. Open this script, add to TOURNAMENTS dict at top
  4. Re-run
""")
