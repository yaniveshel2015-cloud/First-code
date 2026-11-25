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


def _leaf(c, f, hinge_s, tip_s, face, out, layer="DOOR"):
    """Door leaf standing open at 90 degrees from the hinge, and its swing arc back to the closed position."""
    pt = f["pt"]
    w = abs(tip_s - hinge_s)
    tip = face + out * w
    c.line(pt(hinge_s, face), pt(hinge_s, tip), layer, w=0.3)
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
        lay = "GLASS" if o.get("glass") else "DOOR"
        if k == "door":
            if o.get("hinge", "a") == "a":
                _leaf(c, f, a, b, face, sw, lay)
            else:
                _leaf(c, f, b, a, face, sw, lay)
        else:
            m = (a + b) / 2
            _leaf(c, f, a, m, face, sw, lay)
            _leaf(c, f, b, m, face, sw, lay)
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
        w_txt = len(r["name"]) * h * 0.68                    # rough width of the name as rendered
        narrow = (q[3] - q[1]) > (q[2] - q[0]) and ((q[2] - q[0]) < 2.1 or w_txt > (q[2] - q[0]) - 0.25)
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
    "G": [("H", 22.95, 5.0, 36.3), ("H", 28.5, 5.0, 36.3), ("H", 33.05, 5.0, 36.3),
          ("V", 6.55, 21.8, 34.2), ("V", 16.4, 21.8, 34.2), ("V", 21.5, 21.8, 34.2), ("V", 26.6, 21.8, 34.2), ("V", 34.9, 21.8, 34.2)],
    "F": [("H", 22.95, 5.0, 28.0), ("H", 28.5, 5.0, 28.0), ("H", 33.05, 5.0, 28.0),
          ("V", 6.55, 21.8, 34.2), ("V", 12.0, 21.8, 34.2), ("V", 21.2, 21.8, 34.2), ("V", 26.0, 21.8, 34.2)],
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
        c.rect(*r, "PLANT", fill="green")
    px0, py0, px1, py1 = M.PATIO
    c.poly([(px0 - 0.3, py0 - 0.3), (px1, py0 - 0.3), (px1, py1 + 0.3), (px0 - 0.3, py1 + 0.3)], "PLANT", fill="green",
           holes=[[(px0, py0), (px1, py0), (px1, py1), (px0, py1)]])                 # planters around the opening
    c.rect(px0, py0, px1, py1, "OUT", fill="white")
    c.rect(px0 + 0.05, py0 + 0.05, px1 - 0.05, py1 - 0.05, "OUT", dash="2 1", w=0.3)
    c.text(((px0 + px1) / 2, (py0 + py1) / 2), "פתח פטיו אל המרתף", "TEXT-S", h=0.17)
    for x0, y0, x1, y1 in M.SKYLIGHTS:
        c.rect(x0, y0, x1, y1, "GLASS", fill="glass")
    c.text((11.4, 18.45), "פס רצפת זכוכית, אור למרתף", "TEXT-S", h=0.15)
    c.text((20.3, 14.4), "מרפסת גג", "TEXT", h=0.3, bold=True)
    c.text((20.3, 13.9), "מעל החניון והמרתף", "TEXT-S", h=0.2)


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
        c.text((12.0, (ey0 + ey1) / 2), "חצר אנגלית שקועה, בגובה המרתף · אור ואוויר לסטודיו, לשירותים, למטבחון ולמקלט", "TEXT-S", h=0.2)
        px0, py0, px1, py1 = M.PATIO
        c.rect(px0, py0, px1, py1, "GREEN", fill="green")
        c.circle(((px0 + px1) / 2 + 0.6, (py0 + py1) / 2), 0.9, "TREE", fill="tree")
        c.text(((px0 + px1) / 2 - 0.9, (py0 + py1) / 2 + 0.25), "פטיו", "TEXT", h=0.26, bold=True)
        c.text(((px0 + px1) / 2 - 0.9, (py0 + py1) / 2 - 0.25), "פתוח לשמיים", "TEXT-S", h=0.17)
        for x0, y0, x1, y1 in M.SKYLIGHTS:
            c.rect(x0, y0, x1, y1, "CEIL", dash="4 2")
        c.text((11.4, 17.95), "חלונות גג במרפסת שמעל", "CEIL", h=0.15)
        r = M.OFFICE_RAMP
        for x0, y0, x1, y1 in r["landings"]:
            c.rect(x0, y0, x1, y1, "PAVE", fill="pave")
        for x0, y0, x1, y1, d in r["runs"]:
            c.rect(x0, y0, x1, y1, "STAIR")
            xm = (x0 + x1) / 2
            ya, yb = (y1 - 0.2, y0 + 0.2) if d < 0 else (y0 + 0.2, y1 - 0.2)
            _walk(c, [(xm, ya), (xm, yb)], "")
        c.text((2.3, 21.6), "רמפה נגישה 1:12 מהשער ברחוב", "TEXT-S", h=0.15)
        _ext_stair(c)
        level_mark(c, (8.2, 10.0), -3.50)
        level_mark(c, (2.4, 21.0), -3.50)
    elif fl == "G":
        _terrace(c)
        _ext_stair(c, below=False)
        c.rect(*M.POOL_DECK, "PAVE", fill="deck")
        c.rect(*M.POOL, "WATER", fill="water")
        c.rect(*M.NORTH_PATH, "PAVE", fill="pave")
        c.rect(*M.BRIDGE, "PAVE", fill="deck")
        c.text(((M.BRIDGE[0] + M.BRIDGE[2]) / 2, (M.BRIDGE[1] + M.BRIDGE[3]) / 2), "גשר", "TEXT-S", h=0.15)
        for x0, y0, x1, y1 in M.BALCONIES:
            c.rect(x0, y0, x1, y1, "BELOW", dash="4 2")
        ex0, ey0, ex1, ey1 = M.ENGLISH_COURT
        c.rect(ex0, ey0, ex1, ey1, "BELOW", dash="4 2")
        c.poly(M.OFFICE_COURT, "BELOW", dash="4 2")
        level_mark(c, (13.6, 15.4), 0.0)
    else:
        _terrace(c, below=True)
        for x0, y0, x1, y1 in M.BALCONIES:
            c.rect(x0, y0, x1, y1, "PAVE", fill="deck")
        c.line((11.47, 20.25), (11.47, 22.05), "FIX", w=0.4)
        c.text((8.6, 21.15), "מרפסת הורים", "TEXT-S", h=0.17)
        c.text((14.35, 21.15), "מרפסת הילד", "TEXT-S", h=0.17)
        c.text((24.8, 21.15), "מרפסת נוער 1", "TEXT-S", h=0.17)
        c.rect(27.5, 22.05, 36.0, 34.0, "ROOF", fill="roof")
        c.text((30.4, 28.0), "גג ירוק מעל הסלון", "TEXT", h=0.28, bold=True)
        c.text((30.4, 27.4), f"{lvl(M.LIVING_TOP)}", "TEXT-S", h=0.2)
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
        # office WCs under the mamad tower (17.3-19.75 x 29.31-33.7): accessible cubicle by the window, a WC, basin
        _partition(c, [(17.3, 31.2), (17.45, 31.2)], [(18.4, 31.2), (19.75, 31.2)], 0.1)
        _door_mark(c, (18.4, 31.25), (17.45, 31.25), -1)
        place(c, S.wc(), 17.3, 32.35, -90)
        place(c, S.basin(), 18.95, 33.7, 180)
        c.circle((18.65, 32.4), 0.75, "FIX", dash="2 2")
        c.text((18.75, 31.5), "תא נגיש", "TEXT-S", h=0.13)
        _partition(c, [(18.65, 29.31), (18.65, 30.15)], [(18.65, 30.9), (18.65, 31.2)], 0.1)
        _door_mark(c, (18.7, 30.15), (18.7, 30.9), -1, axis="V")
        place(c, S.wc(), 19.75, 29.95, 90)
        place(c, S.basin(0.55, 0.42), 17.3, 30.75, -90)
        # kitchenette (19.9-22.2 x 29.31-33.7)
        place(c, S.counter(2.6, sink=1.3), 22.2, 29.6, 90)
        place(c, S.tall_units(0.9, 0.65, fridge=0.9), 22.2, 32.4, 90)
        # storage shelving
        place(c, S.shelf(4.6, 0.6), 17.15, 17.35, -90)
        place(c, S.shelf(2.7, 0.6), 20.3, 12.75, 90)
        place(c, S.shelf(1.9, 0.6), 17.75, 12.5, 0)
        # systems room (24.5-27.2 x 21.05-27.71)
        place(c, S.tank(0.45), 25.35, 26.9)
        place(c, S.tank(0.45), 26.45, 26.9)
        c.rect(26.5, 23.4, 27.2, 25.6, "FIX")
        c.text((26.85, 24.5), "לוח חשמל", "TEXT-S", h=0.13, rot=90)
        # closet
        place(c, S.shelf(1.9, 0.6), 20.25, 24.55)
        # shared shelter: emergency cabinet and folding benches along the walls
        place(c, S.shelf(1.6, 0.5), 22.35, 33.5, -90)
        for x0, y0, x1, y1 in ((22.4, 29.25, 22.85, 31.7), (24.25, 27.9, 26.6, 28.35)):
            c.rect(x0, y0, x1, y1, "FIX", dash="3 2")
    elif fl == "G":
        # kitchen: counter on the east wall, tall units on the north wall, island
        place(c, S.counter(3.6, sink=None, hob=1.8), 17.15, 22.6, 90)
        place(c, S.tall_units(3.0, 0.65, fridge=0.9), 14.4, 29.16, 180)
        place(c, S.tall_units(1.4, 0.65, fridge=0.0), 17.0, 29.16, 180)
        # back kitchen
        place(c, S.counter(3.2, sink=1.6), 16.95, 33.7, 180)
        place(c, S.shelf(2.2, 0.6), 13.75, 32.9, -90)
        # pantry: shelves on the east wall and the south part of the west wall
        place(c, S.shelf(4.1, 0.5), 19.75, 29.5, 90)
        place(c, S.shelf(1.6, 0.5), 17.3, 31.0, -90)
        # service and dog room
        place(c, S.shower(1.2, 1.0), 21.1, 33.7, 180)
        c.text((20.5, 33.0), "מקלחת לכלב", "TEXT-S", h=0.12)
        place(c, S.counter(1.6, sink=0.8), 19.9, 31.6, -90)
        place(c, S.shelf(2.6, 0.5), 25.2, 29.6, 90)
        # guest WC
        place(c, S.wc(), 26.3, 33.7, 180)
        place(c, S.vanity(1.2, 0.5, n=1), 27.2, 29.9, 90)
        # coat cupboard in the hall
        place(c, S.wardrobe(2.5, 0.6), 27.05, 27.71, 180)
        living(c, fixed=True)
        spa(c, fixed=True)
    else:
        # parents' bath (8.75-11.4 x 29.31-33.7): tub under the window, shower, double basin, WC
        place(c, S.bathtub(1.75, 0.8), 11.2, 33.7, 180)
        place(c, S.shower(1.0, 1.1), 11.4, 31.9, 90)
        place(c, S.vanity(1.4, 0.55, n=2), 11.4, 29.5, 90)
        place(c, S.wc(), 8.75, 32.45, -90)
        # parents' closet: wardrobes on the west and north walls, dresser island
        place(c, S.wardrobe(3.7, 0.6), 5.8, 33.0, -90)
        place(c, S.wardrobe(2.0, 0.6), 8.55, 33.7, 180)
        place(c, S.table(1.2, 0.6, h=0.9), 7.6, 31.0)
        # child's bath (14.75-17.15 x 29.31-33.7)
        place(c, S.bathtub(1.7, 0.75), 16.95, 33.7, 180)
        place(c, S.wc(), 17.15, 31.7, 90)
        place(c, S.basin(), 14.75, 31.2, -90)
        # teen shower room (19.9-22.6 x 29.31-33.7): shower, two basins, WC
        place(c, S.shower(1.2, 1.0), 22.6, 33.7, 180)
        place(c, S.vanity(1.6, 0.55, n=2), 22.6, 29.7, 90)
        place(c, S.wc(), 19.9, 32.3, -90)
        # laundry and linens (11.55-14.6 x 29.31-33.7)
        place(c, S.washer(2), 13.4, 33.7, 180)
        place(c, S.counter(1.6, sink=0.6), 14.6, 30.9, 90)
        place(c, S.shelf(3.2, 0.5), 11.55, 33.0, -90)
        # wardrobes in the bedrooms
        place(c, S.wardrobe(3.9, 0.6), 15.6, 27.71, 180)
        place(c, S.wardrobe(3.6, 0.6), 27.1, 27.71, 180)
        place(c, S.wardrobe(3.35, 0.6), 23.75, 27.86, 0)
        # mamad as a study: shelves
        place(c, S.shelf(3.6, 0.4), 19.75, 29.6, 90)


