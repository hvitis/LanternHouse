// The published 3D-print page, served from the static export under a repository prefix as GitHub Pages does:
// every design loads, its downloads are the published files, and the page has no errors on desktop or mobile.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const root = fileURLToPath(new URL('../_site/', import.meta.url));
const screenshots = fileURLToPath(new URL('../output/prints-smoke/', import.meta.url));
const prefix = '/moominshouse/';
const manifest = JSON.parse(await readFile(resolve(root, 'prints/manifest.json'), 'utf8'));
const designs = Object.values(manifest.parts);
assert.ok(designs.length > 0, 'No published designs in _site/prints/');
const mime = {'.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.stl': 'model/stl'};
const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (!path.startsWith(prefix)) throw new Error('Outside the static site');
    const file = resolve(root, path.slice(prefix.length) || 'index.html');
    if (!file.startsWith(resolve(root) + sep)) throw new Error('Outside the static site');
    const data = await readFile(file);
    res.writeHead(200, {'Content-Type': mime[file.slice(file.lastIndexOf('.'))] || 'application/octet-stream'});
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch({args: ['--enable-unsafe-swiftshader']});
  await mkdir(screenshots, {recursive: true});
  for (const [name, viewport] of [['desktop', {width: 1440, height: 1000}], ['mobile', {width: 390, height: 844}]]) {
    const page = await browser.newPage({viewport, hasTouch: name === 'mobile'});
    const errors = [], failures = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => { if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`); });
    page.on('requestfailed', request => failures.push(`${request.failure()?.errorText} ${request.url()}`));
    await page.route('**/*', route => route.request().url().startsWith(origin + prefix) ? route.continue() : route.abort());
    await page.goto(origin + prefix + 'prints.html');
    for (const design of designs) {
      await page.locator('#parts button', {hasText: design.title}).click();
      await page.locator(`#view[data-ready="true"][data-part="${design.name}"]`).waitFor({timeout: 60_000});
      assert.equal(await page.locator('#title').innerText(), design.title.toUpperCase());
      assert.equal(await page.locator('#checks li').count(), design.checks.length);
      assert.equal(await page.locator('#params input[type=range]').count(), 0, 'The published page shows measurements, not live sliders');
      const links = await page.locator('#downloads a').evaluateAll(as => as.map(a => [a.getAttribute('href'), a.download]));
      assert.deepEqual(links.map(([href]) => href), Object.values(design.files).map(f => `./prints/${f.path}`));
      for (const [href] of links) {
        const response = await page.request.get(new URL(href, page.url()).href);
        assert.equal(response.status(), 200, href);
        assert.equal((await response.body()).length, Object.values(design.files).find(f => href.endsWith(f.path)).bytes, href);
      }
      await page.screenshot({path: `${screenshots}${name}-${design.name}.png`});
    }
    assert.equal(await page.locator('#houseLink').isVisible(), true);
    if (name === 'mobile') {
      const panel = await page.locator('#panel').boundingBox();
      const canvas = await page.locator('canvas').boundingBox();
      assert.ok(canvas.y >= panel.y + panel.height, 'Mobile controls cover the 3D canvas');
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(failures, []);
    await page.close();
  }
  console.log(`Prints page OK: ${designs.length} designs, desktop and mobile. Screenshots in output/prints-smoke/.`);
} finally {
  await browser?.close();
  server.close();
}
