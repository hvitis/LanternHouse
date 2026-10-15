// Preview navigation owns the workspace; each viewer keeps its own inspection state.
const tabs = [...document.querySelectorAll('[data-preview]')];
const houseTools = document.getElementById('houseTools');
const mobile = matchMedia('(max-width: 760px), (max-height: 500px) and (pointer: coarse)');
houseTools.open = !mobile.matches;
const touch = matchMedia('(pointer: coarse)');
function updateHint(){ document.getElementById('hint').textContent = touch.matches ? 'Drag to orbit · pinch to zoom · tap a part to inspect' : 'Drag to orbit · scroll to zoom · click a part to inspect'; }
updateHint();touch.addEventListener('change', updateHint);
mobile.addEventListener('change', event => { houseTools.open = !event.matches; });
// Each preview, including the build companion, owns its inspection state.
export function showPreview(name, {focus = false} = {}) {
  const active = tabs.find(tab => tab.dataset.preview === name) ?? tabs[0];
  for (const tab of tabs) {
    const selected = tab === active;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(tab.getAttribute('aria-controls')).hidden = !selected;
  }
  active.scrollIntoView({block: 'nearest', inline: 'nearest'});
  const preview = active.dataset.preview;
  if (preview === 'printables') {
    const frame = document.getElementById('printablesFrame');
    if (!frame.hasAttribute('src')) frame.src = frame.dataset.src;
  }
  if (focus) active.focus();
  dispatchEvent(new CustomEvent('previewchange', {detail: {preview}}));
}
for (const [index, tab] of tabs.entries()) {
  tab.addEventListener('click', () => { location.hash = tab.dataset.preview; showPreview(tab.dataset.preview); });
  tab.addEventListener('keydown', event => {
    let next;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    if (next === undefined) return;
    event.preventDefault();
    tabs[next].click();
    tabs[next].focus();
  });
}
addEventListener('hashchange', () => showPreview(location.hash.slice(1)));
addEventListener('keydown', event => {
  if (event.key === 'Escape' && !document.getElementById('dxfPanel').hidden) {
    event.preventDefault();
    location.hash = 'house';
    showPreview('house', {focus: true});
  }
});
showPreview(location.hash.slice(1));
