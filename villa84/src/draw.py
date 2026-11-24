"""Plan drawings of villa 84 as Canvas primitives (floor plans and site plan).

The same canvases feed the A1 sheets (sheets.py), the DXF export and, through furniture_solids(), the 3D model.
Everything is read from model.py.
"""
import math

from shapely.geometry import LineString, Polygon, box as sbox
from shapely.ops import unary_union

import model as M
import symbols as S
from symbols import Canvas, place

ORDER = ["SURVEY", "SURV-LOT", "TOPO", "TOPO-M", "TOPO-T", "SPOT", "GREEN", "PAVE", "OUT", "WATER", "ROOF", "BELOW", "TREE",
         "PLOT", "BLINE", "SETBACK", "RUG", "PARK", "CAR", "FURN", "PLANT", "FIX", "STAIR", "DOOR-T", "DOOR", "GLASS", "WALL",
         "CEIL", "CUT", "LEVEL", "DIM", "UTIL", "UTIL-T", "TEXT-S", "TEXT"]

TXT_NAME, TXT_AREA, TXT_DIM = 0.30, 0.21, 0.17


def _sgn(z):
    return "±" if abs(z) < 1e-9 else ("+" if z > 0 else "−")


def lvl(z):
    return f"{_sgn(z)}{abs(z):.2f}"


# ------------------------------------------------------------------ walls and openings
def walls(c, fl):
    for p in M.polys(M.wall_poly(fl)):
        c.poly(list(p.exterior.coords)[:-1], "WALL", fill="wall", holes=[list(h.coords)[:-1] for h in p.interiors])


def _frame(o):
    """Opening geometry in a local frame: start/end along the wall, the two faces across it."""
    x0, y0, x1, y1 = o["rect"]
    if o["axis"] == "H":
        return dict(a=x0, b=x1, f0=y0, f1=y1, pt=lambda s, t: (s, t))
    return dict(a=y0, b=y1, f0=x0, f1=x1, pt=lambda s, t: (t, s))


def _leaf(c, f, hinge_s, tip_s, face, out):
    """Door leaf standing open at 90 degrees from the hinge, and its swing arc back to the closed position."""
    pt = f["pt"]
    w = abs(tip_s - hinge_s)
    tip = face + out * w
    c.line(pt(hinge_s, face), pt(hinge_s, tip), "DOOR", w=0.3)
    # arc: centre at the hinge, from the open leaf to the far jamb
    cx, cy = pt(hinge_s, face)
    ex, ey = pt(tip_s, face)
    ox, oy = pt(hinge_s, tip)
    a0 = math.degrees(math.atan2(ey - cy, ex - cx))
    a1 = math.degrees(math.atan2(oy - cy, ox - cx))
    d = (a1 - a0) % 360
    if d > 180:
        a0, a1 = a1, a0
    c.arc((cx, cy), w, a0, a0 + ((a1 - a0) % 360), "DOOR-T")


