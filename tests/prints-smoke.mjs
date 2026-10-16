// The published 3D prints, served from the static export under the repository prefix GitHub Pages uses
// (https://hvitis.github.io/lanternwood-house/): /#printables opens them directly, the "3D printables" tab opens them
// from the house, every design loads, its downloads are the published files, and nothing errors on desktop or mobile.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const root = fileURLToPath(new URL('../_site/', import.meta.url));
const screenshots = fileURLToPath(new URL('../output/prints-smoke/', import.meta.url));
const prefix = '/lanternwood-house/';
const manifest = JSON.parse(await readFile(resolve(root, 'prints/manifest.json'), 'utf8'));
const designs = Object.values(manifest.parts);
assert.ok(designs.length > 0, 'No published designs in _site/prints/');
const mime = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.stl': 'model/stl', '.txt': 'text/plain'};
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
    page.setDefaultTimeout(30_000);
    const errors = [], failures = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => { if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`); });
    page.on('requestfailed', request => failures.push(`${request.failure()?.errorText} ${request.url()}`));
    await page.route('**/*', route => route.request().url().startsWith(origin + prefix) ? route.continue() : route.abort());
    // Enter from the house viewer, as a visitor does.
    await page.goto(origin + prefix);
    await page.locator('#view[data-ready="true"]').waitFor({timeout: 60_000});
    await page.locator('#tab-printables').click();
    const studio = page.frameLocator('#printablesFrame');
    await studio.locator('#view[data-ready="true"]').waitFor({timeout: 60_000});
    for (const design of designs) {
      await studio.locator('#parts button', {hasText: design.title}).click();
      await studio.locator(`#view[data-ready="true"][data-part="${design.name}"]`).waitFor({timeout: 60_000});
      assert.equal(await studio.locator('#title').innerText(), design.title.toUpperCase());
      assert.equal(await studio.locator('#checks li').count(), design.checks.length);
      assert.equal(await studio.locator('#params input[type=range]').count(), 0, 'The published page shows measurements, not live sliders');
      const links = await studio.locator('#downloads a').evaluateAll(as => as.map(a => [a.getAttribute('href'), a.download]));
      assert.deepEqual(links.map(([href]) => href), Object.values(design.files).map(f => `./prints/${f.path}`));
      for (const [href] of links) {
        const response = await page.request.get(new URL(href, origin + prefix + 'prints.html').href);
        assert.equal(response.status(), 200, href);
        assert.equal((await response.body()).length, Object.values(design.files).find(f => href.endsWith(f.path)).bytes, href);
      }
      await page.screenshot({path: `${screenshots}${name}-${design.name}.png`});
    }
    assert.equal(await studio.locator('#houseLink').isVisible(), false);
    const last = designs.at(-1);
    await page.locator('#tab-house').click();
    assert.equal(await page.locator('#view').isVisible(), true);
    await page.locator('#tab-printables').click();
    assert.equal(await studio.locator('#view').getAttribute('data-part'), last.name, 'Selected printable survives tab switching');
    if (name === 'mobile') {
      const panel = await studio.locator('#panel').boundingBox();
      const canvas = await studio.locator('canvas').boundingBox();
      assert.ok(canvas.y + canvas.height <= panel.y + 1, 'Mobile controls cover the printable canvas');
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(failures, []);
    await page.close();
  }
  // The shareable address: /#printables opens the tab directly, with the first design on the bed.
  const direct = await browser.newPage();
  const directErrors = [];
  direct.on('pageerror', error => directErrors.push(error.message));
  await direct.goto(origin + prefix + '#printables');
  assert.equal(await direct.locator('#tab-printables').getAttribute('aria-selected'), 'true');
  assert.equal(await direct.locator('#printablesFrame').getAttribute('src'), './prints.html?embedded=1');
  await direct.frameLocator('#printablesFrame').locator(`#view[data-ready="true"][data-part="${designs[0].name}"]`).waitFor({timeout: 60_000});
  assert.equal(await direct.frameLocator('#printablesFrame').locator('#parts button').count(), designs.length);
  await direct.screenshot({path: `${screenshots}direct-printables.png`});
  assert.deepEqual(directErrors, []);
  await direct.close();
  const standalone = await browser.newPage();
  await standalone.goto(origin + prefix + 'prints.html');
  await standalone.locator('#view[data-ready="true"]').waitFor();
  assert.equal(await standalone.locator('#houseLink').isVisible(), true, 'Standalone print studio still links to the house');
  await standalone.close();
  // A server without prints/ (an old `make viewer`): the page must say so, not blame WebGL.
  const page = await browser.newPage();
  await page.route('**/prints/manifest.json', route => route.fulfill({status: 404, body: 'Not found'}));
  await page.goto(origin + prefix + 'prints.html');
  await page.locator('#loading[role="alert"]').waitFor();
  assert.match(await page.locator('#loading').innerText(), /list of prints did not load \(.*HTTP 404\).*make viewer/);
  await page.close();
  console.log(`Prints OK: /#printables and the tab, ${designs.length} designs, desktop and mobile, and a clear error without prints/. Screenshots in output/prints-smoke/.`);
} finally {
  await browser?.close();
  server.close();
}
