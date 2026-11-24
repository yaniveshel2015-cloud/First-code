"""Blender scene of the villa on plot 84, built from model3d.json (the same data as the drawings).

  python scene84.py --view aerial_front --out a.png [--res 1600x1000] [--samples 96] [--fast]
  python scene84.py --glb villa84.glb          (plain-colour model for viewers, no render)
Views: aerial_front, aerial_back, aerial_side, street, garden, terrace, top, cut_B, cut_G, cut_F
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SP, "render"))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import vlib as V  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--data", default=os.path.join(HERE, "out", "model3d.json"))
ap.add_argument("--view", default="aerial_front")
ap.add_argument("--res", default="800x500")
ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--exposure", type=float, default=None)
ap.add_argument("--fast", action="store_true")
ap.add_argument("--out", default=None)
ap.add_argument("--glb", default=None)
ap.add_argument("--blend", default=None)
args = ap.parse_args()

SIMPLE = bool(args.glb)
FAST = args.fast or SIMPLE
VIEW = args.view
CUT = VIEW[-1] if VIEW.startswith("cut_") else None

V.reset()
scene = V.scene
DATA = json.load(open(args.data, encoding="utf-8"))

# ============================================================================ materials
P = V.principled
SPEC = {  # name: (colour, roughness, metallic) for the plain model; the render materials below refine some of them
    "wall_ext": ((0.90, 0.89, 0.86), 0.75, 0), "wall_int": ((0.93, 0.93, 0.92), 0.8, 0), "concrete": ((0.60, 0.60, 0.58), 0.8, 0),
    "frame": ((0.04, 0.04, 0.045), 0.35, 0.8), "door": ((0.30, 0.19, 0.11), 0.45, 0), "garage_door": ((0.09, 0.09, 0.095), 0.4, 0.6),
    "steel": ((0.62, 0.62, 0.64), 0.3, 1.0), "floor_epoxy": ((0.42, 0.43, 0.44), 0.2, 0), "floor_carpet": ((0.20, 0.07, 0.08), 1.0, 0),
    "floor_concrete": ((0.56, 0.56, 0.55), 0.35, 0), "floor_rubber": ((0.10, 0.10, 0.11), 0.8, 0), "floor_stone": ((0.80, 0.78, 0.73), 0.2, 0),
    "floor_tile": ((0.84, 0.85, 0.85), 0.25, 0), "floor_wood": ((0.52, 0.36, 0.22), 0.35, 0), "floor_wood_light": ((0.70, 0.55, 0.36), 0.5, 0),
    "roof_gravel": ((0.78, 0.76, 0.72), 0.95, 0), "grass": ((0.12, 0.24, 0.06), 0.95, 0), "garden": ((0.20, 0.27, 0.10), 0.95, 0),
    "ground": ((0.42, 0.36, 0.25), 0.95, 0), "asphalt": ((0.07, 0.07, 0.075), 0.8, 0), "sidewalk": ((0.58, 0.58, 0.56), 0.8, 0),
    "paving": ((0.50, 0.49, 0.47), 0.7, 0), "paving_light": ((0.72, 0.71, 0.67), 0.7, 0), "deck_stone": ((0.76, 0.70, 0.60), 0.45, 0),
    "stone_step": ((0.68, 0.66, 0.61), 0.6, 0), "pool_tile": ((0.20, 0.47, 0.58), 0.2, 0), "planter": ((0.17, 0.17, 0.17), 0.6, 0),
    "soil": ((0.18, 0.12, 0.08), 1.0, 0), "hedge": ((0.07, 0.15, 0.05), 0.9, 0), "retaining": ((0.60, 0.59, 0.56), 0.85, 0),
    "stone_wall": ((0.70, 0.64, 0.52), 0.9, 0), "steel_dark": ((0.04, 0.04, 0.04), 0.4, 0.9), "wood_dark": ((0.20, 0.12, 0.07), 0.5, 0),
    "stair": ((0.66, 0.65, 0.62), 0.5, 0), "wood": ((0.42, 0.28, 0.17), 0.4, 0), "fabric": ((0.72, 0.69, 0.63), 0.95, 0),
    "white": ((0.90, 0.90, 0.88), 0.4, 0), "leather": ((0.24, 0.13, 0.07), 0.45, 0), "grey": ((0.38, 0.38, 0.40), 0.5, 0),
    "black": ((0.03, 0.03, 0.032), 0.4, 0), "teak": ((0.48, 0.33, 0.19), 0.5, 0), "stone_top": ((0.85, 0.84, 0.82), 0.12, 0),
    "stone": ((0.70, 0.68, 0.64), 0.4, 0), "screen": ((0.92, 0.92, 0.92), 0.9, 0), "rug": ((0.62, 0.57, 0.50), 1.0, 0),
    "marble": ((0.88, 0.87, 0.85), 0.12, 0), "linen": ((0.90, 0.88, 0.84), 0.95, 0), "chair": ((0.28, 0.28, 0.30), 0.6, 0),
    "leaf": ((0.10, 0.22, 0.07), 0.8, 0), "mirror": ((0.85, 0.87, 0.88), 0.03, 1.0), "ochre": ((0.70, 0.45, 0.15), 0.8, 0),
    "sauna": ((0.66, 0.48, 0.30), 0.6, 0), "tile": ((0.84, 0.85, 0.85), 0.2, 0), "water": ((0.35, 0.70, 0.82), 0.05, 0),
    "glass": ((0.80, 0.90, 0.92), 0.02, 0), "earth_cut": ((0.30, 0.25, 0.19), 0.95, 0), "util_door": ((0.33, 0.34, 0.35), 0.45, 0.7),
    "bin_green": ((0.04, 0.22, 0.07), 0.5, 0), "bin_orange": ((0.80, 0.28, 0.03), 0.5, 0), "bin_blue": ((0.03, 0.12, 0.50), 0.5, 0),
}
MATS = {}


def mat(name):
    if name in MATS:
        return MATS[name]
    col, rough, metal = SPEC.get(name, ((0.6, 0.6, 0.6), 0.6, 0))
    if name not in SPEC:
        print("unknown material:", name)
    m = None
    if SIMPLE:
        if name == "glass":
            m = P("glass", col, rough=0.05, alpha=0.28)
            try:
                m.blend_method = "BLEND"
            except Exception:
                pass
        else:
            m = P(name, col, rough=rough, metal=metal)
    elif name == "glass":
        m = V.glass("glass", tint=(0.94, 0.97, 0.97))
    elif name == "water":
        m = V.water("water")
    elif name == "wall_ext":
        m = P(name, col, rough=rough, bump=0.12, bump_scale=120, var=0.03, var_scale=1.5)
    elif name in ("concrete", "retaining", "stair"):
        m = P(name, col, rough=rough, bump=0.25, bump_scale=60, var=0.08, var_scale=2.0)
    elif name == "stone_wall":
        m = V.tiled(name, col, (0.45, 0.42, 0.36), 0.55, 0.22, rough=0.9, var=0.14, grout_w=0.012, offset=0.5, bump=0.8, wall=True)
    elif name == "floor_wood":
        m = V.wood_floor(name, col)
    elif name == "floor_stone":
        m = V.tiled(name, col, (0.6, 0.58, 0.54), 1.2, 0.6, rough=0.18, var=0.04, grout_w=0.003, offset=0.5, bump=0.15)
    elif name in ("floor_tile", "tile"):
        m = V.tiled(name, col, (0.65, 0.65, 0.65), 0.6, 0.6, rough=0.2, var=0.03, grout_w=0.003, bump=0.15)
    elif name == "deck_stone":
        m = V.tiled(name, col, (0.55, 0.50, 0.42), 1.2, 0.6, rough=0.5, var=0.07, grout_w=0.005, offset=0.5, bump=0.3)
    elif name in ("paving", "paving_light"):
        m = V.tiled(name, col, tuple(c * 0.7 for c in col), 0.4, 0.2, rough=0.75, var=0.1, grout_w=0.004, offset=0.5, bump=0.4)
    elif name == "pool_tile":
        m = V.tiled(name, col, (0.75, 0.85, 0.88), 0.1, 0.1, rough=0.15, var=0.12, grout_w=0.004, bump=0.2)
    elif name in ("grass", "garden"):
        m = P(name, col, rough=0.95, bump=0.9, bump_scale=260, var=0.28, var_scale=0.9)
    elif name == "ground":
        m = P(name, col, rough=0.95, bump=0.8, bump_scale=30, var=0.25, var_scale=0.25)
    elif name == "asphalt":
        m = P(name, col, rough=0.8, bump=0.5, bump_scale=400, var=0.15, var_scale=0.6)
    elif name == "roof_gravel":
        m = P(name, col, rough=0.95, bump=0.9, bump_scale=500, var=0.1, var_scale=3)
    elif name == "hedge":
        m = V.veg_materials()["hedge"]
    elif name == "marble":
        m = V.marble(name, (0.90, 0.89, 0.87), (0.35, 0.33, 0.32))
    elif name in ("fabric", "linen", "rug", "floor_carpet"):
        m = P(name, col, rough=1.0, sheen=0.4, bump=0.3, bump_scale=900)
    elif name in ("wood", "teak", "door", "wood_dark", "sauna", "floor_wood_light"):
        m = P(name, col, rough=rough, bump=0.1, bump_scale=30, var=0.12, var_scale=6)
    else:
        m = P(name, col, rough=rough, metal=metal)
    MATS[name] = m
    return m


# ============================================================================ visibility per view
def visible(p):
    fl, cat, name = p["floor"], p["cat"], p.get("name", "")
    if CUT is None:
        return True
    if CUT == "B":
        if fl == "B":
            return True
        return fl == "S" and (name.startswith("entrance stair") and cat == "stair" or name.startswith("pillar")
                              or name in ("retaining wall drive", "retaining wall ocourt", "retaining wall ecourt"))
    if CUT == "G":
        return fl in ("G", "S") or (fl == "B" and cat != "furn")
    return fl in ("G", "S", "F") or (fl == "B" and cat != "furn") or (fl == "R" and p["z0"] < 6.0)


def terrain_visible(t):
    return CUT != "B" or t["name"] in ("drive", "ocourt", "ecourt")


# ============================================================================ geometry
GROUP_NAME = {"S": "Site", "B": "Floor B - basement", "G": "Floor G - ground", "F": "Floor F - first", "R": "Roofs"}
parents = {}


def parent_of(fl):
    if fl not in parents:
        e = bpy.data.objects.new(GROUP_NAME[fl], None)
        V.link(e)
        parents[fl] = e
    return parents[fl]


def add_prism(bm, p):
    z0, z1 = p["z0"], p["z1"]
    for ring in [p["pts"]] + p["holes"]:
        n = len(ring)
        vb = [bm.verts.new((x, y, z0)) for x, y in ring]
        vt = [bm.verts.new((x, y, z1)) for x, y in ring]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    caps = p.get("cap") or [p["pts"]]
    for poly in caps:
        a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
        ccw = poly if a > 0 else poly[::-1]
        bm.faces.new([bm.verts.new((x, y, z1)) for x, y in ccw])
        bm.faces.new([bm.verts.new((x, y, z0)) for x, y in ccw[::-1]])


groups = {}
for p in DATA["prisms"]:
    if visible(p):
        groups.setdefault((p["floor"], p["cat"], p["mat"]), []).append(p)
for (fl, cat, mname), items in sorted(groups.items()):
    bm = bmesh.new()
    for p in items:
        add_prism(bm, p)
    me = bpy.data.meshes.new(f"{fl}_{cat}_{mname}")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(f"{fl}_{cat}_{mname}", me)
    me.materials.append(mat(mname))
    V.link(o)
    o.parent = parent_of(fl)
    if cat == "glass" and not SIMPLE:
        o.visible_shadow = True

for t in DATA["terrain"]:
    if not terrain_visible(t) or not t["tris"]:
        continue
    me = bpy.data.meshes.new("terrain_" + t["name"])
    me.from_pydata([tuple(v) for v in t["verts"]], [], [tuple(f) for f in t["tris"]])
    me.validate()
    me.update()
    o = bpy.data.objects.new("terrain_" + t["name"], me)
    me.materials.append(mat(t["mat"]))
    V.link(o)
    o.parent = parent_of("S")
    if t["smooth"]:
        for poly in me.polygons:
            poly.use_smooth = True

# ---------------------------------------------------------------------------- trees and cars
CAR_RGB = {"car_black": (0.02, 0.02, 0.025), "car_red": (0.50, 0.03, 0.03), "car_silver": (0.60, 0.60, 0.62), "car_grey": (0.15, 0.16, 0.17),
           "car_white": (0.85, 0.85, 0.85), "car_blue": (0.03, 0.08, 0.30)}
CAR_GLB = os.path.join(SP, "assets", "CarConcept", "CarConcept.glb")


def bounds(root):
    bpy.context.view_layer.update()
    mn, mx = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    stack = list(root.children)
    while stack:
        o = stack.pop()
        stack += list(o.children)
        if o.type == "MESH":
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
                mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
    return mn, mx


def car(x, y, z, rot, color):
    col = CAR_RGB.get(color, (0.3, 0.3, 0.3))
    if FAST or not os.path.exists(CAR_GLB):
        m = P("car_" + color, col, rough=0.25, metal=0.6) if ("car_" + color) not in bpy.data.materials else bpy.data.materials["car_" + color]
        piv = bpy.data.objects.new("car", None)
        V.link(piv)
        for nm, (x0, x1, y0, y1, z0, z1) in (("body", (-0.95, 0.95, -2.3, 2.3, 0.25, 0.85)), ("cabin", (-0.8, 0.8, -1.2, 0.9, 0.85, 1.35))):
            b = V.box("car_" + nm, x0, x1, y0, y1, z0, z1, m, bevel=0.12)
            b.parent = piv
        piv.location = (x, y, z)
        piv.rotation_euler = (0, 0, math.radians(rot))
        piv.parent = parent_of("B")
        return
    root = V.glb(CAR_GLB, (0, 0, 0), 0, 1.0, recolor={"Paint 1": col, "Paint 2": tuple(c * 0.6 for c in col)})
    mn, mx = bounds(root)
    size = mx - mn
    piv = bpy.data.objects.new("car", None)
    V.link(piv)
    root.parent = piv
    root.location = (-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)
    piv.location = (x, y, z)
    piv.rotation_euler = (0, 0, math.radians(rot + (90 if size.x > size.y else 0)))


if SIMPLE:      # plain colours for the trees too, so they survive the glTF export
    V.VEG.update(bark=P("bark", (0.24, 0.21, 0.17), rough=0.9), olive=P("olive_leaf", (0.20, 0.26, 0.12), rough=0.9),
                 cypress=P("cypress_leaf", (0.04, 0.10, 0.04), rough=0.9), hedge=P("hedge_leaf", (0.07, 0.15, 0.05), rough=0.9),
                 shrub=P("shrub_leaf", (0.12, 0.20, 0.07), rough=0.9))
seed = 11
for m in DATA["markers"]:
    x, y = m["p"]
    if m["kind"] == "car":
        if CUT == "B" or SIMPLE:
            car(x, y, m["z"], m["rot"], m["color"])
    elif m["kind"] == "olive":
        if CUT is None:
            V.olive_tree(x, y, m["r"] / 1.6, seed=seed, fast=FAST, z=m["z"] - 0.05)
    elif m["kind"] == "cypress":
        if CUT != "B":
            V.cypress(x, y, h=6.0 + (seed % 3) * 0.5, rad=0.55, seed=seed, fast=FAST, z=m["z"])
    seed += 7

if args.glb:
    for o in bpy.data.objects:                      # tree parts made by vlib go under the site node
        if o.parent is None and o.type != "EMPTY":
            o.parent = parent_of("S")
    bpy.ops.export_scene.gltf(filepath=args.glb, export_format="GLB", export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("exported", args.glb, os.path.getsize(args.glb) // 1024, "KB")
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=args.blend)
    sys.exit(0)

# ============================================================================ light, camera, render
VIEWS = {
    "aerial_front": dict(pos=(-27, -14, 23), target=(22, 22, -1.5), lens=30, sun=(40, 232), exposure=0.3),
    "aerial_back": dict(pos=(78, -2, 21), target=(30, 24, 0.5), lens=33, sun=(40, 255), exposure=0.3),
    "aerial_side": dict(pos=(24, -31, 27), target=(27, 22, 0), lens=27, sun=(42, 225), exposure=0.3),
    "street": dict(pos=(-12.5, 4.5, -2.2), target=(13, 23, 0.6), lens=22, sun=(38, 228), two_point=True, shift_y=0.12, exposure=0.55),
    "garden": dict(pos=(44.2, 17.9, 1.5), target=(31.5, 27.5, 2.0), lens=19, sun=(36, 240), two_point=True, shift_y=0.06, exposure=0.6),
    "terrace": dict(pos=(7.2, 13.9, 1.65), target=(30, 25, 2.0), lens=20, sun=(36, 240), two_point=True, shift_y=0.06, exposure=0.6),
    "top": dict(ortho=86.0, target=(27, 18.5, 0), dirv=(0.0, -0.001, 1.0), sun=(52, 232), exposure=0.5),
    "cut_B": dict(ortho=41.0, target=(15.5, 23.6, -3.0), dirv=(0.0, -1.0, 2.0), sun=(58, 215), exposure=0.15),
    "cut_G": dict(ortho=63.0, target=(26.0, 21.5, 0.5), dirv=(0.0, -1.0, 2.0), sun=(58, 215), exposure=0.4),
    "cut_F": dict(ortho=44.0, target=(21.5, 24.0, 4.0), dirv=(0.0, -1.0, 2.0), sun=(58, 215), exposure=0.4),
}
vw = VIEWS[VIEW]
V.daylight(vw["sun"][0], vw["sun"][1], sky=0.045, sun=4.2)
if CUT is None:
    V.clouds(coverage=0.42, seed=3.0)
gm = P("studio", (0.40, 0.40, 0.395), rough=0.9)
zb = -3.92 if CUT == "B" else -8.0
V.quad("studio", (-6000, -6000, zb), (6000, -6000, zb), (6000, 6000, zb), (-6000, 6000, zb), gm)
if "ortho" in vw:
    d = Vector(vw["dirv"]).normalized()
    tg = Vector(vw["target"])
    co = V.camera(tuple(tg + d * 150), tuple(tg), 50, two_point=False)
    co.data.type = "ORTHO"
    co.data.ortho_scale = vw["ortho"]
else:
    V.camera(vw["pos"], vw["target"], vw["lens"], shift_y=vw.get("shift_y", 0.0), two_point=vw.get("two_point", False))
if CUT and args.out:
    # image positions of the room names, for the label overlay
    from bpy_extras.object_utils import world_to_camera_view
    rx, ry = (int(v) for v in args.res.split("x"))
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    bpy.context.view_layer.update()
    pil = [(p_["short"] if p_["id"] in ("gas", "bins") else "פילר " + p_["short"], (p_["rect"][0] + p_["rect"][2]) / 2 - (1.6 if p_["face"] == "W" else 0.0),
            (p_["rect"][1] + p_["rect"][3]) / 2, -3.2) for p_ in DATA["pillars"]]
    extra = {"B": [("רחבת כניסה לחניון", 11.0, 10.9, -3.5), ("חצר אנגלית", 12.0, 35.1, -3.5), ("רחבת כניסה למשרד", 3.2, 27.6, -3.5), ("מדרגות כניסה", 19.7, 11.45, -2.0)] + pil,
             "G": [("מרפסת גג מעל החניון", 19.5, 17.8, 0.3), ("בריכה", 41.5, 27.5, 0.0), ("גינה", 37.0, 17.6, 0.0), ("רחבת כניסה לחניון", 10.0, 8.5, -3.5),
                   ("רחוב", -2.5, 20.0, -4.0), ("פרגולה ופינת אוכל", 11.25, 14.3, 0.3)] + pil,
             "F": [("מרפסת", 11.0, 21.1, 3.6), ("מרפסת", 24.7, 21.1, 3.6), ("גג ירוק מעל הסלון", 31.75, 28.0, 5.6), ("מרפסת גג בקומת הקרקע", 16.0, 16.5, 0.1),
                   ("בריכה", 41.5, 27.5, 0.0)]}[CUT]
    seen, labels = set(), []
    for r in DATA["rooms"]:
        if r["floor"] != CUT or r["id"] in seen:
            continue
        seen.add(r["id"])
        co = world_to_camera_view(scene, scene.camera, Vector((r["label"][0], r["label"][1], r["z0"] + 1.2)))
        nm = {"פיר מעלית": "מעלית"}.get(r["name"], r["name"])
        labels.append(dict(name=nm, area=r["area"] if r["name"] not in ("מדרגות", "פיר מעלית") else None, u=co.x, v=1 - co.y, kind="room"))
    for nm, x, y, z in extra:
        co = world_to_camera_view(scene, scene.camera, Vector((x, y, z)))
        labels.append(dict(name=nm, area=None, u=co.x, v=1 - co.y, kind="site"))
    json.dump(labels, open(args.out + ".labels.json", "w", encoding="utf-8"), ensure_ascii=False)
if args.blend:
    bpy.ops.wm.save_as_mainfile(filepath=args.blend)
if args.out:
    V.render(args.out, res=args.res, samples=args.samples, exposure=args.exposure if args.exposure is not None else vw.get("exposure", 0.0))
