"""Render the drawing canvases to A1 sheets (HTML + SVG, millimetre units -> true-scale PDF)."""
import html
import math
import re
import sys

import draw as D
import model as M
import section as SEC

OUT = sys.argv[1]
W_MM, H_MM = 841.0, 594.0
PANEL = 196.0

STYLE = {  # layer: (stroke, width mm)
    "WALL": ("#111", 0.35), "GLASS": ("#1d5fa8", 0.2), "DOOR": ("#111", 0.25), "DOOR-T": ("#777", 0.12),
    "STAIR": ("#333", 0.18), "FIX": ("#333", 0.2), "FURN": ("#6b4a2b", 0.18), "CAR": ("#555", 0.2), "RUG": ("#999", 0.12),
    "PLANT": ("#3d7a3d", 0.15), "OUT": ("#777", 0.15), "PARK": ("#b03a2e", 0.2), "TEXT": ("#111", 0), "TEXT-S": ("#333", 0),
    "LEVEL": ("#b03a2e", 0.15), "DIM": ("#1d5fa8", 0.15), "PLOT": ("#c0392b", 0.5), "BLINE": ("#b5179e", 0.3),
    "PAVE": ("#999", 0.15), "GREEN": ("#6a9955", 0.15), "WATER": ("#2980b9", 0.25), "ROOF": ("#555", 0.3),
    "BELOW": ("#999", 0.15), "CEIL": ("#7a4fa3", 0.25), "CUT": ("#111", 0.5), "SURVEY": ("#bdbdbd", 0.12),
    "SURV-LOT": ("#7c7c7c", 0.22), "TOPO": ("#cbb994", 0.12), "TOPO-M": ("#a8936d", 0.25), "TOPO-T": ("#8a7550", 0),
    "SPOT": ("#555", 0.1), "TREE": ("#5b8a4a", 0.15), "EARTH": ("#8a7550", 0.2), "SEC-CUT": ("#111", 0.4),
    "SEC-VIEW": ("#666", 0.15), "NATURAL": ("#8a7550", 0.25), "SETBACK": ("#b5179e", 0.2), "UTIL": ("#c2410c", 0.25), "UTIL-T": ("#9a3412", 0),
}
FILL = {"wall": "#474747", "white": "#fff", "dark": "#333", "water": "#bfe3f2", "deck": "#ead9c0", "pave": "#e9e6df",
        "green": "#cfe2c0", "roof": "#dfe8d4", "roof2": "#f1efe9", "tree": "#c8ddb5", "tree2": "#9fbf8f",
        "earth": "#e9dfcd", "slab": "#6a6a6a", "room": "#fff", "glass": "#d6e9f5", "sky": "#fff", "util": "#fde3c8"}


def esc(s):
    return html.escape(str(s), quote=False)


HEB = re.compile("[\u0590-\u05FF]")
SIGNED = re.compile(r"\(?[+\-−±]\d[\d.,]*\)?|\d[\d.]*\s*[×x]\s*\d[\d.]*")


def bidi(s):
    """Keep signed numbers left-to-right inside Hebrew text (isolates), so +87.50 does not turn into 87.50+."""
    return SIGNED.sub(lambda m: "\u2066" + m.group(0) + "\u2069", s)


def text_el(x, y, size, s, col, anchor="m", rot=0.0, bold=False):
    heb = bool(HEB.search(s))
    ta = {"m": "middle", "l": "end" if heb else "start", "r": "start" if heb else "end"}[anchor]
    r = f' transform="rotate({-rot:.1f} {x:.2f} {y:.2f})"' if rot else ""
    wgt = ' font-weight="700"' if bold else ""
    return (f'<text class="{"t" if heb else "n"}" x="{x:.2f}" y="{y + size * 0.36:.2f}" font-size="{size:.2f}" text-anchor="{ta}" fill="{col}" stroke-width="{min(1.0, size * 0.2):.2f}"{wgt}{r}>'
            f'{esc(bidi(s) if heb else s)}</text>')


class View:
    """Maps design metres to sheet millimetres (y up in the model, y down on the sheet)."""

    def __init__(self, x0, y0, x1, y1, scale, left, top):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.k = 1000.0 / scale
        self.left, self.top = left, top
        self.w, self.h = (x1 - x0) * self.k, (y1 - y0) * self.k

    def pt(self, p):
        return (self.left + (p[0] - self.x0) * self.k, self.top + (self.y1 - p[1]) * self.k)


