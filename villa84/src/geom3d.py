"""3D geometry of the villa and its site, derived from the plan model.

Writes model3d.json: prisms (vertical extrusions of plan polygons), markers (trees, cars), terrain meshes and room volumes.
Coordinates are design metres; z is relative to level 0.00 (= +91.00).
"""
import json
import math
import sys

import shapely
from shapely.geometry import LineString, Point, Polygon, box as sbox
from shapely.ops import unary_union

import draw as D
import model as M
import section as SEC

OUT = sys.argv[1]
prisms, markers = [], []


def convex(pts):
    s = 0
    n = len(pts)
    for i in range(n):
        (ax, ay), (bx, by), (cx, cy) = pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        cr = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cr) < 1e-12:
            continue
        if s == 0:
            s = 1 if cr > 0 else -1
        elif (cr > 0) != (s > 0):
            return False
    return True


def tri_cap(poly):
    out = []
    for t in shapely.constrained_delaunay_triangles(poly).geoms:
        cs = list(t.exterior.coords)[:3]
        out.append([[round(x, 4), round(y, 4)] for x, y in cs])
    return out


def prism(pts, z0, z1, mat, cat, floor="S", name="", holes=None):
    if z1 - z0 < 1e-4 or len(pts) < 3:
        return
    poly = Polygon(pts, holes or [])
    if not poly.is_valid or poly.area < 1e-6:
        poly = poly.buffer(0)
        if poly.is_empty or poly.geom_type != "Polygon":
            return
    if poly.exterior.is_ccw is False:
        poly = shapely.geometry.polygon.orient(poly, 1.0)
    ext = [[round(x, 4), round(y, 4)] for x, y in list(poly.exterior.coords)[:-1]]
    hs = [[[round(x, 4), round(y, 4)] for x, y in list(r.coords)[:-1]] for r in poly.interiors]
    d = dict(pts=ext, holes=hs, z0=round(z0, 4), z1=round(z1, 4), mat=mat, cat=cat, floor=floor, name=name)
    if hs or not convex(ext):
        d["cap"] = tri_cap(poly)
    prisms.append(d)


def prism_geom(g, z0, z1, mat, cat, floor="S", name=""):
    for p in M.polys(g):
        prism(list(p.exterior.coords)[:-1], z0, z1, mat, cat, floor, name, holes=[list(r.coords)[:-1] for r in p.interiors])


def box(x0, y0, x1, y1, z0, z1, mat, cat, floor="S", name=""):
    prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, mat, cat, floor, name)


def D_pieces(g):
    """LineString parts of a geometry."""
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    return [q for part in getattr(g, "geoms", []) for q in D_pieces(part)]


# ============================================================================ walls and openings
HEAD = {"door": 2.2, "door2": 2.3, "open": 2.6, "elev": 2.2, "garage": 2.6}


def wall_top(fl, x):
    if fl == "B":
        return -0.30
    if fl == "F":
        return 6.50
    if x >= 45.0:
        return M.PAV_TOP - 0.25
    if x >= 27.35:
        return M.LIVING_TOP - 0.30
    return 3.20


