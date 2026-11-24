// Overlay Hebrew room names (and a title) on a render: node label.js render.png labels.json out.png "title" ["subtitle"]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [png, labelsPath, out, title, sub] = process.argv.slice(2);
  const labels = labelsPath && labelsPath !== '-' ? JSON.parse(fs.readFileSync(labelsPath, 'utf8')) : [];
  const b64 = fs.readFileSync(png).toString('base64');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  await page.setContent(`<img id="i" src="data:image/png;base64,${b64}">`);
  const size = await page.evaluate(() => new Promise(r => { const i = document.getElementById('i'); const f = () => r([i.naturalWidth, i.naturalHeight]); i.complete ? f() : i.onload = f; }));
  const [w, h] = size;
  await page.setViewportSize({ width: w, height: h });
  const k = w / 1600;
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const spans = labels.map(l => {
    const area = l.area ? `<small><span dir="ltr">${l.area.toFixed(1)}</span> מ״ר</small>` : '';
    const u = Math.min(Math.max(l.u, 0.045), 0.955), v = Math.min(Math.max(l.v, 0.03), 0.965);
    return `<div class="l ${l.kind}" style="left:${(u * 100).toFixed(2)}%;top:${(v * 100).toFixed(2)}%"><b>${esc(l.name)}</b>${area}</div>`;
  }).join('');
  const html = `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>
    html,body{margin:0;padding:0;background:#fff}
    .wrap{position:relative;width:${w}px;height:${h}px;overflow:hidden;font-family:"Liberation Sans","DejaVu Sans",sans-serif}
    img{position:absolute;left:0;top:0;width:${w}px;height:${h}px}
    .l{position:absolute;transform:translate(-50%,-50%);background:rgba(255,255,255,.9);border:${1 * k}px solid rgba(0,0,0,.55);border-radius:${4 * k}px;
       padding:${2 * k}px ${6 * k}px ${3 * k}px;text-align:center;white-space:nowrap;line-height:1.15;color:#111;direction:rtl}
    .l b{display:block;font-size:${12.5 * k}px;font-weight:700}
    .l small{display:block;font-size:${10 * k}px;color:#444}
    .l.site{background:rgba(40,40,40,.82);color:#fff;border-color:rgba(255,255,255,.6)}
    .t{position:absolute;right:${22 * k}px;top:${18 * k}px;background:rgba(255,255,255,.93);padding:${9 * k}px ${16 * k}px;border-radius:${5 * k}px;direction:rtl;text-align:right;
       border:${1 * k}px solid rgba(0,0,0,.35)}
    .t b{display:block;font-size:${24 * k}px} .t span{display:block;font-size:${14 * k}px;color:#444;margin-top:${3 * k}px}
  </style></head><body><div class="wrap"><img src="data:image/png;base64,${b64}">${spans}
  ${title ? `<div class="t"><b>${esc(title)}</b>${sub ? `<span>${esc(sub)}</span>` : ''}</div>` : ''}</div></body></html>`;
  await page.setContent(html);
  await page.waitForLoadState('networkidle');
  // push overlapping labels apart vertically
  await page.evaluate(() => {
    const els = [...document.querySelectorAll('.l')];
    const off = els.map(() => 0);
    for (let it = 0; it < 12; it++) {
      let moved = false;
      const rs = els.map(e => e.getBoundingClientRect());
      for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
        const a = rs[i], b = rs[j];
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox > 2 && oy > 1) {
          const d = oy / 2 + 2, up = (a.top + a.bottom) <= (b.top + b.bottom) ? i : j, dn = up === i ? j : i;
          off[up] -= d; off[dn] += d; moved = true;
        }
      }
      els.forEach((e, i) => { e.style.transform = `translate(-50%, calc(-50% + ${off[i]}px))`; });
      if (!moved) break;
    }
  });
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
  await browser.close();
  console.log('labelled', path.basename(out), labels.length);
})();
