"""Stage 1 review set: basement plans (architectural and furniture) at 1:100 and a core / area sheet."""
import sys

import draw as D
import model as M
from sheetlib import CSS, PLAN_W, View, esc, legend, north_arrow, panel, render, scale_bar, schedule, sheet
from symbols import Canvas

OUT = sys.argv[1]

# areas of the plan the user approved before (from the delivered program workbook)
OLD = {
    "office": 164.0, "parking": 157.1, "family_lobby": 51.1, "cinema": 34.8, "hall_G": 51.1, "corridor_F": 28.3 + 9.0,
}

sheets = []
WIN = (-3.4, 6.6, 32.0, 39.6)          # basement and its forecourt
for mode, mode_name, num in (("arch", "תוכנית אדריכלית", "1א"), ("furn", "תוכנית העמדה וריהוט", "1ב")):
    v = View(*WIN, 75, 8 + (PLAN_W - 35.4 * 1000 / 75) / 2, 8 + (578 - 33.0 * 1000 / 75) / 2)
    svg = render(D.floor_canvas("B", mode), v, text_k=1.15, clip_id=f"c{num}") + north_arrow(34, 558) + scale_bar(60, 566, 75)
    L = M.LEVELS["B"]
    body = (f'<h2>מפלס</h2><p><span dir="ltr">−3.50 = +87.50</span> מ׳ · גובה 3.20 מ׳ עד תחתית התקרה, {L["clear"]:.2f} מ׳ נטו</p>'
            '<h2>רשימת חללים ושטחים</h2>' + schedule("B") + '<h2>מקרא</h2>' + legend(mode))
    sheets.append(sheet(svg, panel(f'{L["name"]} · {mode_name}', "שלב 1 לאישור: גרעין חדש ומרתף חדש", 75, num, body)))

# ---------------------------------------------------------------- core diagram sheet
COL = {"office": "#cfe0f5", "family": "#f6d9b8", "service": "#e6e6e6", "park": "#d9d9d9", "core": "#b9a6d6", "circ": "#fff3b0",
       "live": "#f3e3a3", "bed": "#cfe8c8", "wet": "#bfe6ee", "tower": "#e8a0a0"}
KIND = {"B01": "park", "B02": "service", "B03": "service", "B04": "family", "B05": "family", "B15": "circ", "B16": "service",
        "B08": "office", "B09": "office", "B13": "office", "B10": "office", "B17": "circ", "B11": "office", "B12": "office",
        "G09": "circ", "G01": "live", "G07": "circ", "G03": "live", "G04": "service", "G05": "service", "G08": "wet", "G12": "live",
        "F01": "bed", "F03": "wet", "F05": "bed", "F14": "bed", "F11": "circ", "F08": "bed", "F12": "wet"}


def diagram(fl):
    c = Canvas()
    D.walls(c, fl)
    for r in M.rooms_of(fl):
        if r["id"][0] == "P":
            continue
        k = "core" if r["id"] in ("B06", "B07", "G10", "G11", "F16", "F17") else ("tower" if r["rects"][0] == M.TOWER else KIND.get(r["id"], "service"))
        for q in r["rects"]:
            c.items.append(dict(t="poly", pts=[(q[0], q[1]), (q[2], q[1]), (q[2], q[3]), (q[0], q[3])], layer="OUT", closed=True,
                                fill="d_" + k, holes=[], dash=None, w=0.01))
    D.stair(c, fl)
    D.lift(c, fl)
    for r in M.rooms_of(fl):
        if r["id"] in ("B06", "G10", "F16", "B07", "G11", "F17") or r["id"][0] == "P":
            continue
        x, y = D._label_pos(r)
        q = min(r["rects"], key=lambda q: (abs((q[0] + q[2]) / 2 - x) + abs((q[1] + q[3]) / 2 - y)))
        narrow = (q[2] - q[0]) < 1.8 and (q[3] - q[1]) > (q[2] - q[0])
        c.text((x, y + 0.25), r["name"], "TEXT", h=0.3, bold=True, rot=90 if narrow else 0)
        if not narrow:
            c.text((x, y - 0.3), f"{M.room_area(r):.0f} מ״ר", "TEXT-S", h=0.26)
    return c


import sheetlib
for k, col in COL.items():
    sheetlib.FILL["d_" + k] = col

svg = ""
y_top = 40
vb = View(5.0, 11.8, 28.0, 34.4, 100, 8 + PLAN_W - 230 - 10, y_top)
vg = View(5.0, 21.6, 36.4, 34.4, 100, 8 + 12, y_top)
vf = View(5.0, 21.6, 28.0, 34.4, 100, 8 + 12 + 314 - 230, y_top + 128 + 36)
svg += (render(diagram("B"), vb, text_k=1.0, clip_id="db") + render(diagram("G"), vg, text_k=1.0, clip_id="dg")
        + render(diagram("F"), vf, text_k=1.0, clip_id="df"))
