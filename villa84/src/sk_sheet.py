"""Dimension sheets (A3) of the living room and the ceiling projector + drop-down screen, for building a SketchUp model.

Local coordinates in metres: origin at the inner south-west corner of the living room, x along the short side (8.35),
y along the long side (11.35) toward the media wall, z up from the finished floor.
Usage: python sk_sheet.py out.html
"""
import math
import os
import sys

from shapely.geometry import box as sbox
from shapely.ops import unary_union

OUT = sys.argv[1]
sys.argv = [sys.argv[0], os.path.join(os.path.dirname(os.path.abspath(OUT)), "_plans_tmp.html")]
import sheets as SH  # noqa: E402  (re-uses the plan renderer; writes the regular plan sheets to the temp file)
import model as M  # noqa: E402
from symbols import Canvas  # noqa: E402

# ------------------------------------------------------------------ design data (metres)
OX, OY = 27.35, 22.35                       # villa coordinates of the local origin
W, D = 8.35, 11.35                          # clear room size
ZC, ZS, ZR, ZP = 5.00, 5.20, 5.50, 5.90     # ceiling underside, slab underside, roof top, parapet top
GH = 4.60                                   # top of the glass walls
OPEN_H = 2.60                               # opening to the entrance hall
S_GL, E_GL, W_OP = (0.55, 7.75), (0.55, 10.75), (0.55, 5.55)
LIB = (2.20, 6.10, 10.95)                   # library: x0, x1, front face y
MARBLE = [(0.55, 2.20), (6.10, 7.80)]
MARBLE_Y = 11.05
CAB_H = 0.92
SHELF_Z = [CAB_H + k * (ZC - CAB_H) / 9 for k in range(10)]
BAYS = [2.20, 3.175, 4.15, 5.125, 6.10]
CX = 4.15                                   # axis of the projector, the screen and the library
SY = 10.70                                  # screen plane
SCR_W, IMG_W, IMG_H, BORDER, TOP_DROP, DROP = 4.20, 3.98, 2.24, 0.11, 1.76, 4.08
IMG_B, IMG_T = 1.00, 3.24
PY = 4.95                                   # projector axis
HATCH, PANEL, BODY = (0.70, 0.60), (0.67, 0.57, 0.022), (0.50, 0.40, 0.158)
LIFT = 1.85
SOFA = (1.60, 2.25, 6.70, 3.35)
CHAISE = (6.70, 2.25, 7.75, 4.75)
RUG = (0.60, 2.15, 7.90, 7.15)
TABLE, SIDE = (3.85, 6.25, 0.72, 0.36), (5.35, 6.85, 0.40, 0.30)
CHAIRS = [(0.65, 7.05, 1.50, 7.90), (0.65, 8.45, 1.50, 9.30)]
EYE = (2.80, 1.15)

T, TS, DIM = "TEXT", "TEXT-S", "DIM"


def cm(v):
    s = f"{v * 100:.1f}"
    return s[:-2] if s.endswith(".0") else s


