"""
Sofascore tennis stats scraper
================================
Pulls full match stats, moneylines, and scores for any date.

Usage:
  python3 sofascore-tennis.py                    # today, all matches
  python3 sofascore-tennis.py 2026-05-31         # specific date
  python3 sofascore-tennis.py 2026-06-01 live    # only live matches
  python3 sofascore-tennis.py 2026-06-01 finished
  python3 sofascore-tennis.py 2026-06-01 upcoming

Output: data/tennislive/matches/ss-<date>[-<mode>].json

Stats included per match:
  aces, double faults, first serve %, winners, unforced errors,
  break points won/saved, net points, total points won, moneyline odds
"""

import json
import sys
import time
from datetime import datetime, date, timezone
from pathlib import Path

import tls_client

BASE_URL = "https://api.sofascore.com/api/v1"
DATA = Path(__file__).parent.parent / "data" / "tennislive"

# Stat keys we care about for the model
STAT_KEYS = {
    "aces", "doubleFaults", "firstServePercentage", "firstServePointsWon",
    "secondServePointsWon", "breakPointsConverted", "breakPointsSaved",
    "winners", "unforcedErrors", "netPointsWon", "totalPointsWon",
    "firstServeReturnPointsWon", "secondServeReturnPointsWon",
    "servicePointsWon", "returnPointsWon",
}

def create_session():
    s = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
    })
    return s

def try_get(session, path):
    try:
        r = session.get(f"{BASE_URL}{path}")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def is_doubles(event):
    t = event.get("tournament", {}).get("name") or ""
    home = event.get("homeTeam", {}).get("name") or ""
    away = event.get("awayTeam", {}).get("name") or ""
    return "Doubles" in t or " / " in home or " / " in away

def normalize_event(event):
    home_score = event.get("homeScore", {})
    away_score = event.get("awayScore", {})
    period_scores = []
    for i in range(1, 6):
        h = home_score.get(f"period{i}")
        a = away_score.get(f"period{i}")
        if h is not None or a is not None:
            period_scores.append({"period": f"S{i}", "home": h, "away": a})

    # Sets won
    home_sets = sum(1 for ps in period_scores
                    if ps["home"] is not None and ps["away"] is not None
                    and ps["home"] > ps["away"])
    away_sets = sum(1 for ps in period_scores
                    if ps["home"] is not None and ps["away"] is not None
                    and ps["away"] > ps["home"])

    status = event.get("status", {})
    return {
        "provider": "sofascore",
        "providerId": str(event.get("id")),
        "tournament": (
            event.get("tournament", {}).get("uniqueTournament", {}).get("name")
            or event.get("tournament", {}).get("name")
            or "Unknown"
        ),
        "category": event.get("tournament", {}).get("category", {}).get("name") or "Tennis",
        "round": event.get("roundInfo", {}).get("name"),
        "status": status.get("description") or "Unknown",
        "statusType": status.get("type"),
        "surface": (event.get("groundType")
                    or event.get("tournament", {}).get("groundType")
                    or "Unknown"),
        "startTimestamp": event.get("startTimestamp"),
        "homePlayer": event.get("homeTeam", {}).get("name") or "?",
        "awayPlayer": event.get("awayTeam", {}).get("name") or "?",
        "homeSetsWon": home_sets,
        "awaySetsWon": away_sets,
        "homeScore": home_score.get("current"),
        "awayScore": away_score.get("current"),
        "periodScores": period_scores,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
    }

def get_stats(session, event_id):
    """Return flat stats dict: {acesHome, acesAway, dfHome, dfAway, ...}"""
    raw = try_get(session, f"/event/{event_id}/statistics")
    if not raw:
        return {}
    result = {}
    for block in raw.get("statistics", []):
        # Prefer ALL period, fall back to others
        period = block.get("period", "")
        for group in block.get("groups", []):
            for item in group.get("statisticsItems", []):
                key = item.get("key") or ""
                if key.lower().replace(" ", "") in {k.lower() for k in STAT_KEYS} or key in STAT_KEYS:
                    suffix = "" if period in ("ALL", "") else f"_{period}"
                    result[f"{key}Home{suffix}"] = item.get("home")
                    result[f"{key}Away{suffix}"] = item.get("away")
    return result

def get_odds(session, event_id):
    """Return moneyline as {homeAmerican, awayAmerican, homeDecimal, awayDecimal}"""
    raw = try_get(session, f"/event/{event_id}/odds/1/all") or \
          try_get(session, f"/event/{event_id}/odds/1/featured") or {}
    markets = raw.get("markets", [])
    market = next(
        (m for m in markets if m.get("marketId") == 1
         or m.get("marketName") in ("Full time", "Winner", "Match Winner")),
        None
    )
    if not market:
        return {}

    def frac_to_dec(f):
        if not f or "/" not in str(f):
            return None
        try:
            n, d = str(f).split("/")
            return round(int(n) / int(d) + 1, 3)
        except Exception:
            return None

    def dec_to_us(d):
        if not d:
            return None
        return round((d - 1) * 100) if d >= 2 else round(-100 / (d - 1))

    home_odds = away_odds = None
    for choice in market.get("choices", []):
        name = str(choice.get("name", "")).lower()
        frac = choice.get("fractionalValue") or choice.get("initialFractionalValue")
        dec = frac_to_dec(frac)
        if name in ("1", "home") or choice.get("position") == 1:
            home_odds = {"decimal": dec, "american": dec_to_us(dec), "fractional": frac}
        elif name in ("2", "away") or choice.get("position") == 2:
            away_odds = {"decimal": dec, "american": dec_to_us(dec), "fractional": frac}

    return {"homeOdds": home_odds, "awayOdds": away_odds,
            "suspended": bool(market.get("suspended"))}

