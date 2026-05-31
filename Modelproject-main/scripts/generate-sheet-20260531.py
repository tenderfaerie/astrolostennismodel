"""
Generate AstroTennis PrizePicks Projection Sheet — May 31 2026
Roland Garros, Day 8 — Rounds of 16 & Doubles QF
"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AstroTennis · May 31 2026 · Roland Garros</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');

  :root {
    --navy:   #0a0f1e;
    --deep:   #111827;
    --card:   #1a2035;
    --border: #1f2d4a;
    --gold:   #f5c842;
    --green:  #22c55e;
    --red:    #ef4444;
    --blue:   #38bdf8;
    --purple: #a78bfa;
    --clay:   #c87941;
    --text:   #e2e8f0;
    --muted:  #64748b;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--navy);
    color: var(--text);
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 11px;
    line-height: 1.45;
    padding: 16px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* ── HEADER ── */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 2px solid var(--gold);
    padding-bottom: 10px;
    margin-bottom: 14px;
  }
  .brand { display: flex; align-items: center; gap: 10px; }
  .logo { font-size: 22px; font-weight: 900; color: var(--gold); letter-spacing: -0.5px; }
  .logo span { color: var(--blue); }
  .tagline { color: var(--muted); font-size: 9.5px; letter-spacing: 0.5px; text-transform: uppercase; }
  .meta { text-align: right; }
  .meta .date { font-size: 13px; font-weight: 700; color: var(--gold); }
  .meta .event { color: var(--clay); font-weight: 600; font-size: 10px; letter-spacing: 0.3px; }

  /* ── CONFIDENCE PILLS ── */
  .pill {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 99px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
  }
  .pill-high   { background: #14532d; color: var(--green); border: 1px solid var(--green); }
  .pill-mid    { background: #1e3a5f; color: var(--blue);  border: 1px solid var(--blue); }
  .pill-over   { color: var(--green); font-weight: 700; }
  .pill-under  { color: var(--red);   font-weight: 700; }
  .pill-bait   { background: #450a0a; color: #fca5a5; border: 1px solid #ef4444; font-size: 8px; padding: 1px 5px; }

  /* ── SECTION LABEL ── */
  .section-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 12px 0 6px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted);
  }
  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  /* ── PICKS TABLE ── */
  .picks-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 6px;
  }
  .picks-table th {
    background: var(--deep);
    color: var(--muted);
    font-size: 8.5px;
    font-weight: 600;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    padding: 5px 8px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  .picks-table td {
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
  .picks-table tr:hover td { background: rgba(255,255,255,0.02); }
  .picks-table tr.high-row td { border-left: 2px solid var(--green); }
  .picks-table tr.mid-row  td { border-left: 2px solid var(--blue); }

  .rank { color: var(--muted); font-size: 10px; font-weight: 600; }
  .player { font-weight: 700; color: var(--text); font-size: 11px; }
  .opponent { color: var(--muted); font-size: 9.5px; }
  .stat-label { font-size: 10px; color: var(--blue); font-weight: 600; }
  .line-val { font-size: 13px; font-weight: 900; font-family: 'Courier New', monospace; }
  .proj-val { font-size: 11px; font-weight: 600; }
  .edge-val { font-size: 10px; font-weight: 700; }
  .edge-pos { color: var(--green); }
  .edge-neg { color: var(--red); }
  .note-text { color: var(--muted); font-size: 9px; max-width: 220px; }

  /* ── SLIPS ── */
  .slips-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 10px;
  }
  .slip-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
  }
  .slip-card.fire { border-color: var(--green); }
  .slip-card.smart { border-color: var(--blue); }
  .slip-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .slip-title { font-size: 11px; font-weight: 700; }
  .slip-legs { font-size: 9px; color: var(--muted); background: var(--deep); padding: 2px 6px; border-radius: 4px; }
  .slip-leg {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
  }
  .slip-leg:last-child { border-bottom: none; }
  .slip-dir { font-size: 9px; font-weight: 800; width: 40px; text-align: center; padding: 2px 4px; border-radius: 3px; }
  .slip-dir.over  { background: #14532d; color: var(--green); }
  .slip-dir.under { background: #450a0a; color: #fca5a5; }
  .slip-player { font-weight: 600; font-size: 10px; flex: 1; }
  .slip-stat { color: var(--muted); font-size: 9px; }
  .slip-line { font-size: 10px; font-weight: 700; color: var(--gold); font-family: monospace; }

  .slip-footer {
    margin-top: 8px;
    font-size: 9px;
    color: var(--muted);
    padding-top: 6px;
    border-top: 1px solid var(--border);
  }
  .slip-footer strong { color: var(--green); }

  /* ── DISCLAIMER ── */
  .disclaimer {
    margin-top: 14px;
    padding: 8px 12px;
    background: var(--deep);
    border-left: 3px solid var(--gold);
    font-size: 8.5px;
    color: var(--muted);
    border-radius: 0 4px 4px 0;
  }

  /* ── PRINT ── */
  @media print {
    body { padding: 8px; background: #fff; color: #000; }
    .navy, .deep, .card { background: #fff !important; }
  }
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div class="brand">
    <div>
      <div class="logo">Astro<span>Tennis</span></div>
      <div class="tagline">Surface-Adjusted Prop Projections</div>
    </div>
  </div>
  <div class="meta">
    <div class="date">May 31, 2026</div>
    <div class="event">🧱 Roland Garros — Clay · R16 + Doubles QF</div>
  </div>
</div>

<!-- HIGH CONFIDENCE PICKS -->
<div class="section-label">⭐ High Confidence Picks</div>
<table class="picks-table">
  <thead>
    <tr>
      <th>#</th>
      <th>Player</th>
      <th>Prop</th>
      <th>Dir</th>
      <th>Line</th>
      <th>Projection</th>
      <th>Edge</th>
      <th>Conf</th>
      <th>Rationale</th>
    </tr>
  </thead>
  <tbody>

    <tr class="high-row">
      <td class="rank">1</td>
      <td><span class="player">Zachary Svajda</span><br><span class="opponent">vs Flavio Cobolli</span></td>
      <td class="stat-label">Total Games Won</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">13.5</td>
      <td class="proj-val">8.6</td>
      <td class="edge-val edge-neg">−4.9</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Cobolli (ITA, clay specialist) dominates. Svajda is an American with limited clay pedigree. Expected 6-2 6-1 6-2. Svajda projection: 8–9 games won.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">2</td>
      <td><span class="player">Flavio Cobolli</span><br><span class="opponent">vs Zachary Svajda</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">32.5</td>
      <td class="proj-val">25.8</td>
      <td class="edge-val edge-neg">−6.7</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">3-set blowout. 6-3 6-2 6-2 = 24 total games. Even a competitive 3-setter stays well under 32. Line overestimates Svajda's resistance on clay.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">3</td>
      <td><span class="player">Marta Kostyuk</span><br><span class="opponent">vs Iga Swiatek</span></td>
      <td class="stat-label">Total Games Won</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">9.5</td>
      <td class="proj-val">6.8</td>
      <td class="edge-val edge-neg">−2.7</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Swiatek is historically untouchable at Roland Garros on clay. Even in a "close" Swiatek win of 6-3 6-4, Kostyuk earns only 7 games. Line sets a comfortable ceiling.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">4</td>
      <td><span class="player">Iga Swiatek</span><br><span class="opponent">vs Marta Kostyuk</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">20.5</td>
      <td class="proj-val">18.1</td>
      <td class="edge-val edge-neg">−2.4</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">WTA best-of-3. Swiatek's clay dominance keeps matches short. 6-2 6-3 = 17 games. Needs 3 sets or a very tight 2-setter to clear 21 total games. Unlikely.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">5</td>
      <td><span class="player">Casper Ruud</span><br><span class="opponent">vs Joao Fonseca</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">38.5</td>
      <td class="proj-val">30.4</td>
      <td class="edge-val edge-neg">−8.1</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Ruud is a clay master; Fonseca is a dangerous young gun but not yet at Ruud's level here. A 3-set Ruud win (6-4 6-3 6-4 = 33 games) stays well under. Would need a 5-setter to hit 39.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">6</td>
      <td><span class="player">Joao Fonseca</span><br><span class="opponent">vs Casper Ruud</span></td>
      <td class="stat-label">Total Games Won</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">19.5</td>
      <td class="proj-val">12.1</td>
      <td class="edge-val edge-neg">−7.4</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Fonseca loses in 3 sets; he wins roughly 10-12 games max in that scenario. Would need to steal 2 sets from Ruud on clay to reach 20. Model and matchup both say UNDER.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">7</td>
      <td><span class="player">Alexander Zverev</span><br><span class="opponent">vs Jesper De Jong</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">30.5</td>
      <td class="proj-val">24.6</td>
      <td class="edge-val edge-neg">−5.9</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Zverev (#3 seed, elite clay) vs De Jong (~#80). 3-set dominant win expected. 6-2 6-2 6-3 = 25 games. Even a solid 3-setter like 6-4 6-3 6-3 = 29. Enormous edge.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">8</td>
      <td><span class="player">Naomi Osaka</span><br><span class="opponent">vs Aryna Sabalenka</span></td>
      <td class="stat-label">Total Games Won</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">8.5</td>
      <td class="proj-val">6.4</td>
      <td class="edge-val edge-neg">−2.1</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Sabalenka is playing elite-level clay tennis. Osaka has shown inconsistency on clay and struggles to hold against powerful baseliners. 6-3 6-2 leaves Osaka with just 5 games.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">9</td>
      <td><span class="player">Mirra Andreeva</span><br><span class="opponent">vs Jil Teichmann</span></td>
      <td class="stat-label">Fantasy Score</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">22.0</td>
      <td class="proj-val">24.3</td>
      <td class="edge-val edge-pos">+2.3</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Andreeva (#5 WTA) is a clay-reared specialist with aggressive return game. Teichmann prefers grass/fast hard. On clay, Andreeva wins comfortably — games won, BPW, and ace accumulation all push her score above 22.</td>
    </tr>

    <tr class="high-row">
      <td class="rank">10</td>
      <td><span class="player">Marta Kostyuk</span><br><span class="opponent">vs Iga Swiatek</span></td>
      <td class="stat-label">Break Points Won</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">3.5</td>
      <td class="proj-val">2.0</td>
      <td class="edge-val edge-neg">−1.5</td>
      <td><span class="pill pill-high">HIGH</span></td>
      <td class="note-text">Swiatek's serve hold rate on clay is elite (~89%). Kostyuk rarely reaches 4+ break points won in any match, let alone against the best clay player alive. Projection: 1-2 BPW.</td>
    </tr>

  </tbody>
</table>

<!-- MEDIUM CONFIDENCE PICKS -->
<div class="section-label">📊 Medium Confidence Picks</div>
<table class="picks-table">
  <thead>
    <tr>
      <th>#</th>
      <th>Player</th>
      <th>Prop</th>
      <th>Dir</th>
      <th>Line</th>
      <th>Projection</th>
      <th>Edge</th>
      <th>Conf</th>
      <th>Rationale</th>
    </tr>
  </thead>
  <tbody>

    <tr class="mid-row">
      <td class="rank">11</td>
      <td><span class="player">Jil Teichmann</span><br><span class="opponent">vs Mirra Andreeva</span></td>
      <td class="stat-label">Total Games Won</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">6.5</td>
      <td class="proj-val">5.1</td>
      <td class="edge-val edge-neg">−1.4</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Pairs with #9. If Andreeva wins 6-2 6-2, Teichmann earns 4 games. Even 6-3 6-3 = 6 games. The 6.5 ceiling is reachable only if Teichmann takes a set.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">12</td>
      <td><span class="player">Flavio Cobolli</span><br><span class="opponent">vs Zachary Svajda</span></td>
      <td class="stat-label">Fantasy Score</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">28.5</td>
      <td class="proj-val">31.2</td>
      <td class="edge-val edge-pos">+2.7</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">3-set dominant win on home clay. Cobolli accumulates games won (18+), aces (8-10), and set wins efficiently. Line assumes a tight match that the model doesn't project here.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">13</td>
      <td><span class="player">Matteo Berrettini</span><br><span class="opponent">vs Juan M. Cerundolo</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">38.5</td>
      <td class="proj-val">41.0</td>
      <td class="edge-val edge-pos">+2.5</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Berrettini vs Cerundolo is a coin-flip. Two clay baseline warriors with nearly identical winPcts. Models project 4-5 sets highly likely. 5-set match averages ~46 games; even 4-sets = ~40.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">14</td>
      <td><span class="player">Matteo Berrettini</span><br><span class="opponent">vs Juan M. Cerundolo</span></td>
      <td class="stat-label">Total Tie Breaks</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">0.5</td>
      <td class="proj-val">1.1</td>
      <td class="edge-val edge-pos">+0.6</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">In a tight 4-5 set clay battle, at least 1 tiebreak is highly probable. Model projects closeness in 2+ sets where neither player clearly dominates. At 0.5, this is nearly a coin-flip even without the edge.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">15</td>
      <td><span class="player">Rafael Jodar</span><br><span class="opponent">vs Pablo Carreno Busta</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">35.5</td>
      <td class="proj-val">38.1</td>
      <td class="edge-val edge-pos">+2.6</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Two Spanish clay specialists — Jodar (#29) rising, Carreno Busta the wily veteran. Competitive from the first game. 4-set match (avg ~38 games) is the base case. 3-set marathon also clears 35.5 if games are close.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">16</td>
      <td><span class="player">Mirra Andreeva</span><br><span class="opponent">vs Jil Teichmann</span></td>
      <td class="stat-label">Break Points Won</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">5.0</td>
      <td class="proj-val">5.9</td>
      <td class="edge-val edge-pos">+0.9</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Andreeva's aggressive return game exploits Teichmann's average clay serve. Teichmann's break-point save rate drops on slow clay. Andreeva consistently creates and converts 5+ BPW against weaker clay servers.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">17</td>
      <td><span class="player">Andrey Rublev</span><br><span class="opponent">vs Jakub Mensik</span></td>
      <td class="stat-label">Aces</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">9.5</td>
      <td class="proj-val">6.8</td>
      <td class="edge-val edge-neg">−2.7</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Clay dramatically suppresses ace rates vs hard courts. Rublev averages 5-7 aces per match on clay. The 9.5 line appears priced off hard-court data. Even in 5 sets, clay gives Rublev very few free points on serve.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">18</td>
      <td><span class="player">Madison Keys</span><br><span class="opponent">vs Diana Shnaider</span></td>
      <td class="stat-label">Fantasy Score</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">16.0</td>
      <td class="proj-val">13.8</td>
      <td class="edge-val edge-neg">−2.2</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Shnaider (#16 WTA) is the better clay mover right now. Keys has a big serve but struggles to accumulate games on slow clay against heavy topspin. If Keys loses in 2 sets, her fantasy score craters below 12. The 16.0 line prices in a competitive Keys win that may not come.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">19</td>
      <td><span class="player">Aryna Sabalenka</span><br><span class="opponent">vs Naomi Osaka</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-under">UNDER</span></td>
      <td class="line-val">20.5</td>
      <td class="proj-val">18.3</td>
      <td class="edge-val edge-neg">−2.2</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Sabalenka dominates when hitting well. WTA best-of-3. 6-3 6-2 = 17 total games; 6-4 6-3 = 19. To clear 20.5 requires a close 3-set match or Osaka having an elite day on clay — both unlikely.</td>
    </tr>

    <tr class="mid-row">
      <td class="rank">20</td>
      <td><span class="player">Elina Svitolina</span><br><span class="opponent">vs Belinda Bencic</span></td>
      <td class="stat-label">Total Games</td>
      <td><span class="pill-over">OVER</span></td>
      <td class="line-val">21.5</td>
      <td class="proj-val">23.4</td>
      <td class="edge-val edge-pos">+1.9</td>
      <td><span class="pill pill-mid">MID</span></td>
      <td class="note-text">Both players are fighters returning from long absences — Svitolina from maternity leave, Bencic the same. Neither dominates on clay. Model projects a competitive 3-setter; even a close 2-setter 7-5 6-4 = 22 games clears the line.</td>
    </tr>

  </tbody>
</table>

<!-- SLIPS -->
<div class="section-label">🎯 Suggested Slips</div>
<div class="slips-grid">

  <!-- 3-LEG SLIP A -->
  <div class="slip-card fire">
    <div class="slip-header">
      <div class="slip-title">🔥 Dominance Card</div>
      <div class="slip-legs">3-Leg Power Play</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Zachary Svajda</div>
        <div class="slip-stat">Total Games Won</div>
      </div>
      <div class="slip-line">13.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Marta Kostyuk</div>
        <div class="slip-stat">Total Games Won</div>
      </div>
      <div class="slip-line">9.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Naomi Osaka</div>
        <div class="slip-stat">Total Games Won</div>
      </div>
      <div class="slip-line">8.5</div>
    </div>
    <div class="slip-footer">
      All three favorites (Cobolli, Swiatek, Sabalenka) are heavy clay-surface operators. <strong>Avg edge: −3.2 games per prop.</strong>
    </div>
  </div>

  <!-- 3-LEG SLIP B -->
  <div class="slip-card smart">
    <div class="slip-header">
      <div class="slip-title">🧠 Clean UNDER Card</div>
      <div class="slip-legs">3-Leg Totals</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Iga Swiatek</div>
        <div class="slip-stat">Total Games</div>
      </div>
      <div class="slip-line">20.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Casper Ruud</div>
        <div class="slip-stat">Total Games</div>
      </div>
      <div class="slip-line">38.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Flavio Cobolli</div>
        <div class="slip-stat">Total Games</div>
      </div>
      <div class="slip-line">32.5</div>
    </div>
    <div class="slip-footer">
      Three dominant players expected to end their matches quickly on clay. <strong>Combined projection edge: −17.2 total games.</strong>
    </div>
  </div>

  <!-- 4-LEG SLIP A -->
  <div class="slip-card fire">
    <div class="slip-header">
      <div class="slip-title">💎 Premium 4-Leg Power</div>
      <div class="slip-legs">4-Leg Flex</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Svajda TGW &amp; Zverev TG</div>
        <div class="slip-stat">Games Won / Total Games</div>
      </div>
      <div class="slip-line">13.5 / 30.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Marta Kostyuk</div>
        <div class="slip-stat">Total Games Won</div>
      </div>
      <div class="slip-line">9.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Casper Ruud</div>
        <div class="slip-stat">Total Games</div>
      </div>
      <div class="slip-line">38.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir over">OVER</div>
      <div>
        <div class="slip-player">Mirra Andreeva</div>
        <div class="slip-stat">Fantasy Score</div>
      </div>
      <div class="slip-line">22.0</div>
    </div>
    <div class="slip-footer">
      Top-4 highest-confidence picks in one slip. <strong>All 4 backed by both model and clay-surface context.</strong>
    </div>
  </div>

  <!-- 4-LEG SLIP B -->
  <div class="slip-card smart">
    <div class="slip-header">
      <div class="slip-title">🌀 Contrarian Angle</div>
      <div class="slip-legs">4-Leg Mixed</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir over">OVER</div>
      <div>
        <div class="slip-player">Matteo Berrettini</div>
        <div class="slip-stat">Total Games</div>
      </div>
      <div class="slip-line">38.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir over">OVER</div>
      <div>
        <div class="slip-player">Berrettini Tie Breaks</div>
        <div class="slip-stat">Total Tie Breaks</div>
      </div>
      <div class="slip-line">0.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir over">OVER</div>
      <div>
        <div class="slip-player">Rafael Jodar</div>
        <div class="slip-stat">Total Games</div>
      </div>
      <div class="slip-line">35.5</div>
    </div>
    <div class="slip-leg">
      <div class="slip-dir under">UNDER</div>
      <div>
        <div class="slip-player">Madison Keys</div>
        <div class="slip-stat">Fantasy Score</div>
      </div>
      <div class="slip-line">16.0</div>
    </div>
    <div class="slip-footer">
      Two competitive long matches + one player fade. Higher risk, higher reward — best as a <strong>small-unit flex entry.</strong>
    </div>
  </div>

</div>

<!-- DISCLAIMER -->
<div class="disclaimer">
  <strong>AstroTennis Proprietary Projections</strong> — All projections are generated by the AstroTennis surface-adjusted prop model using clay-weighted win rates, ace/DF profiles, and matchup-adjusted game expectation formulas.
  Projections are not guarantees of outcome. Tennis matches contain inherent variance. Play responsibly and within your means.
  For AstroTennis subscribers only. Do not distribute.
</div>

</body>
</html>
"""

import os
out = os.path.join(os.path.dirname(__file__), '..', 'AstroTennis_Sheet_20260531.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f"Sheet written → {os.path.abspath(out)}")