# ================================================================== sheet 1: plan
def plan():
    c = Canvas()
    shell = sbox(-0.15, -0.30, W + 0.30, D + 0.30).difference(sbox(0, 0, W, D))
    cuts = unary_union([sbox(S_GL[0], -0.30, S_GL[1], 0), sbox(W, E_GL[0], W + 0.30, E_GL[1]), sbox(-0.15, W_OP[0], 0, W_OP[1])])
    for p in M.polys(shell.difference(cuts)):
        c.poly(list(p.exterior.coords)[:-1], "WALL", fill="wall")
    for k in (-0.19, -0.11):
        c.line((S_GL[0], k), (S_GL[1], k), "GLASS")
    for k in (0.11, 0.19):
        c.line((W + k, E_GL[0]), (W + k, E_GL[1]), "GLASS")
    for x in (-0.15, 0.0):
        c.line((x, W_OP[0]), (x, W_OP[1]), "BELOW", dash="3 2")
    # media wall
    c.rect(LIB[0], LIB[2], LIB[1], D, "FIX")
    for x in BAYS[1:-1]:
        c.line((x, LIB[2]), (x, D), "FIX")
    for a, b in MARBLE:
        c.rect(a, MARBLE_Y, b, D, "FIX", fill="dark")
    # ceiling parts
    c.rect(CX - 2.25, SY - 0.04, CX + 2.25, SY + 0.04, "CEIL", dash="3 1.5", w=0.3)
    c.rect(CX - HATCH[0] / 2, PY - HATCH[1] / 2, CX + HATCH[0] / 2, PY + HATCH[1] / 2, "CEIL", dash="3 1.5", w=0.3)
    c.rect(CX - BODY[0] / 2, PY - BODY[1] / 2, CX + BODY[0] / 2, PY + BODY[1] / 2, "CEIL", w=0.25)
    c.line((CX, PY + 0.2), (CX - IMG_W / 2, SY), "CEIL", dash="1 2", w=0.15)
    c.line((CX, PY + 0.2), (CX + IMG_W / 2, SY), "CEIL", dash="1 2", w=0.15)
    # furniture
    c.rect(*RUG, "RUG", dash="4 2")
    x0, y0, x1, y1 = SOFA
    c.rrect(x0, y0, x1, y1, 0.08, "FURN")
    c.line((x0, y0 + 0.26), (x1, y0 + 0.26), "FURN")
    for i in range(1, 5):
        c.line((x0 + i * (x1 - x0) / 5, y0 + 0.26), (x0 + i * (x1 - x0) / 5, y1), "FURN")
    c.rrect(*CHAISE, 0.08, "FURN")
    c.circle(TABLE[:2], TABLE[2], "FURN")
    c.circle(SIDE[:2], SIDE[2], "FURN")
    for q in CHAIRS:
        c.rrect(*q, 0.1, "FURN")
    c.circle((CX, EYE[0]), 0.07, "LEVEL", fill="dark")
    # labels
    c.text((CX, PY - 0.52), "מקרן על ליפט, בתקרה", TS, h=0.12)
    c.text((CX, SY - 0.22), "מסך נגלל 180״, חריץ בתקרה 450×8", TS, h=0.12)
    c.text((CX, D - 0.2), "ספרייה", TS, h=0.12)
    c.text((1.375, D - 0.15), "שיש", TS, h=0.11)
    c.text((6.95, D - 0.15), "שיש", TS, h=0.11)
    c.text((4.15, 2.62), "ספה 510×110", TS, h=0.12)
    c.text((7.22, 3.9), "שזלונג", TS, h=0.11)
    c.text((7.22, 3.68), "105×250", TS, h=0.1)
    c.text(TABLE[:2], "שולחן ⌀144", TS, h=0.11)
    c.text(SIDE[:2], "⌀80", TS, h=0.11)
    c.text((1.08, 8.15), "2 כורסאות 85×85", TS, h=0.11)
    c.text((2.3, 6.9), "שטיח 730×500", TS, h=0.11)
    c.text((CX + 0.55, EYE[0]), "עין הצופה", TS, h=0.1)
    c.text((-0.75, 3.05), "פתח למבואת הכניסה", TS, h=0.12, rot=90)
    c.text((4.15, -0.52), "קיר זכוכית אל מרפסת הגג והגינה", TS, h=0.12)
    c.text((W + 0.56, 5.65), "קיר זכוכית אל הבריכה", TS, h=0.12, rot=90)
    c.text((4.15, D + 0.52), "קיר המדיה, קיר אטום", TS, h=0.12)
    c.circle((0, 0), 0.09, "LEVEL", fill="dark")
    c.text((0.42, 0.28), "0,0", "LEVEL", h=0.12, bold=True)
    # dimensions (cm)
    for a, b in zip((0, S_GL[0], S_GL[1], W), (S_GL[0], S_GL[1], W, None)):
        if b is not None:
            c.dim((a, -0.30), (b, -0.30), "H", -0.98, h=0.14)
    c.dim((0, -0.30), (W, -0.30), "H", -1.33, h=0.15)
    ys = (0, E_GL[0], E_GL[1], D)
    for a, b in zip(ys, ys[1:]):
        c.dim((W + 0.30, a), (W + 0.30, b), "V", W + 1.08, h=0.14)
    c.dim((W + 0.30, 0), (W + 0.30, D), "V", W + 1.48, h=0.15)
    ys = (0, W_OP[0], W_OP[1], D)
    for a, b in zip(ys, ys[1:]):
        c.dim((-0.15, a), (-0.15, b), "V", -1.1, h=0.14)
    xs = (0, MARBLE[0][0], LIB[0], LIB[1], MARBLE[1][1], W)
    for a, b in zip(xs, xs[1:]):
        c.dim((a, D + 0.30), (b, D + 0.30), "H", D + 0.85, h=0.14)
    # positions inside
    xs = (0, SOFA[0], SOFA[2], CHAISE[2], W)
    for a, b in zip(xs, xs[1:]):
        c.dim((a, 1.7), (b, 1.7), "H", 1.7, h=0.12)
    c.dim((1.05, 0), (1.05, SOFA[1]), "V", 1.05, h=0.12)
    c.dim((1.05, SOFA[1]), (1.05, SOFA[3]), "V", 1.05, h=0.12)
    ys = (0, PY, SY, LIB[2], D)
    for a, b in zip(ys, ys[1:]):
        c.dim((5.0, a), (5.0, b), "V", 5.0, h=0.12)
    c.dim((0, PY + 0.62), (CX, PY + 0.62), "H", PY + 0.62, h=0.12)
    c.dim((CX, PY + 0.62), (W, PY + 0.62), "H", PY + 0.62, h=0.12)
    xs = (0, CX - SCR_W / 2, CX + SCR_W / 2, W)
    for a, b in zip(xs, xs[1:]):
        c.dim((a, 10.05), (b, 10.05), "H", 10.05, h=0.12)
    c.dim((5.75, EYE[0]), (5.75, SY), "V", 5.75, h=0.12)
    c.text((6.02, 7.6), "מרחק צפייה", TS, h=0.1, rot=90)
    return c


