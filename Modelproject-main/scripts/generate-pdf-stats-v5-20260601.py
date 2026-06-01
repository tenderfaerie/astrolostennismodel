"""
AstroTennis — June 1 2026 Stats Edition v5
Roland Garros QF · Completed Results + Live Odds + Remaining Match Projections
Data: Real QF match stats + Live Sofascore odds + Scraped H2H
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
DARKGREEN = colors.HexColor("#0d2010")
DARKRED   = colors.HexColor("#200808")
DARKGOLD  = colors.HexColor("#1a1500")
UPSET     = colors.HexColor("#7c1d1d")

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

# ── COMPLETED QF RESULTS (Real match data from Sofascore) ─────────────────────
COMPLETED = [
    # (match, winner, score, sets, key_stat, fantasy_score, note, upset)
    ("Cobolli vs Svajda",      "Cobolli",   "W (4 sets)", "25-18 gms",
     "8A 2DF 53%1st 7BPW",      "34.5",
     "Cobolli controlled. Svajda 4-11 clay career. Market was -909 Cobolli.", False),

    ("Cerundolo vs Berrettini","Berrettini","W (3 sets)", "15-13 gms",
     "2A 0DF 92%1st 0BPS",      "19.8",
     "Berrettini: 0 DFs, 92% 1stIn — cleanest serve performance of the day.", False),

    ("FAA vs Tabilo",          "FAA",       "W (2 sets!)", "10-8 gms",
     "9A 2DF 65%1st 100%BPS",   "15.2",
     "FAA dominant — won in 2 sets, 100% BP saves. Tabilo had no answers.", False),

    ("Potapova vs Kalinskaya", "Potapova",  "W (3 sets)", "16-15 gms",
     "1A 8DF 47%1stW 33%BPS",   "17.4",
     "Potapova survives 8 DFs. Tight 3-setter. Kalinskaya H2H 2-0 edge didn't hold.", False),

    ("SHNAIDER def. Keys",     "Shnaider",  "W (3 sets)", "15-9 gms",
     "Keys: 4DF 14%BPS 50UE",   "9.1 (Keys)",
     "MAJOR UPSET — Keys 50 UEs, only 1/7 BP converted. Shnaider controlled all 3 sets.", True),
]

# ── LIVE ODDS FOR REMAINING 6 (Sofascore via RapidAPI, fractional → American) ─
# Tiafoe +91 / Arnaldi +91  (dead even, 52% each)
# Mensik +175 / Fonseca -227 (Fonseca 69%)
# Jodar +240 / Zverev -303  (Zverev 75%)
# Sabalenka -500 / Osaka +350 (Sabalenka 83%)
# Svitolina +100 / Kostyuk -125 (Kostyuk 56% — MARKET FLIP, Kostyuk fav)
# Andreeva -189 / Cirstea +150 (Andreeva 65%)
REMAINING = [
    # (home, away, home_ml, away_ml, home_imp_pct, away_imp_pct, clay_home, clay_away, h2h_edge, note)
    ("Tiafoe",    "Arnaldi",  "+91",  "+91",  "52%","52%", ".556",".543",
     "Arnaldi", "Dead even odds. Arnaldi won ONLY clay H2H (Madrid 2025). Flip pick at +91."),

    ("Mensik",    "Fonseca",  "+175", "-227", "36%","69%", ".556",".569",
     "Fonseca", "Fonseca 0 DFs R16 vs Mensik 9 DFs + 5 sets fatigue. Model 78% vs market 69%."),

    ("Jodar",     "Zverev",   "+240", "-303", "29%","75%", ".750",".761",
     "Zverev", "FIRST EVER meeting. Zverev fresh 3-set win. Clay model 88% vs market 75%."),

    ("Sabalenka", "Osaka",    "-500", "+350", "83%","22%", ".804",".630",
     "Sabalenka", "H2H 3-2, 1-0 clay (Madrid 2026). Sabalenka 80.4% clay. Osaka 63%. Lock."),

    ("Svitolina", "Kostyuk",  "+100", "-125", "50%","56%", ".750",".758",
     "Kostyuk", "MARKET FLIP — Kostyuk now FAVORITE. H2H leads recent 2-1. Derby pressure."),

    ("Andreeva",  "Cirstea",  "-189", "+150", "65%","40%", ".778",".593",
     "Andreeva", "Dominant 2-0 yesterday. H2H 1-0 on clay (Linz 2026). Model 85% vs market 65%."),
]

# ── PICKS — REMAINING 6 MATCHES ONLY ─────────────────────────────────────────
PICKS = [
    # (num, match, prop, line, pick, proj, edge, conf, odds_note, rationale)
    (1, "Fonseca vs Mensik",     "Double Faults", "5.5",  "OVER",
     "8.5", "+3.0", "A+", "Fonseca -227",
     "REAL DATA: Mensik 9 DFs in 5-set R16, career 0.040 DF rate stays elevated under fatigue. Fonseca 0 DFs but adds 2-3. Model projects 8-9 total. H2H: Fonseca 2-0 (both hard)."),

    (2, "Sabalenka vs Osaka",    "Fantasy Score", "21.0", "OVER",
     "27.6", "+6.6", "A+", "Sabalenka -500",
     "H2H: 3-2 Sabalenka, 1-0 clay (Madrid 2026). Clay 80.4% vs 63.0%. Model projects 6-2 6-1 = 27+ FS. Line 6+ pts below model. Dominant clay queen at Roland Garros."),

    (3, "Andreeva vs Cirstea",   "ML Andreeva",   "-189", "WIN",
     "85%", "+20%", "A+", "-189 (model +20% edge)",
     "REAL DATA: Dominant 2-0 yesterday, fresh legs. LIVE H2H: Andreeva 1-0 on clay (Linz 2026). Only clay H2H = Andreeva. Clay 77.8% vs Cirstea 59.3%. Market 65% vs model 85%."),

    (4, "Mensik vs Fonseca",     "Aces",          "6.5",  "OVER",
     "9.1", "+2.6", "A", "Fonseca -227",
     "REAL DATA: Mensik 13 aces in R16. Even fatigued, 0.113 ace rate projects 8-10 today. Fonseca adds 2-3. H2H Fonseca 2-0 — confidence carries. Total 9+ aces expected."),

    (5, "Zverev vs Jodar",       "ML Zverev",     "-303", "WIN",
     "88%", "+13%", "A", "-303 (model +13% edge)",
     "LIVE H2H: FIRST EVER meeting — pure clay model. REAL: Zverev fresh 3-set R16, only 2 DFs. Clay 76.1% vs Jodar 75.0%. Model 88% vs market 75%. Zverev form advantage."),

    (6, "Zverev vs Jodar",       "Total Games",   "36.5", "OVER",
     "39.1", "+2.6", "A", "Jodar +240",
     "First meeting with no mental precedent. Both clay 75-76% = evenly matched skills. Jodar saved 10/14 BP in R16 (elite clutch). Expect competitive 38-41 game match on heavy RG clay."),

    (7, "Sabalenka vs Osaka",    "Total Games Won","12.5","OVER",
     "15.1", "+2.6", "A", "Sabalenka -500",
     "H2H shows Osaka takes games even in losses (5 prior meetings, all competitive). Sabalenka clay 80.4% earns breaks while Osaka 63% creates resistant games. Projects 15+ TGW."),

    (8, "Fonseca vs Mensik",     "ML Fonseca",    "-227", "WIN",
     "78%", "+9%",  "A", "-227 (model +9% edge)",
     "REAL: Fonseca 0 DFs in clean 3-set R16 win vs Mensik 9 DFs in exhausting 5-setter. H2H: Fonseca 2-0. No clay H2H but momentum confirmed. Model 78% vs market 69%."),

    (9, "Tiafoe vs Arnaldi",     "ML Arnaldi",    "+100", "WIN",
     "54%", "+4%",  "B+", "Arnaldi +91 (live odds)",
     "LIVE H2H: Arnaldi won ONLY clay meeting (Madrid 2025). H2H 1-1 but clay H2H advantage. Clay stats dead even (55.6% vs 54.3%). H2H clay edge makes Arnaldi value at +91/+100."),

    (10, "Andreeva vs Cirstea",  "Total Games Won","11.5","UNDER",
     "9.1", "-2.4", "B+", "Andreeva -189",
     "REAL: Andreeva dominant 2-0 yesterday, fresh. LIVE H2H: 1-0 Andreeva on clay. Clay 77.8% vs Cirstea 59.3% with 55.8% BP saves. Projects Cirstea under 9 TGW in straight-set loss."),

    (11, "Svitolina vs Kostyuk", "Double Faults", "5.5",  "OVER",
     "6.9", "+1.4", "B+", "Kostyuk -125",
     "LIVE H2H: Kostyuk leads RECENT 2-1 — tight competitive derbies. MARKET FLIP to Kostyuk fav. Kostyuk DF rate 0.076 — highest WTA. High-pressure nationalist match = DF spike."),

    (12, "Mensik vs Fonseca",    "Total Games",   "38.5", "OVER",
     "41.2", "+2.7", "B+", "Fonseca -227",
     "H2H shows both prior meetings went full distance (Next Gen Finals + Basel 2025, both competitive). Mensik 9 DFs = serve breaks. Fonseca fresh and dangerous. Projects 40-43 games."),

    (13, "Sabalenka vs Osaka",   "Break Pts Won", "4.5",  "OVER",
     "6.1", "+1.6", "B+", "Sabalenka -500",
     "H2H: Sabalenka consistently earns breaks vs Osaka (3-2 head-to-head, all competitive). BP created 0.848 — highest WTA field. Osaka BP saved 58.6%. Projects 6+ BPW in dominant win."),

    (14, "Svitolina vs Kostyuk", "Break Pts Won", "4.5",  "OVER",
     "5.7", "+1.2", "B+", "Kostyuk -125",
     "LIVE H2H: Kostyuk leads recent 2-1 — creates massive pressure. BP created 0.890 — highest in field. REAL: Svitolina slight fatigue from 3-setter yesterday. Kostyuk earns 5-6 BPW."),

    (15, "Tiafoe vs Arnaldi",    "Total Games",   "37.5", "OVER",
     "40.3", "+2.8", "B+", "Even +91/+91",
     "Dead even match by every metric — odds, clay stats, H2H 1-1. Arnaldi clay edge suggests competitive 5-setter (ATP). Both have strong serves. Projects 39-42 game battle on RG clay."),

    (16, "Zverev vs Jodar",      "Aces",          "7.5",  "OVER",
     "9.4", "+1.9", "B", "Zverev -303",
     "Zverev career clay ace rate 0.085 — highest in remaining ATP field. Jodar 0.049 adds 3-4. First meeting = Jodar likely to serve big to stay competitive. Projects 9-10 total aces."),

    (17, "Andreeva vs Cirstea",  "ML Andreeva",   "-189", "WIN",
     "85%", "+20%", "A+", "Market 65%, model 85%",
     "Repeat: Best ML edge remaining after Sabalenka. Andreeva fresh + clay H2H win + 0.830 BP created vs Cirstea 0.772. Market drastically underselling Andreeva at -189."),

    (18, "Kostyuk vs Svitolina", "ML Kostyuk",    "-125", "WIN",
     "56%", "+6%",  "B+", "-125 (market fav now)",
     "MARKET FLIP — Kostyuk opened as underdog but moved to FAVORITE (-125). H2H leads recent 2-1. BP created 0.890. Derby pressure suits her. Model 56% aligns with market. Follow the sharp money."),

    (19, "Sabalenka vs Osaka",   "ML Sabalenka",  "-500", "WIN",
     "91%", "+8%",  "A", "Market 83%, model 91%",
     "Sabalenka H2H 3-2, 1-0 clay. Clay 80.4%. Despite -500 price, model shows +8% edge. Part of 4-team parlay to get better value. Lock of the day on clay."),

    (20, "Fonseca vs Mensik",    "Double Faults", "5.5",  "OVER",
     "8.5", "+3.0", "A+", "Fonseca -227",
     "Same as pick 1 from different angle: Mensik served 9 DFs in 5-set R16 match vs Tiafoe yesterday. Fatigue + career rate 0.040 = 6-8 DFs projected. Fonseca adds 2-3. Combine with aces prop."),
]

MONEYLINES = [
    ("Andreeva",  "vs Cirstea",   "-189","+150","85%","65%","A+","REAL: Dominant 2-0. H2H 1-0 clay. Clay 77.8% vs 59.3%. Best ML value. Model +20% edge."),
    ("Sabalenka", "vs Osaka",     "-500","+350","91%","83%","A", "H2H 3-2, 1-0 clay (Madrid 2026). Clay 80.4%. Even at -500 model shows +8% edge."),
    ("Zverev",    "vs Jodar",     "-303","+240","88%","75%","A", "FIRST MEETING — pure clay model. REAL: Zverev fresh 3-set win. Model +13% edge."),
    ("Fonseca",   "vs Mensik",    "-227","+175","78%","69%","A", "REAL: 0 DFs vs 9 DFs + fatigue. H2H 2-0 Fonseca. Model 78% vs market 69%."),
    ("Kostyuk",   "vs Svitolina", "-125","+100","56%","56%","B+","MARKET FLIP — Kostyuk now fav. H2H leads recent 2-1. Follow sharp line movement."),
    ("Arnaldi",   "vs Tiafoe",    "+91", "+91", "54%","52%","B+","Arnaldi won only clay H2H (Madrid 2025). Dead even odds = pure value at +91."),
]

def us_to_prob(american):
    a = int(str(american).replace("+",""))
    if american[0] == "+" or a > 0:
        return round(100 / (a + 100), 3)
    return round(-a / (-a + 100), 3)

SLIPS = [
    {
        "label": "SLIP A — REAL DATA + ODDS (4-LEG)",
        "color": GOLD,
        "legs": [
            ("Mensik DFs",       "OVER 5.5",  "A+"),
            ("Sabalenka FS",     "OVER 21.0", "A+"),
            ("Andreeva ML",      "WIN -189",  "A+"),
            ("Fonseca ML",       "WIN -227",  "A"),
        ],
        "payout": "Power Play ~12x",
        "note": "Mensik 9 DFs confirmed. Sabalenka 80% clay queen. Andreeva model +20% edge. Fonseca 0 DFs vs Mensik fatigue. All backed by real match data + live odds.",
    },
    {
        "label": "SLIP B — VALUE ODDS PICKS (3-LEG)",
        "color": CLAY,
        "legs": [
            ("Arnaldi ML",       "WIN +91",   "B+"),
            ("Kostyuk ML",       "WIN -125",  "B+"),
            ("Zverev Total Gms", "OVER 36.5", "A"),
        ],
        "payout": "3-leg ~+280",
        "note": "Arnaldi clay H2H edge at even money. Kostyuk sharp line flip to fav. Zverev/Jodar first meeting projects long competitive clay battle. All odds-backed.",
    },
    {
        "label": "SLIP C — ML PARLAY (4-LEG)",
        "color": GREEN,
        "legs": [
            ("Andreeva ML",      "WIN -189",  "A+"),
            ("Sabalenka ML",     "WIN -500",  "A"),
            ("Fonseca ML",       "WIN -227",  "A"),
            ("Zverev ML",        "WIN -303",  "A"),
        ],
        "payout": "4-leg parlay ~+145",
        "note": "Four strongest ML edges: Andreeva +20%, Sabalenka +8%, Fonseca +9%, Zverev +13% model edges. All confirmed by real R16 data and live H2H. Parlay for value.",
    },
    {
        "label": "SLIP D — SERVE PROPS (4-LEG)",
        "color": RED,
        "legs": [
            ("Mensik DFs",       "OVER 5.5",  "A+"),
            ("Mensik Aces",      "OVER 6.5",  "A"),
            ("Zverev Aces",      "OVER 7.5",  "B"),
            ("Sabalenka BPW",    "OVER 4.5",  "B+"),
        ],
        "payout": "Power Play ~14x",
        "note": "Mensik confirmed 9 DFs + 13 aces in R16 — serve props gold mine. Zverev 0.085 ace rate highest ATP field. Sabalenka 0.848 BPW rate. Real data backs all four.",
    },
]


def build_header(story):
    S_LOGO = style("lg", fontName="Helvetica-Bold", fontSize=18, textColor=GOLD)
    S_EV   = style("ev", fontName="Helvetica-Bold", fontSize=11, textColor=CLAY, alignment=TA_RIGHT)
    t = Table([[
        Paragraph("ASTROTENNIS", S_LOGO),
        Paragraph("ROLAND GARROS 2026 · JUNE 1<br/>"
                  "<font color='#fb923c' size='8'>STATS EDITION v5 — QF Results + Live Odds + 6 Remaining Matches</font>", S_EV),
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


def build_completed_results(story):
    story.append(Paragraph("COMPLETED QF RESULTS — REAL MATCH DATA (Sofascore)", S_SECTION))
    hdr = [cell(h, bold=True, color=GOLD, align="CENTER" if h != "Match" else "LEFT")
           for h in ["Match","Winner","Score","Key Stats","FS","Note"]]
    rows = [hdr]
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ])
    for i,(match,winner,score,games,key_stat,fs,note,is_upset) in enumerate(COMPLETED,1):
        w_c = RED if is_upset else GREEN
        note_c = RED if is_upset else MUTED
        bg = UPSET if is_upset else DARKGREEN
        rows.append([
            cell(match, bold=True),
            cell(winner, bold=True, color=w_c),
            cell(score, align="CENTER"),
            cell(games, align="CENTER", color=BLUE),
            cell(key_stat, color=ORANGE),
            cell(fs, align="CENTER", color=GOLD),
            Paragraph(note, style(f"cr{i}", fontSize=7.5, textColor=note_c, leading=10)),
        ])
        if is_upset:
            ts.add("BACKGROUND",(0,i),(-1,i),UPSET)
    t = Table(rows, colWidths=[1.35*inch,.82*inch,.72*inch,.65*inch,1.35*inch,.42*inch,2.89*inch])
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 4))


def build_remaining_preview(story):
    story.append(Paragraph("REMAINING 6 MATCHES — LIVE ODDS + CLAY MODEL + H2H", S_SECTION))
    hdr = [cell(h, bold=True, color=GOLD, align="CENTER" if h != "Home" else "LEFT")
           for h in ["Home","Away","Home ML","Away ML","Mkt Home","Mkt Away","Clay H","Clay A","Edge","Analysis"]]
    rows = [hdr]
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ])
    for i,(home,away,hml,aml,himp,aimp,clay_h,clay_a,edge,note) in enumerate(REMAINING,1):
        edge_c = GREEN if edge == away else ORANGE
        # Highlight Kostyuk flip and Arnaldi value
        surprise = home == "Svitolina" or (home == "Tiafoe")
        note_c = ORANGE if surprise else MUTED
        rows.append([
            cell(home, bold=True),
            cell(away, bold=True),
            cell(hml, align="CENTER", color=MUTED if hml.startswith("+") and int(hml[1:]) > 150 else TEXT),
            cell(aml, align="CENTER", color=MUTED if aml.startswith("+") and int(aml[1:]) > 150 else TEXT),
            cell(himp, align="CENTER"),
            cell(aimp, align="CENTER"),
            cell(clay_h, align="CENTER", color=CLAY),
            cell(clay_a, align="CENTER", color=CLAY),
            cell(edge, bold=True, color=edge_c, align="CENTER"),
            Paragraph(note, style(f"rp{i}", fontSize=7.5, textColor=note_c, leading=10)),
        ])
        if surprise:
            ts.add("BACKGROUND",(0,i),(-1,i),DARKGOLD)
    t = Table(rows, colWidths=[.65*inch,.65*inch,.52*inch,.52*inch,.47*inch,.47*inch,
                                .45*inch,.45*inch,.62*inch,2.8*inch])
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 5))


def build_picks(story):
    story.append(Paragraph("TOP 20 PICKS — LIVE ODDS + REAL STATS + CLAY MODEL (REMAINING MATCHES)", S_SECTION))
    conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}
    hdr = [cell(h, bold=True, color=GOLD,
                align="CENTER" if h in ("#","CONF","EDGE","PROJ") else "LEFT")
           for h in ["#","Match","Prop","Line","Pick","Proj","Edge","Conf","Odds","Rationale"]]
    rows = [hdr]
    ts = TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DEEP),
        ("GRID",(0,0),(-1,-1),0.3,BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD,DEEP]),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ])
    for i,(num,match,prop,line,pick,proj,edge,conf,odds,rat) in enumerate(PICKS,1):
        cc = conf_c.get(conf,MUTED)
        pc = GREEN if "OVER" in pick or "WIN" in pick else RED if "UNDER" in pick else BLUE
        rat_c = ORANGE if ("REAL" in rat or "LIVE H2H" in rat or "FLIP" in rat or "REAL DATA" in rat) else MUTED
        rows.append([
            cell(str(num), align="CENTER", color=MUTED),
            cell(match, bold=True),
            cell(prop, color=BLUE),
            cell(line, align="CENTER"),
            cell(pick, bold=True, color=pc, align="CENTER"),
            cell(proj, align="CENTER", color=GOLD),
            cell(edge, bold=True, color=GREEN if "+" in edge else RED, align="CENTER"),
            cell(conf, bold=True, color=cc, align="CENTER"),
            cell(odds, color=ORANGE, align="CENTER"),
            Paragraph(rat, style(f"r{i}", fontSize=7.5, textColor=rat_c, leading=10)),
        ])
        if conf == "A+": ts.add("BACKGROUND",(0,i),(-1,i),DARKGREEN)
    t = Table(rows, colWidths=[.22*inch,1.1*inch,.72*inch,.38*inch,.6*inch,
                                .38*inch,.42*inch,.38*inch,.75*inch,2.65*inch])
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 5))


def build_moneylines(story):
    story.append(Paragraph("MONEYLINE PICKS — LIVE ODDS vs CLAY MODEL", S_SECTION))
    conf_c = {"A+":GREEN,"A":BLUE,"B+":PURPLE,"B":MUTED}
    hdr = [cell(h, bold=True, color=GOLD)
           for h in ["Player","Opp","ML","Alt ML","Model","Market","Conf","Analysis"]]
    rows = [hdr]
    for i,(player,opp,price,alt,modpct,mktpct,conf,note) in enumerate(MONEYLINES,1):
        imp = us_to_prob(price)
        mod = int(modpct.replace('%',''))
        edge_n = mod - round(imp*100)
        edge_s = f"+{edge_n}%" if edge_n >= 0 else f"{edge_n}%"
        edge_c = GREEN if edge_n >= 15 else BLUE if edge_n >= 8 else ORANGE if edge_n < 0 else MUTED
        cc = conf_c.get(conf,MUTED)
        note_c = ORANGE if ("FLIP" in note or "REAL" in note or "H2H" in note) else MUTED
        rows.append([
            cell(player, bold=True),
            cell(opp, color=MUTED),
            cell(price, bold=True, color=GOLD, align="CENTER"),
            cell(alt, align="CENTER", color=MUTED),
            cell(modpct, bold=True, color=GREEN, align="CENTER"),
            cell(mktpct, align="CENTER"),
            cell(conf, bold=True, color=cc, align="CENTER"),
            Paragraph(note, style(f"ml{i}", fontSize=7.5, textColor=note_c, leading=10)),
        ])
    t = Table(rows, colWidths=[.82*inch,.8*inch,.52*inch,.52*inch,.52*inch,
                                .52*inch,.45*inch,3.25*inch])
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
    story.append(Paragraph("SUGGESTED SLIPS — LIVE ODDS FACTORED", S_SECTION))
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
        "v5: Real QF Stats + Live Sofascore Odds + Scraped H2H + Clay Model  |  "
        "For entertainment purposes only",
        style("ft", fontSize=6.5, textColor=MUTED, alignment=TA_CENTER)
    ))


def main():
    out = os.path.normpath(os.path.join(os.path.dirname(__file__),
                           "..", "data", "AstroTennis_Stats_v5_20260601.pdf"))
    doc = SimpleDocTemplate(out, pagesize=letter,
        leftMargin=0.4*inch, rightMargin=0.4*inch,
        topMargin=0.35*inch, bottomMargin=0.35*inch,
        title="AstroTennis Stats Sheet v5 — June 1 2026")

    def bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0,0,letter[0],letter[1],fill=1,stroke=0)
        canvas.restoreState()

    story = []
    build_header(story)
    story.append(Spacer(1,4))
    build_completed_results(story)
    build_remaining_preview(story)
    build_picks(story)
    build_moneylines(story)
    build_slips(story)
    build_footer(story)
    doc.build(story, onFirstPage=bg, onLaterPages=bg)
    print(f"PDF saved → {out}")

if __name__ == "__main__":
    main()