def dash_attr(d, k):
    if not d:
        return ""
    return ' stroke-dasharray="' + " ".join(f"{float(v) * 0.5:.2f}" for v in d.split()) + '"'


def render(canvas, v, text_k=1.0, clip_id=None):
    out = []
    order = D.ORDER
    rank = {l: i for i, l in enumerate(order)}
    items = sorted(enumerate(canvas.items), key=lambda t: (rank.get(t[1]["layer"], 50), t[0]))
    for _, it in items:
        col, lw = STYLE.get(it["layer"], ("#000", 0.2))
        lw = it.get("w") or lw
        t = it["t"]
        if t == "poly":
            pts = [v.pt(p) for p in it["pts"]]
            d = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + (" Z" if it["closed"] else "")
            for hole in it.get("holes") or []:
                hp = [v.pt(p) for p in hole]
                d += " M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in hp) + " Z"
            fill = FILL.get(it.get("fill"), "none") if it.get("fill") else "none"
            op = ' fill-opacity="0.75"' if it.get("fill") in ("tree", "tree2") else ""
            out.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd"{op} stroke="{col}" stroke-width="{lw}" stroke-linejoin="round"{dash_attr(it.get("dash"), v.k)}/>')
        elif t == "line":
            (x1, y1), (x2, y2) = v.pt(it["a"]), v.pt(it["b"])
            out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{lw}"{dash_attr(it.get("dash"), v.k)}/>')
        elif t == "circle":
            x, y = v.pt(it["c"])
            fill = FILL.get(it.get("fill"), "none") if it.get("fill") else "none"
            op = ' fill-opacity="0.75"' if it.get("fill") in ("tree", "tree2") else ""
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{it["r"] * v.k:.2f}" fill="{fill}"{op} stroke="{col}" stroke-width="{lw}"{dash_attr(it.get("dash"), v.k)}/>')
        elif t == "arc":
            cx, cy = it["c"]
            r = it["r"]
            a0, a1 = math.radians(it["a0"]), math.radians(it["a1"])
            p0 = v.pt((cx + r * math.cos(a0), cy + r * math.sin(a0)))
            p1 = v.pt((cx + r * math.cos(a1), cy + r * math.sin(a1)))
            large = 1 if (it["a1"] - it["a0"]) % 360 > 180 else 0
            out.append(f'<path d="M{p0[0]:.2f},{p0[1]:.2f} A{r * v.k:.2f},{r * v.k:.2f} 0 {large} 0 {p1[0]:.2f},{p1[1]:.2f}" fill="none" stroke="{col}" stroke-width="{max(lw * 0.6, 0.1)}"/>')
        elif t == "text":
            x, y = v.pt(it["p"])
            out.append(text_el(x, y, it["h"] * v.k * text_k, it["s"], col, it.get("anchor", "m"), it.get("rot") or 0.0, it.get("bold")))
        elif t == "adim":
            (xa, ya), (xb, yb) = it["a"], it["b"]
            L = math.hypot(xb - xa, yb - ya)
            ux, uy = (xb - xa) / L, (yb - ya) / L
            nx, ny = -uy, ux
            o = it["off"]
            p, q = (xa + nx * o, ya + ny * o), (xb + nx * o, yb + ny * o)
            segs = [(p, q)]
            if abs(o) > 1e-6:
                segs += [((xa, ya), (p[0] + nx * 0.15, p[1] + ny * 0.15)), ((xb, yb), (q[0] + nx * 0.15, q[1] + ny * 0.15))]
            for a, b in segs:
                (x1, y1), (x2, y2) = v.pt(a), v.pt(b)
                out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{lw}"/>')
            tk = it["h"] * 0.45
            for e in (p, q):
                (x1, y1), (x2, y2) = v.pt((e[0] + (ux + nx) * tk, e[1] + (uy + ny) * tk)), v.pt((e[0] - (ux + nx) * tk, e[1] - (uy + ny) * tk))
                out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="0.3"/>')
            ang = math.degrees(math.atan2(uy, ux))
            if ang > 90 or ang <= -90:
                ang += 180
                nx, ny = -nx, -ny
            sgn = 1 if (nx * -math.sin(math.radians(ang)) + ny * math.cos(math.radians(ang))) > 0 else -1
            tx, ty = (p[0] + q[0]) / 2 + nx * sgn * it["h"] * 0.9, (p[1] + q[1]) / 2 + ny * sgn * it["h"] * 0.9
            x, y = v.pt((tx, ty))
            val = f"{L:.2f}" if it["unit"] == "m" else f"{L * 100:.0f}"
            out.append(text_el(x, y, it["h"] * v.k * text_k, val, col, "m", ang, True))
        elif t == "dim":
            (xa, ya), (xb, yb), at = it["a"], it["b"], it["at"]
            he = it.get("h", 0.2) * text_k                      # effective text height in model metres
            g1, g2 = 1.0 * he, 0.72 * he                        # gap from the measured point, overshoot past the line
            if it["axis"] == "H":
                p, q = (xa, at), (xb, at)
                e1 = ((xa, ya + (g1 if at > ya else -g1)), (xa, at + (g2 if at > ya else -g2)))
                e2 = ((xb, yb + (g1 if at > yb else -g1)), (xb, at + (g2 if at > yb else -g2)))
                val, tp, rot = abs(xb - xa), ((xa + xb) / 2, at + (0.9 * he if it.get("side", 1) > 0 else -1.45 * he)), 0
            else:
                p, q = (at, ya), (at, yb)
                e1 = ((xa + (g1 if at > xa else -g1), ya), (at + (g2 if at > xa else -g2), ya))
                e2 = ((xb + (g1 if at > xb else -g1), yb), (at + (g2 if at > xb else -g2), yb))
                val, tp, rot = abs(yb - ya), (at - (0.9 * he if it.get("side", 1) > 0 else -1.45 * he), (ya + yb) / 2), 90
            for a, b in (e1, e2, (p, q)):
                (x1, y1), (x2, y2) = v.pt(a), v.pt(b)
                out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{lw}"/>')
            for e in (p, q):
                x, y = v.pt(e)
                tk = 0.9 if it.get("h", 0.2) >= 0.15 else 0.55
                out.append(f'<line x1="{x - tk:.2f}" y1="{y + tk:.2f}" x2="{x + tk:.2f}" y2="{y - tk:.2f}" stroke="{col}" stroke-width="0.3"/>')
            x, y = v.pt(tp)
            size = it.get("h", 0.2) * v.k * text_k
            r = f' transform="rotate(-90 {x:.2f} {y:.2f})"' if rot else ""
            out.append(f'<text class="n" x="{x:.2f}" y="{y:.2f}" font-size="{size:.2f}" text-anchor="middle" fill="{col}" stroke-width="{min(1.0, size * 0.2):.2f}"{r}>{it.get("txt") or f"{val * 100:.0f}"}</text>')
    g = "".join(out)
    if clip_id:
        return (f'<clipPath id="{clip_id}"><rect x="{v.left:.2f}" y="{v.top:.2f}" width="{v.w:.2f}" height="{v.h:.2f}"/></clipPath>'
                f'<g clip-path="url(#{clip_id})">{g}</g>')
    return g


