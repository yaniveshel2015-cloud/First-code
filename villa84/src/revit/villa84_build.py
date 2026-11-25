# -*- coding: utf-8 -*-
"""Villa 84 - build a native, editable Revit model from villa84-revit-data.json.

Runs inside Revit 2027 in a Dynamo Python Script node (engine: PythonNet3).
  IN[0]  path of villa84-revit-data.json
  IN[1]  (optional) path of the surveyor's DWG, linked into the site plan at its survey coordinates
  OUT    a report: what was created, and every step that failed (the script continues after a failure)

Everything is made of ordinary Revit elements: levels, wall types and joined walls, doors and windows hosted in the walls,
floors and roofs, rooms with names, numbers and areas, stairs, dimensions bound to the walls, sections, a toposolid,
the plot boundary, the shared coordinates of the survey, sheets and a room schedule.
"""
import json
import math
import os
import traceback

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import (BoundingBoxXYZ, BuiltInCategory, BuiltInParameter, CompoundStructure, Curve, CurveArray, CurveLoop,
                               DWGImportOptions, ElementId, FailureProcessingResult, FailureSeverity, FamilyInstanceReferenceType,
                               FamilySymbol, FilteredElementCollector, Floor, FloorType, HostObjectUtils, IFailuresPreprocessor, ImportPlacement,
                               Level, Line, LinkElementId, Material, MaterialFunctionAssignment, ProjectPosition, Reference, ReferenceArray,
                               ScheduleSheetInstance, ScheduleSortGroupField, ShellLayerType, SketchPlane, Transaction, Transform, UV, View,
                               ViewFamily, ViewFamilyType, ViewPlan, ViewSchedule, ViewSection, ViewSheet, Viewport, Wall, WallFunction,
                               WallKind, WallType, XYZ)
from Autodesk.Revit.DB.Architecture import StairsEditScope, StairsLanding, StairsRun, StairsRunJustification
from Autodesk.Revit.DB.Structure import StructuralType
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import List

doc = DocumentManager.Instance.CurrentDBDocument
FT = 1.0 / 0.3048
REPORT = {"created": {}, "notes": [], "errors": []}


def ft(m):
    return m * FT


def P(x, y, z=0.0):
    return XYZ(ft(x), ft(y), ft(z))


def count(what, n=1):
    REPORT["created"][what] = REPORT["created"].get(what, 0) + n


def note(msg):
    REPORT["notes"].append(msg)


def fail(where):
    REPORT["errors"].append(where + ": " + traceback.format_exc(limit=2).strip().splitlines()[-1])


# ------------------------------------------------------------------ quiet transactions (warnings are removed, errors stay)
QUIET = None
try:
    class _Quiet(IFailuresPreprocessor):
        __namespace__ = "Villa84Build"

        def PreprocessFailures(self, accessor):
            for f in list(accessor.GetFailureMessages()):
                if f.GetSeverity() == FailureSeverity.Warning:
                    accessor.DeleteWarning(f)
            return FailureProcessingResult.Continue

    QUIET = _Quiet
except Exception:
    note("warnings will be shown by Revit (the failure handler could not be created)")


def transaction(name, fn):
    t = Transaction(doc, "Villa84: " + name)
    t.Start()
    if QUIET is not None:
        try:
            opts = t.GetFailureHandlingOptions()
            opts.SetFailuresPreprocessor(QUIET())
            t.SetFailureHandlingOptions(opts)
        except Exception:
            pass
    try:
        out = fn()
        t.Commit()
        return out
    except Exception:
        fail(name)
        try:
            t.RollBack()
        except Exception:
            pass
        return None


def param(el, bip, value):
    try:
        p = el.get_Parameter(bip)
        if p is not None and not p.IsReadOnly:
            p.Set(value)
            return True
    except Exception:
        pass
    return False


def param_by_names(el, names, value):
    for p in el.Parameters:
        try:
            if p.Definition.Name in names and not p.IsReadOnly:
                p.Set(value)
                return True
        except Exception:
            continue
    return False


def unique_name(existing, base):
    name, k = base, 2
    while name in existing:
        name = "%s (%d)" % (base, k)
        k += 1
    existing.add(name)
    return name


