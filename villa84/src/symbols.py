"""2D plan symbols (and matching 3D boxes) for furniture and fixtures. All sizes in metres.

A symbol is drawn in its own local frame and then placed with place(target, sym, x, y, rot).
Local conventions:
  * wall-backed items (sofa, wardrobe, shelf, counter, tall units, console, tv unit, bench, desk, bed, wc, basin,
    vanity, shower, bathtub, washer, nightstand, sauna, rack, cinema seat): the back touches the wall on y = 0,
    the front faces +y. Long items run along +x from x = 0, except desk, console, tv unit, bed, nightstand, wc,
    basin and cinema seat, which are centred on x = 0.
  * free items (tables, dining sets, island, rug, plant, round table, car, jacuzzi, lounger, parasol, tank, chair,
    armchair, beanbag, treadmill, bike): centred on the origin; their "front" faces +y.
"""
import math


class Canvas:
    """Collects drawing primitives (2D) and extruded footprints (3D)."""

    def __init__(self):
        self.items = []     # 2D primitives
        self.solids = []    # 3D: dict(pts=[...], z0, z1, mat, tag)

    # ---- 2D
    def poly(self, pts, layer, closed=True, fill=None, holes=None, dash=None, w=None):
        self.items.append(dict(t="poly", pts=[tuple(p) for p in pts], layer=layer, closed=closed, fill=fill,
                               holes=[[tuple(p) for p in h] for h in (holes or [])], dash=dash, w=w))

    def rect(self, x0, y0, x1, y1, layer, **kw):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer, **kw)

    def line(self, a, b, layer, dash=None, w=None):
        self.items.append(dict(t="line", a=tuple(a), b=tuple(b), layer=layer, dash=dash, w=w))

    def circle(self, c, r, layer, fill=None, dash=None):
        self.items.append(dict(t="circle", c=tuple(c), r=r, layer=layer, fill=fill, dash=dash))

    def arc(self, c, r, a0, a1, layer, dash=None):
        self.items.append(dict(t="arc", c=tuple(c), r=r, a0=a0, a1=a1, layer=layer, dash=dash))

    def text(self, p, s, layer, h=0.25, anchor="m", rot=0.0, bold=False):
        self.items.append(dict(t="text", p=tuple(p), s=s, layer=layer, h=h, anchor=anchor, rot=rot, bold=bold))

    def dim(self, a, b, axis, at, layer="DIM", h=0.2, side=1, txt=None):
        """Linear dimension between a and b measured along `axis` ('H' = X distance); dimension line at coordinate `at`.
        h = text height in metres; side = 1 puts the text above / left of the line, -1 below / right (used for wall thicknesses)."""
        self.items.append(dict(t="dim", a=tuple(a), b=tuple(b), axis=axis, at=at, layer=layer, h=h, side=side, txt=txt))

    def adim(self, a, b, layer="DIM", off=0.0, h=0.2, unit="cm"):
        """Aligned dimension from a to b; the dimension line is shifted `off` metres to the left of a->b."""
        self.items.append(dict(t="adim", a=tuple(a), b=tuple(b), layer=layer, off=off, h=h, unit=unit))

    def ellipse(self, c, rx, ry, layer, n=28, **kw):
        self.poly([(c[0] + rx * math.cos(2 * math.pi * i / n), c[1] + ry * math.sin(2 * math.pi * i / n)) for i in range(n)], layer, **kw)

    def rrect(self, x0, y0, x1, y1, r, layer, n=5, **kw):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(n + 1):
                a = math.radians(a0 + 90 * i / n)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.poly(pts, layer, **kw)

    # ---- 3D
    def box(self, x0, y0, x1, y1, z0, z1, mat, tag=""):
        self.solids.append(dict(pts=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0=z0, z1=z1, mat=mat, tag=tag))

    def cyl(self, c, r, z0, z1, mat, n=16, tag=""):
        self.solids.append(dict(pts=[(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)],
                                z0=z0, z1=z1, mat=mat, tag=tag))

    def marker(self, kind, **kw):
        """Non-geometric 3D hint (for example a car model to instance)."""
        self.solids.append(dict(marker=kind, **kw))


def _tf(p, c, s, dx, dy):
    return (p[0] * c - p[1] * s + dx, p[0] * s + p[1] * c + dy)