for fl in "BGF":
    zf = M.LEVELS[fl]["z"]
    wp = M.wall_poly(fl)
    zones = [(-100.0, 27.35), (27.35, 44.0), (44.0, 100.0)] if fl == "G" else [(-100.0, 100.0)]
    for xa, xb in zones:
        part = wp.intersection(sbox(xa, -100, xb, 100))
        for (x0, y0, x1, y1) in M.rect_cells(part):
            ext = x0 < 5.81 or y1 > 33.69 or (fl != "B" and y0 < 22.36) or (fl == "B" and y0 < 12.51) or x1 > 27.19
            box(x0, y0, x1, y1, zf, wall_top(fl, (x0 + x1) / 2), "wall_ext" if ext else "wall_int", "wall", fl)
    for o in M.openings_of(fl):
        x0, y0, x1, y1 = o["rect"]
        k = o["kind"]
        top = wall_top(fl, (x0 + x1) / 2 if o["axis"] == "H" else x0 + 0.01)
        if fl == "G" and o["axis"] == "V" and 27.1 < x0 < 27.4:
            top = 3.20
        sill = o.get("sill", 0.0) if k in ("win", "fixed") else 0.0
        head = min(o.get("head", HEAD.get(k, 2.7)), top - zf)
        if sill > 0:
            box(x0, y0, x1, y1, zf, zf + sill, "wall_ext", "wall", fl)
        if top - (zf + head) > 1e-3:
            box(x0, y0, x1, y1, zf + head, top, "wall_ext" if (y1 - y0 > 0.2 or x1 - x0 > 0.2) and (o["axis"] == "H" and (y1 - y0) > 0.2 or o["axis"] == "V" and (x1 - x0) > 0.2) else "wall_int", "wall", fl)
        horiz = o["axis"] == "H"
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        if k in ("win", "fixed", "slide"):
            fr = 0.05
            if horiz:
                box(x0, ym - 0.012, x1, ym + 0.012, zf + sill, zf + head, "glass", "glass", fl)
                for a, b in ((x0, x0 + fr), (x1 - fr, x1)):
                    box(a, ym - 0.04, b, ym + 0.04, zf + sill, zf + head, "frame", "frame", fl)
                box(x0, ym - 0.04, x1, ym + 0.04, zf + head - fr, zf + head, "frame", "frame", fl)
                box(x0, ym - 0.04, x1, ym + 0.04, zf + sill, zf + sill + fr, "frame", "frame", fl)
                n = max(1, round((x1 - x0) / 1.8)) if k == "slide" else (2 if x1 - x0 > 2.6 else 1)
                for i in range(1, n):
                    xx = x0 + (x1 - x0) * i / n
                    box(xx - fr / 2, ym - 0.04, xx + fr / 2, ym + 0.04, zf + sill, zf + head, "frame", "frame", fl)
            else:
                box(xm - 0.012, y0, xm + 0.012, y1, zf + sill, zf + head, "glass", "glass", fl)
                for a, b in ((y0, y0 + fr), (y1 - fr, y1)):
                    box(xm - 0.04, a, xm + 0.04, b, zf + sill, zf + head, "frame", "frame", fl)
                box(xm - 0.04, y0, xm + 0.04, y1, zf + head - fr, zf + head, "frame", "frame", fl)
                box(xm - 0.04, y0, xm + 0.04, y1, zf + sill, zf + sill + fr, "frame", "frame", fl)
                n = max(1, round((y1 - y0) / 1.8)) if k == "slide" else (2 if y1 - y0 > 2.6 else 1)
                for i in range(1, n):
                    yy = y0 + (y1 - y0) * i / n
                    box(xm - 0.04, yy - fr / 2, xm + 0.04, yy + fr / 2, zf + sill, zf + head, "frame", "frame", fl)
        elif k in ("door", "door2", "garage", "elev"):
            mat = {"garage": "garage_door", "elev": "steel"}.get(k, "door")
            if horiz:
                box(x0, ym - 0.025, x1, ym + 0.025, zf, zf + head, mat, "door", fl)
            else:
                box(xm - 0.025, y0, xm + 0.025, y1, zf, zf + head, mat, "door", fl)

# ============================================================================ slabs, floor finishes, roofs
FLOOR_OF_TOP = {-3.50: "B", 0.00: "G", 3.50: "F", 6.80: "R", 5.50: "R", 3.30: "R"}
for rects, top, t, void in SEC.SLABS:
    g = unary_union([sbox(*r) for r in rects])
    if void:
        g = g.difference(SEC.VOID)
    if abs(top) < 1e-9:
        g = g.difference(SEC.OPEN_G)
    prism_geom(g, top - t, top, "concrete", "slab", FLOOR_OF_TOP[top])
for q in M.SKYLIGHTS:
    box(q[0], q[1], q[2], q[3], -0.06, 0.0, "glass", "glass", "G", "terrace glass strip")