def north_arrow(cx, cy, r=13):
    nx, ny = M.SITE["north_vec"]
    ang = math.degrees(math.atan2(nx, ny))          # clockwise from sheet-up
    return (f'<g transform="translate({cx},{cy}) rotate({ang:.2f})">'
            f'<circle r="{r}" fill="none" stroke="#111" stroke-width="0.3"/>'
            f'<path d="M0,{-r + 1.5} L{r * 0.32},{r * 0.55} L0,{r * 0.3} L{-r * 0.32},{r * 0.55} Z" fill="#111"/>'
            f'<text class="t" x="0" y="{-r - 2.5}" font-size="5" font-weight="700" text-anchor="middle">צ</text></g>')


def scale_bar(x, y, scale, metres=(0, 1, 2, 5, 10)):
    k = 1000.0 / scale
    out = []
    for i in range(len(metres) - 1):
        out.append(f'<rect x="{x + metres[i] * k:.2f}" y="{y}" width="{(metres[i + 1] - metres[i]) * k:.2f}" height="1.6" fill="{"#111" if i % 2 == 0 else "#fff"}" stroke="#111" stroke-width="0.2"/>')
    for m in metres:
        out.append(f'<text class="n" x="{x + m * k:.2f}" y="{y + 5.5}" font-size="3" text-anchor="middle">{m}</text>')
    out.append(f'<text class="t" x="{x + metres[-1] * k + 3:.2f}" y="{y + 5.5}" font-size="3" text-anchor="end">מ׳</text>')
    return "".join(out)


