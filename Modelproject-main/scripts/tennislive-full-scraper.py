"""
tennislive.net comprehensive scraper
=====================================
Scrapes the entire platform to supplement Sackmann baseline data.
Covers: ATP, WTA, Challenger, ITF Men (M15/M25), ITF Women (W15/W25/W35/W75)

Usage:
  python3 tennislive-full-scraper.py rankings          # ATP + WTA rankings
  python3 tennislive-full-scraper.py tournaments       # discover all tournaments
  python3 tennislive-full-scraper.py players           # profiles for all ranked players
  python3 tennislive-full-scraper.py players_from <tour> <slug-list-file>
  python3 tennislive-full-scraper.py player <tour> <slug>
  python3 tennislive-full-scraper.py matches <live|upcoming|finished>
  python3 tennislive-full-scraper.py tournament <slug>   # single tournament results
  python3 tennislive-full-scraper.py all                 # full pipeline

Output layout:
  data/tennislive/
    rankings/atp.json           [{rank, name, country, points, slug}]
    rankings/wta.json
    players/atp/{slug}.json     {name, ranking, surfaces{}, byYear{}}
    players/wta/{slug}.json
    tournaments/index.json      [{slug, name, tour, surface, year, url}]
    tournaments/{slug}.json     [{date, round, home, away, score, surface}]
    matches/live.json
    matches/upcoming.json
    matches/finished-YYYY-MM-DD.json
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, date
from pathlib import Path

BASE = "https://www.tennislive.net"
DATA = Path(__file__).parent.parent / "data" / "tennislive"
RATE_LIMIT = 1.5   # seconds between requests
MAX_RETRIES = 3

# ── HTTP headers — exact match from browser network log ──────────────────────
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8,"
              "application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "referer": "https://www.tennislive.net/",
    "sec-ch-ua": '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
}

SURFACE_COL_MAP = {
    "hard": "Hard", "clay": "Clay", "i. hard": "Indoor",
    "indoor": "Indoor", "carpet": "Carpet", "grass": "Grass",
    "acrylic": "Hard", "summary": "All",
}

TOUR_PATTERNS = {
    "atp":         r"\batp\b",
    "wta":         r"\bwta\b",
    "challenger":  r"challenger",
    "itf_men":     r"\bm\d{2}\b",
    "itf_women":   r"\bw\d{2}\b",
    "futures":     r"futures",
}

_tls_session = None
_playwright_html_cache: dict[str, str] = {}

def get_session():
    global _tls_session
    if _tls_session is None:
        import tls_client
        _tls_session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        _tls_session.cookies.update({"vis_co": "EN"})
    return _tls_session

def fetch_playwright_sync(url: str) -> str:
    """Fetch using a real Playwright browser — bypasses Cloudflare JS challenges."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=HEADERS["user-agent"],
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for actual content — Cloudflare challenge pages don't have <table>
            try:
                page.wait_for_selector("table, div.player_stats, div.player_info", timeout=10000)
            except Exception:
                pass
            html = page.content()
        finally:
            browser.close()
    return html

def fetch(url: str, retries: int = MAX_RETRIES) -> str:
    time.sleep(RATE_LIMIT)
    # Try tls_client first (faster, no browser overhead)
    for attempt in range(retries):
        try:
            resp = get_session().get(url, headers=HEADERS, timeout_seconds=25)
            if resp.status_code == 404:
                return ""
            if resp.status_code == 200:
                html = resp.text
                # Show first 300 chars for diagnosis
                preview = html[:300].replace("\n", " ").strip()
                print(f"  [fetch] {url} — {len(html)} bytes | {preview[:120]}")
                # Cloudflare challenge pages are small or contain challenge markers
                if len(html) > 8000 and not any(x in html[:1000].lower() for x in
                        ("challenge", "cf-browser-verification", "just a moment", "enable javascript")):
                    return html
                print(f"  [CF challenge] falling back to Playwright for {url}")
                break
            print(f"  [HTTP {resp.status_code}] {url} attempt {attempt+1}", file=sys.stderr)
        except Exception as e:
            print(f"  [tls_client ERR] {url}: {e}", file=sys.stderr)
            break

    # Playwright fallback — real browser, handles Cloudflare
    print(f"  [Playwright] launching browser for {url}")
    for attempt in range(2):
        try:
            html = fetch_playwright_sync(url)
            print(f"  [Playwright] got {len(html)} bytes from {url}")
            return html
        except Exception as e:
            print(f"  [Playwright ERR] {url} attempt {attempt+1}: {e}", file=sys.stderr)
            time.sleep(3)
    return ""

