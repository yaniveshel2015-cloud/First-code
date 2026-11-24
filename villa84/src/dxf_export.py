"""Export the drawing canvases to DXF for AutoCAD.

Files written to the output folder:
  villa84-all-drawings.dxf   every drawing side by side, centimetres
  villa84-floor-B/G/F.dxf    one file per floor (walls, openings, fixtures, furniture on its own layers), centimetres
  villa84-site-survey-grid.dxf   site plan in the surveyor's grid coordinates, metres (overlays the measurement file)
The painter's-order fills of the PDF sheets are resolved into real geometry (hidden lines removed), so the DXF looks like the PDF.
"""
import math
import os
import sys

import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box as sbox

import draw as D
import model as M
import section as SEC
from symbols import Canvas

OUT_DIR = sys.argv[1]

LAYER = {  # canvas layer: (DXF layer, ACI colour, linetype, lineweight 1/100 mm)
    "WALL": ("A-WALL", 7, "CONTINUOUS", 50), "GLASS": ("A-GLAZ", 5, "CONTINUOUS", 18), "DOOR": ("A-DOOR", 2, "CONTINUOUS", 25),
    "DOOR-T": ("A-DOOR-SILL", 8, "CONTINUOUS", 13), "STAIR": ("A-STAIR", 6, "CONTINUOUS", 18), "FIX": ("A-FIXTURE", 8, "CONTINUOUS", 18),
    "FURN": ("I-FURN", 30, "CONTINUOUS", 18), "CAR": ("I-FURN-CARS", 9, "CONTINUOUS", 18), "RUG": ("I-FURN-RUGS", 9, "DASHED", 13),
    "PLANT": ("I-FURN-PLANTS", 3, "CONTINUOUS", 13), "OUT": ("L-SITE-FURN", 8, "CONTINUOUS", 13), "PARK": ("A-PARKING", 1, "CONTINUOUS", 18),
    "TEXT": ("A-TEXT-ROOMS", 7, "CONTINUOUS", 18), "TEXT-S": ("A-TEXT-NOTES", 7, "CONTINUOUS", 13), "LEVEL": ("A-LEVELS", 1, "CONTINUOUS", 13),
    "DIM": ("A-DIMS", 5, "CONTINUOUS", 13), "PLOT": ("C-PLOT-BOUNDARY", 1, "DASHDOT", 50), "BLINE": ("C-BUILDING-LINE", 6, "DASHED", 30),
    "PAVE": ("L-PAVING", 8, "CONTINUOUS", 13), "GREEN": ("L-PLANTING", 3, "CONTINUOUS", 13), "WATER": ("L-POOL", 4, "CONTINUOUS", 25),
    "ROOF": ("A-ROOF", 7, "CONTINUOUS", 30), "BELOW": ("A-BELOW", 8, "DASHED", 13), "CEIL": ("A-CEILING-PROJECTOR", 6, "DASHED", 25),
    "CUT": ("A-SECTION-MARKS", 7, "DASHDOT", 50), "SURVEY": ("V-SURVEY", 9, "CONTINUOUS", 9), "SURV-LOT": ("V-SURVEY-LOTS", 8, "CONTINUOUS", 18),
    "TOPO": ("V-TOPO-MINOR", 43, "CONTINUOUS", 9), "TOPO-M": ("V-TOPO-MAJOR", 42, "CONTINUOUS", 25), "TOPO-T": ("V-TOPO-TEXT", 42, "CONTINUOUS", 13),
    "SPOT": ("V-SPOT-HEIGHTS", 8, "CONTINUOUS", 9), "TREE": ("L-TREES", 3, "CONTINUOUS", 13), "EARTH": ("S-EARTH", 43, "CONTINUOUS", 18),
    "SEC-CUT": ("S-CUT", 7, "CONTINUOUS", 40), "SEC-VIEW": ("S-BEYOND", 8, "CONTINUOUS", 13), "NATURAL": ("S-NATURAL-GROUND", 42, "DASHED", 25),
    "SETBACK": ("C-SETBACK-DIMS", 6, "CONTINUOUS", 18), "UTIL": ("U-PILLARS", 30, "CONTINUOUS", 30), "UTIL-T": ("U-PILLARS-TEXT", 30, "CONTINUOUS", 13),
}
FILL = {  # fill name: (hatch layer, RGB); None = opaque eraser only (white)
    "wall": ("A-WALL-HATCH", (71, 71, 71)), "slab": ("S-CUT-HATCH", (106, 106, 106)), "dark": ("A-SYMBOL-HATCH", (51, 51, 51)),
    "water": ("L-POOL-HATCH", (191, 227, 242)), "deck": ("L-DECK-HATCH", (234, 217, 192)), "pave": ("L-PAVING-HATCH", (233, 230, 223)),
    "green": ("L-PLANTING-HATCH", (207, 226, 192)), "roof": ("A-ROOF-GREEN-HATCH", (223, 232, 212)), "roof2": ("A-ROOF-HATCH", (241, 239, 233)),
    "tree": ("L-TREES-HATCH", (200, 221, 181)), "tree2": ("L-TREES-HATCH", (159, 191, 143)), "earth": ("S-EARTH-HATCH", (233, 223, 205)),
    "glass": ("A-GLAZ-HATCH", (214, 233, 245)), "util": ("U-PILLARS-HATCH", (253, 227, 200)), "white": None, "room": None, "sky": None,
}
SEE_THROUGH = {"tree", "tree2"}


