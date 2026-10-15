// Moomin House prints: every 3D-printable design in prints/manifest.json, standing on the printer bed, with its
// print checks and downloads. Served by source/print_studio.py the same page is the live studio: each save of a
// design reloads it, and the sliders rebuild the part on the Mac.
import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';

const $=id=>document.getElementById(id);
const host=$('view'),query=new URLSearchParams(location.search);
async function fetchJSON(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(`${url}: HTTP ${r.status}`);return r.json();}
let manifest=await fetchJSON('./prints/manifest.json');
const live=Boolean(manifest.live);
const fmt=v=>String(+(+v).toFixed(2));
function el(tag,props={},...children){
  const e=document.createElement(tag);
  for(const [k,v] of Object.entries(props))k in e?e[k]=v:e.setAttribute(k,v);
  e.append(...children);return e;
}

// ---------- scene ----------
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0xeef2ee);host.appendChild(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(30,1,.5,5000);camera.up.set(0,0,1);   // Z-up, millimetres, like the house
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=.08;controls.screenSpacePanning=true;
const hemi=new THREE.HemisphereLight(0xffffff,0x8a9a8a,1.35);hemi.position.set(0,0,1);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffffff,1.7);sun.position.set(-70,-110,160);scene.add(sun);
const fill=new THREE.DirectionalLight(0xffffff,.5);fill.position.set(90,70,-30);scene.add(fill);

const bed=new THREE.Group();scene.add(bed);
function drawBed([bx,by]){
  bed.clear();
  const plate=new THREE.Mesh(new THREE.PlaneGeometry(bx,by),new THREE.MeshStandardMaterial({color:0xdfe5dc,roughness:1}));
  plate.position.z=-.05;bed.add(plate);   // one-sided: the underside view looks through it
  const lines=[];
  for(let x=-bx/2;x<=bx/2+1e-6;x+=10)lines.push(x,-by/2,0,x,by/2,0);
  for(let y=-by/2;y<=by/2+1e-6;y+=10)lines.push(-bx/2,y,0,bx/2,y,0);
  const grid=new THREE.BufferGeometry();grid.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));
  bed.add(new THREE.LineSegments(grid,new THREE.LineBasicMaterial({color:0xc6d0c4})));
}

const part=new THREE.Group();scene.add(part);
const surface=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.75,metalness:0,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
const edgeMaterial=new THREE.LineBasicMaterial({color:0x223838,transparent:true,opacity:.35});
const marker=new THREE.Mesh(new THREE.SphereGeometry(1,20,10),new THREE.MeshBasicMaterial({color:0xd8473a,depthTest:false}));
marker.renderOrder=2;marker.visible=false;scene.add(marker);

function parseSTL(buffer){
  const view=new DataView(buffer),count=buffer.byteLength>=84?view.getUint32(80,true):-1;
  if(buffer.byteLength!==84+50*count)throw new Error('Not a binary STL file');
  const position=new Float32Array(count*9);
  for(let i=0;i<count;i++)for(let k=0;k<9;k++)position[i*9+k]=view.getFloat32(84+i*50+12+k*4,true);
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(position,3));
  geometry.computeVertexNormals();   // corners are not shared, so every face is flat, as the printer sees it
  return geometry;
}

// The same rule as print_mesh.overhanging: leaning out more than the printer's limit (plus 1°), off the bed.
function paint(geometry,colour,limit,showOverhang){
  const p=geometry.attributes.position.array,colours=new Float32Array(p.length);
  const base=new THREE.Color(colour),red=new THREE.Color(0xd8473a),sin=Math.sin((limit+1)*Math.PI/180);
  let low=Infinity;for(let i=2;i<p.length;i+=3)low=Math.min(low,p[i]);
  const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
  for(let f=0;f<p.length/9;f++){
    a.fromArray(p,f*9);b.fromArray(p,f*9+3);c.fromArray(p,f*9+6);
    const top=Math.max(a.z,b.z,c.z);b.sub(a);c.sub(a);b.cross(c).normalize();
    const col=showOverhang&&-b.z>sin&&top>low+1e-3?red:base;
    for(let k=0;k<3;k++)col.toArray(colours,f*9+k*3);
  }
  geometry.setAttribute('color',new THREE.BufferAttribute(colours,3));
}

