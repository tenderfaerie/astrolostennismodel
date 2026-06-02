"""
AstroTennis — Daily RG Results Fetcher
Run this ON YOUR LOCAL MACHINE each match day.

HOW TO USE:
  1. Run:  python3 rapidapi-daily-results.py
  2. Upload the output JSON to Claude → "rebuild PDF"

HOW TO GET MATCH IDs FOR NEW DAYS:
  Go to sofascore.com → Tennis → Roland Garros
  Click any match → the number at the end of the URL is the match ID
  Example: sofascore.com/tennis/match/cobolli-svajda/16198484
                                                      ^^^^^^^^
  Add those numbers to MATCH_DATES below under the correct date.

Usage:
  python3 rapidapi-daily-results.py              # uses today's date
  python3 rapidapi-daily-results.py --date 2026-06-02
"""

import json
import time
import requests
import argparse
from datetime import date, datetime

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"
HEADERS_SS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com",
    "Content-Type":    "application/json",
}
BASE = "https://sofascore.p.rapidapi.com"

# ── ADD MATCH IDs HERE for each day ───────────────────────────────────────────
# Get IDs from sofascore.com URLs. Add new dates as the tournament progresses.
MATCH_DATES = {
    "2026-06-01": [
        # QF matches — June 1
        ("16198484", "Cobolli",    "Svajda"),
        ("16198515", "Cerundolo",  "Berrettini"),
        ("16198517", "Tiafoe",     "Arnaldi"),
        ("16198519", "FAA",        "Tabilo"),
        ("16198473", "Mensik",     "Fonseca"),
        ("16198476", "Jodar",      "Zverev"),
        ("16198577", "Potapova",   "Kalinskaya"),
        ("16198570", "Keys",       "Shnaider"),
        ("16198571", "Sabalenka",  "Osaka"),
        ("16198546", "Svitolina",  "Kostyuk"),
        ("16198539", "Andreeva",   "Cirstea"),
    ],
    # ── Add new match days below ───────────────────────────────────────────
    # "2026-06-03": [
    #     ("MATCH_ID", "Player1", "Player2"),
    # ],
}


def get(path, params=None, host="sofascore.p.rapidapi.com"):
    headers = {**HEADERS_SS, "x-rapidapi-host": host}
    try:
        r = requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=12)
        if r.status_code == 200:
            return r.json()
        print(f"  [{r.status_code}] {path} — {r.text[:150]}")
    except Exception as e:
        print(f"  [ERR] {path} — {e}")
    return {}


def get_matches_for_date(target_date: str) -> list[dict]:
    """Load matches for a given date from MATCH_DATES lookup."""
    entries = MATCH_DATES.get(target_date, [])
    if not entries:
        print(f"\n⚠  No match IDs found for {target_date}.")
        print("   To add them:")
        print("   1. Go to sofascore.com → Tennis → Roland Garros")
        print("   2. Click a match — the ID is the number at the end of the URL")
        print(f"   3. Add to MATCH_DATES[\"{target_date}\"] at the top of this script")
        return []
    matches = []
    for mid, home, away in entries:
        matches.append({"matchId": str(mid), "home": home, "away": away})
    print(f"\n  Loaded {len(matches)} matches for {target_date}")
    return matches


def get_stats(match_id: str) -> dict:
    raw = get("/matches/get-statistics", {"matchId": match_id})
    result = {}
    for block in raw.get("statistics", []):
        period = block.get("period", "ALL")
        for group in block.get("groups", []):
            group_name = group.get("groupName", "")
            for item in group.get("statisticsItems", []):
                key   = item.get("key") or item.get("name", "").replace(" ", "_")
                label = f"{key}__{period}" if period != "ALL" else key
                result[label] = {
                    "name":  item.get("name"),
                    "group": group_name,
                    "home":  item.get("home"),
                    "away":  item.get("away"),
                }
    return result


def get_odds(match_id: str) -> dict:
    raw = get("/matches/get-all-odds", {"matchId": match_id})
    markets = raw.get("markets", [])
    market = next(
        (m for m in markets if m.get("marketId") == 1
         or m.get("marketName") in ("Full time", "Winner", "Match Winner")),
        None
    )
    if not market:
        return {}
    home = away = None
    for choice in market.get("choices", []):
        name = str(choice.get("name", "")).lower()
        frac = choice.get("fractionalValue") or choice.get("initialFractionalValue")
        pos  = choice.get("position")
        if name in ("1", "home") or pos == 1:
            home = frac
        elif name in ("2", "away") or pos == 2:
            away = frac
    return {
        "homeFractional": home,
        "awayFractional": away,
        "suspended": bool(market.get("suspended")),
    }


def get_score(match_id: str) -> dict:
    """Get final score / current score from match detail."""
    raw = get("/matches/detail", {"matchId": match_id})
    e = raw.get("event", {})
    if not e:
        return {}
    home_score = e.get("homeScore", {})
    away_score = e.get("awayScore", {})
    winner = e.get("winnerCode")  # 1=home, 2=away
    status = e.get("status", {}).get("type", "unknown")
    return {
        "status":     status,
        "homeSets":   home_score.get("current"),
        "awaySets":   away_score.get("current"),
        "homeGames":  home_score.get("normaltime"),
        "awayGames":  away_score.get("normaltime"),
        "winnerCode": winner,
        "periods": {
            f"set{i}": {
                "home": home_score.get(f"period{i}"),
                "away": away_score.get(f"period{i}"),
            }
            for i in range(1, 6)
            if home_score.get(f"period{i}") is not None
        },
    }


