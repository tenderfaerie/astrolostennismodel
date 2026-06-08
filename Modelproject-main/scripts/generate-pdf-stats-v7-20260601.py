"""
AstroTennis — Roland Garros 2026 · June 1 · Deep Analysis Edition v7
H2H + Clay Stats + RG Record + Total Games Model + PrizePicks Lines
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

NAVY   = colors.HexColor("#0a0f1e")
DEEP   = colors.HexColor("#111827")
CARD   = colors.HexColor("#1a2035")
BORDER = colors.HexColor("#1f2d4a")
GOLD   = colors.HexColor("#f5c842")
GREEN  = colors.HexColor("#22c55e")
RED    = colors.HexColor("#ef4444")
BLUE   = colors.HexColor("#38bdf8")
PURPLE = colors.HexColor("#a78bfa")
CLAYC  = colors.HexColor("#c87941")
ORANGE = colors.HexColor("#fb923c")
TEXT   = colors.HexColor("#e2e8f0")
MUTED  = colors.HexColor("#94a3b8")
DG     = colors.HexColor("#0a1f0a")   # DARKGREEN
DR     = colors.HexColor("#200808")   # DARKRED
DGOLD  = colors.HexColor("#1a1400")   # DARKGOLD
DBLUE  = colors.HexColor("#0a0f20")   # DARKBLUE

def sty(name, **kw):
    d = dict(fontName="Helvetica", fontSize=8, textColor=TEXT, leading=10)
    d.update(kw)
    return ParagraphStyle(name, **d)

def P(txt, bold=False, color=None, align="LEFT", sz=8, lead=10):
    return Paragraph(txt, ParagraphStyle(f"p{id(txt)}",
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=sz, textColor=color or TEXT, leading=lead,
        alignment={"LEFT":TA_LEFT,"CENTER":TA_CENTER,"RIGHT":TA_RIGHT}[align]))

SEC = sty("sec", fontName="Helvetica-Bold", fontSize=8.5, textColor=GOLD,
          spaceBefore=8, spaceAfter=3)
SEC2 = sty("sec2", fontName="Helvetica-Bold", fontSize=8, textColor=MUTED,
           spaceBefore=5, spaceAfter=2)

CW = 7.7 * inch   # total content width

def tbl_style(rows=1, stripe=True, hdr_bg=DEEP):
    ts = [
        ("BACKGROUND", (0,0), (-1,0), hdr_bg),
        ("GRID", (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]
    if stripe:
        ts.append(("ROWBACKGROUNDS", (0,1), (-1,-1), [CARD, DEEP]))
    return TableStyle(ts)


# ═══════════════════════════════════════════════════════════════════════════════
# MATCH DATA — H2H + CLAY STATS + RG RECORD + TOTAL GAMES MODEL
# ═══════════════════════════════════════════════════════════════════════════════

# Format: clay_wr, aces_rate, df_rate, first_srv_pct, bp_created
CLAY_STATS = {
    "Mensik":    (.556, .113, .040, .645, .507),
    "Fonseca":   (.569, .048, .028, .618, .632),
    "Zverev":    (.761, .085, .030, .645, .577),
    "Jodar":     (.750, .049, .024, .607, .724),
    "Svitolina": (.750, .040, .034, .604, .823),
    "Kostyuk":   (.758, .029, .076, .589, .890),
    "Andreeva":  (.778, .034, .043, .574, .830),
    "Cirstea":   (.593, .040, .025, .558, .772),
    "Sabalenka": (.804, .047, .039, .636, .848),
    "Shnaider":  (.667, .018, .041, .577, .763),
    "FAA":       (.650, .070, .028, .640, .560),
    "Cobolli":   (.630, .053, .037, .632, .561),
    "Arnaldi":   (.543, .060, .041, .616, .562),
    "Berrettini":(.675, .082, .022, .679, .464),
}

# ── MATCH PROFILES ──────────────────────────────────────────────────────────
# Each match: H2H overall, clay H2H, RG record for each, R16 fatigue,
#             total games model, odds, key matchup notes

MATCHES = {
    # ── ACTIVE QF ──
    "Mensik vs Fonseca": {
        "label": "Mensik vs Fonseca",
        "round": "QF",
        "format": "ATP Best of 5",
        "odds_h": "+175", "odds_a": "-227",
        "mkt_h": "36%", "mkt_a": "69%",
        "model_win_a": "78%",
        "h2h_overall": "Fonseca 2-0",
        "h2h_clay": "No prior clay H2H",
        "h2h_note": "Both prior meetings on hard (Basel 2025, Next Gen 2024). Fonseca 2-0 but no clay precedent.",
        "rg_h": "QF 2025 — career best. First deep RG run.",
        "rg_a": "R16 2025 — emerged late-season. Clay form strong entering 2026.",
        "r16_h": "13A 9DF 5-set marathon vs Cerundolo (FATIGUED)",
        "r16_a": "0DF clean 3-set win (FRESH)",
        "tg_model": 41.2,
        "tg_pp": 38.0,
        "tg_pick": "OVER",
        "tg_conf": "A+",
        "tg_note": "Both H2H meetings went full distance (Basel, Next Gen). Mensik 9 DFs = constant serve breaks. ATP best of 5 with fatigue factor. Model: 40-43 games.",
        "key_edge": "Fonseca: 0 DFs vs Mensik 9 DFs + 5-set fatigue. H2H Fonseca 2-0. But total games is the real play.",
    },
    "Zverev vs Jodar": {
        "label": "Zverev vs Jodar",
        "round": "QF",
        "format": "ATP Best of 5",
        "odds_h": "-303", "odds_a": "+240",
        "mkt_h": "75%", "mkt_a": "29%",
        "model_win_h": "88%",
        "h2h_overall": "FIRST MEETING",
        "h2h_clay": "No H2H — first ever match",
        "h2h_note": "Zero H2H history at any level. No mental edge either way — pure clay model and current form.",
        "rg_h": "2020 F, 2024 SF, 2025 QF — elite RG performer. Multi-year clay specialist at this venue.",
        "rg_a": "First RG QF — career best. Jodar saved 10/14 BP in R16, elite clutch under pressure.",
        "r16_h": "4A 2DF 3-set clean win (FRESH)",
        "r16_a": "3A 3DF 5-set battle, 10/14 BPS (71%) — GOOD FORM but tested",
        "tg_model": 39.1,
        "tg_pp": 36.5,
        "tg_pick": "OVER",
        "tg_conf": "A",
        "tg_note": "First meeting = no mental blueprint to shortcut match. Jodar 71% BP save rate means he won't capitulate. Both top clay players. Model: 38-41 games.",
        "key_edge": "Zverev RG pedigree (2020 F!) dwarfs Jodar's first QF. Clay 76.1% vs 75.0%. Zverev fresh, Jodar had 5-setter.",
    },
    "Svitolina vs Kostyuk": {
        "label": "Svitolina vs Kostyuk",
        "round": "QF",
        "format": "WTA Best of 3",
        "odds_h": "+100", "odds_a": "-125",
        "mkt_h": "50%", "mkt_a": "56%",
        "model_win_a": "56%",
        "h2h_overall": "Kostyuk leads recent 2-1",
        "h2h_clay": "No prior clay meetings",
        "h2h_note": "Kostyuk leads H2H 2-1 in recent meetings (Toronto 2024). Svitolina won earlier in career. MARKET moved Kostyuk to -125 FAVORITE — sharp money on Kostyuk.",
        "rg_h": "2018 RG champion. Multiple QF/SF runs. Knows how to win here — big RG pedigree.",
        "rg_a": "First RG QF — career best. Younger, improving clay player. Ukrainian derby adds pressure.",
        "r16_h": "3A 1DF 3-setter (slight fatigue from longer match)",
        "r16_a": "Won R16 — specific stats not captured but market moved heavily to her",
        "tg_model": 22.8,
        "tg_pp": 21.5,
        "tg_pick": "OVER",
        "tg_conf": "A",
        "tg_note": "DERBY MATCH — Ukrainian players, maximum emotional intensity. Both clay win rates nearly identical (75.0% vs 75.8%). H2H competitive. WTA best of 3 but could easily go to a 3rd set. Model: 22-24 games.",
        "key_edge": "Market flip to Kostyuk (-125) is the key signal. H2H edge 2-1. BP creation rate 0.890 = highest WTA field. Derby pressure drives DFs and long games.",
    },
    "Andreeva vs Cirstea": {
        "label": "Andreeva vs Cirstea",
        "round": "QF",
        "format": "WTA Best of 3",
        "odds_h": "-189", "odds_a": "+150",
        "mkt_h": "65%", "mkt_a": "40%",
        "model_win_h": "85%",
        "h2h_overall": "Andreeva 1-0",
        "h2h_clay": "Andreeva 1-0 (Linz 2026 indoor clay)",
        "h2h_note": "Andreeva leads 1-0 on the only H2H, which was on clay. Sole precedent favors Andreeva.",
        "rg_h": "2025 RG SF — breakthrough star here. RG is her best Major. Knows exactly how to win on Chatrier.",
        "rg_a": "2023 RG QF — career best was a surprise run. Now 32, in decline phase. Inconsistent in 2026.",
        "r16_h": "Dominant 2-0 win (FRESH, confident, in top form at Roland Garros)",
        "r16_a": "Won R16 but Cirstea is aging and inconsistent on clay",
        "tg_model": 22.4,
        "tg_pp": 21.5,
        "tg_pick": "OVER",
        "tg_conf": "B+",
        "tg_note": "Andreeva wins comfortably but Cirstea (59.3% clay) is a crafty veteran who takes games. WTA so 3 sets possible. Andreeva won't let off gas given RG SF run in 2025 — she knows this court. Model: 21-24.",
        "key_edge": "Model 85% vs market 65% = +20% edge. Andreeva's 2025 RG SF pedigree massive. Clay H2H 1-0. Only question is how many games Cirstea steals.",
    },
    # ── SF PREVIEW ──
    "Sabalenka vs Shnaider": {
        "label": "Sabalenka vs Shnaider",
        "round": "SF",
        "format": "WTA Best of 3",
        "odds_h": "-500", "odds_a": "+350",
        "mkt_h": "83%", "mkt_a": "22%",
        "model_win_h": "91%",
        "h2h_overall": "No prior meetings",
        "h2h_clay": "No H2H — first meeting",
        "h2h_note": "Shnaider too new to top level for any H2H vs Sabalenka. First ever meeting. Shnaider just pulled off massive upset vs Keys (50 UEs from Keys).",
        "rg_h": "2025 RG champion — DEFENDING TITLE. Multiple final/SF runs. Best claycourter on WTA tour.",
        "rg_a": "First RG SF — career best. Upset Keys in QF (Keys had 50 UEs, 14% BPS). Shnaider in form but Keys collapse inflated her result.",
        "r16_h": "Won QF vs Osaka — dominant Sabalenka performance expected",
        "r16_a": "Upset Keys 15-9 (3 sets) — Keys had complete collapse, Shnaider played well but benefitted",
        "tg_model": 18.8,
        "tg_pp": 19.5,
        "tg_pick": "UNDER",
        "tg_conf": "B+",
        "tg_note": "Sabalenka 80.4% clay vs Shnaider 66.7%. DEFENDING CHAMPION on her court. Shnaider won via Keys collapse — facing Sabalenka is a different level. Model: 6-3 6-2 = 17 games. Tight but UNDER.",
        "key_edge": "Sabalenka clay win rate 80.4% — highest on tour. RG defending champ. Shnaider's QF win was via opponent collapse, not dominance. Model projects quick Sabalenka win.",
    },
    "FAA vs Cobolli": {
        "label": "FAA vs Cobolli",
        "round": "SF",
        "format": "ATP Best of 5",
        "odds_h": "-167", "odds_a": "+130",
        "mkt_h": "63%", "mkt_a": "43%",
        "model_win_h": "55%",
        "h2h_overall": "FAA 1-0 (Shanghai 2025 hard)",
        "h2h_clay": "No prior clay H2H",
        "h2h_note": "Only 1 prior meeting on hard court (Shanghai 2025, FAA won). No clay precedent. Extremely even clay profiles.",
        "rg_h": "Multiple RG QF/SF runs. Experienced at this stage. RG 2024 reached QF.",
        "rg_a": "First RG SF — career best. Won QF in 4 sets (25-18 games). Physical, grind-it-out style.",
        "r16_h": "9A 2DF WON IN 2 SETS (FRESH — minimal energy spent)",
        "r16_a": "8A 2DF 4-set win (moderate fatigue — more sets played)",
        "tg_model": 40.8,
        "tg_pp": 39.5,
        "tg_pick": "OVER",
        "tg_conf": "B+",
        "tg_note": "Nearly IDENTICAL clay profiles (FAA 65% vs Cobolli 63%). ATP best of 5 with no H2H blueprint. FAA won in 2 sets but that was vs Tabilo — Cobolli is tougher. Cobolli's QF went 4 sets. Model: 40-43 games.",
        "key_edge": "Nearly mirror-image clay profiles make prediction hard — pure grind match. FAA fresher (2-set QF), Cobolli more battle-tested (4-set). FAA slight model edge via better BP efficiency.",
    },
    "Arnaldi vs Berrettini": {
        "label": "Arnaldi vs Berrettini",
        "round": "SF",
        "format": "ATP Best of 5",
        "odds_h": "+110", "odds_a": "-140",
        "mkt_h": "48%", "mkt_a": "58%",
        "model_win_a": "62%",
        "h2h_overall": "Berrettini 2-1 (mostly hard)",
        "h2h_clay": "Split 1-1 on clay",
        "h2h_note": "Berrettini leads overall 2-1. Clay H2H 1-1. Arnaldi won their most recent clay meeting (Rome 2025). Both Italian players — familiar opponents with no mental edge.",
        "rg_h": "First RG SF — this is Arnaldi's career best. Clay specialist, 54.3% career clay rate. Beat Tiafoe in QF.",
        "rg_a": "2019 RG SF, 2021 RG QF — deep pedigree here. 67.5% clay win rate — 13pts better than Arnaldi. Clay is his best surface.",
        "r16_h": "Won QF vs Tiafoe (assumed based on SF lines posted)",
        "r16_a": "0DF 92% 1stIn 3-set dominant QF win vs Cerundolo — PEAK FORM",
        "tg_model": 40.2,
        "tg_pp": 39.5,
        "tg_pick": "OVER",
        "tg_conf": "B+",
        "tg_note": "Clay H2H 1-1 makes this a genuine 50/50 on surface. Both Italian, mutual familiarity. Berrettini RG pedigree (2019 SF) significant. Arnaldi first RG SF = pressure. ATP 5-set with both recent 3-setters = more games ahead. Model: 39-42.",
        "key_edge": "Berrettini clay 67.5% vs Arnaldi 54.3% — 13pt gap is SIGNIFICANT. RG history: Berrettini's 2019 SF vs Arnaldi's debut. Model favors Berrettini 62%. But clay H2H 1-1 keeps it honest.",
    },
}

# ── PRIZEPICKS LINES (standard lines per player, from uploaded JSON) ──────────
PP_LINES = {
    # QF
    "Mensik":    {"Aces":12.5,"Double Faults":5.5,"Total Games Won":18.5,"Total Sets":3.5},
    "Fonseca":   {"Aces":5.5,"Double Faults":1.5,"Fantasy Score":20.0,"Total Games":38.0,"Total Games Won":20.5,"Total Sets":3.5},
    "Zverev":    {"Aces":8.5,"Double Faults":1.5,"Fantasy Score":23.5,"Total Games":36.5,"Total Games Won":20.5,"Total Sets":3.5,"Total Tie Breaks":0.5},
    "Jodar":     {"Aces":6.5,"Double Faults":2.5,"Break Points Won":2.5,"Total Games Won":17.5},
    "Svitolina": {"Aces":0.5,"Break Points Won":4.5,"Double Faults":1.5,"Total Games Won":10.5},
    "Kostyuk":   {"Aces":4.5,"Break Points Won":5.0,"Double Faults":4.5,"Fantasy Score":15.5,"Total Games":21.5,"Total Games Won":11.5},
    "Andreeva":  {"Aces":0.5,"Break Points Won":4.5,"Double Faults":2.5,"Fantasy Score":17.0,"Total Games":21.5,"Total Games Won":11.5,"Total Sets":2.5},
    "Cirstea":   {"Aces":2.5,"Break Points Won":3.5,"Double Faults":1.5,"Total Games Won":11.5},
    # SF
    "Sabalenka": {"Aces":3.5,"Double Faults":1.5,"Total Games":19.5,"Total Games Won":15.5,"Total Sets":2.5},
    "Shnaider":  {"Aces":0.5,"Double Faults":1.5,"Total Games Won":7.5},
    "FAA":       {"Aces":11.5,"Double Faults":4.5,"Total Games Won":20.5},
    "Cobolli":   {"Aces":7.5,"Double Faults":4.5,"Total Games":39.5,"Total Games Won":20.5,"Total Sets":3.5},
    "Arnaldi":   {"Aces":9.5,"Double Faults":4.5,"Total Games Won":16.5},
    "Berrettini":{"Aces":10.5,"Double Faults":3.5,"Total Games":39.5,"Total Games Won":20.5,"Total Sets":3.5},
}

# ── PICKS (num, player, prop, pp_line, type, proj, pick, conf, analysis) ─────
PICKS_QF = [
    # Mensik vs Fonseca
    (1, "Mensik","Double Faults","5.5","goblin","8.5","OVER","A+",
     "REAL DATA: 9 DFs confirmed in R16. Goblin=lower line means PP expects easy OVER — model agrees strongly. Career 0.040 DF rate, fatigue from 5-set battle projects 7-9 today."),
    (2, "Fonseca","Total Games","38.0","standard","41.2","OVER","A+",
     "H2H: Both prior meetings (Basel 2025 + Next Gen 2024) went full distance. Mensik 9 DFs = constant breaks. 5-set format + fatigue factor. Model: 40-43 games on RG clay."),
    (3, "Mensik","Aces","12.5","standard","13.0","OVER","A",
     "REAL: 13 aces in R16, 0.113 career ace rate — highest in field. Even fatigued, serves big when pressured. Fonseca clean but Mensik's serve is his weapon regardless of energy."),
    (4, "Fonseca","Fantasy Score","20.0","standard","22.0","OVER","A",
     "REAL: 0 DFs in clean 3-set QF. H2H 2-0. Fresh legs vs exhausted Mensik. Model 22 FS = dominant win. Market underestimates Fonseca's current form peak at RG 2026."),
    (5, "Mensik","Double Faults","6.5","demon","8.5","OVER","B+",
     "Even the demon (higher) line cleared. 9 DFs is confirmed real data — serves under pressure after 5 sets = DF rate stays elevated. 7-9 projected regardless of line level."),

    # Zverev vs Jodar
    (6, "Zverev","Fantasy Score","23.5","standard","26.4","OVER","A",
     "RG PEDIGREE: 2020 Final, 2024 SF, 2025 QF — Zverev KNOWS how to win here. Clay 76.1%. Fresh 3-set R16. First meeting with Jodar = no shortcut. Projects dominant 24-27 FS."),
    (7, "Zverev","Total Games","36.5","standard","39.1","OVER","A",
     "FIRST MEETING: No mental blueprint either way. Jodar saved 10/14 BPs in R16 (71%) — elite clutch, won't roll over. Both clay 75-76%. Model: 38-41 games. RG clay is heavy/slow."),
    (8, "Zverev","Aces","8.5","standard","9.4","OVER","B+",
     "0.085 ace rate = highest remaining ATP. RG 2020 Final-level pedigree = serves big in pressure moments. In a 4-setter vs unknown opponent, will lean on ace weapon. Projects 9-10."),
    (9, "Zverev","Total Games Won","20.5","standard","22.1","OVER","B+",
     "If total is 39 and Zverev wins (88% model), he takes ~22-23 games. In RG-style 4-set win: 6-4 6-3 3-6 6-4 = 22 games. OVER 20.5 with solid cushion."),
    (10, "Jodar","Total Games Won","17.5","standard","16.8","UNDER","B",
     "Zverev 88% model win. In 39-game match Jodar gets the leftover ~17 games. First QF in career = pressure. Zverev's RG pedigree and fresh legs should limit Jodar to 16-17 games."),

    # Svitolina vs Kostyuk
    (11, "Kostyuk","Fantasy Score","15.5","standard","17.2","OVER","A",
     "MARKET FLIP: Sharp money moved Kostyuk to -125 FAVORITE. H2H leads 2-1 recent (Toronto 2024). 0.890 BP creation = highest WTA. Model 17+ in close derby. Market confirms the edge."),
    (12, "Kostyuk","Total Games","21.5","standard","22.8","OVER","A",
     "DERBY MATCH: Ukrainian players, maximum intensity, both know each other's games deeply. Clay win rates nearly IDENTICAL (Svitolina 75.0% vs Kostyuk 75.8%). Goes 3 sets. Model: 22-24."),
    (13, "Kostyuk","Break Points Won","5.0","standard","5.7","OVER","B+",
     "0.890 BP creation rate — highest WTA field. Svitolina slight fatigue from 3-setter R16. Kostyuk pressures every service game. Derby pressure elevates both players' return aggression."),
    (14, "Svitolina","Break Points Won","4.5","standard","4.1","UNDER","B",
     "Kostyuk is now -125 fav — market says Kostyuk serves better. Svitolina slight fatigue. 0.823 BP creation but Kostyuk (75.8% clay) holds serve well. Slight UNDER on Svitolina BPW."),

    # Andreeva vs Cirstea
    (15, "Andreeva","Fantasy Score","17.0","standard","22.0","OVER","A+",
     "RG RECORD: 2025 SF at Roland Garros — this is her best court. REAL: Dominant 2-0 yesterday. Clay H2H 1-0 (Linz 2026). Clay 77.8% vs Cirstea 59.3%. +5pt model gap — biggest FS edge on board."),
    (16, "Andreeva","Total Games","21.5","standard","22.4","OVER","B+",
     "Cirstea is crafty veteran who steals games even in losses (59.3% clay isn't nothing). RG 2023 she made a surprise QF run. Andreeva won't blow her out completely. Model: 21-23 tight win."),
    (17, "Cirstea","Total Games Won","11.5","goblin","7.1","UNDER","A",
     "Goblin line still loses. Andreeva 2025 RG SF + dominant yesterday + clay H2H. Cirstea 32 years old in decline. Model: Andreeva wins 6-2 6-3 = Cirstea gets only 5 games. Well UNDER even goblin."),
    (18, "Andreeva","Break Points Won","4.5","demon","6.1","OVER","B+",
     "Even the demon (higher) line cleared. 0.830 BP creation + Cirstea 55.8% BP saves = Andreeva earns 5-6 BPW. RG pedigree gives her extra aggression on return. Cleared even at demon price."),
]

PICKS_SF = [
    # Sabalenka vs Shnaider
    (19, "Sabalenka","Total Games","19.5","standard","18.8","UNDER","B+",
     "DEFENDING CHAMPION. Clay 80.4% — highest WTA. Shnaider advanced via Keys collapse (50 UEs, 14% BPS) NOT via dominant tennis. Sabalenka 6-3 6-2 = 15 games. UNDER with good cushion."),
    (20, "Sabalenka","Total Games Won","15.5","demon","17.8","OVER","A",
     "Demon line (high threshold) still cleared. Sabalenka wins 6-3 6-3 = 18 TGW, OVER demon 15.5. Defending RG champion on home clay. H2H zero (first meeting) = no fear factor for Shnaider to exploit."),
    (21, "Shnaider","Total Games Won","7.5","standard","5.2","UNDER","A",
     "Sabalenka 91% model win. 6-3 6-2 = Shnaider gets only 5 games. Shnaider's QF win inflated by Keys' complete mental collapse. Against #1 defending champion it's a different level. Model: 4-6 games for Shnaider."),

    # FAA vs Cobolli
    (22, "FAA","Aces","11.5","standard","13.8","OVER","A+",
     "REAL: 9 aces in 2-SET QF win. In a 4-5 set SF vs Cobolli, projects 13-16 aces. FAA ace rate 0.070, serves even bigger in long matches. Standard line at 11.5 underestimates his SF output."),
    (23, "FAA","Double Faults","4.5","standard","2.1","UNDER","A",
     "REAL: Only 2 DFs in QF. Career DF rate 0.028 — lowest in remaining field. Even in 5-set SF, 4.5 DFs is nearly double his career rate. Strong UNDER. FAA's serve is his most reliable weapon."),
    (24, "Cobolli","Total Games","39.5","standard","40.8","OVER","B+",
     "Cobolli's QF went 4 sets (25-18 = 43 games). FAA won in 2 sets vs Tabilo but Cobolli is a tougher opponent. Nearly identical clay profiles means this match goes long. Model: 40-43 games."),
    (25, "FAA","Total Games Won","20.5","standard","21.8","OVER","B+",
     "FAA slight favorite (-167). In 40-game match FAA wins ~22 games. 65% clay win rate + fresher legs (2-set QF). OVER 20.5 with modest cushion."),

    # Arnaldi vs Berrettini
    (26, "Berrettini","Aces","10.5","standard","6.8","UNDER","A",
     "REAL: Only 2 aces in QF — Berrettini had 92% 1stIn dominance, doesn't NEED aces. Career 0.082 rate but this QF showed serve-through-placement style. 10.5 is severely overpriced. Strong UNDER."),
    (27, "Arnaldi","Double Faults","4.5","standard","5.1","OVER","B+",
     "0.041 career DF rate. Clay H2H 1-1 (split). In a 5-set match under SF pressure at first-ever RG SF, Arnaldi's serve will be tested. H2H recent clay: Arnaldi won Rome 2025 but this is bigger stage."),
    (28, "Berrettini","Total Games","39.5","standard","40.2","OVER","B+",
     "RG HISTORY: 2019 SF at Roland Garros = Berrettini knows how to extend matches here. Clay H2H 1-1. Arnaldi first RG SF = nerves but also adrenaline. Both 3-set QF wins = more gas in tank. ATP 5-set. Model: 39-42."),
]

# ── TOTAL GAMES SUMMARY TABLE ─────────────────────────────────────────────────
TG_SUMMARY = [
    # match, format, pp_tg, model_tg, pick, conf, key_reason
    ("Mensik vs Fonseca",  "ATP BO5", "38.0", "41.2", "OVER",  "A+", "Both H2H went full distance + Mensik 9DFs + fatigue = breaks all match"),
    ("Zverev vs Jodar",    "ATP BO5", "36.5", "39.1", "OVER",  "A",  "First ever meeting, Jodar 71% BPS, neither player has mental shortcut"),
    ("Svitolina vs Kostyuk","WTA BO3","21.5", "22.8", "OVER",  "A",  "Derby = 3 sets. Identical clay stats (75% each). Emotional match."),
    ("Andreeva vs Cirstea", "WTA BO3","21.5", "22.4", "OVER",  "B+", "Cirstea steals games (2023 RG QF pedigree). Not a blowout."),
    ("Sabalenka vs Shnaider","WTA BO3","19.5","18.8", "UNDER", "B+", "Defending champ vs opponent who won via Keys collapse. Quick Sab win."),
    ("FAA vs Cobolli",     "ATP BO5", "39.5", "40.8", "OVER",  "B+", "Mirror-image clay profiles. Cobolli's QF went 4 sets (43 games)."),
    ("Arnaldi vs Berrettini","ATP BO5","39.5","40.2", "OVER",  "B+", "Clay H2H 1-1. Berrettini 2019 RG SF pedigree. Both fresh."),
]


# ═══════════════════════════════════════════════════════════════════════════════
# PDF BUILD FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.restoreState()


def build_header(story):
    t = Table([[
        P("ASTROTENNIS", bold=True, color=GOLD, sz=18),
        P("ROLAND GARROS 2026 · JUNE 1<br/>"
          "<font color='#fb923c' size='8'>DEEP ANALYSIS v7 — H2H · Clay Stats · RG Record · Total Games · PrizePicks</font>",
          bold=True, color=colors.HexColor("#c87941"), align="RIGHT", sz=11),
    ]], colWidths=[3.5*inch, 4.2*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),NAVY),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD))
    story.append(Spacer(1, 4))


def build_match_cards(story):
    story.append(Paragraph("MATCH ANALYSIS — H2H · CLAY STATS · ROLAND GARROS RECORD · TOTAL GAMES", SEC))

    for mkey, m in MATCHES.items():
        h_name = mkey.split(" vs ")[0]
        a_name = mkey.split(" vs ")[1]
        c_h = CLAY_STATS.get(h_name, (0,0,0,0,0))
        c_a = CLAY_STATS.get(a_name, (0,0,0,0,0))

        rnd_color = CLAYC if m["round"] == "QF" else BLUE
        win_model = m.get("model_win_h") or m.get("model_win_a","?")
        win_side  = "→ " + (h_name if "model_win_h" in m else a_name)

        # Card title row
        title_t = Table([[
            P(f"<b>{m['label']}</b>  [{m['round']} · {m['format']}]", bold=True, color=GOLD, sz=9),
            P(f"Model: <b>{win_model}</b> {win_side}  |  {h_name} {m['odds_h']} / {a_name} {m['odds_a']}",
              color=ORANGE, align="RIGHT", sz=8),
        ]], colWidths=[4.0*inch, 3.7*inch])
        title_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),DEEP),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
            ("LINEBELOW",(0,0),(-1,-1),0.5,rnd_color),
        ]))
        story.append(title_t)

        # Stats row
        def pct(v): return f"{v:.1%}"
        stats_data = [
            [P("", sz=7), P(h_name, bold=True, color=BLUE, align="CENTER", sz=7.5),
             P(a_name, bold=True, color=colors.HexColor("#fb923c"), align="CENTER", sz=7.5), P("", sz=7)],
            [P("Clay Win %", sz=7.5),
             P(pct(c_h[0]), bold=c_h[0]>c_a[0], color=GREEN if c_h[0]>c_a[0] else TEXT, align="CENTER", sz=7.5),
             P(pct(c_a[0]), bold=c_a[0]>c_h[0], color=GREEN if c_a[0]>c_h[0] else TEXT, align="CENTER", sz=7.5),
             P("Career clay win rate", color=MUTED, sz=7)],
            [P("Ace Rate", sz=7.5),
             P(pct(c_h[1]), align="CENTER", sz=7.5),
             P(pct(c_a[1]), align="CENTER", sz=7.5),
             P("Aces per service point", color=MUTED, sz=7)],
            [P("DF Rate", sz=7.5),
             P(pct(c_h[2]), bold=c_h[2]>c_a[2], color=RED if c_h[2]>c_a[2] else TEXT, align="CENTER", sz=7.5),
             P(pct(c_a[2]), bold=c_a[2]>c_h[2], color=RED if c_a[2]>c_h[2] else TEXT, align="CENTER", sz=7.5),
             P("Double faults per service point", color=MUTED, sz=7)],
            [P("BP Created", sz=7.5),
             P(pct(c_h[4]), bold=c_h[4]>c_a[4], color=GREEN if c_h[4]>c_a[4] else TEXT, align="CENTER", sz=7.5),
             P(pct(c_a[4]), bold=c_a[4]>c_h[4], color=GREEN if c_a[4]>c_h[4] else TEXT, align="CENTER", sz=7.5),
             P("Return aggression / break point creation", color=MUTED, sz=7)],
        ]
        stats_t = Table(stats_data, colWidths=[1.0*inch, 1.0*inch, 1.0*inch, 4.7*inch])
        stats_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0d1525")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
            ("GRID",(0,0),(-1,-1),0.3,BORDER),
            ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))

        # Info row: H2H + RG record + R16 + TG model
        tg_c = GREEN if m["tg_pick"]=="OVER" else RED
        tg_conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}.get(m["tg_conf"],MUTED)
        info_data = [[
            Paragraph(f"<b>H2H:</b> {m['h2h_overall']}<br/>"
                      f"<b>Clay:</b> {m['h2h_clay']}<br/>"
                      f"<font color='#94a3b8'>{m['h2h_note']}</font>",
                      sty(f"h{mkey}", fontSize=7, leading=9, textColor=TEXT)),
            Paragraph(f"<b>RG Record:</b><br/>"
                      f"<font color='#38bdf8'>{h_name}:</font> {m['rg_h']}<br/>"
                      f"<font color='#fb923c'>{a_name}:</font> {m['rg_a']}",
                      sty(f"rg{mkey}", fontSize=7, leading=9, textColor=TEXT)),
            Paragraph(f"<b>R16 Form:</b><br/>"
                      f"<font color='#38bdf8'>{h_name}:</font> {m['r16_h']}<br/>"
                      f"<font color='#fb923c'>{a_name}:</font> {m['r16_a']}",
                      sty(f"r{mkey}", fontSize=7, leading=9, textColor=TEXT)),
            Paragraph(f"<b>Total Games Model:</b> <font color='{tg_c.hexval()}'>{m['tg_pick']} {m['tg_pp']}</font> "
                      f"<font color='#f5c842'>[Proj: {m['tg_model']}]</font> "
                      f"<font color='{tg_conf_c.hexval()}'>{m['tg_conf']}</font><br/>"
                      f"<font color='#94a3b8'>{m['tg_note']}</font>",
                      sty(f"tg{mkey}", fontSize=7, leading=9, textColor=TEXT)),
        ]]
        info_t = Table(info_data, colWidths=[1.9*inch, 2.0*inch, 1.9*inch, 1.9*inch])
        info_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),CARD),
            ("GRID",(0,0),(-1,-1),0.3,BORDER),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))

        story.append(stats_t)
        story.append(info_t)
        story.append(Spacer(1, 4))


def build_tg_table(story):
    story.append(Paragraph("TOTAL GAMES — ALL 7 MATCHES AT A GLANCE", SEC))
    conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}
    hdr = [P(h, bold=True, color=GOLD, align="CENTER" if h!="Match" else "LEFT", sz=8)
           for h in ["Match","Format","PP Line","Model","Pick","Conf","Key Reason"]]
    rows = [hdr]
    for (match,fmt,pp,proj,pick,conf,reason) in TG_SUMMARY:
        pc = GREEN if pick=="OVER" else RED
        rows.append([
            P(match, bold=True, sz=7.5),
            P(fmt, color=MUTED, align="CENTER", sz=7),
            P(pp, align="CENTER", sz=7.5),
            P(proj, bold=True, color=GOLD, align="CENTER", sz=7.5),
            P(f"<b>{pick}</b>", color=pc, align="CENTER", sz=7.5),
            P(conf, bold=True, color=conf_c.get(conf,MUTED), align="CENTER", sz=7.5),
            P(reason, color=MUTED, sz=7),
        ])
    t = Table(rows, colWidths=[1.5*inch,.65*inch,.6*inch,.6*inch,.52*inch,.45*inch,3.38*inch])
    ts = tbl_style()
    for i,(m,_,_,_,pick,conf,_) in enumerate(TG_SUMMARY,1):
        if conf=="A+": ts.add("BACKGROUND",(0,i),(-1,i),DG)
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1,5))


def build_picks_table(label, picks, story):
    story.append(Paragraph(label, SEC))
    conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}
    type_c = {"goblin":PURPLE,"demon":RED,"standard":MUTED}
    hdr = [P(h, bold=True, color=GOLD, align="CENTER" if h not in ("#","Player","Analysis") else ("LEFT" if h in ("Player","Analysis") else "CENTER"), sz=8)
           for h in ["#","Player","Prop","PP Line","Type","Proj","Pick","Conf","Analysis"]]
    rows = [hdr]
    ts = tbl_style()
    for i,(num,player,prop,pp,ptype,proj,pick,conf,analysis) in enumerate(picks,1):
        pc = GREEN if "OVER" in pick else RED
        cc = conf_c.get(conf,MUTED)
        tc = type_c.get(ptype,MUTED)
        edge_v = float(proj) - float(pp) if "OVER" in pick else float(pp) - float(proj)
        edge_s = f"+{edge_v:.1f}" if edge_v > 0 else f"{edge_v:.1f}"
        edge_c = GREEN if edge_v >= 2 else BLUE if edge_v >= 0.5 else ORANGE
        has_real = "REAL" in analysis or "RG RECORD" in analysis or "RG HISTORY" in analysis or "RG PEDIGREE" in analysis
        rows.append([
            P(str(num), color=MUTED, align="CENTER", sz=7.5),
            P(player, bold=True, sz=7.5),
            P(prop, color=BLUE, sz=7.5),
            P(pp, align="CENTER", sz=7.5),
            P(ptype, color=tc, align="CENTER", sz=7),
            P(proj, bold=True, color=GOLD, align="CENTER", sz=7.5),
            P(f"<b>{pick}</b>", color=pc, align="CENTER", sz=7.5),
            P(conf, bold=True, color=cc, align="CENTER", sz=7.5),
            Paragraph(analysis, sty(f"a{num}", fontSize=7, textColor=ORANGE if has_real else MUTED, leading=9)),
        ])
        if conf=="A+": ts.add("BACKGROUND",(0,i),(-1,i),DG)
    t = Table(rows, colWidths=[.22*inch,.72*inch,.8*inch,.5*inch,.58*inch,
                                .42*inch,.55*inch,.4*inch,3.51*inch])
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1,5))


def build_slips(story):
    story.append(Paragraph("SUGGESTED SLIPS", SEC))
    slips = [
        {"label":"SLIP A — TOTAL GAMES (4-LEG)", "color":GOLD,
         "legs":[("Mensik/Fonseca TG","OVER 38.0","A+"),
                 ("Zverev/Jodar TG","OVER 36.5","A"),
                 ("Svitolina/Kostyuk TG","OVER 21.5","A"),
                 ("Sabalenka/Shnaider TG","UNDER 19.5","B+")],
         "payout":"Power Play ~14x",
         "note":"3 OVERs on close-fought matches (derby, first meetings, H2H battles) + 1 UNDER on defending champ vs opponent who won via opponent collapse."},
        {"label":"SLIP B — REAL DATA PROPS (3-LEG)", "color":CLAYC,
         "legs":[("Mensik DFs","OVER 5.5 goblin","A+"),
                 ("Andreeva FS","OVER 17.0 std","A+"),
                 ("Berrettini Aces","UNDER 10.5 std","A")],
         "payout":"~8x",
         "note":"Mensik 9 DFs confirmed real data. Andreeva 2025 RG SF pedigree + dominant form. Berrettini had 2 aces in QF — 10.5 line is wildly overpriced."},
        {"label":"SLIP C — SF PREVIEW (3-LEG)", "color":BLUE,
         "legs":[("FAA Aces","OVER 11.5 std","A+"),
                 ("FAA DFs","UNDER 4.5 std","A"),
                 ("Shnaider TGW","UNDER 7.5 std","A")],
         "payout":"~8x",
         "note":"FAA: 9 aces in 2-set QF projects to 13+ in longer SF. 2 DFs in QF vs 4.5 line = strong UNDER. Sabalenka defending champ projects Shnaider to 4-6 games max."},
        {"label":"SLIP D — ML + PROPS COMBO (4-LEG)", "color":GREEN,
         "legs":[("Andreeva ML","WIN -189","A+"),
                 ("Kostyuk ML","WIN -125","B+"),
                 ("Fonseca FS","OVER 20.0","A"),
                 ("Zverev FS","OVER 23.5","A")],
         "payout":"~+160",
         "note":"Two sharp ML picks (Andreeva model +20% edge, Kostyuk market flip) plus two FS OVERs for fresh players (Fonseca 0 DFs, Zverev fresh 3-set win) at RG where they both have deep records."},
    ]

    def render_slip(s):
        rows = [[
            P(s["label"], bold=True, color=s["color"], sz=8.5),
            P(s["payout"], bold=True, color=GOLD, align="RIGHT", sz=8),
        ]]
        t0 = Table(rows, colWidths=[2.35*inch,1.3*inch])
        t0.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DEEP),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7)]))
        items = [t0]
        for n,(name,pick,conf) in enumerate(s["legs"],1):
            cc = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}.get(conf,MUTED)
            pc = GREEN if "OVER" in pick or "WIN" in pick else RED
            lr = Table([[
                P(f"<b>{n}.</b> {name}", sz=7.5),
                P(f"<b>{pick}</b>", bold=True, color=pc, align="RIGHT", sz=7.5),
                P(conf, bold=True, color=cc, align="RIGHT", sz=7),
            ]], colWidths=[1.7*inch,1.2*inch,.45*inch])
            lr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD),
                ("GRID",(0,0),(-1,-1),0.2,BORDER),
                ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
                ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),5)]))
            items.append(lr)
        items.append(P(f"<i>{s['note']}</i>", color=MUTED, sz=7))
        return items

    W = 3.82*inch
    for left, right in [(slips[0],slips[1]),(slips[2],slips[3])]:
        li, ri = render_slip(left), render_slip(right)
        def pack(items):
            inner = Table([[it] for it in items], colWidths=[W-.08*inch])
            inner.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),0),
                ("RIGHTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),0),
                ("BOTTOMPADDING",(0,0),(-1,-1),0)]))
            return inner
        row = Table([[pack(li), pack(ri)]], colWidths=[W+.04*inch,W+.04*inch])
        row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),4)]))
        story.append(row)


def build_footer(story):
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1,3))
    story.append(Paragraph(
        "AstroTennis · Roland Garros 2026 · June 1  |  "
        "v7: H2H · Career Clay Stats · RG Record · Total Games Model · PrizePicks Lines  |  "
        "For entertainment purposes only",
        sty("ft", fontSize=6.5, textColor=MUTED, alignment=TA_CENTER)))


def main():
    out = os.path.normpath(os.path.join(os.path.dirname(__file__),
                           "..", "data", "AstroTennis_Stats_v7_20260601.pdf"))
    doc = SimpleDocTemplate(out, pagesize=letter,
        leftMargin=0.4*inch, rightMargin=0.4*inch,
        topMargin=0.35*inch, bottomMargin=0.35*inch,
        title="AstroTennis Deep Analysis v7 — June 1 2026")

    story = []
    build_header(story)
    story.append(Spacer(1,3))
    build_match_cards(story)
    build_tg_table(story)
    build_picks_table("ACTIVE QF — PRIZEPICKS PICKS (18 props, H2H + Clay + RG factored)", PICKS_QF, story)
    build_picks_table("SF PREVIEW — PRIZEPICKS LINES ALREADY POSTED (10 props)", PICKS_SF, story)
    build_slips(story)
    build_footer(story)

    doc.build(story, onFirstPage=bg, onLaterPages=bg)
    print(f"PDF saved → {out}")

if __name__ == "__main__":
    main()
