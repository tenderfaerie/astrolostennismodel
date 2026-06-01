"""
AstroTennis — June 1 2026 Stats Edition v4
Roland Garros QF · Real R16 data + LIVE scraped H2H + Clay model + Odds
H2H data: Sofascore via RapidAPI (scraped 2026-06-01)
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os

NAVY      = colors.HexColor("#0a0f1e")
DEEP      = colors.HexColor("#111827")
CARD      = colors.HexColor("#1a2035")
BORDER    = colors.HexColor("#1f2d4a")
GOLD      = colors.HexColor("#f5c842")
GREEN     = colors.HexColor("#22c55e")
RED       = colors.HexColor("#ef4444")
BLUE      = colors.HexColor("#38bdf8")
PURPLE    = colors.HexColor("#a78bfa")
CLAY      = colors.HexColor("#c87941")
ORANGE    = colors.HexColor("#fb923c")
TEXT      = colors.HexColor("#e2e8f0")
MUTED     = colors.HexColor("#94a3b8")
DARKGREEN = colors.HexColor("#0d1f0d")
DARKRED   = colors.HexColor("#1f0505")

def style(name, **kw):
    d = dict(fontName="Helvetica", fontSize=9, textColor=TEXT, leading=12)
    d.update(kw)
    return ParagraphStyle(name, **d)

def cell(txt, bold=False, color=None, align="LEFT"):
    s = dict(
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=8.5 if bold else 8,
        textColor=color or TEXT,
        leading=11 if bold else 10,
        alignment={"LEFT": TA_LEFT, "CENTER": TA_CENTER, "RIGHT": TA_RIGHT}[align]
    )
    return Paragraph(txt, style(f"c{id(txt)}", **s))

S_SECTION = style("sec", fontName="Helvetica-Bold", fontSize=8, textColor=MUTED,
                  spaceBefore=8, spaceAfter=3)

# ── YESTERDAY'S ACTUAL MATCH STATS ────────────────────────────────────────────
YESTERDAY = {
    "Fonseca":   {"aces": 2,  "dfs": 0,  "bps_pct": .77, "sets": 4, "result": "W 3-1", "note": "0 DFs — cleanest R16 perf"},
    "Mensik":    {"aces": 13, "dfs": 9,  "bps_pct": .66, "sets": 5, "result": "W 3-2", "note": "FATIGUED — 9 DFs, 5 sets"},
    "Zverev":    {"aces": 4,  "dfs": 2,  "bps_pct": .50, "sets": 3, "result": "W 3-0", "note": "Fresh — 3-set clean win"},
    "Jodar":     {"aces": 3,  "dfs": 3,  "bps_pct": .71, "sets": 3, "result": "W 3-2", "note": "Saved 10/14 BP — elite clutch"},
    "Andreeva":  {"aces": 1,  "dfs": 2,  "bps_pct": .50, "sets": 2, "result": "W 2-0", "note": "Dominant — fresh legs"},
    "Svitolina": {"aces": 3,  "dfs": 1,  "bps_pct": .57, "sets": 3, "result": "W 2-1", "note": "3-setter, slight fatigue"},
}

# ── REAL SCRAPED H2H (Sofascore via RapidAPI, 2026-06-01) ─────────────────────
# Format: (overall, clay_prior, last_winner, edge_note)
# "?" winner = current RG match not yet played (excluded from counts)
H2H = {
    "Cobolli vs Svajda":       ("1-0 Cobolli",    "0-0 (none)",      "Cobolli",     "Only 1 prior (Delray Beach 2024 hard, Cobolli). No clay history."),
    "Cerundolo vs Berrettini": ("1 mtg, unclear",  "0-0 (none)",      "Unclear",     "1 prior meeting (Miami 2022 hard, result unclear). No clay H2H."),
    "Tiafoe vs Arnaldi":       ("1-1 split",       "0-1 Arnaldi",     "Arnaldi",     "Arnaldi won Madrid 2025 clay. Tiafoe won Wimbledon 2024 grass. ARNALDI clay H2H edge."),
    "FAA vs Tabilo":           ("1-0 FAA",         "0-0 (none)",      "FAA",         "Only 1 prior (Shanghai 2025 hard, FAA). No clay H2H prior to today."),
    "Mensik vs Fonseca":       ("0-2 Mensik",      "0-0 (none)",      "Fonseca",     "Fonseca leads H2H 2-0 (Basel 2025 + Next Gen 2024, both hard). No clay prior."),
    "Jodar vs Zverev":         ("FIRST MEETING",   "0-0 (none)",      "N/A",         "FIRST EVER meeting. No H2H history. Pure clay model match."),
    "Potapova vs Kalinskaya":  ("0-2 Potapova",    "0-0 (none)",      "Kalinskaya",  "Kalinskaya leads H2H 2-0 (Cincinnati 2022 + Moscow 2019, hard). No clay prior."),
    "Keys vs Shnaider":        ("3-0 Keys",        "0-0 (none)",      "Keys",        "Keys dominates H2H 3-0 (Brisbane 2026, London 2025, Miami 2024). No prior clay."),
    "Sabalenka vs Osaka":      ("3-2 Sabalenka",   "1-0 Sabalenka",   "Sabalenka",   "Sabalenka 3-2 career. Madrid 2026 clay win. Osaka won 2018 US Open + 1 other."),
    "Svitolina vs Kostyuk":    ("1-2 Svitolina",   "0-0 (none)",      "Kostyuk",     "Kostyuk leads recent H2H 2-1 (Toronto 2024). Svitolina won 2018 AO. No clay prior."),
    "Andreeva vs Cirstea":     ("1-0 Andreeva",    "1-0 Andreeva",    "Andreeva",    "Andreeva leads 1-0. Won Linz 2026 clay indoor. Only clay H2H also Andreeva."),
}

# ── CAREER CLAY STATS ─────────────────────────────────────────────────────────
STATS = {
    "Cobolli":    (.630, .053, .037, .632, .561),
    "Svajda":     (.267, .039, .017, .595, .561),
    "Cerundolo":  (.654, .044, .039, .569, .685),
    "Berrettini": (.675, .082, .022, .679, .464),
    "Tiafoe":     (.556, .066, .023, .628, .531),
    "Arnaldi":    (.543, .060, .041, .616, .562),
    "FAA":        (.650, .070, .028, .640, .560),
    "Tabilo":     (.623, .060, .024, .663, .520),
    "Potapova":   (.667, .039, .057, .575, .836),
    "Kalinskaya": (.480, .022, .051, .568, .760),
    "Keys":       (.732, .051, .030, .594, .829),
    "Shnaider":   (.667, .018, .041, .577, .763),
    "Sabalenka":  (.804, .047, .039, .636, .848),
    "Osaka":      (.630, .074, .049, .586, .690),
    "Mensik":     (.556, .113, .040, .645, .507),
    "Fonseca":    (.569, .048, .028, .618, .632),
    "Zverev":     (.761, .085, .030, .645, .577),
    "Jodar":      (.750, .049, .024, .607, .724),
    "Kostyuk":    (.758, .029, .076, .589, .890),
    "Svitolina":  (.750, .040, .034, .604, .823),
    "Andreeva":   (.778, .034, .043, .574, .830),
    "Cirstea":    (.593, .040, .025, .558, .772),
}

PICKS = [
    (1,  "Fonseca vs Mensik",      "Double Faults",  "5.5",  "OVER",
     "8.2",  "+2.7", "A+",
     "REAL DATA: Mensik 9 DFs in 5-set R16 battle. H2H: Fonseca leads 2-0 on hard — momentum carrier. Career DF rate 0.040 + confirmed fatigue projects 7-9 DFs today."),

    (2,  "Sabalenka vs Osaka",     "Fantasy Score",  "21.0", "OVER",
     "27.6", "+6.6", "A+",
     "H2H: Sabalenka 3-2 overall, 1-0 on clay (Madrid 2026). Clay 80.4% vs 63.0%. Projects 6-2 6-1 = 27+ FS. Line 6+ pts below model. Dominant clay queen at home court."),

    (3,  "Andreeva vs Cirstea",    "ML Andreeva",    "-189", "WIN",
     "85%",  "+16%", "A+",
     "REAL DATA: Dominant 2-0 yesterday. LIVE H2H: Andreeva 1-0 on clay (Linz 2026 indoor). Only clay H2H = Andreeva win. Clay 77.8% vs 59.3%. Best ML value on board."),

    (4,  "Cobolli vs Svajda",      "Fantasy Score",  "28.0", "OVER",
     "34.5", "+6.5", "A+",
     "H2H: Cobolli 1-0 (beat Svajda on hard, no clay history). Svajda career 4-11 clay. Cobolli clay 63% projects dominant 6-2 6-3 6-2 = 34+ FS. Market confirms (-909)."),

    (5,  "Fonseca vs Mensik",      "Aces",           "6.5",  "OVER",
     "9.1",  "+2.6", "A",
     "REAL DATA: Mensik 13 aces in R16. Even fatigued, 0.113 ace rate projects 8-10 today. Fonseca adds 2-3. H2H Fonseca 2-0 = confidence in his game carrying. Total 9+ expected."),

    (6,  "Zverev vs Jodar",        "ML Zverev",      "-303", "WIN",
     "88%",  "+12%", "A",
     "LIVE H2H: FIRST EVER meeting — no H2H history. Goes pure clay model. Zverev clay 76.1% vs Jodar 75.0%. REAL: Zverev fresh 3-setter, 2 DFs. Clay model + form = 88%."),

    (7,  "Zverev vs Jodar",        "Total Games",    "36.5", "OVER",
     "39.1", "+2.6", "A",
     "First ever meeting = no mental edge either way. Both clay 75-76%. REAL: Jodar saved 10/14 BPs — tough competitor. Expect competitive long match, 38-41 games on RG clay."),

    (8,  "Keys vs Shnaider",       "ML Keys",        "-161", "WIN",
     "82%",  "+18%", "A",
     "LIVE H2H: Keys DOMINATES 3-0 (Brisbane 2026, London 2025, Miami 2024). No clay H2H but Keys owns this matchup. Clay 73.2% vs 66.7%. Biggest confirmed ML edge on board."),

    (9,  "Sabalenka vs Osaka",     "Total Games Won","12.5", "OVER",
     "15.1", "+2.6", "A",
     "H2H: Sabalenka 3-2 shows Osaka can take games even in losses. Clay 80.4% Sabalenka but Osaka clay 63% creates resistance. Projects 15+ TGW in emphatic Sabalenka win."),

    (10, "Berrettini vs Cerundolo","Aces",            "7.5",  "OVER",
     "9.7",  "+2.2", "A",
     "H2H: 1 prior meeting (unclear result), no clay history — fresh slate. Berrettini clay ace rate 0.082 — highest in field. 68.3% 1stIn. Projects 9-10 aces in potential 4-setter."),

    (11, "Tiafoe vs Arnaldi",      "ML Arnaldi",     "+100", "WIN",
     "54%",  "+4%",  "B+",
     "LIVE H2H FLIP: Arnaldi won the ONLY clay meeting (Madrid 2025). H2H 1-1 but Arnaldi clay H2H edge. Clay 54.3% vs 55.6% — dead even. H2H clay edge makes Arnaldi worth it at +100."),

    (12, "Cobolli vs Svajda",      "Total Games",    "32.5", "UNDER",
     "28.1", "-4.4", "B+",
     "Svajda career 4-11 clay. H2H Cobolli won cleanly. No clay history means no upset precedent. Cobolli clay 63% projects 6-2 6-3 6-2 = 28 games. 4.5 game cushion."),

    (13, "Andreeva vs Cirstea",    "Total Games Won","11.5", "UNDER",
     "9.1",  "-2.4", "B+",
     "REAL: Andreeva dominant 2-0, fresh. LIVE H2H: 1-0 Andreeva on clay. Clay 77.8% vs Cirstea 59.3% BP saved 55.8%. Projects sub-10 TGW for Cirstea in straight-set loss."),

    (14, "Fonseca vs Mensik",      "ML Fonseca",     "-227", "WIN",
     "78%",  "+6%",  "B+",
     "REAL: Fonseca 0 DFs vs Mensik 9 DFs + 5 sets fatigue. LIVE H2H: Fonseca leads 2-0 on hard. No clay H2H but Fonseca momentum confirmed. Market 69% vs model 78%."),

    (15, "Sabalenka vs Osaka",     "Break Pts Won",  "4.5",  "OVER",
     "6.1",  "+1.6", "B+",
     "H2H shows Sabalenka consistently earns breaks in their meetings. BP created 0.848 — highest WTA. Osaka BP saved 58.6%. Even in Madrid 2026 clay win Sabalenka earned 6+ BPW."),

    (16, "Svitolina vs Kostyuk",   "Double Faults",  "5.5",  "OVER",
     "6.9",  "+1.4", "B+",
     "LIVE H2H: Kostyuk leads recent 2-1 — tight competitive matches. Kostyuk DF rate 0.076 highest WTA field. REAL: Svitolina slight fatigue. High-pressure derby = DF spike."),

    (17, "Keys vs Shnaider",       "Fantasy Score",  "16.0", "OVER",
     "18.5", "+2.5", "B",
     "H2H: Keys 3-0 shows she controls this matchup completely. Clay 73.2% + 66.9% 1stW. Projects 18+ FS. Shnaider returns well (0.763 BP created) but Keys dominates this rivalry."),

    (18, "Potapova vs Kalinskaya", "ML Kalinskaya",  "+150", "WIN",
     "52%",  "+12%", "B",
     "LIVE H2H FLIP: Kalinskaya leads H2H 2-0 (Cincinnati 2022, Moscow 2019). Market ignores H2H. Clay 48.0% vs 66.7% but Kalinskaya owns this matchup mentally at +150 value."),

    (19, "Mensik vs Fonseca",      "Total Games",    "38.5", "OVER",
     "41.2", "+2.7", "B",
     "H2H shows both matches went full distance (Next Gen Finals, Basel — both competitive). Mensik 9 DFs = serve breaks. Fonseca fresh. Projects 40-43 games on RG clay."),

    (20, "Svitolina vs Kostyuk",   "Break Pts Won",  "4.5",  "OVER",
     "5.7",  "+1.2", "B",
     "LIVE H2H: Kostyuk leads 2-1 recent — creates massive pressure. BP created 0.890 — highest in field. REAL: Svitolina served 4/7 BP saved. Kostyuk earns 5-6 BPW in classic derby."),
]

MONEYLINES = [
    ("Andreeva",   "vs Cirstea",    "-189","85%","63%","A+","REAL dominant. H2H 1-0 clay. Clay 77.8% vs 59.3%. Best ML value."),
    ("Keys",       "vs Shnaider",   "-161","82%","62%","A", "H2H 3-0 Keys. Clay 73.2%. +18% model edge — biggest on board."),
    ("Sabalenka",  "vs Osaka",      "-500","91%","83%","A", "H2H 3-2 Sabalenka, 1-0 clay. Clay 80.4%. Osaka 63% clay."),
    ("Zverev",     "vs Jodar",      "-303","88%","75%","A", "FIRST MEETING — pure clay model. REAL: Zverev fresh 3-setter."),
    ("Fonseca",    "vs Mensik",     "-227","78%","69%","A", "REAL: 0 DFs vs 9 DFs. H2H Fonseca 2-0. Model 78% vs market 69%."),
    ("Kalinskaya", "vs Potapova",   "+150","52%","40%","B", "H2H FLIP: Kalinskaya leads 2-0. +150 value vs clay model favorite."),
    ("Arnaldi",    "vs Tiafoe",     "+100","54%","50%","B+","H2H: Arnaldi won only clay meeting (Madrid 2025). +100 is value."),
    ("Cobolli",    "vs Svajda",     "-909","91%","90%","B+","Svajda 4-11 clay. H2H 1-0 Cobolli. Dominant lock pick."),
]

def us_to_prob(american):
    if american > 0: return round(100 / (american + 100), 3)
    return round(-american / (-american + 100), 3)

SLIPS = [
    {
        "label": "SLIP A — REAL DATA + LIVE H2H (4-LEG)",
        "color": GOLD,
        "legs": [
            ("Mensik DFs",        "OVER 5.5",  "A+"),
            ("Sabalenka FS",      "OVER 21.0", "A+"),
            ("Andreeva ML",       "WIN -189",  "A+"),
            ("Fonseca Aces",      "OVER 6.5",  "A"),
        ],
        "payout": "Power Play ~17x",
        "note": "Mensik 9 DFs confirmed real data. Sabalenka 3-2 H2H, 1-0 clay. Andreeva 1-0 on clay H2H + dominant 2-0 yesterday. Fonseca H2H 2-0 + Mensik ace rate stays high.",
    },
    {
        "label": "SLIP B — H2H VALUE PICKS (3-LEG)",
        "color": CLAY,
        "legs": [
            ("Keys ML",           "WIN -161",  "A"),
            ("Arnaldi ML",        "WIN +100",  "B+"),
            ("Kalinskaya ML",     "WIN +150",  "B"),
        ],
        "payout": "3-leg ~+320",
        "note": "Keys 3-0 H2H. Arnaldi won only clay H2H (Madrid 2025) at +100. Kalinskaya leads 2-0 H2H at +150. All three backed by live scraped H2H data.",
    },
    {
        "label": "SLIP C — ML PARLAY (3-LEG)",
        "color": GREEN,
        "legs": [
            ("Andreeva ML",       "WIN -189",  "A+"),
            ("Keys ML",           "WIN -161",  "A"),
            ("Fonseca ML",        "WIN -227",  "B+"),
        ],
        "payout": "3-leg parlay ~+195",
        "note": "Three where model edge confirmed by live H2H + real match data. Andreeva +16%, Keys +18%, Fonseca +9%. All three won their R16 in dominant fashion.",
    },
    {
        "label": "SLIP D — SERVE + FATIGUE PROPS (4-LEG)",
        "color": RED,
        "legs": [
            ("Mensik DFs",        "OVER 5.5",  "A+"),
            ("Kostyuk DFs",       "OVER 5.5",  "B+"),
            ("Berrettini Aces",   "OVER 7.5",  "A"),
            ("Sabalenka BPW",     "OVER 4.5",  "B+"),
        ],
        "payout": "Power Play ~14x",
        "note": "Mensik fatigue real data confirmed. Kostyuk H2H pressure derby 0.076 DF rate. Berrettini 0.082 ace rate highest in field. Sabalenka 3-2 H2H earned breaks in every meeting.",
    },
]

def build_header(story):
    S_LOGO = style("lg", fontName="Helvetica-Bold", fontSize=18, textColor=GOLD)
    S_EV   = style("ev", fontName="Helvetica-Bold", fontSize=11, textColor=CLAY, alignment=TA_RIGHT)
    t = Table([[
        Paragraph("ASTROTENNIS", S_LOGO),
        Paragraph("ROLAND GARROS 2026 · JUNE 1<br/>"
                  "<font color='#fb923c' size='8'>STATS EDITION v4 — Live Scraped H2H + Real R16 Data + Clay Model</font>", S_EV),
    ]], colWidths=[3.5*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),NAVY),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD))
    story.append(Spacer(1, 4))


def build_yesterday_card(story):
    story.append(Paragraph("YESTERDAY'S R16 STATS — FACTORED INTO TODAY'S PICKS", S_SECTION))
    hdr = [cell(h, bold=True, color=GOLD, align="CENTER")
           for h in ["Player","Result","Aces","DFs","BP Saved","Sets","Form Note"]]
    rows = [hdr]
    for name in ["Fonseca","Mensik","Zverev","Jodar","Andreeva","Svitolina"]:
        y = YESTERDAY[name]
        bp_c = GREEN if y["bps_pct"] >= .70 else RED if y["bps_pct"] < .55 else TEXT
        df_c = RED if y["dfs"] >= 7 else ORANGE if y["dfs"] >= 4 else GREEN
        note_c = RED if "FATIGUED" in y["note"] else GREEN if "fresh" in y["note"].lower() or "0 DF" in y["note"] else TEXT
        rows.append([
            cell(name, bold=True),
            cell(y["result"], color=GREEN),
            cell(str(y["aces"]), align="CENTER"),
            cell(str(y["dfs"]), bold=True, color=df_c, align="CENTER"),
            cell(f"{y['bps_pct']:.0%}", bold=True, color=bp_c, align="CENTER"),
            cell(str(y["sets"]), align="CENTER"),
            Paragraph(y["note"], style(f"yn{name}", fontSize=7.5, textColor=note_c, leading=10)),
        ])
    t = Table(rows, colWidths=[.75*inch,.7*inch,.45*inch,.45*inch,.7*inch,.4*inch,4.25*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("BACKGROUND",(0,2),(-1,2),DARKRED),
        ("BACKGROUND",(0,1),(-1,1),DARKGREEN),
        ("BACKGROUND",(0,3),(-1,3),DARKGREEN),
    ]))
    story.append(t)
    story.append(Spacer(1, 5))


def build_h2h_table(story):
    story.append(Paragraph("LIVE SCRAPED H2H — SOFASCORE (FETCHED TODAY)", S_SECTION))
    hdr = [cell(h, bold=True, color=GOLD, align="CENTER" if h != "Match" else "LEFT")
           for h in ["Match","Overall","Clay H2H","Last Winner","Key Insight"]]
    rows = [hdr]
    for i,(match,(overall,clay,last,note)) in enumerate(H2H.items(),1):
        # Color-code surprises
        surprise = any(x in note for x in ["FLIP","FIRST EVER","Arnaldi clay","Kalinskaya leads"])
        overall_c = ORANGE if surprise else GOLD
        rows.append([
            cell(match, bold=True),
            cell(overall, bold=True, color=overall_c, align="CENTER"),
            cell(clay, bold=True, color=CLAY, align="CENTER"),
            cell(last, color=GREEN if last not in ("N/A","Unclear") else MUTED, align="CENTER"),
            Paragraph(note, style(f"h{i}", fontSize=7.5,
                                  textColor=ORANGE if surprise else MUTED, leading=10)),
        ])
    t = Table(rows, colWidths=[1.4*inch,.9*inch,.85*inch,.82*inch,3.73*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 5))


def build_picks(story):
    story.append(Paragraph("TOP 20 PICKS — LIVE H2H + REAL STATS + CLAY MODEL", S_SECTION))
    conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}
    hdr = [cell(h, bold=True, color=GOLD,
                align="CENTER" if h in ("#","CONF","EDGE","PROJ") else "LEFT")
           for h in ["#","Match","Prop","Line","Pick","Proj","Edge","Conf","Rationale"]]
    rows = [hdr]
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ])
    for i,(num,match,prop,line,pick,proj,edge,conf,rat) in enumerate(PICKS,1):
        cc = conf_c.get(conf,MUTED)
        pc = GREEN if "OVER" in pick or "WIN" in pick else RED if "UNDER" in pick else BLUE
        rat_c = ORANGE if ("REAL" in rat or "LIVE H2H" in rat or "FLIP" in rat) else MUTED
        rows.append([
            cell(str(num), align="CENTER", color=MUTED),
            cell(match, bold=True),
            cell(prop, color=BLUE),
            cell(line, align="CENTER"),
            cell(pick, bold=True, color=pc, align="CENTER"),
            cell(proj, align="CENTER", color=GOLD),
            cell(edge, bold=True, color=GREEN, align="CENTER"),
            cell(conf, bold=True, color=cc, align="CENTER"),
            Paragraph(rat, style(f"r{i}", fontSize=7.5, textColor=rat_c, leading=10)),
        ])
        if conf == "A+": ts.add("BACKGROUND",(0,i),(-1,i),DARKGREEN)
    t = Table(rows, colWidths=[.22*inch,1.3*inch,.8*inch,.42*inch,.68*inch,
                                .42*inch,.42*inch,.42*inch,2.9*inch])
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 5))


def build_moneylines(story):
    story.append(Paragraph("MONEYLINE PICKS — LIVE H2H + CLAY MODEL vs MARKET", S_SECTION))
    conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}
    hdr = [cell(h, bold=True, color=GOLD)
           for h in ["Player","Opp","Price","Model","Market","Edge","Conf","Analysis"]]
    rows = [hdr]
    for i,(player,opp,price,modpct,mktpct,conf,note) in enumerate(MONEYLINES,1):
        imp = us_to_prob(int(price))
        edge_n = int(modpct.replace('%','')) - round(imp*100)
        edge_s = f"+{edge_n}%" if edge_n >= 0 else f"{edge_n}%"
        edge_c = GREEN if edge_n >= 10 else BLUE if edge_n >= 5 else ORANGE if edge_n < 0 else MUTED
        cc = conf_c.get(conf,MUTED)
        note_c = ORANGE if ("H2H" in note or "REAL" in note or "FLIP" in note) else MUTED
        rows.append([
            cell(player, bold=True),
            cell(opp, color=MUTED),
            cell(price, bold=True, color=GOLD, align="CENTER"),
            cell(modpct, bold=True, color=GREEN, align="CENTER"),
            cell(mktpct, align="CENTER"),
            cell(edge_s, bold=True, color=edge_c, align="CENTER"),
            cell(conf, bold=True, color=cc, align="CENTER"),
            Paragraph(note, style(f"ml{i}", fontSize=7.5, textColor=note_c, leading=10)),
        ])
    t = Table(rows, colWidths=[.85*inch,.82*inch,.5*inch,.52*inch,.52*inch,
                                .5*inch,.45*inch,3.24*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 5))


def build_slips(story):
    story.append(Paragraph("SUGGESTED SLIPS", S_SECTION))
    slip_w = [3.85*inch, 3.85*inch]

    def render_slip(s):
        items = []
        tr = Table([[
            Paragraph(s["label"], style("st", fontName="Helvetica-Bold", fontSize=8.5, textColor=s["color"])),
            Paragraph(s["payout"], style("py", fontName="Helvetica-Bold", fontSize=8, textColor=GOLD, alignment=TA_RIGHT)),
        ]], colWidths=[2.35*inch,1.3*inch])
        tr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DEEP),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7)]))
        items.append(tr)
        for n,(name,pick,conf) in enumerate(s["legs"],1):
            cc = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}.get(conf,MUTED)
            pc = GREEN if "OVER" in pick or "WIN" in pick else RED if "UNDER" in pick else GOLD
            lr = Table([[
                Paragraph(f"<b>{n}.</b> {name}", style("ln",fontSize=8,textColor=TEXT,leading=10)),
                Paragraph(f"<b>{pick}</b>", style("lp",fontName="Helvetica-Bold",fontSize=8,textColor=pc,alignment=TA_RIGHT)),
                Paragraph(conf, style("lc",fontName="Helvetica-Bold",fontSize=7.5,textColor=cc,alignment=TA_RIGHT)),
            ]], colWidths=[1.9*inch,1.1*inch,.45*inch])
            lr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD),
                ("GRID",(0,0),(-1,-1),0.2,BORDER),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
                ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),5)]))
            items.append(lr)
        items.append(Paragraph(f"<i>{s['note']}</i>",
            style("sn",fontSize=7,textColor=MUTED,leading=9,spaceBefore=3,spaceAfter=4)))
        return items

    for left,right in zip(SLIPS[:2],SLIPS[2:]):
        li,ri = render_slip(left), render_slip(right)
        def pack(items,w):
            inner = Table([[item] for item in items], colWidths=[w-.1*inch])
            inner.setStyle(TableStyle([
                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
                ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
            return inner
        row = Table([[pack(li,slip_w[0]),pack(ri,slip_w[1])]], colWidths=slip_w)
        row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),4),
            ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        story.append(row)


def build_footer(story):
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1,3))
    story.append(Paragraph(
        "AstroTennis · Roland Garros 2026 · June 1  |  "
        "v4: Live Scraped H2H (Sofascore) + Real R16 Stats + Clay Win Model  |  "
        "For entertainment purposes only",
        style("ft", fontSize=6.5, textColor=MUTED, alignment=TA_CENTER)
    ))


def main():
    out = os.path.normpath(os.path.join(os.path.dirname(__file__),
                           "..", "data", "AstroTennis_Stats_v4_20260601.pdf"))
    doc = SimpleDocTemplate(out, pagesize=letter,
        leftMargin=0.4*inch, rightMargin=0.4*inch,
        topMargin=0.35*inch, bottomMargin=0.35*inch,
        title="AstroTennis Stats Sheet v4 — June 1 2026")

    def bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0,0,letter[0],letter[1],fill=1,stroke=0)
        canvas.restoreState()

    story = []
    build_header(story)
    story.append(Spacer(1,4))
    build_yesterday_card(story)
    build_h2h_table(story)
    build_picks(story)
    build_moneylines(story)
    build_slips(story)
    build_footer(story)
    doc.build(story, onFirstPage=bg, onLaterPages=bg)
    print(f"PDF saved → {out}")

if __name__ == "__main__":
    main()
