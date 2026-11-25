"""Stage 3 review set: first floor plans (architectural and furniture) and a summary sheet."""
import sys

import draw as D
import model as M
import sheetlib
from sheetlib import CSS, PLAN_W, View, esc, legend, north_arrow, panel, render, scale_bar, schedule, sheet
from symbols import Canvas

OUT = sys.argv[1]
OLD = {"F01": 29.9, "F02": 13.1, "F04": 18.2, "F11": 28.3 + 9.0, "F12": 16.2, "F13": 9.8, "F14": 23.1}   # areas before the change (corridor + dressing passage)

sheets = []
WIN = (-3.4, 13.0, 32.0, 39.6)
L = M.LEVELS["F"]
for mode, mode_name, num in (("arch", "תוכנית אדריכלית", "3א"), ("furn", "תוכנית העמדה וריהוט", "3ב")):
    v = View(*WIN, 75, 8 + (PLAN_W - 35.4 * 1000 / 75) / 2, 8 + (578 - 26.6 * 1000 / 75) / 2)
    svg = render(D.floor_canvas("F", mode), v, text_k=1.15, clip_id=f"c{num}") + north_arrow(34, 558) + scale_bar(60, 566, 75)
    body = ('<h2>מפלס</h2><p><span dir="ltr">+3.50 = +94.50</span> מ׳ · גובה 3.00 מ׳ עד תחתית התקרה, 2.90 מ׳ נטו</p>'
            '<h2>רשימת חללים ושטחים</h2>' + schedule("F") + '<h2>מקרא</h2>' + legend(mode))
    sheets.append(sheet(svg, panel(f'{L["name"]} · {mode_name}', "שלב 3 לאישור: קומה א׳ החדשה", 75, num, body)))

# ---------------------------------------------------------------- summary sheet
COL = {"par": "#f3e3a3", "kid": "#cfe8c8", "service": "#e6e6e6", "circ": "#fff3b0", "core": "#b9a6d6", "tower": "#e8a0a0",
       "wet": "#bfe6ee", "closet": "#ead9c0"}
KIND = {"F01": "par", "F02": "closet", "F04": "wet", "F14": "kid", "F15": "wet", "F05": "kid", "F08": "kid", "F06": "wet", "F12": "service",
        "F11": "circ", "F13": "tower", "F16": "core", "F17": "core"}
for k, col in COL.items():
    sheetlib.FILL["d_" + k] = col


def diagram():
    c = Canvas()
    D.walls(c, "F")
    for r in M.rooms_of("F"):
        k = KIND.get(r["id"], "service")
        for q in r["rects"]:
            c.items.append(dict(t="poly", pts=[(q[0], q[1]), (q[2], q[1]), (q[2], q[3]), (q[0], q[3])], layer="OUT", closed=True,
                                fill="d_" + k, holes=[], dash=None, w=0.01))
    D.stair(c, "F")
    D.lift(c, "F")
    D.openings(c, "F")
    for r in M.rooms_of("F"):
        if r["id"] in ("F16", "F17"):
            continue
        x, y = D._label_pos(r)
        q = min(r["rects"], key=lambda q: (abs((q[0] + q[2]) / 2 - x) + abs((q[1] + q[3]) / 2 - y)))
        narrow = (q[2] - q[0]) < 2.1 and (q[3] - q[1]) > (q[2] - q[0])
        c.text((x, y + 0.22), r["name"], "TEXT", h=0.28, bold=True, rot=90 if narrow else 0)
        if not narrow:
            c.text((x, y - 0.28), f"{M.room_area(r):.0f} מ״ר", "TEXT-S", h=0.24)
    # arrows: the main routes
    for path in ([(18.7, 26.9), (18.7, 28.5), (10.7, 28.5)], [(21.2, 25.0), (21.2, 28.5), (22.9, 28.5)]):
        for a, b in zip(path, path[1:]):
            c.line(a, b, "CUT", w=0.45, dash="4 2")
    return c


v = View(5.0, 19.8, 28.4, 34.6, 50, 8 + (PLAN_W - 23.4 * 1000 / 50) / 2, 60)
svg = render(diagram(), v, text_k=1.0, clip_id="dg") + north_arrow(34, 558) + scale_bar(60, 566, 50, (0, 1, 2, 5))
svg += f'<text class="t" x="{v.left + v.w:.1f}" y="{v.top - 8:.1f}" font-size="6" font-weight="700" text-anchor="start">קומה א׳ +3.50 · חלוקה ותנועה</text>'
items = [("par", "חדר ההורים"), ("closet", "חדר ארונות"), ("kid", "חדרי הילדים"), ("wet", "חדרי רחצה"),
         ("circ", "מסדרון ומבואה"), ("core", "מדרגות ומעלית"), ("tower", "ממ״ד (מגדל מחוזק)"), ("service", "כביסה ומצעים")]
