"""IFC4 model of the villa on plot 84 (opens in Revit, ArchiCAD, BlenderBIM and IFC viewers), built from model3d.json.

Levels, walls, slabs, doors, windows, stairs, railings, floor finishes, furniture, rooms (IfcSpace with areas), terrain and trees.
Coordinates: design metres, z relative to level 0.00 (= +91.00); map conversion to the old Israel grid is included.
"""
import json
import math
import os
import sys

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.georeference
import ifcopenshell.api.material
import ifcopenshell.api.project
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit

import model as M

DATA = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "scene84.py"), encoding="utf-8").read()
SPEC = eval(src[src.index("SPEC = {") + 7: src.index("\nMATS = {}")])          # same colours as the renders

api = ifcopenshell.api
f = api.project.create_file(version="IFC4")
project = api.root.create_entity(f, ifc_class="IfcProject", name="Villa and architects' office, plot 84, Rosh HaAyin")
api.unit.assign_unit(f, length={"is_metric": True, "raw": "METERS"}, area={"is_metric": True, "raw": "METERS"}, volume={"is_metric": True, "raw": "METERS"})
ctx = api.context.add_context(f, context_type="Model")
body = api.context.add_context(f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=ctx)
S = M.SITE
nx, ny = S["north_vec"]
api.georeference.edit_true_north(f, true_north=(nx, ny))
api.georeference.add_georeferencing(f, ifc_class="IfcMapConversion", name="EPSG:28193")
a, b = S["xh"]
api.georeference.edit_georeferencing(
    f, coordinate_operation={"Eastings": S["origin_world"][0] + S["y_offset"] * b, "Northings": S["origin_world"][1] - S["y_offset"] * a,
                             "OrthogonalHeight": M.ABS0, "XAxisAbscissa": a, "XAxisOrdinate": b, "Scale": 1.0},
    projected_crs={"Name": "EPSG:28193", "Description": "Israel 1923 / Israeli CS Grid (the surveyor's grid)"})

ZDIR = f.createIfcDirection((0.0, 0.0, 1.0))
XDIR = f.createIfcDirection((1.0, 0.0, 0.0))


def aggregate(parent, children):
    f.createIfcRelAggregates(ifcopenshell.guid.new(), None, None, None, parent, list(children))


def contain(structure, elements):
    f.createIfcRelContainedInSpatialStructure(ifcopenshell.guid.new(), None, None, None, list(elements), structure)


def axis(z=0.0):
    return f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, float(z))), ZDIR, XDIR)


site = api.root.create_entity(f, ifc_class="IfcSite", name="מגרש 84")
site.RefElevation = M.ABS0
site.LandTitleNumber = "גוש 5508, מגרש 84"
site.ObjectPlacement = f.createIfcLocalPlacement(None, axis())
building = api.root.create_entity(f, ifc_class="IfcBuilding", name="וילה ומשרד אדריכלים")
building.ObjectPlacement = f.createIfcLocalPlacement(site.ObjectPlacement, axis())
aggregate(project, [site])
aggregate(site, [building])
LEVELS = [("B", "קומת מרתף -3.50", -3.50), ("G", "קומת קרקע ±0.00", 0.00), ("F", "קומה א׳ +3.50", 3.50), ("R", "גג +6.80", 6.80)]
storey, elev = {}, {"S": 0.0}
for key, name, z in LEVELS:
    st = api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=name)
    st.Elevation = z
    st.ObjectPlacement = f.createIfcLocalPlacement(building.ObjectPlacement, axis(z))
    storey[key], elev[key] = st, z
aggregate(building, [storey[k] for k, _, _ in LEVELS])
storey["S"] = site

# ---------------------------------------------------------------- styles and materials
styles, materials, by_material = {}, {}, {}


def srgb(c):
    return max(0.0, min(1.0, c)) ** (1 / 2.2)