def place(target, sym, x, y, rot=0.0, dz=0.0):
    """Copy a symbol canvas into `target`, rotated by `rot` degrees (CCW) and moved to (x, y); 3D raised by dz."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for it in sym.items:
        it = dict(it)
        if it["t"] == "poly":
            it["pts"] = [_tf(p, c, s, x, y) for p in it["pts"]]
            it["holes"] = [[_tf(p, c, s, x, y) for p in h] for h in it["holes"]]
        elif it["t"] == "line":
            it["a"], it["b"] = _tf(it["a"], c, s, x, y), _tf(it["b"], c, s, x, y)
        elif it["t"] in ("circle", "arc"):
            it["c"] = _tf(it["c"], c, s, x, y)
            if it["t"] == "arc":
                it["a0"], it["a1"] = it["a0"] + rot, it["a1"] + rot
        elif it["t"] == "text":
            it["p"] = _tf(it["p"], c, s, x, y)
        target.items.append(it)
    for so in sym.solids:
        so = dict(so)
        if "marker" in so:
            so["p"] = _tf(so.get("p", (0, 0)), c, s, x, y)
            so["rot"] = so.get("rot", 0.0) + rot
            so["z"] = so.get("z", 0.0) + dz
        else:
            so["pts"] = [_tf(p, c, s, x, y) for p in so["pts"]]
            so["z0"], so["z1"] = so["z0"] + dz, so["z1"] + dz
        target.solids.append(so)


F, X = "FURN", "FIX"


# ------------------------------------------------------------------ seating
def chair(w=0.45, layer=F, mat="chair"):
    """Centred, the sitter faces +y (back rest on the -y side)."""
    s = Canvas()
    h = w / 2
    s.rrect(-h, -h, h, h, 0.05, layer)
    s.line((-h, -h + 0.07), (h, -h + 0.07), layer)
    s.box(-h, -h, h, h, 0.0, 0.46, mat)
    s.box(-h, -h, h, -h + 0.07, 0.46, 0.85, mat)
    return s


def armchair(w=0.85, d=0.85, mat="fabric"):
    """Centred, faces +y."""
    s = Canvas()
    x0, x1, y0, y1 = -w / 2, w / 2, -d / 2, d / 2
    s.rrect(x0, y0, x1, y1, 0.08, F)
    s.rrect(x0 + 0.14, y0 + 0.18, x1 - 0.14, y1 - 0.04, 0.06, F)
    s.box(x0, y0, x1, y1, 0.0, 0.42, mat)
    s.box(x0, y0, x1, y0 + 0.18, 0.42, 0.78, mat)
    for a, b in ((x0, x0 + 0.14), (x1 - 0.14, x1)):
        s.box(a, y0, b, y1, 0.42, 0.62, mat)
    return s


def sofa(w=2.4, d=0.95, seats=3, mat="fabric"):
    """Back on y = 0, from x = 0 to w, faces +y."""
    s = Canvas()
    s.rrect(0, 0, w, d, 0.06, F)
    s.line((0, 0.24), (w, 0.24), F)
    for i in range(1, seats):
        x = w * i / seats
        s.line((x, 0.24), (x, d), F)
    s.box(0, 0, w, d, 0.0, 0.42, mat)
    s.box(0, 0, w, 0.24, 0.42, 0.82, mat)
    return s


def chaise(w=1.05, l=2.4, mat="fabric"):
    """From x = 0 to w, y = 0 to l; back rest along x = w (the outer side)."""
    s = Canvas()
    s.rrect(0, 0, w, l, 0.06, F)
    s.line((w - 0.24, 0), (w - 0.24, l), F)
    s.box(0, 0, w, l, 0.0, 0.42, mat)
    s.box(w - 0.24, 0, w, l, 0.42, 0.66, mat)
    return s


def beanbag(r=0.42):
    s = Canvas()
    s.circle((0, 0), r, F)
    s.circle((0, 0), r * 0.55, F)
    s.cyl((0, 0), r, 0.0, 0.45, "ochre")
    return s


def bench(l=1.3, w=0.38, mat="wood"):
    """From x = 0 to l, y = 0 to w."""
    s = Canvas()
    s.rect(0, 0, l, w, F)
    s.box(0, 0, l, w, 0.0, 0.45, mat)
    return s


def cinema_seat(w=0.78, d=0.95):
    """Centred on x; back on y = 0, faces +y."""
    s = Canvas()
    s.rrect(-w / 2, 0, w / 2, d, 0.1, F)
    s.rrect(-w / 2 + 0.1, 0.22, w / 2 - 0.1, d, 0.06, F)
    s.box(-w / 2, 0, w / 2, d, 0.1, 0.45, "leather")
    s.box(-w / 2, 0, w / 2, 0.22, 0.45, 0.95, "leather")
    return s


# ------------------------------------------------------------------ tables and storage
def round_table(r=0.6, h=0.4, mat="stone", layer=F):
    s = Canvas()
    s.circle((0, 0), r, layer)
    s.cyl((0, 0), r, h - 0.04, h, mat, n=24)
    s.cyl((0, 0), 0.08, 0.0, h - 0.04, "black", n=8)
    return s


def table(w, d, h=0.75, mat="wood", layer=F):
    """Centred."""
    s = Canvas()
    s.rect(-w / 2, -d / 2, w / 2, d / 2, layer)
    s.box(-w / 2, -d / 2, w / 2, d / 2, h - 0.04, h, mat)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 0.08), sy * (d / 2 - 0.08)
            s.box(x - 0.03, y - 0.03, x + 0.03, y + 0.03, 0.0, h - 0.04, "black")
    return s


def dining(w=3.6, d=1.1, per_side=5, ends=True, mat="wood"):
    """Centred table with chairs on both long sides (and on the ends)."""
    s = table(w, d, 0.75, mat)
    for i in range(per_side):
        x = -w / 2 + w * (i + 0.5) / per_side
        place(s, chair(), x, -d / 2 - 0.18, 0)
        place(s, chair(), x, d / 2 + 0.18, 180)
    if ends:
        place(s, chair(), -w / 2 - 0.18, 0, -90)
        place(s, chair(), w / 2 + 0.18, 0, 90)
    return s


def wardrobe(length, depth=0.6, mat="wood"):
    """From x = 0 to length, back on y = 0."""
    s = Canvas()
    s.rect(0, 0, length, depth, X)
    n = max(1, round(length / 0.5))
    for i in range(n):
        x0 = length * i / n
        s.line((x0, depth), (x0 + length / n, 0.06), X, w=0.1)
    s.line((0, depth - 0.05), (length, depth - 0.05), X, dash="2 2")
    s.box(0, 0, length, depth, 0.0, 2.4, mat)
    return s


def shelf(length, depth=0.35, h=2.2, mat="wood", layer=X):
    """From x = 0 to length, back on y = 0."""
    s = Canvas()
    s.rect(0, 0, length, depth, layer)
    n = max(1, round(length / 0.9))
    for i in range(1, n):
        x = length * i / n
        s.line((x, 0), (x, depth), layer)
    s.box(0, 0, length, depth, 0.0, h, mat)
    return s


def console(w=1.6, d=0.4, h=0.8, mat="wood"):
    """Centred on x, back on y = 0."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, d, F)
    s.box(-w / 2, 0, w / 2, d, 0.0, h, mat)
    return s