lx, ly = 8 + 12, 440
for i, (k, t) in enumerate(items):
    x = lx + (i % 4) * 115
    y = ly + (i // 4) * 12
    svg += f'<rect x="{x + 100:.1f}" y="{y:.1f}" width="9" height="6" fill="{COL[k]}" stroke="#555" stroke-width="0.2"/>'
    svg += f'<text class="t" x="{x + 98:.1f}" y="{y + 4.8:.1f}" font-size="4.2" text-anchor="start">{esc(t)}</text>'
svg += (f'<line x1="{lx + 300:.1f}" y1="{ly + 27:.1f}" x2="{lx + 309:.1f}" y2="{ly + 27:.1f}" stroke="#111" stroke-width="0.5" stroke-dasharray="2 1"/>'
        f'<text class="t" x="{lx + 298:.1f}" y="{ly + 28.5:.1f}" font-size="4.2" text-anchor="start">תנועה: מהמדרגות והמעלית אל החדרים</text>')

a = {r["id"]: M.room_area(r) for r in M.ROOMS}
rows = "".join(
    f'<tr><td>{esc(r["name"])}</td><td class="n">{OLD[r["id"]]:.0f}</td><td class="n">{a[r["id"]]:.0f}</td>'
    f'<td class="n">{(a[r["id"]] - OLD[r["id"]]) / OLD[r["id"]] * 100:+.0f}%</td></tr>' if r["id"] in OLD else
    f'<tr><td>{esc(r["name"])}</td><td class="n">—</td><td class="n">{a[r["id"]]:.0f}</td><td></td></tr>'
    for r in M.rooms_of("F") if r["id"] not in ("F16", "F17"))
net = sum(M.room_area(r) for r in M.rooms_of("F"))
body = ('<h2>מה בקומה</h2><ul>'
        '<li>שלושה חדרי שינה פונים אל המרפסות בדרום: ההורים, הילד הצעיר (ליד ההורים) ונוער 1.</li>'
        '<li>חדר נוער 2 בפינה הצפון־מזרחית, עם חלון לצפון וחלון עליון למזרח, מעל גג הסלון.</li>'
        '<li>סוויטת הורים: חדר שינה, חדר ארונות שנכנסים אליו מחדר השינה, וחדר רחצה עם אמבטיה, מקלחת וכיור כפול.</li>'
        '<li>לכל חדר רחצה ולחדר הכביסה יש חלון לצפון. חדר רחצה לילד מול החדר שלו, ומקלחת משותפת לשני הנוערים עם 2 כיורים.</li>'
        '<li>מסדרון קצר אחד לאורך הקומה. מעבר ההלבשה הישן ירד. כל הדלתות יוצאות מהמסדרון או ממבואת המדרגות.</li>'
        '<li>הממ״ד במגדל המחוזק, מעל המזווה ומעל שירותי המשרד. ביום־יום חדר לימוד.</li>'
        '<li>במרפסת הדרומית מחיצה בין ההורים לילד. מרפסת נפרדת לנוער 1.</li></ul>'
        '<h2>שטחים לפני ואחרי (מ״ר)</h2><table><tr><th>חלל</th><th>לפני</th><th>אחרי</th><th>שינוי</th></tr>' + rows + '</table>'
        f'<p class="note" style="margin-top:2mm">״לפני״ מופיע רק לחללים ששטחם נשמר אצלי מהגרסה הקודמת. במסדרון, ״לפני״ כולל את מעבר ההלבשה (9 מ״ר).</p>'
        '<h2>סיכום הקומה (מ״ר)</h2><table>'
        f'<tr><td>נטו</td><td class="n">{net:.0f}</td></tr>'
        f'<tr><td>מעברים (מסדרון ומבואה)</td><td class="n">{M.circulation_share("F") * 100:.0f}% מהנטו</td></tr>'
        f'<tr><td>ברוטו</td><td class="n">{M.gross_area("F"):.0f}</td></tr>'
        f'<tr class="tot"><td>ברוטו, כל הבניין</td><td class="n">{sum(M.gross_area(f) for f in "BGF"):,.0f}</td></tr></table>'
        '<p class="note" style="margin-top:2mm">בדיקה אוטומטית: אין חפיפות ואין כיסים ריקים, כל הפתחים בתוך קירות, ולכל חדר רחצה יש חלון החוצה.</p>')
sheets.append(sheet(svg, panel("קומה א׳ · סיכום", "חלוקה, תנועה וטבלת שטחים", 50, "3ג", body)))

doc = (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>וילה 84 · שלב 3</title><style>{CSS}</style></head><body>'
       + "".join(sheets) + "</body></html>")
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, len(sheets))
