"""Program workbook for the villa on plot 84, generated from the drawn model (Hebrew, RTL), by floor like the whiteboard table."""
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.pagebreak import Break
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

import model as M

OUT = sys.argv[1]
FONT, BLUE, BLACK = "Arial", "0000FF", "000000"
HEADER_FILL, INPUT_FILL, OUTDOOR_GREEN = "333F4F", "FFF2CC", "548235"
CIRC = "מעברים ותנועה"
CIRC_NAMES = {"לובי משפחתי", "מדרגות", "פיר מעלית", "מבואה", "מבואת כניסה", "מעבר שירות", "מסדרון ומבואת קומה", "מעבר הלבשה"}
thin = Side(style="thin", color="808080")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def font(size=11, bold=False, color=BLACK, italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)


def fill(hex_):
    return PatternFill("solid", start_color=hex_, end_color=hex_)


def align(h="right", wrap=True, rotation=0):
    return Alignment(horizontal=h, vertical="center", wrap_text=wrap, textRotation=rotation, readingOrder=2)


# ---------------------------------------------------------------- rows from the model
NOTES = {
    "מדרגות": "שני מהלכים ברוחב 1.30 מ׳ כל אחד, 20 רומים של 17.5 ס״מ, שלח 29 ס״מ",
    "פיר מעלית": "פיר במידות פנים 2.00×2.00 מ׳, עוצר בכל 3 הקומות",
    "לובי משפחתי": "מהחניון אל המדרגות והמעלית, נעול ללקוחות המשרד",
    "מבואת כניסה": "כניסה ראשית ממרפסת הגג, פתוחה לסלון ולמטבח",
    "מסדרון ומבואת קומה": "מחבר בין 4 הסוויטות, הממ״ד וחדר הכביסה",
    "מעבר שירות": "מטבח, מזווה, מעלית וחדר הכלב בלי לעבור בסלון",
    "מעבר הלבשה": "מבואה פרטית לסוויטת ההורים",
    "מבואה": "בין המשרד למרחב המוגן ולשירותים",
    "פינת אוכל": "שולחן ל־12 סועדים, ויטרינה אל מרפסת הגג",
    "מטבח": "אי מרכזי, פינת בוקר, פתוח לפינת האוכל",
    "מטבח אחורי": "עבודה ״מלוכלכת״ מאחורי המטבח הראשי",
    "חדר משפחה וגיימינג": "פינת טלוויזיה ו־2 עמדות מחשב לגיימינג",
    "מזווה גדול": "צמוד למעלית: הקניות עולות ישר מהחניון",
    "חדר שירות וכלב": "מקלחת לכלב, כיור ואחסון",
    "שירותי אורחים": "",
    "חדר קולנוע": "8 מושבים ב־2 שורות, מסך על הקיר, בלי חלונות",
    "חדר ישיבות": "8–10 מקומות, קיר זכוכית אל גלריית הרכבים",
    "חדר אדריכל ראשי": "קיר זכוכית אל גלריית הרכבים, דלת פרטית ללובי",
    "סטודיו פתוח וקבלה": "8 עמדות עבודה, 2 עמדות נוספות, קבלה ומטבחון",
    "סדנת מודלים וחומרים": "שולחן מודלים וספריית חומרים",
    "שירותי משרד": "2 תאים, אחד מהם נגיש",
    "מרחב מוגן": "מרחב מוגן למשרד, מתחת לממ״ד",
    "מחסן": "", "חדר מערכות": "חשמל, תקשורת ומשאבות",
    "סלון": "גובה כפול 5.00 מ׳, מקרן ומסך 180״ נסתרים בתקרה, ספרייה מאחורי המסך",
    "חדר מכונות בריכה": "משאבות וסינון לבריכה ולג׳קוזי",
    "חדר כושר": "2 הליכונים, אופניים, משקולות",
    "סאונה": "ל־4–6 אנשים", "מקלחת ושירותים": "משרתים את הספא, חדר הכושר והבריכה", "ג׳קוזי": "ל־5–6 אנשים, יציאה ישירה לדק הבריכה",
    "חדר שינה הורים": "מיטה זוגית, פינת ישיבה, יציאה למרפסת",
    "חדר ארונות": "", "מקלחת הורים": "אמבטיה, מקלחון גדול, 2 כיורים ושירותים",
    "ממ״ד": "ביום־יום חדר לימוד ואורחים",
    "חדר כביסה ומצעים": "מכונת כביסה, מייבש, כיור וארון מצעים",
    "חדר הילד הצעיר": "מיטה, שולחן, פינת משחק, מקלחת צמודה",
}
STYLE = {"B": ("קומת מרתף", "קומת מרתף\nמשרד וחניון", "BDD7EE", "DDEBF7", "משרד אדריכלים, חניון ל־6 רכבים וחדר קולנוע. המפלס בגובה הרחוב"),
         "G": ("קומת קרקע", "קומת קרקע\nחלק ציבורי", "F8CBAD", "FCE4D6", "מגורים ואירוח, ביתן ספא ליד הבריכה"),
         "F": ("קומה א׳", "קומה א׳\nחלק פרטי", "C6E0B4", "E2EFDA", "4 סוויטות: הורים, 2 נוער וילד צעיר")}
