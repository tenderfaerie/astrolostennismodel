"""
tennislive.net scraper — live scores + ATP/WTA player profiles
Uses tls_client for Cloudflare bypass on player profiles (server-rendered HTML).
Uses Playwright for live/scheduled/finished scores (AJAX tab switching).

Usage:
  python3 tennislive-scraper.py live
  python3 tennislive-scraper.py upcoming
  python3 tennislive-scraper.py finished
  python3 tennislive-scraper.py player_atp <slug>   e.g. juan-manuel-cerundolo
  python3 tennislive-scraper.py player_wta <slug>   e.g. aryna-sabalenka
  python3 tennislive-scraper.py rankings_atp
  python3 tennislive-scraper.py rankings_wta

Player profile URL: https://www.tennislive.net/atp/{slug}/
Stats table columns: year | summary | Hard | Clay | I. hard | Carpet | Grass | Acrylic
Each cell <a title="surface: Clay, year: 2026, win: 19, loss: 10, %: 65.52 %"> gives full data.
Bio block: div.player_stats with <b> tags for each value.
"""
import asyncio
import json
import re
import sys
from datetime import datetime, timezone

BASE = "https://www.tennislive.net"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tennislive.net/",
}

# Column header → surface key in our output
SURFACE_COL_MAP = {
    "hard":     "Hard",
    "clay":     "Clay",
    "i. hard":  "Indoor",
    "indoor":   "Indoor",
    "carpet":   "Carpet",
    "grass":    "Grass",
    "acrylic":  "Hard",   # acrylic is a hard court variant
    "summary":  "All",
}

def infer_surface(text: str) -> str:
    t = text.lower()
    if "clay" in t: return "Clay"
    if "grass" in t: return "Grass"
    if "indoor" in t or "i. hard" in t: return "Indoor"
    if "hard" in t or "acrylic" in t: return "Hard"
    if "carpet" in t: return "Carpet"
    return "Unknown"

def infer_level(name: str) -> str:
    t = name.lower()
    if any(x in t for x in ("roland garros","wimbledon","us open","australian open","french open")):
        return "Grand Slam"
    if "challenger" in t: return "Challenger"
    if re.search(r'\bm\d{2}\b|\bw\d{2}\b', t): return "Futures"
    if "itf" in t: return "ITF"
    if "wta" in t: return "WTA"
    return "ATP"

def player_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")

def fetch_html(url: str) -> str:
    """Fetch using tls_client to bypass Cloudflare."""
    try:
        import tls_client
        session = tls_client.Session(
            client_identifier="chrome_124",
            random_tls_extension_order=True
        )
        resp = session.get(url, headers=HEADERS, timeout_seconds=20)
        return resp.text
    except ImportError:
        import urllib.request
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="ignore")