# ================================================================== sheet 2: long section (y, z) and media wall elevation (x, z)
def section():
    c = Canvas()
    c.rect(-0.30, -0.30, D + 0.30, 0.0, "SEC-CUT", fill="slab")
    c.rect(-0.30, ZS, D + 0.30, ZR, "SEC-CUT", fill="slab")
    for a in (-0.30, D + 0.10):
        c.rect(a, ZR, a + 0.20, ZP, "SEC-CUT", fill="wall")
    c.rect(-0.30, GH, 0.0, ZS, "SEC-CUT", fill="wall")
    c.line((-0.15, 0.0), (-0.15, GH), "GLASS", w=0.35)
    c.rect(D, 0.0, D + 0.30, ZS, "SEC-CUT", fill="wall")
    # floating ceiling with the hatch and the screen slot
    for a, b in ((0.15, PY - HATCH[1] / 2), (PY + HATCH[1] / 2, SY - 0.04), (SY + 0.04, LIB[2])):
        c.rect(a, ZC, b, ZC + 0.06, "SEC-CUT", fill="white")
    c.rect(SY - 0.09, ZC + 0.06, SY + 0.09, ZS - 0.01, "FIX")
    c.circle((SY, ZC + 0.125), 0.045, "FIX")
    # library and the screen in front of it
    c.rect(LIB[2], 0.0, D, ZC, "FIX")
    c.line((LIB[2], CAB_H), (D, CAB_H), "FIX")
    for z in SHELF_Z[1:-1]:
        c.line((LIB[2], z), (D, z), "FIX")
    c.line((SY, IMG_T), (SY, ZC), "SEC-CUT", w=0.7)
    c.line((SY, IMG_B), (SY, IMG_T), "GLASS", w=0.7)
    c.rect(SY - 0.014, ZC - DROP, SY + 0.014, ZC - DROP + 0.03, "FIX", fill="dark")
    # projector: lowered (solid) and stowed (dashed)
    zb = ZC - LIFT
    c.rect(PY - PANEL[1] / 2, zb, PY + PANEL[1] / 2, zb + PANEL[2], "FIX", fill="white")
    c.rect(PY - BODY[1] / 2, zb + PANEL[2], PY + BODY[1] / 2, zb + PANEL[2] + BODY[2], "FIX", fill="dark")
    c.rect(PY + BODY[1] / 2, zb + 0.05, PY + BODY[1] / 2 + 0.04, zb + 0.15, "FIX", fill="dark")
    c.line((PY, zb + 0.18), (PY, ZS), "FIX", w=0.4)
    c.rect(PY - BODY[1] / 2, ZC + PANEL[2], PY + BODY[1] / 2, ZC + PANEL[2] + BODY[2], "CEIL", dash="2 1.5")
    c.line((PY - PANEL[1] / 2, ZC), (PY + PANEL[1] / 2, ZC), "CEIL", dash="2 1.5")
    lens = (PY + 0.24, zb + 0.10)
    c.line(lens, (SY, IMG_T), "CEIL", dash="1 2", w=0.15)
    c.line(lens, (SY, IMG_B), "CEIL", dash="1 2", w=0.15)
    # sofa, table, viewer
    y0, y1 = SOFA[1], SOFA[3]
    c.rect(y0 + 0.06, 0.0, y1 - 0.06, 0.08, "FURN", fill="dark")
    c.rect(y0, 0.08, y1, 0.30, "FURN", fill="white")
    c.rect(y0 + 0.26, 0.30, y1, 0.47, "FURN", fill="white")
    c.rect(y0, 0.30, y0 + 0.26, 0.82, "FURN", fill="white")
    c.rect(TABLE[1] - TABLE[2], 0.0, TABLE[1] + TABLE[2], TABLE[3], "FURN", fill="white")
    c.circle(EYE, 0.06, "LEVEL", fill="dark")
    c.line(EYE, (SY, IMG_T), "LEVEL", dash="1 2", w=0.12)
    c.line(EYE, (SY, IMG_B), "LEVEL", dash="1 2", w=0.12)
    # labels
    c.text((PY - 1.25, zb + 0.1), "מקרן במצב הקרנה", TS, h=0.12)
    c.text((PY + 1.5, ZC - 0.22), "מקרן מאוחסן בתקרה", TS, h=0.12)
    c.text((SY - 1.0, 2.1), "מסך פתוח", TS, h=0.12)
    c.text((SY - 1.0, 1.9), "תמונה 398×224", TS, h=0.11)
    c.text((D - 0.2, -0.16), "", TS, h=0.1)
    c.text((2.8, 1.38), "עין 115", TS, h=0.11)
    c.text((2.8, -0.17), "ספה", TS, h=0.11)
    c.text((TABLE[1], -0.17), "שולחן", TS, h=0.11)
    c.text((SY - 1.15, ZC - 0.22), "גליל המסך, בחלל התקרה", TS, h=0.11)
    c.text((1.9, ZC - 0.22), "תקרה צפה, מעליה חלל של 20", TS, h=0.11)
    c.text((-0.62, 2.3), "קיר זכוכית", TS, h=0.11, rot=90)
    # heights
    for a, b in ((0.0, GH), (GH, ZS), (ZS, ZR), (ZR, ZP)):
        c.dim((-0.30, a), (-0.30, b), "V", -1.0, h=0.13)
    c.dim((-0.30, 0.0), (-0.30, ZC), "V", -1.5, h=0.13)
    zs = (0.0, CAB_H, IMG_B, IMG_T, ZC, ZS)
    for a, b in zip(zs, zs[1:]):
        c.dim((D + 0.30, a), (D + 0.30, b), "V", D + 1.0, h=0.13)
    c.dim((D + 0.30, ZC - DROP), (D + 0.30, ZC), "V", D + 1.5, h=0.13)
    c.dim((PY - 0.75, 0.0), (PY - 0.75, zb), "V", PY - 0.75, h=0.12)
    c.dim((PY - 0.75, zb), (PY - 0.75, ZC), "V", PY - 0.75, h=0.12)
    ys = (0.0, SOFA[1], SOFA[3], PY, SY, LIB[2], D)
    for a, b in zip(ys, ys[1:]):
        c.dim((a, -0.30), (b, -0.30), "H", -0.85, h=0.13)
    c.dim((0.0, -0.30), (D, -0.30), "H", -1.3, h=0.13)
    c.dim((EYE[0], 0.72), (SY, 0.72), "H", 0.72, h=0.12)
    c.dim((lens[0], 3.72), (SY, 3.72), "H", 3.72, h=0.12)
    return c