def opening_symbol(c, o):
    f = _frame(o)
    pt = f["pt"]
    a, b, f0, f1 = f["a"], f["b"], f["f0"], f["f1"]
    k = o["kind"]
    fm = (f0 + f1) / 2
    if k in ("door", "door2"):
        sw = o.get("swing", 1)
        face = f1 if sw > 0 else f0
        c.line(pt(a, f0), pt(a, f1), "DOOR-T")
        c.line(pt(b, f0), pt(b, f1), "DOOR-T")
        if k == "door":
            if o.get("hinge", "a") == "a":
                _leaf(c, f, a, b, face, sw)
            else:
                _leaf(c, f, b, a, face, sw)
        else:
            m = (a + b) / 2
            _leaf(c, f, a, m, face, sw)
            _leaf(c, f, b, m, face, sw)
        if o.get("blast"):
            c.poly([pt(a, f0), pt(b, f0), pt(b, f1), pt(a, f1)], "DOOR", w=0.45)
    elif k in ("win", "fixed"):
        for t in (f0, f1):
            c.line(pt(a, t), pt(b, t), "WALL", w=0.18)
        c.line(pt(a, fm), pt(b, fm), "GLASS", w=0.3)
        if k == "win":
            c.line(pt(a, fm - 0.035), pt(b, fm - 0.035), "GLASS", w=0.15)
        if o.get("blast"):
            c.poly([pt(a, f0), pt(b, f0), pt(b, f1), pt(a, f1)], "DOOR", w=0.45)
    elif k == "slide":
        for t in (f0, f1):
            c.line(pt(a, t), pt(b, t), "WALL", w=0.12)
        m = (a + b) / 2
        c.poly([pt(a, fm - 0.06), pt(m + 0.05, fm - 0.06), pt(m + 0.05, fm - 0.01), pt(a, fm - 0.01)], "GLASS", w=0.2)
        c.poly([pt(m - 0.05, fm + 0.01), pt(b, fm + 0.01), pt(b, fm + 0.06), pt(m - 0.05, fm + 0.06)], "GLASS", w=0.2)
    elif k == "garage":
        c.line(pt(a, f0), pt(b, f0), "DOOR", w=0.2)
        c.line(pt(a, f1 + 0.08), pt(b, f1 + 0.08), "DOOR-T", dash="4 2")
        c.line(pt(a, f1 + 2.4), pt(b, f1 + 2.4), "DOOR-T", dash="4 2")
        for s in (a, b):
            c.line(pt(s, f1 + 0.08), pt(s, f1 + 2.4), "DOOR-T", dash="4 2")
    elif k == "elev":
        for t in (f0, f1):
            c.line(pt(a, t), pt(b, t), "DOOR-T")
        c.poly([pt(a + 0.05, fm - 0.03), pt(b - 0.05, fm - 0.03), pt(b - 0.05, fm + 0.03), pt(a + 0.05, fm + 0.03)], "DOOR", w=0.2)
    elif k == "open":
        if (o["rect"][1], o["rect"][3]) == (M.STAIR_RECT[3], M.STAIR_RECT[3] + 0.15):
            return
        for t in (f0, f1):
            c.line(pt(a, t), pt(b, t), "DOOR-T", dash="3 2")


def openings(c, fl):
    for o in M.openings_of(fl):
        opening_symbol(c, o)


# ------------------------------------------------------------------ stair and lift
def stair(c, fl):
    s = M.STAIR
    x0, x1, w = s["x0"], s["x1"], s["width"]
    ys, n, tr = s["y0"], s["n"], s["tread"]
    lx0, ly0, lx1, ly1 = s["landing"]
    xw, xe = (x0, x0 + w), (x1 - w, x1)
    yend = ys - n * tr
    c.rect(x0, ly0, x1, ys, "STAIR")
    c.line((xw[1], yend), (xw[1], ys), "STAIR")
    c.line((xe[0], yend), (xe[0], ys), "STAIR")
    c.line((xw[1] + 0.02, yend), (xe[0] - 0.02, yend), "STAIR")
    for i in range(n + 1):
        y = ys - i * tr
        for xa, xb in (xw, xe):
            c.line((xa, y), (xb, y), "STAIR")
    xm_w, xm_e = sum(xw) / 2, sum(xe) / 2
    yb = (ys + yend) / 2
    if fl != "F":     # cut line across the up flight
        c.line((xw[0], yb + 0.35), (xw[1], yb - 0.35), "STAIR", w=0.35)
    if fl == "B":
        path = [(xm_w, ys - 0.15), (xm_w, (ly0 + ly1) / 2), (xm_e, (ly0 + ly1) / 2), (xm_e, ys - 0.25)]
        _walk(c, path, "עולה")
    elif fl == "G":
        _walk(c, [(xm_w, ys - 0.15), (xm_w, yend + 0.3)], "עולה")
        _walk(c, [(xm_e, ys - 0.15), (xm_e, yend + 0.3)], "יורד")
    else:
        path = [(xm_e, ys - 0.15), (xm_e, (ly0 + ly1) / 2), (xm_w, (ly0 + ly1) / 2), (xm_w, ys - 0.25)]
        _walk(c, path, "יורד")


