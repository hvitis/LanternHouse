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
  browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
  await mkdir(screenshots,{recursive:true});
  const guide=JSON.parse(await readFile(resolve(root,'data/assembly.json'),'utf8'));
  const storageKey='moomin-house:assembly:v1';
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
    const page=await browser.newPage({viewport,hasTouch:name==='mobile'});page.setDefaultTimeout(30000);
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.route('**/*',route=>route.request().url().startsWith(origin+prefix)?route.continue():route.abort());
    await page.goto(origin+prefix+'#instructions');
    await page.locator('#instructionStart').waitFor();
    assert.equal(await page.locator('#instructionView canvas').count(),0,'Scene is lazy until Start');
    assert.match(await page.locator('#instructionTotal').innerText(),new RegExp(String(guide.steps.length)));
    await page.locator('[data-supply="pva"]').check();
    await page.locator('#instructionStart').click();
    await page.locator('#instructionView[data-ready="true"]').waitFor();
    assert.match(await page.locator('#instructionCount').innerText(),/Step 1 of/);
    assert.match(await page.locator('#instructionFieldHints').innerText(),/No field-tested hints/);
    await page.locator('#instructionComplete').click();
    assert.match(await page.locator('#instructionProgressText').innerText(),/^1 of/);
    await page.locator('#instructionNext').click();
    assert.match(await page.locator('#instructionProgressText').innerText(),/^1 of/,'Browsing must not complete work');
    const viewed=await page.locator('#instructionStepSelect').inputValue();
    await page.reload();await page.locator('#instructionBuild').waitFor();
    assert.equal(await page.locator('#instructionStepSelect').inputValue(),viewed);
    assert.match(await page.locator('#instructionProgressText').innerText(),/^1 of/);
    await page.locator('#instructionStepSelect').selectOption('windows-trim');
    assert.match(await page.locator('#instructionRepeat').innerText(),/Repeat × 17/);
    await page.locator('#instructionView[data-step="windows-trim"][data-ready="true"]').waitFor();
    const savedBefore=await page.evaluate(key=>localStorage.getItem(key),storageKey);
    await page.locator('#instructionPlay').click();
    await page.locator('#instructionView[data-playing="true"]').waitFor();
    await page.locator('#instructionPlay').click();
    await page.locator('#instructionView[data-playing="false"]').waitFor();
    await page.locator('#instructionReplay').click();
    await page.locator('#instructionView[data-playing="true"]').waitFor();
    await page.locator('#instructionView[data-playing="false"]').waitFor();
    assert.equal(await page.evaluate(key=>localStorage.getItem(key),storageKey),savedBefore,'Animations never complete work');
    await page.locator('#instructionCloseup').click();
    await page.screenshot({path:resolve(screenshots,`instructions-${name}.png`)});
    await page.locator('#tab-house').click();await page.locator('#view[data-ready="true"]').waitFor();
    if(name==='mobile')await page.locator('#houseTools > summary').click();
    await page.locator('#wallLeft').fill('40');await page.locator('#wallLeft').dispatchEvent('input');
    await page.locator('#tab-instructions').click();
    assert.equal(await page.locator('#instructionStepSelect').inputValue(),'windows-trim');
    await page.locator('#tab-house').click();assert.equal(await page.locator('#wallLeft').inputValue(),'40');
    await page.locator('#tab-instructions').click();
    await page.locator('#instructionPreparation').click();
    assert.equal(await page.locator('[data-supply="pva"]').isChecked(),true);
    await page.locator('#instructionStart').click();
    // Every operation is navigable and has a matching scene, including repeated subassemblies.
    for(const step of guide.steps){
      await page.locator('#instructionStepSelect').selectOption(step.id);
      await page.locator('#instructionView[data-step="'+step.id+'"]').waitFor();
      assert.equal(await page.locator('#instructionStepTitle').innerText(),step.title);
    }
    await page.locator('#instructionComplete').click();
    assert.equal(await page.locator('#instructionNext').isDisabled(),true);
    page.once('dialog',dialog=>dialog.dismiss());await page.locator('#instructionRestart').click();
    assert.equal(await page.locator('#instructionBuild').isVisible(),true);
    page.once('dialog',dialog=>dialog.accept());await page.locator('#instructionRestart').click();
    assert.equal(await page.locator('#instructionPrep').isVisible(),true);
    assert.equal(await page.locator('[data-supply="pva"]').isChecked(),false);
    const width=await page.evaluate(()=>({body:document.documentElement.scrollWidth,viewport:innerWidth}));
    assert.ok(width.body<=width.viewport,'No page horizontal overflow');
    assert.deepEqual(errors,[]);await page.close();console.log(name+': instructions, animation, persistence, batches and tab isolation passed');
  }
  const page=await browser.newPage();
  await page.goto(origin+prefix+'#instructions');await page.locator('#instructionStart').waitFor();
  await page.evaluate(key=>localStorage.setItem(key,'broken JSON'),storageKey);await page.reload();
  await page.locator('#instructionReset').waitFor();
  assert.equal(await page.evaluate(key=>localStorage.getItem(key),storageKey),'broken JSON','Invalid saves are not silently overwritten');
  page.once('dialog',dialog=>dialog.accept());await page.locator('#instructionReset').click();
  await page.locator('#instructionStart').click();await page.locator('#instructionBuild').waitFor();
  await page.evaluate(key=>{const saved=JSON.parse(localStorage.getItem(key));saved.revision='old';localStorage.setItem(key,JSON.stringify(saved));},storageKey);
  await page.reload();await page.locator('#instructionAccept').waitFor();
  await page.locator('#instructionAccept').click();
  assert.equal(await page.locator('#instructionAccept').isVisible(),false);
  await page.close();
  const reduced=await browser.newPage({reducedMotion:'reduce'});
  await reduced.goto(origin+prefix+'#instructions');await reduced.locator('#instructionStart').click();
  await reduced.locator('#instructionView[data-ready="true"]').waitFor();
  await reduced.locator('#instructionPlay').click();assert.equal(await reduced.locator('#instructionView').getAttribute('data-playing'),'false');await reduced.close();
  const noModel=await browser.newPage();
  await noModel.route('**/data/parts.json',route=>route.fulfill({status:404,body:'Missing'}));
  await noModel.goto(origin+prefix+'#instructions');await noModel.locator('#instructionStart').click();
  await noModel.waitForFunction(()=>document.getElementById('instructionSceneStatus').textContent.includes('could not load'));
  await noModel.locator('#instructionNext').click();assert.match(await noModel.locator('#instructionCount').innerText(),/Step 2 of/);await noModel.close();
  const noStorage=await browser.newPage();
  await noStorage.addInitScript(()=>{Storage.prototype.getItem=()=>{throw new DOMException('Blocked','SecurityError');};Storage.prototype.setItem=()=>{throw new DOMException('Blocked','SecurityError');};});
  await noStorage.goto(origin+prefix+'#instructions');await noStorage.locator('#instructionStart').click();
  await noStorage.locator('#instructionNext').click();assert.match(await noStorage.locator('#instructionCount').innerText(),/Step 2 of/);await noStorage.close();
  console.log('Corrupt storage, updated instructions, reduced motion, missing model and unavailable storage passed');
} finally {
  await browser?.close();await new Promise(resolve=>server.close(resolve));
}