def tv_unit(w=2.4, d=0.45):
    """Centred on x, back on y = 0; the screen stands on it."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, d, F)
    s.line((-w * 0.32, 0.08), (w * 0.32, 0.08), F, w=0.5)
    s.box(-w / 2, 0, w / 2, d, 0.0, 0.45, "wood")
    s.box(-w * 0.32, 0.05, w * 0.32, 0.1, 0.55, 1.35, "black")
    return s


def desk(w=1.6, d=0.75, with_chair=True, monitor=True, mat="wood"):
    """Centred on x, back on y = 0; the user sits on the +y side, facing -y."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, d, F)
    s.box(-w / 2, 0, w / 2, d, 0.71, 0.75, mat)
    s.box(-w / 2, 0, -w / 2 + 0.05, d, 0.0, 0.71, mat)
    s.box(w / 2 - 0.05, 0, w / 2, d, 0.0, 0.71, mat)
    if monitor:
        s.line((-0.3, 0.14), (0.3, 0.14), F, w=0.5)
        s.box(-0.3, 0.12, 0.3, 0.16, 0.75, 1.15, "black")
    if with_chair:
        place(s, chair(0.5, mat="chair"), 0, d + 0.3, 180)
    return s


def rug(w, d):
    """Centred."""
    s = Canvas()
    s.rect(-w / 2, -d / 2, w / 2, d / 2, "RUG", dash="4 2")
    s.box(-w / 2, -d / 2, w / 2, d / 2, 0.0, 0.015, "rug")
    return s