FLOOR_MAT = {"מקלט משותף": "floor_concrete", "פטיו": "garden", "חניון": "floor_epoxy", "חדר קולנוע": "floor_carpet", "מחסן": "floor_epoxy", "חדר מערכות": "floor_epoxy",
             "חדר מכונות בריכה": "floor_epoxy", "מרחב מוגן": "floor_stone", "ממ״ד": "floor_wood", "חדר כושר": "floor_rubber", "סאונה": "floor_wood_light",
             "פיר מעלית": "floor_stone"}


def floor_mat(r):
    n = r["name"]
    if n in FLOOR_MAT:
        return FLOOR_MAT[n]
    if any(w in n for w in ("מקלחת", "שירותי", "ג׳קוזי", "כביסה", "שירות", "רחצה", "מטבח")):
        return "floor_tile"
    if r["floor"] == "F" or n in ("סלון", "חדר משפחה וגיימינג"):
        return "floor_wood"
    if r["floor"] == "B":
        return "floor_concrete"
    return "floor_stone"


rooms = []
for r in M.ROOMS:
    zf = M.LEVELS[r["floor"]]["z"]
    poly = M.room_poly(r)
    if r["name"] != "מדרגות":
        prism_geom(poly, zf, zf + 0.02, floor_mat(r), "finish", r["floor"], r["name"])
    q = max(r["rects"], key=M.rect_area)
    top = wall_top(r["floor"], (q[0] + q[2]) / 2)
    for p in M.polys(poly):
        rooms.append(dict(floor=r["floor"], id=r["id"], name=r["name"], cat=r["cat"], group=r["group"], area=round(M.room_area(r), 2),
                          pts=[[round(x, 4), round(y, 4)] for x, y in list(p.exterior.coords)[:-1]], z0=zf, z1=top,
                          label=list(r["label"]) if r.get("label") else [(q[0] + q[2]) / 2, (q[1] + q[3]) / 2]))

for (rect, top, h, mat) in (((5.5, 22.05, 27.5, 34.0), 6.80, 0.5, "roof_gravel"), ((27.5, 22.05, 36.0, 34.0), 5.50, 0.4, "grass"),
                            ((45.5, 20.5, 51.0, 34.0), 3.30, 0.3, "grass")):
    g = sbox(*rect)
    inner = g.buffer(-0.2, join_style=2)
    prism_geom(g.difference(inner), top, top + h, "wall_ext", "parapet", "R")
    prism_geom(inner, top, top + 0.08, mat, "roof", "R")

# ============================================================================ stairs
s = M.STAIR
w = s["width"]
xw0, xw1, xe0, xe1 = s["x0"], s["x0"] + w, s["x1"] - w, s["x1"]
ys, n_, tr, rs = s["y0"], s["n"], s["tread"], s["rise"]
ylan, ly0 = ys - n_ * tr, s["landing"][1]
for z0, fl in ((-3.5, "B"), (0.0, "G")):
    zl = z0 + (n_ + 1) * rs
    for i in range(n_):                         # west flight: from the floor landing (north) down to the half landing
        zt = z0 + (i + 1) * rs
        box(xw0, ys - (i + 1) * tr - 0.02, xw1, ys - i * tr, max(z0, zt - 0.36), zt, "stair", "stair", fl)
    box(s["x0"], ly0, s["x1"], ylan, zl - 0.2, zl, "stair", "stair", fl)
    for i in range(n_):                         # east flight: back north to the next floor
        zt2 = zl + (i + 1) * rs
        box(xe0, ylan + i * tr, xe1, ylan + (i + 1) * tr + 0.02, zt2 - 0.36, zt2, "stair", "stair", fl)
    box(xw1 + 0.05, ylan, xe0 - 0.05, ys, z0, z0 + 3.5 + 1.0, "glass", "glass", fl, "stair balustrade")
