"""Add the SketchUp dimension sheets to the delivery package and the README."""
B = "/tmp/claude-0/-home-user-First-code/bd5e9e04-ec04-58b0-88a8-01d35cd61986/scratchpad/villa84/"


def patch(path, reps):
    s = open(path, encoding="utf-8").read()
    for a, b in reps:
        assert s.count(a) == 1, (path, a[:70], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)


patch(B + "pack.py", [
    ('''dirs = {k: os.path.join(DEL, k) for k in ("01-drawings-pdf", "01-drawings-pdf/png", "02-autocad-dxf", "03-revit-ifc", "04-3d", "04-3d/renders", "05-program")}''',
     '''dirs = {k: os.path.join(DEL, k) for k in ("01-drawings-pdf", "01-drawings-pdf/png", "02-autocad-dxf", "03-revit-ifc", "04-3d", "04-3d/renders", "05-program",
                                           "06-sketchup-living-room")}'''),
    ('''shutil.copy(os.path.join(HERE, "README-he.txt"), os.path.join(DEL, "README-he.txt"))''',
     '''sk = os.path.join(out, "sk")
for fn in sorted(os.listdir(sk)):
    if fn.startswith("living-room-furniture-dimensions") and fn.endswith((".pdf", ".png")):
        shutil.copy(os.path.join(sk, fn), dirs["06-sketchup-living-room"])
shutil.copy(os.path.join(HERE, "README-he.txt"), os.path.join(DEL, "README-he.txt"))'''),
])

patch(B + "README-he.txt", [
    ('''05-program
  villa84-program.xlsx   הפרוגרמה החדשה לפי קומות. השטחים נמדדו מהשרטוטים.
''', '''05-program
  villa84-program.xlsx   הפרוגרמה החדשה לפי קומות. השטחים נמדדו מהשרטוטים.

06-sketchup-living-room
  living-room-furniture-dimensions.pdf   5 דפי A3 עם כל המידות לבניית הסלון והרהיט בסקצ'אפ:
    1 תוכנית הסלון 1:50 ורשימת חלקים עם מידות ומיקום (X, Y, Z)
    2 חתך לאורך הסלון דרך המקרן והמסך, וחתך של הספה
    3 חזית קיר המדיה: ספרייה ולוחות שיש
    4 יחידת המקרן והליפט, במצב סגור ופתוח
    5 המסך הפתוח, סדר בנייה מוצע וחומרים
  וגם כל דף כתמונת PNG.
'''),
])
print("patched")
