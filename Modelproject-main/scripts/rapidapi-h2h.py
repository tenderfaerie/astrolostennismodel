"""
RapidAPI H2H fetcher
====================
Uses two RapidAPI tennis sources to get real H2H records:
  1. Sofascore via RapidAPI  — matches/get-h2h-events (needs event ID)
  2. Tennis API ATP WTA ITF  — getH2HFixtures (needs player IDs)

Usage:
  python3 rapidapi-h2h.py

Output: data/tennislive/h2h/h2h-rapidapi-<date>.json
"""

import json
import time
import requests
from datetime import date
from pathlib import Path

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"

HEADERS_SS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com",
    "Content-Type":    "application/json",
}

HEADERS_TENNIS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "tennis-api-atp-wta-itf.p.rapidapi.com",
    "Content-Type":    "application/json",
}

DATA = Path(__file__).parent.parent / "data" / "tennislive"

# RG June 1 QF event IDs (Sofascore)
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


def fetch_ss_h2h(event_id: str) -> dict:
    """Sofascore RapidAPI — matches/get-h2h-events"""
    url = "https://sofascore.p.rapidapi.com/matches/get-h2h-events"
    params = {"matchId": event_id}
    try:
        r = requests.get(url, headers=HEADERS_SS, params=params, timeout=10)
        print(f"    SS status: {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"    SS body: {r.text[:200]}")
    except Exception as e:
        print(f"    SS error: {e}")
    return {}


def parse_ss_h2h(raw: dict, event_id: str, home: str, away: str) -> dict:
    """Parse Sofascore H2H response."""
    # Try both possible keys
    events = (raw.get("events") or raw.get("h2hEvents") or
              raw.get("data", {}).get("events") or [])

    if not events:
        print(f"    No events found. Keys: {list(raw.keys())}")
        return {"eventId": event_id, "homePlayer": home, "awayPlayer": away,
                "totalMatches": 0, "source": "sofascore-rapidapi", "raw_keys": list(raw.keys())}

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
        from datetime import datetime
        ts = e.get("startTimestamp")
        year = datetime.fromtimestamp(ts).strftime("%Y") if ts else "?"
        surf = (e.get("groundType") or
                e.get("tournament", {}).get("groundType") or "?")
        tourn = (e.get("tournament", {}).get("uniqueTournament", {}).get("name")
                 or e.get("tournament", {}).get("name") or "")
        w_code = e.get("winnerCode")
        h_name = e.get("homeTeam", {}).get("name") or home
        a_name = e.get("awayTeam", {}).get("name") or away
        winner = h_name if w_code == 1 else a_name if w_code == 2 else "?"
        recent.append({"year": year, "surface": surf, "tournament": tourn, "winner": winner})

    # Get actual player names from data
    if events:
        home_name = events[0].get("homeTeam", {}).get("name") or home
        away_name = events[0].get("awayTeam", {}).get("name") or away
    else:
        home_name, away_name = home, away

    return {
        "eventId": event_id,
        "homePlayer": home_name,
        "awayPlayer": away_name,
        "totalMatches": total,
        "homeWins": home_wins,
        "awayWins": away_wins,
        "clayMatches": len(clay),
        "clayHomeWins": clay_h,
        "clayAwayWins": clay_a,
        "recent": recent,
        "source": "sofascore-rapidapi",
    }


def main():
    out_dir = DATA / "h2h"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for m in MATCHES:
        eid = m["eventId"]
        home, away = m["home"], m["away"]
        print(f"\n[{home} vs {away}] event {eid}")

        raw = fetch_ss_h2h(eid)
        parsed = parse_ss_h2h(raw, eid, home, away)
        results.append(parsed)

        if parsed["totalMatches"] > 0:
            hw = parsed["homeWins"]
            aw = parsed["awayWins"]
            ch = parsed["clayHomeWins"]
            ca = parsed["clayAwayWins"]
            print(f"    ✓ Overall: {home} {hw}-{aw} {away} | Clay: {ch}-{ca}")
        else:
            print(f"    ✗ No H2H data returned")

        time.sleep(0.5)

    fname = f"h2h-rapidapi-{date.today().isoformat()}.json"
    out = out_dir / fname
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {len(results)} H2H records → data/tennislive/h2h/{fname}")

    # Summary
    got_data = sum(1 for r in results if r.get("totalMatches", 0) > 0)
    print(f"Got real H2H data: {got_data}/{len(results)} matches")


if __name__ == "__main__":
    main()