CIRC_NOTE = {"B": "נתיבי הנסיעה בחניון מופיעים בשורה נפרדת ולא כאן", "G": "כולל מבואת הכניסה ומעבר השירות", "F": "כולל המבואה לסוויטת ההורים"}

bl = Polygon(M.SITE["building_line"])
e = M.EXT_STAIR
holes = unary_union([sbox(5.5, 12.2, 27.5, 34.0), sbox(27.5, 22.05, 36.0, 34.0), sbox(45.5, 20.5, 51.0, 34.0), sbox(*M.POOL_DECK),
                     sbox(e["x0"], e["y0"], e["x1"], e["y1"]), sbox(*M.EXT_LANDING)])
lawn = bl.intersection(sbox(27.5, -5.0, 60.0, 34.0)).difference(holes)
tx0, ty0, tx1, ty1 = M.TERRACE
ec = M.ENGLISH_COURT
OUTDOOR = {
    "B": ("חוץ במפלס המרתף (לא נספר בשטח הבנוי)", [
        ("רחבת כניסה לחניון", Polygon(M.DRIVEWAY).area, 1, "", "מהשער ברחוב אל שער החניון, בלי רמפה. מפלס +87.45"),
        ("רחבת כניסה למשרד", Polygon(M.OFFICE_COURT).area, 1, "", "כניסת לקוחות נפרדת מהרחוב"),
        ("חצר אנגלית", (ec[2] - ec[0]) * (ec[3] - ec[1]), 1, f"{ec[2] - ec[0]:.2f} × {ec[3] - ec[1]:.2f}", "אור טבעי לסטודיו ולסדנה"),
        ("מדרגות כניסה חיצוניות", (e["x1"] - e["x0"]) * (e["y1"] - e["y0"]) + M.rect_area(M.EXT_LANDING), 1, "רוחב 1.50", "20 רומים, מהרחבה אל מרפסת הגג")]),
    "G": ("חוץ במפלס הקרקע (לא נספר בשטח הבנוי)", [
        ("מרפסת גג מעל החניון", (tx1 - tx0) * (ty1 - ty0), 1, f"{tx1 - tx0:.2f} × {ty1 - ty0:.2f}", "פרגולה, פינת אוכל ומטבח חוץ, פינת ישיבה"),
        ("בריכה", M.rect_area(M.POOL), 1, "4.00 × 12.00", "בין הסלון לביתן הספא"),
        ("דק הבריכה", M.rect_area(M.POOL_DECK) - M.rect_area(M.POOL), 1, "", "4 מיטות שיזוף ושמשייה"),
        ("מדשאה וגינה אחורית", lawn.area, 1, "", "בתוך קווי הבניין, מפלס −0.10")]),
    "F": ("מרפסות (לא נספרות בשטח הבנוי)", [
        ("מרפסת הורים והילד הצעיר", M.rect_area(M.BALCONIES[0]), 1, f"{M.BALCONIES[0][2] - M.BALCONIES[0][0]:.2f} × 1.80", "משותפת לחדר ההורים ולחדר הילד הצעיר, עם מחיצה"),
        ("מרפסת נוער 1", M.rect_area(M.BALCONIES[1]), 1, f"{M.BALCONIES[1][2] - M.BALCONIES[1][0]:.2f} × 1.80", "מעקה זכוכית גבוה")]),
}


