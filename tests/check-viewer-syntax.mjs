// Check the current source as ES modules, even when the static export is older.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';

for (const name of ['app.js', 'workspace.js', 'dxf-viewer.js', 'prints.js']) {
  const source = await readFile(new URL(`../source/viewer/${name}`, import.meta.url), 'utf8');
  const check = spawnSync(process.execPath, ['--input-type=module', '--check'], {input: source, encoding: 'utf8'});
  assert.equal(check.status, 0, `${name}: ${check.stderr || check.error || 'syntax check failed'}`);
}
console.log('Viewer source: all four ES modules parse.');