def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()

def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def load(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return None

def infer_tour(name: str) -> str:
    t = name.lower()
    if re.search(r"\bm\d{2}\b", t): return "ITF Men"
    if re.search(r"\bw\d{2}\b", t): return "ITF Women"
    if "challenger" in t: return "Challenger"
    if "wta" in t or "women" in t: return "WTA"
    if "grand slam" in t or any(x in t for x in ("roland garros","wimbledon","us open","australian open","french open")): return "Grand Slam"
    return "ATP"

def infer_surface(text: str) -> str:
    t = text.lower()
    if "clay" in t: return "Clay"
    if "grass" in t: return "Grass"
    if "indoor" in t or "i. hard" in t: return "Indoor"
    if "carpet" in t: return "Carpet"
    if "hard" in t or "acrylic" in t: return "Hard"
    return "Unknown"

def player_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")

# ── Rankings ──────────────────────────────────────────────────────────────────
def _fetch_rankings_html(url: str) -> str:
    """Fetch rankings page via Playwright, trying multiple selectors."""
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(user_agent=HEADERS["user-agent"], locale="en-US")
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        # Try multiple selectors that might contain rankings
        for sel in ("table.ranking", "table", "#ranking", ".ranking", "tr"):
            try:
                page.wait_for_selector(sel, timeout=5000)
                break
            except PlaywrightTimeout:
                continue
        html = page.content()
        browser.close()
    return html

def scrape_rankings(tour: str) -> list[dict]:
    """Scrape rankings via Playwright (page is JS-rendered)."""
    path_key = "atp" if tour == "atp" else "wta"
    url = f"{BASE}/{path_key}/ranking/"
    print(f"  Fetching {url}")

    html = _fetch_rankings_html(url)
    print(f"  [parse] HTML size: {len(html)} bytes")

    # Diagnostic: show first few <tr> rows to understand structure
    sample_rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.DOTALL)[:5]
    for i, r in enumerate(sample_rows):
        snippet = strip_tags(r)[:120].replace("\n", " ").strip()
        print(f"  [sample row {i}] {snippet}")

    players = []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    print(f"  [parse] found {len(rows)} <tr> rows")

    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        texts = [strip_tags(c).strip() for c in cells]
        if len(texts) < 3:
            continue
        # First cell must be a numeric rank (strip any non-digit chars first)
        rank_str = re.sub(r"[^\d]", "", texts[0])
        if not rank_str:
            continue
        try:
            rank = int(rank_str)
            if rank <= 0 or rank > 2000:
                continue
        except ValueError:
            continue
        # Player name: second cell (may contain link)
        name = texts[1]
        if not name or len(name) < 2:
            continue
        slug_m = re.search(r'href="[^"]*/(?:atp|wta)/([^/"]+)/"', row)
        slug = slug_m.group(1) if slug_m else player_slug(name)
        players.append({
            "rank": rank,
            "name": name,
            "country": texts[2] if len(texts) > 2 else "",
            "points": texts[3] if len(texts) > 3 else "",
            "slug": slug,
            "tour": tour.upper(),
        })

    print(f"  Found {len(players)} {tour.upper()} ranked players")
    return players

def cmd_debug_rankings(tour: str = "atp"):
    """Dump raw rankings page HTML snippet for structure analysis."""
    path_key = "atp" if tour == "atp" else "wta"
    url = f"{BASE}/{path_key}/ranking/"
    print(f"Fetching {url} for debug...")
    html = _fetch_rankings_html(url)
    out = DATA / "rankings" / f"{tour}-debug.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html[:50000], encoding="utf-8")
    print(f"Saved first 50000 bytes of HTML → {out}")
    # Show all unique tag+class combinations to understand structure
    tags = re.findall(r"<((?:table|tr|td|th|div|ul|li)[^>]{0,80})>", html)
    seen = set()
    print("\nUnique block elements (first 30):")
    for t in tags:
        key = re.sub(r'\s+', ' ', t.strip())[:80]
        if key not in seen:
            seen.add(key)
            print(f"  <{key}>")
        if len(seen) >= 30:
            break

