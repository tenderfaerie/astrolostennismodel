import json
import sys
from datetime import datetime, timezone
from fractions import Fraction

import tls_client


BASE_URL = "https://api.sofascore.com/api/v1"


def create_session():
    session = tls_client.Session(
        client_identifier="chrome_120",
        random_tls_extension_order=True,
    )
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.sofascore.com/",
            "Origin": "https://www.sofascore.com",
            "Cache-Control": "max-age=0",
        }
    )
    return session


def get_json(session, path):
    response = session.get(f"{BASE_URL}{path}")
    if response.status_code not in (200, 201):
        raise RuntimeError(f"SofaScore returned {response.status_code} for {path}")
    return response.json()


def try_get_json(session, path):
    try:
        return get_json(session, path)
    except Exception:
        return None


def normalize_surface(event):
    surface = event.get("groundType") or event.get("tournament", {}).get("groundType")
    return surface or "Unknown"


def normalize_event(event):
    home_score = event.get("homeScore", {})
    away_score = event.get("awayScore", {})
    period_scores = []

    for index in range(1, 6):
        home = home_score.get(f"period{index}")
        away = away_score.get(f"period{index}")
        if home is not None or away is not None:
            period_scores.append(
                {
                    "period": f"S{index}",
                    "home": home,
                    "away": away,
                }
            )

    return {
        "provider": "sofascore",
        "providerId": str(event.get("id")),
        "tournament": (
            event.get("tournament", {}).get("uniqueTournament", {}).get("name")
            or event.get("tournament", {}).get("name")
            or "Unknown tournament"
        ),
        "category": event.get("tournament", {}).get("category", {}).get("name") or "Tennis",
        "round": event.get("roundInfo", {}).get("name"),
        "status": event.get("status", {}).get("description") or "Unknown",
        "statusType": event.get("status", {}).get("type"),
        "surface": normalize_surface(event),
        "startTimestamp": event.get("startTimestamp"),
        "homePlayer": event.get("homeTeam", {}).get("name") or "Player A",
        "awayPlayer": event.get("awayTeam", {}).get("name") or "Player B",
        "homeScore": home_score.get("current"),
        "awayScore": away_score.get("current"),
        "periodScores": period_scores,
        "server": "home" if event.get("firstToServe") == 1 else "away" if event.get("firstToServe") == 2 else None,
        "detailUrl": f"https://www.sofascore.com/event/{event.get('id')}",
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
    }


def fractional_to_decimal(value):
    if not value or "/" not in value:
        return None
    fraction = Fraction(value)
    return round(float(fraction) + 1, 3)


def decimal_to_american(decimal):
    if not decimal:
        return None
    if decimal >= 2:
        return round((decimal - 1) * 100)
    return round(-100 / (decimal - 1))


def normalize_moneyline(raw):
    markets = raw.get("markets", []) if raw else []
    market = next(
        (
            item
            for item in markets
            if item.get("marketId") == 1
            or item.get("marketName") in ("Full time", "Winner")
            or item.get("marketGroup") == "Home/Away"
        ),
        None,
    )
    if not market:
        featured = raw.get("featured", {}).get("default") if raw else None
        market = featured if featured and isinstance(featured, dict) else None
    if not market:
        return None

    home = None
    away = None
    for choice in market.get("choices", []):
        name = str(choice.get("name", "")).lower()
        fractional = choice.get("fractionalValue") or choice.get("initialFractionalValue")
        decimal = fractional_to_decimal(fractional)
        normalized = {
            "fractional": fractional,
            "decimal": decimal,
            "american": decimal_to_american(decimal),
        }
        if name in ("1", "home") or choice.get("position") == 1:
            home = normalized
        elif name in ("2", "away") or choice.get("position") == 2:
            away = normalized

    return {
        "marketName": market.get("marketName") or "Moneyline",
        "suspended": bool(market.get("suspended")),
        "home": home,
        "away": away,
    }


def normalize_stats(raw):
    rows = []
    for block in raw.get("statistics", []) if raw else []:
        if block.get("period") not in ("ALL", None):
            continue
        for group in block.get("groups", []):
            group_name = group.get("groupName") or "Stats"
            for item in group.get("statisticsItems", []):
                rows.append(
                    {
                        "group": group_name,
                        "name": item.get("name"),
                        "home": item.get("home"),
                        "away": item.get("away"),
                        "key": item.get("key"),
                    }
                )
    return rows


def normalize_point_by_point(raw):
    sets = raw.get("pointByPoint", []) if raw else []
    if not sets:
        return None

    latest_set = sets[0]
    games = latest_set.get("games", [])
    if not games:
        return None

    latest_game = games[0]
    score = latest_game.get("score", {})
    points = []

    for point in latest_game.get("points", []):
        home_type = point.get("homePointType")
        away_type = point.get("awayPointType")
        winner = None
        if home_type == 1 or away_type == 5:
            winner = "home"
        elif away_type == 1 or home_type == 5:
            winner = "away"

        points.append(
            {
                "homePoint": str(point.get("homePoint", "")),
                "awayPoint": str(point.get("awayPoint", "")),
                "winner": winner,
            }
        )

    serving = score.get("serving")
    scoring = score.get("scoring")
    return {
        "set": latest_set.get("set"),
        "game": latest_game.get("game"),
        "homeGames": score.get("homeScore"),
        "awayGames": score.get("awayScore"),
        "serving": "home" if serving == 1 else "away" if serving == 2 else None,
        "scoring": "home" if scoring == 1 else "away" if scoring == 2 else None,
        "points": points,
    }


def enrich_event(session, match):
    event_id = match["providerId"]
    stats = normalize_stats(try_get_json(session, f"/event/{event_id}/statistics"))
    point_by_point = normalize_point_by_point(try_get_json(session, f"/event/{event_id}/point-by-point"))
    odds = normalize_moneyline(
        try_get_json(session, f"/event/{event_id}/odds/1/all")
        or try_get_json(session, f"/event/{event_id}/odds/1/featured")
        or {}
    )
    if stats:
        match["stats"] = stats
    if point_by_point:
        match["currentGame"] = point_by_point
        match["server"] = point_by_point.get("serving")
        if point_by_point.get("points"):
            last = point_by_point["points"][-1]
            match["lastPoint"] = f"{last.get('homePoint')} - {last.get('awayPoint')}"
    if odds:
        match["moneyline"] = odds
    return match


def is_doubles(event):
    tournament = event.get("tournament", {}).get("name") or ""
    home = event.get("homeTeam", {}).get("name") or ""
    away = event.get("awayTeam", {}).get("name") or ""
    return "Doubles" in tournament or " / " in home or " / " in away


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    session = create_session()

    live = get_json(session, "/sport/tennis/events/live").get("events", [])
    if not live:
        live = get_json(session, f"/sport/tennis/scheduled-events/{date}").get("events", [])

    singles = [event for event in live if not is_doubles(event)]
    matches = [normalize_event(event) for event in singles]
    enriched = [enrich_event(session, match) if index < 8 else match for index, match in enumerate(matches)]
    print(json.dumps(enriched))


if __name__ == "__main__":
    main()