def get_h2h(session, event_id):
    """Return H2H summary: overall and clay records."""
    raw = try_get(session, f"/event/{event_id}/h2h")
    if not raw:
        return {}
    events = raw.get("events", [])
    if not events:
        return {}

    total     = len(events)
    home_wins = sum(1 for e in events if e.get("winnerCode") == 1)
    away_wins = sum(1 for e in events if e.get("winnerCode") == 2)

    def is_clay(e):
        g = (e.get("groundType") or
             e.get("tournament", {}).get("groundType") or "").lower()
        return "clay" in g

    clay_matches = [e for e in events if is_clay(e)]
    clay_home = sum(1 for e in clay_matches if e.get("winnerCode") == 1)
    clay_away = sum(1 for e in clay_matches if e.get("winnerCode") == 2)

    # Last 5 meetings
    recent = []
    for e in events[:5]:
        ts = e.get("startTimestamp")
        year = ""
        if ts:
            from datetime import datetime as dt
            year = dt.fromtimestamp(ts).strftime("%Y")
        surf = (e.get("groundType") or
                e.get("tournament", {}).get("groundType") or "?")
        winner = (e.get("homeTeam", {}).get("name") if e.get("winnerCode") == 1
                  else e.get("awayTeam", {}).get("name") or "?")
        tourn = (e.get("tournament", {}).get("uniqueTournament", {}).get("name")
                 or e.get("tournament", {}).get("name") or "")
        recent.append({
            "year": year, "surface": surf,
            "tournament": tourn, "winner": winner,
        })

    return {
        "totalMatches": total,
        "homeWins": home_wins,
        "awayWins": away_wins,
        "clayMatches": len(clay_matches),
        "clayHomeWins": clay_home,
        "clayAwayWins": clay_away,
        "recent": recent,
    }


def enrich(session, match, fetch_stats=True, fetch_h2h=True):
    eid = match["providerId"]
    if fetch_stats:
        stats = get_stats(session, eid)
        if stats:
            match["stats"] = stats
    odds = get_odds(session, eid)
    if odds.get("homeOdds") or odds.get("awayOdds"):
        match["moneyline"] = odds
    if fetch_h2h:
        h2h = get_h2h(session, eid)
        if h2h:
            match["h2h"] = h2h
    return match

def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"

    session = create_session()
    fetched_at = datetime.now(timezone.utc).isoformat()

    print(f"Fetching Sofascore tennis for {target_date} [{mode}]...")

    # Get all events for the date
    data = try_get(session, f"/sport/tennis/scheduled-events/{target_date}")
    all_events = (data or {}).get("events", [])

    # Also grab live events and merge
    live_data = try_get(session, "/sport/tennis/events/live")
    live_events = (live_data or {}).get("events", [])
    live_ids = {str(e.get("id")) for e in live_events}

    # Merge live into all (update status)
    all_by_id = {str(e.get("id")): e for e in all_events}
    for e in live_events:
        all_by_id[str(e.get("id"))] = e
    all_events = list(all_by_id.values())

    # Filter singles only
    singles = [e for e in all_events if not is_doubles(e)]

    # Filter by mode
    if mode == "live":
        singles = [e for e in singles if str(e.get("id")) in live_ids]
    elif mode == "finished":
        singles = [e for e in singles if e.get("status", {}).get("type") == "finished"]
    elif mode == "upcoming":
        singles = [e for e in singles if e.get("status", {}).get("type") == "notstarted"]
    # "all" keeps everything

    print(f"  Found {len(singles)} singles matches — enriching with stats + odds...")

    matches = []
    for i, event in enumerate(singles):
        match = normalize_event(event)
        fetch_stats = match["statusType"] in ("finished", "inprogress")
        fetch_h2h   = True  # always get H2H
        match = enrich(session, match, fetch_stats=fetch_stats, fetch_h2h=fetch_h2h)
        matches.append(match)
        if (i + 1) % 10 == 0:
            print(f"  Enriched {i+1}/{len(singles)}...")
        time.sleep(0.3)  # polite rate limiting

    # Save
    matches_dir = DATA / "matches"
    matches_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"-{mode}" if mode != "all" else ""
    fname = f"ss-{target_date}{suffix}.json"
    out = matches_dir / fname
    out.write_text(json.dumps(matches, indent=2, ensure_ascii=False), encoding="utf-8")

    # Summary
    by_status = {}
    for m in matches:
        s = m.get("statusType", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    has_stats = sum(1 for m in matches if m.get("stats"))
    has_odds  = sum(1 for m in matches if m.get("moneyline"))
    has_h2h   = sum(1 for m in matches if m.get("h2h"))

    print(f"\nSaved {len(matches)} matches → data/tennislive/matches/{fname}")
    for s, n in sorted(by_status.items()):
        print(f"  {s}: {n}")
    print(f"  with stats: {has_stats}  with odds: {has_odds}  with H2H: {has_h2h}")


if __name__ == "__main__":
    main()
