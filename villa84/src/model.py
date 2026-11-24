"""Villa 84: the single source for levels, floor outlines, rooms, openings and site elements.

Design coordinates in metres. X runs along the plot edge 186G -> 219G (the street is at -X, south-west),
Y runs across it (+Y is roughly north-west). The south facade of the house is Y = 22.05 and faces the terrace.
Walls: exterior 0.30, interior 0.15. Rooms are rectangles (or unions of rectangles) inside the wall lines;
wall poche = floor outline - rooms - openings.
"""
import json
import os

from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = json.load(open(os.path.join(HERE, "site.json"), encoding="utf-8"))

ABS0 = 91.00                      # +-0.00 of the house = +91.00 above sea level
LEVELS = {
    "B": dict(z=-3.50, clear=3.00, top=0.0, name="קומת מרתף", sub="משרד אדריכלים, חניון וחלק משפחתי"),
    "G": dict(z=0.0, clear=3.00, top=3.50, name="קומת קרקע", sub="החלק הציבורי של הווילה"),
    "F": dict(z=3.50, clear=2.90, top=6.80, name="קומה א׳", sub="החלק הפרטי של הווילה"),
}
LIVING_CLEAR, LIVING_TOP = 5.00, 5.50
PAV_CLEAR, PAV_TOP = 2.90, 3.30

OUTLINES = {
    "B": [(5.5, 12.2, 27.5, 34.0)],
    "G": [(5.5, 22.05, 36.0, 34.0), (45.5, 20.5, 51.0, 34.0)],
    "F": [(5.5, 22.05, 27.5, 34.0)],
}
EXT_T, INT_T = 0.30, 0.15
WF, NF, SF, EF = (5.5, 5.8), (33.7, 34.0), (22.05, 22.35), (27.2, 27.5)      # facade wall bands of the bar

# ------------------------------------------------------------------ core (the same on every floor)
# U stair in two flights of 1.30 m, 20 risers of 17.5 cm per storey, treads of 29 cm, half landing at the south end.
# Both flights start and end at the north end, where the floor landing is (Y 26.41-27.71).
STAIR_RECT = (17.3, 22.35, 20.05, 26.26)
STAIR = dict(x0=17.3, x1=20.05, width=1.30, y0=26.26, dir=-1, n=9, tread=0.29, rise=0.175, risers=20,
             landing=(17.3, 22.35, 20.05, 23.65), up="west")
ELEV_RECT = (20.2, 22.35, 22.2, 24.35)             # shaft 2.00 x 2.00 clear; door south in B, north on G and F
CORE_BAND = (17.3, 26.41, 22.35, 27.71)            # floor landing north of the stair
TOWER = (17.3, 29.31, 19.75, 33.7)                 # reinforced tower: office shelter (B), pantry (G), mamad (F)

# ------------------------------------------------------------------ rooms
ROOMS = []


def room(floor, rid, name, rects, cat="עיקרי", group="", label=None, note="", count=True):
    if isinstance(rects, tuple):
        rects = [rects]
    ROOMS.append(dict(floor=floor, id=rid, name=name, rects=[tuple(r) for r in rects], cat=cat, group=group,
                      label=label, note=note, count=count))


# ---- B, -3.50: architects' office, parking and the family part
g_park, g_fam, g_off, g_core = "חניון", "חלק משפחתי", "משרד אדריכלים", "תנועה אנכית"
room("B", "B01", "חניון", (5.8, 12.5, 17.0, 18.9), "שירות", g_park, label=(11.4, 18.3),
     note="4 מקומות חניה 2.80×5.20, בלי מעבר נסיעה. מאחורי הרכבים מעבר הליכה 1.20")
