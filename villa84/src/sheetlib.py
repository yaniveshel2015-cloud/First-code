"""Render the drawing canvases to A1 sheets (HTML + SVG, millimetre units -> true-scale PDF)."""
import html
import math
import re
import sys

import draw as D
import model as M



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


PLAN_W = W_MM - 16 - PANEL