def curve_loop(pts, z):
    loop = CurveLoop()
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1e-6:
            continue
        loop.Append(Line.CreateBound(P(a[0], a[1], z), P(b[0], b[1], z)))
    return loop


# ------------------------------------------------------------------ inputs
DATA_NAME = "villa84-revit-data.json"


def find_data(given):
    """The path picked in the data node, or the data file in a villa84 folder in the usual places."""
    tried = []
    if given:
        g = str(given)
        tried.append(g)
        if os.path.isfile(g):
            return g
        if os.path.isdir(g):
            tried.append(os.path.join(g, DATA_NAME))
    home = os.path.expanduser("~")
    for base in ("C:\\", home, os.path.join(home, "Desktop"), os.path.join(home, "Documents"), os.path.join(home, "Downloads")):
        for sub in ("villa84", os.path.join("villa84", "03-revit"), os.path.join("villa84-all-files", "villa84", "03-revit")):
            tried.append(os.path.join(base, sub, DATA_NAME))
    for t in tried:
        if os.path.isfile(t):
            return t
    raise IOError("Data file not found: " + (str(given) if given else "(empty)") + ". In the node 'קובץ נתונים' click Browse and pick "
                  + DATA_NAME + " (in the folder 03-revit of the zip). לא נמצא קובץ הנתונים: לחץ Browse בצומת 'קובץ נתונים' ובחר את הקובץ.")


data_path = find_data(IN[0])  # noqa: F821  (Dynamo input)
dwg_path = IN[1] if len(IN) > 1 else None  # noqa: F821
D = json.load(open(str(data_path), encoding="utf-8"))
TransactionManager.Instance.ForceCloseTransaction()

LEVEL = {}
LEVEL_Z = {L["key"]: L["elevation"] for L in D["levels"]}
PLAN = {}
WALL = {}
FLOORPLAN_VFT = None
SECTION_VFT = None


def view_family_type(family):
    for v in FilteredElementCollector(doc).OfClass(ViewFamilyType):
        if v.ViewFamily == family:
            return v
    return None


# ------------------------------------------------------------------ 1. levels and plan views
def make_levels():
    global FLOORPLAN_VFT
    existing = list(FilteredElementCollector(doc).OfClass(Level))
    used = set()
    for L in D["levels"]:
        z = ft(L["elevation"])
        lv = next((e for e in existing if abs(e.Elevation - z) < 0.003 and e.Id not in used), None)
        if lv is None:
            lv = Level.Create(doc, z)
            count("levels")
        used.add(lv.Id)
        try:
            lv.Name = L["name"]
        except Exception:
            lv.Name = L["name"] + " "
        LEVEL[L["key"]] = lv
    FLOORPLAN_VFT = view_family_type(ViewFamily.FloorPlan)
    names = set(v.Name for v in FilteredElementCollector(doc).OfClass(View))
    for L in D["levels"]:
        if not L["plan"]:
            continue
        lv = LEVEL[L["key"]]
        vp = next((v for v in FilteredElementCollector(doc).OfClass(ViewPlan)
                   if not v.IsTemplate and v.GenLevel is not None and v.GenLevel.Id == lv.Id and v.ViewType.ToString() == "FloorPlan"), None)
        if vp is None:
            vp = ViewPlan.Create(doc, FLOORPLAN_VFT.Id, lv.Id)
            count("plan views")
        try:
            vp.Name = unique_name(names, "תוכנית " + L["name"])
        except Exception:
            pass
        vp.Scale = 100
        PLAN[L["key"]] = vp
    site = ViewPlan.Create(doc, FLOORPLAN_VFT.Id, LEVEL["G"].Id)
    site.Name = unique_name(names, "תוכנית מגרש")
    site.Scale = 200
    PLAN["site"] = site
    count("plan views")
    # template levels we did not use (for example "Level 2"), if they carry nothing
    for e in existing:
        if e.Id not in used:
            try:
                doc.Delete(e.Id)
                note("deleted the template level " + e.Name)
            except Exception:
                pass


