"""
AstroTennis — Roland Garros 2026 · June 1 · PrizePicks Edition v6
Active QF Props + SF Preview
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
DARKGREEN = colors.HexColor("#0a1f0a")
DARKRED   = colors.HexColor("#200808")
DARKGOLD  = colors.HexColor("#1a1400")

PAGE_W, PAGE_H = letter
MARGIN = 0.4 * inch
CONTENT_W = PAGE_W - 2 * MARGIN  # 7.7 inches


def mk_style(name, **kw):
    d = dict(fontName="Helvetica", fontSize=8, textColor=TEXT, leading=10)
    d.update(kw)
    return ParagraphStyle(name, **d)


def cell(txt, bold=False, color=None, align="LEFT", size=8, leading=10):
    s = dict(
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        textColor=color or TEXT,
        leading=leading,
        alignment={"LEFT": TA_LEFT, "CENTER": TA_CENTER, "RIGHT": TA_RIGHT}[align],
    )
    return Paragraph(txt, ParagraphStyle(f"c{id(txt)}", **s))


S_SECTION = mk_style("sec", fontName="Helvetica-Bold", fontSize=8, textColor=MUTED,
                     spaceBefore=6, spaceAfter=3)

# ── PICK TABLE COLUMN WIDTHS ────────────────────────────────────────────────
# #(0.22"), Player(0.9"), Prop(0.8"), PP Line(0.52"), Type(0.58"),
# Proj(0.42"), Edge(0.42"), Conf(0.38"), Analysis(3.46") = 7.7"
COL_WIDTHS = [
    0.22 * inch,  # #
    0.9  * inch,  # Player
    0.8  * inch,  # Prop
    0.52 * inch,  # PP Line
    0.58 * inch,  # Type
    0.42 * inch,  # Proj
    0.42 * inch,  # Edge
    0.38 * inch,  # Conf
    3.46 * inch,  # Analysis
]

PICK_HEADER = ["#", "Player", "Prop", "PP Line", "Type", "Proj", "Edge", "Conf", "Analysis"]

TYPE_COLOR  = {"goblin": PURPLE, "demon": RED, "standard": MUTED}
CONF_COLOR  = {"A+": GREEN, "A": BLUE, "B+": PURPLE, "B": MUTED}


def over_under_color(pp_line):
    """Return GREEN for OVER props, RED for UNDER props based on pp_line string."""
    if "UNDER" in pp_line:
        return RED
    return GREEN


def pick_row(num, player, prop, pp_line, typ, proj, edge, conf, analysis, idx):
    """Build one data row for the picks table."""
    bg = DARKGREEN if conf == "A+" else (CARD if idx % 2 == 0 else DEEP)
    edge_val = float(edge)
    edge_color = GREEN if edge_val >= 0 else RED
    edge_str = f"+{edge}" if edge_val >= 0 else str(edge)
    line_color = over_under_color(pp_line)
    # Analysis: highlight REAL keyword in orange
    analysis_txt = analysis.replace("REAL:", '<font color="#fb923c">REAL:</font>')
    return (
        bg,
        [
            cell(str(num), align="CENTER", color=MUTED, size=7),
            cell(player, bold=True, color=TEXT, size=7.5),
            cell(prop, color=TEXT, size=7.5),
            cell(pp_line, bold=True, color=line_color, size=7.5),
            cell(typ, color=TYPE_COLOR.get(typ, MUTED), size=7.5),
            cell(str(proj), color=TEXT, size=7.5),
            cell(edge_str, bold=True, color=edge_color, size=7.5),
            cell(conf, bold=True, color=CONF_COLOR.get(conf, MUTED), size=7.5),
            Paragraph(analysis_txt, ParagraphStyle(f"a{num}", fontName="Helvetica",
                      fontSize=7.5, textColor=MUTED, leading=9)),
        ]
    )


def build_picks_table(rows_data, header_label=None):
    """Build a picks Table from list of (bg, cells) tuples."""
    header_cells = [cell(h, bold=True, color=GOLD, size=7.5, align="CENTER") for h in PICK_HEADER]
    table_data = [header_cells]
    row_bgs = [BORDER]

    for bg, cells_list in rows_data:
        table_data.append(cells_list)
        row_bgs.append(bg)

    t = Table(table_data, colWidths=COL_WIDTHS, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), BORDER),
        ("TEXTCOLOR",  (0, 0), (-1, 0), GOLD),
        ("GRID",       (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [bg for bg in row_bgs[1:]]),
    ]
    # Per-row backgrounds
    for i, bg in enumerate(row_bgs[1:], start=1):
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_cmds))
    return t


# ── ACTIVE QF PICKS ──────────────────────────────────────────────────────────
QF_PICKS_DATA = [
    (1,  "Mensik",   "Double Faults",   "OVER 5.5",   "goblin",   8.5,  3.0,  "A+", "REAL: 9 DFs in R16 5-setter confirmed. Goblin line means PrizePicks expects OVER easily — we agree strongly. Fatigue + 0.040 career DF rate = 7-9 DFs today."),
    (2,  "Andreeva", "Fantasy Score",   "OVER 17.0",  "standard", 22.0, 5.0,  "A+", "REAL: Dominant 2-0 yesterday, fresh legs. Clay H2H 1-0 (Linz 2026). 77.8% clay win rate vs Cirstea 59.3%. +5 pt model gap — best FS edge on board."),
    (3,  "Fonseca",  "Total Games",     "OVER 38.0",  "standard", 41.2, 3.2,  "A+", "H2H: Both prior meetings (Basel + Next Gen) went full distance. Mensik 9 DFs = serve breaks. Fonseca clean but dangerous. Model: 40-43 games on RG clay."),
    (4,  "Zverev",   "Fantasy Score",   "OVER 23.5",  "standard", 26.4, 2.9,  "A",  "FIRST MEETING. Zverev fresh 3-set R16 win. Clay 76.1% + ace rate 0.085 highest in field. Projects 24-27 FS. Market 23.5 underestimates Zverev's dominance on clay."),
    (5,  "Mensik",   "Aces",            "OVER 12.5",  "standard", 13.0, 0.5,  "A",  "REAL: 13 aces in R16. 0.113 career ace rate — highest in field. Even fatigued he serves big. Line is set correctly at 12.5 but he hits exactly here or OVER."),
    (6,  "Zverev",   "Total Games",     "OVER 36.5",  "standard", 39.1, 2.6,  "A",  "FIRST MEETING — no H2H precedent for quick finish. Both clay 75-76%. Jodar saved 10/14 BP in R16 — won't go quietly. Model: 38-41 game battle."),
    (7,  "Kostyuk",  "Fantasy Score",   "OVER 15.5",  "standard", 17.2, 1.7,  "A",  "MARKET FLIP — Kostyuk opened underdog, now -125 favorite. H2H leads recent 2-1. BP created 0.890 — highest WTA field. Model 17+ in close derby."),
    (8,  "Zverev",   "Aces",            "OVER 8.5",   "standard", 9.4,  0.9,  "B+", "0.085 ace rate on clay — highest remaining ATP field. In a potential 4-setter vs first-time opponent, serves big. Projects 9-10 aces."),
    (9,  "Fonseca",  "Fantasy Score",   "OVER 20.0",  "standard", 22.0, 2.0,  "B+", "REAL: 0 DFs in R16, clean 3-set win. H2H 2-0. No fatigue factor. Model 22 FS in dominant QF performance. Line is soft at 20.0."),
    (10, "Andreeva", "Total Games",     "OVER 21.5",  "standard", 23.2, 1.7,  "B+", "Andreeva dominant but Cirstea (59.3% clay) can take games. 0.593 clay win rate = she'll contribute games. Model: 22-24 total in straight-set Andreeva win."),
    (11, "Zverev",   "Total Games Won", "OVER 20.5",  "standard", 22.1, 1.6,  "B+", "If total is 39.1 games and Zverev wins (88% model), he takes ~22-23 games. OVER 20.5 with cushion."),
    (12, "Kostyuk",  "Break Pts Won",   "OVER 5.0",   "standard", 5.7,  0.7,  "B+", "0.890 BP creation rate — highest WTA. Derby pressure favors her aggressive return game. Svitolina slightly fatigued from 3-setter. Kostyuk earns 5-6 BPW."),
    (13, "Mensik",   "Double Faults",   "OVER 6.5",   "demon",    8.5,  2.0,  "B+", "Even the demon (higher) line gets cleared. 9 DFs confirmed real data. Career rate 0.040 stays elevated under 5-set fatigue. 7-9 DFs projected regardless."),
    (14, "Cirstea",  "Total Games Won", "UNDER 11.5", "goblin",   7.1,  -4.4, "B+", "Goblin = lower line, but Cirstea still projected at just 7 games. Andreeva 77.8% clay win rate + clay H2H edge = dominant win. Even \"easy\" goblin gets beaten here."),
    (15, "Jodar",    "Total Games Won", "UNDER 17.5", "standard", 16.8, -0.7, "B",  "Zverev 88% model win, first ever meeting. In 39-game match Zverev wins ~22, Jodar gets ~17 — right at line. Slight UNDER edge given Zverev's clay dominance."),
]

# ── SF PREVIEW PICKS ─────────────────────────────────────────────────────────
SF_PICKS_DATA = [
    (16, "FAA",        "Aces",            "OVER 11.5",  "standard", 13.8, 2.3,  "A+", "REAL: 9 aces in 2-SET QF win. Cobolli won 4-setter. SF = 4-5 sets projected. FAA ace rate 0.070 over longer match = 12-16 aces. Standard line at 11.5 is very hittable."),
    (17, "FAA",        "Double Faults",   "UNDER 4.5",  "standard", 2.1,  -2.4, "A",  "REAL: Only 2 DFs in QF. Career DF rate 0.028 — very reliable serve. Even in a 5-set SF, 4.5 DFs is extremely high for FAA. Strong UNDER."),
    (18, "Sabalenka",  "Total Games Won", "OVER 15.5",  "demon",    17.8, 2.3,  "A",  "Demon line (high threshold) still cleared. Sabalenka 80.4% clay + H2H 3-2. Even if she wins 6-3 6-3 = 18 TGW. Vs Shnaider who just upset Keys, Sabalenka won't be complacent."),
    (19, "Berrettini", "Aces",            "UNDER 10.5", "standard", 6.8,  -3.7, "A",  "REAL: Only 2 aces in QF but 92% 1stIn dominance — he doesn't need aces. Career 0.082 rate projects 6-8 in typical match. 10.5 standard line is severely overpriced. Strong UNDER."),
    (20, "Cobolli",    "Aces",            "OVER 7.5",   "standard", 8.2,  0.7,  "B+", "REAL: 8 aces in 4-set QF. Career 0.053 rate. SF vs FAA will also go long (FAA 2-set QF). In similar 4-set match, Cobolli hits exactly this line or OVER."),
]

# ── COMPLETED QF DATA ────────────────────────────────────────────────────────
COMPLETED = [
    ("Cobolli vs Svajda",        "Cobolli",   "W 4 sets / 25-18 gms", "8A 2DF 53%1st",        "Svajda 4-11 clay career — market was right",               False),
    ("Cerundolo vs Berrettini",  "Berrettini","W 3 sets / 15-13 gms", "2A 0DF 92%1st",        "Cleanest serve display of the round",                      False),
    ("FAA vs Tabilo",            "FAA",       "W 2 sets / 10-8 gms",  "9A 2DF 100%BPS",       "Dominant — won in 2, 100% BP saves",                       False),
    ("Potapova vs Kalinskaya",   "Potapova",  "W 3 sets / 16-15 gms", "1A 8DF 33%BPS",        "Survived 8 DFs, Kalinskaya H2H edge didn't hold",          False),
    ("SHNAIDER def. Keys [UPSET]","Shnaider", "W 3 sets / 15-9 gms",  "Keys 4DF 14%BPS 50UE", "MAJOR UPSET — Keys collapsed completely",                  True),
]


def draw_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()


def build_story():
    story = []

    # ── HEADER ───────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("ASTROTENNIS", ParagraphStyle("h1", fontName="Helvetica-Bold",
                  fontSize=18, textColor=GOLD, leading=22)),
        Paragraph("ROLAND GARROS 2026 · JUNE 1 / PRIZEPICKS EDITION v6 — Active QF Props + SF Preview",
                  ParagraphStyle("h2", fontName="Helvetica", fontSize=11,
                                 textColor=CLAY, leading=14, alignment=TA_RIGHT)),
    ]]
    ht = Table(header_data, colWidths=[3.0 * inch, 4.7 * inch])
    ht.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    story.append(ht)
    story.append(HRFlowable(width="100%", thickness=1.2, color=GOLD, spaceAfter=4))

    # ── SECTION 2: COMPLETED QF RESULTS ─────────────────────────────────────
    story.append(Paragraph("COMPLETED QF RESULTS", S_SECTION))

    comp_header = [
        cell("Match", bold=True, color=GOLD, size=7.5),
        cell("Winner", bold=True, color=GOLD, size=7.5),
        cell("Score", bold=True, color=GOLD, size=7.5),
        cell("Key Stat", bold=True, color=GOLD, size=7.5),
        cell("Note", bold=True, color=GOLD, size=7.5),
    ]
    comp_rows = [comp_header]
    comp_bgs = [BORDER]
    COMP_WIDTHS = [1.6*inch, 0.8*inch, 1.3*inch, 1.1*inch, 2.9*inch]

    for i, (match, winner, score, stat, note, upset) in enumerate(COMPLETED):
        bg = colors.HexColor("#7c1d1d") if upset else (CARD if i % 2 == 0 else DEEP)
        note_color = RED if upset else MUTED
        comp_rows.append([
            cell(match, color=TEXT, size=7.5),
            cell(winner, bold=True, color=GREEN, size=7.5),
            cell(score, color=BLUE, size=7.5),
            cell(stat, color=ORANGE, size=7.5),
            cell(note, color=note_color, size=7.5),
        ])
        comp_bgs.append(bg)

    ct = Table(comp_rows, colWidths=COMP_WIDTHS)
    comp_style = [
        ("BACKGROUND", (0, 0), (-1, 0), BORDER),
        ("GRID",       (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]
    for i, bg in enumerate(comp_bgs[1:], start=1):
        comp_style.append(("BACKGROUND", (0, i), (-1, i), bg))
    ct.setStyle(TableStyle(comp_style))
    story.append(ct)

    # ── SECTION 3: ACTIVE QF PICKS ───────────────────────────────────────────
    story.append(Paragraph("ACTIVE QF MATCHES — PRIZEPICKS LINES vs MODEL PROJECTION", S_SECTION))

    qf_rows = []
    for i, (num, player, prop, pp_line, typ, proj, edge, conf, analysis) in enumerate(QF_PICKS_DATA):
        bg, cells_list = pick_row(num, player, prop, pp_line, typ, proj, edge, conf, analysis, i)
        qf_rows.append((bg, cells_list))
    story.append(build_picks_table(qf_rows))

    # ── SECTION 4: SF PREVIEW ────────────────────────────────────────────────
    story.append(Paragraph("SF PREVIEW — LINES ALREADY POSTED (PrizePicks)", S_SECTION))

    sf_rows = []
    for i, (num, player, prop, pp_line, typ, proj, edge, conf, analysis) in enumerate(SF_PICKS_DATA):
        bg, cells_list = pick_row(num, player, prop, pp_line, typ, proj, edge, conf, analysis, i)
        sf_rows.append((bg, cells_list))
    story.append(build_picks_table(sf_rows))

    # ── SECTION 5: SUGGESTED SLIPS ───────────────────────────────────────────
    story.append(Paragraph("SUGGESTED SLIPS", S_SECTION))

    SLIPS = [
        ("Slip A", "QF POWER PLAY (3-LEG)",
         "Mensik DFs OVER 5.5 goblin (A+), Andreeva FS OVER 17.0 (A+), Fonseca Total Games OVER 38.0 (A+)",
         "~8x",
         "Three A+ picks all backed by real R16 match data. Mensik 9 DFs confirmed. Andreeva dominant. Fonseca vs tired Mensik = long match."),
        ("Slip B", "SF PREVIEW (3-LEG)",
         "FAA Aces OVER 11.5 (A+), FAA DFs UNDER 4.5 (A), Berrettini Aces UNDER 10.5 (A)",
         "~8x",
         "All three grounded in real QF stats. FAA 9 aces in 2-set win — projects higher in SF. Berrettini relied on 92% 1stIn not aces. Both UNDER values are dramatic."),
        ("Slip C", "ML PARLAY (4-LEG)",
         "Andreeva WIN -189 (A+), Zverev WIN -303 (A), Fonseca WIN -227 (A), Kostyuk WIN -125 (B+)",
         "~+125",
         "Four clearest ML edges. Andreeva model +20% over market. Zverev first meeting clay model 88%. Fonseca 0 DFs vs Mensik 9 DFs fatigue. Kostyuk sharp line flip."),
        ("Slip D", "ZVEREV STACK (3-LEG)",
         "Zverev FS OVER 23.5 (A), Zverev Total Games OVER 36.5 (A), Zverev Aces OVER 8.5 (B+)",
         "~8x",
         "First meeting with Jodar = no mental edge, pure clay model. Zverev 76.1% clay + 0.085 ace rate. All three props point same direction — Zverev dominant long win."),
    ]

    slip_header = [
        cell("Slip", bold=True, color=GOLD, size=7.5),
        cell("Name", bold=True, color=GOLD, size=7.5),
        cell("Legs", bold=True, color=GOLD, size=7.5),
        cell("Payout", bold=True, color=GOLD, size=7.5),
        cell("Notes", bold=True, color=GOLD, size=7.5),
    ]
    SLIP_WIDTHS = [0.45*inch, 1.3*inch, 2.2*inch, 0.55*inch, 3.2*inch]
    slip_rows = [slip_header]
    slip_bgs = [BORDER]

    for i, (slip_id, name, legs, payout, notes) in enumerate(SLIPS):
        bg = DARKGOLD if i % 2 == 0 else DEEP
        slip_rows.append([
            cell(slip_id, bold=True, color=GOLD, size=7.5),
            cell(name, bold=True, color=CLAY, size=7.5),
            cell(legs, color=TEXT, size=7.5),
            cell(payout, bold=True, color=GREEN, size=7.5),
            cell(notes, color=MUTED, size=7.5),
        ])
        slip_bgs.append(bg)

    st = Table(slip_rows, colWidths=SLIP_WIDTHS)
    slip_style = [
        ("BACKGROUND", (0, 0), (-1, 0), BORDER),
        ("GRID",       (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]
    for i, bg in enumerate(slip_bgs[1:], start=1):
        slip_style.append(("BACKGROUND", (0, i), (-1, i), bg))
    st.setStyle(TableStyle(slip_style))
    story.append(st)

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=3))
    story.append(Paragraph(
        "AstroTennis · Roland Garros 2026 · June 1  |  v6: PrizePicks lines + AstroTennis model projections  |  For entertainment purposes only",
        ParagraphStyle("footer", fontName="Helvetica", fontSize=7, textColor=MUTED,
                       alignment=TA_CENTER, leading=9)
    ))

    return story


def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, "AstroTennis_Stats_v6_20260601.pdf"))

    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    story = build_story()
    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    print(f"PDF saved → {out_path}")


if __name__ == "__main__":
    main()