def style(mat):
    if mat not in styles:
        col = SPEC.get(mat, ((0.6, 0.6, 0.6), 0.6, 0))[0]
        transp = {"glass": 0.7, "water": 0.35}.get(mat, 0.0)
        sh = f.createIfcSurfaceStyleShading(f.createIfcColourRgb(None, srgb(col[0]), srgb(col[1]), srgb(col[2])), transp)
        styles[mat] = f.createIfcSurfaceStyle(mat, "BOTH", [sh])
    return styles[mat]


def styled(item, mat):
    f.createIfcStyledItem(item, [style(mat)], None)
    return item


def polyline(pts):
    return f.createIfcPolyline([f.createIfcCartesianPoint((float(x), float(y))) for x, y in list(pts) + [pts[0]]])


def solid(p, zref):
    if p["holes"]:
        prof = f.createIfcArbitraryProfileDefWithVoids("AREA", None, polyline(p["pts"]), [polyline(h) for h in p["holes"]])
    else:
        prof = f.createIfcArbitraryClosedProfileDef("AREA", None, polyline(p["pts"]))
    return styled(f.createIfcExtrudedAreaSolid(prof, axis(p["z0"] - zref), ZDIR, float(p["z1"] - p["z0"])), p["mat"])


def mesh(verts, tris, mat, zref=0.0):
    pl = f.createIfcCartesianPointList3D([[float(x), float(y), float(z - zref)] for x, y, z in verts])
    return styled(f.createIfcTriangulatedFaceSet(pl, None, None, [[i + 1, j + 1, k + 1] for i, j, k in tris], None), mat)


contained = {}


def product(ifc_class, name, key, items, predefined=None, reptype="SweptSolid", mat=None, aggregate=False):
    el = api.root.create_entity(f, ifc_class=ifc_class, name=name, predefined_type=predefined)
    el.ObjectPlacement = f.createIfcLocalPlacement(storey[key].ObjectPlacement, axis())
    el.Representation = f.createIfcProductDefinitionShape(None, None, [f.createIfcShapeRepresentation(body, "Body", reptype, items)])
    if not aggregate:
        contained.setdefault(key, []).append(el)
    if mat:
        by_material.setdefault(mat, []).append(el)
    return el


MAT_HE = {"wall_ext": "קיר חוץ בטיח לבן", "wall_int": "קיר פנים", "concrete": "בטון", "glass": "זכוכית", "frame": "אלומיניום כהה", "door": "עץ אגוז",
          "stone_wall": "אבן", "retaining": "בטון חשוף", "deck_stone": "אבן טרוורטין", "floor_wood": "פרקט אלון", "floor_stone": "אריחי אבן",
          "floor_tile": "אריחי קרמיקה", "floor_epoxy": "אפוקסי", "floor_carpet": "שטיח", "grass": "דשא", "water": "מים"}