# ------------------------------------------------------------------ 2. survey coordinates, true north, +91.00
def set_location():
    S = D["site"]
    ew, ns = S["survey_origin"]
    elev = S["elevation_zero"]
    target = S["check_point"]
    for sign in (1, -1):
        ang = math.radians(S["x_axis_angle_deg"]) * sign
        pos = ProjectPosition(ft(ew), ft(ns), ft(elev), ang)
        doc.ActiveProjectLocation.SetProjectPosition(XYZ.Zero, pos)
        tr = doc.ActiveProjectLocation.GetTotalTransform()
        p = P(target[0][0], target[0][1], 0.0)
        for cand in (tr.OfPoint(p), tr.Inverse.OfPoint(p)):
            if abs(cand.X / FT - target[1][0]) < 0.05 and abs(cand.Y / FT - target[1][1]) < 0.05:
                note("shared coordinates set: corner 219G = %.2f, %.2f (survey grid)" % (target[1][0], target[1][1]))
                return True
    note("check the shared coordinates: the test corner did not land on its survey point")
    return False


# ------------------------------------------------------------------ 3. types
def concrete_material():
    for m in FilteredElementCollector(doc).OfClass(Material):
        if "concrete" in m.Name.lower() or "בטון" in m.Name:
            return m.Id
    return ElementId.InvalidElementId


WALL_TYPES = {}
FLOOR_TYPES = {}


def make_types():
    mat = concrete_material()
    base = next((w for w in FilteredElementCollector(doc).OfClass(WallType) if w.Kind == WallKind.Basic), None)
    names = set(w.Name for w in FilteredElementCollector(doc).OfClass(WallType))
    for t in sorted(set(round(w["thickness"], 2) for w in D["walls"])):
        ext = abs(t - D["wall_types"]["exterior"]) < 0.01
        nm = unique_name(names, "Villa84 - %s %d" % ("חוץ" if ext else "פנים", round(t * 100)))
        wt = base.Duplicate(nm)
        wt.SetCompoundStructure(CompoundStructure.CreateSingleLayerCompoundStructure(MaterialFunctionAssignment.Structure, ft(t), mat))
        try:
            wt.Function = WallFunction.Exterior if ext else WallFunction.Interior
        except Exception:
            pass
        WALL_TYPES[t] = wt
        count("wall types")
    fbase = next(iter(FilteredElementCollector(doc).OfClass(FloorType)), None)
    fnames = set(f.Name for f in FilteredElementCollector(doc).OfClass(FloorType))
    for t in sorted(set(round(f["thickness"], 2) for f in D["floors"])):
        ft_ = fbase.Duplicate(unique_name(fnames, "Villa84 - תקרה %d" % round(t * 100)))
        ft_.SetCompoundStructure(CompoundStructure.CreateSingleLayerCompoundStructure(MaterialFunctionAssignment.Structure, ft(t), mat))
        FLOOR_TYPES[t] = ft_
        count("floor types")


# ------------------------------------------------------------------ 4. walls
def make_walls():
    for w in D["walls"]:
        try:
            lv = LEVEL[w["level"]]
            z = LEVEL_Z[w["level"]]
            (x0, y0), (x1, y1) = w["line"]
            ln = Line.CreateBound(P(x0, y0, z), P(x1, y1, z))
            wall = Wall.Create(doc, ln, WALL_TYPES[round(w["thickness"], 2)].Id, lv.Id, ft(w["height"]), 0.0, False, False)
            param(wall, BuiltInParameter.ALL_MODEL_MARK, w["id"])
            WALL[w["id"]] = (wall, w)
            count("walls")
        except Exception:
            fail("wall " + w["id"])


# ------------------------------------------------------------------ 5. doors, windows and openings in the walls
def symbols(cat):
    return [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(cat)]


def load_family(subfolder, names):
    try:
        paths = doc.Application.GetLibraryPaths()
        roots = [paths[k] for k in paths.Keys]
    except Exception:
        roots = []
    for r in roots:
        for nm in names:
            for sub in (subfolder, ""):
                p = os.path.join(r, sub, nm)
                if os.path.exists(p):
                    try:
                        doc.LoadFamily(p)
                        note("loaded family " + nm)
                        return True
                    except Exception:
                        pass
    return False


def pick(cands, words):
    for w in words:
        for s in cands:
            full = (s.FamilyName + " " + s.Name).lower()
            if w in full:
                return s
    return cands[0] if cands else None


SIZED = {}