// ---------- camera ----------
const DIRECTIONS={iso:[1,-1.35,.95],front:[0,-1,.1],side:[1,0,.1],back:[0,1,.1],top:[0,-.001,1],under:[0,-.001,-1]};
let view=DIRECTIONS[query.get('view')]?query.get('view'):'iso';
function panelShift(){return innerWidth>700?($('panel').offsetWidth+12)/2:0;}
function resize(){
  const w=host.clientWidth,h=host.clientHeight,shift=panelShift();
  renderer.setSize(w,h);camera.aspect=w/h;
  // Centre the part in the space beside the panel, not behind it.
  if(shift)camera.setViewOffset(w,h,-shift,0,w,h);else camera.clearViewOffset();
  camera.updateProjectionMatrix();
}
function setView(name=view){
  view=name;for(const b of document.querySelectorAll('[data-view]'))b.classList.toggle('on',b.dataset.view===name);
  const box=new THREE.Box3().setFromObject(part);if(box.isEmpty())return;
  const centre=box.getCenter(new THREE.Vector3()),radius=box.getSize(new THREE.Vector3()).length()/2;
  const w=host.clientWidth-2*panelShift(),h=host.clientHeight,half=THREE.MathUtils.degToRad(camera.fov/2);
  const fit=Math.min(half,Math.atan(Math.tan(half)*w/h));
  camera.position.copy(centre).addScaledVector(new THREE.Vector3(...DIRECTIONS[name]).normalize(),radius/Math.sin(fit)*1.08);
  controls.target.copy(centre);controls.update();
}
addEventListener('resize',()=>resize());resize();
renderer.setAnimationLoop(()=>{
  controls.update();bed.visible=$('showBed').checked&&camera.position.z>0;   // from below, the grid would hide the part
  renderer.render(scene,camera);
});

// ---------- the panel ----------
let current=null,shownVersion=null,paramsShape=null,loadToken=0,geometry=null;
const DOWNLOADS={stl:['STL','Any slicer'],'3mf':['3MF','Modern slicers, keeps millimetres'],step:['STEP','Exact solid, to change it in CAD']};
const MARKS={pass:'✓',warn:'!',fail:'✕'};
const parts=()=>Object.values(manifest.parts);
const fileUrl=(entry,f)=>`./prints/${f.path}`+(live?`?v=${entry.version}`:'');

function renderSub(busy){
  const sub=$('sub');sub.replaceChildren();
  if(live){
    sub.append(el('span',{className:'live'+(busy?' busy':'')},busy?`Building ${busy}…`:'Live'));
    const entry=manifest.parts[current];
    sub.append(entry?.error?` ${entry.name} did not build · `:entry?.build_ms!=null?` ${entry.name} built in ${entry.build_ms} ms · `:' ');
  }
  sub.append(manifest.printer.name);
}

function renderList(){
  $('parts').replaceChildren(...parts().map(p=>{
    const button=el('button',{type:'button',className:p.name===current?'on':''},
      el('span',{className:`dot ${p.error?'error':p.status}`}),el('span',{},p.title),el('small',{},p.grams?`${fmt(p.grams.estimate)} g`:''));
    if(p.name===current)button.setAttribute('aria-current','true');
    button.addEventListener('click',()=>{location.hash=p.name;});
    return button;
  }));
}

function renderParams(entry){
  const params=entry.params||{},shape=JSON.stringify(Object.entries(params).map(([k,p])=>[k,p.min,p.max,p.step,p.default]));
  $('reset').hidden=!live||!Object.keys(entry.overrides||{}).length;
  if(shape===paramsShape&&live){   // same sliders: move the ones the visitor is not holding
    for(const [k,p] of Object.entries(params)){
      const input=document.querySelector(`#params input[name="${k}"]`);if(!input)continue;
      if(document.activeElement!==input)input.value=p.value;
      input.nextElementSibling.textContent=`${fmt(input.value)} ${p.unit}`;
      input.parentElement.classList.toggle('changed',+input.value!==p.default);
    }
    return;
  }
  paramsShape=shape;const box=$('params');box.replaceChildren();
  const label=k=>k.replace(/_/g,' ').replace(/^./,c=>c.toUpperCase());
  if(!live){
    box.append(el('table',{},...Object.entries(params).map(([k,p])=>el('tr',{},el('td',{},label(k)),el('td',{},`${fmt(p.value)} ${p.unit}`)))));
    return;
  }
  for(const [k,p] of Object.entries(params)){
    const input=el('input',{type:'range',name:k,min:p.min,max:p.max,step:p.step,value:p.value,'aria-label':label(k)});
    const out=el('output',{},`${fmt(p.value)} ${p.unit}`),row=el('div',{className:'slider'+(p.value!==p.default?' changed':'')},el('span',{},label(k)),input,out);
    input.addEventListener('input',()=>{out.textContent=`${fmt(input.value)} ${p.unit}`;row.classList.toggle('changed',+input.value!==p.default);send({values:{[k]:+input.value}});});
    box.append(row);
  }
}