room("B", "B02", "מחסן", (17.15, 12.5, 20.3, 17.55), "שירות", g_fam)
room("B", "B03", "חדר מערכות", (22.35, 17.7, 27.2, 20.75), "שירות", g_fam, note="משאבות, דוד, לוח חשמל ראשי")
room("B", "B04", "חדר קולנוע", (20.45, 12.5, 27.2, 17.55), "עיקרי", g_fam, label=(25.2, 16.75), note="8 מושבים בשתי שורות, בלי חלונות")
room("B", "B05", "לובי משפחתי", (17.15, 17.7, 22.2, 22.2), "שירות", g_fam, note="יוצאים מהרכב ונכנסים ישר ללובי, המעלית נפתחת אליו")
room("B", "B15", "מעבר למדרגות", [(22.35, 20.9, 23.65, 27.71), CORE_BAND], "שירות", g_fam, label=(23.0, 24.6))
room("B", "B16", "ארון", (20.2, 24.5, 22.2, 26.26), "שירות", g_fam)
room("B", "B06", "מדרגות", STAIR_RECT, "שירות", g_core, note="2 מהלכים ברוחב 1.30")
room("B", "B07", "מעלית", ELEV_RECT, "שירות", g_core, note="פיר 2.00×2.00, דלת לכל צד")
room("B", "B08", "חדר ישיבות", (5.8, 19.05, 11.0, 23.6), "עיקרי", g_off, label=(8.4, 22.95), note="חלון לחצר המשרד וקיר זכוכית אל מעבר החניון")
room("B", "B09", "חדר אדריכל ראשי", (11.15, 19.05, 17.0, 23.6), "עיקרי", g_off, label=(13.4, 19.95), note="קיר זכוכית אל מעבר החניון")
room("B", "B13", "קבלה והמתנה", (5.8, 23.75, 11.0, 27.6), "עיקרי", g_off, label=(8.6, 25.55), note="כניסת לקוחות מחצר המשרד")
room("B", "B10", "סטודיו פתוח", [(5.8, 27.75, 17.15, 33.7), (11.15, 23.75, 17.15, 27.75)], "עיקרי", g_off,
     label=(10.6, 30.0), note="10 עמדות עבודה, אור מהחצר המערבית ומהחצר האנגלית")
room("B", "B17", "מסדרון משרד", (17.3, 27.86, 27.2, 29.16), "שירות", g_off)
room("B", "B14", "מרחב מוגן", TOWER, "שירות", g_off, note="ביום־יום ארכיון")
room("B", "B11", "סדנת מודלים וחומרים", (19.9, 29.31, 27.2, 33.7), "עיקרי", g_off, label=(23.4, 32.75), note="אור מהחצר האנגלית")
room("B", "B12", "שירותים ומטבחון", (23.8, 20.9, 27.2, 27.71), "שירות", g_off, label=(25.15, 26.45), note="תא נגיש, תא רגיל ומטבחון")

# ---- G, +-0.00: public part. Stage 2 will lay out these zones in detail.
g_pub, g_svc, g_spa = "מגורים ואירוח", "שירות", "ביתן ספא"
room("G", "G09", "מבואת כניסה", [(22.35, 22.35, 27.2, 27.71), (20.2, 24.5, 22.35, 27.71), (17.3, 26.41, 20.2, 27.71)], "שירות", g_pub,
     label=(24.8, 25.6), note="דלת הכניסה מול מדרגות הכניסה מהרחבה")