def dims(r):
    if len(r["rects"]) == 1:
        q = r["rects"][0]
        return f"{q[2] - q[0]:.2f} × {q[3] - q[1]:.2f}"
    return "צורה מורכבת"


BLOCKS = []
for fl in "BGF":
    name, label, strong, light, note = STYLE[fl]
    groups, order = {}, []
    for r in M.rooms_of(fl):
        g = CIRC if r["name"] in CIRC_NAMES else r["group"]
        if g == "תנועה אנכית":
            g = CIRC
        if g not in groups:
            groups[g] = []
            order.append(g)
        a = round(M.room_area(r), 1)
        nt = NOTES.get(r["name"], r.get("note") or "")
        if r["name"] == "חניון":
            bay = round(2.70 * 5.10, 1)
            groups[g].append(("מקום חניה", bay, 6, "שירות", "2.70 × 5.10", "6 מקומות מסומנים, 3 מכל צד של המעבר"))
            groups[g].append(("מעבר נסיעה ותמרון בחניון", round(a - 6 * bay, 1), 1, "שירות", "רוחב 6.00", "שער חניון ברוחב 5.00 מ׳ בחזית הדרום־מערבית"))
            continue
        groups[g].append((r["name"], a, 1, r["cat"], dims(r), nt))
    if CIRC in order:                      # circulation last among the built groups
        order.remove(CIRC)
        order.append(CIRC)
    gl = [(g, groups[g]) for g in order]
    og, items = OUTDOOR[fl]
    gl.append((og, [(n, round(a, 1), q, "חוץ", d, t) for n, a, q, d, t in items]))
    BLOCKS.append(dict(fl=fl, name=name, label=label, strong=strong, light=light, note=note, circ_note=CIRC_NOTE[fl], groups=gl,
                       gross=round(M.gross_area(fl), 1)))

# ---------------------------------------------------------------- workbook
wb = Workbook()
ws = wb.active
ws.title = "פרוגרמה מגרש 84"
ws.sheet_view.rightToLeft = True
wb.properties.title = "פרוגרמה – וילה ומשרד אדריכלים, מגרש 84"
for col, width in {"A": 11, "B": 30, "C": 12, "D": 8, "E": 13, "F": 11, "G": 15, "H": 56}.items():
    ws.column_dimensions[col].width = width
NC = 8


def put(row, col, value, *, f=None, fl=None, al=None, numfmt=None, border=True):
    c = ws.cell(row=row, column=col, value=value)
    c.font = f or font()
    if fl:
        c.fill = fl
    c.alignment = al or align()
    if border:
        c.border = BORDER
    if numfmt:
        c.number_format = numfmt
    return c


def merged(row1, col1, row2, col2, value, **kw):
    put(row1, col1, value, **kw)
    if (row1, col1) != (row2, col2):
        ws.merge_cells(start_row=row1, start_column=col1, end_row=row2, end_column=col2)


merged(1, 1, 1, NC, "פרוגרמה – וילה ומשרד אדריכלים במגרש 84, ראש העין", f=font(16, bold=True), border=False)
merged(2, 1, 2, NC, "השטחים נלקחו מהשרטוטים (נטו, בין הקירות) · זוג הורים, 3 ילדים וכלב · מרתף: משרד וחניון · קרקע: חלק ציבורי · קומה א׳: חלק פרטי",
       f=font(11, color="595959"), border=False)
