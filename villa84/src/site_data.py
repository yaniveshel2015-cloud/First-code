"""Plot 84 site data from the surveyor's DWG -> site.json (design coordinates in metres).

Design frame: origin at corner 186G placed at (0, 37); X runs from 186G toward 219G (the north-east boundary, Y = 37).
world = origin_world + X * xh + (Y - 37) * yh.
Usage: python -I site_data.py survey.dwg site.json
"""
import json
import math
import re
import sys

import ezdwg
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from shapely.geometry import LineString, Polygon

SRC, OUT = sys.argv[1], sys.argv[2]
CORNERS = ["186G", "187G", "188G", "189G", "220G", "219G"]
SETBACKS = [5.0, 5.0, 5.0, 3.0, 5.0, 3.0]          # front x3, south-west side, rear, north-east side (assumed, verify with the plan)
AREA_REGISTERED = 1556.0
Y_OFF = 37.0
GRID = dict(x0=-16.0, y0=-14.0, step=0.5, x1=72.0, y1=52.0)
REGION = (-30.0, -25.0, 90.0, 65.0)                  # what is kept of the survey underlay

ents = list(ezdwg.read(SRC).modelspace().iter_entities())
corner_ins = [e for e in ents if e.dxftype == "INSERT" and e.dxf.get("name") == "142_0_DX"]
names = {str(a.dxf.get("text")): a.dxf.get("insert") for a in ents
         if a.dxftype == "ATTRIB" and a.dxf.get("tag") == "RGMPOINTNAME"}
world = {}
for n in CORNERS:
    ap = names[n]
    world[n] = min((e.dxf["insert"][:2] for e in corner_ins), key=lambda p: math.dist(p, ap[:2]))
O, Q = world["186G"], world["219G"]
L = math.dist(O, Q)
xh = ((Q[0] - O[0]) / L, (Q[1] - O[1]) / L)
yh = (-xh[1], xh[0])


def to_design(p):
    dx, dy = p[0] - O[0], p[1] - O[1]
    return (dx * xh[0] + dy * xh[1], Y_OFF + dx * yh[0] + dy * yh[1])


def inside_region(p):
    return REGION[0] <= p[0] <= REGION[2] and REGION[1] <= p[1] <= REGION[3]


plot = [tuple(round(v, 3) for v in to_design(world[n])) for n in CORNERS]
poly = Polygon(plot)
edges = []
for i, n in enumerate(CORNERS):
    a, b = plot[i], plot[(i + 1) % len(plot)]
    edges.append(dict(name=f"{n}-{CORNERS[(i + 1) % len(CORNERS)]}", len=round(math.dist(a, b), 2), setback=SETBACKS[i]))

# building line: each edge moved inward by its setback, consecutive offset lines intersected
sign = 1 if poly.exterior.is_ccw else -1
lines = []
for i in range(len(plot)):
    (ax, ay), (bx, by) = plot[i], plot[(i + 1) % len(plot)]
    ln = math.hypot(bx - ax, by - ay)
    nx, ny = -(by - ay) / ln * sign, (bx - ax) / ln * sign          # inward normal
    s = SETBACKS[i]
    lines.append(((ax + nx * s, ay + ny * s), (bx + nx * s, by + ny * s)))


def intersect(l1, l2):
    (x1, y1), (x2, y2) = l1
    (x3, y3), (x4, y4) = l2
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


bl = [intersect(lines[i - 1], lines[i]) for i in range(len(lines))]
bl_poly = Polygon(bl)
building_line = [[round(x, 3), round(y, 3)] for x, y in bl]

# survey heights: points with z
spots = []
for e in ents:
    if e.dxftype == "POINT":
        p = e.dxf.get("location")
        if p is not None and len(p) > 2 and abs(p[2]) > 1e-6:
            x, y = to_design(p)
            spots.append([round(x, 3), round(y, 3), round(p[2], 3)])
pts = np.array([[s[0], s[1]] for s in spots])
zv = np.array([s[2] for s in spots])
gx = np.arange(GRID["x0"], GRID["x1"] + 1e-9, GRID["step"])
gy = np.arange(GRID["y0"], GRID["y1"] + 1e-9, GRID["step"])
GX, GY = np.meshgrid(gx, gy)
Z = griddata(pts, zv, (GX, GY), method="linear")
Zn = griddata(pts, zv, (GX, GY), method="nearest")
Z = np.where(np.isnan(Z), Zn, Z)
Z = gaussian_filter(Z, sigma=2.0, mode="nearest")
grid = dict(x0=GRID["x0"], y0=GRID["y0"], step=GRID["step"], nx=len(gx), ny=len(gy), z=[[round(float(v), 3) for v in row] for row in Z])

# contours every 0.5 m
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

levels = np.arange(math.floor(Z.min() * 2) / 2, Z.max() + 0.5, 0.5)
cs = plt.contour(GX, GY, Z, levels=levels)
contours = []
for z, segs in zip(cs.levels, cs.allsegs):
    for seg in segs:
        if len(seg) >= 4:
            contours.append(dict(z=round(float(z), 2), pts=[[round(float(x), 3), round(float(y), 3)] for x, y in seg[::2]]))

# survey underlay: polylines and lines, by colour
underlay = []
for e in ents:
    if e.dxftype == "LWPOLYLINE":
        p = [to_design(q) for q in e.dxf.get("points") or []]
        if e.dxf.get("closed") and p:
            p.append(p[0])
    elif e.dxftype == "LINE":
        p = [to_design(e.dxf["start"]), to_design(e.dxf["end"])]
    else:
        continue
    if len(p) >= 2 and any(inside_region(q) for q in p):
        underlay.append(dict(color=e.dxf.get("resolved_color_index"), pts=[[round(x, 3), round(y, 3)] for x, y in p]))

# lot numbers: the large digit texts (point numbers and grid ticks are small)
lots = []
for e in ents:
    if e.dxftype == "TEXT":
        s = str(e.dxf.get("text", "")).strip()
        if re.fullmatch(r"\d{2,3}", s) and (e.dxf.get("height") or 0) >= 1.0:
            x, y = to_design(e.dxf["insert"])
            if inside_region((x, y)):
                lots.append([s, round(x, 2), round(y, 2)])

north = (xh[1], yh[1])          # world +Y expressed in design components
site = dict(
    origin_world=[round(O[0], 3), round(O[1], 3)], xh=list(xh), yh=list(yh), y_offset=Y_OFF,
    x_axis_azimuth=math.degrees(math.atan2(xh[0], xh[1])) % 360, north_angle_deg=(360 - math.degrees(math.atan2(-north[0], north[1]))) % 360,
    plot=[list(p) for p in plot], plot_names=CORNERS, edges=edges,
    area_measured=round(poly.area, 1), area_registered=AREA_REGISTERED,
    building_line=building_line, buildable_area=round(bl_poly.area, 1),
    grid=grid, contours=contours, underlay=underlay, spots=spots, lots=lots, north_vec=list(north),
)
json.dump(site, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print("plot", plot)
print("edges", [(e["name"], e["len"]) for e in edges])
print("area", site["area_measured"], "building line", building_line, "buildable", site["buildable_area"])
print("spots", len(spots), "contours", len(contours), "underlay", len(underlay), "lots", lots)
print("north_vec", site["north_vec"], "azimuth", round(site["x_axis_azimuth"], 3))