def elevation():
    c = Canvas()
    c.rect(0.0, 0.0, W, ZC, "WALL")
    c.rect(-0.15, -0.30, W + 0.30, 0.0, "SEC-CUT", fill="slab")
    c.rect(-0.15, ZS, W + 0.30, ZR, "SEC-CUT", fill="slab")
    c.rect(0.0, ZC, W, ZC + 0.06, "FIX")
    for a, b in MARBLE:
        c.rect(a, 0.0, b, ZC, "FIX", fill="roof2")
    for x in (1.375, 6.95):
        c.line((x, 0.0), (x, ZC), "FIX", w=0.1)
    c.rect(LIB[0], 0.0, LIB[1], ZC, "FIX", fill="white")
    c.rect(LIB[0], 0.0, LIB[1], 0.06, "FIX", fill="dark")
    c.line((LIB[0], CAB_H), (LIB[1], CAB_H), "FIX", w=0.3)
    for x in BAYS[1:-1]:
        c.line((x, 0.06), (x, ZC), "FIX")
    for z in SHELF_Z[1:-1]:
        c.line((LIB[0], z), (LIB[1], z), "FIX")
    # the lowered screen, dashed
    c.rect(CX - SCR_W / 2, ZC - DROP, CX + SCR_W / 2, ZC, "CEIL", dash="4 2", w=0.35)
    c.rect(CX - IMG_W / 2, IMG_B, CX + IMG_W / 2, IMG_T, "CEIL", dash="2 2", w=0.25)
    c.text((1.375, 2.6), "שיש כהה", TS, h=0.12)
    c.text((6.95, 2.6), "שיש כהה", TS, h=0.12)
    c.text((CX, 0.5), "ארון תחתון, 4 דלתות", TS, h=0.12)
    c.text((CX, 2.2), "ספרייה מעץ אגוז", TS, h=0.12)
    c.text((CX, 2.0), "קו מקווקו: המסך כשהוא פתוח", TS, h=0.11)
    xs = (0, MARBLE[0][0], LIB[0], LIB[1], MARBLE[1][1], W)
    for a, b in zip(xs, xs[1:]):
        c.dim((a, -0.30), (b, -0.30), "H", -0.85, h=0.13)
    c.dim((0, -0.30), (W, -0.30), "H", -1.3, h=0.13)
    for a, b in zip(BAYS, BAYS[1:]):
        c.dim((a, 1.38), (b, 1.38), "H", 1.38, h=0.11, txt="97.5")
    zs = (0.0, CAB_H, SHELF_Z[1], SHELF_Z[2])
    for a, b in zip(zs, zs[1:]):
        c.dim((W, a), (W, b), "V", W + 0.75, h=0.12, txt=cm(b - a))
    c.dim((W, 0.0), (W, ZC), "V", W + 1.25, h=0.13)
    c.text((W + 0.75, 3.2), "9 מדפים", TS, h=0.11, rot=90)
    c.dim((0.0, 0.0), (0.0, ZC), "V", -0.7, h=0.13)
    c.dim((CX - SCR_W / 2, 3.9), (CX + SCR_W / 2, 3.9), "H", 3.9, h=0.12)
    return c


# ================================================================== sheet 3: details
def proj_plan():
    c = Canvas()
    hw, hd = HATCH[0] / 2, HATCH[1] / 2
    c.rect(-hw, -hd, hw, hd, "CEIL", dash="3 2", w=0.3)
    c.rect(-PANEL[0] / 2, -PANEL[1] / 2, PANEL[0] / 2, PANEL[1] / 2, "FIX")
    c.rrect(-BODY[0] / 2, -BODY[1] / 2, BODY[0] / 2, BODY[1] / 2, 0.014, "FIX", fill="roof2")
    c.rect(0.1 - 0.062, BODY[1] / 2, 0.1 + 0.062, BODY[1] / 2 + 0.03, "FIX", fill="dark")
    for x in (-0.18, 0.18):
        c.circle((x, 0.0), 0.019, "FIX")
    c.text((0.0, 0.08), "גוף המקרן", TS, h=0.022)
    c.text((0.1, BODY[1] / 2 + 0.06), "עדשה", TS, h=0.02)
    c.text((0.0, -0.055), "2 תרנים טלסקופיים", TS, h=0.019)
    c.text((0.0, hd + 0.12), "אל המסך", TS, h=0.022)
    c.line((0.0, hd + 0.03), (0.0, hd + 0.09), "FIX")
    for sx in (-0.02, 0.02):
        c.line((0.0, hd + 0.09), (sx, hd + 0.065), "FIX")
    c.dim((-hw, -hd), (hw, -hd), "H", -hd - 0.14, h=0.024)
    c.dim((-PANEL[0] / 2, -hd), (PANEL[0] / 2, -hd), "H", -hd - 0.085, h=0.022)
    c.dim((-BODY[0] / 2, -hd), (BODY[0] / 2, -hd), "H", -hd - 0.035, h=0.022)
    c.dim((hw, -hd), (hw, hd), "V", hw + 0.14, h=0.024)
    c.dim((hw, -PANEL[1] / 2), (hw, PANEL[1] / 2), "V", hw + 0.085, h=0.022)
    c.dim((hw, -BODY[1] / 2), (hw, BODY[1] / 2), "V", hw + 0.035, h=0.022)
    c.dim((0.0, 0.14), (0.1, 0.14), "H", 0.14, h=0.02)
    c.dim((-0.18, -0.12), (0.18, -0.12), "H", -0.12, h=0.02)
    return c


def proj_side():
    c = Canvas()
    c.rect(-PANEL[1] / 2, 0.0, PANEL[1] / 2, PANEL[2], "FIX", fill="white")
    c.rect(-BODY[1] / 2, PANEL[2], BODY[1] / 2, PANEL[2] + BODY[2], "FIX", fill="roof2")
    c.rect(BODY[1] / 2, 0.10 - 0.062, BODY[1] / 2 + 0.03, 0.10 + 0.062, "FIX", fill="dark")
    c.rect(BODY[1] / 2 + 0.03, 0.10 - 0.05, BODY[1] / 2 + 0.042, 0.10 + 0.05, "FIX", fill="dark")
    c.line((0.0, 0.18), (0.0, 0.36), "FIX", w=0.5)
    c.text((0.0, 0.1), "גוף המקרן", TS, h=0.022)
    c.text((-0.12, -0.035), "לוח סגירה, בגוון התקרה", TS, h=0.02)
    c.text((0.07, 0.3), "תורן", TS, h=0.02)
    c.dim((-PANEL[1] / 2, 0.0), (PANEL[1] / 2, 0.0), "H", -0.09, h=0.022)
    c.dim((-BODY[1] / 2, 0.18), (BODY[1] / 2, 0.18), "H", 0.24, h=0.022)
    c.dim((-PANEL[1] / 2, 0.0), (-PANEL[1] / 2, PANEL[2]), "V", -PANEL[1] / 2 - 0.05, h=0.02, txt="2.2")
    c.dim((-PANEL[1] / 2, PANEL[2]), (-PANEL[1] / 2, 0.18), "V", -PANEL[1] / 2 - 0.05, h=0.02, txt="15.8")
    c.dim((-PANEL[1] / 2, 0.0), (-PANEL[1] / 2, 0.18), "V", -PANEL[1] / 2 - 0.12, h=0.022)
    c.dim((BODY[1] / 2 + 0.042, 0.0), (BODY[1] / 2 + 0.042, 0.10), "V", BODY[1] / 2 + 0.11, h=0.02)
    c.text((BODY[1] / 2 + 0.2, 0.05), "ציר העדשה", TS, h=0.019)
    return c