merged(3, 1, 3, NC, "מקרא: כחול = נתונים שאפשר לשנות · שחור = נוסחאות שמתעדכנות לבד · ירוק נטוי = שטחי חוץ שלא נספרים בשטח הבנוי",
       f=font(10, italic=True, color="595959"), border=False)
ws.row_dimensions[1].height = 28
ws.row_dimensions[2].height = 20
HEADERS = ["קומה", "ייעוד", "שטח ליחידה (מ״ר)", "מס׳", "סה״כ שטח (מ״ר)", "סוג שטח", "מידות בשרטוט (מ׳)", "הערות"]
for i, h in enumerate(HEADERS, start=1):
    put(4, i, h, f=font(bold=True, color="FFFFFF"), fl=fill(HEADER_FILL), al=align("center"))
ws.row_dimensions[4].height = 32

type_dv = DataValidation(type="list", formula1='"עיקרי,שירות,חוץ"', allow_blank=True)
ws.add_data_validation(type_dv)
r = 5
first_data_row = r
floor_ranges = []
for b in BLOCKS:
    start = r
    for group_name, items in b["groups"]:
        merged(r, 2, r, NC, group_name, f=font(bold=True), fl=fill(b["light"]))
        r += 1
        if group_name == CIRC:
            circ_first, circ_last = r, r + len(items) - 1
        for name, area, qty, kind, dm, note in items:
            put(r, 2, name)
            put(r, 3, area, f=font(color=BLUE), al=align("center"), numfmt="#,##0.0")
            put(r, 4, qty, f=font(color=BLUE), al=align("center"), numfmt="0")
            put(r, 5, f"=C{r}*D{r}", al=align("center"), numfmt="#,##0.0")
            put(r, 6, kind, f=font(color=BLUE), al=align("center"))
            put(r, 7, dm or None, f=font(10), al=align("center"))
            put(r, 8, note or None, f=font(10))
            type_dv.add(f"F{r}")
            r += 1
    end = r - 1
    merged(start, 1, end, 1, b["label"], f=font(12, bold=True), fl=fill(b["strong"]), al=align("center", rotation=90))
    f_rng, e_rng = f"$F${start}:$F${end}", f"$E${start}:$E${end}"
    merged(r, 1, r, 4, f"סה״כ שטח נטו – {b['name']} (בלי שטחי חוץ)", f=font(bold=True), fl=fill(b["strong"]))
    put(r, 5, f'=SUMIF({f_rng},"עיקרי",{e_rng})+SUMIF({f_rng},"שירות",{e_rng})', f=font(bold=True), fl=fill(b["strong"]), al=align("center"),
        numfmt="#,##0.0")
    put(r, 6, None, fl=fill(b["strong"]))
    put(r, 7, None, fl=fill(b["strong"]))
    put(r, 8, f'="מתוכם מעברים ותנועה: "&TEXT(SUM(E{circ_first}:E{circ_last}),"0.0")&" מ״ר"', f=font(10, bold=True), fl=fill(b["strong"]))
    floor_ranges.append((b, start, end, circ_first, circ_last, r))
    ws.row_breaks.append(Break(id=r))
    r += 1
last_data_row = r - 1
ws.conditional_formatting.add(f"B{first_data_row}:H{last_data_row}",
                              FormulaRule(formula=[f'$F{first_data_row}="חוץ"'], font=Font(name=FONT, italic=True, color=OUTDOOR_GREEN)))

