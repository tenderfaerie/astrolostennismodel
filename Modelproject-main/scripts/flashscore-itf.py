"""
Scrape ITF Men Singles matches from Flashscore using Playwright.
Outputs a JSON array of LiveMatch objects to stdout.
Usage: python3 scripts/flashscore-itf.py [live|upcoming|finished]
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone

CHROMIUM_PATH = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BASE_URL = "https://www.flashscore.com"
ITF_PATH = "/tennis/itf-men-singles/"
MODE = sys.argv[1] if len(sys.argv) > 1 else "live"

LEVEL_MAP = {
    "m15": "ITF 15K", "w15": "ITF 15K", "15k": "ITF 15K",
    "m25": "ITF 25K", "w25": "ITF 25K", "25k": "ITF 25K",
    "m40": "ITF 40K", "w40": "ITF 40K", "40k": "ITF 40K",
    "m60": "ITF 60K", "w60": "ITF 60K", "60k": "ITF 60K",
    "m80": "ITF 80K", "w80": "ITF 80K", "80k": "ITF 80K",
    "m100": "ITF 100K", "w100": "ITF 100K", "100k": "ITF 100K",
}

SURFACE_MAP = {
    "hard": "Hard", "clay": "Clay", "grass": "Grass",
    "carpet": "Carpet", "indoor": "Hard",
}

def infer_level(name: str) -> str:
    nl = name.lower()
    for k, v in LEVEL_MAP.items():
        if k in nl:
            return v
    return "ITF Men"

def infer_surface(name: str) -> str:
    nl = name.lower()
    for k, v in SURFACE_MAP.items():
        if k in nl:
            return v
    return "Unknown"

def parse_sets(score_text: str):
    """Parse '6-3 4-6 6-2' into period scores array."""
    parts = score_text.strip().split()
    result = []
    for i, part in enumerate(parts):
        m = re.match(r"(\d+)-(\d+)", part)
        if m:
            result.append({"period": f"S{i+1}", "home": int(m.group(1)), "away": int(m.group(2))})
    return result

def status_type(raw_status: str) -> str:
    s = raw_status.lower()
    if any(x in s for x in ["live", "in progress", "playing", "1st", "2nd", "3rd"]):
        return "inprogress"
    if any(x in s for x in ["finished", "ended", "retired", "walkover", "awarded"]):
        return "finished"
    return "notstarted"

async def scrape():
    from playwright.async_api import async_playwright

    matches = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=CHROMIUM_PATH,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--ignore-certificate-errors",
                      "--disable-blink-features=AutomationControlled"]
            )
            ctx = await browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            page = await ctx.new_page()

            # Block images/fonts to speed up
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", lambda r: r.abort())

            await page.goto(f"{BASE_URL}{ITF_PATH}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # Click the right tab based on mode
            if MODE == "upcoming":
                for selector in ["a[href*='scheduled']", "button:has-text('Scheduled')", "a:has-text('Scheduled')"]:
                    try:
                        await page.click(selector, timeout=3000)
                        await page.wait_for_timeout(2000)
                        break
                    except:
                        pass
            elif MODE == "finished":
                for selector in ["a[href*='results']", "button:has-text('Results')", "a:has-text('Results')"]:
                    try:
                        await page.click(selector, timeout=3000)
                        await page.wait_for_timeout(2000)
                        break
                    except:
                        pass
            else:
                # Live tab
                for selector in ["a:has-text('LIVE')", "button:has-text('LIVE')", ".filters__tab:has-text('LIVE')"]:
                    try:
                        await page.click(selector, timeout=3000)
                        await page.wait_for_timeout(2000)
                        break
                    except:
                        pass

            await page.wait_for_timeout(2000)

            # Scrape all match rows
            current_tournament = "ITF Men Singles"
            current_surface = "Unknown"

            elements = await page.query_selector_all("[class*='event__header'], [class*='event__match']")

            for el in elements:
                cls = await el.get_attribute("class") or ""

                if "event__header" in cls:
                    # Tournament header
                    try:
                        name_el = await el.query_selector("[class*='event__title']")
                        if name_el:
                            current_tournament = (await name_el.inner_text()).strip()
                            current_surface = infer_surface(current_tournament)
                    except:
                        pass
                    continue

                if "event__match" not in cls:
                    continue

                try:
                    # Player names
                    home_els = await el.query_selector_all("[class*='event__participant--home']")
                    away_els = await el.query_selector_all("[class*='event__participant--away']")
                    home_name = (await home_els[0].inner_text()).strip() if home_els else ""
                    away_name = (await away_els[0].inner_text()).strip() if away_els else ""
                    if not home_name or not away_name:
                        continue

                    # Score
                    score_el = await el.query_selector("[class*='event__score']")
                    score_text = (await score_el.inner_text()).strip() if score_el else ""
                    period_scores = parse_sets(score_text)
                    home_score = period_scores[-1]["home"] if period_scores else None
                    away_score = period_scores[-1]["away"] if period_scores else None

                    # Status
                    status_el = await el.query_selector("[class*='event__stage']")
                    raw_status = (await status_el.inner_text()).strip() if status_el else "Scheduled"
                    st = status_type(raw_status)

                    # Time
                    time_el = await el.query_selector("[class*='event__time']")
                    time_text = (await time_el.inner_text()).strip() if time_el else ""

                    # Match ID from element id attribute
                    el_id = await el.get_attribute("id") or ""
                    match_id = el_id.replace("g_2_", "fs-") if el_id else f"fs-{len(matches)}"

                    # Check for bet365 indicator
                    inner_html = await el.inner_html()
                    has_bet365 = "/549/" in inner_html or "bet365" in inner_html.lower()

                    matches.append({
                        "provider": "flashscore",
                        "providerId": match_id,
                        "tournament": current_tournament,
                        "category": infer_level(current_tournament),
                        "round": None,
                        "status": raw_status,
                        "statusType": st,
                        "surface": current_surface,
                        "startTimestamp": None,
                        "homePlayer": home_name,
                        "awayPlayer": away_name,
                        "homeScore": home_score,
                        "awayScore": away_score,
                        "periodScores": period_scores,
                        "server": None,
                        "hasBet365": has_bet365,
                        "fetchedAt": fetched_at,
                    })
                except Exception:
                    continue

            await browser.close()

    except Exception as e:
        sys.stderr.write(f"Flashscore scrape error: {e}\n")

    print(json.dumps(matches))

asyncio.run(scrape())