CSS = """
@page { size: 841mm 594mm; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; color: #111; background: #fff; }
.sheet { position: relative; width: 841mm; height: 594mm; overflow: hidden; page-break-after: always; background: #fff; }
.sheet svg { position: absolute; left: 0; top: 0; width: 841mm; height: 594mm; }
.t { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; direction: rtl; paint-order: stroke; stroke: #fff; stroke-width: 1.1px; stroke-linejoin: round; }
.n { font-family: "Liberation Sans", "DejaVu Sans", sans-serif; direction: ltr; paint-order: stroke; stroke: #fff; stroke-width: 1.1px; stroke-linejoin: round; }
.frame { position: absolute; left: 8mm; top: 8mm; right: 8mm; bottom: 8mm; border: 0.5mm solid #111; }
.panel { position: absolute; top: 8mm; bottom: 8mm; right: 8mm; width: 196mm; border-right: 0; border-left: 0.5mm solid #111; direction: rtl;
         padding: 7mm 7mm 6mm 7mm; font-size: 3.6mm; line-height: 1.42; display: flex; flex-direction: column; }
.panel h1 { font-size: 9mm; line-height: 1.12; font-weight: 700; }
.panel .sub { font-size: 4.4mm; color: #444; margin-top: 1.5mm; }
.panel h2 { font-size: 4.6mm; font-weight: 700; border-bottom: 0.4mm solid #111; padding-bottom: 0.8mm; margin: 6mm 0 2mm; }
.panel table { border-collapse: collapse; width: 100%; font-size: 3.4mm; }
.panel td, .panel th { text-align: right; padding: 0.75mm 1mm; border-bottom: 0.15mm solid #cfcfcf; vertical-align: top; }
.panel th { border-bottom: 0.3mm solid #111; font-size: 3.2mm; }
.panel td.n { text-align: left; direction: ltr; white-space: nowrap; font-variant-numeric: tabular-nums; }
.panel tr.tot td { font-weight: 700; border-top: 0.3mm solid #111; border-bottom: 0; }
.panel tr.grp td { font-weight: 700; background: #f1efe9; }
.panel ul { list-style: none; }
.panel li { padding-right: 3.5mm; position: relative; margin-bottom: 1mm; }
.panel li::before { content: "•"; position: absolute; right: 0; }
.panel .note { font-size: 3.1mm; color: #555; }
.tb { margin-top: auto; border-top: 0.5mm solid #111; padding-top: 3mm; display: grid; grid-template-columns: 1fr 1fr; gap: 1.5mm 4mm; font-size: 3.4mm; }
.tb b { display: block; font-size: 2.8mm; color: #555; font-weight: 400; }
.tb .big { font-size: 7mm; font-weight: 700; }
.lg { display: flex; align-items: center; gap: 2.5mm; margin-bottom: 1.1mm; }
.lg i { display: inline-block; width: 11mm; height: 0; border-top: 0.6mm solid #111; flex: none; }
.lg i.box { height: 3.2mm; border: 0.2mm solid #555; }
"""


def schedule(floor):
    rows, groups = [], []
    for r in M.rooms_of(floor):
        if r["group"] not in groups:
            groups.append(r["group"])
    tot = {"עיקרי": 0.0, "שירות": 0.0}
    for g in groups:
        rows.append(f'<tr class="grp"><td colspan="3">{esc(g)}</td></tr>')
        for r in M.rooms_of(floor):
            if r["group"] != g:
                continue
            a = M.room_area(r)
            tot[r["cat"]] += a
            rows.append(f'<tr><td>{esc(r["name"])}</td><td class="n">{a:.1f}</td><td>{esc(r["cat"])}</td></tr>')
    net = tot["עיקרי"] + tot["שירות"]
    rows.append(f'<tr class="tot"><td>סה״כ חדרים (נטו)</td><td class="n">{net:.1f}</td><td></td></tr>')
    rows.append(f'<tr><td>מתוכם עיקרי / שירות</td><td class="n">{tot["עיקרי"]:.0f} / {tot["שירות"]:.0f}</td><td></td></tr>')
    rows.append(f'<tr><td>שטח בנוי ברוטו, כולל קירות</td><td class="n">{M.gross_area(floor):.1f}</td><td></td></tr>')
    return '<table><tr><th>חלל</th><th>מ״ר</th><th>סוג</th></tr>' + "".join(rows) + "</table>"


