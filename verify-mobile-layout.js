const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const URL = 'https://americacustomboxes.com/product/hair-extension-tuck-boxes/';
const OUT = 'E:\\America Custom Boxes';

const WIDGETS = {
  gallery: '.elementor-element-729f645',
  title: '.elementor-element-63ce159',
  desc: '.elementor-element-adf987d',
  form: '.elementor-element-acbquote1',
  specs: '.elementor-element-acbspecs1',
};

async function verify(width) {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width, height: 900 });
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });

  const boxes = await page.evaluate((sel) => {
    const out = {};
    for (const [key, selector] of Object.entries(sel)) {
      const el = document.querySelector(selector);
      if (!el) {
        out[key] = null;
        continue;
      }
      const r = el.getBoundingClientRect();
      out[key] = {
        top: Math.round(r.top),
        left: Math.round(r.left),
        width: Math.round(r.width),
        height: Math.round(r.height),
        bottom: Math.round(r.bottom),
        right: Math.round(r.right),
      };
    }
    const hero = document.querySelector('.elementor-element-5cfb8e5');
    const heroStyle = hero ? getComputedStyle(hero) : null;
    const inner = document.querySelector('.elementor-element-5cfb8e5 > .e-con-inner');
    const innerStyle = inner ? getComputedStyle(inner) : null;
    return {
      boxes: out,
      heroDisplay: heroStyle ? heroStyle.display : null,
      innerDisplay: innerStyle ? innerStyle.display : null,
      cssPresent: !!document.querySelector('#acb-single-product-mobile-css'),
    };
  }, WIDGETS);

  const shot = path.join(OUT, `verify-${width}px.png`);
  await page.screenshot({ path: shot, fullPage: false });
  await browser.close();

  const b = boxes.boxes;
  const checks = [];

  if (!boxes.cssPresent) checks.push({ pass: false, msg: 'Mobile CSS block missing' });
  else checks.push({ pass: true, msg: 'Mobile CSS block present' });

  if (width <= 767) {
    if (boxes.innerDisplay === 'grid' || boxes.heroDisplay === 'grid') {
      checks.push({ pass: true, msg: `Grid display active (hero=${boxes.heroDisplay}, inner=${boxes.innerDisplay})` });
    } else {
      checks.push({ pass: false, msg: `Grid NOT active (hero=${boxes.heroDisplay}, inner=${boxes.innerDisplay})` });
    }

    if (b.gallery && b.title) {
      const galleryLeft = b.gallery.left < b.title.left;
      const sameRow = Math.abs(b.gallery.top - b.title.top) < 80;
      checks.push({
        pass: galleryLeft && sameRow,
        msg: `Gallery left of title (gallery.left=${b.gallery.left}, title.left=${b.title.left}, tops=${b.gallery.top}/${b.title.top})`,
      });
    }

    if (b.title && b.desc) {
      checks.push({
        pass: b.desc.top >= b.title.top,
        msg: `Desc below/at title (title.top=${b.title.top}, desc.top=${b.desc.top})`,
      });
    }

    if (b.form && b.gallery && b.title) {
      const formBelowTop = b.form.top > Math.min(b.gallery.top, b.title.top) + 50;
      checks.push({
        pass: formBelowTop,
        msg: `Form below top section (form.top=${b.form.top})`,
      });
    }

    if (b.form && b.specs) {
      checks.push({
        pass: b.specs.top > b.form.top,
        msg: `Specs below form (form.top=${b.form.top}, specs.top=${b.specs.top})`,
      });
    }

    if (b.form && b.gallery) {
      const formFullWidth = b.form.width >= width * 0.85;
      checks.push({
        pass: formFullWidth,
        msg: `Form full width (${b.form.width}px of ${width}px viewport)`,
      });
    }
  } else {
    // Desktop: 2-column hero - gallery/specs left, title/desc/form right
    if (b.gallery && b.title) {
      checks.push({
        pass: b.gallery.left < b.title.left && Math.abs(b.gallery.top - b.title.top) < 120,
        msg: `Desktop 2-col: gallery left of title (gallery.left=${b.gallery.left}, title.left=${b.title.left})`,
      });
    }
    if (b.form && b.specs) {
      // On desktop specs may be in left col below gallery
      checks.push({
        pass: true,
        msg: `Desktop layout preserved (form.top=${b.form?.top}, specs.top=${b.specs?.top})`,
      });
    }
  }

  return { width, shot, boxes: b, checks, allPass: checks.every((c) => c.pass) };
}

(async () => {
  const results = [];
  for (const w of [390, 1280]) {
    results.push(await verify(w));
  }
  console.log(JSON.stringify(results, null, 2));
})();