def furniture(c, fl):
    if fl == "B":
        cars = ("car_red", "car_grey", "car_white", "car_blue")
        for i, x in enumerate((7.2, 10.0, 12.8, 15.6)):
            place(c, S.car(color=cars[i]), x, 15.05, 0)
        # cinema: screen on the east wall, two rows of four, seats face east
        c.line((27.05, 13.2), (27.05, 16.85), "FIX", w=0.5)
        c.text((26.75, 15.0), "מסך", "TEXT-S", h=0.15, rot=90)
        for xr in (22.0, 23.35):
            for j in range(4):
                place(c, S.cinema_seat(), xr, 13.45 + j * 0.85, -90)
        place(c, S.rug(2.4, 3.6), 24.9, 15.0)
        # family lobby
        place(c, S.bench(1.6, 0.42), 17.15, 21.1, -90)
        place(c, S.plant(0.3), 21.75, 18.15)
        # meeting room
        place(c, S.dining(3.0, 1.1, per_side=4, ends=True), 8.4, 21.45)
        # principal architect
        place(c, S.desk(1.8, 0.8), 15.4, 21.6, 90)
        place(c, S.shelf(3.6, 0.4), 17.0, 19.6, 90)
        place(c, S.round_table(0.5), 12.4, 22.4)
        for ang in (-30, 90, 210):
            place(c, S.chair(), 12.4 + 0.75 * math.cos(math.radians(ang)), 22.4 + 0.75 * math.sin(math.radians(ang)), ang + 90)
        # reception and waiting
        place(c, S.desk(1.8, 0.75), 8.9, 26.85, 180)
        place(c, S.sofa(2.0, 0.85, seats=2), 6.3, 23.75, 0)
        place(c, S.round_table(0.3), 7.3, 25.0)
        place(c, S.plant(0.3), 10.6, 24.2)
        # studio: ten desks in two rows, plotter, plan chests and a work table
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
        # kitchenette table by the window
        place(c, S.table(1.2, 0.7), 20.75, 32.75)
        for dx in (-0.3, 0.3):
            place(c, S.chair(), 20.75 + dx, 32.1, 0)
        # shared shelter, day use: model workshop and materials library
        place(c, S.table(1.1, 2.6, mat="wood"), 24.7, 30.7)
        place(c, S.shelf(5.2, 0.5), 27.2, 28.2, 90)
        place(c, S.rack(1.4, 0.5), 23.95, 33.7, 180)
    elif fl == "G":
        # dining for twelve, along the room
        place(c, S.dining(3.6, 1.1, per_side=5, ends=True), 8.4, 25.6, 90)
        # kitchen island with bar stools toward the dining
        place(c, S.island(3.0, 1.1, stools=4, sink=True), 13.9, 25.4, 90)
        # family and gaming room: sofa facing the TV on the east wall, gaming desk, bean bags
        place(c, S.tv_unit(2.4, 0.45), 13.6, 31.5, 90)
        place(c, S.sofa(2.8, 0.95, seats=3), 9.6, 33.0, -90)
        place(c, S.armchair(0.85, 0.85), 11.3, 33.0, 180)
        place(c, S.rug(2.6, 2.4), 11.4, 31.5)
        place(c, S.desk(1.6, 0.7), 6.9, 33.7, 180)
        place(c, S.beanbag(0.42), 13.0, 30.05)
        # service room: dog bed
        place(c, S.rug(0.9, 0.7), 24.4, 30.2)
        c.text((24.4, 30.2), "מיטת כלב", "TEXT-S", h=0.11)
        # hall: bench by the lift
        place(c, S.bench(1.4, 0.4), 22.35, 25.3, -90)
        living(c, fixed=False)
        spa(c, fixed=False)
        terrace_furniture(c)
    else:
        # parents' bedroom: bed head on the east wall, reading corner by the windows
        place(c, S.bed(1.8, 2.05), 11.4, 24.6, 90)
        for y in (23.25, 25.95):
            place(c, S.nightstand(), 11.4, y, 90)
        place(c, S.armchair(0.8, 0.8), 6.6, 23.2, 45)
        place(c, S.round_table(0.3), 7.5, 22.9)
        place(c, S.rug(2.4, 2.6), 9.2, 24.6)
        # young child: bed, desk, play rug
        place(c, S.bed(1.2, 2.0), 17.15, 24.1, 90)
        place(c, S.desk(1.4, 0.65), 13.0, 22.35, 0)
        place(c, S.rug(2.0, 2.0), 13.6, 25.6)
        place(c, S.beanbag(0.38), 12.2, 26.6)
        # teen 1: bed on the east wall, desk at the window
        place(c, S.bed(1.4, 2.0), 27.2, 24.6, 90)
        place(c, S.desk(1.6, 0.7), 23.6, 22.35, 0)
        place(c, S.armchair(0.8, 0.8), 23.3, 25.8, 0)
        # teen 2: bed on the east wall, desk under the north window
        place(c, S.bed(1.4, 2.0), 27.2, 31.4, 90)
        place(c, S.desk(1.6, 0.7), 24.0, 33.7, 180)
        place(c, S.beanbag(0.4), 23.6, 30.4)
        # mamad as a study
        place(c, S.desk(1.4, 0.65), 18.5, 33.7, 180)


