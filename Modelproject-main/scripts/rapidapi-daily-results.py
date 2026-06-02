"""
AstroTennis — Daily RG Results Fetcher
Run this ON YOUR LOCAL MACHINE each match day.

Step 1: Auto-discovers today's Roland Garros match IDs from schedule
Step 2: Fetches full stats for any completed matches
Step 3: Fetches live odds for upcoming matches
Step 4: Saves everything to results-YYYY-MM-DD.json — upload to Claude

Usage:
  python3 rapidapi-daily-results.py
  python3 rapidapi-daily-results.py --date 2026-06-02   # specific date
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

# Roland Garros tournament IDs on Sofascore
# uniqueTournamentId = 495 (Roland Garros ATP)
# uniqueTournamentId = 496 (Roland Garros WTA)
RG_TOURNAMENT_IDS = [495, 496]

# ── Fallback: manually add match IDs if discovery fails ───────────────────────
# Copy match IDs from Sofascore URLs (sofascore.com/tennis/match/XXXXXXXX)
# Leave empty [] to rely purely on auto-discovery
MANUAL_MATCH_IDS = []


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


def discover_matches(target_date: str) -> list[dict]:
    """
    Try multiple endpoints to find today's RG matches.
    Returns list of {matchId, home, away, status, startTime}
    """
    matches = []
    print(f"\n=== Discovering RG matches for {target_date} ===")

    # Endpoint 1: scheduled-events by date (sport=tennis id=1)
    print("  Trying sport/tennis/scheduled-events...")
    raw = get(f"/sport/1/scheduled-events/{target_date}")
    if raw:
        events = raw.get("events", [])
        print(f"  Found {len(events)} total tennis events")
        for e in events:
            tourn = e.get("tournament", {})
            uid = tourn.get("uniqueTournament", {}).get("id")
            if uid in RG_TOURNAMENT_IDS:
                matches.append(_parse_event(e))

    if not matches:
        # Endpoint 2: events/list-by-date
        print("  Trying events/list-by-date...")
        raw = get("/events/list-by-date", {"sport": "tennis", "date": target_date})
        if raw:
            for e in raw.get("events", []):
                uid = e.get("tournament", {}).get("uniqueTournament", {}).get("id")
                if uid in RG_TOURNAMENT_IDS:
                    matches.append(_parse_event(e))

    if not matches:
        # Endpoint 3: tournament events
        print("  Trying tournament events endpoint...")
        for tid in RG_TOURNAMENT_IDS:
            raw = get(f"/unique-tournament/{tid}/events/last/0")
            for e in raw.get("events", []):
                ts = e.get("startTimestamp", 0)
                e_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
                if e_date == target_date:
                    matches.append(_parse_event(e))

    if not matches:
        # Endpoint 4: try /tournaments/get-rounds style
        print("  Trying tournament seasons/rounds...")
        for tid in RG_TOURNAMENT_IDS:
            # Get current season
            raw = get(f"/unique-tournament/{tid}/seasons")
            seasons = raw.get("seasons", [])
            if seasons:
                season_id = seasons[0].get("id")
                rounds_raw = get(f"/unique-tournament/{tid}/season/{season_id}/events/last/0")
                for e in rounds_raw.get("events", []):
                    ts = e.get("startTimestamp", 0)
                    e_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
                    if e_date == target_date:
                        matches.append(_parse_event(e))

    # Add any manually specified IDs
    for mid in MANUAL_MATCH_IDS:
        if not any(m["matchId"] == str(mid) for m in matches):
            detail = get("/matches/detail", {"matchId": mid})
            e = detail.get("event", {})
            if e:
                matches.append(_parse_event(e))

    print(f"\n  Found {len(matches)} RG matches for {target_date}")
    return matches


def _parse_event(e: dict) -> dict:
    status = e.get("status", {}).get("type", "unknown")  # "finished", "inprogress", "notstarted"
    home = (e.get("homeTeam") or e.get("homeScore") or {}).get("name", "?")
    away = (e.get("awayTeam") or e.get("awayScore") or {}).get("name", "?")
    # Try homeTeam/awayTeam keys
    home = e.get("homeTeam", {}).get("name") or home
    away = e.get("awayTeam", {}).get("name") or away
    ts = e.get("startTimestamp")
    round_info = e.get("roundInfo", {}).get("name", "")
    return {
        "matchId":   str(e.get("id", "")),
        "home":      home,
        "away":      away,
        "status":    status,
        "round":     round_info,
        "startTime": datetime.fromtimestamp(ts).strftime("%H:%M") if ts else "?",
        "customId":  e.get("customId", ""),
    }


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
    return {
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

# Discover matches
matches = discover_matches(target_date)

if not matches:
    print("\n⚠ No matches auto-discovered.")
    print("  Add match IDs manually to MANUAL_MATCH_IDS list at top of script.")
    print("  Find IDs on Sofascore: sofascore.com/tennis → click match → ID is in the URL")
    exit(0)

results = []
for m in matches:
    mid = m["matchId"]
    if not mid:
        continue

    is_finished = m["status"] == "finished"
    has_score   = m["status"] in ("finished", "inprogress")

    print(f"\n[{m['home']} vs {m['away']}] ID={mid} status={m['status']}")

    # Always get score
    score = {}
    if has_score:
        print("  Score...", end=" ", flush=True)
        score = get_score(mid)
        print("ok" if score else "empty")
        time.sleep(0.3)

    # Stats only for finished matches
    stats = {}
    if is_finished:
        print("  Stats...", end=" ", flush=True)
        stats = get_stats(mid)
        print(f"{len(stats)} keys" if stats else "no data")
        time.sleep(0.3)

    # Odds for all matches
    print("  Odds...", end=" ", flush=True)
    odds = get_odds(mid)
    h_am = frac_to_american(odds.get("homeFractional")) if odds else "N/A"
    a_am = frac_to_american(odds.get("awayFractional")) if odds else "N/A"
    print(f"{h_am} / {a_am}" if odds else "no odds")
    time.sleep(0.3)

    print_match_summary(m, stats, odds, score)

    results.append({
        "matchId":    mid,
        "home":       m["home"],
        "away":       m["away"],
        "round":      m["round"],
        "status":     m["status"],
        "startTime":  m["startTime"],
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
