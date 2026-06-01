"""
Run this ON YOUR LOCAL MACHINE.
Fetches RG 2026 QF predictions + player seasonal stats from Tennis API (tennis-api5).

Usage:
  python3 tennisapi5-local.py

Output: tennisapi5-2026-06-01.json  — upload to Claude
"""

import json
import time
import requests
from datetime import datetime

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "tennis-api5.p.rapidapi.com",
    "Content-Type":    "application/json",
}
BASE = "https://tennis-api5.p.rapidapi.com"

QF_PLAYERS = [
    "Tiafoe", "Arnaldi", "Mensik", "Fonseca", "Jodar", "Zverev",
    "Sabalenka", "Osaka", "Svitolina", "Kostyuk", "Andreeva", "Cirstea",
    # Completed QF players (for SF projections later)
    "Cobolli", "Shnaider", "Berrettini", "FAA", "Potapova",
]

def get(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=12)
        print(f"    [{r.status_code}] {path}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"    body: {r.text[:300]}")
    except Exception as e:
        print(f"    Error: {e}")
    return {}

# ── Step 1: Find RG competition ──────────────────────────────────────────────
print("=== Step 1: Discover Roland Garros 2026 ===")
schedule = get("/competitionschedule", {"name": "Roland Garros"})
print(json.dumps(schedule, indent=2)[:2000])

time.sleep(0.5)

# Also try tour calendar
print("\n=== Tour Calendar (June 2026) ===")
cal = get("/tourcalendar", {"year": "2026", "month": "6"})
print(json.dumps(cal, indent=2)[:2000])

time.sleep(0.5)

# ── Step 2: Try rankings to find player IDs ──────────────────────────────────
print("\n=== Rankings (ATP) ===")
atp_rank = get("/rankings", {"tour": "atp"})
print(json.dumps(atp_rank, indent=2)[:3000])

time.sleep(0.5)

print("\n=== Rankings (WTA) ===")
wta_rank = get("/rankings", {"tour": "wta"})
print(json.dumps(wta_rank, indent=2)[:3000])

time.sleep(0.5)

# ── Step 3: Try seasonal stats (clay) ────────────────────────────────────────
print("\n=== Seasonal Stats / Rankings (clay) ===")
clay_stats = get("/seasonalstatsrankings", {"surface": "clay", "tour": "atp", "year": "2026"})
print(json.dumps(clay_stats, indent=2)[:3000])

time.sleep(0.5)

clay_wta = get("/seasonalstatsrankings", {"surface": "clay", "tour": "wta", "year": "2026"})
print(json.dumps(clay_wta, indent=2)[:3000])

time.sleep(0.5)

# ── Step 4: Search for players by name to get their IDs ─────────────────────
print("\n=== Player search ===")
player_ids = {}
for name in QF_PLAYERS[:6]:  # limit to avoid quota
    result = get("/players", {"name": name})
    if result:
        print(f"  {name}: {json.dumps(result)[:200]}")
        player_ids[name] = result
    time.sleep(0.4)

# ── Save everything ──────────────────────────────────────────────────────────
output = {
    "schedule": schedule,
    "calendar": cal,
    "atp_rankings": atp_rank,
    "wta_rankings": wta_rank,
    "clay_stats_atp": clay_stats,
    "clay_stats_wta": clay_wta,
    "player_lookups": player_ids,
}

with open("tennisapi5-2026-06-01.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n✓ Saved tennisapi5-2026-06-01.json — upload this to Claude.")
print("  This will show us what IDs and endpoints are available.")
