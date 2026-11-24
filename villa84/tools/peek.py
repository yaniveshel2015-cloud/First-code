"""Render a region of a floor canvas to PNG for close checking: python peek.py FL MODE x0 y0 x1 y1 scale out.png"""
import subprocess, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "villa84"))
import draw as D
from sheetlib import CSS, View, render
fl, mode = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, sc = map(float, sys.argv[3:8])
out = sys.argv[8]
v = View(x0, y0, x1, y1, sc, 2, 2)
svg = render(D.floor_canvas(fl, mode), v, text_k=1.15)
w, h = v.w + 4, v.h + 4
html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS} body{{width:{w}mm}}</style></head><body>'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}" style="background:#fff">{svg}</svg></body></html>')
hp = out + ".html"
open(hp, "w", encoding="utf-8").write(html)
js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:%d,height:%d}});"
      "await p.goto('file://%s');await p.screenshot({path:'%s',fullPage:true});await b.close();})();") % (int(w * 3.78) + 4, int(h * 3.78) + 4, os.path.abspath(hp), os.path.abspath(out))
subprocess.run(["node", "-e", js], check=True)