class TF:
    """Design metres -> drawing units. Local: scale and shift. World: the surveyor's grid, metres."""

    def __init__(self, ox=0.0, oy=0.0, k=100.0, world=False):
        self.ox, self.oy, self.k, self.world = ox, oy, k, world
        S = M.SITE
        self.o, self.xh, self.yh, self.yoff = S["origin_world"], S["xh"], S["yh"], S["y_offset"]
        self.ang = math.degrees(math.atan2(self.xh[1], self.xh[0])) if world else 0.0

    def pt(self, p):
        if self.world:
            x, y = p[0], p[1] - self.yoff
            return (self.o[0] + x * self.xh[0] + y * self.yh[0], self.o[1] + x * self.xh[1] + y * self.yh[1])
        return (self.ox + p[0] * self.k, self.oy + p[1] * self.k)


def new_doc(units_cm=True):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 5 if units_cm else 6
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 40.0 if units_cm else 0.6
    doc.header["$LUNITS"] = 2
    doc.header["$LUPREC"] = 1 if units_cm else 3
    doc.styles.add("HEB", font="arial.ttf")
    doc.styles.add("HEB-BOLD", font="arialbd.ttf")
    for name, aci, lt, lw in LAYER.values():
        if name not in doc.layers:
            doc.layers.add(name, color=aci, linetype=lt, lineweight=lw)
    for v in FILL.values():
        if v and v[0] not in doc.layers:
            lay = doc.layers.add(v[0], color=8)
            lay.rgb = v[1]
    doc.layers.add("A-TITLES", color=7)
    doc.layers.add("X-FRAMES", color=9)
    k = 100.0 if units_cm else 1.0
    base = dict(dimtxsty="HEB", dimtad=1, dimtih=0, dimtoh=0, dimclrd=5, dimclre=5, dimclrt=5, dimscale=1.0, dimblk="OBLIQUE", dimtsz=0.0, dimzin=8)
    st = doc.dimstyles.new("V84-PLAN", dxfattribs=dict(base, dimtxt=0.2 * k, dimasz=0.14 * k, dimexe=0.1 * k, dimexo=0.2 * k, dimgap=0.06 * k,
                                                         dimdec=0 if units_cm else 2, dimlfac=1.0 if units_cm else 100.0))
    st = doc.dimstyles.new("V84-SITE", dxfattribs=dict(base, dimtxt=0.42 * k, dimasz=0.3 * k, dimexe=0.2 * k, dimexo=0.2 * k, dimgap=0.12 * k,
                                                         dimdec=2, dimlfac=0.01 if units_cm else 1.0, dimclrd=6, dimclre=6, dimclrt=6))
    return doc