def sized(sym, w, h, door):
    key = (sym.Id.ToString(), round(w, 2), round(h, 2))
    if key in SIZED:
        return SIZED[key]
    names = set(s.Name for s in FilteredElementCollector(doc).OfClass(FamilySymbol))
    new = sym.Duplicate(unique_name(names, "Villa84 %dx%d" % (round(w * 100), round(h * 100))))
    wb = [BuiltInParameter.DOOR_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM] if door else [BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM]
    hb = [BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM] if door else [BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM]
    if not any(param(new, b, ft(w)) for b in wb):
        param_by_names(new, ("Width", "רוחב"), ft(w))
    if not any(param(new, b, ft(h)) for b in hb):
        param_by_names(new, ("Height", "גובה"), ft(h))
    if not new.IsActive:
        new.Activate()
    SIZED[key] = new
    return new


def wall_opening(wall, w, op, z):
    (x0, y0), (x1, y1) = w["line"]
    if abs(y0 - y1) < 1e-9:
        p1, p2 = P(op["a"], y0, z + op["sill"]), P(op["b"], y0, z + op["head"])
    else:
        p1, p2 = P(x0, op["a"], z + op["sill"]), P(x0, op["b"], z + op["head"])
    doc.Create.NewOpening(wall, p1, p2)
    count("wall openings")


def make_openings():
    doors = symbols(BuiltInCategory.OST_Doors)
    if not doors:
        load_family("Doors", ["M_Single-Flush.rfa", "Single-Flush.rfa", "M_Door-Single-Panel.rfa"])
        load_family("Doors", ["M_Double-Flush.rfa", "Double-Flush.rfa"])
        doors = symbols(BuiltInCategory.OST_Doors)
    wins = symbols(BuiltInCategory.OST_Windows)
    if not wins:
        load_family("Windows", ["M_Fixed.rfa", "Fixed.rfa", "M_Window-Fixed.rfa"])
        wins = symbols(BuiltInCategory.OST_Windows)
    single = pick(doors, ["single", "חד"])
    double = pick(doors, ["double", "כפול"])
    garage = pick(doors, ["overhead", "garage", "sectional", "חניה"])
    fixed = pick(wins, ["fixed", "קבוע"])
    casement = pick(wins, ["casement", "awning", "sliding", "window"])
    if not doors:
        note("no door family in the project: doors are made as wall openings")
    if not wins:
        note("no window family in the project: windows are made as wall openings")
    for op in D["openings"]:
        try:
            wall, w = WALL[op["wall"]]
            z = LEVEL_Z[op["level"]]
            k = op["kind"]
            door = k in ("door", "door2", "garage")
            if k in ("open", "elev") or (door and not doors) or (not door and not wins):
                wall_opening(wall, w, op, z)
                continue
            sym = {"door": single, "door2": double, "garage": garage}.get(k) if door else (fixed if k in ("fixed", "slide") else casement)
            h = op["head"] - op["sill"]
            st = sized(sym, op["width"], h, door)
            (x0, y0), (x1, y1) = w["line"]
            cm = (op["a"] + op["b"]) / 2
            pt = P(cm, y0, z) if abs(y0 - y1) < 1e-9 else P(x0, cm, z)
            inst = doc.Create.NewFamilyInstance(pt, st, wall, LEVEL[op["level"]], StructuralType.NonStructural)
            if not door:
                param(inst, BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM, ft(op["sill"]))
            # doors open to the side given in the plan
            want = XYZ(0, op["swing"], 0) if abs(y0 - y1) < 1e-9 else XYZ(op["swing"], 0, 0)
            try:
                if door and inst.FacingOrientation.DotProduct(want) < 0:
                    inst.flipFacing()
            except Exception:
                pass
            param(inst, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, {"door": "דלת", "door2": "דלת כפולה", "garage": "שער חניון", "win": "חלון",
                                                                        "fixed": "זיגוג קבוע", "slide": "זכוכית נגררת"}.get(k, k)
                  + (" · דלת הדף" if op.get("blast") else ""))
            count("doors" if door else "windows")
        except Exception:
            fail("opening %s %s %.2f-%.2f" % (op["level"], op["kind"], op["a"], op["b"]))