async function render(entry,{frame=false}={}){
  shownVersion=entry.version??entry.hash;
  $('part').hidden=false;$('title').textContent=entry.title;
  // The design's docstring: its summary line at the top, the rest below the checks.
  const [summary,...design]=(entry.about||'').split(/\n\s*\n/).map(p=>el('p',{},p.replace(/\s*\n\s*/g,' ')));
  $('about').replaceChildren(...summary?[summary]:[]);$('design').replaceChildren(...design);$('designTitle').hidden=!design.length;
  $('error').hidden=!entry.error;$('error').textContent=entry.error?`The last change did not build${entry.files?.stl?' (showing the build before it)':''}:\n\n${entry.error}`:'';
  const facts=[];
  if(entry.size)facts.push(['Size',`${entry.size.map(fmt).join(' × ')} mm`]);
  if(entry.grams)facts.push(['Weight',`≈ ${fmt(entry.grams.estimate)} g ${manifest.printer.material.name} at ${Math.round(manifest.printer.infill*100)} % infill (${fmt(entry.grams.solid)} g solid)`]);
  if(entry.triangles)facts.push(['Mesh',`${entry.triangles.toLocaleString('en')} triangles`]);
  $('facts').replaceChildren(...facts.flatMap(([k,v])=>[el('dt',{},k),el('dd',{},v)]));
  $('downloads').replaceChildren(...Object.entries(entry.files||{}).map(([kind,f])=>
    el('a',{href:fileUrl(entry,f),download:`moomin-house-${entry.name}.${kind}`,title:DOWNLOADS[kind][1]},DOWNLOADS[kind][0],el('small',{},`${Math.max(1,Math.round(f.bytes/1024))} KB`))));
  $('notes').textContent=entry.notes||'';
  $('checks').replaceChildren(...(entry.checks||[]).map(c=>el('li',{className:c.status},el('span',{className:'mark','aria-label':c.status},MARKS[c.status]),el('span',{},c.label,el('span',{className:'detail'},c.detail)))));
  renderParams(entry);renderSub();renderList();
  await showMesh(entry);
  if(frame)setView();
  host.dataset.part=entry.name;host.dataset.version=shownVersion;host.dataset.ready='true';
  $('loading')?.remove();
}

async function showMesh(entry){
  const token=++loadToken,file=entry.files?.stl;
  if(!file){part.clear();marker.visible=false;return;}
  const response=await fetch(fileUrl(entry,file),{cache:live?'no-store':'default'});
  if(!response.ok)throw new Error(`${file.path}: HTTP ${response.status}`);
  const next=parseSTL(await response.arrayBuffer());
  if(token!==loadToken)return;   // a newer build arrived while this one loaded
  geometry?.dispose();geometry=next;geometry.userData.colour=entry.color;
  paint(geometry,entry.color,manifest.printer.max_overhang,$('showOverhang').checked);
  part.clear();
  const mesh=new THREE.Mesh(geometry,surface);surface.transparent=Boolean(entry.error);surface.opacity=entry.error?.45:1;
  part.add(mesh,new THREE.LineSegments(new THREE.EdgesGeometry(geometry,25),edgeMaterial));
  const wall=(entry.checks||[]).find(c=>c.id==='wall');
  marker.visible=Boolean(wall&&wall.status!=='pass'&&wall.at);
  if(marker.visible){marker.position.fromArray(wall.at);marker.scale.setScalar(Math.max(.6,Math.max(...entry.size)*.025));}
}

function select(name){
  if(!manifest.parts[name])name=parts()[0]?.name;
  if(!name)return;
  current=name;pending=null;paramsShape=null;
  render(manifest.parts[name],{frame:true});
}

// ---------- live studio: sliders and rebuilds ----------
let pending=null,sending=false;
async function send(change){
  pending={...pending,...change,values:{...pending?.values,...change.values}};
  if(sending)return;sending=true;
  try{
    while(pending){
      const body={part:current,...pending};pending=null;renderSub(current);
      const response=await fetch('./api/params',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if(!response.ok)throw new Error(`Rebuild failed: HTTP ${response.status}`);
      const entry=await response.json();manifest.parts[entry.name]=entry;
      if(entry.name===current)await render(entry);
    }
  }finally{sending=false;renderSub();}
}
$('reset').addEventListener('click',()=>{paramsShape=null;send({reset:true});});

if(live){
  $('houseLink').hidden=true;   // the studio serves the prints only
  const events=new EventSource('./api/events');
  events.onmessage=async({data})=>{
    const message=JSON.parse(data);
    if(message.event==='building'){renderSub(message.part);return;}
    manifest=await fetchJSON('./prints/manifest.json');
    if(!current||!manifest.parts[current]){select(location.hash.slice(1));return;}
    const entry=manifest.parts[current];
    if(entry.version!==shownVersion&&!sending)await render(entry);else{renderList();renderSub();}
  };
}

// ---------- start ----------
drawBed(manifest.printer.bed);
for(const b of document.querySelectorAll('[data-view]'))b.addEventListener('click',()=>setView(b.dataset.view));
$('showOverhang').addEventListener('change',()=>{if(geometry)paint(geometry,geometry.userData.colour,manifest.printer.max_overhang,$('showOverhang').checked);});
addEventListener('hashchange',()=>select(decodeURIComponent(location.hash.slice(1))));
renderSub();
if(parts().length)select(decodeURIComponent(location.hash.slice(1)));
else $('loading').textContent=live?'Building the designs… (the first build loads the CAD kernel, a few seconds)':'No designs are published yet.';