def cmd_rankings():
    for tour in ("atp", "wta"):
        players = scrape_rankings(tour)
        if players:
            save(DATA / "rankings" / f"{tour}.json", players)
            print(f"Saved {len(players)} {tour.upper()} rankings")

# ── Tournament discovery ──────────────────────────────────────────────────────
def scrape_tournament_index() -> list[dict]:
    """Discover all tournaments from the left menu on the scores page."""
    print(f"  Fetching tournament list from {BASE}")
    html = fetch(BASE)
    if not html:
        return []

    tournaments = []
    seen = set()
    # Left menu links: /atp-men/{slug}/ and /wta-women/{slug}/
    links = re.findall(
        r'href="(https://www\.tennislive\.net/(?:atp-men|wta-women)/([^/"]+)/)"[^>]*title="([^"]+)"',
        html
    )
    for url, slug, title in links:
        if slug in seen or slug in ("", "atp-men", "wta-women"):
            continue
        seen.add(slug)
        name = title.replace(" - Tennis ATP", "").replace(" - Tennis WTA", "").strip()
        year_m = re.search(r"(\d{4})", slug)
        year = int(year_m.group(1)) if year_m else datetime.now().year
        tournaments.append({
            "slug": slug,
            "name": name,
            "tour": infer_tour(name),
            "surface": infer_surface(name),
            "year": year,
            "url": url,
        })

    # Also discover historical years by checking year-specific index pages
    for section in ("atp-men", "wta-women"):
        for y in range(2023, datetime.now().year + 1):
            year_url = f"{BASE}/{section}/{y}/"
            year_html = fetch(year_url)
            if not year_html:
                continue
            year_links = re.findall(
                r'href="(https://www\.tennislive\.net/' + section + r'/([^/"]+)/)"[^>]*title="([^"]+)"',
                year_html
            )
            for url2, slug2, title2 in year_links:
                if slug2 in seen or not slug2:
                    continue
                seen.add(slug2)
                name2 = title2.replace(" - Tennis ATP", "").replace(" - Tennis WTA", "").strip()
                year_m2 = re.search(r"(\d{4})", slug2)
                year2 = int(year_m2.group(1)) if year_m2 else y
                tournaments.append({
                    "slug": slug2, "name": name2,
                    "tour": infer_tour(name2), "surface": infer_surface(name2),
                    "year": year2, "url": url2,
                })

    print(f"  Discovered {len(tournaments)} tournaments")
    return tournaments

def cmd_tournaments():
    tournaments = scrape_tournament_index()
    if tournaments:
        save(DATA / "tournaments" / "index.json", tournaments)
        print(f"Saved {len(tournaments)} tournaments to index")

# ── Tournament match results ──────────────────────────────────────────────────
def scrape_tournament_matches(slug: str, url: str) -> list[dict]:
    """Scrape all match results from a tournament page."""
    print(f"  Scraping tournament: {slug}")
    html = fetch(url)
    if not html:
        return []

    matches = []
    current_round = "Unknown"
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)

    for row in rows:
        # Round header rows
        round_m = re.search(r'class="[^"]*(?:round|header)[^"]*"', row)
        if round_m:
            txt = strip_tags(row)
            if txt and len(txt) < 50:
                current_round = txt
                continue

        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        texts = [strip_tags(c) for c in cells]
        if len(texts) < 4:
            continue

        # Date cell
        date_m = re.search(r"(\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})", " ".join(texts[:3]))
        match_date = date_m.group(1) if date_m else ""

        # Player names: non-empty, non-numeric, not date-like
        names = [t for t in texts if t and len(t) > 2 and not re.match(r"^[\d.:/-]+$", t)
                 and not re.match(r"\d{2}\.\d{2}", t)]
        if len(names) < 2:
            continue

        # Score: look for cells like "6:4 6:2" or "3-6 7-5 6-3"
        score_cells = [t for t in texts if re.search(r"\d[:\-]\d", t)]
        score = " ".join(score_cells) if score_cells else ""

        # Set scores for period breakdown
        sets = re.findall(r"(\d)[:\-](\d)", score)
        period_scores = [{"set": f"S{i+1}", "home": int(h), "away": int(a)}
                         for i, (h, a) in enumerate(sets[:5])]

        # Winner detection: first player listed is usually winner, or check bold/class
        winner_class = "home" if re.search(r'class="[^"]*winner[^"]*"', cells[0] if cells else "") else None

        matches.append({
            "date": match_date,
            "round": current_round,
            "homePlayer": names[0],
            "awayPlayer": names[1],
            "score": score,
            "periodScores": period_scores,
            "surface": infer_surface(slug),
            "slug": slug,
        })

    return matches

