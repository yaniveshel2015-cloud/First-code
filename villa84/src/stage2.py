"""Stage 2 review set: ground floor plans (architectural and furniture) at 1:100 and a summary sheet."""
import sys

import draw as D
import model as M
import sheetlib
from sheetlib import CSS, PLAN_W, View, esc, legend, north_arrow, panel, render, scale_bar, schedule, sheet
from symbols import Canvas

OUT = sys.argv[1]
OLD = {"G09": 51.1, "G01": 36.2, "G02": 50.2, "G03": 34.7}          # areas in the plan delivered before the change

sheets = []
WIN = (-2.4, 9.4, 59.5, 39.4)
L = M.LEVELS["G"]
for mode, mode_name, num in (("arch", "תוכנית אדריכלית", "2א"), ("furn", "תוכנית העמדה וריהוט", "2ב")):
    v = View(*WIN, 100, 8 + (PLAN_W - 61.9 * 10) / 2, 8 + (578 - 30.0 * 10) / 2)
    svg = render(D.floor_canvas("G", mode), v, text_k=1.25, clip_id=f"c{num}") + north_arrow(34, 558) + scale_bar(60, 566, 100)
    body = ('<h2>מפלס</h2><p><span dir="ltr">±0.00 = +91.00</span> מ׳ · גובה 3.20 מ׳ עד תחתית התקרה, 3.00 מ׳ נטו. בסלון גובה כפול: 5.00 מ׳ נטו</p>'
            '<h2>רשימת חללים ושטחים</h2>' + schedule("G") + '<h2>מקרא</h2>' + legend(mode))
    sheets.append(sheet(svg, panel(f'{L["name"]} · {mode_name}', "שלב 2 לאישור: קומת הקרקע החדשה", 100, num, body)))

# ---------------------------------------------------------------- summary sheet
COL = {"live": "#f3e3a3", "kitchen": "#f6d9b8", "service": "#e6e6e6", "circ": "#fff3b0", "core": "#b9a6d6", "tower": "#e8a0a0",
       "wet": "#bfe6ee", "spa": "#d7ecd0"}
KIND = {"G01": "live", "G02": "kitchen", "G03": "live", "G04": "kitchen", "G05": "service", "G06": "tower", "G07": "circ", "G08": "wet",
        "G09": "circ", "G10": "core", "G11": "core", "G12": "live"}
for k, col in COL.items():
    sheetlib.FILL["d_" + k] = col


def diagram():
    c = Canvas()
    D.walls(c, "G")
    for r in M.rooms_of("G"):
        k = KIND.get(r["id"], "spa")
        for q in r["rects"]:
            c.items.append(dict(t="poly", pts=[(q[0], q[1]), (q[2], q[1]), (q[2], q[3]), (q[0], q[3])], layer="OUT", closed=True,
                                fill="d_" + k, holes=[], dash=None, w=0.01))
    D.stair(c, "G")
    D.lift(c, "G")
    D.openings(c, "G")
    for r in M.rooms_of("G"):
        if r["id"] in ("G10", "G11"):
            continue
        x, y = D._label_pos(r)
        q = min(r["rects"], key=lambda q: (abs((q[0] + q[2]) / 2 - x) + abs((q[1] + q[3]) / 2 - y)))
        narrow = (q[2] - q[0]) < 2.1 and (q[3] - q[1]) > (q[2] - q[0])
        c.text((x, y + 0.22), r["name"], "TEXT", h=0.28, bold=True, rot=90 if narrow else 0)
        if not narrow:
            c.text((x, y - 0.28), f"{M.room_area(r):.0f} מ״ר", "TEXT-S", h=0.24)
    # arrows: the main routes
    for path in ([(23.3, 21.2), (23.3, 25.0), (27.8, 25.0)], [(21.2, 25.0), (21.2, 27.1), (16.6, 27.1)], [(21.2, 27.1), (21.2, 28.5), (24.8, 28.5)]):
        for a, b in zip(path, path[1:]):
            c.line(a, b, "CUT", w=0.45, dash="4 2")
    return c


v = View(5.0, 20.2, 51.5, 36.8, 75, 8 + (PLAN_W - 46.5 * 1000 / 75) / 2, 60)
svg = render(diagram(), v, text_k=1.0, clip_id="dg") + north_arrow(34, 558) + scale_bar(60, 566, 75)
svg += f'<text class="t" x="{v.left + v.w:.1f}" y="{v.top - 8:.1f}" font-size="6" font-weight="700" text-anchor="start">קומת קרקע ±0.00 · חלוקה ותנועה</text>'
items = [("live", "מגורים"), ("kitchen", "מטבח ומטבח אחורי"), ("circ", "מבואה ומעבר"), ("core", "מדרגות ומעלית"),
         ("tower", "מזווה (מגדל מחוזק)"), ("service", "שירות"), ("wet", "שירותים"), ("spa", "ביתן ספא")]