def pieces(g):
    if g.is_empty:
        return []
    if g.geom_type in ("LineString", "LinearRing"):
        return [g]
    if g.geom_type == "Polygon":
        return []
    return [q for part in g.geoms for q in pieces(part)]


def polygons(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    if g.geom_type in ("MultiPolygon", "GeometryCollection"):
        return [q for part in g.geoms for q in polygons(part)]
    return []


def emit(canvas, msp, tf, text_k=1.0, clip=None, dimstyle="V84-PLAN"):
    rank = {l: i for i, l in enumerate(D.ORDER)}
    items = sorted(enumerate(canvas.items), key=lambda t: (rank.get(t[1]["layer"], 50), t[0]))
    cover = cover_in = None
    hatches, strokes, annos = [], [], []
    for _, it in reversed(items):                       # top-most first: everything already seen hides what comes next
        t = it["t"]
        if t in ("text", "dim", "adim"):
            annos.append(it)
            continue
        native = None
        region = None
        if t == "poly":
            pts = it["pts"]
            if it["closed"] and len(pts) >= 3:
                rings = [LineString(pts + [pts[0]])] + [LineString(h + [h[0]]) for h in it["holes"] if len(h) >= 3]
                g = MultiLineString(rings)
                if it.get("fill"):
                    region = Polygon(pts, [h for h in it["holes"] if len(h) >= 3]).buffer(0)
            elif len(pts) >= 2:
                g = LineString(pts)
            else:
                continue
        elif t == "line":
            if math.dist(it["a"], it["b"]) < 1e-9:
                continue
            g = LineString([it["a"], it["b"]])
        elif t == "circle":
            disc = Point(it["c"]).buffer(it["r"], 24)
            g = LineString(disc.exterior.coords)
            native = ("circle", it["c"], it["r"])
            if it.get("fill"):
                region = disc
        elif t == "arc":
            n = max(6, int(abs(it["a1"] - it["a0"]) / 6))
            g = LineString([(it["c"][0] + it["r"] * math.cos(math.radians(it["a0"] + (it["a1"] - it["a0"]) * i / n)),
                             it["c"][1] + it["r"] * math.sin(math.radians(it["a0"] + (it["a1"] - it["a0"]) * i / n))) for i in range(n + 1)])
            native = ("arc", it["c"], it["r"], it["a0"], it["a1"])
        else:
            continue
        if clip is not None and not clip.contains(g):
            g = g.intersection(clip)
            native = None
            if region is not None:
                region = region.intersection(clip)
        vis = g
        if it["layer"] not in ("PLOT", "BLINE", "CUT") and cover_in is not None and not g.is_empty and g.intersects(cover_in):
            vis = g.difference(cover_in)
            native = None
        if not vis.is_empty:
            strokes.append((it, vis, native))
        fill = it.get("fill")
        if region is not None and not region.is_empty and fill in FILL:
            if FILL[fill]:
                visf = region if cover is None else region.difference(cover)
                if not visf.is_empty:
                    hatches.append((fill, visf))
            if fill not in SEE_THROUGH:
                cover = region if cover is None else cover.union(region)
                cover_in = cover.buffer(-1e-4)
    for fill, g in reversed(hatches):
        lay, rgb = FILL[fill]
        for p in polygons(g):
            if p.area < 1e-5:
                continue
            h = msp.add_hatch(color=256, dxfattribs={"layer": lay})
            h.rgb = rgb
            h.paths.add_polyline_path([tf.pt(q) for q in p.exterior.coords[:-1]], is_closed=True, flags=ezdxf.const.BOUNDARY_PATH_EXTERNAL)
            for r in p.interiors:
                h.paths.add_polyline_path([tf.pt(q) for q in r.coords[:-1]], is_closed=True, flags=ezdxf.const.BOUNDARY_PATH_DEFAULT)
    for it, g, native in reversed(strokes):
        lay, _, lt, _ = LAYER.get(it["layer"], ("0", 7, "CONTINUOUS", 13))
        att = {"layer": lay}
        if it.get("dash"):
            att["linetype"] = "DASHDOT" if len(it["dash"].split()) >= 4 else "DASHED"
        if native and native[0] == "circle":
            msp.add_circle(tf.pt(native[1]), native[2] * tf.k if not tf.world else native[2], dxfattribs=att)
            continue
        if native and native[0] == "arc":
            msp.add_arc(tf.pt(native[1]), native[2] * tf.k if not tf.world else native[2], native[3] + tf.ang, native[4] + tf.ang, dxfattribs=att)
            continue
        for ls in pieces(g):
            cs = list(ls.coords)
            closed = len(cs) > 3 and math.dist(cs[0], cs[-1]) < 1e-9
            if it["layer"] in ("PLOT", "BLINE") and closed:
                att = dict(att, const_width=0.0)
            if len(cs) == 2:
                msp.add_line(tf.pt(cs[0]), tf.pt(cs[1]), dxfattribs=att)
            else:
                msp.add_lwpolyline([tf.pt(q) for q in (cs[:-1] if closed else cs)], close=closed, dxfattribs=att)
    ku = 1.0 if tf.world else tf.k
    for it in reversed(annos):
        lay = LAYER.get(it["layer"], ("0", 7, "CONTINUOUS", 13))[0]
        if clip is not None and not clip.contains(Point(it.get("p") or it["a"])):
            continue
        if it["t"] == "text":
            al = {"m": TextEntityAlignment.MIDDLE_CENTER, "l": TextEntityAlignment.MIDDLE_LEFT, "r": TextEntityAlignment.MIDDLE_RIGHT}[it.get("anchor", "m")]
            msp.add_text(it["s"], height=it["h"] * ku * text_k,
                         dxfattribs={"layer": lay, "style": "HEB-BOLD" if it.get("bold") else "HEB", "rotation": (it.get("rot") or 0.0) + tf.ang}
                         ).set_placement(tf.pt(it["p"]), align=al)
        elif it["t"] == "dim":
            a, b, at = it["a"], it["b"], it["at"]
            if it["axis"] == "H":
                base, ang = ((a[0] + b[0]) / 2, at), 0.0
            else:
                base, ang = (at, (a[1] + b[1]) / 2), 90.0
            hh = it.get("h", 0.2) * ku
            ov = {"dimtxt": hh, "dimasz": hh * 0.7, "dimgap": hh * 0.3, "dimtad": 1 if it.get("side", 1) > 0 else 4}
            if abs(a[0] - b[0]) < 1e-9 and it["axis"] == "H" or abs(a[1] - b[1]) < 1e-9 and it["axis"] == "V":
                continue
            if it["axis"] == "H" and abs(a[1] - at) < 1e-9 or it["axis"] == "V" and abs(a[0] - at) < 1e-9:
                ov["dimexe"], ov["dimexo"] = hh * 0.3, 0.0          # interior chain: the line sits on the measured points
            msp.add_linear_dim(base=tf.pt(base), p1=tf.pt(a), p2=tf.pt(b), angle=ang + tf.ang, dimstyle=dimstyle, override=ov,
                               dxfattribs={"layer": lay}).render()
        else:
            msp.add_aligned_dim(p1=tf.pt(it["a"]), p2=tf.pt(it["b"]), distance=it["off"] * ku, dimstyle="V84-SITE" if it["unit"] == "m" else dimstyle,
                                dxfattribs={"layer": lay}).render()


def title(msp, tf, p, text, sub=""):
    msp.add_text(text, height=0.9 * tf.k, dxfattribs={"layer": "A-TITLES", "style": "HEB-BOLD"}).set_placement(tf.pt(p), align=TextEntityAlignment.MIDDLE_RIGHT)
    if sub:
        msp.add_text(sub, height=0.45 * tf.k, dxfattribs={"layer": "A-TITLES", "style": "HEB"}).set_placement(tf.pt((p[0], p[1] - 1.3)), align=TextEntityAlignment.MIDDLE_RIGHT)


def frame(msp, tf, x0, y0, x1, y1):
    msp.add_lwpolyline([tf.pt(q) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))], close=True, dxfattribs={"layer": "X-FRAMES"})