def _walk(c, path, word):
    for a, b in zip(path, path[1:]):
        c.line(a, b, "STAIR", w=0.15)
    (xa, ya), (xb, yb) = path[-2], path[-1]
    L = math.hypot(xb - xa, yb - ya) or 1
    ux, uy = (xb - xa) / L, (yb - ya) / L
    for sgn in (1, -1):
        c.line((xb, yb), (xb - 0.22 * ux + sgn * 0.1 * -uy, yb - 0.22 * uy + sgn * 0.1 * ux), "STAIR", w=0.15)
    c.circle(path[0], 0.06, "STAIR", fill="dark")
    c.text((path[0][0], path[0][1] + 0.28), word, "TEXT-S", h=0.15)


def lift(c, fl):
    x0, y0, x1, y1 = M.ELEV_RECT
    c.rect(x0 + 0.1, y0 + 0.1, x1 - 0.1, y1 - 0.1, "STAIR")
    c.line((x0 + 0.1, y0 + 0.1), (x1 - 0.1, y1 - 0.1), "STAIR")
    c.line((x0 + 0.1, y1 - 0.1), (x1 - 0.1, y0 + 0.1), "STAIR")


# ------------------------------------------------------------------ labels
def _label_pos(r):
    if r.get("label"):
        return r["label"]
    q = max(r["rects"], key=M.rect_area)
    return ((q[0] + q[2]) / 2, (q[1] + q[3]) / 2)


def labels(c, fl, compact=False):
    for r in M.rooms_of(fl):
        if r["id"] in ("B07", "G11", "F17"):
            x0, y0, x1, y1 = M.ELEV_RECT
            c.text(((x0 + x1) / 2, (y0 + y1) / 2), "מעלית", "TEXT", h=0.2, bold=True)
            continue
        if r["id"] in ("B06", "G10", "F16"):
            continue
        x, y = _label_pos(r)
        a = M.room_area(r)
        small = a < 6.0
        h = (0.2 if small else TXT_NAME) * (0.9 if compact else 1.0)
        q = min(r["rects"], key=lambda q: (abs((q[0] + q[2]) / 2 - x) + abs((q[1] + q[3]) / 2 - y)))
        narrow = (q[2] - q[0]) < 1.8 and (q[3] - q[1]) > (q[2] - q[0])
        if small:
            c.text((x, y + 0.12), r["name"], "TEXT", h=h, bold=True)
            c.text((x, y - 0.18), f"{a:.1f}", "TEXT-S", h=0.15)
            continue
        sub = f"{a:.1f} מ״ר"
        if not compact and len(r["rects"]) == 1:
            sub += f" · {q[2] - q[0]:.2f}×{q[3] - q[1]:.2f}"
        if narrow:
            c.text((x - h * 0.6, y), r["name"], "TEXT", h=h, bold=True, rot=90)
            c.text((x + h * 0.55, y), sub, "TEXT-S", h=TXT_AREA * 0.9, rot=90)
        else:
            c.text((x, y + h * 0.75), r["name"], "TEXT", h=h, bold=True)
            c.text((x, y - h * 0.55), sub, "TEXT-S", h=TXT_AREA * (0.85 if compact else 1.0))


def level_mark(c, p, z, txt=None):
    x, y = p
    c.poly([(x, y), (x - 0.16, y + 0.22), (x + 0.16, y + 0.22)], "LEVEL", fill="white")
    c.line((x - 0.16, y + 0.22), (x + 1.25, y + 0.22), "LEVEL")
    c.text((x + 0.2, y + 0.4), txt or f"{lvl(z)} (+{M.ABS0 + z:.2f})", "LEVEL", h=0.17, anchor="r")


# ------------------------------------------------------------------ dimensions
def _segments(line, g):
    out = []
    inter = line.intersection(g)
    for part in ([inter] if inter.geom_type == "LineString" else list(getattr(inter, "geoms", []))):
        if part.geom_type == "LineString" and part.length > 1e-4:
            (xa, ya), (xb, yb) = part.coords[0], part.coords[-1]
            out.append((min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)))
    return out


