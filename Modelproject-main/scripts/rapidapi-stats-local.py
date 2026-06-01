"""
Run this script ON YOUR LOCAL MACHINE.
Fetches match stats for all QF players via RapidAPI Sofascore.

Steps:
  1. Gets R16 match stats (yesterday's matches)
  2. Gets recent clay match stats (Rome/Madrid) for each player
  3. Saves player-stats-2026-06-01.json — upload that to Claude

Usage:
  pip install requests
  python3 rapidapi-stats-local.py

Output: player-stats-2026-06-01.json
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

# ── R16 match IDs (yesterday's completed matches) ─────────────────────────────
# Each entry: (matchId, home_player, away_player)
R16_MATCHES = [
    # ATP R16 — players in today's QF
    ("16198473", "Mensik",    "Fonseca"),    # Mensik vs Fonseca R16 (wait — check: Mensik beat Rublev, Fonseca beat Ruud)
    ("16198476", "Jodar",     "Zverev"),     # Jodar R16, Zverev R16
    # WTA R16 — players in today's QF
    ("16198539", "Andreeva",  "Cirstea"),    # Andreeva R16
    ("16198546", "Svitolina", "Kostyuk"),    # Svitolina R16
]

# ── TODAY'S QF match IDs ──────────────────────────────────────────────────────
QF_MATCHES = [
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

# ── Player IDs (Sofascore) ────────────────────────────────────────────────────
# Get these from matches/detail homeTeam.id / awayTeam.id
# We'll look them up dynamically, but hardcode known ones as fallback
PLAYER_IDS = {
    "Cobolli":    273680,
    "Svajda":     298247,
    "Mensik":     None,   # will be fetched
    "Fonseca":    None,
    "Zverev":     None,
    "Jodar":      None,
    "Andreeva":   None,
    "Cirstea":    None,
    "Svitolina":  None,
    "Kostyuk":    None,
    "Sabalenka":  None,
    "Osaka":      None,
    "Keys":       None,
    "Shnaider":   None,
    "Cerundolo":  None,
    "Berrettini": None,
    "Tiafoe":     None,
    "Arnaldi":    None,
    "FAA":        None,
    "Tabilo":     None,
    "Potapova":   None,
    "Kalinskaya": None,
}


def get(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        print(f"  HTTP {r.status_code}: {path} {params}")
    except Exception as e:
        print(f"  Error: {e}")
    return {}


def get_match_detail(match_id):
    return get("/matches/detail", {"matchId": match_id})


def get_match_stats(match_id):
    """Get overall match stats (aces, DFs, 1st serve %, etc.)"""
    return get("/matches/get-statistics", {"matchId": match_id})


def get_player_match_stats(match_id, player_id):
    """Get individual player stats for a specific match."""
    return get("/matches/get-player-statistics",
               {"matchId": match_id, "playerId": player_id})


def get_player_recent_matches(player_id):
    """Get recent matches for a player to find clay results."""
    return get(f"/players/{player_id}/matches/previous/0")


def parse_match_stats(raw):
    """Extract key tennis stats from match statistics response."""
    result = {}
    stats_list = raw.get("statistics", []) or []
    for block in stats_list:
        if block.get("period") not in ("ALL", None, ""):
            continue
        for group in block.get("groups", []):
            for item in group.get("statisticsItems", []):
                key = item.get("key") or item.get("name") or ""
                result[key] = {
                    "home": item.get("home"),
                    "away": item.get("away"),
                    "name": item.get("name"),
                }
    return result


def parse_player_stats(raw):
    """Extract stats from player-statistics response."""
    result = {}
    for group in raw.get("playerStatistics", {}).get("statistics", []):
        for item in group.get("statisticsItems", []):
            key = item.get("key") or item.get("name") or ""
            result[key] = item.get("value")
    # Also try flat structure
    stats = raw.get("statistics", {})
    if isinstance(stats, dict):
        result.update(stats)
    return result


def lookup_player_ids():
    """Fetch player IDs from match detail for all QF matches."""
    print("Looking up player IDs from match details...")
    for match_id, home, away in QF_MATCHES:
        detail = get_match_detail(match_id)
        event = detail.get("event", {})
        home_id = event.get("homeTeam", {}).get("id")
        away_id = event.get("awayTeam", {}).get("id")
        if home_id and PLAYER_IDS.get(home) is None:
            PLAYER_IDS[home] = home_id
            print(f"  {home}: {home_id}")
        if away_id and PLAYER_IDS.get(away) is None:
            PLAYER_IDS[away] = away_id
            print(f"  {away}: {away_id}")
        time.sleep(0.3)


def fetch_r16_stats():
    """Get stats from yesterday's R16 matches."""
    print("\nFetching R16 match stats...")
    r16_stats = {}

    # We need the actual R16 match IDs for the players who are in today's QF
    # The QF match IDs are reused — we need their R16 match IDs
    # Let's get them from player recent matches
    r16_match_ids = {
        # Known R16 match IDs from earlier in the tournament
        # These are the matches played yesterday (R16)
        # We'll fetch via player recent matches
    }

    for player, pid in PLAYER_IDS.items():
        if pid is None:
            continue
        print(f"  {player} recent matches...", end=" ", flush=True)
        recent = get_player_recent_matches(pid)
        events = recent.get("events", [])

        clay_matches = []
        for e in events[:20]:  # last 20 matches
            ground = (e.get("groundType") or
                      e.get("tournament", {}).get("groundType") or "").lower()
            tourn_name = (e.get("tournament", {}).get("uniqueTournament", {}).get("name")
                         or e.get("tournament", {}).get("name") or "")
            ts = e.get("startTimestamp", 0)
            year = datetime.fromtimestamp(ts).strftime("%Y") if ts else "?"
            eid = str(e.get("id", ""))

            if "clay" in ground:
                home_name = e.get("homeTeam", {}).get("name") or ""
                away_name = e.get("awayTeam", {}).get("name") or ""
                w_code = e.get("winnerCode")
                is_home = pid == e.get("homeTeam", {}).get("id")
                won = (w_code == 1 and is_home) or (w_code == 2 and not is_home)
                clay_matches.append({
                    "matchId": eid,
                    "tournament": tourn_name,
                    "year": year,
                    "opponent": away_name if is_home else home_name,
                    "won": won,
                    "surface": e.get("groundType") or "clay",
                })

        print(f"{len(clay_matches)} clay matches found")
        r16_stats[player] = {"recentClay": clay_matches[:5]}
        time.sleep(0.4)

    return r16_stats