def plant(r=0.35):
    s = Canvas()
    s.circle((0, 0), r, "PLANT")
    for k in range(6):
        a = math.radians(k * 60 + 15)
        s.line((0, 0), (r * 0.95 * math.cos(a), r * 0.95 * math.sin(a)), "PLANT")
    s.cyl((0, 0), r * 0.45, 0.0, 0.45, "planter", n=12)
    s.cyl((0, 0), r, 0.45, 1.5, "leaf", n=10)
    return s


# ------------------------------------------------------------------ kitchen
def counter(length, depth=0.62, sink=None, hob=None, mat="stone_top"):
    """From x = 0 to length, back on y = 0. sink / hob: x of their centres."""
    s = Canvas()
    s.rect(0, 0, length, depth, X)
    if sink is not None:
        s.rrect(sink - 0.3, 0.1, sink + 0.3, depth - 0.12, 0.05, X)
        s.circle((sink, depth / 2 - 0.01), 0.03, X)
    if hob is not None:
        s.rect(hob - 0.3, 0.08, hob + 0.3, depth - 0.1, X)
        for dx in (-0.14, 0.14):
            for dy in (-0.11, 0.11):
                s.circle((hob + dx, depth / 2 + dy - 0.01), 0.07, X)
    s.box(0, 0, length, depth, 0.0, 0.86, "wood")
    s.box(0, 0, length, depth, 0.86, 0.9, mat)
    return s


def tall_units(length, depth=0.65, fridge=0.9):
    """Full-height kitchen units from x = 0 to length, the fridge at the x = 0 end."""
    s = Canvas()
    s.rect(0, 0, length, depth, X)
    s.line((fridge, 0), (fridge, depth), X)
    s.line((0, 0), (fridge, depth), X)
    s.line((0, depth), (fridge, 0), X)
    for x in (fridge + 0.6, fridge + 1.2):
        if x < length - 0.1:
            s.line((x, 0), (x, depth), X)
    s.box(0, 0, length, depth, 0.0, 2.35, "white")
    return s


def island(w=3.2, d=1.2, stools=4, sink=True):
    """Centred; stools on the +y side."""
    s = Canvas()
    s.rect(-w / 2, -d / 2, w / 2, d / 2, X)
    if sink:
        s.rrect(-w / 2 + 0.25, -d / 2 + 0.12, -w / 2 + 0.85, -d / 2 + 0.55, 0.05, X)
    s.box(-w / 2, -d / 2, w / 2, d / 2, 0.0, 0.88, "wood")
    s.box(-w / 2 - 0.02, -d / 2 - 0.02, w / 2 + 0.02, d / 2 + 0.02, 0.88, 0.92, "stone_top")
    for i in range(stools):
        x = -w / 2 + w * (i + 0.5) / stools
        s.circle((x, d / 2 + 0.3), 0.19, F)
        s.cyl((x, d / 2 + 0.3), 0.19, 0.0, 0.7, "black", n=12)
    return s


# ------------------------------------------------------------------ bedrooms
def bed(w=1.8, l=2.05, mat="linen"):
    """Centred on x, head board on y = 0."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, l, F)
    s.rect(-w / 2, 0, w / 2, 0.06, F, fill="dark")
    n = 2 if w >= 1.3 else 1
    for i in range(n):
        x0 = -w / 2 + 0.1 + i * (w - 0.2) / n
        s.rrect(x0 + 0.04, 0.12, x0 + (w - 0.2) / n - 0.04, 0.55, 0.06, F)
    s.line((-w / 2, l * 0.42), (w / 2, l * 0.42), F, dash="3 2")
    s.box(-w / 2, 0, w / 2, l, 0.0, 0.3, "wood")
    s.box(-w / 2 + 0.02, 0.06, w / 2 - 0.02, l - 0.02, 0.3, 0.55, mat)
    s.box(-w / 2, 0, w / 2, 0.06, 0.0, 1.05, "fabric")
    return s


def nightstand(w=0.5, d=0.42):
    """Centred on x, back on y = 0."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, d, F)
    s.box(-w / 2, 0, w / 2, d, 0.0, 0.5, "wood")
    return s