def chain(c, fl, axis, at, lo=-100.0, hi=100.0):
    """Interior chain along a line: clear room sizes and wall thicknesses."""
    out = M.floor_outline(fl)
    line = LineString([(lo, at), (hi, at)]) if axis == "H" else LineString([(at, lo), (at, hi)])
    solid = M.wall_solid(fl)
    spans = []
    for x0, y0, x1, y1 in _segments(line, out.difference(solid)):
        spans.append(("room", x0, y0, x1, y1))
    for x0, y0, x1, y1 in _segments(line, solid):
        spans.append(("wall", x0, y0, x1, y1))
    for kind, x0, y0, x1, y1 in spans:
        if axis == "H":
            if kind == "room":
                c.dim((x0, at), (x1, at), "H", at, h=TXT_DIM)
            else:
                c.dim((x0, at), (x1, at), "H", at, h=0.1, side=-1)
        else:
            if kind == "room":
                c.dim((at, y0), (at, y1), "V", at, h=TXT_DIM)
            else:
                c.dim((at, y0), (at, y1), "V", at, h=0.1, side=-1)


def _facade_points(fl, side, rect):
    """Stations along one facade: outline corners, opening edges and the faces of walls that meet it."""
    x0, y0, x1, y1 = rect
    pts = set()
    if side in ("S", "N"):
        yf = y0 if side == "S" else y1
        pts |= {x0, x1}
        band = (yf, yf + 0.3) if side == "S" else (yf - 0.3, yf)
        for o in M.openings_of(fl):
            ox0, oy0, ox1, oy1 = o["rect"]
            if o["axis"] == "H" and abs(oy0 - band[0]) < 0.02 and abs(oy1 - band[1]) < 0.02 and x0 - 1e-6 <= ox0 and ox1 <= x1 + 1e-6:
                pts |= {ox0, ox1}
    else:
        xf = x0 if side == "W" else x1
        pts |= {y0, y1}
        band = (xf, xf + 0.3) if side == "W" else (xf - 0.3, xf)
        for o in M.openings_of(fl):
            ox0, oy0, ox1, oy1 = o["rect"]
            if o["axis"] == "V" and abs(ox0 - band[0]) < 0.02 and abs(ox1 - band[1]) < 0.02 and y0 - 1e-6 <= oy0 and oy1 <= y1 + 1e-6:
                pts |= {oy0, oy1}
    return sorted(pts)


def _wall_axes(fl, side, rect):
    """Centre lines of the interior walls that meet the facade."""
    x0, y0, x1, y1 = rect
    solid = M.wall_solid(fl)
    out = set()
    if side in ("S", "N"):
        y = y0 + 0.45 if side == "S" else y1 - 0.45
        for a, _, b, _ in _segments(LineString([(x0 + 0.31, y), (x1 - 0.31, y)]), solid):
            if b - a < 0.4:
                out.add(round((a + b) / 2, 3))
        return sorted({x0, x1} | out)
    x = x0 + 0.45 if side == "W" else x1 - 0.45
    for _, a, _, b in _segments(LineString([(x, y0 + 0.31), (x, y1 - 0.31)]), solid):
        if b - a < 0.4:
            out.add(round((a + b) / 2, 3))
    return sorted({y0, y1} | out)


EXT_DIMS = {   # (side, facade rectangle, rows)
    "B": [("S", (5.5, 12.2, 27.5, 34.0), 3), ("W", (5.5, 12.2, 27.5, 34.0), 3), ("N", (5.5, 12.2, 27.5, 34.0), 3), ("E", (5.5, 12.2, 27.5, 34.0), 2)],
    "G": [("W", (5.5, 22.05, 36.0, 34.0), 3), ("N", (5.5, 22.05, 36.0, 34.0), 3), ("S", (5.5, 22.05, 36.0, 34.0), 3),
          ("E", (45.5, 20.5, 51.0, 34.0), 2), ("S", (45.5, 20.5, 51.0, 34.0), 1)],
    "F": [("S", (5.5, 22.05, 27.5, 34.0), 3), ("W", (5.5, 22.05, 27.5, 34.0), 3), ("N", (5.5, 22.05, 27.5, 34.0), 3), ("E", (5.5, 22.05, 27.5, 34.0), 2)],
}