def floor_full(fl):
    """Architectural plan plus loose furniture on its own layers, for the per-floor files."""
    c = D.floor_canvas(fl, "arch")
    f = Canvas()
    D.furniture(f, fl)
    c.items += [it for it in f.items if it["layer"] in ("FURN", "RUG", "PLANT", "CAR")]
    return c


def save(doc, name):
    path = os.path.join(OUT_DIR, name)
    doc.saveas(path)
    chk = ezdxf.readfile(path)
    aud = chk.audit()
    kinds = {}
    for e in chk.modelspace():
        kinds[e.dxftype()] = kinds.get(e.dxftype(), 0) + 1
    print(f"{name}: {os.path.getsize(path) / 1024:.0f} KB, audit errors {len(aud.errors)}, fixes {len(aud.fixes)}, {kinds}")


SITE_WIN = (-14.0, -10.0, 68.0, 48.0)
PLAN_WIN = (-2.4, -1.6, 59.5, 39.4)
NAMES = {"B": "קומת מרתף", "G": "קומת קרקע", "F": "קומה א׳"}

# ---------------------------------------------------------------- all drawings, centimetres
doc = new_doc(True)
msp = doc.modelspace()
tf = TF(0, 0, 100.0)
emit(D.site_canvas(), msp, tf, clip=sbox(*SITE_WIN), dimstyle="V84-SITE")
title(msp, tf, (68.0, 50.5), "תוכנית מגרש והעמדה · מגרש 84", "קנה מידה להדפסה 1:200 · יחידות השרטוט: ס״מ")
frame(msp, tf, *SITE_WIN)
for row, (mode, mname) in enumerate((("arch", "תוכנית אדריכלית"), ("furn", "תוכנית העמדה וריהוט"))):
    for i, fl in enumerate("BGF"):
        t2 = TF((90.0 + i * 68.0) * 100, (4.0 - row * 50.0) * 100, 100.0)
        emit(D.floor_canvas(fl, mode), msp, t2, text_k=1.25)
        title(msp, t2, (59.5, 42.0), f"{NAMES[fl]} · {mname}", "קנה מידה להדפסה 1:100 · המידות בס״מ")
        frame(msp, t2, *PLAN_WIN)