def legend(kind):
    def row(css, text):
        return f'<div class="lg"><i style="{css}"></i><span>{text}</span></div>'
    out = [row("border-color:#c0392b; border-top-style:dashed", "גבול מגרש 84"),
           row("border-color:#b5179e; border-top-style:dashed", "קו בניין (קדמי 5, צדדי 3, אחורי 5 מ׳)"),
           '<div class="lg"><i class="box" style="background:#fde3c8;border-color:#c2410c"></i><span>פילר תשתית בחזית המגרש. הקו העבה: צד הדלתות</span></div>']
    if kind == "site":
        out += [row("border-color:#a8936d", "קו גובה של הקרקע הטבעית, כל 0.5 מ׳"),
                row("border-color:#7c7c7c", "גבולות מגרשים שכנים ושפת הכביש (מהמדידה)"),
                row("border-color:#b5179e; border-top-width:0.3mm", "מרחק מהבניין לגבול המגרש, במטרים"),
                '<div class="lg"><i class="box" style="background:#f1efe9"></i><span>גג קומה א׳</span></div>',
                '<div class="lg"><i class="box" style="background:#dfe8d4"></i><span>גג ירוק</span></div>',
                '<div class="lg"><i class="box" style="background:#ead9c0"></i><span>מרפסת גג ודק</span></div>',
                '<div class="lg"><i class="box" style="background:#e9e6df"></i><span>ריצוף חוץ בגובה הרחוב</span></div>']
    else:
        out += ['<div class="lg"><i class="box" style="background:#474747"></i><span>קיר (חיצוני 30 ס״מ, פנימי 15 ס״מ)</span></div>',
                row("border-color:#1d5fa8", "חלון, ויטרינה או קיר זכוכית"),
                row("border-color:#1d5fa8; border-top-width:0.3mm", "קווי מידה, המידות בס״מ. המספרים הקטנים על הקירות: עובי הקיר"),
                row("border-color:#7a4fa3; border-top-style:dashed", "רכיב בתקרה (מקרן ומסך נסתרים)")]
        if kind == "furn":
            out += [row("border-color:#6b4a2b", "ריהוט"), row("border-color:#333", "ציוד קבוע: מטבח, כלים סניטריים, ארונות")]
    return "".join(out)


def pillar_table():
    rows = []
    for p in M.PILLARS:
        x0, y0, x1, y1 = p["rect"]
        along, deep = (x1 - x0, y1 - y0) if p["face"] == "S" else (y1 - y0, x1 - x0)
        rows.append(f'<tr><td>{esc(p["name"])}</td><td class="n">{p["inner"][0] * 100:.0f} × {p["inner"][1] * 100:.0f}</td>'
                    f'<td class="n">{along * 100:.0f} × {deep * 100:.0f}</td><td class="n">{p["h"] * 100:.0f}</td></tr>')
    return ('<h2>פילרים ותשתיות בחזית המגרש</h2><table><tr><th>פילר</th><th>פנים, ס״מ</th><th>חוץ, ס״מ</th><th>גובה</th></tr>' + "".join(rows) + '</table>'
            '<p class="note" style="margin-top:1.5mm">רוחב × עומק. חשמל, תקשורת ומים נפתחים אל הרחוב, ליד שער המשרד. גז ופחים ליד שער הרכב, ונפתחים אל תוך המגרש.</p>')


def panel(title, sub, scale, num, body):
    return (f'<div class="panel"><h1>{esc(title)}</h1><div class="sub">{esc(sub)}</div>{body}'
            f'<div class="tb"><div><b>פרויקט</b>וילה ומשרד אדריכלים</div><div><b>מיקום</b>ראש העין, גוש 5508, מגרש 84</div>'
            f'<div><b>קנה מידה</b><span class="big">{f"1:{scale}" if isinstance(scale, int) else scale}</span></div><div><b>גיליון</b><span class="big">{num}</span></div>'
            f'<div><b>גודל גיליון</b>A1 (841×594 מ״מ)</div><div><b>מפלס ±0.00</b>+{M.ABS0:.2f} מ׳</div></div></div>')


def sheet(svg, pan):
    return f'<div class="sheet"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_MM} {H_MM}">{svg}</svg><div class="frame"></div>{pan}</div>'


PLAN_W = W_MM - 16 - PANEL          # drawing area width (mm)
sheets = []