def exterior_dims(c, fl):
    for side, rect, rows in EXT_DIMS[fl]:
        x0, y0, x1, y1 = rect
        sets = [_facade_points(fl, side, rect), _wall_axes(fl, side, rect), None][:rows]
        for i, pts in enumerate(sets):
            off = 1.0 + 0.75 * i
            if pts is None:
                pts = [x0, x1] if side in ("S", "N") else [y0, y1]
            if side == "S":
                at = y0 - off
                for a, b in zip(pts, pts[1:]):
                    c.dim((a, y0), (b, y0), "H", at, h=TXT_DIM)
            elif side == "N":
                at = y1 + off
                for a, b in zip(pts, pts[1:]):
                    c.dim((a, y1), (b, y1), "H", at, h=TXT_DIM)
            elif side == "W":
                at = x0 - off
                for a, b in zip(pts, pts[1:]):
                    c.dim((x0, a), (x0, b), "V", at, h=TXT_DIM)
            else:
                at = x1 + off
                for a, b in zip(pts, pts[1:]):
                    c.dim((x1, a), (x1, b), "V", at, h=TXT_DIM)


CHAINS = {
    "B": [("H", 13.3, 5.0, 28.0), ("H", 21.5, 5.0, 28.0), ("H", 24.55, 5.0, 28.0), ("H", 32.85, 5.0, 28.0),
          ("V", 6.55, 12.0, 34.2), ("V", 16.35, 12.0, 34.2), ("V", 22.95, 12.0, 34.2), ("V", 26.25, 12.0, 34.2)],
    "G": [("H", 24.4, 5.0, 28.0), ("H", 31.0, 5.0, 28.0), ("V", 9.0, 21.8, 34.2), ("V", 15.0, 21.8, 34.2), ("V", 25.8, 21.8, 34.2)],
    "F": [("H", 24.4, 5.0, 28.0), ("H", 31.0, 5.0, 28.0), ("V", 9.0, 21.8, 34.2), ("V", 15.0, 21.8, 34.2), ("V", 25.8, 21.8, 34.2)],
}


def interior_dims(c, fl):
    for axis, at, lo, hi in CHAINS[fl]:
        chain(c, fl, axis, at, lo, hi)


# ------------------------------------------------------------------ outdoor context
def _plot_and_lines(c):
    c.poly(M.SITE["plot"], "PLOT", dash="8 3 2 3")
    c.poly(M.SITE["building_line"], "BLINE", dash="6 3")


def pillars(c, site=False):
    for p in M.PILLARS:
        x0, y0, x1, y1 = p["rect"]
        c.rect(x0, y0, x1, y1, "UTIL", fill="util")
        f = p["face"]
        if f == "W":
            c.line((x0, y0 + 0.05), (x0, y1 - 0.05), "UTIL", w=0.6)
        elif f == "E":
            c.line((x1, y0 + 0.05), (x1, y1 - 0.05), "UTIL", w=0.6)
        else:
            c.line((x0 + 0.05, y0), (x1 - 0.05, y0), "UTIL", w=0.6)
        if f in ("W", "E"):
            c.text((x1 + 0.25 if f == "W" else x0 - 0.25, (y0 + y1) / 2), p["short"], "UTIL-T", h=0.2, anchor="l" if f == "W" else "r")
        else:
            c.text(((x0 + x1) / 2, y1 + 0.3), p["short"], "UTIL-T", h=0.2)
    for name, (a, b) in M.GATES.items():
        c.line(a, b, "OUT", w=0.5)


def _terrace(c, below=False):
    tx0, ty0, tx1, ty1 = M.TERRACE
    g0, g1 = M.TERRACE_GATE
    lay = "BELOW" if below else "PAVE"
    if below:
        c.rect(tx0, ty0, tx1, ty1, "BELOW", dash="4 2")
        return
    c.rect(tx0, ty0, tx1, ty1, "PAVE", fill="deck")
    for r in ((tx0, ty0, g0 - 0.15, ty0 + 0.8), (g1 + 0.15, ty0, tx1, ty0 + 0.8), (tx0, ty0 + 0.8, tx0 + 0.8, ty1)):
        c.rect(*r, "GREEN", fill="green")
    c.text(((tx0 + tx1) / 2 - 3.0, 16.4), "מרפסת גג", "TEXT", h=0.3, bold=True)
    c.text(((tx0 + tx1) / 2 - 3.0, 15.9), "מעל החניון והמרתף", "TEXT-S", h=0.2)