# ------------------------------------------------------------------ 6. floors and roofs
def make_floors():
    for f in D["floors"]:
        try:
            z = LEVEL_Z[f["level"]]
            loops = List[CurveLoop]()
            for pts in f["loops"]:
                loops.Add(curve_loop(pts, z))
            fl = Floor.Create(doc, loops, FLOOR_TYPES[round(f["thickness"], 2)].Id, LEVEL[f["level"]].Id)
            param(fl, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, f["name"])
            count("roofs" if f["kind"] == "roof" else "floors")
        except Exception:
            fail("floor " + f["name"])


# ------------------------------------------------------------------ 7. stairs
def make_stairs():
    for s in D["stairs"]:
        base, top = LEVEL[s["base"]], LEVEL[s["top"]]
        zb = LEVEL_Z[s["base"]]
        try:
            scope = StairsEditScope(doc, "Villa84 stairs")
            sid = scope.Start(base.Id, top.Id)
            t = Transaction(doc, "Villa84: stair runs")
            t.Start()
            st = doc.GetElement(sid)
            param(st, BuiltInParameter.STAIRS_DESIRED_NUMBER_OF_RISERS, s["risers"])
            param(st, BuiltInParameter.STAIRS_ACTUAL_TREAD_DEPTH, ft(s["tread"]))
            (a, b) = s["run1"]
            r1 = StairsRun.CreateStraightRun(doc, sid, Line.CreateBound(P(a[0], a[1], zb), P(b[0], b[1], zb)), StairsRunJustification.Center)
            r1.ActualRunWidth = ft(s["width"])
            zl = zb + (s["risers"] // 2) * s["riser"]
            (a, b) = s["run2"]
            r2 = StairsRun.CreateStraightRun(doc, sid, Line.CreateBound(P(a[0], a[1], zl), P(b[0], b[1], zl)), StairsRunJustification.Center)
            r2.ActualRunWidth = ft(s["width"])
            StairsLanding.CreateAutomaticLanding(doc, r1.Id, r2.Id)
            t.Commit()
            scope.Commit(QUIET() if QUIET else None)
            count("stairs")
        except Exception:
            fail("stairs %s-%s" % (s["base"], s["top"]))
            for closer in ("t.RollBack()", "scope.Cancel()"):
                try:
                    eval(closer)
                except Exception:
                    pass


# ------------------------------------------------------------------ 8. rooms, separation lines, tags
ROOMS = []


def make_separations():
    for sp in D["separations"]:
        try:
            z = LEVEL_Z[sp["level"]]
            plane = SketchPlane.Create(doc, LEVEL[sp["level"]].Id)
            arr = CurveArray()
            (a, b) = sp["line"]
            arr.Append(Line.CreateBound(P(a[0], a[1], z), P(b[0], b[1], z)))
            doc.Create.NewRoomBoundaryLines(plane, arr, PLAN[sp["level"]])
            count("room separation lines")
        except Exception:
            fail("separation line")


def make_rooms():
    for r in D["rooms"]:
        try:
            lv = LEVEL[r["level"]]
            room = doc.Create.NewRoom(lv, UV(ft(r["point"][0]), ft(r["point"][1])))
            room.Name = r["name"]
            room.Number = r["number"]
            param(room, BuiltInParameter.ROOM_DEPARTMENT, r["department"])
            param(room, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, r["comments"])
            param(room, BuiltInParameter.ROOM_UPPER_OFFSET, ft(r["height"]))
            ROOMS.append((room, r))
            count("rooms")
        except Exception:
            fail("room " + r["number"])


def tag_rooms():
    for room, r in ROOMS:
        try:
            doc.Create.NewRoomTag(LinkElementId(room.Id), UV(ft(r["point"][0]), ft(r["point"][1])), PLAN[r["level"]].Id)
            count("room tags")
        except Exception:
            fail("room tag " + r["number"])


def check_areas():
    off = []
    for room, r in ROOMS:
        try:
            a = room.Area * 0.3048 * 0.3048
            if a < 0.5:
                off.append("%s %s: not enclosed" % (r["number"], r["name"]))
            elif abs(a - r["area"]) > max(0.5, 0.03 * r["area"]):
                off.append("%s %s: %.1f m2 in Revit, %.1f m2 in the drawings" % (r["number"], r["name"], a, r["area"]))
        except Exception:
            pass
    if off:
        note("rooms to check: " + "; ".join(off))
    else:
        note("all room areas match the drawings")


# ------------------------------------------------------------------ 9. dimensions bound to the walls
def side_refs(wall):
    out = []
    for side in (ShellLayerType.Exterior, ShellLayerType.Interior):
        try:
            refs = HostObjectUtils.GetSideFaces(wall, side)
            if refs.Count:
                out.append(refs[0])
        except Exception:
            pass
    return out


def make_chains():
    for c in D["chains"]:
        try:
            view = PLAN[c["level"]]
            z = LEVEL_Z[c["level"]]
            hits = []
            for wid, (wall, w) in WALL.items():
                if w["level"] != c["level"]:
                    continue
                (x0, y0), (x1, y1) = w["line"]
                if c["axis"] == "H" and abs(x0 - x1) < 1e-9 and min(y0, y1) < c["at"] < max(y0, y1) and c["lo"] <= x0 <= c["hi"]:
                    hits.append((x0, wall))
                if c["axis"] == "V" and abs(y0 - y1) < 1e-9 and min(x0, x1) < c["at"] < max(x0, x1) and c["lo"] <= y0 <= c["hi"]:
                    hits.append((y0, wall))
            if len(hits) < 2:
                continue
            arr = ReferenceArray()
            for _, wall in sorted(hits, key=lambda h: h[0]):
                for ref in side_refs(wall):
                    arr.Append(ref)
            ln = Line.CreateBound(P(c["lo"], c["at"], z), P(c["hi"], c["at"], z)) if c["axis"] == "H" else \
                Line.CreateBound(P(c["at"], c["lo"], z), P(c["at"], c["hi"], z))
            doc.Create.NewDimension(view, ln, arr)
            count("dimension chains")
        except Exception:
            fail("dimension chain %s %s %.2f" % (c["level"], c["axis"], c["at"]))


MID = {}


def make_exterior_dims():
    """Along every exterior wall: its hosted windows, and the overall length between the end walls."""
    for k in ("B", "G", "F"):
        xs = [p[0] for w in D["walls"] if w["level"] == k and w["exterior"] for p in w["line"]]
        ys = [p[1] for w in D["walls"] if w["level"] == k and w["exterior"] for p in w["line"]]
        MID[k] = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2) if xs else (0.0, 0.0)
    for wid, (wall, w) in WALL.items():
        if not w["exterior"]:
            continue
        try:
            (x0, y0), (x1, y1) = w["line"]
            horiz = abs(y0 - y1) < 1e-9
            z = LEVEL_Z[w["level"]]
            ends = []
            for oid, (ow, o) in WALL.items():
                if oid == wid or o["level"] != w["level"] or not o["exterior"]:
                    continue
                (a0, b0), (a1, b1) = o["line"]
                if horiz and abs(a0 - a1) < 1e-9 and min(b0, b1) - 0.2 <= y0 <= max(b0, b1) + 0.2 and min(abs(a0 - x0), abs(a0 - x1)) < 0.05:
                    ends.append((a0, ow))
                if not horiz and abs(b0 - b1) < 1e-9 and min(a0, a1) - 0.2 <= x0 <= max(a0, a1) + 0.2 and min(abs(b0 - y0), abs(b0 - y1)) < 0.05:
                    ends.append((b0, ow))
            if len(ends) < 2:
                continue
            ends.sort(key=lambda e: e[0])
            # outward side: away from the middle of the floor
            mid_floor = MID[w["level"]]
            if horiz:
                out = 1 if y0 > mid_floor[1] else -1
            else:
                out = 1 if x0 > mid_floor[0] else -1
            for off, with_openings in ((1.2, True), (2.4, False)):
                arr = ReferenceArray()
                r_lo = [r for r in side_refs(ends[0][1])][:1]
                r_hi = [r for r in side_refs(ends[-1][1])][:1]
                for r in r_lo:
                    arr.Append(r)
                if with_openings:
                    for el in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows).WhereElementIsNotElementType().ToElements():
                        if el.Host is not None and el.Host.Id.Equals(wall.Id):
                            for rt in (FamilyInstanceReferenceType.Left, FamilyInstanceReferenceType.Right):
                                for ref in el.GetReferences(rt):
                                    arr.Append(ref)
                for r in r_hi:
                    arr.Append(r)
                if arr.Size < 2:
                    continue
                if horiz:
                    yy = y0 + out * (w["thickness"] / 2 + off)
                    ln = Line.CreateBound(P(ends[0][0], yy, z), P(ends[-1][0], yy, z))
                else:
                    xx = x0 + out * (w["thickness"] / 2 + off)
                    ln = Line.CreateBound(P(xx, ends[0][0], z), P(xx, ends[-1][0], z))
                doc.Create.NewDimension(PLAN[w["level"]], ln, arr)
                count("exterior dimensions")
        except Exception:
            fail("exterior dimension " + wid)


