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
const mime = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.txt': 'text/plain'};
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
    const page = await browser.newPage({viewport, hasTouch: name === 'mobile'});
    page.setDefaultTimeout(30_000);
    const errors = [], requests = [], failures = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push(request.url()));
    page.on('response', response => { if (response.status() >= 400) failures.push(`${response.status()} ${response.url()}`); });
    page.on('requestfailed', request => failures.push(`${request.failure()?.errorText} ${request.url()}`));
    await page.route('**/*', async route => {
      if (!route.request().url().startsWith(origin + prefix)) return route.abort();
      // Expose the real scene to assertions only in this browser test.
      if (route.request().url().endsWith('/app.js')) return route.fulfill({
        contentType: 'text/javascript', body: await readFile(resolve(root, 'app.js'), 'utf8') + '\nexport {meshes, lines, select, visibleChain, searchMatches, camera, controls, flight, nodes};',
      });
      return route.continue();
    });
    await page.goto(origin + prefix);
    await page.locator('#view[data-ready="true"]').waitFor({timeout: 60_000});
    assert.equal(await page.locator('#tab-house').getAttribute('aria-selected'), 'true');
    assert.equal(await page.locator('#dxfPanel').isVisible(), false);
    assert.equal(await page.locator('#printablesFrame').getAttribute('src'), null, 'Printables load only when opened');
    assert.equal(requests.some(url => url.endsWith('/data/house.dxf')), false, 'DXF loads only when opened');
    // Preload the module so polling predicates return booleans instead of promises.
    await page.evaluate(async () => {window.searchViewer = await import('./app.js');});
    await page.waitForFunction(() => window.searchViewer.flight?.t === 1);
    assert.equal(await page.locator('#showDims').isChecked(), false, 'The default house preview is free of dimension labels');
    await page.screenshot({path: resolve(screenshots, `${name}-workbench.png`)});
    if (name === 'mobile') await page.locator('#houseTools > summary').click();
    const stats = await page.locator('#stats').innerText();
    assert.match(stats, /build part profiles/);
    assert.ok(stats.includes(`${model.derived.total_height ?? model.config.height} mm tall`));
    assert.equal(await page.locator('#loading').count(), 0);
    assert.equal(await page.locator('canvas').count(), 1);
    if (name === 'mobile') {
      const panel = await page.locator('#panel').boundingBox();
      const canvas = await page.locator('canvas').boundingBox();
      assert.ok(canvas.y + canvas.height <= panel.y + 1, 'Mobile controls cover the 3D canvas');
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
    await page.locator('#displayTools > summary').click();
    assert.equal(await page.locator('#showThickness').isChecked(), false);
    assert.equal(await page.locator('#thicknessLegend').isVisible(), false);
    async function checkMaterials(thickness) {
      const failures = await page.evaluate(async thickness => {
        const {meshes} = await import('./app.js');
        return meshes.filter(m => {
          const expected = thickness && m.userData.part?.dxf;
          return expected ? '#' + m.material.color.getHexString() !== expected.color : m.material !== m.userData.base;
        }).map(m => m.userData.inst?.id ?? m.userData.kind);
      }, thickness);
      assert.deepEqual(failures, [], `${name}: incorrect ${thickness ? 'DXF' : 'normal'} materials`);
    }
    await checkMaterials(false);
    await page.locator('#showThickness').check();
    assert.match(await page.locator('#thicknessLegend').innerText(), /3 mm · CUT_3MM/);
    assert.match(await page.locator('#thicknessLegend').innerText(), /6 mm · CUT_6MM/);
    await checkMaterials(true);
    await page.locator('#showThickness').uncheck();
    assert.equal(await page.locator('#thicknessLegend').isVisible(), false);
    await checkMaterials(false);
    await page.locator('#highlight').check();
    await page.locator('#showThickness').check();
    assert.equal(await page.locator('#highlight').isChecked(), false);
    await checkMaterials(true);
    // Selection must restore the active thickness color when cleared, even across mode changes.
    await page.evaluate(async () => {const {meshes, select} = await import('./app.js'); select(meshes.find(m => m.userData.part?.dxf));});
    await page.locator('#showThickness').uncheck();
    await page.keyboard.press('Escape');
    await checkMaterials(false);
    await page.locator('#showThickness').check();
    await checkMaterials(true);
    await page.locator('#showPieceIds').check();
    await page.waitForFunction(() => [...document.querySelectorAll('.piece-id')].some(label => label.style.display !== 'none'));
    const pieceIds = await page.locator('.piece-id').allTextContents();
    assert.ok(pieceIds.length > 100 && pieceIds.includes('W01'), 'Build IDs must label the physical pieces');
    assert.ok(pieceIds.every(id => model.parts[id] && !model.parts[id].render_only));
    await page.screenshot({path: resolve(screenshots, `piece-ids-${name}.png`)});
    await page.locator('#showPieceIds').uncheck();
    await page.waitForFunction(() => [...document.querySelectorAll('.piece-id')].every(label => label.style.display === 'none'));
    // Search only exact IDs. A part code finds every copy; an instance code finds one piece.
    const search = page.locator('#elementId');
    await search.fill('P0');
    assert.equal(await search.getAttribute('aria-invalid'), 'true');
    assert.equal(await page.locator('#xray').isChecked(), false);
    await search.fill(' p01 ');
    const copies = model.instances.filter(i => i.part === 'P01');
    await page.waitForFunction(count => {
      const {searchMatches, flight, controls} = window.searchViewer;
      return searchMatches.size === count && flight?.t === 1 && controls.target.distanceTo(flight.toT) < .001;
    }, copies.length);
    assert.equal(await page.locator('#xray').isChecked(), true);
    const inspected = await page.evaluate(async () => {
      const {searchMatches, meshes, controls} = await import('./app.js');
      const {Box3, Vector3} = await import('./vendor/three.module.js');
      const box = new Box3();for (const mesh of searchMatches) box.union(new Box3().setFromObject(mesh));
      return {
        ids: [...searchMatches].map(m => m.userData.inst.id),
        yellow: [...searchMatches].every(m => m.material.color.getHex() === 0xffe600 && m.material.opacity === 1),
        ghosted: meshes.filter(m => !searchMatches.has(m)).every(m => m.material.transparent && m.material.opacity <= .12),
        centered: controls.target.distanceTo(box.getCenter(new Vector3())) < .001,
      };
    });
    assert.deepEqual(inspected.ids.sort(), copies.map(i => i.id).sort());
    assert.ok(inspected.yellow && inspected.ghosted && inspected.centered, 'An exact part match must be yellow, visible through the house, and centered');
    await search.fill(copies[1].id);
    await page.waitForFunction(id => {
      const {searchMatches, flight} = window.searchViewer;
      return searchMatches.size === 1 && [...searchMatches][0].userData.inst.id === id && flight?.t === 1;
    }, copies[1].id);
    await page.screenshot({path: resolve(screenshots, `element-search-${name}.png`)});
    await page.locator('#clearSearch').click();
    assert.equal(await search.inputValue(), '');
    assert.equal(await page.locator('#xray').isChecked(), false);
    await checkMaterials(true);
    await page.locator('#showPorch').uncheck();
    const porch = model.instances.find(i => i.group === 'Porch' && !model.parts[i.part].render_only);
    await search.fill(porch.id);
    await page.waitForFunction(() => {
      const {searchMatches, visibleChain} = window.searchViewer;return [...searchMatches].every(visibleChain);
    });
    assert.equal(await page.locator('#showPorch').isChecked(), true);
    await search.press('Escape');
    await checkMaterials(true);
    await page.locator('#xray').check();
    await search.fill('W01');await page.locator('#clearSearch').click();
    assert.equal(await page.locator('#xray').isChecked(), true, 'Clearing search must preserve a pre-existing X-ray setting');
    await page.locator('#xray').uncheck();
    await page.locator('[data-view="fit"]').click();
    // Furniture includes every display-only solid, inside and around the house, with its edges.
    for (const checked of [false, true]) {
      await page.locator('#showFurniture').setChecked(checked);
      await page.waitForFunction(checked => {
        const {meshes, lines, visibleChain} = window.searchViewer;
        const decorations = meshes.filter(m => m.userData.part?.render_only);
        return decorations.length > 0 && decorations.every(m => visibleChain(m) === checked)
          && lines.filter(l => l.userData.mesh.userData.part?.render_only).every(l => visibleChain(l) === checked);
      }, checked);
      const visible = await page.evaluate(async () => {
        const {meshes, visibleChain} = await import('./app.js');
        return {
          figures: meshes.filter(m => m.userData.kind === 'figure').every(visibleChain),
          buildParts: meshes.filter(m => m.userData.kind === 'part' && !m.userData.part.render_only).every(visibleChain),
          scenery: meshes.filter(m => m.userData.inst?.group === 'Garden').length,
        };
      });
      assert.ok(visible.scenery > 0, 'The model must include the huts, tent and other garden scenery');
      assert.ok(visible.figures && visible.buildParts, 'Furniture must not hide figures or build parts');
    }
    await page.locator('#openAll').click();
    await page.waitForFunction(() => ['walls', 'wallLeft', 'wallRight', 'doors', 'drawer'].every(id => {
      const input = document.getElementById(id);
      return Number(input.value) === Number(input.max);
    }));
    assert.equal(await page.locator('#doors').inputValue(), '90');
    assert.equal(await page.locator('#drawer').inputValue(), String(model.config.plinth.drawer.travel));
    await page.locator('#closeAll').click();
    await page.waitForFunction(() => document.querySelector('#walls').value === '0' && document.querySelector('#wallLeft').value === '0' && document.querySelector('#wallRight').value === '0' && document.querySelector('#drawer').value === '0');

    // Slider values change before apply() updates the scene on the next animation frame.
    async function waitForWallRotations(left, right) {
      await page.waitForFunction(([left, right]) => {
        const {nodes} = window.searchViewer;
        return Math.abs(-nodes.WallLeft.pivot.rotation.z * 180 / Math.PI - left) < .05
          && Math.abs(nodes.WallRight.pivot.rotation.z * 180 / Math.PI - right) < .05;
      }, [left, right]);
    }
    // Test opening left and right walls separately.
    await waitForWallRotations(0, 0);
    await page.locator('#wallLeft').fill('45');
    await page.locator('#wallLeft').dispatchEvent('input');
    await waitForWallRotations(45, 0);
    const wallRotations = await page.evaluate(async () => {
      const {nodes} = await import('./app.js');
      const {MathUtils} = await import('./vendor/three.module.js');
      return {
        leftDeg: Math.round(MathUtils.radToDeg(-nodes.WallLeft.pivot.rotation.z)),
        rightDeg: Math.round(MathUtils.radToDeg(nodes.WallRight.pivot.rotation.z)),
      };
    });
    assert.equal(wallRotations.leftDeg, 45, 'Left wall opens to 45 degrees');
    assert.equal(wallRotations.rightDeg, 0, 'Right wall remains closed when left wall opens');
    assert.equal(await page.locator('#wallLeftOut').innerText(), '45°');
    assert.equal(await page.locator('#wallsOut').innerText(), '45° / 0°');

    await page.locator('#wallRight').fill('70');
    await page.locator('#wallRight').dispatchEvent('input');
    await waitForWallRotations(45, 70);
    const wallRotations2 = await page.evaluate(async () => {
      const {nodes} = await import('./app.js');
      const {MathUtils} = await import('./vendor/three.module.js');
      return {
        leftDeg: Math.round(MathUtils.radToDeg(-nodes.WallLeft.pivot.rotation.z)),
        rightDeg: Math.round(MathUtils.radToDeg(nodes.WallRight.pivot.rotation.z)),
      };
    });
    assert.equal(wallRotations2.leftDeg, 45, 'Left wall stays at 45 degrees');
    assert.equal(wallRotations2.rightDeg, 70, 'Right wall opens to 70 degrees');
    assert.equal(await page.locator('#wallRightOut').innerText(), '70°');
    assert.equal(await page.locator('#wallsOut').innerText(), '45° / 70°');

    await page.locator('#closeAll').click();
    await page.waitForFunction(() => document.querySelector('#wallLeft').value === '0' && document.querySelector('#wallRight').value === '0');
    await waitForWallRotations(0, 0);
    await page.locator('[data-view="top"]').click();
    await page.locator('#showFigures').uncheck();
    await page.locator('#xray').check();
    await page.waitForFunction(() => {
      const {meshes} = window.searchViewer;
      return meshes.filter(m => m.userData.part?.category === 'Walls').every(m => m.material.transparent && m.material.opacity === .22);
    });
    // DXF is the real cutting file, loaded on demand under the same static-site prefix.
    await page.locator('#tab-dxf').click();
    await page.locator('#dxfViewport[data-ready="true"]').waitFor({timeout: 30_000});
    const drawing = page.locator('#dxfViewport canvas');
    assert.equal(await page.locator('#dxfPanel').isVisible(), true);
    assert.match(await page.locator('#dxfStatus').innerText(), /Supplier-Cut.dxf · \d+ paths/);
    assert.equal(await page.locator('#dxfLayers input').count(), 2);
    await page.locator('#dxfPieceIds').check();
    assert.ok(Number(await drawing.getAttribute('data-labels')) > 100, 'DXF piece IDs must follow the nested pieces');
    await page.locator('#dxfPieceIds').uncheck();
    assert.equal(await drawing.getAttribute('data-labels'), '0');
    const initialScale = Number(await drawing.getAttribute('data-scale'));
    await page.locator('#dxfZoomIn').click();
    assert.ok(Number(await drawing.getAttribute('data-scale')) > initialScale);
    await page.locator('#dxfZoomOut').click();
    assert.ok(Math.abs(Number(await drawing.getAttribute('data-scale')) - initialScale) < .000001);
    const drawingBox = await drawing.boundingBox(), center = {x: drawingBox.x + drawingBox.width / 2, y: drawingBox.y + drawingBox.height / 2};
    await page.mouse.move(center.x, center.y);
    await page.mouse.wheel(0, -200);
    await page.waitForFunction(scale => Number(document.querySelector('#dxfViewport canvas').dataset.scale) > scale, initialScale);
    const panBefore = await drawing.getAttribute('data-pan');
    await page.mouse.down();await page.mouse.move(center.x + 45, center.y + 25, {steps: 5});await page.mouse.up();
    assert.notEqual(await drawing.getAttribute('data-pan'), panBefore);
    await drawing.focus();await page.keyboard.press('f');
    assert.ok(Math.abs(Number(await drawing.getAttribute('data-scale')) - initialScale) < .000001);
    const keyboardPan = await drawing.getAttribute('data-pan');await page.keyboard.press('ArrowRight');
    assert.notEqual(await drawing.getAttribute('data-pan'), keyboardPan);
    if (name === 'mobile') {
      const session = await page.context().newCDPSession(page);
      const touches = spread => [{x: center.x - spread, y: center.y, id: 1}, {x: center.x + spread, y: center.y, id: 2}];
      const pinchBefore = Number(await drawing.getAttribute('data-scale'));
      await session.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: touches(25)});
      await session.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: touches(50)});
      await session.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
      assert.ok(Number(await drawing.getAttribute('data-scale')) > pinchBefore, 'Pinch must zoom the drawing');
      await session.detach();
    }
    await page.locator('#dxfFit').click();
    await page.getByRole('checkbox', {name: 'Show CUT_3MM', exact: true}).uncheck();
    await page.getByRole('checkbox', {name: 'Show CUT_3MM', exact: true}).check();
    const pixelColours = await drawing.evaluate(canvas => {
      const {data} = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height);
      let red = 0, green = 0;
      for (let i = 0; i < data.length; i += 4) {if (data[i] > 120 && data[i] > data[i + 1] * 2) red++; if (data[i + 1] > 120 && data[i + 1] > data[i] * 2) green++;}
      return {red, green};
    });
    assert.ok(pixelColours.red > 20 && pixelColours.green > 20, `${name}: both DXF layers must render`);
    await page.locator('#dxfPieceIds').check();
    await page.screenshot({path: resolve(screenshots, `dxf-${name}.png`)});
    const downloadEvent = page.waitForEvent('download');await page.locator('#dxfDownload').click();const download = await downloadEvent;
    assert.equal(download.suggestedFilename(), 'Moomin-House-Supplier-Cut.dxf');
    assert.equal(await readFile(await download.path(), 'utf8'), await readFile(resolve(root, 'data/house.dxf'), 'utf8'));
    await page.locator('#dxfFile').setInputFiles({name: 'invalid.dxf', mimeType: 'application/dxf', buffer: Buffer.from('invalid')});
    await page.locator('#dxfStatus[role="alert"]').waitFor();
    assert.equal(await drawing.isVisible(), true, 'An invalid file must preserve the current drawing');
    const custom = '0\nSECTION\n2\nENTITIES\n0\nLINE\n8\nEXAMPLE\n10\n0\n20\n0\n11\n20\n21\n10\n0\nCIRCLE\n8\nEXAMPLE\n10\n10\n20\n5\n40\n2\n0\nENDSEC\n0\nEOF\n';
    await page.locator('#dxfFile').setInputFiles({name: 'example.dxf', mimeType: 'application/dxf', buffer: Buffer.from(custom)});
    await page.waitForFunction(() => document.getElementById('dxfStatus').textContent.includes('example.dxf · 2 paths'));
    assert.equal(await page.locator('#dxfPieceIds').isDisabled(), true, 'Uploaded drawings must not inherit house piece IDs');
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#dxfPanel').isVisible(), false);
    assert.equal(await page.locator('#tab-house').evaluate(button => button === document.activeElement), true);
    assert.equal(await page.locator('#xray').isChecked(), true, 'House settings survive switching tabs');
    await page.locator('#tab-house').focus();
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#tab-dxf').getAttribute('aria-selected'), 'true');
    assert.match(await page.locator('#dxfStatus').innerText(), /example.dxf · 2 paths/, 'Custom drawing survives switching tabs');
    await page.keyboard.press('Home');
    assert.equal(await page.locator('#housePanel').isVisible(), true);
    await page.goBack();
    assert.equal(await page.locator('#dxfPanel').isVisible(), true, 'Back restores the previous preview');
    await page.locator('#tab-house').click();
    assert.ok(requests.some(url => url.endsWith('/data/house.dxf')));
    assert.ok(requests.some(url => url.endsWith('/data/parts.json')));
    assert.ok(requests.some(url => url.endsWith('/vendor/three.module.js')));
    assert.deepEqual(errors, [], `${name}: JavaScript errors`);
    assert.deepEqual(failures, [], `${name}: missing static files`);
    assert.ok(requests.every(url => url.startsWith(origin + prefix)), `${name}: external or root-relative dependency`);
    console.log(`${name}: static assets, WebGL pixels and viewer controls passed`);
    await page.close();
  }
  for (const preview of ['dxf', 'printables']) {
    const direct = await browser.newPage();
    await direct.goto(origin + prefix + '#' + preview);
    assert.equal(await direct.locator(`#tab-${preview}`).getAttribute('aria-selected'), 'true');
    if (preview === 'dxf') await direct.locator('#dxfViewport[data-ready="true"]').waitFor();
    else await direct.frameLocator('#printablesFrame').locator('#view[data-ready="true"]').waitFor();
    await direct.locator('#tab-house').click();
    await direct.locator('#view[data-ready="true"]').waitFor();
    const size = await direct.locator('#view canvas').boundingBox();
    assert.ok(size.width > 100 && size.height > 100, 'House sizes correctly after direct entry to another tab');
    await direct.close();
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
