"""
Run this ON YOUR LOCAL MACHINE.
Pulls match statistics for all 11 RG matches via RapidAPI Sofascore.
matches/get-statistics works directly with match IDs — no player lookup needed.

Usage:
  pip install requests
  python3 rapidapi-stats-local.py

Output: player-stats-2026-06-01.json  — upload to Claude
"""

import json
import time
import requests

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com",
    "Content-Type":    "application/json",
}
BASE = "https://sofascore.p.rapidapi.com"

MATCHES = [
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
]

def get(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        print(f"  HTTP {r.status_code}")
    except Exception as e:
        print(f"  Error: {e}")
    return {}

def parse_stats(raw):
    """Flatten all stats periods into a clean dict."""
    result = {}
    for block in raw.get("statistics", []):
        period = block.get("period", "ALL")
        for group in block.get("groups", []):
            group_name = group.get("groupName", "")
            for item in group.get("statisticsItems", []):
                key   = item.get("key") or item.get("name", "").replace(" ", "_")
                home  = item.get("home")
                away  = item.get("away")
                label = f"{key}__{period}" if period != "ALL" else key
                result[label] = {
                    "name":  item.get("name"),
                    "group": group_name,
                    "home":  home,
                    "away":  away,
                }
    return result

def get_odds(match_id):
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
    return {"homeFractional": home, "awayFractional": away,
            "suspended": bool(market.get("suspended"))}

results = []
for match_id, home, away in MATCHES:
    print(f"\n[{home} vs {away}]")

    # Stats
    print(f"  Stats...", end=" ", flush=True)
    raw_stats = get("/matches/get-statistics", {"matchId": match_id})
    stats = parse_stats(raw_stats)
    if stats:
        print(f"{len(stats)} keys")
        # Show key stats
        for key in ["Aces", "DoubleFaults", "FirstServePercentage",
                    "FirstServePointsWon", "BreakPointsConverted",
                    "Winners", "UnforcedErrors"]:
            if key in stats:
                s = stats[key]
                print(f"    {s['name']}: {home} {s['home']} | {away} {s['away']}")
    else:
        print("no stats (match not yet played or unavailable)")

    # Odds
    print(f"  Odds...", end=" ", flush=True)
    odds = get_odds(match_id)
    if odds.get("homeFractional") or odds.get("awayFractional"):
        print(f"home={odds['homeFractional']} away={odds['awayFractional']}")
    else:
        print("no odds")

    results.append({
        "matchId":    match_id,
        "homePlayer": home,
        "awayPlayer": away,
        "stats":      stats,
        "odds":       odds,
    })
    time.sleep(0.4)

with open("player-stats-2026-06-01.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved player-stats-2026-06-01.json — upload this to Claude.")
has_stats = sum(1 for r in results if r["stats"])
print(f"  Matches with stats: {has_stats}/{len(results)}")