for i, (cut, name) in enumerate((("A", "חתך א–א · לאורך המגרש"), ("B", "חתך ב–ב · דרך החניון והמשרד"), ("C", "חתך ג–ג · דרך המדרגות"))):
    cc = SEC.CUTS[cut]
    t2 = TF(0, (-24.0 - i * 21.0) * 100, 100.0)
    emit(SEC.section(cut), msp, t2, text_k=1.25)
    title(msp, t2, (cc["hi"], 11.2), name, "קנה מידה להדפסה 1:100")
    frame(msp, t2, cc["lo"], -5.4, cc["hi"], 9.2)
save(doc, "villa84-all-drawings.dxf")

# ---------------------------------------------------------------- one file per floor, centimetres, shared origin
for fl in "BGF":
    doc = new_doc(True)
    msp = doc.modelspace()
    tf = TF(0, 0, 100.0)
    emit(floor_full(fl), msp, tf, text_k=1.25)
    title(msp, tf, (59.5, 42.0), f"{NAMES[fl]} · תוכנית אדריכלית וריהוט", "קנה מידה להדפסה 1:100 · הריהוט בשכבות I-FURN")
    save(doc, f"villa84-floor-{fl}.dxf")

# ---------------------------------------------------------------- site plan on the surveyor's grid, metres
doc = new_doc(False)
msp = doc.modelspace()
emit(D.site_canvas(), msp, TF(world=True), clip=sbox(-30.0, -25.0, 85.0, 62.0), dimstyle="V84-SITE")
save(doc, "villa84-site-survey-grid.dxf")