lx, ly = 8 + 12, 380
for i, (k, t) in enumerate(items):
    x = lx + (i % 4) * 115
    y = ly + (i // 4) * 12
    svg += f'<rect x="{x + 100:.1f}" y="{y:.1f}" width="9" height="6" fill="{COL[k]}" stroke="#555" stroke-width="0.2"/>'
    svg += f'<text class="t" x="{x + 98:.1f}" y="{y + 4.8:.1f}" font-size="4.2" text-anchor="start">{esc(t)}</text>'
svg += (f'<line x1="{lx + 300:.1f}" y1="{ly + 27:.1f}" x2="{lx + 309:.1f}" y2="{ly + 27:.1f}" stroke="#111" stroke-width="0.5" stroke-dasharray="2 1"/>'
        f'<text class="t" x="{lx + 298:.1f}" y="{ly + 28.5:.1f}" font-size="4.2" text-anchor="start">תנועה: מהכניסה לסלון, למטבח ולחדרי השירות</text>')

a = {r["id"]: M.room_area(r) for r in M.ROOMS}
rows = "".join(
    f'<tr><td>{esc(r["name"])}</td><td class="n">{OLD[r["id"]]:.0f}</td><td class="n">{a[r["id"]]:.0f}</td>'
    f'<td class="n">{(a[r["id"]] - OLD[r["id"]]) / OLD[r["id"]] * 100:+.0f}%</td></tr>' if r["id"] in OLD else
    f'<tr><td>{esc(r["name"])}</td><td class="n">—</td><td class="n">{a[r["id"]]:.0f}</td><td></td></tr>'
    for r in M.rooms_of("G") if r["id"][0] == "G" and r["id"] not in ("G10", "G11", "G12"))
net = sum(M.room_area(r) for r in M.rooms_of("G") if r["id"][0] == "G")
body = ('<h2>מה בקומה</h2><ul>'
        '<li>דלת זכוכית כפולה (1.80) בדיוק מול מדרגות הכניסה מהרחבה. המבואה צמודה למדרגות ולמעלית, ונפתחת אל הסלון.</li>'
        '<li>פינת האוכל והמטבח עם האי פונים אל מרפסת הגג, דרך קיר זכוכית נגרר לכל האורך.</li>'
        '<li>חדר המשפחה והגיימינג בפינה הצפון־מערבית, עם חלונות לשתי חצרות.</li>'
        '<li>מאחורי המטבח: מטבח אחורי ומזווה גדול. מהחניון עולים במעלית, והמזווה במרחק כמה צעדים.</li>'
        '<li>חדר שירות וכלב עם יציאה בגשר מעל החצר האנגלית אל השביל הצפוני, לגינה ולבריכה.</li>'
        '<li>שירותי אורחים עם חלון, מהמעבר שליד המבואה.</li>'
        '<li>במרפסת הגג: פרגולה ופינת אוכל, פתח הפטיו של המרתף עם מעקה ואדניות, ופס זכוכית מעל מעבר החניון.</li>'
        '<li>הסלון, הספא והבריכה לא זזו. פתח הסלון למבואה קצר ב־19 ס״מ (4.81 במקום 5.00), ודפי המידות לסקצ׳אפ יתעדכנו בשלב 4.</li></ul>'
        '<h2>שטחים לפני ואחרי (מ״ר)</h2><table><tr><th>חלל</th><th>לפני</th><th>אחרי</th><th>שינוי</th></tr>' + rows + '</table>'
        f'<p class="note" style="margin-top:2mm">״לפני״ מופיע רק לחללים ששטחם נשמר אצלי מהגרסה הקודמת. המבואה כוללת את משטח המדרגות והמעלית.</p>'
        '<h2>סיכום הקומה (מ״ר)</h2><table>'
        f'<tr><td>בית, נטו (בלי הספא)</td><td class="n">{net:.0f}</td></tr>'
        f'<tr><td>מעברים (מבואה ומעבר שירות)</td><td class="n">{M.circulation_share("G") * 100:.0f}% מהנטו</td></tr>'
        f'<tr><td>ברוטו, כולל הספא</td><td class="n">{M.gross_area("G"):.0f}</td></tr>'
        f'<tr class="tot"><td>ברוטו, כל הבניין</td><td class="n">{sum(M.gross_area(f) for f in "BGF"):,.0f}</td></tr></table>'
        '<p class="note" style="margin-top:2mm">בדיקה אוטומטית: אין חפיפות ואין כיסים ריקים, כל הפתחים בתוך קירות, ולכל חדר שירותים יש חלון החוצה.</p>')
sheets.append(sheet(svg, panel("קומת קרקע · סיכום", "חלוקה, תנועה וטבלת שטחים", 75, "2ג", body)))

doc = (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>וילה 84 · שלב 2</title><style>{CSS}</style></head><body>'
       + "".join(sheets) + "</body></html>")
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, len(sheets))