def frac_to_american(frac_str: str) -> str:
    """Convert '5/4' fractional odds to American (+125)."""
    if not frac_str or "/" not in str(frac_str):
        return str(frac_str)
    try:
        n, d = map(int, str(frac_str).split("/"))
        decimal = n / d + 1
        if decimal >= 2.0:
            return f"+{round((decimal - 1) * 100)}"
        else:
            return f"{round(-100 / (decimal - 1))}"
    except:
        return str(frac_str)


def print_match_summary(m: dict, stats: dict, odds: dict, score: dict):
    home, away = m["home"], m["away"]
    print(f"\n  ── {home} vs {away} [{m['round']}] ──")
    print(f"     Status: {m['status']}  |  Start: {m['startTime']}")

    if score:
        wc = score.get("winnerCode")
        winner = home if wc == 1 else away if wc == 2 else "TBD"
        sets_h = score.get("homeSets", "?")
        sets_a = score.get("awaySets", "?")
        periods = score.get("periods", {})
        period_str = "  ".join(f"{v['home']}-{v['away']}" for v in periods.values())
        print(f"     Score: {home} {sets_h}-{sets_a} {away}  ({period_str})")
        if wc:
            print(f"     WINNER: {winner}")

    if stats:
        key_stats = [
            ("aces", "Aces"),
            ("doubleFaults", "Double Faults"),
            ("firstServeAccuracy", "1st Serve %"),
            ("firstServePointsAccuracy", "1st Srv Pts Won"),
            ("breakPointsScored", "BP Won"),
            ("gamesWon", "Games Won"),
            ("winnersTotal", "Winners"),
            ("unforcedErrorsTotal", "Unforced Errors"),
        ]
        for key, label in key_stats:
            if key in stats:
                s = stats[key]
                print(f"     {label}: {home} {s['home']} | {away} {s['away']}")
    else:
        print("     Stats: not yet available (match not finished or no data)")

    if odds:
        h_am = frac_to_american(odds.get("homeFractional"))
        a_am = frac_to_american(odds.get("awayFractional"))
        susp = " [SUSPENDED]" if odds.get("suspended") else ""
        print(f"     Odds: {home} {h_am} | {away} {a_am}{susp}")


# ── MAIN ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--date", default=date.today().isoformat(),
                    help="Date to fetch (YYYY-MM-DD). Default: today.")
args = parser.parse_args()
target_date = args.date

print(f"\nAstroTennis — Daily Results Fetcher")
print(f"Target date: {target_date}")
print("=" * 50)

# Load matches for this date
matches = get_matches_for_date(target_date)

if not matches:
    exit(0)

results = []
for m in matches:
    mid = m["matchId"]
    if not mid:
        continue

    print(f"\n[{m['home']} vs {m['away']}] ID={mid}")

    # Get score + status from match detail
    print("  Detail...", end=" ", flush=True)
    score = get_score(mid)
    status = score.pop("status", "unknown") if score else "unknown"
    print(f"status={status}")
    time.sleep(0.3)

    is_finished = status == "finished"

    # Stats only for finished matches
    stats = {}
    if is_finished:
        print("  Stats...", end=" ", flush=True)
        stats = get_stats(mid)
        print(f"{len(stats)} keys" if stats else "no data")
        time.sleep(0.3)
    else:
        print(f"  Stats: skipped (match {status})")

    # Odds for all matches
    print("  Odds...", end=" ", flush=True)
    odds = get_odds(mid)
    h_am = frac_to_american(odds.get("homeFractional")) if odds else "N/A"
    a_am = frac_to_american(odds.get("awayFractional")) if odds else "N/A"
    print(f"{h_am} / {a_am}" if odds else "no odds")
    time.sleep(0.3)

    print_match_summary({**m, "status": status, "round": "", "startTime": ""},
                        stats, odds, score)

    results.append({
        "matchId":    mid,
        "home":       m["home"],
        "away":       m["away"],
        "status":     status,
        "score":      score,
        "stats":      stats,
        "odds":       odds,
        "oddsAmerican": {
            "home": frac_to_american(odds.get("homeFractional")) if odds else None,
            "away": frac_to_american(odds.get("awayFractional")) if odds else None,
        },
    })

# Save output
fname = f"results-{target_date}.json"
with open(fname, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{'='*50}")
print(f"✓ Saved {fname} — upload this file to Claude.")
finished = sum(1 for r in results if r["status"] == "finished")
with_stats = sum(1 for r in results if r["stats"])
print(f"  Matches found:       {len(results)}")
print(f"  Finished:            {finished}")
print(f"  With full stats:     {with_stats}")
print(f"  With odds:           {sum(1 for r in results if r['odds'])}")
print(f"\nThen tell Claude: 'rebuild PDF with results-{target_date}.json'")
