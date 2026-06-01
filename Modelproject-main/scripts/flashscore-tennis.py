"""
Flashscore tennis scraper — ATP, WTA, Grand Slams, Challengers, ITF
====================================================================
Scrapes any tennis section on flashscore.com using Playwright.

Usage:
  python3 flashscore-tennis.py <section> <mode>

Sections:
  atp          ATP tour matches
  wta          WTA tour matches
  gs           Grand Slam matches (all active GS)
  challenger   ATP Challenger + ITF Men
  itf-women    ITF Women Singles
  all          ATP + WTA + GS

Modes:
  live         Currently in progress (default)
  finished     Results tab (today's completed)
  upcoming     Scheduled matches

Examples:
  python3 flashscore-tennis.py atp finished
  python3 flashscore-tennis.py wta finished
  python3 flashscore-tennis.py gs finished
  python3 flashscore-tennis.py all live

Output: data/tennislive/matches/fs-<section>-<mode>[-YYYY-MM-DD].json
"""

import asyncio
import json
import re
import sys
from datetime import datetime, date, timezone
from pathlib import Path

# ── URL map ───────────────────────────────────────────────────────────────────
BASE_URL = "https://www.flashscore.com"

SECTION_PATHS = {
    "atp":       ["/tennis/atp-singles/"],
    "wta":       ["/tennis/wta-singles/"],
    "gs":        ["/tennis/atp-singles/", "/tennis/wta-singles/"],  # GS appear in both
    "challenger":["/tennis/atp-challenger-singles/"],
    "itf-men":   ["/tennis/itf-men-singles/"],
    "itf-women": ["/tennis/itf-women-singles/"],
    "all":       ["/tennis/atp-singles/", "/tennis/wta-singles/"],
}

GS_NAMES = {"roland garros", "french open", "wimbledon", "us open", "australian open"}

SURFACE_MAP = {
    "clay": "Clay", "hard": "Hard", "grass": "Grass",
    "carpet": "Carpet", "indoor": "Hard",
}

DATA = Path(__file__).parent.parent / "data" / "tennislive"

def infer_surface(name: str) -> str:
    nl = name.lower()
    for k, v in SURFACE_MAP.items():
        if k in nl:
            return v
    if any(gs in nl for gs in ("roland garros", "french open")):
        return "Clay"
    if "wimbledon" in nl:
        return "Grass"
    if "australian open" in nl or "us open" in nl:
        return "Hard"
    return "Unknown"

def infer_category(name: str) -> str:
    nl = name.lower()
    if any(gs in nl for gs in GS_NAMES):
        return "Grand Slam"
    if "challenger" in nl:
        return "Challenger"
    if re.search(r"\bw\d{2}\b|\bitf women\b", nl):
        return "ITF Women"
    if re.search(r"\bm\d{2}\b|\bitf men\b", nl):
        return "ITF Men"
    if "wta" in nl or "women" in nl:
        return "WTA"
    return "ATP"

def parse_sets(score_text: str) -> list:
    parts = score_text.strip().split()
    result = []
    for i, part in enumerate(parts):
        m = re.match(r"(\d+)-(\d+)", part)
        if m:
            result.append({"period": f"S{i+1}",
                           "home": int(m.group(1)),
                           "away": int(m.group(2))})
    return result

def status_label(raw: str) -> tuple[str, str]:
    s = raw.lower()
    if any(x in s for x in ["finished", "ended", "retired", "walkover", "awarded", "w.o"]):
        return "Finished", "finished"
    if any(x in s for x in ["1st", "2nd", "3rd", "4th", "5th", "live", "playing", "break"]):
        return "Live", "inprogress"
    return "Scheduled", "notstarted"

