"""Building sections cut from the plan model. Section coordinates: (s, z) with z relative to level 0.00 = +91.00."""
from shapely.geometry import LineString, Polygon, box as sbox
from shapely.ops import unary_union

import model as M
from symbols import Canvas

CUTS = {
    "A": dict(axis="y", at=24.0, lo=-1.5, hi=61.0),      # along the plot, street to garden
    "B": dict(axis="x", at=14.0, lo=-2.0, hi=43.0),      # across the plot, through garage and office
    "C": dict(axis="x", at=26.55, lo=-2.0, hi=43.0),     # across the plot, through the east stair flight
}
VOID = unary_union([sbox(*M.STAIR_RECT), sbox(*M.ELEV_RECT)])          # stairwell and shaft: no floor slab
SLABS = [  # (rects, top level, thickness, has stairwell void)
    (M.OUTLINES["B"], -3.50, 0.35, False),
    ([(5.5, 12.2, 27.5, 34.0), (27.5, 22.05, 36.0, 34.0)], 0.00, 0.30, True),
    ([(45.5, 20.5, 51.0, 34.0)], 0.00, 0.25, False),
    ([(5.5, 22.05, 27.5, 34.0)] + M.BALCONIES, 3.50, 0.30, True),
    ([(5.5, 22.05, 27.5, 34.0)], 6.80, 0.30, False),
    ([(27.5, 22.05, 36.0, 34.0)], 5.50, 0.30, False),
    ([(45.5, 20.5, 51.0, 34.0)], 3.30, 0.25, False),
]
PARAPET = {6.80: 0.5, 5.50: 0.4, 3.30: 0.3}


def cut_line(cut):
    c = CUTS[cut]
    return LineString([(c["lo"], c["at"]), (c["hi"], c["at"])]) if c["axis"] == "y" else LineString([(c["at"], c["lo"]), (c["at"], c["hi"])])


def spans(geom, cut):
    """Intervals of the section coordinate where the cut line is inside geom."""
    c = CUTS[cut]
    g = geom.intersection(cut_line(cut))
    out = []
    parts = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
    for p in parts:
        if p.geom_type != "LineString" or p.length < 1e-6:
            continue
        xs = [q[0] if c["axis"] == "y" else q[1] for q in p.coords]
        out.append((min(xs), max(xs)))
    out.sort()
    merged = []
    for a, b in out:
        if merged and a - merged[-1][1] < 1e-6:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def wall_top(floor, s0, cut):
    if floor == "B":
        return -0.30
    if floor == "F":
        return 6.50
    if cut == "A" and s0 >= 45.0:
        return M.PAV_TOP - 0.25
    if cut == "A" and s0 >= 27.3:
        return M.LIVING_TOP - 0.30
    return 3.20


def natural(cut, s):
    c = CUTS[cut]
    x, y = (s, c["at"]) if c["axis"] == "y" else (c["at"], s)
    return M.terrain_z(x, y) - M.ABS0


def earth_profile(cut):
    """Top of the earth after development, as (s, z) breakpoints."""
    c = CUTS[cut]
    if cut == "A":
        xw, xe = 0.45, 57.89
        segs = [(xw, 5.5, -3.55), (5.5, 27.5, -3.85), (27.5, 36.0, -0.30), (36.0, 39.3, -0.15), (39.3, 43.7, -1.85),
                (43.7, 45.5, -0.15), (45.5, 51.0, -0.25), (51.0, 52.0, -0.10)]
        tail = 52.5
    elif cut == "B":
        xw, xe = M.south_boundary_y(c["at"]), 37.0
        segs = [(xw, 12.2, -3.55), (12.2, 34.0, -3.85), (34.0, 36.2, -3.55)]
        tail = 36.2
    else:
        xw, xe = M.south_boundary_y(c["at"]), 37.0
        segs = [(12.2, 34.0, -3.85)]
        tail = 34.0
    pts = []
    s = c["lo"]
    first = segs[0][0]
    while s < first:
        pts.append((s, natural(cut, s))); s += 0.5
    if cut != "C":
        pts.append((first, natural(cut, first)))
    else:
        pts.append((first, natural(cut, first - 0.3)))
    for a, b, z in segs:
        pts += [(a, z), (b, z)]
    s = tail
    while s <= c["hi"] + 1e-6:
        z = natural(cut, min(s + (0.3 if s == tail else 0), c["hi"]))
        pts.append((s, max(z, -0.10) if cut == "A" else z)); s += 0.5
    return pts, (xw, xe)


