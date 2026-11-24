"""Assemble the delivery folder: JPEG copies of the renders for the PDF, final PDF, CAD, IFC, 3D and program files, and a zip."""
import os
import shutil
import subprocess
import sys
import zipfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
FINAL = os.path.join(HERE, "out", "r3d", "final")
JPG = os.path.join(HERE, "out", "r3d", "jpg")
DEL = os.path.join(SP, "villa84_deliver", "villa84")
PY = sys.executable
os.makedirs(JPG, exist_ok=True)

VIEWS = ["cut_B_labelled", "cut_G_labelled", "cut_F_labelled", "top", "aerial_front", "aerial_back", "aerial_side", "street", "garden", "terrace"]
for v in VIEWS:
    Image.open(os.path.join(FINAL, v + ".png")).convert("RGB").save(os.path.join(JPG, v + ".jpg"), quality=90)

subprocess.run([PY, os.path.join(HERE, "sheets.py"), os.path.join(HERE, "out", "sheets.html"), JPG], check=True, cwd=HERE)
subprocess.run(["node", os.path.join(HERE, "shoot.js"), os.path.join(HERE, "out", "sheets.html"), os.path.join(HERE, "out")], check=True, cwd=HERE)

if os.path.isdir(DEL):
    for root, dirs, files in os.walk(DEL):
        for fn in files:
            os.unlink(os.path.join(root, fn))
dirs = {k: os.path.join(DEL, k) for k in ("01-drawings-pdf", "01-drawings-pdf/png", "02-autocad-dxf", "03-revit-ifc", "04-3d", "04-3d/renders", "05-program",
                                           "06-sketchup-living-room")}
for d in dirs.values():
    os.makedirs(d, exist_ok=True)
out = os.path.join(HERE, "out")
shutil.copy(os.path.join(out, "villa84-drawings.pdf"), dirs["01-drawings-pdf"])
names = ["site-plan", "basement-architectural", "ground-architectural", "first-architectural", "basement-furniture", "ground-furniture",
         "first-furniture", "sections", "3d-floors", "3d-exterior"]
for i, n in enumerate(names, start=1):
    shutil.copy(os.path.join(out, f"sheet-{i:02d}.png"), os.path.join(dirs["01-drawings-pdf/png"], f"{i:02d}-{n}.png"))
for fn in sorted(os.listdir(os.path.join(out, "cad"))):
    if fn.endswith(".dxf"):
        shutil.copy(os.path.join(out, "cad", fn), dirs["02-autocad-dxf"])
shutil.copy(os.path.join(out, "deliver", "villa84.ifc"), dirs["03-revit-ifc"])
for fn in sorted(os.listdir(os.path.join(out, "deliver"))):
    if fn.endswith(".glb"):
        shutil.copy(os.path.join(out, "deliver", fn), dirs["04-3d"])
rn = {"cut_B_labelled": "01-floor-basement-open", "cut_G_labelled": "02-floor-ground-open", "cut_F_labelled": "03-floor-first-open", "top": "04-site-top",
      "aerial_front": "05-aerial-from-street", "aerial_back": "06-aerial-garden-and-pool", "aerial_side": "07-aerial-side", "street": "08-street-eye-level",
      "garden": "09-garden-living-room-pool", "terrace": "10-roof-terrace-pergola"}
for v, n in rn.items():
    shutil.copy(os.path.join(FINAL, v + ".png"), os.path.join(dirs["04-3d/renders"], n + ".png"))
shutil.copy(os.path.join(out, "deliver", "villa84-program.xlsx"), dirs["05-program"])
sk = os.path.join(out, "sk")
for fn in sorted(os.listdir(sk)):
    if fn.startswith("living-room-furniture-dimensions") and fn.endswith((".pdf", ".png")):
        shutil.copy(os.path.join(sk, fn), dirs["06-sketchup-living-room"])
shutil.copy(os.path.join(HERE, "README-he.txt"), os.path.join(DEL, "README-he.txt"))

zpath = os.path.join(SP, "villa84_deliver", "villa84-all-files.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(DEL):
        for fn in sorted(files):
            full = os.path.join(root, fn)
            z.write(full, os.path.relpath(full, os.path.dirname(DEL)))
print("zip", zpath, f"{os.path.getsize(zpath) / 1e6:.1f} MB")
for root, _, files in sorted(os.walk(DEL)):
    for fn in sorted(files):
        print(f"  {os.path.relpath(os.path.join(root, fn), DEL):60s} {os.path.getsize(os.path.join(root, fn)) / 1024:9.0f} KB")