# ------------------------------------------------------------------ living room (unchanged; same data as the SketchUp sheets)
LIV_O = (27.35, 22.35)
LIV = dict(LIB=(2.20, 6.10, 10.95), MARBLE=[(0.55, 2.20), (6.10, 7.80)], MARBLE_Y=11.05, BAYS=[2.20, 3.175, 4.15, 5.125, 6.10], D=11.35,
           CX=4.15, SY=10.70, PY=4.95, HATCH=(0.70, 0.60), BODY=(0.50, 0.40), SOFA=(1.60, 2.25, 6.70, 3.35), CHAISE=(6.70, 2.25, 7.75, 4.75),
           RUG=(0.60, 2.15, 7.90, 7.15), TABLE=(3.85, 6.25, 0.72), SIDE=(5.35, 6.85, 0.40), CHAIRS=[(0.65, 7.05, 1.50, 7.90), (0.65, 8.45, 1.50, 9.30)])


def _lv(x, y):
    return (LIV_O[0] + x, LIV_O[1] + y)


def _lr(r):
    return (LIV_O[0] + r[0], LIV_O[1] + r[1], LIV_O[0] + r[2], LIV_O[1] + r[3])


def living(c, fixed):
    L = LIV
    if fixed:
        x0, x1, yf = L["LIB"]
        c.rect(*_lr((x0, yf, x1, L["D"])), "FIX")
        c.box(*_lr((x0, yf, x1, L["D"])), 0.0, 5.0, "wood", "library")
        for x in L["BAYS"][1:-1]:
            c.line(_lv(x, yf), _lv(x, L["D"]), "FIX")
        for a, b in L["MARBLE"]:
            c.rect(*_lr((a, L["MARBLE_Y"], b, L["D"])), "FIX", fill="dark")
            c.box(*_lr((a, L["MARBLE_Y"], b, L["D"])), 0.0, 5.0, "stone", "marble wall")
        cx, sy, py = L["CX"], L["SY"], L["PY"]
        c.rect(*_lr((cx - 2.25, sy - 0.04, cx + 2.25, sy + 0.04)), "CEIL", dash="3 1.5", w=0.3)
        hx, hy = L["HATCH"]
        c.rect(*_lr((cx - hx / 2, py - hy / 2, cx + hx / 2, py + hy / 2)), "CEIL", dash="3 1.5", w=0.3)
        c.text(_lv(cx, py - 0.55), "מקרן על ליפט בתקרה", "CEIL", h=0.13)
        c.text(_lv(cx, sy - 0.25), "מסך נגלל בתקרה", "CEIL", h=0.13)
        return
    c.rect(*_lr(L["RUG"]), "RUG", dash="4 2")
    x0, y0, x1, y1 = L["SOFA"]
    c.rrect(*_lr(L["SOFA"]), 0.08, "FURN")
    c.line(_lv(x0, y0 + 0.26), _lv(x1, y0 + 0.26), "FURN")
    for i in range(1, 5):
        c.line(_lv(x0 + i * (x1 - x0) / 5, y0 + 0.26), _lv(x0 + i * (x1 - x0) / 5, y1), "FURN")
    c.box(*_lr(L["SOFA"]), 0.0, 0.42, "fabric", "sofa")
    c.box(*_lr((x0, y0, x1, y0 + 0.26)), 0.42, 0.85, "fabric", "sofa back")
    c.rrect(*_lr(L["CHAISE"]), 0.08, "FURN")
    c.box(*_lr(L["CHAISE"]), 0.0, 0.42, "fabric", "chaise")
    for t in (L["TABLE"], L["SIDE"]):
        c.circle(_lv(t[0], t[1]), t[2], "FURN")
        c.cyl(_lv(t[0], t[1]), t[2], 0.0, 0.38, "wood", tag="table")
    for q in L["CHAIRS"]:
        c.rrect(*_lr(q), 0.1, "FURN")
        c.box(*_lr(q), 0.0, 0.42, "leather", "armchair")
    place(c, S.plant(0.4), *_lv(7.6, 9.6))