# ------------------------------------------------------------------ 10. sections with level dimensions
SECTIONS = {}


def make_sections():
    global SECTION_VFT
    SECTION_VFT = view_family_type(ViewFamily.Section)
    names = set(v.Name for v in FilteredElementCollector(doc).OfClass(View))
    for s in D["sections"]:
        try:
            (x0, y0), (x1, y1) = s["line"]
            L = math.hypot(x1 - x0, y1 - y0)
            d = XYZ((x1 - x0) / L, (y1 - y0) / L, 0)
            up = XYZ.BasisZ
            tr = Transform.Identity
            tr.Origin = P((x0 + x1) / 2, (y0 + y1) / 2, 0)
            tr.BasisX = d
            tr.BasisY = up
            tr.BasisZ = d.CrossProduct(up)
            box = BoundingBoxXYZ()
            box.Transform = tr
            box.Min = XYZ(-ft(L / 2), ft(s["zmin"]), -ft(25.0))
            box.Max = XYZ(ft(L / 2), ft(s["zmax"]), 0)
            v = ViewSection.CreateSection(doc, SECTION_VFT.Id, box)
            v.Name = unique_name(names, s["name"])
            v.Scale = 100
            SECTIONS[s["name"]] = v
            count("sections")
            arr = ReferenceArray()
            for k in ("B", "G", "F", "R"):
                arr.Append(LEVEL[k].GetPlaneReference())
            xa, ya = x0 + d.X * 1.0, y0 + d.Y * 1.0
            doc.Create.NewDimension(v, Line.CreateBound(P(xa, ya, LEVEL_Z["B"]), P(xa, ya, LEVEL_Z["R"])), arr)
            count("height dimensions")
        except Exception:
            fail("section " + s["name"])