room("G", "G10", "מדרגות", STAIR_RECT, "שירות", g_core)
room("G", "G11", "מעלית", ELEV_RECT, "שירות", g_core)
room("G", "G01", "מטבח ופינת אוכל", (5.8, 22.35, 17.15, 27.71), "עיקרי", g_pub, note="פונים אל מרפסת הגג")
room("G", "G07", "מעבר שירות", (12.15, 27.86, 27.2, 29.16), "שירות", g_svc)
room("G", "G03", "חדר משפחה וגיימינג", (5.8, 27.86, 12.0, 33.7), "עיקרי", g_pub)
room("G", "G04", "מטבח אחורי", (12.15, 29.31, 17.15, 33.7), "שירות", g_svc)
room("G", "G06", "מזווה גדול", TOWER, "שירות", g_svc, note="קירות מחוזקים, מעל המרחב המוגן")
room("G", "G05", "חדר שירות וכלב", (19.9, 29.31, 23.5, 33.7), "שירות", g_svc, note="יציאה לחצר הצפונית")
room("G", "G08", "שירותי אורחים", (23.65, 29.31, 27.2, 33.7), "שירות", g_svc)
room("G", "G12", "סלון", (27.35, 22.35, 35.7, 33.7), "עיקרי", g_pub, label=(31.5, 31.2), note="גובה כפול 5.00 מ׳, מקרן ומסך נסתרים")
room("G", "P01", "חדר מכונות בריכה", (45.8, 20.8, 50.7, 22.5), "שירות", g_spa)
room("G", "P02", "חדר כושר", (45.8, 22.65, 50.7, 28.4), "עיקרי", g_spa)
room("G", "P03", "סאונה", (45.8, 28.55, 48.1, 31.0), "עיקרי", g_spa)
room("G", "P04", "מקלחת ושירותים", (48.25, 28.55, 50.7, 31.0), "עיקרי", g_spa)
room("G", "P05", "ג׳קוזי", (45.8, 31.15, 50.7, 33.7), "עיקרי", g_spa)

# ---- F, +3.50: private part. Stage 3 will lay out these zones in detail.
g_par, g_kid, g_com = "סוויטת הורים", "חדרי ילדים", "משותף"
room("F", "F01", "חדר שינה הורים", (5.8, 22.35, 11.4, 27.71), "עיקרי", g_par)
room("F", "F03", "חדר ארונות ומקלחת הורים", (5.8, 27.86, 11.4, 33.7), "עיקרי", g_par)
room("F", "F05", "חדר נוער 1", (11.55, 22.35, 17.15, 27.71), "עיקרי", g_kid)
room("F", "F14", "חדר הילד הצעיר", (22.35, 22.35, 27.2, 27.71), "עיקרי", g_kid)
room("F", "F11", "מסדרון ומבואת קומה", [(11.55, 27.86, 27.2, 29.16), (17.3, 26.41, 22.35, 27.86), (20.2, 24.5, 22.35, 26.41)], "שירות", g_com)
room("F", "F08", "חדר נוער 2", (11.55, 29.31, 17.15, 33.7), "עיקרי", g_kid)
room("F", "F13", "ממ״ד", TOWER, "שירות", g_com, note="ביום־יום חדר לימוד")
room("F", "F12", "כביסה, מקלחות ילדים", (19.9, 29.31, 27.2, 33.7), "עיקרי", g_kid)
room("F", "F16", "מדרגות", STAIR_RECT, "שירות", g_core)
room("F", "F17", "מעלית", ELEV_RECT, "שירות", g_core)

# ------------------------------------------------------------------ openings
OPENINGS = []


def H(floor, x0, x1, ya, yb, kind, **kw):
    """Opening in a wall that runs along X (between Y ya and yb)."""
    OPENINGS.append(dict(floor=floor, axis="H", rect=(x0, ya, x1, yb), kind=kind, **kw))


def Vv(floor, y0, y1, xa, xb, kind, **kw):
    """Opening in a wall that runs along Y (between X xa and xb)."""
    OPENINGS.append(dict(floor=floor, axis="V", rect=(xa, y0, xb, y1), kind=kind, **kw))