def cmd_tournament(slug: str):
    index = load(DATA / "tournaments" / "index.json") or []
    entry = next((t for t in index if t["slug"] == slug), None)
    if not entry:
        url = f"{BASE}/atp-men/{slug}/"
        entry = {"slug": slug, "url": url, "name": slug, "tour": "ATP"}
    matches = scrape_tournament_matches(slug, entry["url"])
    if matches:
        save(DATA / "tournaments" / f"{slug}.json", matches)
        print(f"Saved {len(matches)} matches for {slug}")

# ── Player profiles ───────────────────────────────────────────────────────────
def parse_player_profile(html: str, tour: str, slug: str) -> dict:
    result: dict = {
        "slug": slug, "tour": tour.upper(),
        "url": f"{BASE}/{tour}/{slug}/",
        "scrapedAt": datetime.now(timezone.utc).isoformat(),
        "surfaces": {}, "byYear": {},
    }

    # Bio block
    bio_m = re.search(r'class="player_stats">(.*?)</div>', html, re.DOTALL)
    if bio_m:
        bio = bio_m.group(1)
        def get_b(label: str) -> str:
            m = re.search(re.escape(label) + r"[:\s]*<b[^>]*>(.*?)</b>", bio, re.IGNORECASE | re.DOTALL)
            return strip_tags(m.group(1)) if m else ""
        result["name"] = get_b("Name")
        result["country"] = get_b("Country")
        result["birthdate"] = get_b("Birthdate")
        for rk_label in ("ATP ranking", "WTA ranking"):
            r = get_b(rk_label)
            if r:
                try: result["ranking"] = int(re.sub(r"[^\d]", "", r))
                except: pass
                break
        pts = get_b("Points")
        try: result["points"] = int(re.sub(r"[^\d]", "", pts))
        except: pass
        wins = get_b("Win")
        try: result["careerWins"] = int(re.sub(r"[^\d]", "", wins))
        except: pass
        total = get_b("Matches total")
        try: result["careerMatches"] = int(re.sub(r"[^\d]", "", total))
        except: pass
        pct = get_b("%")
        m = re.search(r"([\d.]+)", pct)
        if m: result["careerWinPct"] = round(float(m.group(1)) / 100, 4)

    # Stats table: table.table_stats
    table_m = re.search(r'class="table_stats[^"]*">(.*?)</table>', html, re.DOTALL)
    if not table_m:
        return result

    table_html = table_m.group(1)
    header_row = re.search(r'class="header">(.*?)</tr>', table_html, re.DOTALL)
    if not header_row:
        return result

    header_cells = re.findall(r"<td[^>]*>(.*?)</td>", header_row.group(1), re.DOTALL)
    col_surface: dict[int, str] = {}
    for i, cell in enumerate(header_cells):
        text = strip_tags(cell).lower()
        if text in SURFACE_COL_MAP:
            col_surface[i] = SURFACE_COL_MAP[text]

    data_rows = re.findall(r'<tr class="(?:unpair|pair)"[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    for row_html in data_rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
        if not cells:
            continue
        year_text = strip_tags(cells[0])
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
            title_m = re.search(r'title="([^"]+)"', cell)
            if title_m:
                t = title_m.group(1)
                win_m = re.search(r"win:\s*(\d+)", t)
                loss_m = re.search(r"loss:\s*(\d+)", t)
                pct_m = re.search(r"%:\s*([\d.]+)", t)
                if win_m and loss_m:
                    w, l = int(win_m.group(1)), int(loss_m.group(1))
                    total = w + l
                    if total > 0:
                        year_data[surface] = {
                            "wins": w, "losses": l, "matches": total,
                            "winPct": round(float(pct_m.group(1)) / 100, 4) if pct_m else round(w / total, 4),
                        }
            else:
                text = strip_tags(cell)
                wl_m = re.match(r"(\d+)/(\d+)", text)
                if wl_m:
                    w, l = int(wl_m.group(1)), int(wl_m.group(2))
                    total = w + l
                    if total > 0:
                        year_data[surface] = {
                            "wins": w, "losses": l, "matches": total,
                            "winPct": round(w / total, 4),
                        }
        if year_data:
            result["byYear"][str(year)] = year_data

    # Recent matches section
    recent = []
    match_rows = re.findall(r'<tr[^>]*class="[^"]*(?:unpair|pair)[^"]*"[^>]*>(.*?)</tr>', html, re.DOTALL)
    for row_html in match_rows[:20]:
        cells2 = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL)
        texts2 = [strip_tags(c) for c in cells2]
        if len(texts2) < 4:
            continue
        # Date | tournament | opponent | result | score
        date_m = re.search(r"(\d{2}\.\d{2}\.\d{4})", " ".join(texts2[:2]))
        if not date_m:
            continue
        names2 = [t for t in texts2 if t and len(t) > 2 and not re.match(r"^[\d.:\-/]+$", t)]
        score_t = next((t for t in texts2 if re.search(r"\d[:\-]\d", t)), "")
        result_t = next((t for t in texts2 if t in ("W", "L", "Win", "Loss")), "")
        if len(names2) >= 2:
            recent.append({
                "date": date_m.group(1),
                "opponent": names2[-1],
                "score": score_t,
                "result": "W" if result_t in ("W", "Win") else "L",
            })
    result["recentMatches"] = recent[:10]

    # Aggregate surface totals
    for year_data in result["byYear"].values():
        for surface, stats in year_data.items():
            if surface not in result["surfaces"]:
                result["surfaces"][surface] = {"wins": 0, "losses": 0, "matches": 0, "winPct": 0}
            result["surfaces"][surface]["wins"] += stats["wins"]
            result["surfaces"][surface]["losses"] += stats["losses"]
            result["surfaces"][surface]["matches"] += stats["matches"]
    for surface, stats in result["surfaces"].items():
        t = stats["matches"]
        stats["winPct"] = round(stats["wins"] / t, 4) if t else 0

    return result