def lift_states():
    c = Canvas()
    for ox, lift, name in ((0.0, 0.0, "סגור: הלוח בקו התקרה"), (1.75, LIFT, "פתוח: ירידה של 185 ס״מ")):
        c.rect(ox - 0.75, ZS, ox + 0.75, ZS + 0.3, "SEC-CUT", fill="slab")
        for a, b in ((ox - 0.75, ox - HATCH[1] / 2), (ox + HATCH[1] / 2, ox + 0.75)):
            c.rect(a, ZC, b, ZC + 0.06, "SEC-CUT", fill="white")
        zb = ZC - lift
        c.rect(ox - PANEL[1] / 2, zb, ox + PANEL[1] / 2, zb + PANEL[2], "FIX", fill="white")
        c.rect(ox - BODY[1] / 2, zb + PANEL[2], ox + BODY[1] / 2, zb + 0.18, "FIX", fill="roof2")
        c.rect(ox + BODY[1] / 2, zb + 0.04, ox + BODY[1] / 2 + 0.04, zb + 0.16, "FIX", fill="dark")
        if lift:
            c.line((ox, zb + 0.18), (ox, ZS), "FIX", w=0.5)
            c.dim((ox - 0.5, zb), (ox - 0.5, ZC), "V", ox - 0.5, h=0.05)
            c.dim((ox + 0.62, zb + 0.10), (ox + 0.62, ZC), "V", ox + 0.62, h=0.045)
        c.text((ox, ZS + 0.42), name, TS, h=0.055)
    c.dim((-0.75, ZC), (-0.75, ZS), "V", -0.95, h=0.05)
    c.dim((-0.75, ZS), (-0.75, ZS + 0.3), "V", -0.95, h=0.05)
    c.text((0.0, ZC - 0.12), "מפלס התקרה +500", TS, h=0.05)
    c.text((1.75, ZC - LIFT - 0.14), "תחתית הלוח +315, ציר העדשה +325", TS, h=0.05)
    return c


def screen_front():
    c = Canvas()
    x0, x1 = -SCR_W / 2, SCR_W / 2
    c.rect(-2.25, DROP, 2.25, DROP + 0.2, "SEC-CUT", fill="slab")
    c.rect(x0, DROP - TOP_DROP, x1, DROP, "FIX", fill="dark")
    c.rect(x0, 0.03, x1, DROP - TOP_DROP, "FIX", fill="dark")
    c.rect(-IMG_W / 2, 0.08, IMG_W / 2, 0.08 + IMG_H, "FIX", fill="white")
    c.rect(x0 - 0.01, 0.0, x1 + 0.01, 0.03, "FIX", fill="roof2")
    c.text((0.0, 1.3), "שטח התמונה", TS, h=0.13)
    c.text((0.0, 1.05), "398×224, יחס 16:9, אלכסון 180״", TS, h=0.11)
    c.text((0.0, DROP + 0.1), "תקרה", TS, h=0.1)
    c.dim((x0, 0.0), (x1, 0.0), "H", -0.75, h=0.12)
    xs = (x0, -IMG_W / 2, IMG_W / 2, x1)
    for a, b in zip(xs, xs[1:]):
        c.dim((a, 0.0), (b, 0.0), "H", -0.35, h=0.11)
    zs = (0.0, 0.08, 0.08 + IMG_H, DROP)
    for a, b in zip(zs, zs[1:]):
        c.dim((x1, a), (x1, b), "V", x1 + 0.5, h=0.11, txt=cm(b - a))
    c.text((x1 + 0.62, -0.28), "8 = מוט 3 + שוליים 5", TS, h=0.1)
    c.dim((x1, 0.0), (x1, DROP), "V", x1 + 1.0, h=0.12)
    return c


def sofa_side():
    c = Canvas()
    d = SOFA[3] - SOFA[1]
    c.line((-0.25, 0.0), (d + 0.25, 0.0), "FIX", w=0.4)
    c.rect(0.06, 0.0, d - 0.06, 0.08, "FURN", fill="dark")
    c.rect(0.0, 0.08, d, 0.30, "FURN", fill="white")
    c.rect(0.26, 0.30, d, 0.47, "FURN", fill="white")
    c.rect(0.0, 0.30, 0.26, 0.82, "FURN", fill="white")
    c.rect(0.0, 0.08, d, 0.62, "FURN", dash="2 1.5")
    c.text((d / 2 + 0.1, 0.385), "מושב", TS, h=0.045)
    c.text((0.13, 0.9), "גב", TS, h=0.045)
    c.dim((0.0, 0.0), (d, 0.0), "H", -0.27, h=0.05)
    c.dim((0.0, 0.0), (0.26, 0.0), "H", -0.15, h=0.045)
    c.dim((0.26, 0.0), (d, 0.0), "H", -0.15, h=0.045)
    zs = (0.0, 0.08, 0.30, 0.47)
    for a, b in zip(zs, zs[1:]):
        c.dim((d, a), (d, b), "V", d + 0.16, h=0.045)
    c.dim((d, 0.0), (d, 0.62), "V", d + 0.32, h=0.045)
    c.dim((0.0, 0.0), (0.0, 0.82), "V", -0.16, h=0.05)
    c.text((d + 0.42, 0.31), "משענת יד", TS, h=0.04, rot=90)
    return c