# ------------------------------------------------------------------ 11. site: toposolid, plot boundary, building line, survey DWG
def make_site():
    S = D["site"]
    pts = List[XYZ]()
    for x, y, z in S["topo_points"]:
        pts.Add(P(x, y, z))
    made = False
    try:
        from Autodesk.Revit.DB import Toposolid, ToposolidType
        tt = next(iter(FilteredElementCollector(doc).OfClass(ToposolidType)), None)
        Toposolid.Create(doc, pts, tt.Id, LEVEL["G"].Id)
        count("toposolid")
        made = True
    except Exception:
        fail("toposolid")
    if not made:
        try:
            from Autodesk.Revit.DB.Architecture import TopographySurface
            TopographySurface.Create(doc, pts)
            count("topography surface")
        except Exception:
            fail("topography surface")
    plane = SketchPlane.Create(doc, LEVEL["G"].Id)
    dashed = None
    try:
        from Autodesk.Revit.DB import GraphicsStyle
        for gs in FilteredElementCollector(doc).OfClass(GraphicsStyle):
            if gs.GraphicsStyleCategory is not None and gs.GraphicsStyleCategory.Parent is not None and \
                    gs.GraphicsStyleCategory.Parent.Name == "Lines" and ("Hidden" in gs.Name or "Dash" in gs.Name):
                dashed = gs
                break
    except Exception:
        pass
    for ring, label in ((S["plot"], "plot boundary"), (S["building_line"], "building line")):
        n = len(ring)
        for i in range(n):
            try:
                a, b = ring[i], ring[(i + 1) % n]
                mc = doc.Create.NewModelCurve(Line.CreateBound(P(a[0], a[1], 0), P(b[0], b[1], 0)), plane)
                if label == "building line" and dashed is not None:
                    mc.LineStyle = dashed
                count(label + " lines")
            except Exception:
                fail(label)