# ---------------------------------------------------------------- 01 site plan 1:200
v = View(-14.0, -10.0, 68.0, 48.0, 200, 8 + (PLAN_W - 82 * 5) / 2, 30)
vs = View(-1.5, -5.4, 61.0, 9.2, 200, 8 + (PLAN_W - 62.5 * 5) / 2, 30 + 290 + 34)
svg = render(D.site_canvas(), v, clip_id="c1") + render(SEC.section("A", site=True), vs, clip_id="c1s")
svg += f'<text class="t" x="{v.left + v.w:.1f}" y="24" font-size="6" font-weight="700" text-anchor="start">תוכנית מגרש · קנה מידה 1:200</text>'
svg += f'<text class="t" x="{v.left + v.w:.1f}" y="{vs.top - 8:.1f}" font-size="6" font-weight="700" text-anchor="start">חתך מגרש א–א · הקרקע הטבעית מול מפלסי הבניין · קנה מידה 1:200</text>'
svg += north_arrow(40, 548) + scale_bar(70, 566, 200, (0, 5, 10, 20, 30))
S = M.SITE
net = sum(M.room_area(r) for r in M.ROOMS)
gross = sum(M.gross_area(f) for f in "BGF")
body = ('<h2>נתוני המגרש</h2><table>'
        f'<tr><td>שטח רשום</td><td class="n">{S["area_registered"]:,.0f} מ״ר</td></tr>'
        f'<tr><td>שטח לפי קואורדינטות המדידה</td><td class="n">{S["area_measured"]:,.0f} מ״ר</td></tr>'
        f'<tr><td>חזית לרחוב</td><td class="n">{sum(e["len"] for e in S["edges"][:3]):.2f} מ׳</td></tr>'
        f'<tr><td>עומק (גבול צפון־מזרחי)</td><td class="n">{S["edges"][5]["len"]:.2f} מ׳</td></tr>'
        f'<tr><td>רוחב בקצה האחורי</td><td class="n">{S["edges"][4]["len"]:.2f} מ׳</td></tr>'
        '<tr><td>גובה הקרקע ברחוב</td><td class="n">+86.9 עד +87.3</td></tr>'
        '<tr><td>גובה הקרקע בעומק המגרש</td><td class="n">+90.6 עד +92.5</td></tr>'
        f'<tr><td>שטח בתוך קווי הבניין</td><td class="n">{S["buildable_area"]:,.0f} מ״ר</td></tr></table>'
        '<h2>שטחי הבנייה</h2><table><tr><th>קומה</th><th>נטו</th><th>ברוטו</th></tr>'
        + "".join(f'<tr><td>{M.LEVELS[f]["name"]}</td><td class="n">{sum(M.room_area(r) for r in M.rooms_of(f)):.0f}</td><td class="n">{M.gross_area(f):.0f}</td></tr>' for f in "BGF")
        + f'<tr class="tot"><td>סה״כ</td><td class="n">{net:.0f}</td><td class="n">{gross:.0f}</td></tr>'
        f'<tr><td>תכסית קומת הקרקע</td><td class="n" colspan="2">{M.gross_area("G") / S["area_registered"] * 100:.0f}% מהמגרש</td></tr></table>'
        '<h2>מפלסים</h2><table>'
        '<tr><td>קומת מרתף, בגובה הרחוב</td><td class="n">−3.50 (+87.50)</td></tr>'
        '<tr><td>קומת קרקע, בגובה הגינה</td><td class="n">±0.00 (+91.00)</td></tr>'
        '<tr><td>קומה א׳</td><td class="n">+3.50 (+94.50)</td></tr>'
        '<tr><td>מעקה הגג העליון</td><td class="n">+7.30 (+98.30)</td></tr></table>'
        + pillar_table() + '<h2>מקרא</h2>' + legend("site") +
        '<p class="note" style="margin-top:3mm">קווי הבניין הם הנחה לפי המקובל במגרשי מגורים. יש לעדכן אותם לפי התב״ע של המגרש.</p>')
sheets.append(sheet(svg, panel("תוכנית מגרש והעמדה", "מגרש 84 על רקע המדידה, קווי בניין ומפלסים", 200, "01", body)))

# ---------------------------------------------------------------- floor plans 1:100
WIN = (-2.4, -1.6, 59.5, 39.4)
num = 2
for mode, mode_name in (("arch", "תוכנית אדריכלית"), ("furn", "תוכנית העמדה וריהוט")):
    for fl in "BGF":
        v = View(*WIN, 100, 8 + (PLAN_W - 61.9 * 10) / 2, 8 + (578 - 41.0 * 10) / 2)
        svg = render(D.floor_canvas(fl, mode), v, text_k=1.25, clip_id=f"c{num}") + north_arrow(34, 558) + scale_bar(60, 566, 100)
        L = M.LEVELS[fl]
        body = (f'<h2>מפלס</h2><p><span dir="ltr">{"±" if abs(L["z"]) < 1e-9 else ("+" if L["z"] > 0 else "−")}{abs(L["z"]):.2f} = +{M.ABS0 + L["z"]:.2f}</span> מ׳ · גובה {dict(B=3.20, G=3.20, F=3.00)[fl]:.2f} מ׳ עד תחתית התקרה, {L["clear"]:.2f} מ׳ נטו אחרי ריצוף ותקרה מונמכת</p>'
                '<h2>רשימת חללים ושטחים</h2>' + schedule(fl) + pillar_table() + '<h2>מקרא</h2>' + legend(mode))
        sheets.append(sheet(svg, panel(f'{L["name"]} · {mode_name}', L["sub"], 100, f"{num:02d}", body)))
        num += 1