# ------------------------------------------------------------------ bathrooms and laundry
def wc():
    """Wall-hung toilet: centred on x, cistern on y = 0."""
    s = Canvas()
    s.rect(-0.2, 0, 0.2, 0.16, X)
    s.ellipse((0, 0.42), 0.18, 0.26, X)
    s.box(-0.18, 0.16, 0.18, 0.68, 0.2, 0.42, "white")
    s.box(-0.25, 0, 0.25, 0.16, 0.0, 1.1, "white")
    return s


def basin(w=0.6, d=0.46):
    """Centred on x, back on y = 0."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, d, X)
    s.ellipse((0, d / 2 + 0.02), w * 0.32, d * 0.3, X)
    s.box(-w / 2, 0, w / 2, d, 0.68, 0.85, "white")
    return s


def vanity(w=1.6, d=0.55, n=2):
    """From x = 0 to w, back on y = 0, n basins."""
    s = Canvas()
    s.rect(0, 0, w, d, X)
    for i in range(n):
        cx = w * (i + 0.5) / n
        s.ellipse((cx, d / 2 + 0.02), 0.2, 0.15, X)
    s.box(0, 0, w, d, 0.0, 0.85, "wood")
    s.box(0, 0, w, 0.02, 0.9, 1.9, "mirror")
    return s


def shower(w=1.0, d=1.0):
    """From x = 0 to w, y = 0 to d (tray in a corner)."""
    s = Canvas()
    s.rect(0, 0, w, d, X)
    s.line((0, 0), (w, d), X)
    s.line((0, d), (w, 0), X)
    s.circle((w / 2, d / 2), 0.04, X)
    s.box(0, 0, w, d, 0.0, 0.04, "tile")
    s.box(0, d - 0.01, w, d, 0.04, 2.1, "glass")
    return s


def bathtub(l=1.8, w=0.8):
    """From x = 0 to l, back on y = 0."""
    s = Canvas()
    s.rrect(0, 0, l, w, 0.08, X)
    s.rrect(0.08, 0.08, l - 0.08, w - 0.08, 0.2, X)
    s.circle((l - 0.25, w / 2), 0.03, X)
    s.box(0, 0, l, w, 0.0, 0.55, "white")
    return s


def washer(n=2):
    """n machines from x = 0 along +x, back on y = 0."""
    s = Canvas()
    for i in range(n):
        x0 = i * 0.62
        s.rect(x0, 0, x0 + 0.6, 0.6, X)
        s.circle((x0 + 0.3, 0.32), 0.2, X)
        s.box(x0, 0, x0 + 0.6, 0.6, 0.0, 0.85, "white")
    return s


# ------------------------------------------------------------------ garage, cinema, gym, spa, office
def car(l=4.7, w=1.95, color="car_red"):
    """Centred, nose toward +y."""
    s = Canvas()
    s.rrect(-w / 2, -l / 2, w / 2, l / 2, 0.42, "CAR")
    s.rrect(-w / 2 + 0.16, -l / 2 + 0.95, w / 2 - 0.16, l / 2 - 1.35, 0.3, "CAR")
    s.line((-w / 2 + 0.2, l / 2 - 1.35), (w / 2 - 0.2, l / 2 - 1.35), "CAR")
    for sx in (-1, 1):
        s.rect(sx * (w / 2) - 0.05 * (sx > 0) - 0.05 * (sx < 0), l / 2 - 1.55, sx * (w / 2) + 0.12 * sx, l / 2 - 1.35, "CAR")
    s.marker("car", p=(0, 0), rot=0.0, z=0.0, color=color)
    return s


def treadmill():
    """Centred, the runner faces +y."""
    s = Canvas()
    s.rrect(-0.42, -1.0, 0.42, 1.0, 0.08, F)
    s.rect(-0.3, -0.9, 0.3, 0.6, F)
    s.rect(-0.42, 0.75, 0.42, 1.0, F, fill="dark")
    s.box(-0.42, -1.0, 0.42, 1.0, 0.0, 0.22, "black")
    s.box(-0.42, 0.75, 0.42, 1.0, 0.22, 1.35, "black")
    return s


def bike():
    """Centred, faces +y."""
    s = Canvas()
    s.rrect(-0.28, -0.65, 0.28, 0.65, 0.08, F)
    s.line((0, -0.6), (0, 0.6), F)
    s.box(-0.28, -0.65, 0.28, 0.65, 0.0, 1.05, "black")
    return s


def rack(l=1.4, d=0.45):
    """From x = 0 to l, back on y = 0 (dumbbell rack)."""
    s = Canvas()
    s.rect(0, 0, l, d, F)
    n = int(l / 0.22)
    for i in range(n):
        s.circle((0.12 + i * (l - 0.24) / max(n - 1, 1), d / 2), 0.07, F)
    s.box(0, 0, l, d, 0.0, 0.9, "grey")
    return s


def jacuzzi(w=2.2):
    """Centred square spa."""
    s = Canvas()
    s.rrect(-w / 2, -w / 2, w / 2, w / 2, 0.2, X)
    s.rrect(-w / 2 + 0.15, -w / 2 + 0.15, w / 2 - 0.15, w / 2 - 0.15, 0.35, "WATER", fill="water")
    for sx in (-1, 1):
        for sy in (-1, 1):
            s.circle((sx * w * 0.3, sy * w * 0.3), 0.06, X)
    s.box(-w / 2, -w / 2, w / 2, w / 2, 0.0, 0.75, "tile")
    s.box(-w / 2 + 0.15, -w / 2 + 0.15, w / 2 - 0.15, w / 2 - 0.15, 0.75, 0.78, "water")
    return s


def sauna(w, d):
    """Sauna cabin from x = 0 to w, y = 0 to d, two-level bench along the y = 0 and x = 0 walls, heater opposite."""
    s = Canvas()
    s.rect(0, 0, w, d, X)
    for k, depth in enumerate((0.5, 0.95)):
        s.line((0, depth), (w, depth), X)
    s.rect(w - 0.45, d - 0.45, w - 0.05, d - 0.05, X, fill="dark")
    s.box(0, 0, w, 0.5, 0.0, 0.85, "sauna")
    s.box(0, 0.5, w, 0.95, 0.0, 0.45, "sauna")
    s.box(w - 0.45, d - 0.45, w - 0.05, d - 0.05, 0.0, 0.7, "black")
    return s


def lounger(w=0.7, l=1.95):
    """Centred, head toward +y."""
    s = Canvas()
    s.rect(-w / 2, -l / 2, w / 2, l / 2, F)
    s.line((-w / 2, l / 2 - 0.6), (w / 2, l / 2 - 0.6), F)
    s.box(-w / 2, -l / 2, w / 2, l / 2, 0.0, 0.32, "white")
    s.box(-w / 2, l / 2 - 0.6, w / 2, l / 2, 0.32, 0.6, "white")
    return s


def parasol(r=1.4):
    s = Canvas()
    s.circle((0, 0), r, "OUT", dash="4 2")
    for k in range(8):
        a = math.radians(k * 45)
        s.line((0, 0), (r * math.cos(a), r * math.sin(a)), "OUT", dash="2 2")
    s.cyl((0, 0), 0.03, 0.0, 2.3, "black", n=6)
    s.cyl((0, 0), r, 2.3, 2.36, "white", n=12)
    return s


def tank(r=0.45):
    """Pump, filter or water heater."""
    s = Canvas()
    s.circle((0, 0), r, X)
    s.circle((0, 0), r * 0.45, X)
    s.cyl((0, 0), r, 0.0, 1.4, "grey", n=16)
    return s


def plotter(w=1.4, d=0.6):
    """Office plotter / printer: centred on x, back on y = 0."""
    s = Canvas()
    s.rect(-w / 2, 0, w / 2, d, X)
    s.line((-w / 2, d * 0.55), (w / 2, d * 0.55), X)
    s.box(-w / 2, 0, w / 2, d, 0.0, 1.05, "grey")
    return s
