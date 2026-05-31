"""
AstroTennis — May 31 2026 Projection Sheet PDF Generator
Uses ReportLab for server-side PDF generation.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable
import os

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#0a0f1e")
DEEP    = colors.HexColor("#111827")
CARD    = colors.HexColor("#1a2035")
BORDER  = colors.HexColor("#1f2d4a")
GOLD    = colors.HexColor("#f5c842")
GREEN   = colors.HexColor("#22c55e")
RED     = colors.HexColor("#ef4444")
BLUE    = colors.HexColor("#38bdf8")
PURPLE  = colors.HexColor("#a78bfa")
CLAY    = colors.HexColor("#c87941")
TEXT    = colors.HexColor("#e2e8f0")
MUTED   = colors.HexColor("#94a3b8")
WHITE   = colors.white
DARKGREEN = colors.HexColor("#14532d")
DARKRED   = colors.HexColor("#450a0a")

# ── Styles ────────────────────────────────────────────────────────────────────
def style(name, **kw):
    defaults = dict(fontName="Helvetica", fontSize=9, textColor=TEXT, leading=12)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

S_LOGO       = style("logo",  fontName="Helvetica-Bold", fontSize=20, textColor=GOLD)
S_TAG        = style("tag",   fontSize=7.5, textColor=MUTED)
S_DATE       = style("date",  fontName="Helvetica-Bold", fontSize=11, textColor=GOLD, alignment=TA_RIGHT)
S_EVENT      = style("event", fontName="Helvetica-Bold", fontSize=8,  textColor=CLAY, alignment=TA_RIGHT)
S_SECTION    = style("sec",   fontName="Helvetica-Bold", fontSize=8,  textColor=MUTED, spaceBefore=10, spaceAfter=4)
S_CELL       = style("cell",  fontSize=8, textColor=TEXT, leading=10)
S_CELL_BOLD  = style("cellb", fontName="Helvetica-Bold", fontSize=8.5, textColor=TEXT, leading=11)
S_MUTED      = style("mut",   fontSize=7.5, textColor=MUTED, leading=10)
S_NOTE       = style("note",  fontSize=7, textColor=MUTED, leading=9)
S_SLIP_TITLE = style("slt",   fontName="Helvetica-Bold", fontSize=9, textColor=TEXT)
S_SLIP_STAT  = style("sls",   fontSize=7, textColor=MUTED, leading=9)
S_DISC       = style("disc",  fontSize=7, textColor=MUTED, leading=10)

def bold(text, color=TEXT):
    return f'<font name="Helvetica-Bold" color="{color.hexval()}">{text}</font>'

def colored(text, color):
    return f'<font color="{color.hexval()}">{text}</font>'

def P(text, s=S_CELL):
    return Paragraph(text, s)

# ── Pick data ─────────────────────────────────────────────────────────────────
HIGH_PICKS = [
    # (rank, player, opponent, stat, dir, line, proj, edge, note)
    (1,  "Zachary Svajda",       "vs Flavio Cobolli",       "Total Games Won",   "UNDER", "13.5", " 8.6", "−4.9",
     "Cobolli (ITA, clay specialist) dominates. Svajda is an American with limited clay pedigree. Expected 6-2 6-1 6-2. Svajda earns 8–9 games max."),
    (2,  "Flavio Cobolli",       "vs Zachary Svajda",       "Total Games",       "UNDER", "32.5", "25.8", "−6.7",
     "3-set blowout. 6-3 6-2 6-2 = 24 total games. Even a solid 3-setter stays well under 32. Line overestimates Svajda's clay resistance."),
    (3,  "Marta Kostyuk",        "vs Iga Swiatek",          "Total Games Won",   "UNDER",  "9.5", " 6.8", "−2.7",
     "Swiatek is historically untouchable at Roland Garros. Even 6-3 6-4 leaves Kostyuk with only 7 games. Line sets a comfortable ceiling."),
    (4,  "Iga Swiatek",          "vs Marta Kostyuk",        "Total Games",       "UNDER", "20.5", "18.1", "−2.4",
     "WTA best-of-3. Swiatek's clay dominance keeps matches short. 6-2 6-3 = 17 games. Needs a competitive 3-setter to clear 21. Unlikely."),
    (5,  "Casper Ruud",          "vs Joao Fonseca",         "Total Games",       "UNDER", "38.5", "30.4", "−8.1",
     "Ruud is a clay master. A 3-set Ruud win (6-4 6-3 6-4 = 33 games) stays well under. Would need a 5-setter to reach 39. Projection strongly under."),
    (6,  "Joao Fonseca",         "vs Casper Ruud",          "Total Games Won",   "UNDER", "19.5", "12.1", "−7.4",
     "Fonseca loses in 3 sets. Wins roughly 10-12 games in that scenario. Would need to steal 2 sets from Ruud on clay to reach 20. Not happening."),
    (7,  "Alexander Zverev",     "vs Jesper De Jong",       "Total Games",       "UNDER", "30.5", "24.6", "−5.9",
     "Zverev (#3 seed) vs De Jong (~#80). 3-set dominant win. 6-2 6-2 6-3 = 25 games. Even 6-4 6-3 6-3 = 29. Enormous edge against the line."),
    (8,  "Naomi Osaka",          "vs Aryna Sabalenka",      "Total Games Won",   "UNDER",  "8.5", " 6.4", "−2.1",
     "Sabalenka playing elite clay tennis. Osaka struggles to hold vs powerful baseliners. 6-3 6-2 leaves Osaka with just 5 games. Clean UNDER."),
    (9,  "Mirra Andreeva",       "vs Jil Teichmann",        "Fantasy Score",     "OVER",  "22.0", "24.3", "+2.3",
     "Andreeva (#5 WTA) is clay-reared. Teichmann prefers grass/fast hard. On clay, Andreeva wins comfortably — games won, BPW, and aces push FS above 22."),
    (10, "Marta Kostyuk",        "vs Iga Swiatek",          "Break Points Won",  "UNDER",  "3.5", " 2.0", "−1.5",
     "Swiatek's serve hold rate on clay is elite (~89%). Kostyuk rarely reaches 4+ BPW in any match, let alone against the best clay player alive."),
]

MID_PICKS = [
    (11, "Jil Teichmann",        "vs Mirra Andreeva",       "Total Games Won",   "UNDER",  "6.5", " 5.1", "−1.4",
     "Pairs with pick #9. Andreeva wins 6-2 6-2 = Teichmann earns 4 games. Even 6-3 6-3 = 6 games. The 6.5 ceiling requires Teichmann to take a full set."),
    (12, "Flavio Cobolli",       "vs Zachary Svajda",       "Fantasy Score",     "OVER",  "28.5", "31.2", "+2.7",
     "3-set dominant win on clay. Cobolli accumulates games won (18+), aces (8-10), and set wins. Line assumes a tight match the model doesn't project."),
    (13, "Matteo Berrettini",    "vs J.M. Cerundolo",       "Total Games",       "OVER",  "38.5", "41.0", "+2.5",
     "Coin-flip match. Two clay baseline warriors with nearly identical profiles. Model projects 4-5 sets highly likely. 4-set avg = ~40 games."),
    (14, "Matteo Berrettini",    "vs J.M. Cerundolo",       "Total Tie Breaks",  "OVER",   "0.5", " 1.1", "+0.6",
     "In a tight 4-5 set clay battle, at least 1 tiebreak is highly probable. Model projects closeness in 2+ sets. At 0.5, this is a near coin-flip with edge."),
    (15, "Rafael Jodar",         "vs Pablo Carreno Busta",  "Total Games",       "OVER",  "35.5", "38.1", "+2.6",
     "Two Spanish clay specialists — Jodar (#29) rising, Carreno Busta the wily veteran. Competitive from game 1. 4-set match is the base case."),
    (16, "Mirra Andreeva",       "vs Jil Teichmann",        "Break Points Won",  "OVER",   "5.0", " 5.9", "+0.9",
     "Andreeva's aggressive return exploits Teichmann's average clay serve. Teichmann's BP save rate drops on slow clay. Model projects 5+ BPW consistently."),
    (17, "Andrey Rublev",        "vs Jakub Mensik",         "Aces",              "UNDER",  "9.5", " 6.8", "−2.7",
     "Clay dramatically suppresses ace rates. Rublev averages 5-7 aces per match on clay. The 9.5 line appears priced off hard-court data. Clear edge."),
    (18, "Madison Keys",         "vs Diana Shnaider",       "Fantasy Score",     "UNDER", "16.0", "13.8", "−2.2",
     "Shnaider (#16 WTA) is the better clay mover right now. Keys has a big serve but struggles on slow clay. If Keys loses in 2 sets, FS craters below 12."),
    (19, "Aryna Sabalenka",      "vs Naomi Osaka",          "Total Games",       "UNDER", "20.5", "18.3", "−2.2",
     "Sabalenka dominates. WTA best-of-3. 6-3 6-2 = 17 total games; 6-4 6-3 = 19. Clearing 20.5 requires Osaka having an elite clay day — unlikely."),
    (20, "Elina Svitolina",      "vs Belinda Bencic",       "Total Games",       "OVER",  "21.5", "23.4", "+1.9",
     "Both fighters returning from long absences. Neither dominates on clay. Model projects competitive 3-setter; even close 2-set 7-5 6-4 = 22 clears line."),
]

SLIPS = [
    {
        "title": "🔥  Dominance Card",
        "legs": "3-Leg Power Play",
        "color": GREEN,
        "legs_data": [
            ("UNDER", "Zachary Svajda",    "Total Games Won",  "13.5"),
            ("UNDER", "Marta Kostyuk",     "Total Games Won",   "9.5"),
            ("UNDER", "Naomi Osaka",       "Total Games Won",   "8.5"),
        ],
        "note": "All three favorites (Cobolli, Swiatek, Sabalenka) are heavy clay-surface operators. Avg model edge: −3.2 games per prop.",
    },
    {
        "title": "🧠  Clean UNDER Card",
        "legs": "3-Leg Totals",
        "color": BLUE,
        "legs_data": [
            ("UNDER", "Iga Swiatek",       "Total Games",      "20.5"),
            ("UNDER", "Casper Ruud",       "Total Games",      "38.5"),
            ("UNDER", "Flavio Cobolli",    "Total Games",      "32.5"),
        ],
        "note": "Three dominant players expected to close matches quickly on clay. Combined projection edge: −17.2 total games below the lines.",
    },
    {
        "title": "💎  Premium 4-Leg Power",
        "legs": "4-Leg Flex",
        "color": GOLD,
        "legs_data": [
            ("UNDER", "Zachary Svajda",    "Total Games Won",  "13.5"),
            ("UNDER", "Marta Kostyuk",     "Total Games Won",   "9.5"),
            ("UNDER", "Casper Ruud",       "Total Games",      "38.5"),
            ("OVER",  "Mirra Andreeva",    "Fantasy Score",    "22.0"),
        ],
        "note": "Top-4 highest-confidence picks combined. All backed by both model projection and clay-surface context. Best unit allocation.",
    },
    {
        "title": "🌀  Contrarian Angle",
        "legs": "4-Leg Mixed",
        "color": PURPLE,
        "legs_data": [
            ("OVER",  "Matteo Berrettini", "Total Games",      "38.5"),
            ("OVER",  "Berrettini Match",  "Total Tie Breaks",  "0.5"),
            ("OVER",  "Rafael Jodar",      "Total Games",      "35.5"),
            ("UNDER", "Madison Keys",      "Fantasy Score",    "16.0"),
        ],
        "note": "Two competitive long matches + one player fade. Higher variance — best as a small-unit flex entry.",
    },
]

# ── Build PDF ─────────────────────────────────────────────────────────────────
out_path = os.path.join(os.path.dirname(__file__), '..', 'AstroTennis_Sheet_20260531.pdf')

doc = SimpleDocTemplate(
    out_path,
    pagesize=letter,
    leftMargin=0.45*inch,
    rightMargin=0.45*inch,
    topMargin=0.45*inch,
    bottomMargin=0.45*inch,
)

story = []

# ── HEADER ────────────────────────────────────────────────────────────────────
header_data = [[
    [P(bold("Astro", GOLD) + colored("Tennis", BLUE), S_LOGO),
     P("Surface-Adjusted Prop Projections", S_TAG)],
    [P("May 31, 2026", S_DATE),
     P("🧱  Roland Garros · Clay · R16 + Doubles QF", S_EVENT)],
]]
header_table = Table(header_data, colWidths=[3.8*inch, 3.5*inch])
header_table.setStyle(TableStyle([
    ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
    ("ALIGN",     (1,0), (1,0),   "RIGHT"),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(header_table)
story.append(HRFlowable(width="100%", thickness=1.5, color=GOLD, spaceAfter=8))

# ── PICKS TABLE function ───────────────────────────────────────────────────────
def picks_table(picks, conf_color):
    col_w = [0.25*inch, 1.45*inch, 1.05*inch, 0.95*inch, 0.42*inch, 0.45*inch, 0.45*inch, 0.42*inch, 2.3*inch]

    hdr = [P(t, ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=7,
                                textColor=MUTED, leading=9))
           for t in ("#", "Player", "Opponent", "Prop", "Dir", "Line", "Proj", "Edge", "Rationale")]
    rows = [hdr]

    for pick in picks:
        rank, player, opp, stat, direction, line, proj, edge, note = pick
        dir_color = GREEN if direction == "OVER" else RED
        edge_color = GREEN if edge.startswith("+") else RED

        rows.append([
            P(str(rank), S_MUTED),
            P(bold(player), S_CELL_BOLD),
            P(opp, S_MUTED),
            P(colored(stat, BLUE), S_CELL),
            P(bold(direction, dir_color), S_CELL_BOLD),
            P(bold(line, GOLD), S_CELL_BOLD),
            P(proj, S_CELL),
            P(bold(edge, edge_color), S_CELL_BOLD),
            P(note, S_NOTE),
        ])

    t = Table(rows, colWidths=col_w, repeatRows=1)
    ts = TableStyle([
        # Header
        ("BACKGROUND",   (0,0), (-1,0),  DEEP),
        ("LINEBELOW",    (0,0), (-1,0),  0.5, BORDER),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [NAVY, DEEP]),
        ("LINEBELOW",    (0,1), (-1,-1), 0.4, BORDER),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        # Confidence accent stripe
        ("LINEBEFORE",   (0,1), (0,-1),  2, conf_color),
    ])
    t.setStyle(ts)
    return t

# High confidence section
story.append(P("⭐  HIGH CONFIDENCE PICKS", S_SECTION))
story.append(picks_table(HIGH_PICKS, GREEN))
story.append(Spacer(1, 8))

# Mid confidence section
story.append(P("📊  MEDIUM CONFIDENCE PICKS", S_SECTION))
story.append(picks_table(MID_PICKS, BLUE))
story.append(Spacer(1, 10))

# ── SLIPS ─────────────────────────────────────────────────────────────────────
story.append(P("🎯  SUGGESTED SLIPS", S_SECTION))

slip_col_w = [3.57*inch, 3.57*inch]
slip_rows = []
for i in range(0, len(SLIPS), 2):
    pair = SLIPS[i:i+2]
    cells = []
    for slip in pair:
        inner = []
        # Slip header
        inner.append(P(bold(slip["title"], slip["color"]) +
                       f'  <font color="{MUTED.hexval()}" size="7">{slip["legs"]}</font>', S_CELL_BOLD))
        inner.append(Spacer(1, 3))
        # Legs
        for direction, player, stat, line in slip["legs_data"]:
            dir_color = GREEN if direction == "OVER" else RED
            inner.append(P(
                bold(f"[{direction}]", dir_color) +
                f'  {bold(player)}  ' +
                colored(f'{stat}  ', MUTED) +
                bold(line, GOLD),
                ParagraphStyle("leg", fontName="Helvetica", fontSize=8, textColor=TEXT, leading=11)
            ))
        inner.append(Spacer(1, 4))
        inner.append(HRFlowable(width="100%", thickness=0.4, color=BORDER))
        inner.append(Spacer(1, 3))
        inner.append(P(slip["note"], S_NOTE))
        cells.append(inner)

    if len(cells) == 1:
        cells.append([P("")])  # pad

    slip_rows.append(cells)

slip_table = Table(slip_rows, colWidths=slip_col_w)
slip_table.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,-1), CARD),
    ("BOX",           (0,0), (0,-1),  0.6, GREEN),
    ("BOX",           (1,0), (1,-1),  0.6, BLUE),
    ("TOPPADDING",    (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ("INNERGRID",     (0,0), (-1,-1), 0.4, BORDER),
]))
story.append(slip_table)

# ── DISCLAIMER ────────────────────────────────────────────────────────────────
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4, spaceAfter=4))
story.append(P(
    bold("AstroTennis Proprietary Projections", GOLD) +
    " — All projections are generated by the AstroTennis surface-adjusted prop model using clay-weighted win rates, "
    "ace/DF profiles, and matchup-adjusted game expectation formulas. Projections are not guarantees of outcome. "
    "Tennis matches contain inherent variance. Play responsibly and within your means. "
    "For AstroTennis subscribers only. Do not distribute.",
    S_DISC
))

# ── BUILD ─────────────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF written → {os.path.abspath(out_path)}")
