// Crop a region of one sheet at high zoom: node crop.js html sheetNo x y w h (mm on sheet) out.png [scale]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [htmlPath, n, x, y, w, h, out, scale] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 3179, height: 2245 }, deviceScaleFactor: Number(scale || 2.2) });
  await page.goto('file://' + path.resolve(htmlPath));
  const sheets = await page.$$('.sheet');
  const bb = await sheets[Number(n) - 1].boundingBox();
  const k = 3179 / 841;
  await page.screenshot({ path: out, fullPage: true, clip: { x: bb.x + x * k, y: bb.y + y * k, width: w * k, height: h * k } });
  await browser.close();
})();