# ---------------------------------------------------------------- sections 1:100
va = View(-1.5, -5.4, 61.0, 9.2, 100, 8 + (PLAN_W - 62.5 * 10) / 2, 30)
vb = View(-2.0, -5.4, 43.0, 9.2, 100, 8 + (PLAN_W - 45 * 10) / 2, 30 + 146 + 24)
vc = View(-2.0, -5.4, 43.0, 9.2, 100, 8 + (PLAN_W - 45 * 10) / 2, 30 + 2 * (146 + 24))
svg = (render(SEC.section("A"), va, text_k=1.25, clip_id="sa") + render(SEC.section("B"), vb, text_k=1.25, clip_id="sb")
       + render(SEC.section("C"), vc, text_k=1.25, clip_id="sc"))
for vv, ttl in ((va, "חתך א–א · לאורך המגרש, מהרחוב אל הגינה"), (vb, "חתך ב–ב · לרוחב המגרש, דרך החניון והמשרד"),
                (vc, "חתך ג–ג · לרוחב המגרש, דרך המדרגות, הלובי המשפחתי ושירותי המשרד")):
    svg += f'<text class="t" x="{W_MM - 16 - PANEL:.1f}" y="{vv.top - 6:.1f}" font-size="6" font-weight="700" text-anchor="start">{ttl}</text>'
svg += scale_bar(60, 566, 100)
body = ('<h2>מה רואים בחתכים</h2><ul>'
        '<li>הקרקע הטבעית עולה כ־4 מ׳ מהרחוב אל עומק המגרש. קומת המרתף יושבת בגובה הרחוב, וקומת הקרקע בגובה הגינה.</li>'
        '<li>החניון והמשרד נפתחים אל הרחוב בלי רמפה. הצד המזרחי שלהם חפור באדמה.</li>'
        '<li>גג החניון הוא מרפסת של קומת הקרקע.</li>'
        '<li>הסלון בגובה כפול: 5.20 מ׳ עד תחתית התקרה (5.00 מ׳ נטו), ומעליו גג ירוק.</li>'
        '<li>מידות הגובה בחתכים נמדדות עד תחתית התקרה הקונסטרוקטיבית. הגובה נטו, אחרי ריצוף ותקרה מונמכת, קטן ב־10–20 ס״מ.</li>'
        '<li>בחתך ג–ג: מדרגות בשני מהלכים ברוחב 1.30 מ׳. 20 רומים של 17.5 ס״מ ושלחים של 29 ס״מ בכל קומה.</li></ul>'
        '<h2>מפלסים</h2><table>'
        '<tr><td>רחוב</td><td class="n">+86.95</td></tr><tr><td>קומת מרתף</td><td class="n">−3.50 (+87.50)</td></tr>'
        '<tr><td>קומת קרקע</td><td class="n">±0.00 (+91.00)</td></tr><tr><td>קומה א׳</td><td class="n">+3.50 (+94.50)</td></tr>'
        '<tr><td>גג הסלון</td><td class="n">+5.50 (+96.50)</td></tr><tr><td>גג עליון</td><td class="n">+6.80 (+97.80)</td></tr></table>'
        '<h2>מקרא</h2>'
        '<div class="lg"><i class="box" style="background:#474747"></i><span>קיר או תקרה חתוכים</span></div>'
        '<div class="lg"><i class="box" style="background:#e9dfcd"></i><span>אדמה</span></div>'
        '<div class="lg"><i style="border-color:#8a7550; border-top-style:dashed"></i><span>קו הקרקע הטבעית לפי המדידה</span></div>'
        '<div class="lg"><i style="border-color:#c0392b; border-top-style:dashed"></i><span>גבול המגרש</span></div>'
        '<div class="lg"><i style="border-color:#b5179e; border-top-style:dashed"></i><span>קו בניין</span></div>'
        '<div class="lg"><i style="border-color:#1d5fa8; border-top-width:0.3mm"></i><span>קווי מידה בס״מ: גובה קומה, גובה חלל עד תחתית התקרה, אורכים</span></div>')
