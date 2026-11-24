"""Quick layout sketches: rooms as rectangles on the floor outline, with names, areas and a dead-space check.

Usage: python sketch.py layout.py out.png
layout.py defines OUTLINE (list of rects), ROOMS (list of (name, [rects], kind)) and optional MARKS (list of (label, rect)).
"""
import importlib.util
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from shapely.geometry import box
from shapely.ops import unary_union

spec = importlib.util.spec_from_file_location("lay", sys.argv[1])
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
COL = {"office": "#cfe0f5", "family": "#f6d9b8", "service": "#e3e3e3", "park": "#d8d8d8", "core": "#b9a6d6", "circ": "#fff3b0",
       "live": "#f3e3a3", "bed": "#cfe8c8", "wet": "#bfe6ee"}

fig, ax = plt.subplots(figsize=(13, 12))
outline = unary_union([box(*r) for r in L.OUTLINE])
for p in getattr(outline, "geoms", [outline]):
    ax.fill(*p.exterior.xy, color="#444")
rooms_u = []
tot = {}
for name, rects, kind in L.ROOMS:
    g = unary_union([box(*r) for r in rects])
    rooms_u.append(g)
    tot[kind] = tot.get(kind, 0) + g.area
    for r in rects:
        ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], facecolor=COL.get(kind, "#fff"), edgecolor="none"))
    c = max(rects, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    ax.text((c[0] + c[2]) / 2, (c[1] + c[3]) / 2, f"{name[::-1]}\n{g.area:.1f}", ha="center", va="center", fontsize=8)
for lab, r in getattr(L, "MARKS", []):
    ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fill=False, edgecolor="red", lw=1.2, ls="--"))
    ax.text(r[0], r[3], lab[::-1], color="red", fontsize=7, va="bottom")
walls = outline.difference(unary_union(rooms_u))
fat = walls.buffer(-0.18, join_style=2).buffer(0.18, join_style=2)          # anything thicker than a 36 cm wall
dead = [p for p in getattr(fat, "geoms", [fat]) if p.area > 0.05]
for p in dead:
    ax.fill(*p.exterior.xy, color="red", alpha=0.6)
ax.set_aspect("equal")
ax.set_xlim(L.VIEW[0], L.VIEW[2])
ax.set_ylim(L.VIEW[1], L.VIEW[3])
ax.grid(True, lw=0.3)
summary = "  ".join(f"{k}:{v:.0f}" for k, v in tot.items())
net = sum(tot.values())
ax.set_title(f"{L.TITLE}   net {net:.0f}  gross {outline.area:.0f}  walls {outline.area - net:.0f}\n{summary}", fontsize=9)
fig.savefig(sys.argv[2], dpi=90, bbox_inches="tight")
print("dead pockets:", [(round(p.area, 2), [round(v, 2) for v in p.bounds]) for p in dead])
print(summary, "net", round(net, 1))