def _ext_stair(c, below=False):
    e = M.EXT_STAIR
    lay = "BELOW" if below else "STAIR"
    c.rect(e["x0"], e["y0"], e["x1"], e["y1"], lay)
    for i in range(1, e["n"]):
        x = e["x0"] + i * e["tread"]
        c.line((x, e["y0"]), (x, e["y1"]), lay)
    c.rect(*M.EXT_LANDING, lay)
    if not below:
        _walk(c, [(e["x0"] + 0.2, (e["y0"] + e["y1"]) / 2), (e["x1"] - 0.15, (e["y0"] + e["y1"]) / 2)], "")
        c.text(((e["x0"] + e["x1"]) / 2, e["y0"] - 0.35), "מדרגות כניסה אל מרפסת הגג · 20 רומים", "TEXT-S", h=0.17)


def outdoor(c, fl):
    _plot_and_lines(c)
    pillars(c)
    if fl == "B":
        c.poly(M.DRIVEWAY, "PAVE", fill="pave")
        c.text((9.5, 10.6), "רחבת כניסה וחניה · −3.50", "TEXT-S", h=0.22)
        c.poly(M.OFFICE_COURT, "PAVE", fill="pave")
        c.text((3.1, 30.5), "חצר המשרד", "TEXT", h=0.24, bold=True, rot=90)
        c.text((2.5, 30.5), "כניסת לקוחות מהרחוב", "TEXT-S", h=0.17, rot=90)
        ex0, ey0, ex1, ey1 = M.ENGLISH_COURT
        c.rect(ex0, ey0, ex1, ey1, "PAVE", fill="pave")
        c.text(((ex0 + ex1) / 2, (ey0 + ey1) / 2), "חצר אנגלית (שקועה, בגובה המרתף)", "TEXT-S", h=0.2)
        _ext_stair(c)
        level_mark(c, (8.2, 10.0), -3.50)
        level_mark(c, (2.4, 21.0), -3.50)
    elif fl == "G":
        _terrace(c)
        _ext_stair(c, below=False)
        c.rect(*M.POOL_DECK, "PAVE", fill="deck")
        c.rect(*M.POOL, "WATER", fill="water")
        c.rect(*M.NORTH_PATH, "PAVE", fill="pave")
        for x0, y0, x1, y1 in M.BALCONIES:
            c.rect(x0, y0, x1, y1, "BELOW", dash="4 2")
        ex0, ey0, ex1, ey1 = M.ENGLISH_COURT
        c.rect(ex0, ey0, ex1, ey1, "BELOW", dash="4 2")
        c.poly(M.OFFICE_COURT, "BELOW", dash="4 2")
        level_mark(c, (9.0, 18.4), 0.0)
    else:
        _terrace(c, below=True)
        for x0, y0, x1, y1 in M.BALCONIES:
            c.rect(x0, y0, x1, y1, "PAVE", fill="deck")
        c.rect(27.5, 22.05, 36.0, 34.0, "ROOF", fill="roof")
        c.text((31.75, 28.0), "גג ירוק מעל הסלון", "TEXT", h=0.28, bold=True)
        c.text((31.75, 27.4), f"{lvl(M.LIVING_TOP)}", "TEXT-S", h=0.2)
        c.rect(45.5, 20.5, 51.0, 34.0, "ROOF", fill="roof")
        c.rect(*M.POOL, "BELOW", dash="4 2")


# ------------------------------------------------------------------ fixtures and furniture
def _bays(c):
    for x in (8.6, 11.4, 14.2):
        c.line((x, 12.5), (x, 17.7), "PARK", w=0.25)
    c.line((5.8, 17.7), (17.0, 17.7), "PARK", dash="5 3")
    for i, x in enumerate((7.2, 10.0, 12.8, 15.6)):
        c.text((x, 13.1), str(i + 1), "PARK", h=0.3, bold=True)


def _partition(c, *runs_and_t):
    """Thin built-in partitions (drawn as double lines) between the given points."""
    *runs, t = runs_and_t
    for run in runs:
        for a, b in zip(run, run[1:]):
            if abs(a[1] - b[1]) < 1e-9:
                c.rect(min(a[0], b[0]), a[1], max(a[0], b[0]), a[1] + t, "FIX", fill="white")
            else:
                c.rect(a[0], min(a[1], b[1]), a[0] + t, max(a[1], b[1]), "FIX", fill="white")