box(xw0, ys - 0.02, xw1 + 0.05, ys + 0.02, 3.5, 4.55, "glass", "glass", "F", "stairwell guard")

e = M.EXT_STAIR
rise = (e["z1"] - e["z0"]) / e["risers"]
for i in range(e["n"]):
    box(e["x0"] + i * e["tread"], e["y0"], e["x0"] + (i + 1) * e["tread"], e["y1"], e["z0"] - 0.15, e["z0"] + (i + 1) * rise, "stone_step", "stair", "S", "entrance stair")
lx0, ly0, lx1, ly1 = M.EXT_LANDING
box(lx0, ly0, lx1, ly1, -2.2, 0.0, "stone_step", "stair", "S", "entrance stair landing")
box(e["x0"], e["y0"] - 0.03, lx1, e["y0"], -3.6, 1.0, "glass", "glass", "S", "entrance stair guard")
box(lx1, ly0, lx1 + 0.03, ly1, -0.2, 1.05, "glass", "glass", "S", "entrance stair guard")

# ============================================================================ terrace, balconies, pool, pavilion deck
tx0, ty0, tx1, ty1 = M.TERRACE
g0, g1 = M.TERRACE_GATE
planters = [sbox(tx0, ty0, g0 - 0.15, ty0 + 0.8), sbox(g1 + 0.15, ty0, tx1, ty0 + 0.8), sbox(tx0, ty0 + 0.8, tx0 + 0.8, ty1)]
pq = M.PATIO
patio_ring = sbox(pq[0] - 0.3, pq[1] - 0.3, pq[2], pq[3] + 0.3).difference(sbox(*pq))
planters.append(patio_ring)
terr = sbox(tx0, ty0, tx1, ty1).difference(unary_union(planters)).difference(SEC.OPEN_G)
prism_geom(terr, 0.0, 0.03, "deck_stone", "finish", "G", "roof terrace")
for p in planters:
    prism_geom(p.difference(p.buffer(-0.08, join_style=2)), 0.0, 0.5, "planter", "site", "G")
    prism_geom(p.buffer(-0.08, join_style=2), 0.0, 0.42, "soil", "site", "G")
    prism_geom(p.buffer(-0.14, join_style=2), 0.42, 0.95, "hedge", "site", "G")
box(tx0, ty0 - 0.02, g0 - 0.15, ty0 + 0.01, 0.0, 1.1, "glass", "glass", "G", "terrace guard")
box(g1 + 0.15, ty0 - 0.02, tx1, ty0 + 0.01, 0.0, 1.1, "glass", "glass", "G", "terrace guard")
box(tx0 - 0.02, ty0, tx0 + 0.01, ty1, 0.0, 1.1, "glass", "glass", "G", "terrace guard")
for a0, b0, a1, b1 in ((pq[0] - 0.32, pq[1] - 0.32, pq[2], pq[1] - 0.29), (pq[0] - 0.32, pq[3] + 0.29, pq[2], pq[3] + 0.32),
                       (pq[0] - 0.32, pq[1] - 0.32, pq[0] - 0.29, pq[3] + 0.32)):
    box(a0, b0, a1, b1, 0.0, 1.1, "glass", "glass", "G", "patio guard")
prism_geom(sbox(*pq), -3.5, -3.42, "garden", "site", "B", "patio garden")
markers.append(dict(kind="olive", p=[(pq[0] + pq[2]) / 2 + 0.6, (pq[1] + pq[3]) / 2], r=1.0, z=-3.45, floor="B"))
# pergola over the outdoor dining
pg = M.PERGOLA
for px in (pg[0] + 0.1, pg[2] - 0.1):
    for py in (pg[1] + 0.1, pg[3] - 0.1):
        box(px - 0.07, py - 0.07, px + 0.07, py + 0.07, 0.03, 2.65, "steel_dark", "site", "G", "pergola")
for py in (pg[1] + 0.1, pg[3] - 0.1):
    box(pg[0], py - 0.07, pg[2], py + 0.07, 2.65, 2.83, "steel_dark", "site", "G", "pergola")