# ================================================================== page assembly
CSS = """
@page { size: 420mm 297mm; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; color: #111; background: #fff; }
.sheet { position: relative; width: 420mm; height: 297mm; overflow: hidden; page-break-after: always; background: #fff; }
.sheet svg { position: absolute; left: 0; top: 0; width: 420mm; height: 297mm; }
.t { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; direction: rtl; paint-order: stroke; stroke: #fff; stroke-width: 0.8px; stroke-linejoin: round; }
.n { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; direction: ltr; paint-order: stroke; stroke: #fff; stroke-width: 0.8px; stroke-linejoin: round; }
.frame { position: absolute; left: 7mm; top: 7mm; right: 7mm; bottom: 7mm; border: 0.4mm solid #111; }
.panel { position: absolute; top: 7mm; bottom: 7mm; right: 7mm; border-left: 0.4mm solid #111; direction: rtl; padding: 5mm 5mm 4mm; font-size: 2.9mm; line-height: 1.4;
         display: flex; flex-direction: column; }
.panel h1 { font-size: 6.4mm; line-height: 1.15; }
.panel .sub { font-size: 3.4mm; color: #444; margin-top: 1mm; }
.panel h2 { font-size: 3.7mm; border-bottom: 0.3mm solid #111; padding-bottom: 0.6mm; margin: 4mm 0 1.5mm; }
.panel table { border-collapse: collapse; width: 100%; font-size: 2.65mm; }
.panel td, .panel th { text-align: right; padding: 0.55mm 0.8mm; border-bottom: 0.12mm solid #cfcfcf; vertical-align: top; }
.panel th { border-bottom: 0.25mm solid #111; font-size: 2.5mm; }
.panel td.n { direction: ltr; text-align: left; white-space: nowrap; }
.panel tr.grp td { font-weight: 700; background: #f1efe9; }
.panel ul { list-style: none; }
.panel li { padding-right: 3mm; position: relative; margin-bottom: 0.7mm; }
.panel li::before { content: "•"; position: absolute; right: 0; }
.tb { margin-top: auto; border-top: 0.4mm solid #111; padding-top: 2mm; display: grid; grid-template-columns: 1fr 1fr; gap: 1mm 3mm; font-size: 2.7mm; }
.tb b { display: block; font-size: 2.3mm; color: #555; font-weight: 400; }
.tb .big { font-size: 5mm; font-weight: 700; }
"""
esc = SH.esc


def title(x, y, s, size=4.6):
    return f'<text class="t" x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="700" text-anchor="start">{esc(s)}</text>'


def panel(width, head, sub, num, scale, body):
    return (f'<div class="panel" style="width:{width}mm"><h1>{esc(head)}</h1><div class="sub">{esc(sub)}</div>{body}'
            f'<div class="tb"><div><b>פרויקט</b>וילה במגרש 84 · הרהיט: מקרן ומסך נסתרים</div><div><b>יחידות</b>כל המידות בס״מ</div>'
            f'<div><b>קנה מידה</b><span class="big">{scale}</span></div><div><b>דף</b><span class="big">{num}</span></div></div></div>')


def sheet(svg, pan):
    return f'<div class="sheet"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297">{svg}</svg><div class="frame"></div>{pan}</div>'


def row(name, size, pos):
    return f'<tr><td>{esc(name)}</td><td class="n">{esc(size)}</td><td>{esc(pos)}</td></tr>'


def grp(name):
    return f'<tr class="grp"><td colspan="3">{esc(name)}</td></tr>'


pages = []
NP = 5


def pos(x=None, y=None, z=None, pre=""):
    parts = [f"{k}={v}" for k, v in (("X", x), ("Y", y), ("Z", z)) if v is not None]
    return f'{esc(pre)}<span dir="ltr">{" · ".join(parts)}</span>'


def prow(name, size, where):
    return f'<tr><td>{esc(name)}</td><td class="n">{esc(size)}</td><td>{where}</td></tr>'


# ---- 1: plan 1:50
v = SH.View(-1.45, -1.55, W + 1.8, D + 1.1, 50, 10, 9.5)
svg = SH.render(plan(), v, text_k=1.0, clip_id="p1")
body = ('<h2>איך לקרוא את הדף</h2><ul>'
        '<li>נקודת האפס היא הפינה הפנימית של הסלון ליד מבואת הכניסה. X לרוחב הסלון, Y לאורכו אל קיר המדיה, Z מהרצפה למעלה.</li>'
        '<li>המיקום בטבלה הוא הפינה של החלק שקרובה לנקודת האפס. כשכתוב ״מרכז״, זה מרכז החלק.</li></ul>'
        '<h2>רשימת החלקים</h2><table><tr><th>חלק</th><th>רוחב × עומק × גובה</th><th>מיקום</th></tr>'
        + grp("מעטפת הסלון")
        + prow("חלל הסלון", "835 × 1135 × 500", pos(0, 0, 0) + ". עד תקרת הבטון: 520")
        + prow("קירות חוץ", "עובי 30", "דרום־מערב, מזרח וצפון־מזרח")
        + prow("קיר למבואה", "עובי 15", "פתח 500 × 260, מ־" + pos(y=55))
        + prow("קיר זכוכית לגינה", "720 × 460", "בקיר הדרומי, מ־" + pos(x=55))
        + prow("קיר זכוכית לבריכה", "1020 × 460", "בקיר המזרחי, מ־" + pos(y=55))
        + prow("תקרה צפה", "805 × 1080 × 6", pos(z=500) + ", רווח 15 מהקירות")
        + prow("תקרת בטון", "עובי 30", pos(z=520) + ", מעקה עד 590")
        + grp("קיר המדיה")
        + prow("ספרייה מעץ אגוז", "390 × 40 × 500", pos(220, 1095, 0))
        + prow("ארון תחתון", "390 × 40 × 92", "4 דלתות של 97.5")
        + prow("מדפים", "9 שורות", "מרווח 45.3, עובי 3.5")
        + prow("לוח שיש שמאלי", "165 × 30 × 500", pos(55, 1105, 0))
        + prow("לוח שיש ימני", "170 × 30 × 500", pos(610, 1105, 0))
        + grp("הרהיט: מסך")
        + prow("חריץ בתקרה", "450 × 8", pos(415, 1070, pre="מרכז "))
        + prow("בד המסך", "420 × 408", pos(205, 1070, 92))
        + prow("שטח התמונה", "398 × 224", pos(216, 1070, 100))
        + prow("פס שחור עליון", "420 × 176", pos(205, 1070, 324))
        + prow("מוט משקולת", "422 × 2.8 × 3", pos(z=92) + " כשהמסך פתוח")
        + prow("בית הגליל", "450 × 18 × 14", "מעל החריץ, בחלל התקרה")
        + grp("הרהיט: מקרן על ליפט")
        + prow("פתח בתקרה", "70 × 60", pos(415, 495, pre="מרכז "))
        + prow("לוח סגירה", "67 × 57 × 2.2", "סגור " + pos(z=500) + ", פתוח " + pos(z=315))
        + prow("גוף המקרן", "50 × 40 × 15.8", "על הלוח. עדשה ⌀10 בחזית")
        + prow("מהלך הליפט", "185", "2 תרנים, 18 מכל צד של המרכז")
        + grp("ריהוט הסלון")
        + prow("ספה, 5 מושבים", "510 × 110 × 82", pos(160, 225, 0))
        + prow("שזלונג", "105 × 250 × 47", pos(670, 225, 0))
        + prow("שולחן קפה עגול", "⌀144 × 36", pos(385, 625, pre="מרכז "))
        + prow("שולחן צד עגול", "⌀80 × 30", pos(535, 685, pre="מרכז "))
        + prow("2 כורסאות", "85 × 85", pos(65, 705) + " וגם " + pos(65, 845))
        + prow("שטיח", "730 × 500", pos(60, 215))
        + '</table>')