def scrape_player(tour: str, slug: str, force: bool = False) -> dict | None:
    out_path = DATA / "players" / tour / f"{slug}.json"
    if not force and out_path.exists():
        # Skip if scraped in last 12 hours
        age = time.time() - out_path.stat().st_mtime
        if age < 43200:
            return None  # already fresh

    url = f"{BASE}/{tour}/{slug}/"
    html = fetch(url)
    if not html:
        return None

    data = parse_player_profile(html, tour, slug)
    save(out_path, data)
    return data

def cmd_players(tour_filter: str | None = None, force: bool = False):
    """Scrape profiles for all players in rankings files."""
    tours = ["atp", "wta"] if not tour_filter else [tour_filter]
    total = 0
    for tour in tours:
        rankings = load(DATA / "rankings" / f"{tour}.json")
        if not rankings:
            print(f"No rankings for {tour} — run `rankings` first")
            continue
        print(f"Scraping {len(rankings)} {tour.upper()} player profiles...")
        for i, player in enumerate(rankings):
            slug = player.get("slug", "")
            if not slug:
                continue
            result = scrape_player(tour, slug, force=force)
            if result:
                total += 1
                name = result.get("name", slug)
                clay = result.get("surfaces", {}).get("Clay", {})
                clay_str = f"clay {clay.get('wins',0)}/{clay.get('losses',0)}" if clay else ""
                print(f"  [{i+1}/{len(rankings)}] {name} — {clay_str}")
            else:
                print(f"  [{i+1}/{len(rankings)}] {slug} (cached/skipped)")
    print(f"Done. Scraped {total} new profiles.")

def cmd_player(tour: str, slug: str):
    result = scrape_player(tour, slug, force=True)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Failed to scrape {tour}/{slug}")