nb = int((pg[2] - pg[0]) / 0.5)
for kx in range(nb + 1):
    xx = pg[0] + kx * (pg[2] - pg[0]) / nb
    box(xx - 0.03, pg[1], xx + 0.03, pg[3], 2.83, 2.97, "wood_dark", "site", "G", "pergola")
# bridge from the service room over the English court to the north path
bq = M.BRIDGE
box(bq[0], bq[1], bq[2], bq[3], -0.18, 0.0, "deck_stone", "site", "S", "bridge")
box(bq[0], bq[3] - 0.03, bq[2], bq[3], 0.0, 1.05, "glass", "glass", "S", "bridge guard")
# accessible ramp in the office court: runs as stepped slabs between the street gate and the court
rp = M.OFFICE_RAMP
zg, zc = rp["z0"] - M.ABS0, rp["z1"] - M.ABS0
box(*rp["landings"][0], zg - 0.3, zg, "paving", "site", "S", "ramp landing")
zm = (zg + zc) / 2
box(*rp["landings"][1], zm - 0.3, zm, "paving", "site", "S", "ramp landing")
for (x0, y0, x1, y1, d), (za, zb) in zip(rp["runs"], ((zg, zm), (zm, zc))):
    k = 8
    for i in range(k):
        ya, yb = (y1 - (i + 1) * (y1 - y0) / k, y1 - i * (y1 - y0) / k) if d < 0 else (y0 + i * (y1 - y0) / k, y0 + (i + 1) * (y1 - y0) / k)
        zt = za + (zb - za) * (i + 0.5) / k
        box(x0, ya, x1, yb, zt - 0.3, zt, "paving", "site", "S", "ramp")
for b in M.BALCONIES:
    box(b[0], b[1], b[2], b[3], 3.5, 3.53, "deck_stone", "finish", "F", "balcony")
    box(b[0], b[1] - 0.01, b[2], b[1] + 0.02, 3.5, 4.6, "glass", "glass", "F", "balcony guard")
    box(b[0] - 0.01, b[1], b[0] + 0.02, b[3], 3.5, 4.6, "glass", "glass", "F", "balcony guard")
    box(b[2] - 0.02, b[1], b[2] + 0.01, b[3], 3.5, 4.6, "glass", "glass", "F", "balcony guard")
px0, py0, px1, py1 = M.POOL
deck = sbox(*M.POOL_DECK)
pool = sbox(*M.POOL)
prism_geom(deck.difference(pool), -0.25, -0.05, "deck_stone", "site", "G", "pool deck")
prism_geom(deck.difference(pool.buffer(0.2, join_style=2)), -1.3, -0.25, "concrete", "site", "S")
prism_geom(pool.buffer(0.2, join_style=2).difference(pool), -1.85, -0.25, "pool_tile", "site", "G", "pool shell")
prism_geom(pool.buffer(0.2, join_style=2), -1.85, -1.65, "pool_tile", "site", "G", "pool floor")
prism_geom(pool, -1.65, -0.14, "water", "water", "G", "pool water")
box(27.5, 22.05, 36.0, 34.0, -1.3, -0.30, "concrete", "site", "S", "foundation")
box(45.5, 20.5, 51.0, 34.0, -1.3, -0.25, "concrete", "site", "S", "foundation")

# ============================================================================ furniture
for fl, solids in D.furniture_solids().items():
    for so in solids:
        if "marker" in so:
            markers.append(dict(kind=so["marker"], p=[round(so["p"][0], 3), round(so["p"][1], 3)], rot=so.get("rot", 0.0), z=so.get("z", 0.0),
                                color=so.get("color", ""), floor=fl))
        else:
            prism(so["pts"], so["z0"], so["z1"], so["mat"], "furn", fl, so.get("tag", ""))