def _door_mark(c, a, b, swing, axis="H"):
    """A small door leaf and swing in a partition opening from a to b."""
    w = math.hypot(b[0] - a[0], b[1] - a[1])
    if axis == "H":
        tip = (a[0], a[1] + swing * w)
        c.line(a, tip, "DOOR", w=0.25)
        c.arc(a, w, 0 if swing > 0 else -90, 90 if swing > 0 else 0, "DOOR-T")
    else:
        tip = (a[0] + swing * w, a[1])
        c.line(a, tip, "DOOR", w=0.25)
        c.arc(a, w, 90 if swing < 0 else 0, 180 if swing < 0 else 90, "DOOR-T")


def fixtures(c, fl):
    """Built-in items drawn on every plan: parking bays, sanitary ware, kitchens, closets."""
    if fl == "B":
        _bays(c)
        # office WC and kitchenette (23.8-27.2 x 20.9-27.71): accessible WC at the south, a WC, basins, kitchenette at the door
        _partition(c, [(23.8, 23.1), (24.0, 23.1)], [(24.95, 23.1), (27.2, 23.1)], 0.1)          # accessible WC 3.40 x 2.20
        _door_mark(c, (24.0, 23.15), (24.95, 23.15), -1)
        place(c, S.wc(), 27.2, 22.0, 90)
        place(c, S.basin(), 25.4, 20.9, 0)
        c.text((24.6, 21.7), "תא נגיש", "TEXT-S", h=0.15)
        _partition(c, [(25.75, 23.2), (25.75, 23.4)], [(25.75, 24.25), (25.75, 24.9)], 0.1)       # WC 1.45 x 1.70
        _partition(c, [(25.75, 24.9), (27.2, 24.9)], [], 0.1)
        _door_mark(c, (25.8, 23.4), (25.8, 24.25), -1, axis="V")
        place(c, S.wc(), 27.2, 24.05, 90)
        place(c, S.basin(0.55, 0.42), 23.8, 24.2, -90)
        place(c, S.counter(2.5, sink=0.9), 27.2, 25.1, 90)
        place(c, S.shelf(1.8, 0.4), 23.8, 27.55, -90)
        # storage shelving
        place(c, S.shelf(4.6, 0.6), 17.15, 17.35, -90)
        place(c, S.shelf(2.7, 0.6), 20.3, 12.75, 90)
        place(c, S.shelf(1.9, 0.6), 17.75, 12.5, 0)
        # systems room
        place(c, S.tank(0.45), 24.6, 18.35)
        place(c, S.tank(0.45), 25.6, 18.35)
        c.rect(26.45, 18.0, 27.2, 20.4, "FIX")
        c.text((26.82, 19.2), "לוח חשמל", "TEXT-S", h=0.13, rot=90)
        # closet
        place(c, S.shelf(1.9, 0.6), 20.25, 24.55)
    elif fl == "G":
        pass
    else:
        pass


