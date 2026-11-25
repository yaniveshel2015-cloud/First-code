"""Export the villa model as a data file for building a native, editable Revit model (Dynamo script villa84_build.py).

All lengths in metres, in design coordinates (the same as the PDF sheets and the DXF files); z relative to +-0.00 = +91.00.
Walls are derived as centre lines with a thickness from the gaps between rooms and the floor outline.

  python revit_export.py out/revit/villa84-revit-data.json
"""
import json
import math
import sys

from shapely.geometry import Point, Polygon, box as sbox
from shapely.ops import unary_union

import draw as D
import model as M
import section as SEC

OUT = sys.argv[1]
TOL = 0.02
MAXT = 0.33                     # thickest wall band (exterior 0.30)

WALL_TOP = {"B": lambda x: -0.30, "F": lambda x: 6.50,
            "G": lambda x: M.PAV_TOP - 0.25 if x >= 45.0 else (M.LIVING_TOP - 0.30 if x >= 27.35 else 3.20)}


# ------------------------------------------------------------------ walls from the plan
def wall_bands(fl):
    """Wall pieces found by probing outward from every room edge: (axis, centre, a, b, thickness, exterior).
    axis 'H' = wall running along X (centre is its Y), 'V' = along Y (centre is its X)."""
    rooms = [(r["id"], q) for r in M.rooms_of(fl) for q in r["rects"]] + [("hole", h) for h in M.OUTLINE_HOLES.get(fl, [])]
    room_geoms = [sbox(*q) for rid, q in rooms if rid != "hole"]
    allrooms = unary_union(room_geoms)
    outline = M.floor_outline(fl)
    xs = sorted({round(v, 4) for _, q in rooms for v in (q[0], q[2])} | {round(c[0], 4) for p in M.polys(outline) for c in p.exterior.coords}
                | {round(c[0], 4) for p in M.polys(outline) for h in p.interiors for c in h.coords})
    ys = sorted({round(v, 4) for _, q in rooms for v in (q[1], q[3])} | {round(c[1], 4) for p in M.polys(outline) for c in p.exterior.coords}
                | {round(c[1], 4) for p in M.polys(outline) for h in p.interiors for c in h.coords})
    out = []

    def probe(px, py, dx, dy):
        """Distance from an edge point to the next room or to the outside, and which one it was."""
        step = 0.005
        d = step
        while d <= MAXT + 1e-9:
            p = Point(px + dx * d, py + dy * d)
            if not outline.buffer(1e-6).contains(p):
                return d - step / 2, True
            if allrooms.contains(p):
                return d - step / 2, False
            d += step
        return None, None

    for rid, q in rooms:
        x0, y0, x1, y1 = q
        # top (+y) and bottom (-y) edges: horizontal walls
        for yy, dy in ((y1, 1), (y0, -1)):
            cuts = [x0] + [x for x in xs if x0 + 1e-6 < x < x1 - 1e-6] + [x1]
            for a, b in zip(cuts, cuts[1:]):
                xm = (a + b) / 2
                d, ext = probe(xm, yy, 0, dy)
                if d is None or d < 0.05:
                    continue
                d = round(d / 0.05) * 0.05
                if not ext and dy < 0:
                    continue                          # interior bands are taken once, from the lower room
                out.append(("H", round(yy + dy * d / 2, 4), a, b, round(d, 3), ext))
        for xx, dx in ((x1, 1), (x0, -1)):
            cuts = [y0] + [y for y in ys if y0 + 1e-6 < y < y1 - 1e-6] + [y1]
            for a, b in zip(cuts, cuts[1:]):
                ym = (a + b) / 2
                d, ext = probe(xx, ym, dx, 0)
                if d is None or d < 0.05:
                    continue
                d = round(d / 0.05) * 0.05
                if not ext and dx < 0:
                    continue
                out.append(("V", round(xx + dx * d / 2, 4), a, b, round(d, 3), ext))
    return out