BS = (12.2, 12.5)                   # basement south wall band
# ---- B
H("B", 6.1, 11.1, *BS, "garage")
H("B", 11.7, 16.7, *BS, "garage")
Vv("B", 17.75, 18.75, 17.0, 17.15, "door", hinge="a", swing=1)                    # parking -> family lobby
H("B", 6.0, 10.8, 18.9, 19.05, "fixed", sill=0.9, head=2.7)                       # glass to the parking walkway
H("B", 11.35, 16.8, 18.9, 19.05, "fixed", sill=0.9, head=2.7)
H("B", 18.9, 19.8, 17.55, 17.7, "door", hinge="b", swing=-1)                     # lobby -> storage
H("B", 20.8, 21.9, 17.55, 17.7, "door2", swing=-1)                                # lobby -> cinema
Vv("B", 17.95, 18.85, 22.2, 22.35, "door", hinge="a", swing=1)                    # lobby -> systems
Vv("B", 20.9, 22.2, 22.2, 22.35, "open")                                          # lobby -> passage to the stair
H("B", 20.7, 21.7, 22.2, 22.35, "elev")                                           # lift door (south)
H("B", 20.75, 21.65, 26.26, 26.41, "door", hinge="b", swing=1)                   # closet
# office
Vv("B", 24.3, 25.3, *WF, "door", hinge="a", swing=1)                              # client entrance from the office court
Vv("B", 25.6, 27.3, *WF, "fixed", head=2.7)
Vv("B", 19.5, 23.2, *WF, "fixed", sill=0.6, head=2.7)                             # meeting room window to the court
Vv("B", 28.2, 33.3, *WF, "fixed", head=2.7)                                       # studio, west
H("B", 6.3, 10.9, *NF, "win", sill=0.9, head=2.7)                                 # studio, north (English court)
H("B", 11.6, 16.6, *NF, "win", sill=0.9, head=2.7)
H("B", 17.95, 19.05, *NF, "win", sill=1.2, head=2.2, blast=True)                  # shelter
H("B", 20.4, 23.3, *NF, "win", sill=0.9, head=2.7)                                # workshop
H("B", 9.2, 10.2, 23.6, 23.75, "door", hinge="b", swing=-1)                      # reception -> meeting
Vv("B", 24.1, 27.3, 11.0, 11.15, "open")                                          # reception -> studio
H("B", 15.65, 16.6, 23.6, 23.75, "door", hinge="b", swing=-1)                    # studio -> principal
H("B", 11.5, 15.3, 23.6, 23.75, "fixed", sill=0.9, head=2.7)
Vv("B", 27.86, 29.16, 17.15, 17.3, "open")                                        # studio -> office corridor
H("B", 18.05, 18.95, 29.16, 29.31, "door", hinge="a", swing=1, blast=True)        # shelter
H("B", 21.3, 22.9, 29.16, 29.31, "door2", swing=1)                                # workshop
H("B", 24.2, 25.1, 27.71, 27.86, "door", hinge="a", swing=-1)                    # WC and kitchenette

# ---- core openings on every floor
for fl in "BGF":
    H(fl, 17.3, 20.05, 26.26, 26.41, "open")                                      # stair <-> floor landing
for fl in "GF":
    H(fl, 20.7, 21.7, 24.35, 24.5, "elev")                                        # lift door (north)