# ── Live / Upcoming / Finished scores (Playwright) ───────────────────────────
TAB_TEXT = {"live": "live tennis", "upcoming": "scheduled", "finished": "finished"}

# Day-of-week abbreviations used in calendar navigation rows
_WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

def _extract_player_links(row_html: str) -> list[tuple[str, str]]:
    """Return [(slug, display_name), ...] for /atp/ or /wta/ player profile links.
    Excludes the H2H link which points to /atp/h2h/ or similar."""
    found = re.findall(
        r'href="/(?:atp|wta)/([^/"]+)/"[^>]*>\s*([^<]{2,40})\s*</a>',
        row_html, re.IGNORECASE
    )
    # Filter out non-player links (H2H pages, flag images, etc.)
    return [(slug, name.strip()) for slug, name in found
            if "h2h" not in slug.lower() and name.strip()
            and not re.match(r"^\d+$", name.strip())]

async def scrape_scores_async(mode: str) -> list[dict]:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(user_agent=HEADERS["user-agent"], locale="en-US")
        page = await ctx.new_page()
        await page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("table", timeout=8000)
        except PlaywrightTimeout:
            pass

        target = TAB_TEXT.get(mode, "live tennis")
        for el in await page.query_selector_all("a, li, div"):
            try:
                txt = (await el.inner_text()).strip().lower()
                if txt == target:
                    await el.click()
                    await asyncio.sleep(1.5)
                    break
            except Exception:
                continue

        matches = []
        fetched_at = datetime.now(timezone.utc).isoformat()
        current_tournament = "Unknown"
        current_surface = "Unknown"
        current_tour = "ATP"
        status_type = "inprogress" if mode == "live" else (
            "notstarted" if mode == "upcoming" else "finished")
        status_label = "Live" if mode == "live" else ("Scheduled" if mode == "upcoming" else "Finished")

        for row in await page.query_selector_all("table tr"):
            cells = await row.query_selector_all("td, th")
            texts = [(await c.inner_text()).strip() for c in cells]
            row_html = await row.inner_html()

            if not any(texts):
                continue

            # ── Calendar navigation rows ─────────────────────────────────────
            # These contain day-of-week abbreviations like "Mon", "Tue", etc.
            if any(t.lower() in _WEEKDAYS for t in texts):
                continue

            # ── Column-header / tournament sub-header rows ───────────────────
            # These look like: ["Paris", "1", "2", "3", "4", "5", "sets", "H2H"]
            # The presence of the literal text "sets" (case-insensitive) marks this.
            lower_texts = [t.lower() for t in texts]
            if "sets" in lower_texts:
                # Extract tournament name: first non-empty, non-digit, non-keyword text
                skip_words = {"sets", "h2h", "1", "2", "3", "4", "5", "s1", "s2", "s3", "s4", "s5"}
                t_name = next(
                    (t for t in texts if t and t.lower() not in skip_words
                     and not re.match(r"^\d+$", t)),
                    None
                )
                if t_name:
                    current_tournament = t_name
                    current_surface = infer_surface(t_name)
                    current_tour = infer_tour(t_name)
                continue

            # ── Single-cell / very short rows — big tournament section headers ─
            if len(cells) <= 2:
                full = " ".join(t for t in texts if t).strip()
                if full and not any(c.isdigit() for c in full[:3]):
                    current_tournament = full
                    current_surface = infer_surface(full)
                    current_tour = infer_tour(full)
                continue

            # ── Extract player names from anchor href links ───────────────────
            # Player links look like /atp/cerundolo/ or /wta/keys/
            player_links = _extract_player_links(row_html)
            if len(player_links) < 2:
                # Not a match row (no two recognisable player links)
                continue

            home_slug, home_name = player_links[0]
            away_slug, away_name = player_links[1]

            # ── Scores ───────────────────────────────────────────────────────
            # Single-digit cells (≤ 7) are set/game scores. Typical layout:
            #   time | player | s1_home | s2_home | s3_home | s1_away | s2_away | s3_away | H2H
            # The scores split at the midpoint: first half = home, second half = away.
            nums = [int(t) for t in texts if re.match(r"^\d{1,2}$", t) and int(t) <= 99]
            # Only consider scores ≤ 7 (set/tiebreak-like values)
            set_nums = [n for n in nums if n <= 7]
            mid = len(set_nums) // 2
            period_scores = []
            for i in range(min(mid, 5)):
                period_scores.append({
                    "period": f"S{i+1}",
                    "home": set_nums[i],
                    "away": set_nums[mid + i],
                })

            time_str = next((t for t in texts if re.match(r"^\d{1,2}:\d{2}", t)), None)
            # Clean up time (may have round info appended after newline)
            if time_str and "\n" in time_str:
                time_str = time_str.split("\n")[0].strip()

            # Round info may appear in texts[0] after the time
            round_info = ""
            if texts[0] and "\n" in texts[0]:
                round_info = texts[0].split("\n", 1)[1].strip()

            matches.append({
                "provider": "tennislive",
                "providerId": f"tl-{len(matches)+1}",
                "tournament": current_tournament,
                "category": current_tour,
                "surface": current_surface,
                "status": status_label,
                "statusType": status_type,
                "startTime": time_str,
                "round": round_info or None,
                "homePlayer": home_name,
                "homeSlug": home_slug,
                "awayPlayer": away_name,
                "awaySlug": away_slug,
                "homeScore": set_nums[0] if set_nums else None,
                "awayScore": set_nums[mid] if mid > 0 else None,
                "periodScores": period_scores,
                "fetchedAt": fetched_at,
            })

        await browser.close()
        return matches