sheets.append(sheet(svg, panel("חתכים", "חתך א–א, חתך ב–ב וחתך ג–ג", 100, f"{num:02d}", body)))

# ---------------------------------------------------------------- 3D sheets (only when a folder of renders is given)
R3D = sys.argv[2] if len(sys.argv) > 2 else None
if R3D:
    import os

    def img_sheet(title, sub, number, cells, cols, iw, body):
        ih = iw * 1000 / 1600
        gap = 7.0
        rows = (len(cells) + cols - 1) // cols
        left0 = 8 + (PLAN_W - (cols * iw + (cols - 1) * gap)) / 2
        top0 = 8 + (578 - (rows * (ih + 9) + (rows - 1) * gap)) / 2
        out = []
        for i, (fn, cap) in enumerate(cells):
            cx = left0 + (cols - 1 - i % cols) * (iw + gap)          # right-to-left reading order
            cy = top0 + (i // cols) * (ih + 9 + gap)
            out.append(f'<img src="file://{os.path.abspath(os.path.join(R3D, fn))}" style="position:absolute;left:{cx:.1f}mm;top:{cy:.1f}mm;width:{iw:.1f}mm;height:{ih:.1f}mm;border:0.2mm solid #111">'
                       f'<div style="position:absolute;left:{cx:.1f}mm;top:{cy + ih + 1.5:.1f}mm;width:{iw:.1f}mm;direction:rtl;text-align:right;font-size:4.2mm;font-weight:700">{esc(cap)}</div>')
        return f'<div class="sheet">{"".join(out)}<div class="frame"></div>{panel(title, sub, "הדמיה", number, body)}</div>'

    credit = ('<p class="note" style="margin-top:4mm">ההדמיות והשרטוטים נוצרו מאותו מודל, ולכן המידות והחדרים זהים בשניהם. '
              '</p><p class="note" style="margin-top:2mm">קרדיט למודל הרכבים בחניון:<br><span dir="ltr" style="white-space:nowrap">CarConcept © Darmstadt Graphics Group GmbH, CC BY 4.0</span></p>')
    body = ('<h2>מה רואים</h2><ul><li>כל קומה מוצגת בלי התקרה שמעליה, עם הקירות, הדלתות, החלונות והריהוט.</li>'
            '<li>שם כל חדר ושטחו מסומנים מעל החדר.</li><li>המבט מדרום־מערב, כמו בתוכניות: הרחוב משמאל והגינה מימין.</li></ul>' + credit)
    sheets.append(img_sheet("מבטי־על תלת־ממדיים", "כל קומה פתוחה מלמעלה, עם שמות החדרים", f"{num + 1:02d}",
                            [("cut_B_labelled.jpg", "קומת מרתף · משרד, חניון וקולנוע"), ("cut_G_labelled.jpg", "קומת קרקע · החלק הציבורי, הבריכה והספא"),
                             ("cut_F_labelled.jpg", "קומה א׳ · החלק הפרטי"), ("top.jpg", "מבט־על על המגרש כולו")], 2, 303.0, body))
    body = ('<h2>מה רואים</h2><ul><li>הווילה על הטופוגרפיה האמיתית של מגרש 84, לפי קובץ המדידה.</li>'
            '<li>קומת המרתף נפתחת אל הרחוב, והחלק האחורי שלה חפור במדרון.</li><li>גג החניון הוא מרפסת גדולה עם פרגולה.</li>'
            '<li>הבריכה נמצאת בגינה האחורית, בין הסלון לביתן הספא.</li></ul>' + credit)
    sheets.append(img_sheet("הדמיות חוץ", "הווילה והמגרש מכמה כיוונים", f"{num + 2:02d}",
                            [("aerial_front.jpg", "מבט מהרחוב מלמעלה, מדרום־מערב"), ("aerial_back.jpg", "מבט מעל הגינה האחורית והבריכה"),
                             ("street.jpg", "מבט מהרחוב בגובה העיניים"), ("garden.jpg", "מהמדשאה אל הסלון והבריכה"),
                             ("terrace.jpg", "על מרפסת הגג, מתחת לפרגולה"), ("aerial_side.jpg", "מבט מלמעלה מצד מגרש 85")], 2, 272.0, body))

doc = (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>וילה במגרש 84</title><style>{CSS}</style></head><body>'
       + "".join(sheets) + "</body></html>")
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, "sheets:", len(sheets))