# ---- G (zones; stage 2)
H("G", 22.6, 24.0, *SF, "door", hinge="a", swing=1, head=2.6)                     # front door, in line with the entrance stair
H("G", 24.4, 26.8, *SF, "fixed", head=2.6)
H("G", 6.1, 16.9, *SF, "slide", head=2.7)                                         # kitchen and dining to the terrace
Vv("G", 23.6, 27.3, *WF, "win", sill=0.9, head=2.7)
H("G", 6.3, 11.6, *NF, "win", sill=0.9, head=2.7)
H("G", 13.0, 16.4, *NF, "win", sill=1.2, head=2.4)
H("G", 20.4, 21.4, *NF, "door", hinge="a", swing=-1)                               # service exit
H("G", 24.6, 25.4, *NF, "win", sill=1.6, head=2.2)
Vv("G", 22.9, 27.5, 27.2, 27.35, "open", head=3.0)                                # hall -> living room
H("G", 17.3, 22.35, 27.71, 27.86, "open")                                         # hall -> service passage
H("G", 12.5, 16.8, 27.71, 27.86, "open")                                          # kitchen -> service passage
Vv("G", 28.0, 29.0, 12.0, 12.15, "door", hinge="a", swing=1)                      # family room
H("G", 14.0, 14.9, 29.16, 29.31, "door", hinge="a", swing=1)                      # back kitchen
H("G", 18.0, 18.9, 29.16, 29.31, "door", hinge="a", swing=1)                      # pantry
H("G", 21.0, 21.9, 29.16, 29.31, "door", hinge="a", swing=1)                      # service room
H("G", 24.9, 25.8, 29.16, 29.31, "door", hinge="a", swing=1)                      # guest WC
# living room and pavilion (unchanged)
H("G", 27.9, 35.1, *SF, "slide", head=4.6)
Vv("G", 22.9, 33.1, 35.7, 36.0, "slide", head=4.6)
Vv("G", 23.2, 27.8, 45.5, 45.8, "slide")
Vv("G", 31.5, 33.3, 45.5, 45.8, "slide")
Vv("G", 21.2, 22.1, 45.5, 45.8, "door", hinge="a", swing=-1)
H("G", 46.5, 47.3, 31.0, 31.15, "door")
H("G", 49.0, 49.8, 28.4, 28.55, "door")
H("G", 49.0, 49.8, 31.0, 31.15, "door")
Vv("G", 23.6, 27.4, 50.7, 51.0, "win", sill=1.5, head=2.5)
H("G", 46.6, 49.9, *NF, "win", sill=1.2, head=2.5)

# ---- F (zones; stage 3)
H("F", 6.1, 11.1, *SF, "slide", head=2.6)
H("F", 12.0, 16.7, *SF, "slide", head=2.6)
H("F", 22.8, 26.8, *SF, "slide", head=2.6)
Vv("F", 23.0, 27.0, *WF, "win", sill=0.9, head=2.6)
Vv("F", 28.5, 33.0, *WF, "win", sill=1.2, head=2.4)
H("F", 12.2, 16.5, *NF, "win", sill=0.9, head=2.6)
H("F", 17.95, 19.05, *NF, "win", sill=1.2, head=2.2, blast=True)
H("F", 20.5, 26.6, *NF, "win", sill=1.2, head=2.4)
Vv("F", 28.0, 29.0, 11.4, 11.55, "door", hinge="a", swing=-1)                     # parents' wing
H("F", 12.2, 13.1, 27.71, 27.86, "door", hinge="a", swing=-1)                     # teen 1
H("F", 23.0, 23.9, 27.71, 27.86, "door", hinge="a", swing=-1)                     # young child
H("F", 12.2, 13.1, 29.16, 29.31, "door", hinge="a", swing=1)                      # teen 2
H("F", 18.05, 18.95, 29.16, 29.31, "door", hinge="a", swing=1, blast=True)        # mamad
H("F", 21.0, 21.9, 29.16, 29.31, "door", hinge="a", swing=1)                      # laundry and showers
H("F", 7.8, 8.7, 27.71, 27.86, "door", hinge="a", swing=1)                        # bedroom -> closet and bath

# ------------------------------------------------------------------ site elements
POOL = (39.5, 21.5, 43.5, 33.5)
POOL_DECK = (36.0, 20.5, 45.5, 34.0)
TERRACE = (5.5, 12.2, 27.5, 22.05)
TERRACE_GATE = (22.6, 24.0)
BALCONIES = [(5.8, 20.25, 16.2, 22.05), (22.15, 20.25, 27.2, 22.05)]
EXT_STAIR = dict(x0=16.9, x1=22.6, y0=10.7, y1=12.2, n=19, tread=0.30, risers=20, z0=-3.50, z1=0.0)
EXT_LANDING = (22.6, 10.7, 24.0, 12.2)
ENGLISH_COURT = (5.5, 34.0, 23.6, 36.2)
NORTH_PATH = (27.5, 34.0, 45.5, 35.0)
OFFICE_COURT = [(0.9, 19.0), (5.5, 19.0), (5.5, 34.0), (0.75, 34.0)]