def fetch_qf_match_stats():
    """Get stats for today's QF matches (may be empty if not started)."""
    print("\nFetching QF match stats (pre-match odds + any available stats)...")
    qf_stats = {}
    for match_id, home, away in QF_MATCHES:
        print(f"  {home} vs {away}...", end=" ", flush=True)
        stats = get_match_stats(match_id)
        parsed = parse_match_stats(stats)
        if parsed:
            print(f"{len(parsed)} stat keys")
        else:
            print("no stats yet (pre-match)")
        qf_stats[f"{home}_vs_{away}"] = {
            "matchId": match_id,
            "stats": parsed,
        }
        time.sleep(0.3)
    return qf_stats


def fetch_recent_clay_match_stats(r16_data):
    """For each player, fetch actual stats from their most recent clay matches."""
    print("\nFetching stats from recent clay matches...")
    player_clay_stats = {}

    for player, data in r16_data.items():
        clay_matches = data.get("recentClay", [])
        if not clay_matches:
            continue

        match_stats_list = []
        for cm in clay_matches[:3]:  # get stats for last 3 clay matches
            mid = cm["matchId"]
            if not mid:
                continue
            pid = PLAYER_IDS.get(player)
            print(f"  {player} vs {cm['opponent']} ({cm['tournament']} {cm['year']})...",
                  end=" ", flush=True)

            # Try match-level stats first
            mstats = get_match_stats(mid)
            parsed = parse_match_stats(mstats)

            # Try player-level stats
            pstats = {}
            if pid:
                praw = get_player_match_stats(mid, pid)
                pstats = parse_player_stats(praw)

            if parsed or pstats:
                print("✓")
            else:
                print("empty")

            match_stats_list.append({
                **cm,
                "matchStats": parsed,
                "playerStats": pstats,
            })
            time.sleep(0.4)

        player_clay_stats[player] = match_stats_list

    return player_clay_stats


def main():
    # Step 1: Get all player IDs
    lookup_player_ids()

    # Step 2: Get recent clay matches for each player
    r16_data = fetch_r16_stats()

    # Step 3: Get stats from those clay matches
    clay_stats = fetch_recent_clay_match_stats(r16_data)

    # Step 4: Check today's QF matches for any live stats
    qf_stats = fetch_qf_match_stats()

    # Combine everything
    output = {
        "fetchedAt": datetime.now().isoformat(),
        "playerIds": PLAYER_IDS,
        "recentClaySummary": {
            player: {
                "recentClay": data.get("recentClay", []),
                "detailedStats": clay_stats.get(player, []),
            }
            for player, data in r16_data.items()
        },
        "qfMatchStats": qf_stats,
    }

    with open("player-stats-2026-06-01.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n✓ Done! Upload player-stats-2026-06-01.json to Claude.")
    print(f"  Players with clay history: "
          f"{sum(1 for p in r16_data.values() if p.get('recentClay'))}")


if __name__ == "__main__":
    main()