# ── Player profile (server-rendered HTML) ────────────────────────────────────
def parse_player_profile(html: str, tour: str, slug: str) -> dict:
    from html.parser import HTMLParser

    result: dict = {
        "slug": slug,
        "tour": tour.upper(),
        "url": f"{BASE}/{tour}/{slug}/",
        "surfaces": {},
        "byYear": {},
    }

    # ── Bio: use regex on the player_stats div ────────────────────────────
    bio_match = re.search(r'class="player_stats">(.*?)</div>', html, re.DOTALL)
    if bio_match:
        bio = bio_match.group(1)
        def extract_b(label: str) -> str:
            # Match <b> content, stripping any inner tags (e.g. <a>name</a>)
            m = re.search(re.escape(label) + r'[:\s]*<b[^>]*>(.*?)</b>', bio, re.IGNORECASE | re.DOTALL)
            return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ""
        result["name"]    = extract_b("Name")
        result["country"] = extract_b("Country")
        result["birthdate"] = extract_b("Birthdate")
        rank_b = extract_b("ATP ranking") or extract_b("WTA ranking") or extract_b("ranking")
        try: result["ranking"] = int(re.sub(r"[^\d]", "", rank_b))
        except: pass
        pts_b = extract_b("Points")
        try: result["points"] = int(re.sub(r"[^\d]", "", pts_b))
        except: pass
        wins_b = extract_b("Win")
        try: result["careerWins"] = int(re.sub(r"[^\d]", "", wins_b))
        except: pass
        total_b = extract_b("Matches total")
        try: result["careerMatches"] = int(re.sub(r"[^\d]", "", total_b))
        except: pass
        pct_b = extract_b("%")
        m = re.search(r"([\d.]+)", pct_b)
        if m: result["careerWinPct"] = round(float(m.group(1)) / 100, 4)

    # ── Stats table: table.table_stats ───────────────────────────────────
    # Find the header row to map column index → surface name
    table_match = re.search(r'class="table_stats[^"]*">(.*?)</table>', html, re.DOTALL)
    if not table_match:
        return result
    table_html = table_match.group(1)

    # Parse header row
    header_row = re.search(r'class="header">(.*?)</tr>', table_html, re.DOTALL)
    if not header_row:
        return result
    header_cells = re.findall(r'<td[^>]*>(.*?)</td>', header_row.group(1), re.DOTALL)
    col_surface: dict[int, str] = {}
    for i, cell in enumerate(header_cells):
        # Get visible text (strip tags)
        text = re.sub(r'<[^>]+>', '', cell).strip().lower()
        if text in SURFACE_COL_MAP:
            col_surface[i] = SURFACE_COL_MAP[text]

    # Parse data rows
    data_rows = re.findall(r'<tr class="(?:unpair|pair)"[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    for row_html in data_rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        if not cells:
            continue

        # Year from first cell
        year_text = re.sub(r'<[^>]+>', '', cells[0]).strip()
        if year_text.upper() in ("TOTAL", "PERC. %", ""):
            continue
        try:
            year = int(year_text)
        except ValueError:
            continue

        year_data: dict[str, dict] = {}
        for col_idx, cell in enumerate(cells):
            surface = col_surface.get(col_idx)
            if not surface:
                continue

            # Try title attribute first — most reliable
            # title="surface: Clay, year: 2026, win: 19, loss: 10, %: 65.52 %"
            title_m = re.search(r'title="([^"]+)"', cell)
            if title_m:
                title = title_m.group(1)
                win_m  = re.search(r'win:\s*(\d+)',  title)
                loss_m = re.search(r'loss:\s*(\d+)', title)
                pct_m  = re.search(r'%:\s*([\d.]+)', title)
                if win_m and loss_m:
                    w = int(win_m.group(1))
                    l = int(loss_m.group(1))
                    total = w + l
                    year_data[surface] = {
                        "wins": w, "losses": l, "matches": total,
                        "winPct": round(float(pct_m.group(1)) / 100, 4) if pct_m else (w/total if total else 0)
                    }
            else:
                # Fallback: parse "19/10" text directly
                text = re.sub(r'<[^>]+>', '', cell).strip()
                wl_m = re.match(r"(\d+)/(\d+)", text)
                if wl_m:
                    w, l = int(wl_m.group(1)), int(wl_m.group(2))
                    total = w + l
                    year_data[surface] = {
                        "wins": w, "losses": l, "matches": total,
                        "winPct": round(w / total, 4) if total else 0
                    }

        if year_data:
            result["byYear"][str(year)] = year_data

    # Aggregate across all years
    for year_data in result["byYear"].values():
        for surface, stats in year_data.items():
            if surface not in result["surfaces"]:
                result["surfaces"][surface] = {"wins": 0, "losses": 0, "matches": 0, "winPct": 0}
            result["surfaces"][surface]["wins"]    += stats["wins"]
            result["surfaces"][surface]["losses"]  += stats["losses"]
            result["surfaces"][surface]["matches"] += stats["matches"]
    for surface, stats in result["surfaces"].items():
        t = stats["matches"]
        stats["winPct"] = round(stats["wins"] / t, 4) if t else 0

    return result

async def scrape_player(tour: str, slug: str) -> dict:
    url = f"{BASE}/{tour}/{slug}/"
    html = fetch_html(url)
    return parse_player_profile(html, tour, slug)

# ── Rankings ──────────────────────────────────────────────────────────────────
def parse_rankings(html: str, tour: str) -> list[dict]:
    players = []
    # Rankings table: tr rows with rank | name | country | points | ...
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        texts = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        if len(texts) < 3:
            continue
        try:
            rank = int(texts[0])
        except ValueError:
            continue
        # Get slug from player link
        slug_m = re.search(r'href="[^"]*/' + ('atp' if 'atp' in tour else 'wta') + r'/([^/"]+)/', row)
        slug = slug_m.group(1) if slug_m else player_slug(texts[1])
        players.append({
            "rank": rank,
            "name": texts[1] if len(texts) > 1 else "",
            "country": texts[2] if len(texts) > 2 else "",
            "points": texts[3] if len(texts) > 3 else "",
            "slug": slug,
            "tour": "ATP" if "atp" in tour else "WTA"
        })
    return players

async def scrape_rankings(tour: str) -> list[dict]:
    path = "atp" if "atp" in tour else "wta"
    url = f"{BASE}/{path}/ranking/"
    html = fetch_html(url)
    return parse_rankings(html, tour)

# ── Live / Upcoming / Finished scores (Playwright) ───────────────────────────
TAB_TEXT = {"live": "live tennis", "upcoming": "scheduled", "finished": "finished"}

async def scrape_scores(mode: str) -> list[dict]:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            args=["--no-sandbox", "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent=HEADERS["User-Agent"], locale="en-US"
        )
        page = await ctx.new_page()
        await page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("table", timeout=8000)
        except PlaywrightTimeout:
            pass

        # Click the right tab
        target = TAB_TEXT.get(mode, "live tennis")
        for el in await page.query_selector_all("a, li, div"):
            try:
                txt = (await el.inner_text()).strip().lower()
                if txt == target:
                    await el.click()
                    await asyncio.sleep(1)
                    break
            except Exception:
                continue

        matches = []
        fetched_at = datetime.now(timezone.utc).isoformat()
        current_tournament = "Unknown"
        current_surface = "Unknown"

        for row in await page.query_selector_all("table tr"):
            cells = await row.query_selector_all("td, th")
            texts = [(await c.inner_text()).strip() for c in cells]
            if not texts:
                continue

            # Tournament header (few cells, non-numeric text)
            if len(cells) <= 3:
                full = " ".join(t for t in texts if t)
                if full and len(full) < 100 and not full[0].isdigit():
                    current_tournament = full
                    current_surface = infer_surface(full)
                continue

            if len(cells) < 4:
                continue

            # Player names — non-empty, non-numeric, not a time
            names = [t for t in texts if t and not re.match(r"^\d{0,2}$", t)
                     and not re.match(r"\d{1,2}:\d{2}", t) and len(t) > 1]
            if len(names) < 2:
                continue
            player1, player2 = names[0], names[1]

            # Set scores: single digits 0-7
            nums = [int(t) for t in texts if re.match(r"^\d$", t) and int(t) <= 7]
            mid = len(nums) // 2
            period_scores = [
                {"period": f"S{i+1}", "home": nums[i], "away": nums[mid+i]}
                for i in range(min(mid, 5))
            ]

            time_str = next((t for t in texts if re.match(r"\d{1,2}:\d{2}", t)), None)
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
                "homeScore": nums[0] if nums else None,
                "awayScore": nums[mid] if mid > 0 else None,
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
                raise ValueError("provide player slug, e.g. juan-manuel-cerundolo")
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
