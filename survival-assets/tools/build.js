// Renders every asset to SVG + transparent PNG.  usage: node build.js [filter]
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..');
const modules = ['characters', 'backgrounds', 'bubbles', 'props', 'frames'].filter((m) => fs.existsSync(path.join(__dirname, m + '.js')));
(async () => {
  const filter = process.argv[2] || '';
  const assets = modules.flatMap((m) => require('./' + m)()).filter((a) => (a.dir + '/' + a.name).includes(filter));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const index = [];
  for (const a of assets) {
    const W = Math.round(a.w * (a.scale || 1)), H = Math.round(a.h * (a.scale || 1));
    const svgDir = path.join(ROOT, 'svg', a.dir), pngDir = path.join(ROOT, a.dir);
    fs.mkdirSync(svgDir, { recursive: true }); fs.mkdirSync(pngDir, { recursive: true });
    fs.writeFileSync(path.join(svgDir, a.name + '.svg'), a.svg);
    const scaled = a.svg.replace(/width="[\d.]+" height="[\d.]+"/, `width="${W}" height="${H}"`);
    await page.setViewportSize({ width: W, height: H });
    await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:transparent;overflow:hidden}svg{display:block}</style></head><body>${scaled}</body></html>`);
    await page.screenshot({ path: path.join(pngDir, a.name + '.png'), omitBackground: !a.opaque, clip: { x: 0, y: 0, width: W, height: H } });
    index.push({ file: `${a.dir}/${a.name}.png`, he: a.he, w: W, h: H });
  }
  await browser.close();
  if (!filter) fs.writeFileSync(path.join(__dirname, 'index.json'), JSON.stringify(index, null, 1));
  console.log('rendered', assets.length);
})();