def _plot_edge_y(y, i, j):
    (xa, ya), (xb, yb) = SITE["plot"][i], SITE["plot"][j]
    return xa + (xb - xa) * (y - ya) / (yb - ya)


def front_x(y):
    """X of the street-front boundary (points 186G-187G-188G-189G) at a given Y."""
    pts = SITE["plot"][:4]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        lo, hi = min(ya, yb), max(ya, yb)
        if lo - 1e-9 <= y <= hi + 1e-9:
            return xa + (xb - xa) * (y - ya) / (yb - ya)
    return pts[0][0] if y > pts[0][1] else pts[-1][0]


def south_boundary_y(x):
    """Y of the south-east boundary (189G -> 220G) at a given X."""
    (xa, ya), (xb, yb) = SITE["plot"][3], SITE["plot"][4]
    return ya + (yb - ya) * (x - xa) / (xb - xa)


DRIVEWAY = [(0.95, 2.1), (0.72, 8.3), (6.6, 9.4), (6.6, 12.2), (16.7, 12.2), (16.7, 10.5), (20.5, 10.5),
            (20.5, south_boundary_y(20.5) + 1.0), (12.0, south_boundary_y(12.0) + 1.0), (5.0, south_boundary_y(5.0) + 1.0)]
GATES = {"vehicle": ((0.93, 2.6), (0.74, 7.4)), "pedestrian": ((0.52, 26.9), (0.5, 28.6))}
TREES = [(30.0, 16.2, 1.6), (34.5, 17.4, 1.5), (3.2, 14.0, 1.4), (3.0, 16.9, 1.1), (47.5, 16.9, 1.3), (53.0, 23.5, 1.2),
         (38.0, 18.2, 1.3)]
CYPRESS = [(20.5 + 2.5 * i, 35.6) for i in range(int((53.0 - 20.5) / 2.5) + 1)] + [(54.6, y) for y in (25.0, 27.5, 30.0, 32.5)]


def _niche(y0, width, depth, back=0.0):
    x0 = max(front_x(y0), front_x(y0 + width)) + back + 0.005
    return (round(x0, 3), y0, round(x0 + depth, 3), round(y0 + width, 3))


PILLARS = [
    dict(id="elec", name="פילר חשמל", short="חשמל", rect=_niche(28.95, 1.02, 0.50), h=1.65, inner=(0.82, 0.40, 1.55), face="W",
         use="ארון מונים של חברת החשמל, 2 מונים: וילה ומשרד", std="גומחה ל־2–3 מונים לפי חברת החשמל: 82×40 ס״מ, גובה כולל 215, מתוכו 155 מעל הקרקע"),
    dict(id="comm", name="פילר תקשורת", short="תקשורת", rect=_niche(30.12, 0.80, 0.50), h=1.65, inner=(0.60, 0.40, 1.55), face="W",
         use="בזק, הוט וסיב אופטי", std="גומחה טרומית 60×40 ס״מ, באותו גובה של גומחת החשמל"),
    dict(id="water", name="פילר מים", short="מים", rect=_niche(31.07, 1.20, 0.40), h=1.65, inner=(1.00, 0.30, 1.55), face="W",
         use="2 מדי מים: וילה ומשרד, עם ברז ראשי", std="גומחה למוני מים 100×30 ס״מ לפי קטלוג גומחות טרומיות"),
    dict(id="gas", name="גומחת גז", short="גז", rect=_niche(12.00, 1.45, 0.75, back=0.10), h=1.80, inner=(1.25, 0.65, 1.70), face="E",
         use="2 בלוני גז של 48 ק״ג (קוטר 37.5 ס״מ, גובה כ־129 ס״מ), דלת מאווררת", std="גומחה לגז 125×65 ס״מ לפי קטלוג גומחות טרומיות. התקנה לפי ת״י 158"),
    dict(id="bins", name="מסתור פחים", short="פחים", rect=(0.60, 8.85, 3.20, 10.05), h=1.40, inner=(2.40, 1.00, 1.30), face="S",
         use="3 פחים של 360 ליטר (58×88×108 ס״מ כל אחד)", std="80 ס״מ רוחב לכל פח. הדלתות נפתחות אל רחבת הכניסה ולא אל הרחוב"),
]