def classify(p):
    """-> (IFC class, name, predefined type, group key or None)"""
    cat, name, mat, fl = p["cat"], p.get("name", ""), p["mat"], p["floor"]
    if cat == "wall":
        return "IfcWall", "קיר חוץ" if mat == "wall_ext" else "קיר פנים", None, None
    if cat == "parapet":
        return "IfcWall", "מעקה גג", "PARAPET", None
    if cat == "slab":
        return "IfcSlab", "גג" if fl == "R" else "רצפה", "ROOF" if fl == "R" else ("BASESLAB" if p["z1"] < -3.0 else "FLOOR"), None
    if cat == "finish":
        return "IfcCovering", "ריצוף – " + (name or mat), "FLOORING", None
    if cat == "roof":
        return "IfcCovering", "גג ירוק" if mat == "grass" else "גמר גג", "ROOFING", None
    if cat == "door":
        return "IfcDoor", {"garage_door": "שער חניון", "steel": "דלת מעלית"}.get(mat, "דלת"), "GATE" if mat == "garage_door" else "DOOR", None
    if cat == "glass":
        if "guard" in name or "balustrade" in name:
            return "IfcRailing", "מעקה זכוכית", "GUARDRAIL", None
        return "IfcWindow", "חלון", "WINDOW", None
    if cat == "frame":
        return "IfcMember", "מסגרות חלונות", "MULLION", ("frame", fl)
    if cat == "stair":
        if name.startswith("entrance"):
            return "IfcStair", "מדרגות כניסה חיצוניות", "STRAIGHT_RUN_STAIR", ("stair", "ext")
        return "IfcStair", "מדרגות, רוחב מהלך 1.30 מ׳", "HALF_TURN_STAIR", ("stair", fl)
    if cat == "furn":
        return "IfcFurniture", "ריהוט – " + (name or mat), None, ("furn", fl, name or mat)
    if cat == "water":
        return "IfcBuildingElementProxy", "מי הבריכה", None, None
    if name.startswith("retaining wall"):
        return "IfcWall", "קיר תומך", None, ("ret", name)
    if name == "boundary wall":
        return "IfcWall", "גדר אבן בגבול המגרש", None, ("bound",)
    if name == "foundation":
        return "IfcFooting", "יסוד", None, None
    if name.startswith("pillar "):
        he = {pl["id"]: pl["name"] for pl in M.PILLARS}[name.split()[1]]
        return "IfcBuildingElementProxy", he, None, ("pillar", name)
    he = {"pergola": "פרגולה", "pool deck": "דק הבריכה", "pool shell": "קירות הבריכה", "pool floor": "רצפת הבריכה"}.get(name)
    if not he:
        he = {"planter": "אדנית", "soil": "אדמת גן", "hedge": "גדר חיה"}.get(mat, name or mat)
    return "IfcBuildingElementProxy", he, None, ("site", fl, he, mat)


groups = {}
count = {}
for p in DATA["prisms"]:
    cls, name, pre, gkey = classify(p)
    fl = p["floor"]
    if gkey is None:
        product(cls, name, fl, [solid(p, elev[fl])], pre, mat=p["mat"])
        count[cls] = count.get(cls, 0) + 1
    else:
        groups.setdefault((cls, name, pre, fl, gkey), []).append(p)
for (cls, name, pre, fl, gkey), ps in groups.items():
    mats = {q["mat"] for q in ps}
    product(cls, name, fl, [solid(q, elev[fl]) for q in ps], pre, mat=ps[0]["mat"] if len(mats) == 1 else None)
    count[cls] = count.get(cls, 0) + 1

# ---------------------------------------------------------------- rooms as spaces
spaces = {}
for r in DATA["rooms"]:
    fl = r["floor"]
    prof = f.createIfcArbitraryClosedProfileDef("AREA", None, polyline(r["pts"]))
    item = f.createIfcExtrudedAreaSolid(prof, axis(r["z0"] - elev[fl] + 0.02), ZDIR, float(r["z1"] - r["z0"] - 0.02))
    sp = product("IfcSpace", r["id"], fl, [item], "PARKING" if r["name"] == "חניון" else "SPACE", aggregate=True)
    sp.LongName = r["name"]
    sp.CompositionType = "ELEMENT"
    q = api.pset.add_qto(f, product=sp, name="Qto_SpaceBaseQuantities")
    api.pset.edit_qto(f, qto=q, properties={"NetFloorArea": float(r["area"]), "Height": float(r["z1"] - r["z0"])})
    ps = api.pset.add_pset(f, product=sp, name="Pset_SpaceCommon")
    api.pset.edit_pset(f, pset=ps, properties={"Reference": r["group"], "IsExternal": False})
    spaces.setdefault(fl, []).append(sp)
for fl, sps in spaces.items():
    aggregate(storey[fl], sps)
count["IfcSpace"] = sum(len(v) for v in spaces.values())

# ---------------------------------------------------------------- terrain, trees, cars
TERRAIN_HE = {"drive": "רחבת כניסה לחניון", "ocourt": "רחבת כניסה למשרד", "ecourt": "חצר אנגלית", "lawn": "מדשאה", "npath": "שביל שירות מאחורי הבריכה", "garden": "גינה, קרקע טבעית",
              "road": "כביש", "walk": "מדרכה", "around": "קרקע טבעית מסביב למגרש"}
