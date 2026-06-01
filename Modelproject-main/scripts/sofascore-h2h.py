"""
Sofascore H2H scraper — uses Playwright real browser to bypass auth
====================================================================
Fetches head-to-head records for specific match event IDs.

Usage:
  python3 sofascore-h2h.py <event_id1> <event_id2> ...
  python3 sofascore-h2h.py --file <json_file>   # reads providerId from matches JSON

Output: data/tennislive/h2h/h2h-<date>.json

Example:
  python3 sofascore-h2h.py 16198484 16198515 16198517 16198519 16198473 16198476 16198577 16198570 16198571 16198546 16198539
"""

import asyncio
import json
import sys
import re
from datetime import date, datetime, timezone
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "tennislive"

# RG June 1 main draw event IDs (hardcoded as fallback)
RG_JUNE1_IDS = [
    "16198484",  # Cobolli vs Svajda
    "16198515",  # Cerundolo vs Berrettini
    "16198517",  # Tiafoe vs Arnaldi
    "16198519",  # FAA vs Tabilo
    "16198473",  # Mensik vs Fonseca
    "16198476",  # Jodar vs Zverev
    "16198577",  # Potapova vs Kalinskaya
    "16198570",  # Keys vs Shnaider
    "16198571",  # Sabalenka vs Osaka
    "16198546",  # Svitolina vs Kostyuk
    "16198539",  # Andreeva vs Cirstea
]


async def fetch_h2h(page, event_id: str) -> dict:
    """Navigate to match page and intercept the H2H API response."""
    import re as _re
    match_url = f"https://www.sofascore.com/event/{event_id}#id:{event_id}"

    try:
        async with page.expect_response(
            lambda r: f"/event/{event_id}/h2h" in r.url and r.status == 200,
            timeout=15000
        ) as resp_info:
            await page.goto(match_url, wait_until="domcontentloaded", timeout=20000)

        resp = await resp_info.value
        return await resp.json()

    except Exception:
        # H2H didn't fire on load — try clicking the H2H tab
        for sel in ["a:has-text('H2H')", "button:has-text('H2H')",
                    "[data-testid='h2h']", "li:has-text('H2H')"]:
            try:
                async with page.expect_response(
                    lambda r: f"/event/{event_id}/h2h" in r.url and r.status == 200,
                    timeout=6000
                ) as resp_info:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=1000):
                        await loc.click()
                resp = await resp_info.value
                return await resp.json()
            except Exception:
                continue

    return {}


def parse_h2h(raw: dict, event_id: str) -> dict:
    events = raw.get("events", [])
    if not events:
        return {"eventId": event_id, "totalMatches": 0}

    home_wins = sum(1 for e in events if e.get("winnerCode") == 1)
    away_wins = sum(1 for e in events if e.get("winnerCode") == 2)

    def is_clay(e):
        g = (e.get("groundType") or
             e.get("tournament", {}).get("groundType") or "").lower()
        return "clay" in g

    clay = [e for e in events if is_clay(e)]
    clay_home = sum(1 for e in clay if e.get("winnerCode") == 1)
    clay_away = sum(1 for e in clay if e.get("winnerCode") == 2)

    recent = []
    for e in events[:6]:
        ts = e.get("startTimestamp")
        year = datetime.fromtimestamp(ts).strftime("%Y") if ts else "?"
        surf = (e.get("groundType") or
                e.get("tournament", {}).get("groundType") or "Unknown")
        tourn = (e.get("tournament", {}).get("uniqueTournament", {}).get("name")
                 or e.get("tournament", {}).get("name") or "")
        winner_code = e.get("winnerCode")
        home_name = e.get("homeTeam", {}).get("name") or "?"
        away_name = e.get("awayTeam", {}).get("name") or "?"
        winner = home_name if winner_code == 1 else away_name if winner_code == 2 else "?"
        hs = e.get("homeScore", {}).get("current", "?")
        as_ = e.get("awayScore", {}).get("current", "?")
        recent.append({
            "year": year, "surface": surf, "tournament": tourn,
            "winner": winner, "score": f"{hs}-{as_}",
            "homePlayer": home_name, "awayPlayer": away_name,
        })

    # Derive player names from most recent match
    home_player = events[0].get("homeTeam", {}).get("name") or "Home"
    away_player = events[0].get("awayTeam", {}).get("name") or "Away"

    return {
        "eventId": event_id,
        "homePlayer": home_player,
        "awayPlayer": away_player,
        "totalMatches": len(events),
        "homeWins": home_wins,
        "awayWins": away_wins,
        "clayMatches": len(clay),
        "clayHomeWins": clay_home,
        "clayAwayWins": clay_away,
        "recent": recent,
    }


async def main():
    # Parse args
    args = sys.argv[1:]

    event_ids = []
    if "--file" in args:
        idx = args.index("--file")
        fpath = Path(args[idx + 1])
        matches = json.loads(fpath.read_text(encoding="utf-8"))
        # Filter to Roland Garros upcoming only
        event_ids = [
            m["providerId"] for m in matches
            if (any(x in (m.get("tournament") or "").lower()
                    for x in ["roland", "french open"])
                and m.get("statusType") == "notstarted"
                and m.get("moneyline"))  # main draw only (has odds)
        ]
        print(f"Loaded {len(event_ids)} RG upcoming match IDs from {fpath.name}")
    elif args:
        event_ids = args
    else:
        event_ids = RG_JUNE1_IDS
        print(f"Using hardcoded RG June 1 event IDs ({len(event_ids)} matches)")

    from playwright.async_api import async_playwright
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        await ctx.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico,mp4}",
                        lambda r: r.abort())
        page = await ctx.new_page()

        # Visit homepage first to get cookies
        print("Warming up session...")
        await page.goto("https://www.sofascore.com/tennis/",
                       wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)

        # Dismiss cookie banner
        for sel in ["button#onetrust-accept-btn-handler", "button:has-text('Accept')",
                    "button:has-text('I Accept')"]:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=1500):
                    await btn.click()
                    await page.wait_for_timeout(500)
                    break
            except Exception:
                pass

        for i, eid in enumerate(event_ids):
            print(f"  [{i+1}/{len(event_ids)}] event {eid}...", end=" ", flush=True)
            raw = await fetch_h2h(page, eid)
            if raw.get("error"):
                print(f"ERROR {raw['error']}")
            parsed = parse_h2h(raw, eid)
            results.append(parsed)
            home = parsed.get("homePlayer", "?")
            away = parsed.get("awayPlayer", "?")
            total = parsed.get("totalMatches", 0)
            hw = parsed.get("homeWins", 0)
            aw = parsed.get("awayWins", 0)
            ch = parsed.get("clayHomeWins", 0)
            ca = parsed.get("clayAwayWins", 0)
            print(f"    {home} vs {away}: overall {hw}-{aw} ({total} matches) | clay {ch}-{ca}")
            await asyncio.sleep(1)

        await browser.close()

    # Save
    out_dir = DATA / "h2h"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"h2h-{date.today().isoformat()}.json"
    out = out_dir / fname
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {len(results)} H2H records → data/tennislive/h2h/{fname}")


asyncio.run(main())
