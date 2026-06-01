"""
Run this script ON YOUR LOCAL MACHINE (not the server).
It fetches H2H data for all 11 RG QF matches via RapidAPI.

Usage:
  pip install requests
  python3 rapidapi-h2h-local.py

Output: h2h-live-2026-06-01.json  (upload this file to Claude)
"""

import json
import time
import requests
from datetime import datetime

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com",
    "Content-Type":    "application/json",
}
BASE = "https://sofascore.p.rapidapi.com"

MATCHES = [
    {"eventId": "16198484", "home": "Cobolli",    "away": "Svajda"},
    {"eventId": "16198515", "home": "Cerundolo",  "away": "Berrettini"},
    {"eventId": "16198517", "home": "Tiafoe",     "away": "Arnaldi"},
    {"eventId": "16198519", "home": "FAA",         "away": "Tabilo"},
    {"eventId": "16198473", "home": "Mensik",     "away": "Fonseca"},
    {"eventId": "16198476", "home": "Jodar",      "away": "Zverev"},
    {"eventId": "16198577", "home": "Potapova",   "away": "Kalinskaya"},
    {"eventId": "16198570", "home": "Keys",       "away": "Shnaider"},
    {"eventId": "16198571", "home": "Sabalenka",  "away": "Osaka"},
    {"eventId": "16198546", "home": "Svitolina",  "away": "Kostyuk"},
    {"eventId": "16198539", "home": "Andreeva",   "away": "Cirstea"},
]

def get_custom_id(event_id):
    r = requests.get(f"{BASE}/matches/detail",
                     params={"matchId": event_id}, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json().get("event", {}).get("customId")
    return None

def get_h2h(custom_id):
    r = requests.get(f"{BASE}/matches/get-h2h-events",
                     params={"customId": custom_id}, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()
    return {}

def parse_h2h(raw, home, away):
    events = raw.get("events") or raw.get("h2hEvents") or []
    if not events:
        return {"totalMatches": 0, "homeWins": 0, "awayWins": 0,
                "clayMatches": 0, "clayHomeWins": 0, "clayAwayWins": 0, "recent": []}

    total = len(events)
    home_wins = sum(1 for e in events if e.get("winnerCode") == 1)
    away_wins = sum(1 for e in events if e.get("winnerCode") == 2)

    def is_clay(e):
        g = (e.get("groundType") or
             e.get("tournament", {}).get("groundType") or "").lower()
        return "clay" in g

    clay = [e for e in events if is_clay(e)]
    clay_h = sum(1 for e in clay if e.get("winnerCode") == 1)
    clay_a = sum(1 for e in clay if e.get("winnerCode") == 2)

    recent = []
    for e in events[:6]:
        ts = e.get("startTimestamp")
        year = datetime.fromtimestamp(ts).strftime("%Y") if ts else "?"
        surf = (e.get("groundType") or
                e.get("tournament", {}).get("groundType") or "?")
        tourn = (e.get("tournament", {}).get("uniqueTournament", {}).get("name")
                 or e.get("tournament", {}).get("name") or "")
        w = e.get("winnerCode")
        h_name = e.get("homeTeam", {}).get("name") or home
        a_name = e.get("awayTeam", {}).get("name") or away
        winner = h_name if w == 1 else a_name if w == 2 else "?"
        recent.append({"year": year, "surface": surf, "tournament": tourn, "winner": winner})

    return {
        "totalMatches": total,
        "homeWins": home_wins,
        "awayWins": away_wins,
        "clayMatches": len(clay),
        "clayHomeWins": clay_h,
        "clayAwayWins": clay_a,
        "recent": recent,
    }

results = []
for m in MATCHES:
    home, away = m["home"], m["away"]
    print(f"{home} vs {away}...", end=" ", flush=True)

    cid = get_custom_id(m["eventId"])
    if not cid:
        print("FAILED (no customId)")
        results.append({"home": home, "away": away, "error": "no customId"})
        continue

    time.sleep(0.3)
    raw = get_h2h(cid)
    h2h = parse_h2h(raw, home, away)
    h2h["home"] = home
    h2h["away"] = away
    h2h["customId"] = cid
    results.append(h2h)

    total = h2h["totalMatches"]
    if total > 0:
        hw, aw = h2h["homeWins"], h2h["awayWins"]
        ch, ca = h2h["clayHomeWins"], h2h["clayAwayWins"]
        print(f"Overall {home} {hw}-{aw} {away} | Clay {ch}-{ca}")
    else:
        print("No prior H2H")
    time.sleep(0.4)

with open("h2h-live-2026-06-01.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDone! Upload h2h-live-2026-06-01.json to Claude.")