def merge(bands):
    """Join collinear pieces of the same thickness, also across the junctions of crossing walls."""
    groups = {}
    for ax, c, a, b, t, ext in bands:
        key = (ax, round(c, 3), round(t, 2))
        groups.setdefault(key, []).append([a, b, ext])
    segs = []
    for (ax, c, t), items in groups.items():
        items.sort()
        cur = None
        for a, b, ext in items:
            if cur and a - cur[1] <= MAXT + 0.01:
                cur[1] = max(cur[1], b)
                cur[2] = cur[2] or ext
            else:
                if cur:
                    segs.append(dict(axis=ax, c=c, a=cur[0], b=cur[1], t=t, ext=cur[2]))
                cur = [a, b, ext]
        if cur:
            segs.append(dict(axis=ax, c=c, a=cur[0], b=cur[1], t=t, ext=cur[2]))
    return segs


def extend_ends(segs):
    """Run each wall end to the centre line of the wall it meets, so Revit joins them (L and T joins)."""
    for s in segs:
        for end in ("a", "b"):
            v = s[end]
            best = None
            for p in segs:
                if p["axis"] == s["axis"]:
                    continue
                if not (p["a"] - s["t"] / 2 - TOL <= s["c"] <= p["b"] + s["t"] / 2 + TOL):
                    continue
                gap = abs(p["c"] - v)
                if gap <= p["t"] / 2 + s["t"] / 2 + TOL and (best is None or gap < abs(best - v)):
                    best = p["c"]
            if best is not None:
                s[end] = best
        if s["a"] > s["b"]:
            s["a"], s["b"] = s["b"], s["a"]
    return segs