# ------------------------------------------------------------------ geometry helpers



def rect_area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def room_poly(r):
    return unary_union([sbox(*q) for q in r["rects"]])


def room_area(r):
    return room_poly(r).area


def rooms_of(fl):
    return [r for r in ROOMS if r["floor"] == fl]


def openings_of(fl):
    return [o for o in OPENINGS if o["floor"] == fl and o["kind"] != "none"]


def floor_outline(fl):
    return unary_union([sbox(*r) for r in OUTLINES[fl]])


def gross_area(fl):
    return floor_outline(fl).area


def polys(g):
    if g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def wall_solid(fl):
    """Wall poche before openings are cut."""
    return floor_outline(fl).difference(unary_union([room_poly(r) for r in rooms_of(fl)]))


def wall_poly(fl):
    return wall_solid(fl).difference(unary_union([sbox(*o["rect"]) for o in openings_of(fl)] or [sbox(0, 0, 0, 0)]))


def rect_cells(g, step=None):
    """Split a rectilinear polygon (or multipolygon) into rectangles: row runs between the distinct Y edges,
    merged vertically where a run repeats on the next row."""
    out = []
    for p in polys(g):
        ys = sorted({round(v, 4) for v in [c[1] for c in p.exterior.coords] + [c[1] for h in p.interiors for c in h.coords]})
        xs = sorted({round(v, 4) for v in [c[0] for c in p.exterior.coords] + [c[0] for h in p.interiors for c in h.coords]})
        open_runs = {}
        for ya, yb in zip(ys, ys[1:]):
            ym = (ya + yb) / 2
            runs = []
            cur = None
            for xa, xb in zip(xs, xs[1:]):
                inside = p.contains(sbox(xa, ym - 1e-6, xb, ym + 1e-6).centroid) and sbox(xa + 1e-6, ya + 1e-6, xb - 1e-6, yb - 1e-6).within(p.buffer(1e-7))
                if inside:
                    cur = [xa, xb] if cur is None else [cur[0], xb]
                else:
                    if cur:
                        runs.append(tuple(cur))
                    cur = None
            if cur:
                runs.append(tuple(cur))
            nxt = {}
            for run in runs:
                if run in open_runs:
                    nxt[run] = open_runs.pop(run)
                else:
                    nxt[run] = ya
            for run, y0 in open_runs.items():
                out.append((run[0], y0, run[1], ya))
            open_runs = {run: nxt[run] for run in runs}
            for run in runs:
                open_runs[run] = nxt[run]
        for run, y0 in open_runs.items():
            out.append((run[0], y0, run[1], ys[-1]))
    return out


def terrain_z(x, y):
    """Natural ground level (absolute) from the survey grid, bilinear."""
    g = SITE["grid"]
    fx = (x - g["x0"]) / g["step"]
    fy = (y - g["y0"]) / g["step"]
    ix = max(0, min(g["nx"] - 2, int(fx)))
    iy = max(0, min(g["ny"] - 2, int(fy)))
    tx, ty = min(max(fx - ix, 0.0), 1.0), min(max(fy - iy, 0.0), 1.0)
    z = g["z"]
    return (z[iy][ix] * (1 - tx) * (1 - ty) + z[iy][ix + 1] * tx * (1 - ty) + z[iy + 1][ix] * (1 - tx) * ty + z[iy + 1][ix + 1] * tx * ty)