# ============================================================================ site: designed ground, retaining walls, boundary wall
REG = sbox(-12.0, -9.0, 66.0, 46.0)
plot = Polygon(M.SITE["plot"])
bl = Polygon(M.SITE["building_line"])
bfoot, living, pav = sbox(5.5, 12.2, 27.5, 34.0), sbox(27.5, 22.05, 36.0, 34.0), sbox(45.5, 20.5, 51.0, 34.0)
extst = sbox(e["x0"], e["y0"], e["x1"], e["y1"]).union(sbox(*M.EXT_LANDING))
holes = unary_union([bfoot, living, pav, deck, extst])
drive = Polygon(M.DRIVEWAY).difference(holes)
ocourt = Polygon(M.OFFICE_COURT).difference(holes)
ecourt = sbox(*M.ENGLISH_COURT).difference(holes)
lawn = bl.intersection(sbox(27.5, -5.0, 60.0, 34.0)).difference(holes).buffer(-0.01)
nstrip = sbox(*M.NORTH_PATH)          # service path behind the living room and the pool deck, cut into the mound


def nat(x, y):
    return M.terrain_z(x, y) - M.ABS0


def z_drive(x, y):
    t = min(max((x - 0.8) / 4.0, 0.0), 1.0)
    return nat(0.8, min(max(y, 2.6), 7.4)) * (1 - t) + (-3.55) * t


def z_court(x, y):
    t = min(max((x - 0.6) / 2.4, 0.0), 1.0)
    return nat(0.6, min(max(y, 26.9), 28.6)) * (1 - t) + (-3.55) * t


road = sbox(-8.6, -9.0, -1.4, 46.0)
walk = sbox(-1.4, -9.0, 2.0, 46.0).difference(plot).difference(sbox(1.0, -9.0, 2.0, 0.0)).difference(sbox(0.0, 37.0, 2.0, 46.0))
ZONES = [  # (name, polygon, z function, material, flat)
    ("drive", drive, z_drive, "paving", True), ("ocourt", ocourt, z_court, "paving", True), ("ecourt", ecourt, lambda x, y: -3.50, "paving_light", True),
    ("lawn", lawn, lambda x, y: -0.10, "grass", True), ("npath", nstrip, lambda x, y: -0.10, "paving_light", True),
]
zone_union = unary_union([z[1] for z in ZONES])
garden = plot.difference(holes).difference(zone_union)
outside = REG.difference(plot)
SURF = ZONES + [("garden", garden, nat, "garden", False), ("road", road.intersection(outside), nat, "asphalt", False),
                ("walk", walk.intersection(outside), nat, "sidewalk", False),
                ("around", outside.difference(road).difference(walk), nat, "ground", False)]


def ground(x, y):
    """Finished ground level at a point; None inside a building or structure."""
    p = Point(x, y)
    if holes.contains(p):
        return None
    for _, poly, zf, _, _ in ZONES:
        if poly.contains(p):
            return zf(x, y)
    return nat(x, y)


terrain = []
STEP = 1.0
for name, poly, zf, mat, flat in SURF:
    verts, index, tris = [], {}, []

    def vid(x, y):
        k = (round(x, 3), round(y, 3))
        if k not in index:
            index[k] = len(verts)
            verts.append([k[0], k[1], round(zf(k[0], k[1]), 3)])
        return index[k]

    if poly.is_empty:
        continue
    x0, y0, x1, y1 = poly.bounds
    prep = shapely.prepared.prep(poly)
    xi = math.floor(x0 / STEP) * STEP
    while xi < x1:
        yi = math.floor(y0 / STEP) * STEP
        while yi < y1:
            cell = sbox(xi, yi, xi + STEP, yi + STEP)
            if prep.contains(cell):
                a, b, c, d = vid(xi, yi), vid(xi + STEP, yi), vid(xi + STEP, yi + STEP), vid(xi, yi + STEP)
                tris += [[a, b, c], [a, c, d]]
            elif prep.intersects(cell):
                piece = poly.intersection(cell)
                for pp in M.polys(piece):
                    if pp.area < 1e-6:
                        continue
                    for t in shapely.constrained_delaunay_triangles(pp).geoms:
                        cs = list(shapely.geometry.polygon.orient(t, 1.0).exterior.coords)[:3]
                        tris.append([vid(*c) for c in cs])
            yi += STEP
        xi += STEP
    terrain.append(dict(name=name, mat=mat, smooth=not flat, verts=verts, tris=tris))