pages.append(sheet(svg, panel(172, "הסלון והרהיט · תוכנית", "דף מידות לבניית המודל בסקצ׳אפ", f"1/{NP}", "1:50", body)))

# ---- 2: long section 1:50, sofa profile 1:20
vs = SH.View(-1.9, -1.6, D + 1.9, 6.2, 50, 10, 22)
vf = SH.View(-0.35, -0.3, 1.75, 1.05, 20, 34, 22 + vs.h + 14)
svg = SH.render(section(), vs, clip_id="p2a") + SH.render(sofa_side(), vf, clip_id="p2f")
svg += title(10 + vs.w, 16, "חתך לאורך הסלון, דרך המקרן והמסך · 1:50")
svg += title(34 + vf.w + 62, 22 + vs.h + 20, "הספה, חתך · 1:20")
svg += (f'<text class="t" x="{34 + vf.w + 62}" y="{22 + vs.h + 30}" font-size="3" text-anchor="start">בסיס שחור 8, גוף עד 30, מושב עד 47, גב עד 82.</text>'
        f'<text class="t" x="{34 + vf.w + 62}" y="{22 + vs.h + 36}" font-size="3" text-anchor="start">אורך הספה 510: חמישה מושבים של 102.</text>'
        f'<text class="t" x="{34 + vf.w + 62}" y="{22 + vs.h + 42}" font-size="3" text-anchor="start">הקו המקווקו: משענת יד בגובה 62.</text>')
body = ('<h2>מפלסים (Z מהרצפה)</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("רצפת הסלון", "0"), ("תחתית המסך הפתוח", "92"), ("תחתית התמונה", "100"), ("עין של צופה יושב", "115"),
            ("תחתית המקרן במצב הקרנה", "315"), ("ראש התמונה", "324"), ("ציר העדשה", "325"), ("ראש קירות הזכוכית", "460"),
            ("תקרה צפה", "500"), ("תחתית תקרת הבטון", "520"), ("פני הגג", "550"), ("ראש המעקה", "590")))
        + '</table><h2>מרחקים לאורך הסלון (Y)</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("גב הספה", "225"), ("עין הצופה", "280"), ("חזית הספה", "335"), ("ציר המקרן", "495"), ("חזית העדשה", "519"),
            ("מישור המסך", "1070"), ("חזית הספרייה", "1095"), ("קיר המדיה", "1135")))
        + '</table><h2>בדיקות</h2><ul>'
        '<li>מרחק מהעדשה למסך: 551. יחס הטלה 1.38 לתמונה ברוחב 398.</li>'
        '<li>מרחק צפייה: 790, כמעט פי 2 מרוחב התמונה. זווית צפייה של כ־28°.</li>'
        '<li>המסך הפתוח רחב ב־15 מכל צד מהספרייה ומכסה את כל המדפים.</li>'
        '<li>המסך יורד 25 לפני חזית הספרייה.</li></ul>')
pages.append(sheet(svg, panel(98, "חתך לאורך", "גבהים, מיקום המקרן והמסך", f"2/{NP}", "1:50 · 1:20", body)))

# ---- 3: media wall elevation 1:50
ve = SH.View(-1.3, -1.6, W + 1.75, 5.85, 50, 14, 62)
svg = SH.render(elevation(), ve, clip_id="p3e")
svg += title(14 + ve.w, 56, "חזית קיר המדיה, מבט מתוך הסלון · 1:50")
body = ('<h2>הספרייה</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("רוחב כולל", "390"), ("עומק", "40"), ("גובה, עד התקרה הצפה", "500"), ("4 תאים, רוחב כל תא", "97.5"),
            ("ארון תחתון, גובה", "92"), ("בסיס שחור מתחת לארון", "6"), ("9 שורות מדפים, מרווח", "45.3"),
            ("עובי מדף", "3.5"), ("עובי מחיצה אנכית", "3.6")))
        + '</table><h2>לוחות השיש</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("לוח שמאלי", "165 × 30 × 500"), ("לוח ימני", "170 × 30 × 500"), ("רווח מהקירות הצדדיים", "55")))
        + '</table><ul style="margin-top:2mm"><li>בכל לוח יש פוגה אנכית באמצע.</li></ul>'
        '<h2>המסך מול הספרייה</h2><ul>'
        '<li>המסך הפתוח: רוחב 420, מגובה 92 עד התקרה. הוא מכסה את כל המדפים.</li>'
        '<li>הארון התחתון, בגובה 92, נשאר גלוי מתחת למסך.</li>'
        '<li>כשהמסך סגור רואים את הספרייה כולה.</li></ul>'
        '<h2>הקיר</h2><ul><li>קיר המדיה אטום, בלי חלונות, כדי שלא ייכנס אור ליד המסך.</li>'
        '<li>רוחב הקיר 835, גובה עד התקרה הצפה 500.</li></ul>')
