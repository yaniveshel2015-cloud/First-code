// Render A3 sheets (420 x 297 mm) to a true-scale PDF and one PNG per sheet: node shoot_a3.js in.html outDir baseName
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [htmlPath, outDir, base] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1588, height: 1123 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(htmlPath));
  await page.waitForLoadState('networkidle');
  const sheets = await page.$$('.sheet');
  for (let i = 0; i < sheets.length; i++) {
    const bb = await sheets[i].boundingBox();
    await page.screenshot({ path: path.join(outDir, `${base}-${i + 1}.png`), fullPage: true, clip: { x: bb.x, y: bb.y, width: bb.width, height: bb.height } });
  }
  const p2 = await browser.newPage();
  await p2.goto('file://' + path.resolve(htmlPath));
  await p2.waitForLoadState('networkidle');
  await p2.pdf({ path: path.join(outDir, base + '.pdf'), width: '420mm', height: '297mm', printBackground: true, preferCSSPageSize: true });
  await browser.close();
  console.log('saved', sheets.length, 'sheets');
})();