# vertical sides of the terrain block, so the site reads as a model on a base
bx0, by0, bx1, by1 = REG.bounds
bv, bt = [], []
ZB = -8.0
for (ax, ay), (cx, cy) in (((bx0, by0), (bx1, by0)), ((bx1, by0), (bx1, by1)), ((bx1, by1), (bx0, by1)), ((bx0, by1), (bx0, by0))):
    n = int(round(math.hypot(cx - ax, cy - ay) / STEP))
    for i in range(n):
        p0 = (ax + (cx - ax) * i / n, ay + (cy - ay) * i / n)
        p1 = (ax + (cx - ax) * (i + 1) / n, ay + (cy - ay) * (i + 1) / n)
        k = len(bv)
        bv += [[p0[0], p0[1], ZB], [p1[0], p1[1], ZB], [p1[0], p1[1], round(nat(*p1), 3)], [p0[0], p0[1], round(nat(*p0), 3)]]
        bt += [[k, k + 1, k + 2], [k, k + 2, k + 3]]
terrain.append(dict(name="base", mat="earth_cut", smooth=False, verts=bv, tris=bt))

# retaining walls where the finished levels differ across a zone edge
def skirt(poly, zf, name):
    rings = []
    for p in M.polys(poly):
        rings += [p.exterior] + list(p.interiors)
    for ring in rings:
        L = ring.length
        n = max(1, int(L / 0.5))
        for i in range(n):
            a, b = ring.interpolate(L * i / n), ring.interpolate(L * (i + 1) / n)
            mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
            dx, dy = b.x - a.x, b.y - a.y
            ln = math.hypot(dx, dy)
            if ln < 1e-6:
                continue
            nx, ny = dy / ln, -dx / ln
            if poly.contains(Point(mx + nx * 0.06, my + ny * 0.06)):
                nx, ny = -nx, -ny
            zo = ground(mx + nx * 0.08, my + ny * 0.08)
            if zo is None or not REG.contains(Point(mx + nx * 0.08, my + ny * 0.08)):
                continue
            zi = zf(mx, my)
            other_zone = zone_union.contains(Point(mx + nx * 0.08, my + ny * 0.08))
            if abs(zo - zi) < 0.1 or (other_zone and zi > zo):
                continue
            w = 0.1
            prism([(a.x - nx * w, a.y - ny * w), (b.x - nx * w, b.y - ny * w), (b.x + nx * w, b.y + ny * w), (a.x + nx * w, a.y + ny * w)],
                  min(zo, zi) - 0.3, max(zo, zi) + 0.12, "retaining", "site", "S", "retaining wall " + name)


for name, poly, zf, mat, flat in ZONES:
    skirt(poly, zf, name)