def link_survey():
    if not dwg_path or not os.path.exists(str(dwg_path)):
        return
    try:
        opts = DWGImportOptions()
        opts.Placement = ImportPlacement.Shared
        opts.ThisViewOnly = False
        try:
            from Autodesk.Revit.DB import ImportUnit
            opts.Unit = ImportUnit.Meter  # the survey is in metres (Israel grid); a unitless DWG would otherwise come in as feet
        except Exception:
            note("could not set the DWG units to metres; check the scale of the linked survey")
        try:
            doc.Link(str(dwg_path), opts, PLAN["site"])
        except TypeError:
            doc.Link(str(dwg_path), opts, PLAN["site"], ElementId.InvalidElementId)
        count("linked survey DWG")
    except Exception:
        fail("link survey DWG")


# ------------------------------------------------------------------ 12. room schedule and sheets
def make_schedule():
    sch = ViewSchedule.CreateSchedule(doc, ElementId(BuiltInCategory.OST_Rooms))
    sch.Name = "טבלת חדרים ושטחים"
    d = sch.Definition
    want = [BuiltInParameter.ROOM_LEVEL_ID, BuiltInParameter.ROOM_NUMBER, BuiltInParameter.ROOM_NAME, BuiltInParameter.ROOM_DEPARTMENT,
            BuiltInParameter.ROOM_AREA]
    fields = list(d.GetSchedulableFields())
    added = {}
    for bip in want:
        for f in fields:
            if f.ParameterId.Equals(ElementId(bip)):
                added[bip] = d.AddField(f)
                break
    for bip in (BuiltInParameter.ROOM_LEVEL_ID, BuiltInParameter.ROOM_NUMBER):
        if bip in added:
            d.AddSortGroupField(ScheduleSortGroupField(added[bip].FieldId))
    count("schedules")
    return sch


def make_sheets(schedule):
    tb = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType().FirstElementId()
    if tb is None:
        tb = ElementId.InvalidElementId
    for sh in D["sheets"]:
        try:
            sheet = ViewSheet.Create(doc, tb)
            sheet.SheetNumber = sh["number"]
            sheet.Name = sh["name"]
            n = len(sh["views"])
            for i, key in enumerate(sh["views"]):
                cy = 0.30 - (i - (n - 1) / 2.0) * (0.17 if n > 1 else 0)
                where = XYZ(ft(0.40), ft(cy), 0)
                if key.startswith("schedule:"):
                    if schedule is not None:
                        ScheduleSheetInstance.Create(doc, sheet.Id, schedule.Id, XYZ(ft(0.05), ft(0.55), 0))
                    continue
                view = SECTIONS.get(key.split(":", 1)[1]) if key.startswith("section:") else PLAN.get(key)
                if view is not None and Viewport.CanAddViewToSheet(doc, sheet.Id, view.Id):
                    Viewport.Create(doc, sheet.Id, view.Id, where)
            count("sheets")
        except Exception:
            fail("sheet " + sh["number"])


# ------------------------------------------------------------------ run
transaction("levels and plan views", make_levels)
transaction("survey coordinates", set_location)
transaction("wall and floor types", make_types)
transaction("walls", make_walls)
transaction("doors and windows", make_openings)
transaction("floors and roofs", make_floors)
make_stairs()
transaction("room separation lines", make_separations)
transaction("rooms", make_rooms)
transaction("room tags", tag_rooms)
check_areas()
transaction("dimension chains", make_chains)
transaction("exterior dimensions", make_exterior_dims)
transaction("sections", make_sections)
transaction("site", make_site)
transaction("survey DWG", link_survey)
schedule = transaction("room schedule", make_schedule)
transaction("sheets", lambda: make_sheets(schedule))

lines = ["Villa 84 - Revit model built from " + os.path.basename(str(data_path)), ""]
lines += ["%-26s %d" % (k, v) for k, v in sorted(REPORT["created"].items())]
lines += [""] + ["note: " + n for n in REPORT["notes"]]
lines += [""] + (["failed: " + e for e in REPORT["errors"]] or ["no failures"])
try:
    with open(os.path.join(os.path.dirname(str(data_path)), "villa84-revit-report.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
except Exception:
    pass
OUT = lines