def spa(c, fixed):
    if fixed:
        place(c, S.sauna(2.3, 2.45), 45.8, 28.55, 0)
        place(c, S.shower(1.0, 1.0), 50.7, 29.5, 90)
        place(c, S.wc(), 49.6, 31.0, 180)
        place(c, S.basin(), 48.25, 29.4, -90)
        place(c, S.jacuzzi(2.2), 48.25, 32.4)
        place(c, S.tank(0.4), 47.0, 21.6)
        place(c, S.tank(0.4), 48.2, 21.6)
        return
    place(c, S.treadmill(), 47.0, 26.6, 180)
    place(c, S.bike(), 48.9, 26.9, 180)
    place(c, S.rack(1.6, 0.45), 50.7, 23.1, 90)
    place(c, S.rug(2.0, 1.4), 47.4, 23.9)


def terrace_furniture(c):
    x0, y0, x1, y1 = M.PERGOLA
    c.rect(x0, y0, x1, y1, "ROOF", dash="6 3")
    for i in range(1, 10):
        x = x0 + i * (x1 - x0) / 10
        c.line((x, y0), (x, y1), "OUT", dash="2 2")
    c.text(((x0 + x1) / 2, y1 - 0.35), "פרגולה", "TEXT-S", h=0.17)
    place(c, S.dining(3.0, 1.0, per_side=4, ends=True), 10.0, 20.6)
    place(c, S.sofa(2.2, 0.85, seats=3), 17.2, 13.3, 0)
    place(c, S.round_table(0.45), 18.3, 14.8)
    for x in (36.9, 37.9):
        for y in (24.0, 27.5):
            place(c, S.lounger(), x, y, 0)
    place(c, S.parasol(1.3), 37.4, 30.9)


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


LEVEL_AT = {"B": (20.4, 18.35), "G": (24.2, 23.0), "F": (20.5, 26.9)}


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