# ---------------------------------------------------------------- summary by floor
r += 1
merged(r, 1, r, NC, "סיכום שטחים לפי קומות", f=font(12, bold=True, color="FFFFFF"), fl=fill(HEADER_FILL))
r += 1
merged(r, 1, r, 2, "קומה", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
for col, h in zip(range(3, 9), ["שטח עיקרי (מ״ר)", "שטח שירות (מ״ר)", "סה״כ נטו (מ״ר)", "קירות (מ״ר)", "ברוטו בשרטוט (מ״ר)", "חוץ ומרפסות (מ״ר) · הערות"]):
    put(r, col, h, f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
ws.row_dimensions[r].height = 46
r += 1
summary_rows = {}
first_summary = r
for b, start, end, _, _, _ in floor_ranges:
    f_rng, e_rng = f"$F${start}:$F${end}", f"$E${start}:$E${end}"
    merged(r, 1, r, 2, b["name"], f=font(bold=True), fl=fill(b["strong"]))
    put(r, 3, f'=SUMIF({f_rng},"עיקרי",{e_rng})', al=align("center"), numfmt="#,##0.0")
    put(r, 4, f'=SUMIF({f_rng},"שירות",{e_rng})', al=align("center"), numfmt="#,##0.0")
    put(r, 5, f"=C{r}+D{r}", f=font(bold=True), al=align("center"), numfmt="#,##0.0")
    put(r, 6, f"=G{r}-E{r}", al=align("center"), numfmt="#,##0.0")
    put(r, 7, b["gross"], f=font(bold=True, color=BLUE), al=align("center"), numfmt="#,##0.0")
    put(r, 8, f'=TEXT(SUMIF({f_rng},"חוץ",{e_rng}),"#,##0")&" מ״ר חוץ · {b["note"]}"', f=font(10))
    summary_rows[b["name"]] = r
    r += 1
last_summary = r - 1
total_row = r
merged(r, 1, r, 2, "סה״כ", f=font(bold=True), fl=fill("D9D9D9"))
for col_idx, col in zip(range(3, 8), "CDEFG"):
    put(r, col_idx, f"=SUM({col}{first_summary}:{col}{last_summary})", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"), numfmt="#,##0.0")
put(r, 8, "ברוטו = שטח הקומה כולל הקירות, כפי שנמדד בשרטוט", f=font(10), fl=fill("D9D9D9"))

# ---------------------------------------------------------------- circulation by floor
r += 2
merged(r, 1, r, NC, "מעברים ותנועה לפי קומה", f=font(12, bold=True, color="FFFFFF"), fl=fill(HEADER_FILL))
r += 1
merged(r, 1, r, 2, "קומה", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
put(r, 3, "מעברים ותנועה (מ״ר)", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
put(r, 4, "% מהנטו", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
merged(r, 5, r, NC, "הערות", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
ws.row_dimensions[r].height = 46
r += 1
first_circ = r
for b, _, _, cf, cl, _ in floor_ranges:
    merged(r, 1, r, 2, b["name"], f=font(bold=True), fl=fill(b["strong"]))
    put(r, 3, f"=SUM(E{cf}:E{cl})", al=align("center"), numfmt="#,##0.0")
    put(r, 4, f"=IFERROR(C{r}/E{summary_rows[b['name']]},0)", al=align("center"), numfmt="0.0%")
    merged(r, 5, r, NC, b["circ_note"], f=font(10))
    r += 1
merged(r, 1, r, 2, "סה״כ", f=font(bold=True), fl=fill("D9D9D9"))
put(r, 3, f"=SUM(C{first_circ}:C{r - 1})", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"), numfmt="#,##0.0")
put(r, 4, f"=IFERROR(C{r}/E{total_row},0)", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"), numfmt="0.0%")
merged(r, 5, r, NC, "כולל מדרגות ומעלית בכל קומה", f=font(10), fl=fill("D9D9D9"))
ws.row_breaks.append(Break(id=r))

# ---------------------------------------------------------------- vertical circulation and parking data
r += 2
merged(r, 1, r, NC, "מדרגות, מעלית וחניה – נתוני התכנון", f=font(12, bold=True, color="FFFFFF"), fl=fill(HEADER_FILL))
r += 1
s = M.STAIR
design = [
    ("רוחב מהלך מדרגות (מ׳)", s["width"], "0.00", "כל אחד משני המהלכים. בין המהלכים רווח של 15 ס״מ"),
    ("מספר רומים בין קומה לקומה", s["risers"], "0", "10 רומים בכל מהלך, עם משטח ביניים"),
    ("גובה רום (ס״מ)", s["rise"] * 100, "0.0", "הפרש המפלסים 3.50 מ׳ חלקי 20 רומים"),
    ("עומק שלח (ס״מ)", s["tread"] * 100, "0", "2 רומים + שלח = 64 ס״מ, בטווח הנוח 61–65"),
    ("פיר מעלית, מידות פנים (מ׳)", "2.00 × 2.00", None, "2 דלתות: במרתף אל הלובי המשפחתי, בקומות האחרות אל המבואה"),
    ("מקומות חניה בחניון", 4, "0", "כל מקום 2.80 × 5.20 מ׳, בשורה אחת, בלי מעבר נסיעה פנימי"),
    ("רוחב מעבר ההליכה מאחורי הרכבים (מ׳)", 1.5, "0.00", "עם קיר זכוכית אל המשרד וחלונות גג במרפסת שמעל"),
    ("רוחב שער החניון (מ׳)", 5.0, "0.00", "2 שערים, כל אחד ל־2 רכבים, מול רחבת הכניסה"),
    ("שטח המקלט המשותף (מ״ר)", round(M.room_area([r for r in M.ROOMS if r["id"] == "B14"][0]), 1), "0.0", "לכ־25 איש. דלת הדף מצד המשפחה ודלת הדף מצד המשרד"),
]
for label, value, numfmt, note in design:
    merged(r, 1, r, 2, label, f=font(bold=True))
    put(r, 3, value, al=align("center"), numfmt=numfmt)
    merged(r, 4, r, NC, note, f=font(10))
    r += 1

# ---------------------------------------------------------------- utility pillars on the street front
r += 1
merged(r, 1, r, NC, "פילרים ותשתיות בחזית המגרש (חוץ, לא נספרים בשטח הבנוי)", f=font(12, bold=True, color="FFFFFF"), fl=fill(HEADER_FILL))
r += 1
merged(r, 1, r, 2, "פילר", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
for col, h in zip(range(3, 8), ["מידות פנים, רוחב×עומק (ס״מ)", "גובה (ס״מ)", "מידות חוץ, רוחב×עומק (ס״מ)", "שטח (מ״ר)", "הדלתות פונות אל"]):
    put(r, col, h, f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
put(r, 8, "שימוש ומקור המידות", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"))
ws.row_dimensions[r].height = 46
r += 1
first_pil = r
for pl in M.PILLARS:
    x0, y0, x1, y1 = pl["rect"]
    along, deep = (x1 - x0, y1 - y0) if pl["face"] == "S" else (y1 - y0, x1 - x0)
    merged(r, 1, r, 2, pl["name"], f=font(bold=True))
    put(r, 3, f'{pl["inner"][0] * 100:.0f} × {pl["inner"][1] * 100:.0f}', al=align("center"))
    put(r, 4, round(pl["h"] * 100), f=font(color=BLUE), al=align("center"), numfmt="0")
    put(r, 5, f"{along * 100:.0f} × {deep * 100:.0f}", al=align("center"))
    put(r, 6, round(along * deep, 2), f=font(color=BLUE), al=align("center"), numfmt="0.00")
    put(r, 7, {"W": "הרחוב", "E": "המגרש", "S": "רחבת הכניסה"}[pl["face"]], al=align("center"))
    put(r, 8, pl["use"] + ". " + pl["std"], f=font(10))
    ws.row_dimensions[r].height = 30
    r += 1
merged(r, 1, r, 5, "סה״כ שטח הפילרים", f=font(bold=True), fl=fill("D9D9D9"))
put(r, 6, f"=SUM(F{first_pil}:F{r - 1})", f=font(bold=True), fl=fill("D9D9D9"), al=align("center"), numfmt="0.00")
put(r, 7, None, fl=fill("D9D9D9"))
put(r, 8, "חשמל, תקשורת ומים ליד שער המשרד. גז ופחים ליד שער הרכב, במרחק של כ־15 מ׳ מפילר החשמל", f=font(10), fl=fill("D9D9D9"))
r += 1

# ---------------------------------------------------------------- checks against the plot
r += 1
merged(r, 1, r, NC, "בדיקות מול המגרש ודרישות התרגיל", f=font(12, bold=True, color="FFFFFF"), fl=fill(HEADER_FILL))
r += 1
g_row, b_row, f_row = summary_rows["קומת קרקע"], summary_rows["קומת מרתף"], summary_rows["קומה א׳"]
plot_row, meas_row, bl_row, min_row, max_row, net_row, gross_row = r, r + 1, r + 2, r + 3, r + 4, r + 5, r + 6
g_out = [fr for fr in floor_ranges if fr[0]["fl"] == "G"][0]
checks = [
    ("שטח המגרש הרשום (מ״ר)", M.SITE["area_registered"], "#,##0", "נתון מהתרגיל וממפת המדידה", True),
    ("שטח המגרש לפי קואורדינטות המדידה (מ״ר)", round(M.SITE["area_measured"]), "#,##0", "חושב מ־6 נקודות הגבול בקובץ המודד. השרטוטים לפי המדידה", True),
    ("שטח בתוך קווי הבניין (מ״ר)", round(M.SITE["buildable_area"]), "#,##0", "קווי בניין שהונחו: קדמי 5 מ׳, צדדי 3 מ׳, אחורי 5 מ׳. לוודא מול התב״ע", True),
    ("שטח בנוי מינימלי נדרש (מ״ר)", 550, "#,##0", "דרישת התרגיל", True),
    ("שטח בנוי מקסימלי מותר (מ״ר)", 1200, "#,##0", "דרישת התרגיל", True),
    ("סה״כ שטח נטו (מ״ר)", f"=E{total_row}", "#,##0.0", "סכום החדרים בשלוש הקומות", False),
    ("סה״כ שטח ברוטו (מ״ר)", f"=G{total_row}", "#,##0.0", "כולל קירות. זה המספר המחמיר", False),
    ("עמידה בטווח 550–1,200", f'=IF(AND(C{gross_row}>=C{min_row},C{gross_row}<=C{max_row}),"בתוך הטווח","מחוץ לטווח")', None, "לפי הברוטו", False),
    ("שטח פנוי עד המקסימום (מ״ר)", f"=C{max_row}-C{gross_row}", "#,##0.0", "", False),
    ("תכסית קומת הקרקע", f"=IFERROR(G{g_row}/C{plot_row},0)", "0.0%", "ברוטו קומת הקרקע חלקי שטח המגרש הרשום", False),
    ("תכסית כל המבנים, כולל המרתף הבולט", f"=IFERROR(({M.gross_area('B'):.1f}+{M.gross_area('G') - M.rect_area((5.5, 22.05, 27.5, 34.0)):.1f})/C{plot_row},0)", "0.0%",
     "היטל המרתף + הסלון + ביתן הספא", False),
    ("יחס שטח בנוי למגרש", f"=IFERROR(C{gross_row}/C{plot_row},0)", "0.0%", "ברוטו חלקי שטח המגרש הרשום", False),
    ("ניצול השטח שבתוך קווי הבניין", f"=IFERROR(({M.gross_area('B'):.1f}+{M.gross_area('G') - M.rect_area((5.5, 22.05, 27.5, 34.0)):.1f})/C{bl_row},0)", "0.0%",
     "היטל המבנים חלקי השטח המותר לבנייה", False),
]
for label, value, numfmt, note, is_input in checks:
    merged(r, 1, r, 2, label, f=font(bold=True))
    put(r, 3, value, f=font(bold=not is_input, color=BLUE if is_input else BLACK), fl=fill(INPUT_FILL) if is_input else None, al=align("center"), numfmt=numfmt)
    merged(r, 4, r, NC, note or None, f=font(10))
    if label.startswith("עמידה"):
        status_row = r
    r += 1
ws.conditional_formatting.add(f"C{status_row}", FormulaRule(formula=[f'C{status_row}="בתוך הטווח"'], fill=fill("C6EFCE"), font=Font(name=FONT, bold=True, color="006100")))
ws.conditional_formatting.add(f"C{status_row}", FormulaRule(formula=[f'C{status_row}="מחוץ לטווח"'], fill=fill("FFC7CE"), font=Font(name=FONT, bold=True, color="9C0006")))

# ---------------------------------------------------------------- levels
r += 1
merged(r, 1, r, NC, "מפלסים", f=font(12, bold=True, color="FFFFFF"), fl=fill(HEADER_FILL))
r += 1
for label, rel, note in (("קומת מרתף", -3.50, "בגובה הרחוב (הרחוב בערך +87.0). גובה נטו 3.00 מ׳"), ("קומת קרקע ±0.00", 0.0, "בגובה הגינה האחורית. גובה נטו 3.00 מ׳, בסלון 5.00 מ׳"),
                        ("קומה א׳", 3.50, "גובה נטו 2.90 מ׳"), ("מעקה הגג העליון", 7.30, "גג קומה א׳ במפלס +6.80")):
    merged(r, 1, r, 2, label, f=font(bold=True))
    put(r, 3, rel, al=align("center"), numfmt='+0.00;-0.00;"±"0.00')
    put(r, 4, f"=C{r}+{M.ABS0}", al=align("center"), numfmt='"+"0.00')
    merged(r, 5, r, NC, note, f=font(10))
    r += 1

# ---------------------------------------------------------------- notes
r += 1
merged(r, 1, r, NC, "הערות", f=font(12, bold=True))
r += 1
notes = [
    "השטחים בטבלה הם שטחי נטו שנמדדו מהשרטוטים (בין פני הקירות). הברוטו בכחול נמדד מקווי המתאר של כל קומה בשרטוט.",
    "איך לערוך: המספרים בכחול הם נתונים. אם משנים חדר בשרטוט, מעדכנים כאן את השטח שלו, וכל הסכומים והבדיקות מתעדכנים לבד.",
    "מה השתנה מהפרוגרמה הקודמת: חדר הקולנוע ירד למרתף, חדר הגיימינג אוחד עם חדר המשפחה בקומת הקרקע, הספא וחדר הכושר עברו לביתן נפרד ליד הבריכה, "
    "והבריכה היא 4×12 מ׳ כדי להישאר בתוך קווי הבניין.",
    "לבדוק מול התב״ע של המגרש: קווי בניין, אחוזי בנייה, מספר קומות וגובה, תקן חניה, והאם קומה בגובה הרחוב נחשבת מרתף.",
    "סוג שטח: עיקרי / שירות / חוץ, לפי המקובל (ממ״ד ומרחב מוגן, מדרגות, מעלית, חניון, מחסן וחדרי מערכות = שירות). כדאי לוודא מול המרצה.",
    "פילרים: מידות גומחת החשמל לפי חברת החשמל (גומחה ל־2–3 מונים). מים, תקשורת וגז לפי מידות של גומחות טרומיות מקטלוג יצרן. מסתור הפחים לפי מידות פח של 360 ליטר. "
    "המיקום והמידות הסופיים נקבעים מול חברת החשמל, תאגיד המים, חברת הגז וההנחיות המרחביות של העירייה.",
]
for n in notes:
    merged(r, 1, r, NC, n, f=font(10), border=False)
    ws.row_dimensions[r].height = 30
    r += 1

ws.freeze_panes = "A5"
ws.print_title_rows = "4:4"
ws.page_setup.orientation = "landscape"
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.print_options.horizontalCentered = True
ws.page_margins.left = ws.page_margins.right = 0.4
ws.page_margins.top = ws.page_margins.bottom = 0.5
wb.save(OUT)
print("saved", OUT, "rows:", r - 1)
