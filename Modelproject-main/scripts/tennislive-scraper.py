"""
tennislive.net scraper — live scores + ATP/WTA player stats/profiles
Usage:
  python3 tennislive-scraper.py live
  python3 tennislive-scraper.py upcoming
  python3 tennislive-scraper.py finished
  python3 tennislive-scraper.py player_atp <slug>     e.g. juan-manuel-cerundolo
  python3 tennislive-scraper.py player_wta <slug>     e.g. aryna-sabalenka
  python3 tennislive-scraper.py rankings_atp
  python3 tennislive-scraper.py rankings_wta

Player profile URL: https://www.tennislive.net/atp/{slug}/
Profile page contains:
  - Bio: name, country, birthdate, ATP/WTA ranking, career W/L, prize money
  - Year-by-year surface breakdown table: Hard | Clay | Indoor hard | Carpet | Grass | Acrylic
    Format in each cell: wins/losses (e.g. "19/10")
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BASE = "https://www.tennislive.net"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

SURFACE_KEYWORDS = {
    "clay": "Clay", "red clay": "Clay",
    "grass": "Grass",
    "hard": "Hard",
    "i. hard": "Indoor", "indoor hard": "Indoor", "indoor": "Indoor",
    "carpet": "Carpet",
    "acrylic": "Hard",
}

def infer_surface(text: str) -> str:
    t = text.lower()
    for k, v in SURFACE_KEYWORDS.items():
        if k in t:
            return v
    return "Unknown"

def infer_level(name: str) -> str:
    t = name.lower()
    if any(x in t for x in ("roland garros","wimbledon","us open","australian open","grand slam")):
        return "Grand Slam"
    if "challenger" in t: return "Challenger"
    if "futures" in t or re.search(r'\bm\d{2}\b|\bw\d{2}\b', t): return "Futures"
    if "itf" in t: return "ITF"
    if "wta" in t: return "WTA"
    return "ATP"

def parse_wl(cell: str):
    """Parse '19/10' -> (19, 10), or None."""
    m = re.match(r"(\d+)\s*/\s*(\d+)", cell.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return None

def player_slug(name: str) -> str:
    """Convert 'Juan Manuel Cerundolo' -> 'juan-manuel-cerundolo'"""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")

async def make_page(playwright):
    browser = await playwright.chromium.launch(
        executable_path=CHROME,
        args=["--no-sandbox", "--ignore-certificate-errors",
              "--disable-blink-features=AutomationControlled"]
    )
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        locale="en-US"
    )
    return browser, await ctx.new_page()

# ── Player profile ────────────────────────────────────────────────────────────
async def scrape_player(tour: str, slug: str) -> dict:
    url = f"{BASE}/{tour}/{slug}/"
    async with async_playwright() as p:
        browser, page = await make_page(p)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("table", timeout=8000)
        except PlaywrightTimeout:
            pass

        result = {"slug": slug, "tour": tour.upper(), "url": url, "surfaces": {}, "byYear": {}}

        # ── Bio block ──────────────────────────────────────────────────────
        bio_el = await page.query_selector("div.player-info, div[class*='player'], td.player-bio, div.bio")
        if not bio_el:
            # Fall back: parse raw text from the bio area
            bio_el = await page.query_selector("div.leftcol, div#player, div.player_info")
        if bio_el:
            bio_text = await bio_el.inner_text()
            for line in bio_text.splitlines():
                line = line.strip()
                if "Name:" in line:
                    result["name"] = line.split("Name:")[-1].strip()
                elif "Country:" in line:
                    result["country"] = line.split("Country:")[-1].strip()
                elif "Birthdate:" in line:
                    result["birthdate"] = line.split("Birthdate:")[-1].strip()
                elif "ranking:" in line.lower():
                    m = re.search(r"(\d+)", line)
                    if m:
                        result["ranking"] = int(m.group(1))
                elif "Points:" in line:
                    m = re.search(r"[\d,]+", line)
                    if m:
                        result["points"] = int(m.group(0).replace(",", ""))
                elif "Win:" in line:
                    m = re.search(r"(\d+)", line)
                    if m:
                        result["careerWins"] = int(m.group(1))
                elif re.match(r"%:", line) or "%" in line and "Win" in line:
                    m = re.search(r"([\d.]+)\s*%", line)
                    if m:
                        result["careerWinPct"] = float(m.group(1)) / 100

        # ── Stats table: year × surface ───────────────────────────────────
        # Structure: year | summary | Hard | Clay | I.hard | Carpet | Grass | Acrylic
        tables = await page.query_selector_all("table")
        for table in tables:
            headers_els = await table.query_selector_all("thead tr th, tr:first-child th, tr:first-child td")
            headers = [((await h.inner_text()).strip().lower()) for h in headers_els]
            if "clay" not in headers and "hard" not in headers:
                continue  # not the stats table

            # Map column index -> surface name
            col_surface: dict[int, str] = {}
            for i, h in enumerate(headers):
                if h in SURFACE_KEYWORDS:
                    col_surface[i] = SURFACE_KEYWORDS[h]
                elif h == "summary":
                    col_surface[i] = "All"

            rows = await table.query_selector_all("tbody tr, tr")
            for row in rows:
                cells = await row.query_selector_all("td, th")
                texts = [(await c.inner_text()).strip() for c in cells]
                if not texts:
                    continue
                # First column is year or "TOTAL" or "perc. %"
                year_raw = texts[0]
                if year_raw.upper() in ("TOTAL", "PERC. %", "YEAR", ""):
                    continue
                try:
                    year = int(year_raw)
                except ValueError:
                    continue

                year_data: dict[str, dict] = {}
                for col_idx, surface in col_surface.items():
                    if col_idx < len(texts):
                        wl = parse_wl(texts[col_idx])
                        if wl:
                            w, l = wl
                            total = w + l
                            year_data[surface] = {
                                "wins": w, "losses": l, "matches": total,
                                "winPct": round(w / total, 4) if total else 0
                            }
                if year_data:
                    result["byYear"][str(year)] = year_data

            # Aggregate surfaces across all years
            for year_data in result["byYear"].values():
                for surface, stats in year_data.items():
                    if surface not in result["surfaces"]:
                        result["surfaces"][surface] = {"wins": 0, "losses": 0, "matches": 0}
                    result["surfaces"][surface]["wins"]   += stats["wins"]
                    result["surfaces"][surface]["losses"] += stats["losses"]
                    result["surfaces"][surface]["matches"] += stats["matches"]

            for surface, stats in result["surfaces"].items():
                t = stats["matches"]
                stats["winPct"] = round(stats["wins"] / t, 4) if t else 0

            break  # only parse first matching table

        await browser.close()
        return result

# ── Rankings ──────────────────────────────────────────────────────────────────
async def scrape_rankings(tour: str) -> list[dict]:
    path = "atp" if "atp" in tour else "wta"
    url = f"{BASE}/{path}/"
    async with async_playwright() as p:
        browser, page = await make_page(p)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("table", timeout=8000)
        except PlaywrightTimeout:
            pass

        players = []
        rows = await page.query_selector_all("table tbody tr, table tr")
        for row in rows:
            cells = await row.query_selector_all("td")
            texts = [(await c.inner_text()).strip() for c in cells]
            if len(texts) < 3:
                continue
            try:
                rank = int(texts[0])
            except ValueError:
                continue
            # Try to get player link slug
            link_el = await row.query_selector("a")
            slug = ""
            if link_el:
                href = await link_el.get_attribute("href") or ""
                slug = href.strip("/").split("/")[-1]
            players.append({
                "rank": rank,
                "name": texts[1] if len(texts) > 1 else "",
                "country": texts[2] if len(texts) > 2 else "",
                "points": texts[3] if len(texts) > 3 else "",
                "slug": slug,
                "tour": path.upper()
            })

        await browser.close()
        return players

# ── Live / Upcoming / Finished scores ────────────────────────────────────────
TAB_TEXT = {"live": "live tennis", "upcoming": "scheduled", "finished": "finished"}

async def scrape_scores(mode: str) -> list[dict]:
    async with async_playwright() as p:
        browser, page = await make_page(p)
        await page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("table", timeout=8000)
        except PlaywrightTimeout:
            pass

        # Click the right tab
        target_tab = TAB_TEXT.get(mode, "live tennis")
        tab_links = await page.query_selector_all("a, li.tab, div.tab")
        for el in tab_links:
            txt = (await el.inner_text()).strip().lower()
            if target_tab in txt:
                await el.click()
                await asyncio.sleep(1)
                break

        matches = []
        fetched_at = datetime.now(timezone.utc).isoformat()
        current_tournament = "Unknown"
        current_surface = "Unknown"

        rows = await page.query_selector_all("table tr")
        for row in rows:
            cells = await row.query_selector_all("td, th")
            texts = [(await c.inner_text()).strip() for c in cells]
            if not texts:
                continue

            # Tournament header row (few cells, contains tournament name)
            if len(cells) <= 3 and texts[0] and not texts[0].isdigit():
                full = " ".join(t for t in texts if t)
                if len(full) < 100:
                    current_tournament = full
                    current_surface = infer_surface(full)
                continue

            if len(cells) < 4:
                continue

            # Extract time, player names, scores
            time_str = texts[0] if re.match(r"\d{1,2}:\d{2}", texts[0]) else None
            player1 = texts[1] if len(texts) > 1 else ""
            player2 = ""

            # Find player 2 — look for non-numeric cell after scores
            numeric_idx = []
            for i, t in enumerate(texts):
                clean = re.sub(r"[^0-9]", "", t)
                if clean and len(t) <= 4:
                    numeric_idx.append(i)

            # Player names: first non-time text, and next non-numeric after scores
            name_cells = [t for t in texts[1:] if t and not re.match(r"^\d{0,2}$", t)
                          and not re.match(r"\d{1,2}:\d{2}", t)]
            if len(name_cells) >= 2:
                player1 = name_cells[0]
                player2 = name_cells[1]

            # Parse set scores — pairs of numbers in range 0-7
            nums = [int(t) for t in texts if re.match(r"^\d$", t) and int(t) <= 7]
            period_scores = []
            mid = len(nums) // 2
            for i in range(min(mid, 5)):
                period_scores.append({"period": f"S{i+1}", "home": nums[i], "away": nums[mid+i]})

            home_sets = nums[0] if nums else None
            away_sets = nums[mid] if mid > 0 and len(nums) > mid else None

            if not player1 or not player2 or player1 == player2:
                continue

            status_type = "inprogress" if mode == "live" else (
                "notstarted" if mode == "upcoming" else "finished")

            matches.append({
                "provider": "tennislive",
                "providerId": f"tl-{len(matches)+1}",
                "tournament": current_tournament,
                "category": infer_level(current_tournament),
                "surface": current_surface,
                "status": "Live" if mode == "live" else ("Scheduled" if mode == "upcoming" else "Finished"),
                "statusType": status_type,
                "startTime": time_str,
                "homePlayer": player1,
                "awayPlayer": player2,
                "homeScore": home_sets,
                "awayScore": away_sets,
                "periodScores": period_scores,
                "fetchedAt": fetched_at
            })

        await browser.close()
        return matches

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "live"
    try:
        if mode in ("live", "upcoming", "finished"):
            result = await scrape_scores(mode)
        elif mode in ("player_atp", "player_wta"):
            tour = "atp" if mode == "player_atp" else "wta"
            slug = sys.argv[2] if len(sys.argv) > 2 else ""
            if not slug:
                raise ValueError("provide player slug as second arg, e.g. juan-manuel-cerundolo")
            result = await scrape_player(tour, slug)
        elif mode in ("rankings_atp", "rankings_wta"):
            result = await scrape_rankings(mode)
        else:
            result = []
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        sys.stderr.write(f"tennislive-scraper error ({mode}): {e}\n")
        print(json.dumps([]))

asyncio.run(main())