def host_of(o, segs):
    x0, y0, x1, y1 = o["rect"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for i, s in enumerate(segs):
        if o["axis"] == "H" and s["axis"] == "H" and abs(s["c"] - cy) <= s["t"] / 2 + TOL and s["a"] - TOL <= cx <= s["b"] + TOL:
            return i
        if o["axis"] == "V" and s["axis"] == "V" and abs(s["c"] - cx) <= s["t"] / 2 + TOL and s["a"] - TOL <= cy <= s["b"] + TOL:
            return i
    return None


HEAD = {"door": 2.2, "door2": 2.3, "open": 2.6, "elev": 2.2, "garage": 2.6, "win": 2.6, "fixed": 2.7, "slide": 2.7}


def floor_walls(fl):
    z = M.LEVELS[fl]["z"]
    segs = extend_ends(merge(wall_bands(fl)))
    ops = []
    for o in M.openings_of(fl):
        i = host_of(o, segs)
        x0, y0, x1, y1 = o["rect"]
        along = (x0, x1) if o["axis"] == "H" else (y0, y1)
        k = o["kind"]
        sill = o.get("sill", 0.0) if k in ("win", "fixed") else 0.0
        ops.append(dict(wall=i, kind=k, a=along[0], b=along[1], width=round(along[1] - along[0], 3), sill=sill,
                        head=o.get("head", HEAD.get(k, 2.6)), hinge=o.get("hinge", "a"), swing=o.get("swing", 1),
                        glass=bool(o.get("glass")), blast=bool(o.get("blast"))))
    # an 'open' opening without a header: no wall over its span, a room separation line instead
    cuts = {}
    seps = []
    for op in ops:
        if op["kind"] == "open" and op["wall"] is not None and op["head"] == HEAD["open"]:
            cuts.setdefault(op["wall"], []).append((op["a"], op["b"]))
            sg = segs[op["wall"]]
            seps.append([[op["a"], sg["c"]], [op["b"], sg["c"]]] if sg["axis"] == "H" else [[sg["c"], op["a"]], [sg["c"], op["b"]]])
    pieces = []                       # (seg index, a, b)
    for i, sg in enumerate(segs):
        iv = [(sg["a"], sg["b"])]
        for a, b in sorted(cuts.get(i, [])):
            nxt = []
            for p, q in iv:
                if b <= p or a >= q:
                    nxt.append((p, q))
                    continue
                if a > p:
                    nxt.append((p, a))
                if b < q:
                    nxt.append((b, q))
            iv = nxt
        for p, q in iv:
            if q - p >= 0.1:
                pieces.append((i, p, q))
    walls = []
    for i, p, q in pieces:
        sg = segs[i]
        mid = (p + q) / 2
        xm = mid if sg["axis"] == "H" else sg["c"]
        top = WALL_TOP[fl](xm)
        line = [[p, sg["c"]], [q, sg["c"]]] if sg["axis"] == "H" else [[sg["c"], p], [sg["c"], q]]
        walls.append(dict(id=f"{fl}-W{len(walls) + 1:03d}", line=line, thickness=sg["t"], exterior=sg["ext"], height=round(top - z, 3),
                          seg=i, a=p, b=q))
    openings = []
    for op in ops:
        if op["wall"] is None or (op["kind"] == "open" and op["head"] == HEAD["open"]):
            continue
        cm = (op["a"] + op["b"]) / 2
        host = next((w for w in walls if w["seg"] == op["wall"] and w["a"] - TOL <= cm <= w["b"] + TOL), None)
        if host is None:
            continue
        op = dict(op)
        op["wall"] = host["id"]
        openings.append(op)
    for w in walls:
        del w["seg"], w["a"], w["b"]
    return walls, openings, seps


# ------------------------------------------------------------------ floors, roofs, rooms, stairs
def loops(g):
    out = []
    for p in M.polys(g):
        out.append([[round(x, 4), round(y, 4)] for x, y in list(p.exterior.coords)[:-1]]
                   + [])
        for h in p.interiors:
            out.append([[round(x, 4), round(y, 4)] for x, y in list(h.coords)[:-1]])
    return out


def slabs():
    void = SEC.VOID
    out = []
    for rects, top, t, has_void in SEC.SLABS:
        g = unary_union([sbox(*r) for r in rects])
        if has_void:
            g = g.difference(void)
        if abs(top) < 1e-9:
            g = g.difference(SEC.OPEN_G)
        if abs(top + 3.5) < 1e-9:
            g = g.difference(sbox(*M.PATIO))
        level = {-3.50: "B", 0.0: "G", 3.50: "F", 6.80: "R", 5.50: "RL", 3.30: "RP"}[round(top, 2)]
        kind = "roof" if level.startswith("R") else "floor"
        for p in M.polys(g):
            out.append(dict(level=level, kind=kind, thickness=t, loops=loops(p),
                            name={"B": "רצפת מרתף", "G": "תקרת מרתף ורצפת קרקע", "F": "רצפת קומה א׳", "R": "גג עליון", "RL": "גג הסלון",
                                  "RP": "גג ביתן הספא"}[level]))
    out.append(dict(level="B", kind="floor", thickness=0.10, loops=loops(sbox(*M.PATIO)), name="פטיו"))
    return out


def rooms():
    out = []
    for r in M.ROOMS:
        fl = r["floor"]
        x, y = D._label_pos(r)
        poly = M.room_poly(r)
        if not poly.contains(Point(x, y)):
            p = poly.representative_point()
            x, y = p.x, p.y
        q = max(r["rects"], key=M.rect_area)
        top = WALL_TOP[fl]((q[0] + q[2]) / 2)
        out.append(dict(level=fl, number=r["id"], name=r["name"], point=[round(x, 3), round(y, 3)], area=round(M.room_area(r), 2),
                        department=r["group"], comments=r["note"], category=r["cat"], height=round(top - M.LEVELS[fl]["z"], 2)))
    return out


def stairs():
    s = M.STAIR
    w = s["width"]
    xw, xe = s["x0"] + w / 2, s["x1"] - w / 2
    ys, n, tr = s["y0"], s["n"], s["tread"]
    ylan = ys - n * tr
    out = []
    for base, top in (("B", "G"), ("G", "F")):
        out.append(dict(base=base, top=top, width=w, risers=s["risers"], riser=s["rise"], tread=tr,
                        run1=[[xw, ys], [xw, ylan]], run2=[[xe, ylan], [xe, ys]], landing=list(s["landing"]),
                        outline=list(M.STAIR_RECT)))
    return out


# ------------------------------------------------------------------ dimensions, sections, site, sheets
def chains():
    out = []
    for fl in "BGF":
        for axis, at, lo, hi in D.CHAINS[fl]:
            out.append(dict(level=fl, axis=axis, at=at, lo=lo, hi=hi))
    return out


def sections():
    out = []
    names = {"A": "חתך א–א", "B": "חתך ב–ב", "C": "חתך ג–ג"}
    for k, c in SEC.CUTS.items():
        if c["axis"] == "y":
            line = [[c["lo"], c["at"]], [c["hi"], c["at"]]]
        else:
            line = [[c["at"], c["lo"]], [c["at"], c["hi"]]]
        out.append(dict(name=names[k], line=line, zmin=-5.4, zmax=9.2, look=[0, 1] if c["axis"] == "y" else [-1, 0]))
    return out


def site():
    S_ = M.SITE
    g = S_["grid"]
    pts = []
    for iy in range(0, g["ny"], 4):                     # every 2 m
        for ix in range(0, g["nx"], 4):
            x, y = g["x0"] + ix * g["step"], g["y0"] + iy * g["step"]
            if -14.0 <= x <= 68.0 and -10.0 <= y <= 48.0:
                pts.append([round(x, 3), round(y, 3), round(g["z"][iy][ix] - M.ABS0, 3)])
    for x, y, z in S_["spots"]:
        if -14.0 <= x <= 68.0 and -10.0 <= y <= 48.0:
            pts.append([round(x, 3), round(y, 3), round(z - M.ABS0, 3)])
    ox, oy = S_["origin_world"]
    xh, yh = S_["xh"], S_["yh"]
    # survey (shared) coordinates of the design origin (0, 0): world = O + x*xh + (y - 37)*yh
    w0 = [ox + (0 - S_["y_offset"]) * yh[0], oy + (0 - S_["y_offset"]) * yh[1]]
    angle = math.degrees(math.atan2(xh[1], xh[0]))      # direction of the design X axis in the survey grid
    check = [[56.0, 37.0], [ox + 56.0 * xh[0], oy + 56.0 * xh[1]]]     # corner 219G: design point -> survey point
    return dict(topo_points=pts, plot=S_["plot"], plot_names=S_["plot_names"], building_line=S_["building_line"],
                survey_origin=w0, x_axis_angle_deg=angle, elevation_zero=M.ABS0, check_point=check,
                north_vec=S_["north_vec"], area_registered=S_["area_registered"])


def main():
    data = dict(
        units="m", project="וילה ומשרד אדריכלים · מגרש 84, גוש 5508, ראש העין",
        levels=[dict(key=k, name=f'{L["name"]} {D.lvl(L["z"])}', elevation=L["z"], plan=True) for k, L in M.LEVELS.items()]
        + [dict(key="R", name=f"גג עליון {D.lvl(6.80)}", elevation=6.80, plan=False),
           dict(key="RL", name=f"גג הסלון {D.lvl(M.LIVING_TOP)}", elevation=M.LIVING_TOP, plan=False),
           dict(key="RP", name=f"גג ביתן הספא {D.lvl(M.PAV_TOP)}", elevation=M.PAV_TOP, plan=False)],
        wall_types=dict(exterior=0.30, interior=0.15),
        walls=[], openings=[], separations=[], floors=slabs(), rooms=rooms(), stairs=stairs(),
        shaft=dict(outline=list(M.ELEV_RECT), base="B", top="F"), chains=chains(), sections=sections(), site=site(),
        sheets=[dict(number="A-001", name="תוכנית מגרש", views=["site"]), dict(number="A-101", name="קומת מרתף", views=["B"]),
                dict(number="A-102", name="קומת קרקע", views=["G"]), dict(number="A-103", name="קומה א׳", views=["F"]),
                dict(number="A-201", name="חתכים", views=["section:חתך א–א", "section:חתך ב–ב", "section:חתך ג–ג"]),
                dict(number="A-301", name="טבלת חדרים ושטחים", views=["schedule:rooms"])])
    for fl in "BGF":
        walls, openings, seps = floor_walls(fl)
        for w in walls:
            w["level"] = fl
        for o in openings:
            o["level"] = fl
        data["walls"] += walls
        data["openings"] += openings
        data["separations"] += [dict(level=fl, line=s) for s in seps]
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_open_unhosted = sum(1 for o in data["openings"] if o["wall"] is None)
    print("levels", len(data["levels"]), "walls", len(data["walls"]), "openings", len(data["openings"]), "unhosted", n_open_unhosted,
          "separations", len(data["separations"]), "floors", len(data["floors"]), "rooms", len(data["rooms"]),
          "topo points", len(data["site"]["topo_points"]), "chains", len(data["chains"]))


if __name__ == "__main__":
    main()