async def scrape_path(page, path: str, mode: str, section: str, dump: bool = False) -> list:
    """Navigate to one flashscore path and scrape all match rows."""
    url = f"{BASE_URL}{path}"
    print(f"  → {url} [{mode}]")

    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2500)

    # Cookie banner dismiss
    for sel in ["button#onetrust-accept-btn-handler", "button:has-text('Accept')",
                 "button:has-text('I Accept')", "[id*='accept']"]:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1500):
                await btn.click()
                await page.wait_for_timeout(500)
                break
        except Exception:
            pass

    # Tab switching
    if mode == "finished":
        for sel in ["a:has-text('Results')", "a[href*='results']",
                     "button:has-text('Results')", ".filters__tab:has-text('Results')"]:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    await page.wait_for_timeout(2500)
                    break
            except Exception:
                pass
    elif mode == "upcoming":
        for sel in ["a:has-text('Scheduled')", "a[href*='scheduled']",
                     "button:has-text('Scheduled')"]:
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=2000):
                    await loc.click()
                    await page.wait_for_timeout(2500)
                    break
            except Exception:
                pass

    # Expand all "Show more" buttons
    for _ in range(5):
        try:
            more = page.locator("a.event__more, button:has-text('Show more matches')").first
            if await more.is_visible(timeout=1500):
                await more.click()
                await page.wait_for_timeout(1000)
            else:
                break
        except Exception:
            break

    if dump:
        slug = path.strip("/").replace("/", "-")
        dump_path = DATA / "matches" / f"debug-fs-{slug}-{mode}.html"
        dump_path.parent.mkdir(parents=True, exist_ok=True)
        dump_path.write_text(await page.content(), encoding="utf-8")
        print(f"    [DUMP] saved → {dump_path}")

    # Count all elements to diagnose selector issues
    all_els = await page.query_selector_all("[class*='event__']")
    print(f"    [DEBUG] event__ elements on page: {len(all_els)}")

    fetched_at = datetime.now(timezone.utc).isoformat()
    matches = []
    current_tournament = "Unknown"
    current_surface = "Unknown"
    current_category = "ATP"

    elements = await page.query_selector_all(
        "[class*='event__header'], [class*='event__match']"
    )

    for el in elements:
        cls = await el.get_attribute("class") or ""

        if "event__header" in cls:
            try:
                name_el = await el.query_selector(
                    "[class*='event__title--name'], [class*='event__title']"
                )
                if name_el:
                    current_tournament = (await name_el.inner_text()).strip()
                    current_surface  = infer_surface(current_tournament)
                    current_category = infer_category(current_tournament)
            except Exception:
                pass
            continue

        if "event__match" not in cls:
            continue

        # Filter for Grand Slam section
        if section == "gs" and current_category != "Grand Slam":
            continue

        try:
            home_els = await el.query_selector_all("[class*='event__participant--home']")
            away_els = await el.query_selector_all("[class*='event__participant--away']")
            home_name = (await home_els[0].inner_text()).strip() if home_els else ""
            away_name = (await away_els[0].inner_text()).strip() if away_els else ""
            if not home_name or not away_name:
                continue

            # Score — try period scores first, fall back to total
            score_text = ""
            score_els = await el.query_selector_all("[class*='event__score']")
            if score_els:
                parts = []
                for se in score_els:
                    t = (await se.inner_text()).strip()
                    if t:
                        parts.append(t)
                score_text = " ".join(parts)

            period_scores = parse_sets(score_text)

            # Sets won
            home_sets = sum(1 for ps in period_scores if ps["home"] > ps["away"])
            away_sets = sum(1 for ps in period_scores if ps["away"] > ps["home"])

            # Status
            status_el = await el.query_selector(
                "[class*='event__stage'], [class*='event__status']"
            )
            raw_status = (await status_el.inner_text()).strip() if status_el else "Scheduled"
            label, stype = status_label(raw_status)

            # Time
            time_el = await el.query_selector("[class*='event__time']")
            time_text = (await time_el.inner_text()).strip() if time_el else ""

            # Round
            round_el = await el.query_selector("[class*='event__round']")
            round_text = (await round_el.inner_text()).strip() if round_el else ""

            el_id = await el.get_attribute("id") or ""
            match_id = el_id.replace("g_2_", "fs-") if el_id else f"fs-{len(matches)}"

            matches.append({
                "provider": "flashscore",
                "providerId": match_id,
                "tournament": current_tournament,
                "category": current_category,
                "surface": current_surface,
                "round": round_text or None,
                "status": label,
                "statusType": stype,
                "startTime": time_text,
                "homePlayer": home_name,
                "awayPlayer": away_name,
                "homeSetsWon": home_sets,
                "awaySetsWon": away_sets,
                "homeScore": period_scores[-1]["home"] if period_scores else None,
                "awayScore": period_scores[-1]["away"] if period_scores else None,
                "periodScores": period_scores,
                "fetchedAt": fetched_at,
            })
        except Exception:
            continue

    print(f"    Found {len(matches)} matches")
    return matches


async def main():
    section = sys.argv[1] if len(sys.argv) > 1 else "atp"
    mode    = sys.argv[2] if len(sys.argv) > 2 else "live"
    dump    = "--dump" in sys.argv

    paths = SECTION_PATHS.get(section, SECTION_PATHS["atp"])

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        # Block images/fonts for speed
        await ctx.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
            lambda r: r.abort()
        )
        page = await ctx.new_page()

        all_matches = []
        for path in paths:
            matches = await scrape_path(page, path, mode, section, dump=dump)
            all_matches.extend(matches)

        await browser.close()

    # Deduplicate by providerId
    seen = set()
    deduped = []
    for m in all_matches:
        if m["providerId"] not in seen:
            seen.add(m["providerId"])
            deduped.append(m)

    # Save
    DATA.mkdir(parents=True, exist_ok=True)
    matches_dir = DATA / "matches"
    matches_dir.mkdir(exist_ok=True)

    today = date.today().isoformat()
    fname = (f"fs-{section}-{mode}.json" if mode in ("live", "upcoming")
             else f"fs-{section}-finished-{today}.json")
    out = matches_dir / fname

    out.write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")

    cats = {}
    for m in deduped:
        c = m.get("category", "Unknown")
        cats[c] = cats.get(c, 0) + 1

    print(f"\nSaved {len(deduped)} matches → data/tennislive/matches/{fname}")
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")


asyncio.run(main())
