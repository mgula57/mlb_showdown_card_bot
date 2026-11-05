// node shoot.js <html_path> <out_dir> : 2x captures of each sheet (#pdf-N)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [html, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 2 });
  for (const [i, slug] of [[1, 'al'], [2, 'nl']]) {
    await page.goto('file://' + path.resolve(html) + '#pdf-' + i);
    await page.reload();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(out, `gold_gloves_${i}_${slug}.png`), clip: { x: 0, y: 0, width: 1080, height: 1350 } });
  }
  await browser.close();
})();