def cmd_matches(mode: str):
    matches = asyncio.run(scrape_scores_async(mode))
    today = date.today().isoformat()
    fname = f"{mode}.json" if mode in ("live", "upcoming") else f"finished-{today}.json"
    save(DATA / "matches" / fname, matches)
    print(f"Saved {len(matches)} {mode} matches → data/tennislive/matches/{fname}")

# ── All tournament results ─────────────────────────────────────────────────────
def cmd_all_tournaments():
    index = load(DATA / "tournaments" / "index.json")
    if not index:
        print("No tournament index — run `tournaments` first")
        return
    done = 0
    for t in index:
        out = DATA / "tournaments" / f"{t['slug']}.json"
        if out.exists():
            continue
        matches = scrape_tournament_matches(t["slug"], t["url"])
        if matches:
            save(out, matches)
            print(f"  {t['name']}: {len(matches)} matches")
            done += 1
    print(f"Scraped {done} new tournament result files")

# ── Full pipeline ──────────────────────────────────────────────────────────────
def cmd_all():
    print("=== Step 1: Rankings ===")
    cmd_rankings()
    print("\n=== Step 2: Tournament index ===")
    cmd_tournaments()
    print("\n=== Step 3: Player profiles (ATP) ===")
    cmd_players("atp")
    print("\n=== Step 4: Player profiles (WTA) ===")
    cmd_players("wta")
    print("\n=== Step 5: Tournament match results ===")
    cmd_all_tournaments()
    print("\n=== Step 6: Today's matches ===")
    for mode in ("live", "upcoming", "finished"):
        cmd_matches(mode)
    print("\n=== All done ===")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "rankings":
        cmd_rankings()
    elif cmd == "tournaments":
        cmd_tournaments()
    elif cmd == "players":
        tour = sys.argv[2] if len(sys.argv) > 2 else None
        force = "--force" in sys.argv
        cmd_players(tour, force=force)
    elif cmd == "player":
        if len(sys.argv) < 4:
            print("Usage: player <atp|wta> <slug>")
        else:
            cmd_player(sys.argv[2], sys.argv[3])
    elif cmd == "matches":
        mode = sys.argv[2] if len(sys.argv) > 2 else "live"
        cmd_matches(mode)
    elif cmd == "tournament":
        if len(sys.argv) < 3:
            print("Usage: tournament <slug>")
        else:
            cmd_tournament(sys.argv[2])
    elif cmd == "all_tournaments":
        cmd_all_tournaments()
    elif cmd == "all":
        cmd_all()
    elif cmd == "debug_rankings":
        tour = sys.argv[2] if len(sys.argv) > 2 else "atp"
        cmd_debug_rankings(tour)
    else:
        print(__doc__)
