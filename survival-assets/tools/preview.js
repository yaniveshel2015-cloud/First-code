// Builds gallery.html (browse everything locally) + preview contact sheets in previews/
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..');
const idx = JSON.parse(fs.readFileSync(path.join(__dirname, 'index.json'), 'utf8'));
const CATS = [
  ['01-characters', 'דמויות'], ['02-backgrounds', 'רקעים'], ['03-speech-bubbles', 'בועות דיבור'], ['04-props', 'אביזרים וקישוטים'], ['05-frames-and-signs', 'שלטים, מסגרות ומגילות'],
];
const css = `body{margin:0;font-family:'DejaVu Sans',Arial,sans-serif;background:#F6EBD3;color:#3B2414;direction:rtl}
h1{margin:0;padding:28px 32px 6px;font-size:34px}h2{margin:0;padding:22px 32px 8px;font-size:26px;color:#8B4513}p.sub{margin:0 32px 8px;color:#6B4A2E}
.grid{display:grid;gap:14px;padding:8px 32px 24px}
.card{background:#fff;border-radius:14px;box-shadow:0 2px 6px rgba(60,30,10,.15);overflow:hidden;display:flex;flex-direction:column}
.img{background-color:#EFE6D2;background-image:linear-gradient(45deg,#E4D8BE 25%,transparent 25%,transparent 75%,#E4D8BE 75%),linear-gradient(45deg,#E4D8BE 25%,transparent 25%,transparent 75%,#E4D8BE 75%);background-size:20px 20px;background-position:0 0,10px 10px;display:flex;align-items:center;justify-content:center;padding:8px;flex:1}
.img img{max-width:100%;max-height:100%;object-fit:contain;display:block}
.cap{padding:6px 10px 8px;font-size:13px;line-height:1.35}.cap b{display:block;font-weight:600}.cap code{direction:ltr;display:block;color:#8a7560;font-size:11px;text-align:left}`;
const card = (e, h, showFile = true) => `<div class="card"><div class="img" style="height:${h}px"><img src="${e.file}" loading="lazy"></div><div class="cap"><b>${e.he}</b>${showFile ? `<code>${e.file}</code>` : ''}</div></div>`;
const section = (title, entries, cols, h, sub = '') => `<h2>${title}</h2>${sub ? `<p class="sub">${sub}</p>` : ''}<div class="grid" style="grid-template-columns:repeat(${cols},1fr)">${entries.map((e) => card(e, h)).join('')}</div>`;

function gallery() {
  let body = `<h1>ערכת הישרדות – גלריית תמונות למצגת</h1><p class="sub">${idx.length} תמונות PNG עם רקע שקוף (חוץ מהרקעים). לחיצה ימנית על תמונה ← "שמור תמונה בשם", או פשוט לקחת את הקובץ מהתיקייה שמופיעה מתחת לכל תמונה.</p>`;
  for (const [dir, he] of CATS) {
    const es = idx.filter((e) => e.file.startsWith(dir + '/'));
    if (dir === '01-characters') {
      const groups = [...new Set(es.map((e) => e.file.split('/')[1]))];
      for (const g of groups) body += section(`${he} – ${es.find((e) => e.file.split('/')[1] === g).he.split(' – ')[0]}`, es.filter((e) => e.file.split('/')[1] === g), 5, 260);
    } else body += section(he, es, dir === '02-backgrounds' ? 3 : 4, dir === '02-backgrounds' ? 240 : 220);
  }
  return `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ערכת הישרדות</title><style>${css}</style></head><body>${body}</body></html>`;
}
fs.writeFileSync(path.join(ROOT, 'gallery.html'), gallery());

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  fs.mkdirSync(path.join(ROOT, 'previews'), { recursive: true });
  const shoot = async (name, html, width) => {
    await page.setViewportSize({ width, height: 800 });
    fs.writeFileSync(path.join(ROOT, '_tmp.html'), `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>${css} .cap code{display:none}</style></head><body>${html}</body></html>`);
    await page.goto('file://' + path.join(ROOT, '_tmp.html'));
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => Promise.all([...document.images].map((i) => i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; }))));
    await page.screenshot({ path: path.join(ROOT, 'previews', name + '.png'), fullPage: true });
  };
  const by = (dir) => idx.filter((e) => e.file.startsWith(dir + '/'));
  const chars = by('01-characters').filter((e) => !e.file.includes('avatars'));
  const charSheet = `<h1>דמויות – 9 דמויות × 10 תנוחות</h1><div class="grid" style="grid-template-columns:repeat(10,1fr);gap:8px">${chars.map((e) => `<div class="card"><div class="img" style="height:190px"><img src="${e.file}"></div><div class="cap" style="font-size:11px">${e.he.split(' – ')[1]}</div></div>`).join('')}</div>`
    + section('תמונות פרופיל עגולות', by('01-characters/avatars'), 9, 120);
  await shoot('1-characters', charSheet, 1500);
  await shoot('2-backgrounds', section('רקעים (1920×1080)', by('02-backgrounds'), 3, 260), 1500);
  await shoot('3-speech-bubbles', section('בועות דיבור', by('03-speech-bubbles'), 5, 160), 1500);
  await shoot('4-props', section('אביזרים וקישוטים', by('04-props'), 7, 170), 1500);
  await shoot('5-frames-and-signs', section('שלטים, מסגרות ומגילות', by('05-frames-and-signs'), 6, 170), 1500);
  fs.unlinkSync(path.join(ROOT, '_tmp.html'));
  await browser.close();
  console.log('previews done');
})();