pages.append(sheet(svg, panel(170, "חזית קיר המדיה", "ספרייה, לוחות שיש ומיקום המסך", f"3/{NP}", "1:50", body)))

# ---- 4: projector unit 1:10 and the lift 1:20
va = SH.View(-0.62, -0.5, 0.62, 0.52, 10, 14, 22)
vb = SH.View(-0.5, -0.17, 0.66, 0.42, 10, 14 + va.w + 14, 40)
vc = SH.View(-1.15, 2.95, 2.75, 5.68, 20, 30, 22 + va.h + 16)
svg = SH.render(proj_plan(), va, clip_id="p4a") + SH.render(proj_side(), vb, clip_id="p4b") + SH.render(lift_states(), vc, clip_id="p4c")
svg += title(14 + va.w, 17, "יחידת המקרן, מבט מלמעלה · 1:10")
svg += title(14 + va.w + 14 + vb.w, 17, "יחידת המקרן, מבט מהצד · 1:10")
svg += title(30 + vc.w, 22 + va.h + 12, "הליפט: סגור ופתוח · 1:20")
body = ('<h2>יחידת המקרן</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("פתח בתקרה הצפה", "70 × 60"), ("לוח סגירה", "67 × 57 × 2.2"), ("גוף המקרן", "50 × 40 × 15.8"),
            ("גובה כולל של היחידה", "18"), ("עדשה, קוטר", "10"), ("ציר העדשה מעל תחתית הלוח", "10"),
            ("העדשה ימינה ממרכז המקרן", "10"), ("העדשה בולטת מחזית הגוף", "4.2"), ("מרחק בין שני התרנים", "36")))
        + '</table><h2>שני מצבים</h2><table><tr><th>חלק</th><th>סגור</th><th>פתוח</th></tr>'
        '<tr><td>תחתית לוח הסגירה</td><td class="n">Z=500</td><td class="n">Z=315</td></tr>'
        '<tr><td>תחתית גוף המקרן</td><td class="n">Z=502.2</td><td class="n">Z=317.2</td></tr>'
        '<tr><td>ציר העדשה</td><td class="n">Z=510</td><td class="n">Z=325</td></tr></table>'
        '<ul style="margin-top:2mm"><li>מהלך הליפט: 185.</li><li>במצב סגור הלוח בקו התקרה והמקרן כולו בתוך חלל התקרה, שגובהו 20.</li>'
        '<li>שני תרנים טלסקופיים מחברים את המקרן לתקרת הבטון.</li></ul>')
pages.append(sheet(svg, panel(120, "המקרן והליפט", "יחידת המקרן ושני מצבי הליפט", f"4/{NP}", "1:10 · 1:20", body)))

# ---- 5: the open screen 1:25
vd = SH.View(-2.75, -1.05, 3.45, 4.55, 25, 22, 34)
svg = SH.render(screen_front(), vd, text_k=0.5, clip_id="p5d")
svg += title(22 + vd.w, 24, "המסך הפתוח, מבט מהספה · 1:25")
body = ('<h2>המסך</h2><table>'
        + "".join(f'<tr><td>{a}</td><td class="n">{b}</td></tr>' for a, b in (
            ("רוחב הבד", "420"), ("ירידה כוללת מהתקרה", "408"), ("שטח התמונה, 16:9", "398 × 224"), ("אלכסון התמונה", "457 (180״)"),
            ("פס שחור עליון", "176"), ("שוליים שחורים בצדדים", "11"), ("שוליים שחורים למטה", "5"), ("מוט משקולת", "422 × 2.8 × 3"),
            ("חריץ בתקרה", "450 × 8"), ("בית הגליל בחלל התקרה", "450 × 18 × 14")))
        + '</table><h2>שני מצבים</h2><table><tr><th>חלק</th><th>סגור</th><th>פתוח</th></tr>'
        '<tr><td>מוט המשקולת</td><td class="n">Z=500</td><td class="n">Z=92</td></tr>'
        '<tr><td>בד המסך</td><td>מגולגל בתקרה</td><td class="n">Z=95 → 500</td></tr></table>'
        '<h2>סדר בנייה מוצע בסקצ׳אפ</h2><ul>'
        '<li>יחידות בסנטימטרים: Window, Model Info, Units.</li>'
        '<li>רצפה 835 × 1135, ומעליה הקירות לגובה 520.</li>'
        '<li>קירות הזכוכית והפתח למבואה, לפי דף 1.</li>'
        '<li>תקרת בטון בגובה 520, ותקרה צפה בגובה 500 עם הפתח למקרן והחריץ למסך.</li>'
        '<li>קיר המדיה: שני לוחות שיש וביניהם הספרייה.</li>'
        '<li>המקרן והמסך: כל אחד כ־Component נפרד, כדי להזיז אותו בין סגור לפתוח.</li>'
        '<li>ריהוט: ספה, שזלונג, שולחנות, כורסאות ושטיח.</li>'
        '<li>לכל מצב שומרים Scene נפרד, עם Tags לחלקים שזזים.</li></ul>'
        '<h2>חומרים</h2><ul><li>קירות ותקרה: טיח לבן. רצפה: פרקט אלון.</li><li>ספרייה וארון: עץ אגוז. לוחות צד: שיש כהה.</li>'
        '<li>מקרן ומסגרות: שחור מט. מוט המסך: אלומיניום.</li><li>ספה: בד בהיר. כורסאות: עור חום.</li></ul>')
pages.append(sheet(svg, panel(122, "המסך", "מידות המסך הפתוח, סדר בנייה וחומרים", f"5/{NP}", "1:25", body)))

doc = f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>הסלון והרהיט · דף מידות</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT)
