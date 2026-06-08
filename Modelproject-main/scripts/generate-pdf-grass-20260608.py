"""
AstroTennis — June 8 2026 · Grass Court Edition
PrizePicks Picks + Grass Surface Analysis
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
GRASS  = colors.HexColor("#22c55e")   # grass green accent
LIME   = colors.HexColor("#84cc16")
ORANGE = colors.HexColor("#fb923c")
TEXT   = colors.HexColor("#e2e8f0")
MUTED  = colors.HexColor("#94a3b8")
DG     = colors.HexColor("#0a1f0a")
DR     = colors.HexColor("#200808")
DGOLD  = colors.HexColor("#1a1400")
DBLUE  = colors.HexColor("#0a0f20")
DGRASS = colors.HexColor("#052005")


def sty(name, **kw):
    d = dict(fontName="Helvetica", fontSize=8, textColor=TEXT, leading=10)
    d.update(kw)
    return ParagraphStyle(name, **d)


def P(txt, bold=False, color=None, align="LEFT", sz=8, lead=10):
    return Paragraph(txt, ParagraphStyle(f"p{id(txt)}",
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=sz, textColor=color or TEXT, leading=lead,
        alignment={"LEFT": TA_LEFT, "CENTER": TA_CENTER, "RIGHT": TA_RIGHT}[align]))


SEC = sty("sec", fontName="Helvetica-Bold", fontSize=8.5, textColor=GOLD,
          spaceBefore=8, spaceAfter=3)
SEC2 = sty("sec2", fontName="Helvetica-Bold", fontSize=8, textColor=MUTED,
           spaceBefore=5, spaceAfter=2)

CW = 7.7 * inch


def tbl_style(rows=1, stripe=True, hdr_bg=DEEP):
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), hdr_bg),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if stripe:
        ts.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [CARD, DEEP]))
    return TableStyle(ts)


# ═══════════════════════════════════════════════════════════════════════════════
# GRASS COURT STATS
# Format: (grass_wr, aces_per_match, df_per_match, first_srv_pct, serve_dominance)
# serve_dominance = how well player holds serve on grass (0–1)
# ═══════════════════════════════════════════════════════════════════════════════

GRASS_STATS = {
    # ATP
    "GMP":       (0.712, 32.0, 3.1, 0.648, 0.91),   # ace monster
    "T. Paul":   (0.571, 14.0, 3.8, 0.619, 0.78),
    "Hurkacz":   (0.741, 22.0, 2.9, 0.661, 0.92),   # Wimbledon specialist
    "Fucsovics": (0.423, 8.0,  4.2, 0.585, 0.69),
    "Kyrgios":   (0.688, 19.0, 4.5, 0.643, 0.87),   # grass dominator
    "Moutet":    (0.312, 5.0,  5.1, 0.561, 0.61),   # clay grinder, grass struggles
    "Korda":     (0.558, 13.0, 3.4, 0.624, 0.80),
    "Norrie":    (0.611, 10.0, 2.8, 0.618, 0.82),   # UK grass specialist
    "Draper":    (0.667, 15.0, 3.2, 0.638, 0.85),   # UK homegrown talent
    "Shelton":   (0.543, 18.0, 4.0, 0.632, 0.82),
    # WTA
    "Krejcikova":  (0.741, 4.5, 2.8, 0.621, 0.79),  # defending Wimbledon champ
    "Zarazua":     (0.312, 2.1, 4.3, 0.556, 0.58),
    "Kasatkina":   (0.583, 3.8, 3.1, 0.608, 0.74),
    "Montgomery":  (0.421, 2.4, 4.0, 0.571, 0.63),
    "Navarro":     (0.563, 4.1, 2.9, 0.618, 0.76),
    "McNally":     (0.488, 3.4, 3.6, 0.591, 0.69),
    "Kostyuk":     (0.531, 3.6, 3.9, 0.598, 0.72),
    "Stojsavljevic": (0.289, 1.8, 5.2, 0.541, 0.55),
    "Raducanu":    (0.611, 5.2, 3.3, 0.628, 0.77),  # US Open champ, grass suit
    "Blinkova":    (0.463, 3.1, 4.1, 0.579, 0.65),
    "Zheng":       (0.619, 4.3, 2.7, 0.631, 0.78),
    "Alexandrova": (0.538, 5.8, 3.2, 0.616, 0.74),
    "Shnaider":    (0.512, 3.4, 3.8, 0.585, 0.70),
    "Keys":        (0.578, 5.9, 3.5, 0.624, 0.77),
}

# ═══════════════════════════════════════════════════════════════════════════════
# MATCH PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

MATCHES = {
    "GMP vs Tommy Paul": {
        "label": "GMP vs Tommy Paul",
        "round": "R1 Grass",
        "format": "ATP Best of 3",
        "odds_h": "-165", "odds_a": "+135",
        "mkt_h": "62%", "mkt_a": "45%",
        "h2h": "3-2 GMP",
        "h2h_grass": "2-0 GMP",
        "grass_h": "71.2%", "grass_a": "57.1%",
        "notes": [
            "GMP is the premier ace machine on Tour — averages 32 aces/match on grass",
            "Flat, heavy serve causes major problems on fast courts",
            "Tommy Paul plays best on hard courts; grass serve stats drop significantly",
            "GMP holds near perfectly on grass — above 91% hold rate",
        ],
        "picks": [
            ("GMP Aces", "OVER 25.5", "DEMON", "A+", "+0.0", "GMP hits 30+ aces on grass. Demon line still has massive value — model projects 32.4"),
        ],
    },
    "Hurkacz vs Fucsovics": {
        "label": "Hurkacz vs Fucsovics",
        "round": "R1 Grass",
        "format": "ATP Best of 3",
        "odds_h": "-400", "odds_a": "+300",
        "mkt_h": "80%", "mkt_a": "25%",
        "h2h": "4-0 Hurkacz",
        "h2h_grass": "2-0 Hurkacz",
        "grass_h": "74.1%", "grass_a": "42.3%",
        "notes": [
            "Hurkacz is a Wimbledon finalist and one of the best grass servers alive",
            "Averages 22 aces/match on grass with 92%+ hold rate",
            "Fucsovics is a baseline grinder who struggles at net — grass nightmare",
            "Hurkacz has won all 4 meetings; 2 on grass, both in straight sets",
        ],
        "picks": [
            ("Hurkacz Aces", "OVER 18.5", "DEMON", "A", "+2.5", "Hurkacz projects 21 aces on grass. Clean value on the demon line"),
            ("Total Games", "UNDER 22.5", "STANDARD", "B+", "-2.5", "Hurkacz dominant on grass, expect 6-3 6-2 or similar. Grass holds = shorter matches"),
        ],
    },
    "Kyrgios vs Moutet": {
        "label": "Kyrgios vs Moutet",
        "round": "R1 Grass",
        "format": "ATP Best of 3",
        "odds_h": "-250", "odds_a": "+195",
        "mkt_h": "71%", "mkt_a": "34%",
        "h2h": "1-0 Kyrgios",
        "h2h_grass": "1-0 Kyrgios",
        "grass_h": "68.8%", "grass_a": "31.2%",
        "notes": [
            "Kyrgios is arguably the most naturally gifted grass court player — holds 87% on grass",
            "Moutet is a clay specialist who struggles on pace. Grass plays into every Kyrgios strength",
            "Enormous surface mismatch — Moutet's topspin baseline game completely neutralized",
            "Kyrgios serves and volleys, huge serve, wicked slice. Moutet has no answer on grass",
        ],
        "picks": [
            ("Total Games", "UNDER 23.0", "STANDARD", "A", "-3.0", "Kyrgios dominates Moutet on grass. Model says 19-20 total games. Strong UNDER"),
        ],
    },
    "Krejcikova vs Zarazua": {
        "label": "Krejcikova vs Zarazua",
        "round": "R1 Grass",
        "format": "WTA Best of 3",
        "odds_h": "-500", "odds_a": "+370",
        "mkt_h": "83%", "mkt_a": "21%",
        "h2h": "1-0 Krejcikova",
        "h2h_grass": "No previous grass H2H",
        "grass_h": "74.1%", "grass_a": "31.2%",
        "notes": [
            "Krejcikova is the defending Wimbledon champion — this is her best surface",
            "Uses net approach and varied serve brilliantly on grass",
            "Zarazua is a clay/hard specialist ranked outside top 80",
            "Massive ranking and experience gap — Krejcikova should cruise in straights",
        ],
        "picks": [
            ("Total Games", "UNDER 19.0", "STANDARD", "A", "-2.5", "Krejcikova dominates lower-ranked opponent on her best surface. Model: 16-17 total games"),
        ],
    },
    "Kasatkina vs Montgomery": {
        "label": "Kasatkina vs Montgomery",
        "round": "R1 Grass",
        "format": "WTA Best of 3",
        "odds_h": "-180", "odds_a": "+148",
        "mkt_h": "64%", "mkt_a": "40%",
        "h2h": "2-1 Kasatkina",
        "h2h_grass": "1-0 Kasatkina",
        "grass_h": "58.3%", "grass_a": "42.1%",
        "notes": [
            "Kasatkina top-20 player with solid all-surface game and consistent first serve",
            "Montgomery competitive but drops off significantly on grass",
            "Kasatkina averages 3.8 aces/match on grass with 74% hold rate",
            "Model projects 17.2 fantasy score — standard line at 16.5 has edge",
        ],
        "picks": [
            ("Kasatkina Fantasy Score", "OVER 16.5", "STANDARD", "B+", "+0.7", "Kasatkina's serve-volley combo on grass generates FS. Projects 17.2 vs 16.5 line"),
        ],
    },
    "Navarro vs McNally": {
        "label": "Navarro vs McNally",
        "round": "R1 Grass",
        "format": "WTA Best of 3",
        "odds_h": "-145", "odds_a": "+115",
        "mkt_h": "59%", "mkt_a": "47%",
        "h2h": "1-1",
        "h2h_grass": "No previous grass H2H",
        "grass_h": "56.3%", "grass_a": "48.8%",
        "notes": [
            "Tight matchup — both players have similar grass court records",
            "Navarro has the serve edge on grass (4.1 aces vs McNally 3.4)",
            "McNally is a fighter who can extend matches — both hold reasonably well",
            "Close match likely means more games played — lean OVER total",
        ],
        "picks": [
            ("Total Games", "OVER 21.5", "STANDARD", "B", "+0.5", "Competitive matchup between two even players. Expect 3 sets and 22+ total games"),
        ],
    },
    "Kostyuk vs Stojsavljevic": {
        "label": "Kostyuk vs Stojsavljevic",
        "round": "R1 Grass",
        "format": "WTA Best of 3",
        "odds_h": "-350", "odds_a": "+270",
        "mkt_h": "78%", "mkt_a": "27%",
        "h2h": "No previous H2H",
        "h2h_grass": "No previous H2H",
        "grass_h": "53.1%", "grass_a": "28.9%",
        "notes": [
            "Massive ranking gap — Kostyuk top 30 vs Stojsavljevic ranked ~130",
            "Stojsavljevic is a wildcard/qualifier — limited grass data",
            "Kostyuk's aggressive game translates well to faster grass courts",
            "Huge favorite, expect straight-set victory with minimal drama",
        ],
        "picks": [
            ("Total Games", "UNDER 18.5", "STANDARD", "B+", "-2.5", "Top-30 vs qualifier on grass. Kostyuk dominates — model says 15-16 total games"),
        ],
    },
    "Raducanu vs Blinkova": {
        "label": "Raducanu vs Blinkova",
        "round": "R1 Grass",
        "format": "WTA Best of 3",
        "odds_h": "-195", "odds_a": "+157",
        "mkt_h": "66%", "mkt_a": "39%",
        "h2h": "1-1",
        "h2h_grass": "1-0 Raducanu",
        "grass_h": "61.1%", "grass_a": "46.3%",
        "notes": [
            "Raducanu is a UK crowd favorite and grass specialist — US Open champ",
            "Averaging 5.2 aces/match on grass, 77% hold rate",
            "Blinkova is a competent all-rounder but grass is her weakest surface",
            "Raducanu has the serve and return advantage on this surface",
        ],
        "picks": [
            ("Raducanu Fantasy Score", "OVER 17.5", "STANDARD", "B+", "+0.8", "Raducanu on home grass is a different player. Model projects 18.3 FS"),
        ],
    },
    "Alexandrova vs Shnaider": {
        "label": "Alexandrova vs Shnaider",
        "round": "R1 Grass",
        "format": "WTA Best of 3",
        "odds_h": "-130", "odds_a": "+105",
        "mkt_h": "57%", "mkt_a": "49%",
        "h2h": "2-1 Alexandrova",
        "h2h_grass": "1-0 Alexandrova",
        "grass_h": "53.8%", "grass_a": "51.2%",
        "notes": [
            "Very competitive matchup — both players capable on grass",
            "Alexandrova has the serve edge (5.8 vs 3.4 aces/match on grass)",
            "Shnaider made QF at Roland Garros — excellent form but clay specialist",
            "Alexandrova FS line at 21.0 standard — her serve should generate big FS",
        ],
        "picks": [
            ("Alexandrova Fantasy Score", "OVER 21.0", "STANDARD", "B", "+1.0", "Alexandrova's big serve on grass. Model projects 22.0 FS. Slight edge on standard"),
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# PICKS SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════════════════════

ALL_PICKS = [
    # (Match, Player/Prop, Line Type, Line, Pick, Grade, Edge, Rationale)
    ("GMP vs T. Paul",     "GMP Aces",          "DEMON",    "O 25.5", "OVER",  "A+", "+6.4", "Ace machine on grass — projects 32.4"),
    ("Hurkacz vs Fucsovics","Hurkacz Aces",      "DEMON",    "O 18.5", "OVER",  "A",  "+2.5", "Wimbledon specialist, 22 aces/match avg"),
    ("Hurkacz vs Fucsovics","Total Games",       "STANDARD", "U 22.5", "UNDER", "B+", "-2.5", "Hurkacz dominates, fast grass holds"),
    ("Kyrgios vs Moutet",  "Total Games",        "STANDARD", "U 23.0", "UNDER", "A",  "-3.0", "Massive surface mismatch, Kyrgios cruise"),
    ("Krejcikova vs Zarazua","Total Games",      "STANDARD", "U 19.0", "UNDER", "A",  "-2.5", "Defending Wimb champ vs ranked-80+ opp"),
    ("Kasatkina vs Mont.", "Kasatkina FS",       "STANDARD", "O 16.5", "OVER",  "B+", "+0.7", "Serve + hold on grass = FS upside"),
    ("Navarro vs McNally", "Total Games",        "STANDARD", "O 21.5", "OVER",  "B",  "+0.5", "Even matchup, 3 sets likely"),
    ("Kostyuk vs Stojsav.","Total Games",        "STANDARD", "U 18.5", "UNDER", "B+", "-2.5", "Top-30 vs qualifier, dominant expected"),
    ("Raducanu vs Blinkova","Raducanu FS",       "STANDARD", "O 17.5", "OVER",  "B+", "+0.8", "UK grass fav, 18.3 FS projected"),
    ("Alexandrova vs Shn.","Alexandrova FS",     "STANDARD", "O 21.0", "OVER",  "B",  "+1.0", "Big server advantage on grass"),
]

# ═══════════════════════════════════════════════════════════════════════════════
# SLIP COMBOS
# ═══════════════════════════════════════════════════════════════════════════════

SLIPS = [
    {
        "title": "GRASS ACE HAMMER (2-Pick)",
        "grade": "A+",
        "legs": [
            ("GMP Aces OVER 25.5", "DEMON", "A+"),
            ("Hurkacz Aces OVER 18.5", "DEMON", "A"),
        ],
        "note": "Two Wimbledon-caliber servers on grass. Both averaging 20+ aces. Highest-confidence slip.",
    },
    {
        "title": "SURFACE MISMATCH UNDERS (3-Pick)",
        "grade": "A",
        "legs": [
            ("Kyrgios/Moutet TG UNDER 23.0", "STANDARD", "A"),
            ("Krejcikova/Zarazua TG UNDER 19.0", "STANDARD", "A"),
            ("Kostyuk/Stojsav TG UNDER 18.5", "STANDARD", "B+"),
        ],
        "note": "Three mismatches: clay grinders vs grass specialists. All three should be quick.",
    },
    {
        "title": "FANTASY SCORE TRIO (3-Pick)",
        "grade": "B+",
        "legs": [
            ("Kasatkina FS OVER 16.5", "STANDARD", "B+"),
            ("Raducanu FS OVER 17.5", "STANDARD", "B+"),
            ("Alexandrova FS OVER 21.0", "STANDARD", "B"),
        ],
        "note": "Three top players expected to dominate. Grass serve = fantasy score upside.",
    },
    {
        "title": "GRASS GRAND SLAM (4-Pick)",
        "grade": "A",
        "legs": [
            ("GMP Aces OVER 25.5", "DEMON", "A+"),
            ("Kyrgios/Moutet TG UNDER 23.0", "STANDARD", "A"),
            ("Krejcikova/Zarazua TG UNDER 19.0", "STANDARD", "A"),
            ("Hurkacz Aces OVER 18.5", "DEMON", "A"),
        ],
        "note": "Best 4-pick combo. High confidence throughout. Servers on grass = money.",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# PDF BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_header(story):
    story.append(Table(
        [[P("🎾  AstroTennis", bold=True, color=GOLD, sz=20, lead=24),
          P("GRASS COURT EDITION", bold=True, color=LIME, sz=11, align="RIGHT")]],
        colWidths=[CW * 0.65, CW * 0.35],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    ))
    story.append(Table(
        [[P("June 8, 2026  ·  Grass Season Begins  ·  PrizePicks Analysis", color=MUTED, sz=8, align="CENTER")]],
        colWidths=[CW],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DEEP),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    ))
    story.append(Spacer(1, 6))


def build_surface_banner(story):
    story.append(KeepTogether([
        Table(
            [[P("⚡  SURFACE SHIFT: CLAY → GRASS", bold=True, color=LIME, sz=9, align="CENTER")]],
            colWidths=[CW],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), DGRASS),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 1.0, GRASS),
            ])
        ),
        Spacer(1, 4),
        Table(
            [[
                P("GRASS COURT RULES", bold=True, color=GOLD, sz=8, align="CENTER"),
                P("WHAT CHANGES", bold=True, color=GOLD, sz=8, align="CENTER"),
            ]],
            colWidths=[CW * 0.5, CW * 0.5],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        ),
        Table(
            [
                [
                    P("• Big servers DOMINATE on grass\n• Holds are easier — fewer break points\n• Rallies are shorter — quick points\n• Serve-and-volley effective again\n• Clay grinders STRUGGLE with pace", color=TEXT, sz=7.5, lead=12),
                    P("• Ace rates go UP (avg +40% vs clay)\n• Total games go DOWN (faster holds)\n• Break points go DOWN significantly\n• Fantasy Scores skew higher for servers\n• 3-set matches less common for favorites", color=TEXT, sz=7.5, lead=12),
                ],
            ],
            colWidths=[CW * 0.5, CW * 0.5],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), DEEP),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        ),
        Spacer(1, 8),
    ]))


def build_match_card(story, m):
    gs = GRASS_STATS
    h_name = m["label"].split(" vs ")[0].strip()
    a_name = m["label"].split(" vs ")[1].strip()

    h_gs = gs.get(h_name, (0, 0, 0, 0, 0))
    a_gs = gs.get(a_name, (0, 0, 0, 0, 0))

    h_wr, h_aces, h_df, h_1st, h_hold = h_gs
    a_wr, a_aces, a_df, a_1st, a_hold = a_gs

    rnd_color = GRASS

    card_elements = [
        Table(
            [[
                P(f"{m['label']}", bold=True, color=GOLD, sz=10, lead=13),
                P(f"{m['round']}  ·  {m['format']}", color=rnd_color, sz=8, align="RIGHT"),
            ]],
            colWidths=[CW * 0.65, CW * 0.35],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, rnd_color),
            ])
        ),
        # Odds + H2H
        Table(
            [[
                P(f"Odds: {h_name} {m['odds_h']}  ·  {a_name} {m['odds_a']}", color=BLUE, sz=8),
                P(f"H2H: {m['h2h']}  ·  Grass: {m['h2h_grass']}", color=MUTED, sz=7.5, align="RIGHT"),
            ]],
            colWidths=[CW * 0.55, CW * 0.45],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), DEEP),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        ),
        # Grass stats comparison
        Table(
            [
                [P("GRASS STATS", bold=True, color=GOLD, sz=7.5, align="CENTER"),
                 P(h_name, bold=True, color=BLUE, sz=7.5, align="CENTER"),
                 P(a_name, bold=True, color=ORANGE, sz=7.5, align="CENTER")],
                [P("Grass Win Rate", sz=7.5), P(f"{h_wr:.1%}", color=GREEN if h_wr > a_wr else TEXT, sz=7.5, align="CENTER"), P(f"{a_wr:.1%}", color=GREEN if a_wr > h_wr else TEXT, sz=7.5, align="CENTER")],
                [P("Aces / Match", sz=7.5), P(f"{h_aces:.1f}", color=BLUE if h_aces > a_aces else TEXT, sz=7.5, align="CENTER"), P(f"{a_aces:.1f}", color=BLUE if a_aces > h_aces else TEXT, sz=7.5, align="CENTER")],
                [P("Double Faults", sz=7.5), P(f"{h_df:.1f}", color=GREEN if h_df < a_df else RED, sz=7.5, align="CENTER"), P(f"{a_df:.1f}", color=GREEN if a_df < h_df else RED, sz=7.5, align="CENTER")],
                [P("1st Serve %", sz=7.5), P(f"{h_1st:.1%}", color=BLUE if h_1st > a_1st else TEXT, sz=7.5, align="CENTER"), P(f"{a_1st:.1%}", color=BLUE if a_1st > h_1st else TEXT, sz=7.5, align="CENTER")],
                [P("Hold Rate (Grass)", sz=7.5), P(f"{h_hold:.1%}", color=LIME if h_hold > a_hold else TEXT, sz=7.5, align="CENTER"), P(f"{a_hold:.1%}", color=LIME if a_hold > h_hold else TEXT, sz=7.5, align="CENTER")],
            ],
            colWidths=[CW * 0.38, CW * 0.31, CW * 0.31],
            style=tbl_style()
        ),
        Spacer(1, 3),
        # Analysis notes
        Table(
            [[P("  ".join(f"▸ {n}" for n in m["notes"]), color=MUTED, sz=7, lead=11)]],
            colWidths=[CW],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ])
        ),
    ]

    # Picks for this match
    if m.get("picks"):
        pick_rows = [[
            P("PROP", bold=True, color=GOLD, sz=7),
            P("LINE", bold=True, color=GOLD, sz=7, align="CENTER"),
            P("TYPE", bold=True, color=GOLD, sz=7, align="CENTER"),
            P("PICK", bold=True, color=GOLD, sz=7, align="CENTER"),
            P("GRADE", bold=True, color=GOLD, sz=7, align="CENTER"),
            P("MODEL EDGE", bold=True, color=GOLD, sz=7, align="CENTER"),
        ]]
        for prop, line, ptype, grade, edge, rationale in m["picks"]:
            pick_dir = "OVER" if "O " in line or "OVER" in line.upper() else "UNDER"
            pick_color = GREEN if pick_dir == "OVER" else RED
            type_color = PURPLE if ptype == "DEMON" else (ORANGE if ptype == "GOBLIN" else BLUE)
            grade_color = GREEN if grade in ("A+", "A") else (GOLD if grade == "B+" else MUTED)
            edge_val = float(edge.replace("+", "")) if edge else 0
            edge_color = GREEN if edge_val > 0 else RED

            pick_rows.append([
                P(prop, sz=7),
                P(line, bold=True, color=TEXT, sz=7, align="CENTER"),
                P(ptype, bold=True, color=type_color, sz=7, align="CENTER"),
                P(pick_dir, bold=True, color=pick_color, sz=7, align="CENTER"),
                P(grade, bold=True, color=grade_color, sz=7, align="CENTER"),
                P(edge, bold=True, color=edge_color, sz=7, align="CENTER"),
            ])

        card_elements.append(
            Table(pick_rows, colWidths=[CW*0.28, CW*0.13, CW*0.12, CW*0.12, CW*0.10, CW*0.14],
                  style=tbl_style())
        )
        # Rationale
        for prop, line, ptype, grade, edge, rationale in m["picks"]:
            card_elements.append(
                Table([[P(f"  ↳ {prop}: {rationale}", color=MUTED, sz=6.5, lead=9)]],
                      colWidths=[CW],
                      style=TableStyle([
                          ("BACKGROUND", (0,0),(-1,-1), NAVY),
                          ("TOPPADDING", (0,0),(-1,-1), 2),
                          ("BOTTOMPADDING", (0,0),(-1,-1), 2),
                          ("LEFTPADDING", (0,0),(-1,-1), 8),
                      ]))
            )

    card_elements.append(Spacer(1, 10))
    story.append(KeepTogether(card_elements))


def build_picks_summary(story):
    story.append(Paragraph("ALL PICKS — JUNE 8 2026", SEC))

    grade_order = {"A+": 0, "A": 1, "B+": 2, "B": 3, "B-": 4}
    sorted_picks = sorted(ALL_PICKS, key=lambda x: grade_order.get(x[6], 9))

    rows = [[
        P("#", bold=True, color=GOLD, sz=7.5, align="CENTER"),
        P("MATCH", bold=True, color=GOLD, sz=7.5),
        P("PROP / LINE", bold=True, color=GOLD, sz=7.5),
        P("TYPE", bold=True, color=GOLD, sz=7.5, align="CENTER"),
        P("PICK", bold=True, color=GOLD, sz=7.5, align="CENTER"),
        P("GRADE", bold=True, color=GOLD, sz=7.5, align="CENTER"),
        P("EDGE", bold=True, color=GOLD, sz=7.5, align="CENTER"),
    ]]

    for i, (match, prop, ptype, line, pick, grade, edge, rat) in enumerate(sorted_picks, 1):
        pick_color = GREEN if pick == "OVER" else RED
        type_color = PURPLE if ptype == "DEMON" else (ORANGE if ptype == "GOBLIN" else BLUE)
        grade_color = GREEN if grade in ("A+","A") else (GOLD if grade == "B+" else MUTED)
        edge_val = float(edge.replace("+","")) if edge else 0
        edge_color = GREEN if edge_val > 0 else RED

        rows.append([
            P(str(i), color=MUTED, sz=7.5, align="CENTER"),
            P(match, sz=7.5),
            P(f"{prop}  {line}", sz=7.5),
            P(ptype, bold=True, color=type_color, sz=7.5, align="CENTER"),
            P(pick, bold=True, color=pick_color, sz=7.5, align="CENTER"),
            P(grade, bold=True, color=grade_color, sz=7.5, align="CENTER"),
            P(edge, bold=True, color=edge_color, sz=7.5, align="CENTER"),
        ])

    story.append(Table(
        rows,
        colWidths=[CW*0.05, CW*0.20, CW*0.30, CW*0.11, CW*0.10, CW*0.10, CW*0.09],
        style=tbl_style()
    ))
    story.append(Spacer(1, 8))


def build_slips(story):
    story.append(Paragraph("PRIZE PICKS SLIPS", SEC))

    for slip in SLIPS:
        grade_color = GREEN if slip["grade"] in ("A+","A") else (GOLD if slip["grade"] == "B+" else MUTED)
        rows = [[
            P(slip["title"], bold=True, color=LIME, sz=8.5),
            P(f"Grade: {slip['grade']}", bold=True, color=grade_color, sz=8.5, align="RIGHT"),
        ]]
        leg_table_rows = [[
            P("LEG", bold=True, color=GOLD, sz=7, align="CENTER"),
            P("PROP", bold=True, color=GOLD, sz=7),
            P("TYPE", bold=True, color=GOLD, sz=7, align="CENTER"),
            P("CONF", bold=True, color=GOLD, sz=7, align="CENTER"),
        ]]
        for j, (prop, ptype, conf) in enumerate(slip["legs"], 1):
            type_color = PURPLE if ptype == "DEMON" else (ORANGE if ptype == "GOBLIN" else BLUE)
            conf_color = GREEN if conf in ("A+","A") else (GOLD if conf == "B+" else MUTED)
            leg_table_rows.append([
                P(str(j), color=MUTED, sz=7, align="CENTER"),
                P(prop, sz=7),
                P(ptype, bold=True, color=type_color, sz=7, align="CENTER"),
                P(conf, bold=True, color=conf_color, sz=7, align="CENTER"),
            ])

        story.append(KeepTogether([
            Table(rows, colWidths=[CW * 0.75, CW * 0.25],
                  style=TableStyle([
                      ("BACKGROUND", (0,0),(-1,-1), DGRASS),
                      ("TOPPADDING", (0,0),(-1,-1), 5),
                      ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                      ("LEFTPADDING", (0,0),(-1,-1), 8),
                      ("RIGHTPADDING", (0,0),(-1,-1), 8),
                      ("BOX", (0,0),(-1,-1), 0.8, GRASS),
                  ])),
            Table(leg_table_rows,
                  colWidths=[CW*0.07, CW*0.56, CW*0.18, CW*0.14],
                  style=tbl_style()),
            Table(
                [[P(f"  ↳ {slip['note']}", color=MUTED, sz=7, lead=9)]],
                colWidths=[CW],
                style=TableStyle([
                    ("BACKGROUND", (0,0),(-1,-1), NAVY),
                    ("TOPPADDING", (0,0),(-1,-1), 3),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 5),
                    ("LEFTPADDING", (0,0),(-1,-1), 8),
                ])
            ),
            Spacer(1, 8),
        ]))


def build_footer(story):
    story.append(HRFlowable(width=CW, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4))
    story.append(Table(
        [[
            P("AstroTennis proprietary model  ·  Grass surface analytics  ·  June 8 2026", color=MUTED, sz=6.5),
            P("For entertainment purposes only  ·  Bet responsibly", color=MUTED, sz=6.5, align="RIGHT"),
        ]],
        colWidths=[CW * 0.6, CW * 0.4],
        style=TableStyle([
            ("TOPPADDING", (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ])
    ))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

os.makedirs("data", exist_ok=True)
OUT = "data/AstroTennis_Grass_20260608.pdf"

doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    leftMargin=0.4*inch, rightMargin=0.4*inch,
    topMargin=0.4*inch, bottomMargin=0.4*inch,
)

story = []
build_header(story)
build_surface_banner(story)

story.append(Paragraph("MATCH ANALYSIS — GRASS COURT SEASON", SEC))

for match_key, match_data in MATCHES.items():
    build_match_card(story, match_data)

build_picks_summary(story)
build_slips(story)
build_footer(story)

doc.build(story)
print(f"✓  Saved → {OUT}")
