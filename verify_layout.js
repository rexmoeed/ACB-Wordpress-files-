const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  for (const [name, w, h] of [['mobile', 390, 844], ['desktop', 1200, 900]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    await page.goto('https://americacustomboxes.com/product/hair-extension-tuck-boxes/?v=' + Date.now(), {
      waitUntil: 'networkidle',
      timeout: 90000,
    });
    await page.waitForTimeout(2000);

    await page.waitForSelector('.elementor-element-5cfb8e5', { timeout: 30000 });

    const layout = await page.evaluate(() => {
      const q = (sel) => document.querySelector(sel)?.getBoundingClientRect();
      const heroEl = document.querySelector('.elementor-element-5cfb8e5');
      const hero = q('.elementor-element-5cfb8e5');
      const gallery = q('.elementor-element-729f645');
      const title = q('.elementor-element-63ce159');
      const form = q('.elementor-element-acbquote1');
      const specs = q('.elementor-element-acbspecs1');
      const dd = document.querySelector('.elementor-element-dd570a0');
      const r = (el) => el ? { x: Math.round(el.x), y: Math.round(el.y), w: Math.round(el.width), h: Math.round(el.height) } : null;
      return {
        heroFound: !!heroEl,
        heroDisplay: heroEl ? getComputedStyle(heroEl).display : null,
        ddDisplay: dd ? getComputedStyle(dd).display : null,
        gallery: r(gallery), title: r(title), form: r(form), specs: r(specs),
        formBelowTitle: form && title ? form.top > title.bottom - 5 : null,
        specsBelowForm: specs && form ? specs.top > form.bottom - 5 : null,
        formFullWidth: form && hero ? form.width >= hero.width * 0.9 : null,
        specsFullWidth: specs && hero ? specs.width >= hero.width * 0.9 : null,
        galleryLeftOfTitle: gallery && title ? gallery.right <= title.left + 20 && gallery.top < title.bottom : null,
      };
    });

    await page.screenshot({ path: `E:/America Custom Boxes/verify-${name}.png`, fullPage: true });
    console.log(name.toUpperCase(), JSON.stringify(layout, null, 2));
    await page.close();
  }
  await browser.close();
})();