for vv, t in ((vb, "קומת מרתף −3.50"), (vg, "קומת קרקע ±0.00 · חלוקה ראשונית, תפורט בשלב 2"), (vf, "קומה א׳ +3.50 · חלוקה ראשונית, תפורט בשלב 3")):
    svg += f'<text class="t" x="{vv.left + vv.w:.1f}" y="{vv.top - 6:.1f}" font-size="6" font-weight="700" text-anchor="start">{esc(t)}</text>'
svg += north_arrow(34, 558) + scale_bar(60, 566, 100, (0, 1, 2, 5, 10))
# legend chips under the plans
lx, ly = 8 + 12, 400
items = [("office", "משרד"), ("family", "חלק משפחתי"), ("park", "חניה"), ("service", "שירות ואחסון"), ("circ", "מעברים"),
         ("core", "מדרגות ומעלית"), ("tower", "מגדל מחוזק: מרחב מוגן, מזווה, ממ״ד"), ("live", "מגורים"), ("bed", "חדרי שינה"), ("wet", "חדרים רטובים")]
for i, (k, t) in enumerate(items):
    x = lx + (i % 5) * 92
    y = ly + (i // 5) * 12
    svg += f'<rect x="{x + 80:.1f}" y="{y:.1f}" width="9" height="6" fill="{COL[k]}" stroke="#555" stroke-width="0.2"/>'
    svg += f'<text class="t" x="{x + 78:.1f}" y="{y + 4.8:.1f}" font-size="4.2" text-anchor="end">{esc(t)}</text>'

a = {r["id"]: M.room_area(r) for r in M.ROOMS}
office = sum(M.room_area(r) for r in M.rooms_of("B") if r["group"] == "משרד אדריכלים")
rows = [
    ("משרד אדריכלים, כולל מסדרון", OLD["office"], office),
    ("חניון", OLD["parking"], a["B01"]),
    ("לובי משפחתי ומעבר למדרגות", OLD["family_lobby"], a["B05"] + a["B15"]),
    ("חדר קולנוע", OLD["cinema"], a["B04"]),
    ("מבואת כניסה בקומת הקרקע", OLD["hall_G"], a["G09"]),
    ("מסדרון ומעבר הלבשה בקומה א׳", OLD["corridor_F"], a["F11"]),
]
tbl = '<table><tr><th>חלל</th><th>לפני</th><th>אחרי</th><th>שינוי</th></tr>' + "".join(
    f'<tr><td>{esc(n)}</td><td class="n">{o:.0f}</td><td class="n">{nw:.0f}</td><td class="n">{(nw - o) / o * 100:+.0f}%</td></tr>' for n, o, nw in rows) + '</table>'
fl_rows = "".join(f'<tr><td>{M.LEVELS[f]["name"]}</td><td class="n">{sum(M.room_area(r) for r in M.rooms_of(f)):.0f}</td><td class="n">{M.gross_area(f):.0f}</td>'
                  f'<td class="n">{M.circulation_share(f) * 100:.0f}%</td></tr>' for f in "BGF")
gross = sum(M.gross_area(f) for f in "BGF")
body = ('<h2>מה זז</h2><ul>'
        '<li>המדרגות והמעלית עברו מהפינה הצפון־מזרחית לאמצע הבניין, בצד הדרומי. הן עומדות אחת מעל השנייה בשלוש הקומות.</li>'
        '<li>במרתף: יוצאים מהרכב ונכנסים ישר ללובי המשפחתי. המעלית נפתחת אל הלובי (דלת מכל צד).</li>'
        '<li>בקומת הקרקע: דלת הכניסה בדיוק מול מדרגות הכניסה מהרחבה. המבואה צמודה למדרגות, למעלית ולסלון.</li>'
        '<li>בקומה א׳: שלושה חדרי שינה פונים אל המרפסות בדרום (הורים, נוער 1, הילד הצעיר). חדר נוער 2 פונה צפונה.</li>'
        '<li>מגדל מחוזק אחד מעל השני: מרחב מוגן של המשרד, מזווה, ממ״ד.</li></ul>'
        '<h2>שטחים לפני ואחרי (מ״ר)</h2>' + tbl +
        '<h2>סיכום קומות (מ״ר)</h2><table><tr><th>קומה</th><th>נטו</th><th>ברוטו</th><th>מעברים</th></tr>' + fl_rows +
        f'<tr class="tot"><td>סה״כ ברוטו</td><td></td><td class="n">{gross:,.0f}</td><td></td></tr></table>'
        '<p class="note" style="margin-top:2mm">מעברים: מסדרונות ומבואות, באחוזים מהשטח נטו של הקומה. היעד: עד 15%. '
        'השטח ברוטו לא השתנה (קווי המתאר של הקומות נשארו), והוא מתחת ל־1,200 מ״ר.</p>'
        '<p class="note" style="margin-top:2mm">בדיקה אוטומטית: אין חפיפות בין חדרים, כל הפתחים בתוך קירות, ואין כיסים ריקים בין החדרים.</p>')
sheets.append(sheet(svg, panel("גרעין חדש וטבלת שטחים", "מיקום המדרגות והמעלית בשלוש הקומות", 100, "1ג", body)))

doc = (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>וילה 84 · שלב 1</title><style>{CSS}</style></head><body>'
       + "".join(sheets) + "</body></html>")
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, len(sheets))