def stair_flights(c, z0):
    """Cut flight (east) in solid, the return flight beyond it in outline. Used by section C."""
    s = M.STAIR
    y0, tr, rs, n = s["y0"], s["tread"], s["rise"], s["n"]
    yl, zl, yn = y0 + n * tr, z0 + (n + 1) * rs, M.STAIR_RECT[3]
    top = [(y0, z0)]
    for i in range(n + 1):
        y = y0 + i * tr
        top.append((y, z0 + (i + 1) * rs))
        if i < n:
            top.append((y + tr, z0 + (i + 1) * rs))
    top.append((yn, zl))
    under = [(yn, zl - 0.18), (yl + 0.12, zl - 0.18), (y0, z0 - 0.22)]
    c.poly(top + under, "SEC-CUT", fill="slab")
    c.line((y0 + 0.1, z0 + rs + 0.9), (yl, zl + 0.9), "SEC-VIEW", w=0.25)        # handrail
    c.line((yl, zl + 0.9), (yn - 0.05, zl + 0.9), "SEC-VIEW", w=0.25)
    prof = [(yl, zl)]
    for i in range(n + 1):
        y = yl - i * tr
        prof.append((y, zl + (i + 1) * rs))
        if i < n:
            prof.append((y - tr, zl + (i + 1) * rs))
    c.poly(prof, "SEC-VIEW", closed=False)
    c.line((yl + 0.12, zl - 0.18), (y0 + tr, z0 + 3.5 - 0.42), "SEC-VIEW")
    c.line((yl - 0.1, zl + rs + 0.9), (y0, z0 + 3.5 + 0.9), "SEC-VIEW", dash="3 2")


