"""
Diagnostic: find the correct endpoint for player recent matches.
Run this, paste the output to Claude.

Usage: python3 rapidapi-find-endpoint.py
"""
import requests

API_KEY = "ccb713eb03msh65a47090f359a7fp158927jsncaee283e8076"
HEADERS = {
    "x-rapidapi-key":  API_KEY,
    "x-rapidapi-host": "sofascore.p.rapidapi.com",
}
BASE = "https://sofascore.p.rapidapi.com"

# Zverev player ID = 57163
PID = 57163

# Known working match ID (Cobolli vs Svajda QF)
MID = 16198484

TESTS = [
    # Player/team recent matches
    f"/teams/{PID}/matches/previous/0",
    f"/teams/{PID}/events/previous/0",
    f"/teams/{PID}/matches",
    f"/players/{PID}/matches/previous/0",
    f"/players/{PID}/events",
    # Match stats endpoints using known match ID
    f"/matches/get-statistics?matchId={MID}",
    f"/matches/get-player-statistics?matchId={MID}&playerId={PID}",
    f"/matches/get-best-players?matchId={MID}",
    f"/matches/get-lineups?matchId={MID}",
]

print(f"Testing endpoints with playerId={PID}, matchId={MID}\n")
for path in TESTS:
    if "?" in path:
        url = f"{BASE}/{path.split('?')[0]}"
        params = dict(p.split("=") for p in path.split("?")[1].split("&"))
    else:
        url = f"{BASE}{path}"
        params = None
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=8)
        body = r.text[:120].replace("\n", " ")
        print(f"[{r.status_code}] {path}")
        print(f"         {body}")
    except Exception as e:
        print(f"[ERR] {path} — {e}")
    print()