# ------------------------------------------------------------------ checks
CIRC_IDS = {"B15", "B17", "G07", "G09", "F11"}


def dead_pockets(fl, thick=0.36):
    """Pieces of the wall poche thicker than a wall: leftover space nobody can use."""
    w = wall_solid(fl)
    fat = w.buffer(-thick / 2, join_style=2).buffer(thick / 2, join_style=2)
    return [p for p in polys(fat) if p.area > 0.05]


def circulation_share(fl):
    net = sum(room_area(r) for r in rooms_of(fl) if r["id"][0] != "P")
    circ = sum(room_area(r) for r in rooms_of(fl) if r["id"] in CIRC_IDS)
    return circ / net if net else 0.0


def validate():
    problems = []
    for fl in "BGF":
        out = floor_outline(fl)
        rs = rooms_of(fl)
        for r in rs:
            p = room_poly(r)
            if p.difference(out).area > 1e-6:
                problems.append(f"{r['id']}: outside the floor outline")
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                ov = room_poly(a).intersection(room_poly(b)).area
                if ov > 1e-6:
                    problems.append(f"{a['id']} overlaps {b['id']} ({ov:.2f} m2)")
        solid = wall_solid(fl)
        for o in openings_of(fl):
            g = sbox(*o["rect"])
            if g.difference(solid.buffer(1e-6)).area > 1e-6:
                problems.append(f"{fl} opening {o['kind']} {o['rect']}: not fully inside a wall")
        for p in dead_pockets(fl):
            problems.append(f"{fl}: dead pocket {p.area:.2f} m2 at {[round(v, 2) for v in p.bounds]}")
    bl = Polygon(SITE["building_line"])
    for fl in "BGF":
        if floor_outline(fl).difference(bl.buffer(1e-6)).area > 1e-6:
            problems.append(f"{fl}: outside the building line")
    e = EXT_STAIR
    for name, r in (("entrance stair", (e["x0"], e["y0"], e["x1"], e["y1"])), ("stair landing", EXT_LANDING), ("pool", POOL), ("terrace", TERRACE)):
        if sbox(*r).difference(bl.buffer(1e-6)).area > 1e-6:
            problems.append(f"{name}: outside the building line")
    plotp = Polygon(SITE["plot"])
    for pl in PILLARS:
        if sbox(*pl["rect"]).difference(plotp.buffer(0.005)).area > 1e-4:
            problems.append(f"pillar {pl['id']}: outside the plot")
        for o2 in PILLARS:
            if o2 is not pl and sbox(*pl["rect"]).intersects(sbox(*o2["rect"])):
                problems.append(f"pillar {pl['id']} touches {o2['id']}")
        if sbox(*pl["rect"]).intersects(Polygon(DRIVEWAY)):
            problems.append(f"pillar {pl['id']}: on the driveway")
    # the reinforced tower and the core must stack
    for fl in "BGF":
        for rect in (TOWER, STAIR_RECT, ELEV_RECT):
            if not any(abs(room_area(r) - rect_area(rect)) < 1e-6 and room_poly(r).equals(sbox(*rect)) for r in rooms_of(fl)):
                problems.append(f"{fl}: core/tower rect {rect} is not a room on this floor")
    if sum(gross_area(f) for f in "BGF") > 1200:
        problems.append("gross area above 1,200 m2")
    return problems


if __name__ == "__main__":
    for fl in "BGF":
        net = sum(room_area(r) for r in rooms_of(fl))
        print(fl, f"net {net:.1f}  gross {gross_area(fl):.1f}  circulation {circulation_share(fl) * 100:.0f}%")
    print("total gross", round(sum(gross_area(f) for f in "BGF"), 1))
    print("\n".join(validate()) or "valid")