def section(cut, site=False):
    """site=True gives the simplified version used at 1:200 on the site sheet (no room names)."""
    c = Canvas()
    cc = CUTS[cut]
    zb = -5.4
    prof, (xw, xe) = earth_profile(cut)
    c.poly(prof + [(cc["hi"], zb), (cc["lo"], zb)], "EARTH", fill="earth")
    nat = []
    s = cc["lo"]
    while s <= cc["hi"] + 1e-6:
        nat.append((s, natural(cut, s))); s += 0.5
    c.poly(nat, "NATURAL", closed=False, dash="4 2")
    # room voids
    for fl in "BGF":
        z0 = M.LEVELS[fl]["z"]
        for a, b in spans(M.floor_outline(fl), cut):
            c.rect(a, z0, b, wall_top(fl, a + 0.4, cut), "SEC-VIEW", fill="room")
    if cut == "A":
        c.rect(27.5, 0.0, 36.0, M.LIVING_TOP - 0.3, "SEC-VIEW", fill="room")
        c.rect(39.5, -1.65, 43.5, -0.12, "WATER", fill="water")
        for x0, x1, z0, z1 in ((39.3, 43.7, -1.85, -1.65), (39.3, 39.5, -1.65, -0.05), (43.5, 43.7, -1.65, -0.05)):
            c.rect(x0, z0, x1, z1, "SEC-CUT", fill="slab")
        c.rect(36.0, -0.15, 39.3, -0.05, "SEC-CUT", fill="slab")
        c.rect(43.7, -0.15, 45.5, -0.05, "SEC-CUT", fill="slab")
    # cut walls with their openings
    for fl in "BGF":
        z0 = M.LEVELS[fl]["z"]
        for a, b in spans(M.wall_solid(fl), cut):
            c.rect(a, z0, b, wall_top(fl, a, cut), "SEC-CUT", fill="wall")
        for o in M.openings_of(fl):
            for a, b in spans(sbox(*o["rect"]), cut):
                k = o["kind"]
                sill = o.get("sill", 0.0) if k in ("win", "fixed") else 0.0
                head = o.get("head", {"door": 2.2, "door2": 2.3, "open": 2.6, "elev": 2.2, "garage": 2.6}.get(k, 2.7))
                head = min(head, wall_top(fl, a, cut) - z0)
                c.rect(a, z0 + sill, b, z0 + head, "SEC-VIEW", fill="white")
                if k in ("win", "fixed", "slide"):
                    m = (a + b) / 2
                    c.line((m, z0 + sill), (m, z0 + head), "GLASS", w=0.3)
    if cut == "C":
        stair_flights(c, -3.5)
        stair_flights(c, 0.0)
    for rects, top, t, void in SLABS:
        g = unary_union([sbox(*r) for r in rects])
        if void:
            g = g.difference(VOID)
        for a, b in spans(g, cut):
            c.rect(a, top - t, b, top, "SEC-CUT", fill="slab")
            if top in PARAPET:
                h = PARAPET[top]
                c.rect(a, top, a + 0.2, top + h, "SEC-CUT", fill="wall")
                c.rect(b - 0.2, top, b, top + h, "SEC-CUT", fill="wall")
    if cut in ("B", "C"):       # terrace over the garage: glass railing and planter; balcony railing
        c.line((12.25, 0.0), (12.25, 1.05), "GLASS", w=0.3)
        c.rect(12.4, 0.0, 13.0, 0.45, "SEC-VIEW", fill="green")
        c.line((20.29, 3.5), (20.29, 4.55), "GLASS", w=0.3)
    if cut == "B":
        c.line((36.2, -3.5), (36.2, natural(cut, 36.6)), "SEC-CUT", w=0.5)
    # room names
    if not site:
        for fl in "BGF":
            z0 = M.LEVELS[fl]["z"]
            for r in M.rooms_of(fl):
                for a, b in spans(M.room_poly(r), cut):
                    if b - a < 1.6 or r["name"] in ("מדרגות", "פיר מעלית"):
                        continue
                    top = wall_top(fl, a + 0.2, cut)
                    c.text(((a + b) / 2, z0 + min(1.5, (top - z0) / 2)), r["name"], "TEXT-S", h=0.2 if b - a > 3.2 else 0.15)
    k = 2.0 if site else 1.0
    # plot boundary, building lines
    bl = spans(Polygon(M.SITE["building_line"]), cut)
    for x in (xw, xe):
        c.line((x, -4.9), (x, 8.2), "PLOT", dash="10 3 2 3")
        c.text((x, 8.55), "גבול מגרש", "PLOT", h=0.2 * k)
    if bl:
        for x in (bl[0][0], bl[-1][1]):
            c.line((x, -4.6), (x, 7.6), "BLINE", dash="5 3")
            c.text((x, 7.9 - (0.35 if site else 0)), "קו בניין", "BLINE", h=0.18 * k)
    # level marks, to the right of the plot
    marks = [(-3.5, "קומת מרתף"), (0.0, "קומת קרקע"), (3.5, "קומה א׳"), (6.8, "גג עליון")]
    for z, name in marks:
        x = cc["hi"] - 1.7
        c.line((xe + 0.4, z), (x + 0.3, z), "LEVEL", dash="1 2")
        c.poly([(x - 0.18 * k, z + 0.24 * k), (x + 0.18 * k, z + 0.24 * k), (x, z)], "LEVEL", fill="dark")
        sign = "±" if abs(z) < 1e-9 else ("+" if z > 0 else "−")
        c.text((x + 1.3, z + 0.42 * k), f"{sign}{abs(z):.2f} (+{M.ABS0 + z:.2f})", "LEVEL", h=0.19 * k, bold=True, anchor="r")
        if not site:
            c.text((x + 1.3, z + 0.12), name, "LEVEL", h=0.16, anchor="r")
    if cut == "A":
        c.text((31.75, 5.74), "גג הסלון +5.50", "TEXT-S", h=0.16 * k)
        c.text((48.25, 3.52), "+3.30", "TEXT-S", h=0.15 * k)
        c.text((-0.6, natural(cut, -0.6) + 0.55 * k), "רחוב", "TEXT", h=0.22 * k, bold=True)
        c.text((-0.6, natural(cut, -0.6) + 0.2 * k), f"+{M.ABS0 + natural(cut, -0.6):.2f}", "TEXT-S", h=0.16 * k)
        c.text((41.5, -0.85), "בריכה", "TEXT-S", h=0.2 * k)
        c.text((54.6, natural(cut, 54.6) + 0.4 * k), "גינה", "TEXT-S", h=0.2 * k)
        if not site:
            c.text((2.0, -3.25), "רחבת המשרד", "TEXT-S", h=0.17)
            c.text((37.7, 0.25), "דק", "TEXT-S", h=0.17)
            c.text((16.5, -4.6), "אדמה", "TEXT-S", h=0.2)
        else:
            c.text((16.5, -1.75), "מרתף: חניון ומשרד", "TEXT-S", h=0.36)
            c.text((16.5, 1.75), "קומת קרקע", "TEXT-S", h=0.36)
            c.text((16.5, 5.1), "קומה א׳", "TEXT-S", h=0.36)
            c.text((31.75, 2.6), "סלון", "TEXT-S", h=0.36)
            c.text((48.25, 1.6), "ספא", "TEXT-S", h=0.36)
    else:
        c.text((xw - 1.6, natural(cut, xw - 1.6) + 0.45), "מגרש 85", "TEXT-S", h=0.2)
        c.text((38.4, natural(cut, 38.4) + 0.45), "מגרש 83", "TEXT-S", h=0.2)
        c.text((17.1, 0.75) if cut == "B" else (16.2, 0.75), "מרפסת גג", "TEXT-S", h=0.2)
        if cut == "B":
            c.text((8.3, -3.2), "רחבת כניסה לחניון", "TEXT-S", h=0.17)
            c.text((35.1, -4.15), "חצר אנגלית", "TEXT-S", h=0.14)
        else:
            c.text((31.3, -2.9), "מדרגות", "TEXT-S", h=0.17)
            c.text((31.3, 0.6), "מדרגות", "TEXT-S", h=0.17)
            c.text((23.6, 4.0), "מרפסת", "TEXT-S", h=0.15)
            c.text((9.8, natural(cut, 9.8) + 0.45), "גינה", "TEXT-S", h=0.2)
    if not site:
        # heights: floor to floor on one side of the building, clear heights inside, lengths under the building (all in cm)
        ref, hx, sg = (5.5, 4.5, -1) if cut == "A" else (34.0, 34.9, 1)
        lv = [-3.5, 0.0, 3.5, 6.8, 7.3]
        for a, b in zip(lv, lv[1:]):
            c.dim((ref, a), (ref, b), "V", hx, h=0.17)
        c.dim((ref, lv[0]), (ref, lv[-1]), "V", hx + sg * 0.8, h=0.17)
        clear = {"A": [(10.25, -3.5, -0.3), (10.25, 0.0, 3.2), (10.25, 3.5, 6.5), (35.2, 0.0, M.LIVING_TOP - 0.3), (50.4, 0.0, M.PAV_TOP - 0.25)],
                 "B": [(13.2, -3.5, -0.3), (22.9, -3.5, -0.3), (22.9, 0.0, 3.2), (22.9, 3.5, 6.5)],
                 "C": [(16.0, -3.5, -0.3), (22.9, -3.5, -0.3), (22.9, 0.0, 3.2), (22.9, 3.5, 6.5)]}[cut]
        for s_, z0, z1 in clear:
            c.dim((s_, z0), (s_, z1), "V", s_, h=0.15)
        sp = {"A": [5.5, 27.5, 36.0, 45.5, 51.0], "B": [12.2, 22.05, 34.0], "C": [12.2, 22.05, 34.0]}[cut]
        for a, b in zip(sp, sp[1:]):
            c.dim((a, -3.85), (b, -3.85), "H", -4.45, h=0.17)
        if cut != "A":
            c.dim((sp[0], -3.85), (sp[-1], -3.85), "H", -5.0, h=0.17)
    return c