for t in DATA["terrain"]:
    if t["name"] == "base" or not t["tris"]:
        continue
    product("IfcGeographicElement", TERRAIN_HE.get(t["name"], t["name"]), "S", [mesh(t["verts"], t["tris"], t["mat"])], "TERRAIN", reptype="Tessellation")
    count["terrain"] = count.get("terrain", 0) + 1


def lathe(profile, cx, cy, z, n=10):
    """Revolve (radius, height) pairs around a vertical axis -> triangles."""
    verts, tris = [], []
    for r, h in profile:
        for i in range(n):
            ang = 2 * math.pi * i / n
            verts.append((cx + r * math.cos(ang), cy + r * math.sin(ang), z + h))
    for k in range(len(profile) - 1):
        for i in range(n):
            a0, a1, b0, b1 = k * n + i, k * n + (i + 1) % n, (k + 1) * n + i, (k + 1) * n + (i + 1) % n
            tris += [(a0, a1, b1), (a0, b1, b0)]
    return verts, tris


SPEC.setdefault("bark", ((0.24, 0.21, 0.17), 0.9, 0))
SPEC.setdefault("olive", ((0.25, 0.30, 0.16), 0.9, 0))
SPEC.setdefault("cypress", ((0.05, 0.12, 0.05), 0.9, 0))
for m in DATA["markers"]:
    x, y = m["p"]
    if m["kind"] == "olive":
        r = m["r"]
        tv, tt = lathe([(0.16, 0.0), (0.12, 1.5)], x, y, m["z"], 8)
        cv, ct = lathe([(0.02, 1.2), (r * 0.75, 1.6), (r, 2.4), (r * 0.8, 3.2), (0.02, 3.7)], x, y, m["z"], 10)
        product("IfcGeographicElement", "עץ זית", "S", [mesh(tv, tt, "bark"), mesh(cv, ct, "olive")], "USERDEFINED", reptype="Tessellation").ObjectType = "TREE"
    elif m["kind"] == "cypress":
        cv, ct = lathe([(0.05, 0.0), (0.5, 0.8), (0.55, 2.5), (0.35, 5.0), (0.02, 6.5)], x, y, m["z"], 10)
        product("IfcGeographicElement", "ברוש", "S", [mesh(cv, ct, "cypress")], "USERDEFINED", reptype="Tessellation").ObjectType = "TREE"
    elif m["kind"] == "car":
        c, s = math.cos(math.radians(m["rot"])), math.sin(math.radians(m["rot"]))
        items = []
        for (x0, x1, y0, y1, z0, z1) in ((-0.95, 0.95, -2.3, 2.3, 0.25, 0.85), (-0.8, 0.8, -1.2, 0.9, 0.85, 1.35)):
            pts = [(x + px * c - py * s, y + px * s + py * c) for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            SPEC.setdefault(m["color"], ({"car_black": (0.02, 0.02, 0.025), "car_red": (0.5, 0.03, 0.03), "car_silver": (0.6, 0.6, 0.62), "car_grey": (0.15, 0.16, 0.17),
                                          "car_white": (0.85, 0.85, 0.85), "car_blue": (0.03, 0.08, 0.3)}.get(m["color"], (0.3, 0.3, 0.3)), 0.3, 0.5))
            items.append(solid(dict(pts=pts, holes=[], z0=m["z"] + z0, z1=m["z"] + z1, mat=m["color"]), elev["B"]))
        product("IfcFurniture", "רכב בחניה", "B", items)
    count["markers"] = count.get("markers", 0) + 1

for key, els in contained.items():
    contain(storey[key], els)
for mat, els in by_material.items():
    mm = api.material.add_material(f, name=MAT_HE.get(mat, mat), category=mat)
    api.material.assign_material(f, products=els, type="IfcMaterial", material=mm)

f.write(OUT)
print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.2f} MB", count)