def furniture(c, fl):
    if fl == "B":
        cars = ("car_red", "car_grey", "car_white", "car_blue")
        for i, x in enumerate((7.2, 10.0, 12.8, 15.6)):
            place(c, S.car(color=cars[i]), x, 15.05, 0)
        # cinema: screen on the east wall, two rows of four, seats face east
        c.line((27.05, 13.2), (27.05, 16.85), "FIX", w=0.5)
        c.text((26.75, 15.0), "מסך", "TEXT-S", h=0.15, rot=90)
        for row, xr in enumerate((22.0, 23.35)):
            for j in range(4):
                place(c, S.cinema_seat(), xr, 13.45 + j * 0.85 + (0.0 if row == 0 else 0.0), -90)
        place(c, S.rug(2.4, 3.6), 24.9, 15.0)
        # family lobby: bench and shoe cabinet
        place(c, S.bench(1.6, 0.42), 17.15, 19.3, -90)
        place(c, S.console(1.4, 0.38), 17.15 + 0.0, 21.0, -90)
        # meeting room
        place(c, S.dining(3.0, 1.1, per_side=4, ends=True), 8.4, 21.0)
        # principal architect
        place(c, S.desk(1.8, 0.8), 15.4, 21.6, 90)
        place(c, S.shelf(3.6, 0.4), 17.0, 19.4, 90)
        place(c, S.round_table(0.5), 12.4, 22.4)
        for ang in (-30, 90, 210):
            place(c, S.chair(), 12.4 + 0.75 * math.cos(math.radians(ang)), 22.4 + 0.75 * math.sin(math.radians(ang)), ang + 90)
        # reception and waiting
        place(c, S.desk(1.8, 0.75), 8.9, 26.85, 180)
        place(c, S.sofa(2.0, 0.85, seats=2), 6.3, 23.75, 0)
        place(c, S.round_table(0.3), 7.3, 25.0)
        place(c, S.plant(0.3), 10.6, 24.2)
        # studio: ten desks in two rows facing the windows, plus plotter and plan chests
        for j in range(5):
            x = 6.9 + j * 1.9
            place(c, S.desk(1.6, 0.75), x, 31.0, 0)
            place(c, S.desk(1.6, 0.75), x, 29.0, 180)
        place(c, S.plotter(), 14.8, 33.25, 180)
        place(c, S.shelf(3.4, 0.45), 17.15, 24.2, 90)
        place(c, S.table(2.4, 1.2), 14.2, 26.0)
        for dx in (-0.6, 0.6):
            for sy in (-1, 1):
                place(c, S.chair(), 14.2 + dx, 26.0 + sy * 0.95, 90 + 90 * sy)
        # workshop and materials
        place(c, S.table(3.0, 1.2, mat="wood"), 23.4, 30.95)
        place(c, S.shelf(4.0, 0.5), 27.2, 29.6, 90)
        place(c, S.rack(1.8, 0.5), 20.0, 33.7, -90 + 180)
        place(c, S.counter(2.2, sink=0.6), 19.9, 31.0, -90)
        # shelter
        place(c, S.shelf(3.6, 0.45), 17.3, 29.5 + 3.6, -90)
    elif fl == "G":
        pass
    else:
        pass


def furniture_solids():
    out = {}
    for fl in "BGF":
        c = Canvas()
        fixtures(c, fl)
        furniture(c, fl)
        out[fl] = c.solids
    return out


# ------------------------------------------------------------------ section marks
CUTS_PLAN = {"A": ("H", 24.0, -1.4, 56.7), "B": ("V", 14.0, 8.4, 38.0), "C": ("V", 19.4, 8.4, 38.0)}


def section_marks(c):
    for name, (axis, at, lo, hi) in CUTS_PLAN.items():
        letter = {"A": "א", "B": "ב", "C": "ג"}[name]
        if axis == "H":
            a, b = (lo, at), (hi, at)
            arrow = (0, 1)
        else:
            a, b = (at, lo), (at, hi)
            arrow = (-1, 0)
        c.line(a, b, "CUT", dash="12 3 2 3", w=0.2)
        for p in (a, b):
            c.line(p, (p[0] + arrow[0] * 0.8, p[1] + arrow[1] * 0.8), "CUT", w=0.5)
            c.circle((p[0] + arrow[0] * 1.15, p[1] + arrow[1] * 1.15), 0.35, "CUT", fill="white")
            c.text((p[0] + arrow[0] * 1.15, p[1] + arrow[1] * 1.15), letter, "TEXT", h=0.32, bold=True)


LEVEL_AT = {"B": (20.4, 18.35), "G": (24.2, 23.0), "F": (12.6, 28.2)}


# ------------------------------------------------------------------ floor plan
def floor_canvas(fl, mode="arch"):
    c = Canvas()
    outdoor(c, fl)
    for r in M.rooms_of(fl):
        for q in r["rects"]:
            c.rect(*q, "OUT", fill="room", w=0.01)
    stair(c, fl)
    lift(c, fl)
    fixtures(c, fl)
    if mode == "furn":
        furniture(c, fl)
    walls(c, fl)
    openings(c, fl)
    labels(c, fl, compact=(mode == "furn"))
    if mode == "arch":
        exterior_dims(c, fl)
        interior_dims(c, fl)
        section_marks(c)
    level_mark(c, LEVEL_AT[fl], M.LEVELS[fl]["z"])
    return c


def site_canvas():
    """Site plan: written in stage 4."""
    c = Canvas()
    _plot_and_lines(c)
    pillars(c, site=True)
    return c
