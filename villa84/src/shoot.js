// Render the A1 sheet HTML to a true-scale PDF and one PNG per sheet.
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [htmlPath, outDir, only] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 3179, height: 2245 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(htmlPath));
  await page.waitForLoadState('networkidle');
  if (!only) {
    await page.pdf({ path: path.join(outDir, 'villa84-drawings.pdf'), width: '841mm', height: '594mm', printBackground: true, preferCSSPageSize: true });
  }
  const sheets = await page.$$('.sheet');
  for (let i = 0; i < sheets.length; i++) {
    if (only && String(i + 1) !== only) continue;
    await sheets[i].screenshot({ path: path.join(outDir, `sheet-${String(i + 1).padStart(2, '0')}.png`) });
  }
  await browser.close();
  console.log('saved', sheets.length, 'sheets');
})();