# utility pillars and niches on the street front
for pl in M.PILLARS:
    x0, y0, x1, y1 = pl["rect"]
    ym, h, nm = (y0 + y1) / 2, pl["h"], "pillar " + pl["id"]
    zg = min(nat(M.front_x(ym) - 0.3, ym), ground((x0 + x1) / 2, ym) or 0.0, ground(x1 + 0.2, ym) or 0.0)
    if pl["id"] == "bins":
        t = 0.10
        box(x0, y0, x1, y1, zg - 0.25, zg + 0.03, "concrete", "site", "S", nm)
        for (a0, b0, a1, b1) in ((x0, y0, x0 + t, y1), (x1 - t, y0, x1, y1), (x0, y1 - t, x1, y1)):
            box(a0, b0, a1, b1, zg, zg + h, "wall_ext", "site", "S", nm)
        xm = (x0 + x1) / 2
        box(x0 + t, y0, xm - 0.01, y0 + 0.04, zg + 0.08, zg + h - 0.05, "util_door", "site", "S", nm)
        box(xm + 0.01, y0, x1 - t, y0 + 0.04, zg + 0.08, zg + h - 0.05, "util_door", "site", "S", nm)
        for i, col in enumerate(("bin_green", "bin_orange", "bin_blue")):
            bx = x0 + 0.21 + i * 0.80
            box(bx, y0 + 0.12, bx + 0.58, y0 + 1.0, zg + 0.03, zg + 1.11, col, "site", "S", nm)
    else:
        box(x0, y0, x1, y1, zg - 0.3, zg + h, "wall_ext", "site", "S", nm)
        if pl["face"] == "W":
            box(x0 - 0.025, y0 + 0.1, x0, y1 - 0.1, zg + 0.15, zg + h - 0.12, "util_door", "site", "S", nm)
        else:
            box(x1, y0 + 0.1, x1 + 0.025, y1 - 0.1, zg + 0.15, zg + h - 0.12, "util_door", "site", "S", nm)

# plot boundary wall, stepped with the ground, open at the two gates and in front of the street-facing pillars
gaps = [LineString(M.GATES["vehicle"]).buffer(0.6), LineString(M.GATES["pedestrian"]).buffer(0.6)]
gaps += [sbox(pl["rect"][0] - 0.6, pl["rect"][1] - 0.01, pl["rect"][2], pl["rect"][3] + 0.01) for pl in M.PILLARS if pl["face"] == "W"]
c = plot.centroid
for piece in D_pieces(plot.exterior.difference(unary_union(gaps))):
    L = piece.length
    n = max(1, int(math.ceil(L / 1.0)))
    for i in range(n):
        a, b = piece.interpolate(L * i / n), piece.interpolate(L * (i + 1) / n)
        mid = Point((a.x + b.x) / 2, (a.y + b.y) / 2)
        dx, dy = c.x - mid.x, c.y - mid.y
        d = math.hypot(dx, dy)
        zi = ground(mid.x + dx / d * 0.3, mid.y + dy / d * 0.3)
        zo = nat(mid.x - dx / d * 0.3, mid.y - dy / d * 0.3)
        if zi is None:
            zi = zo
        ux, uy = (b.x - a.x), (b.y - a.y)
        ln = math.hypot(ux, uy)
        if ln < 1e-6:
            continue
        nx, ny = -uy / ln * 0.1, ux / ln * 0.1
        prism([(a.x - nx, a.y - ny), (b.x - nx, b.y - ny), (b.x + nx, b.y + ny), (a.x + nx, a.y + ny)],
              min(zi, zo) - 0.3, max(zi, zo) + 1.1, "stone_wall", "site", "S", "boundary wall")

for kind, x, y, r in M.TREES:
    markers.append(dict(kind="olive", p=[x, y], r=r, z=round(ground(x, y) or 0.0, 3), floor="S"))
for x, y in M.CYPRESS:
    markers.append(dict(kind="cypress", p=[x, y], r=0.55, z=round(ground(x, y) or 0.0, 3), floor="S"))

json.dump(dict(prisms=prisms, markers=markers, terrain=terrain, rooms=rooms, abs0=M.ABS0,
               pillars=[dict(id=pl['id'], name=pl['name'], short=pl['short'], rect=list(pl['rect']), h=pl['h'], face=pl['face']) for pl in M.PILLARS], plot=M.SITE["plot"], building_line=M.SITE["building_line"],
               levels={k: dict(z=v["z"], name=v["name"]) for k, v in M.LEVELS.items()}), open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
cats = {}
for p in prisms:
    cats[p["cat"]] = cats.get(p["cat"], 0) + 1
print("prisms", len(prisms), cats)
print("markers", len(markers), "terrain", [(t["name"], len(t["verts"]), len(t["tris"])) for t in terrain], "rooms", len(rooms))
