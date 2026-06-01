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
  python3 tennislive-full-scraper.py itf <live|upcoming|finished>   # ITF Men + Women only
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
                # tls_client may return raw compressed bytes via .text;
                # try to decode content bytes explicitly first
                try:
                    raw = resp.content
                    if raw[:2] in (b"\x1f\x8b", b"\x78\x9c", b"\x78\x01"):
                        # gzip or zlib — decompress
                        import zlib, gzip as _gzip
                        try:
                            html = _gzip.decompress(raw).decode("utf-8", errors="replace")
                        except Exception:
                            html = zlib.decompress(raw, -15).decode("utf-8", errors="replace")
                    else:
                        html = raw.decode("utf-8", errors="replace")
                except Exception:
                    html = resp.text
                # Show first 120 chars for diagnosis (ASCII only)
                preview = "".join(c if c.isprintable() else "?" for c in html[:120])
                print(f"  [fetch] {url} — {len(html)} bytes | {preview}")
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
def scrape_rankings(tour: str) -> list[dict]:
    """Scrape rankings page via Playwright then parse with regex.

    The page has a real <table> with <tr class="pair|unpair"> rows.
    Ranks are formatted "1." (with a period). Player names come from
    the <a title="..."> attribute. Country code is in (ITA) parenthetical.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    path_key = "atp" if tour == "atp" else "wta"
    url = f"{BASE}/{path_key}/ranking/"
    print(f"  Fetching {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(user_agent=HEADERS["user-agent"], locale="en-US")
        page = ctx.new_page()
        page.goto(url, wait_until="load", timeout=30000)
        try:
            page.wait_for_selector("tr.pair, tr.unpair", timeout=10000)
        except PlaywrightTimeout:
            print("  [rankings] timed out waiting for tr.pair/tr.unpair")
        html = page.content()
        browser.close()

    # Target only ranking rows (skip header and unrelated rows)
    rows = re.findall(r'<tr\s+class="(?:pair|unpair)"[^>]*>(.*?)</tr>', html, re.DOTALL)
    print(f"  [parse] {len(html)} bytes, {len(rows)} ranking rows found")

    players = []
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if len(cells) < 3:
            continue

        # Rank cell: "1." → strip non-digits
        rank_str = re.sub(r"[^\d]", "", strip_tags(cells[0]).strip())
        if not rank_str:
            continue
        try:
            rank = int(rank_str)
            if rank <= 0 or rank > 2000:
                continue
        except ValueError:
            continue

        # Name cell: <img flag> <a href="/atp/slug/" title="Full Name">Full Name</a> (CTY) (age)
        name_m = re.search(r'title="([^"]+)"', cells[1])
        name = name_m.group(1).strip() if name_m else strip_tags(cells[1]).split("(")[0].strip()
        if not name or len(name) < 2:
            continue

        slug_m = re.search(r'/(?:atp|wta)/([^/"]+)/', cells[1])
        slug = slug_m.group(1) if slug_m else player_slug(name)

        country_m = re.search(r'\(([A-Z]{2,3})\)', strip_tags(cells[1]))
        country = country_m.group(1) if country_m else ""

        points = strip_tags(cells[2]).strip()

        players.append({
            "rank": rank, "name": name, "country": country,
            "points": points, "slug": slug, "tour": tour.upper(),
        })

    print(f"  Found {len(players)} {tour.upper()} ranked players")
    return players

def cmd_debug_rankings(tour: str = "atp"):
    """Quick rankings parse test — prints first 5 players found."""
    players = scrape_rankings(tour)
    for p in players[:5]:
        print(f"  #{p['rank']} {p['name']} ({p['country']}) — {p['points']} pts  [{p['slug']}]")

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
    """Return [(slug, display_name), ...] for ATP/WTA player profile links.
    Handles both relative (/atp/slug/) and absolute (https://...tennislive.net/atp/slug/) hrefs."""
    found = re.findall(
        r'href="(?:https?://[^/"]*)?/(?:atp|wta)/([^/"]+)/"[^>]*>\s*([^<]{2,40})\s*</a>',
        row_html, re.IGNORECASE
    )
    return [(slug, name.strip()) for slug, name in found
            if "h2h" not in slug.lower() and name.strip()
            and not re.match(r"^\d+$", name.strip())]

async def scrape_itf_async(mode: str, dump_html: bool = False) -> list[dict]:
    """Scrape ITF Men + Women matches from the dedicated /itf/ page."""
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

    itf_url = f"{BASE}/itf/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--ignore-certificate-errors",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(user_agent=HEADERS["user-agent"], locale="en-US")
        page = await ctx.new_page()
        await page.goto(itf_url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector("table", timeout=10000)
        except PlaywrightTimeout:
            print("[WARN] ITF page: no table found within timeout")

        target = TAB_TEXT.get(mode, "live tennis")
        if mode != "live":
            clicked = False
            for selector in [f"a:has-text('{target}')", f"li:has-text('{target}')",
                             f"div:has-text('{target}')"]:
                try:
                    loc = page.locator(selector).first
                    if await loc.is_visible(timeout=2000):
                        await loc.click()
                        clicked = True
                        break
                except Exception:
                    continue
            if not clicked:
                for el in await page.query_selector_all("a, li, div, span, button"):
                    try:
                        txt = (await el.inner_text()).strip().lower()
                        if txt == target:
                            await el.click()
                            clicked = True
                            break
                    except Exception:
                        continue
            if clicked:
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    await asyncio.sleep(3)
                await asyncio.sleep(1)
            else:
                print(f"[WARN] ITF: could not find tab: {target!r}")

        # Scroll to load all rows
        prev_count = 0
        for _ in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.8)
            count = await page.evaluate("document.querySelectorAll('table tr').length")
            if count == prev_count:
                break
            prev_count = count

        fetched_at = datetime.now(timezone.utc).isoformat()
        status_type = "inprogress" if mode == "live" else (
            "notstarted" if mode == "upcoming" else "finished")
        status_label = "Live" if mode == "live" else ("Scheduled" if mode == "upcoming" else "Finished")

        raw_rows = []
        for row in await page.query_selector_all("table tr"):
            cells = await row.query_selector_all("td, th")
            texts = [(await c.inner_text()).strip() for c in cells]
            row_html = await row.inner_html()
            raw_rows.append((texts, row_html))

        print(f"[DEBUG] ITF page total rows: {len(raw_rows)}")

        if dump_html:
            dump_path = DATA / "matches" / f"debug-itf-{mode}.html"
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            dump_path.write_text(await page.content(), encoding="utf-8")
            print(f"[DEBUG] ITF HTML saved → {dump_path}")

        await browser.close()

        # Reuse the same row-parsing logic as main scraper
        matches = []
        pending_home = None
        current_tournament = "ITF"
        current_surface = "Unknown"
        current_tour = "ITF"

        def row_scores(texts):
            nums = []
            for t in texts:
                if not re.match(r"^\d{1,2}$", t):
                    continue
                v = int(t)
                if v <= 7:
                    nums.append(v)
            return nums

        for texts, row_html in raw_rows:
            if not any(texts):
                continue
            if any(t.lower() in _WEEKDAYS for t in texts):
                pending_home = None
                continue
            lower_texts = [t.lower() for t in texts]
            if "sets" in lower_texts:
                skip_words = {"sets","h2h","1","2","3","4","5","s1","s2","s3","s4","s5"}
                t_name = next((t for t in texts if t and t.lower() not in skip_words
                               and not re.match(r"^\d+$", t)), None)
                if t_name:
                    current_tournament = t_name
                    current_surface = infer_surface(t_name)
                    current_tour = infer_tour(t_name)
                pending_home = None
                continue
            if len(texts) <= 2:
                full = " ".join(t for t in texts if t).strip()
                if full and not any(c.isdigit() for c in full[:3]):
                    current_tournament = full
                    current_surface = infer_surface(full)
                    current_tour = infer_tour(full)
                pending_home = None
                continue

            player_links = _extract_player_links(row_html)
            if not player_links:
                pending_home = None
                continue

            slug, name = player_links[0]
            name = re.sub(r"\s*\[\d+\]$", "", name).strip()
            has_time = bool(re.search(r"\d{1,2}:\d{2}", texts[0]))

            if has_time:
                time_str = re.search(r"\d{1,2}:\d{2}", texts[0]).group(0)
                round_parts = texts[0].split("\n")
                round_info = " ".join(p.strip() for p in round_parts[1:] if p.strip())
                pending_home = {
                    "slug": slug, "name": name,
                    "scores": row_scores(texts),
                    "time": time_str, "round": round_info,
                    "tournament": current_tournament,
                    "surface": current_surface,
                    "tour": current_tour,
                }
            elif pending_home is not None:
                away_scores = row_scores(texts)
                home_scores = pending_home["scores"]
                n_sets = min(len(home_scores), len(away_scores), 5)
                while n_sets > 1 and home_scores[n_sets-1] == 0 and away_scores[n_sets-1] == 0:
                    n_sets -= 1
                period_scores = [
                    {"period": f"S{i+1}", "home": home_scores[i], "away": away_scores[i]}
                    for i in range(n_sets)
                ]
                home_sets = sum(1 for i in range(n_sets) if home_scores[i] > away_scores[i])
                away_sets = sum(1 for i in range(n_sets) if away_scores[i] > home_scores[i])
                matches.append({
                    "provider": "tennislive",
                    "providerId": f"itf-{len(matches)+1}",
                    "tournament": pending_home["tournament"],
                    "category": pending_home["tour"],
                    "surface": pending_home["surface"],
                    "status": status_label,
                    "statusType": status_type,
                    "startTime": pending_home["time"],
                    "round": pending_home["round"] or None,
                    "homePlayer": pending_home["name"],
                    "homeSlug": pending_home["slug"],
                    "awayPlayer": name,
                    "awaySlug": slug,
                    "homeSetsWon": home_sets,
                    "awaySetsWon": away_sets,
                    "homeScore": home_scores[0] if home_scores else None,
                    "awayScore": away_scores[0] if away_scores else None,
                    "periodScores": period_scores,
                    "fetchedAt": fetched_at,
                })
                pending_home = None
            else:
                pending_home = None

        return matches


def cmd_itf(mode: str):
    """Scrape the main scores page and filter to ITF Men + ITF Women only."""
    dump_html = "--dump" in sys.argv
    all_matches = asyncio.run(scrape_scores_async(mode, dump_html=dump_html))
    itf = [m for m in all_matches if "itf" in m.get("category", "").lower()]
    today = date.today().isoformat()
    fname = f"itf-{mode}.json" if mode in ("live", "upcoming") else f"itf-finished-{today}.json"
    save(DATA / "matches" / fname, itf)
    men   = [m for m in itf if "men"   in m.get("category", "").lower()]
    women = [m for m in itf if "women" in m.get("category", "").lower()]
    print(f"Saved {len(itf)} ITF {mode} matches → data/tennislive/matches/{fname}")
    print(f"  ITF Men: {len(men)}   ITF Women: {len(women)}")
    if not itf:
        print(f"  (Total matches scraped from main page: {len(all_matches)} — ITF may not be listed today)")


async def scrape_scores_async(mode: str, dump_html: bool = False) -> list[dict]:
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
        if mode != "live":  # live is the default tab — no click needed
            clicked = False
            # Try exact Playwright text locator first (fastest, most reliable)
            for selector in [
                f"a:has-text('{target}')",
                f"li:has-text('{target}')",
                f"div:has-text('{target}')",
            ]:
                try:
                    loc = page.locator(selector).first
                    if await loc.is_visible(timeout=2000):
                        await loc.click()
                        clicked = True
                        break
                except Exception:
                    continue

            # Fallback: iterate all clickable elements
            if not clicked:
                for el in await page.query_selector_all("a, li, div, span, button"):
                    try:
                        txt = (await el.inner_text()).strip().lower()
                        if txt == target:
                            await el.click()
                            clicked = True
                            break
                    except Exception:
                        continue

            if clicked:
                # Wait for the table to repopulate with new content
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    await asyncio.sleep(3)
                # Extra buffer for dynamic rows
                await asyncio.sleep(1)
            else:
                print(f"[WARN] Could not find tab: {target!r}")

        fetched_at = datetime.now(timezone.utc).isoformat()
        current_tournament = "Unknown"
        current_surface = "Unknown"
        current_tour = "ATP"
        status_type = "inprogress" if mode == "live" else (
            "notstarted" if mode == "upcoming" else "finished")
        status_label = "Live" if mode == "live" else ("Scheduled" if mode == "upcoming" else "Finished")

        # ── Scroll to load all lazy-rendered rows ────────────────────────────
        prev_count = 0
        for _ in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.8)
            count = await page.evaluate("document.querySelectorAll('table tr').length")
            if count == prev_count:
                break
            prev_count = count

        # ── Collect all rows first ────────────────────────────────────────────
        # Each match is TWO consecutive rows: row1=home player (has time), row2=away player
        raw_rows = []
        for row in await page.query_selector_all("table tr"):
            cells = await row.query_selector_all("td, th")
            texts = [(await c.inner_text()).strip() for c in cells]
            row_html = await row.inner_html()
            raw_rows.append((texts, row_html))

        print(f"[DEBUG] Total table rows found: {len(raw_rows)}")

        # ── Process rows ──────────────────────────────────────────────────────
        matches = []
        pending_home: dict | None = None   # home-player row waiting for away row

        def row_scores(texts: list[str]) -> list[int]:
            """Extract set-score integers (0-7) from a row's cell texts."""
            nums = []
            for t in texts:
                # Skip the player name cell and time cell (they contain letters)
                if not re.match(r"^\d{1,2}$", t):
                    continue
                v = int(t)
                if v <= 7:
                    nums.append(v)
            return nums

        for texts, row_html in raw_rows:
            if not any(texts):
                continue

            # Calendar rows (Mon/Tue/…)
            if any(t.lower() in _WEEKDAYS for t in texts):
                pending_home = None
                continue

            # Column-header rows — contain literal "sets"
            lower_texts = [t.lower() for t in texts]
            if "sets" in lower_texts:
                skip_words = {"sets", "h2h", "1", "2", "3", "4", "5", "s1", "s2", "s3", "s4", "s5"}
                t_name = next((t for t in texts if t and t.lower() not in skip_words
                               and not re.match(r"^\d+$", t)), None)
                if t_name:
                    current_tournament = t_name
                    current_surface = infer_surface(t_name)
                    current_tour = infer_tour(t_name)
                pending_home = None
                continue

            # Very short rows — tournament section headers
            if len(texts) <= 2:
                full = " ".join(t for t in texts if t).strip()
                if full and not any(c.isdigit() for c in full[:3]):
                    current_tournament = full
                    current_surface = infer_surface(full)
                    current_tour = infer_tour(full)
                pending_home = None
                continue

            # Extract single player link from this row
            player_links = _extract_player_links(row_html)
            if not player_links:
                pending_home = None
                continue

            slug, name = player_links[0]
            # Strip seeding bracket: "Jakub Mensik [26]" → "Jakub Mensik"
            name = re.sub(r"\s*\[\d+\]$", "", name).strip()

            # Time in texts[0] → this is the HOME player row
            has_time = bool(re.search(r"\d{1,2}:\d{2}", texts[0]))

            if has_time:
                # Start of a new match
                time_str = re.search(r"\d{1,2}:\d{2}", texts[0]).group(0)
                round_parts = texts[0].split("\n")
                round_info = " ".join(p.strip() for p in round_parts[1:] if p.strip())
                pending_home = {
                    "slug": slug, "name": name,
                    "scores": row_scores(texts),
                    "time": time_str, "round": round_info,
                    "tournament": current_tournament,
                    "surface": current_surface,
                    "tour": current_tour,
                }
            elif pending_home is not None:
                # Away player row — pair with pending home
                away_scores = row_scores(texts)
                home_scores = pending_home["scores"]

                n_sets = min(len(home_scores), len(away_scores), 5)
                # Drop trailing phantom sets where both sides are 0 (empty columns)
                while n_sets > 1 and home_scores[n_sets-1] == 0 and away_scores[n_sets-1] == 0:
                    n_sets -= 1
                period_scores = [
                    {"period": f"S{i+1}", "home": home_scores[i], "away": away_scores[i]}
                    for i in range(n_sets)
                ]
                # Sets won = count of sets where this player won more games
                home_sets = sum(1 for i in range(n_sets) if home_scores[i] > away_scores[i])
                away_sets = sum(1 for i in range(n_sets) if away_scores[i] > home_scores[i])

                matches.append({
                    "provider": "tennislive",
                    "providerId": f"tl-{len(matches)+1}",
                    "tournament": pending_home["tournament"],
                    "category": pending_home["tour"],
                    "surface": pending_home["surface"],
                    "status": status_label,
                    "statusType": status_type,
                    "startTime": pending_home["time"],
                    "round": pending_home["round"] or None,
                    "homePlayer": pending_home["name"],
                    "homeSlug": pending_home["slug"],
                    "awayPlayer": name,
                    "awaySlug": slug,
                    "homeSetsWon": home_sets,
                    "awaySetsWon": away_sets,
                    "homeScore": home_scores[0] if home_scores else None,
                    "awayScore": away_scores[0] if away_scores else None,
                    "periodScores": period_scores,
                    "fetchedAt": fetched_at,
                })
                pending_home = None
            else:
                # Away row with no pending home — orphan, skip
                pending_home = None

        if dump_html:
            dump_path = DATA / "matches" / f"debug-{mode}.html"
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            dump_path.write_text(await page.content(), encoding="utf-8")
            print(f"[DEBUG] Full page HTML saved → {dump_path}")

        await browser.close()
        return matches

def cmd_matches(mode: str):
    dump_html = "--dump" in sys.argv
    matches = asyncio.run(scrape_scores_async(mode, dump_html=dump_html))
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
    elif cmd == "itf":
        mode = sys.argv[2] if len(sys.argv) > 2 else "live"
        cmd_itf(mode)
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
