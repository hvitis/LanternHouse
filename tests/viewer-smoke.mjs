// Serve the export under a repository prefix, as GitHub Pages does. No app server or CDN is available.
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const root = fileURLToPath(new URL('../_site/', import.meta.url));
const screenshots = fileURLToPath(new URL('../output/viewer-smoke/', import.meta.url));
const prefix = '/moominshouse/';
const model = JSON.parse(await readFile(resolve(root, 'data/parts.json'), 'utf8'));
const mime = {'.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.txt': 'text/plain'};
const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (!path.startsWith(prefix)) throw new Error('Outside the static site');
    const file = resolve(root, path.slice(prefix.length) || 'index.html');
    if (!file.startsWith(resolve(root) + sep)) throw new Error('Outside the static site');
    const data = await readFile(file);
    const extension = file.slice(file.lastIndexOf('.'));
    res.writeHead(200, {'Content-Type': mime[extension] || 'application/octet-stream'});
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
    const page = await browser.newPage({viewport});
    const errors = [], requests = [], failures = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push(request.url()));
    page.on('response', response => { if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`); });
    page.on('requestfailed', request => failures.push(`${request.failure()?.errorText} ${request.url()}`));
    await page.route('**/*', route => route.request().url().startsWith(origin + prefix) ? route.continue() : route.abort());
    await page.goto(origin + prefix);
    await page.locator('#view[data-ready="true"]').waitFor({timeout: 60_000});
    const stats = await page.locator('#stats').innerText();
    assert.match(stats, /build part profiles/);
    assert.ok(stats.includes(`${model.derived.total_height ?? model.config.height} mm tall`));
    assert.equal(await page.locator('#loading').count(), 0);
    assert.equal(await page.locator('canvas').count(), 1);
    if (name === 'mobile') {
      const panel = await page.locator('#panel').boundingBox();
      const canvas = await page.locator('canvas').boundingBox();
      assert.ok(canvas.y >= panel.y + panel.height, 'Mobile controls cover the 3D canvas');
    }
    // Read the rendered pixels immediately after a WebGL frame, before the browser clears its drawing buffer.
    const colours = await page.locator('canvas').evaluate(canvas => new Promise(resolve => requestAnimationFrame(() => {
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      const pixels = new Uint8Array(canvas.width * canvas.height * 4);
      gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      const values = new Set();
      for (let i = 0; i < pixels.length; i += 64) values.add(`${pixels[i]},${pixels[i + 1]},${pixels[i + 2]}`);
      resolve(values.size);
    })));
    assert.ok(colours > 20, `${name}: the WebGL frame is blank (${colours} colours)`);
    await page.screenshot({path: resolve(screenshots, `${name}.png`)});
    await page.locator('#openAll').click();
    await page.waitForFunction(() => ['walls', 'doors', 'drawer'].every(id => {
      const input = document.getElementById(id);
      return Number(input.value) === Number(input.max);
    }));
    assert.equal(await page.locator('#doors').inputValue(), '90');
    assert.equal(await page.locator('#drawer').inputValue(), String(model.config.plinth.drawer.travel));
    await page.locator('#closeAll').click();
    await page.waitForFunction(() => document.querySelector('#walls').value === '0' && document.querySelector('#drawer').value === '0');
    await page.locator('[data-view="top"]').click();
    await page.locator('#showFigures').uncheck();
    await page.locator('#xray').check();
    assert.ok(requests.some(url => url.endsWith('/data/parts.json')));
    assert.ok(requests.some(url => url.endsWith('/vendor/three.module.js')));
    assert.deepEqual(errors, [], `${name}: JavaScript errors`);
    assert.deepEqual(failures, [], `${name}: missing static files`);
    assert.ok(requests.every(url => url.startsWith(origin + prefix)), `${name}: external or root-relative dependency`);
    console.log(`${name}: static assets, WebGL pixels and viewer controls passed`);
    await page.close();
  }
  const page = await browser.newPage();
  await page.route('**/data/parts.json', route => route.fulfill({status: 404, body: 'Not found'}));
  await page.goto(origin + prefix);
  await page.locator('#loading[role="alert"]').waitFor();
  assert.match(await page.locator('#loading').innerText(), /could not load/);
  console.log('missing model: visible error passed');
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
