// Moomin House 3D viewer: every solid is rebuilt from output/parts.json (the same profiles,
// thicknesses and placements the CAD export uses). Walls and doors turn about their real hinge axes,
// the hidden plinth drawer slides along its guides, and dimension annotations come from the model.
import * as THREE from 'three';
import {geometryOf,matrixOf} from './geometry.js';
import {hingeRadians,drawerOffset} from './motion.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {CSS2DRenderer,CSS2DObject} from './vendor/CSS2DRenderer.js';

const response=await fetch('./data/parts.json');
if(!response.ok)throw new Error(`Could not load the model (HTTP ${response.status})`);
const data=await response.json();
const {parts,instances,hardware,fasteners,derived,config}=data;
const maxWallAngle=derived.views.open_angle;   // the walls stop at the garden posts
document.getElementById('walls').max=maxWallAngle;
document.getElementById('wallLeft').max=maxWallAngle;
document.getElementById('wallRight').max=maxWallAngle;
const total=derived.total_height??config.height;

// ---------- scene ----------
const host=document.getElementById('view');
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,matchMedia('(pointer: coarse)').matches?1.5:2));renderer.setSize(Math.max(1,host.clientWidth),Math.max(1,host.clientHeight));
renderer.setClearColor(0xeef2ee);host.appendChild(renderer.domElement);
const labels=new CSS2DRenderer();labels.setSize(Math.max(1,host.clientWidth),Math.max(1,host.clientHeight));
Object.assign(labels.domElement.style,{position:'absolute',top:'0',left:'0',pointerEvents:'none'});host.appendChild(labels.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(32,Math.max(1,host.clientWidth)/Math.max(1,host.clientHeight),5,20000);
camera.up.set(0,0,1);   // CAD is Z-up, millimetres
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=.08;controls.screenSpacePanning=true;
const hemi=new THREE.HemisphereLight(0xffffff,0x8a9a8a,1.35);hemi.position.set(0,0,1);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffffff,1.7);sun.position.set(-700,-1100,1600);scene.add(sun);
const fill=new THREE.DirectionalLight(0xffffff,.45);fill.position.set(900,700,500);scene.add(fill);
const grid=new THREE.GridHelper(1800,36,0xc9d3c9,0xdde4dc);grid.rotation.x=Math.PI/2;grid.position.z=-.5;scene.add(grid);

// ---------- geometry from 2D profiles ----------
const geometry={},edges={};
for(const [pid,p] of Object.entries(parts)){
  geometry[pid]=geometryOf(p);edges[pid]=new THREE.EdgesGeometry(geometry[pid],25);
}
const materials={};
function material(p){
  const key=p.color+(p.category==='Walls'?':wall':'');
  return materials[key]??=new THREE.MeshStandardMaterial({color:new THREE.Color(p.color),roughness:.85,metalness:0,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
}
const flagged={new:new THREE.MeshStandardMaterial({color:0x3fae6b,roughness:.7,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1}),
  changed:new THREE.MeshStandardMaterial({color:0xf0b93a,roughness:.7,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1})};
const edgeMaterial=new THREE.LineBasicMaterial({color:0x223838,transparent:true,opacity:.35});
const pickMaterial=new THREE.MeshStandardMaterial({color:0xffc04d,emissive:0x6b3a00,roughness:.6});
const searchMaterial=new THREE.MeshBasicMaterial({color:0xffe600,transparent:true,opacity:1,depthTest:false,depthWrite:false});
const searchMatches=new Set(),ghostMaterials=new Map();let searchRestore=null;

// ---------- assembly hierarchy: explode offset -> pivot / slide -> meshes ----------
const LABEL={Fixed:'Fixed rear shell, plinth, floors and frame',WallRight:'Right opening wall shell',WallLeft:'Left opening wall shell',Roof:'Removable roof',RoofLocks:'Roof turn-button catches',Porch:'Permanent veranda',Drawer:'Hidden plinth drawer',Furniture:'Furniture for the 3D view',Figures:'Example clay figures',Printables:'3D-printable objects',RoomDoors:'Room door leaves',Garden:'Garden scene (display only)'};
const root=new THREE.Group();scene.add(root);
const nodes={};
for(const g of Object.keys(LABEL)){
  const explode=new THREE.Group(),pivot=new THREE.Group(),inner=new THREE.Group();
  explode.add(pivot);pivot.add(inner);root.add(explode);
  const axis=derived.hinge_axes[g];
  if(axis){pivot.position.set(axis[0],axis[1],0);inner.position.set(-axis[0],-axis[1],0);}
  nodes[g]={explode,pivot,inner};
}
const byId=Object.fromEntries(instances.map(i=>[i.id,i]));
// Doors swing about their hinge axis inside their own group: entrance doors on butt hinges, room doors on tape hinges.
const DOOR_KIND={'Door butt hinge':'front'};
const doors={},doorOf={};
for(const h of hardware){
  if(!DOOR_KIND[h.kind]||doors[h.door])continue;
  const wallNode=nodes[byId[h.door].group];const pivot=new THREE.Group(),inner=new THREE.Group();
  pivot.position.set(h.position[0],h.position[1],0);inner.position.set(-h.position[0],-h.position[1],0);
  pivot.add(inner);wallNode.inner.add(pivot);
  doors[h.door]={pivot,inner,hinge:h,sign:1,kind:DOOR_KIND[h.kind]};for(const id of h.moves_with)doorOf[id]=h.door;
}
// Each roof catch turns about its own bolt.
const catches={};
for(const f of fasteners){
  if(f.type!=='BL1')continue;const tab=f.parts.find(id=>byId[id]?.group==='RoofLocks');
  const pivot=new THREE.Group(),inner=new THREE.Group();pivot.position.set(f.origin[0],f.origin[1],0);inner.position.set(-f.origin[0],-f.origin[1],0);
  pivot.add(inner);nodes.RoofLocks.inner.add(pivot);catches[tab]={pivot,inner};
}
const meshes=[],lines=[],pieceLabels=[],parentOf={};
for(const i of instances){
  if(!nodes[i.group])continue;   // jigs, test coupons and the loose accessory tray are not in the house
  const p=parts[i.part];const parent=doorOf[i.id]?doors[doorOf[i.id]].inner:catches[i.id]?catches[i.id].inner:nodes[i.group].inner;
  const mesh=new THREE.Mesh(geometry[i.part],material(i.color?{...p,color:i.color}:p));mesh.matrixAutoUpdate=false;mesh.matrix.copy(matrixOf(i));
  mesh.userData={kind:'part',inst:i,part:p,base:mesh.material,dxf:p.dxf?material({...p,color:p.dxf.color}):null};parent.add(mesh);meshes.push(mesh);parentOf[i.id]=parent;
  const line=new THREE.LineSegments(edges[i.part],edgeMaterial);line.matrixAutoUpdate=false;line.matrix.copy(mesh.matrix);parent.add(line);lines.push(line);line.userData.mesh=mesh;
  if(!p.render_only){
    const element=document.createElement('div');element.className='piece-id';element.textContent=i.part;
    const tag=new CSS2DObject(element);mesh.geometry.computeBoundingBox();mesh.geometry.boundingBox.getCenter(tag.position);tag.visible=false;
    mesh.add(tag);pieceLabels.push(tag);
  }
}
// Thermo-clay Moomins: closed meshes from clay.py (base64 arrays), one per floor, placed by derived.figures.
function decode(text,Type){const bin=atob(text),bytes=new Uint8Array(bin.length);for(let k=0;k<bin.length;k++)bytes[k]=bin.charCodeAt(k);return new Type(bytes.buffer);}
const clayGeometry={};
for(const [key,c] of Object.entries(data.clay??{})){
  const g=new THREE.BufferGeometry(),index=decode(c.mesh.colour,Uint8Array),palette=c.mesh.palette.map(h=>new THREE.Color(h)),rgb=new Float32Array(index.length*3);
  index.forEach((k,j)=>palette[k].toArray(rgb,j*3));
  g.setAttribute('position',new THREE.BufferAttribute(decode(c.mesh.positions,Float32Array),3));g.setAttribute('color',new THREE.BufferAttribute(rgb,3));
  g.setIndex(new THREE.BufferAttribute(decode(c.mesh.index,Uint16Array),1));g.computeVertexNormals();clayGeometry[key]=g;
}
const clayMaterial=new THREE.MeshPhysicalMaterial({vertexColors:true,roughness:.6,metalness:0,sheen:.5,sheenRoughness:.7,sheenColor:new THREE.Color(0xffffff)});
for(const f of derived.figures??[]){
  const mesh=new THREE.Mesh(clayGeometry[f.key],clayMaterial);mesh.position.set(f.x,f.y,f.z);mesh.rotation.z=THREE.MathUtils.degToRad(f.yaw);
  const part={id:f.code,name:`${f.name} (thermo-clay)`,revision:f.revision,clay:data.clay[f.key]};
  mesh.userData={kind:'figure',inst:{id:f.id,part:f.code,group:'Figures'},part,figure:f,base:clayMaterial};nodes.Figures.inner.add(mesh);meshes.push(mesh);
}

// 3D-printable objects inside the house
function parseSTL(buffer){
  const view=new DataView(buffer),count=buffer.byteLength>=84?view.getUint32(80,true):-1;
  if(buffer.byteLength!==84+50*count)throw new Error('Not a binary STL file');
  const position=new Float32Array(count*9);
  for(let i=0;i<count;i++)for(let k=0;k<9;k++)position[i*9+k]=view.getFloat32(84+i*50+12+k*4,true);
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(position,3));
  geometry.computeVertexNormals();
  return geometry;
}
const printableMeshes=[];
async function loadPrintables(){
  try{
    const r=await fetch('./prints/manifest.json');if(!r.ok)return;
    const manifest=await r.json();
    const geomCache={};
    const placements=[
      {design:'stove',pos:[-52,40,tops[0]],rot:[0,0,Math.PI/4]},
      {design:'chandelier',pos:[58,62,tops[1]+(config.floor_pitch-config.thickness.floor)*450/config.wall_height-54],rot:[0,0,0]},
      {design:'bathtub',pos:[65,55,tops[2]],rot:[0,0,0]},
      {design:'table',pos:[52,40,tops[0]],rot:[0,0,0]},
      {design:'chair',pos:[52,22,tops[0]],rot:[0,0,Math.PI]},
      {design:'chair',pos:[52,58,tops[0]],rot:[0,0,0]},
    ];
    for(const pl of placements){
      const entry=manifest.parts?.[pl.design];
      if(!entry?.files?.stl)continue;
      if(!geomCache[pl.design]){
        const resp=await fetch(`./prints/${entry.files.stl.path}`);
        if(resp.ok)geomCache[pl.design]=parseSTL(await resp.arrayBuffer());
      }
      const geom=geomCache[pl.design];
      if(!geom)continue;
      const mat=new THREE.MeshStandardMaterial({color:new THREE.Color(entry.color||'#f5f0e1'),roughness:.75,metalness:0,polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
      const mesh=new THREE.Mesh(geom,mat);
      mesh.position.set(...pl.pos);
      mesh.rotation.set(...pl.rot);
      mesh.userData={kind:'printable',printable:entry,inst:{id:entry.name,part:entry.name,group:'Printables'},base:mat};
      nodes.Printables.inner.add(mesh);
      meshes.push(mesh);
      printableMeshes.push(mesh);
      const line=new THREE.LineSegments(new THREE.EdgesGeometry(geom,25),edgeMaterial);
      line.position.copy(mesh.position);line.rotation.copy(mesh.rotation);
      nodes.Printables.inner.add(line);
      lines.push(line);line.userData.mesh=mesh;
    }
    apply();
  }catch(e){console.warn('Could not load 3D printables in house viewer:',e);}
}
loadPrintables();

// Door rotation sign: positive angles must carry the door outward (measured with everything closed).
root.updateMatrixWorld(true);
for(const d of Object.values(doors)){
  const box=new THREE.Box3();d.inner.children.filter(o=>o.isMesh).forEach(o=>box.union(new THREE.Box3().setFromObject(o)));
  const c=box.getCenter(new THREE.Vector3()),hx=d.hinge.position[0],hy=d.hinge.position[1],a=THREE.MathUtils.degToRad(10);
  const rx=hx+(c.x-hx)*Math.cos(a)-(c.y-hy)*Math.sin(a),ry=hy+(c.x-hx)*Math.sin(a)+(c.y-hy)*Math.cos(a);
  d.sign=((rx-c.x)*d.hinge.outward[0]+(ry-c.y)*d.hinge.outward[1])>0?1:-1;
}

// ---------- hardware: screw / bolt solids, heads, nuts and hinge axes ----------
const hardwareObjects=[];
const metal=new THREE.MeshStandardMaterial({color:0xc19a55,metalness:.6,roughness:.4});
const brass=new THREE.MeshStandardMaterial({color:0xd4af37,metalness:.85,roughness:.25});
for(const f of fasteners){
  const parent=parentOf[f.parts[0]];if(!parent)continue;
  const axis=new THREE.Vector3(...f.axis).normalize();
  const shank=new THREE.Mesh(new THREE.CylinderGeometry(f.diameter/2,f.diameter/2,f.length,12),metal);
  shank.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),axis);
  shank.position.copy(new THREE.Vector3(...f.origin).addScaledVector(axis,f.length/2));
  if(f.head_diameter){
    const headH=f.head_height||1.2;
    const headGeom=new THREE.CylinderGeometry(f.head_diameter/2,f.diameter/2,headH,12);
    const headMesh=new THREE.Mesh(headGeom,brass);
    headMesh.position.set(0,-f.length/2-headH/2,0);
    shank.add(headMesh);
  }
  if(f.nut||f.type==='SC1'){
    const nutD=f.nut?.diameter??5.0, nutH=f.nut?.height??3.5;
    const nutCyl=new THREE.Mesh(new THREE.CylinderGeometry(nutD/2,nutD/2,nutH*0.6,12),brass);
    const nutDome=new THREE.Mesh(new THREE.SphereGeometry(nutD/2,12,8,0,Math.PI*2,0,Math.PI/2),brass);
    nutDome.position.y=nutH*0.3;
    const nutGroup=new THREE.Group();
    nutGroup.add(nutCyl);nutGroup.add(nutDome);
    nutGroup.position.set(0,f.length/2+nutH*0.3,0);
    shank.add(nutGroup);
  }
  shank.userData={kind:'fastener',fastener:f,owners:f.parts,base:metal};parent.add(shank);hardwareObjects.push(shank);meshes.push(shank);shank.visible=false;
}
const axisMaterial=new THREE.LineDashedMaterial({color:0xb56535,dashSize:8,gapSize:5});
function axisLine(parent,x,y,z0,z1){const g=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x,y,z0),new THREE.Vector3(x,y,z1)]);const l=new THREE.Line(g,axisMaterial);l.computeLineDistances();l.visible=false;parent.add(l);hardwareObjects.push(l);}
const tops=derived.floor_tops;
for(const [g,[x,y]] of Object.entries(derived.hinge_axes))axisLine(root,x,y,tops[0],tops[3]);
for(const d of Object.values(doors))axisLine(nodes[byId[d.hinge.door].group].inner,d.hinge.position[0],d.hinge.position[1],d.hinge.position[2]-d.hinge.height/2,d.hinge.position[2]+d.hinge.height/2);

// ---------- dimensions (from derived.dimensions) ----------
const dimObjects=[];
const dimLine=new THREE.LineBasicMaterial({color:0x197f98}),dimExt=new THREE.LineDashedMaterial({color:0x197f98,dashSize:4,gapSize:3});
function label(text,p,parent,cls='dim'){const el=document.createElement('div');el.className=cls;el.textContent=text;const o=new CSS2DObject(el);o.position.set(...p);parent.add(o);dimObjects.push(o);return o;}
for(const d of derived.dimensions??[]){
  const parent=d.group&&nodes[d.group]?nodes[d.group].inner:root;
  if(d.kind==='label'){label(d.label,d.p,parent,'dim mark');continue;}
  const a=new THREE.Vector3(...d.a),b=new THREE.Vector3(...d.b),dir=b.clone().sub(a).normalize();
  // End ticks lie across the line: horizontal ticks on vertical lines, vertical ticks on horizontal ones.
  const across=Math.abs(dir.z)>.9?new THREE.Vector3(1,0,0):new THREE.Vector3(0,0,1);
  const pts=[a,b];for(const e of [a,b])pts.push(e.clone().addScaledVector(across,-5),e.clone().addScaledVector(across,5));
  const g=new THREE.BufferGeometry().setFromPoints(pts);g.setIndex([0,1,2,3,4,5]);
  const line=new THREE.LineSegments(g,dimLine);parent.add(line);dimObjects.push(line);
  for(const [p,q] of d.ext??[]){const eg=new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...p),new THREE.Vector3(...q)]);const el=new THREE.Line(eg,dimExt);el.computeLineDistances();parent.add(el);dimObjects.push(el);}
  label(d.label,a.clone().add(b).multiplyScalar(.5),parent);
}

// ---------- what "remove attic" hides ----------
const atticFloorZ=tops[3];
function minZ(mesh){return new THREE.Box3().setFromObject(mesh).min.z;}
const attic=meshes.filter(m=>['part','figure'].includes(m.userData.kind)&&(m.userData.part.assembly_panel==='F02'||m.userData.inst.group==='RoofLocks'||(['Furniture','Figures'].includes(m.userData.inst.group)&&minZ(m)>=atticFloorZ-1)));
const atticIds=new Set(attic.map(m=>m.userData.inst.id));
for(const h of hardwareObjects)if(h.userData.owners?.some(id=>atticIds.has(id)))attic.push(h);

// ---------- state, animation and controls ----------
const travel=derived.drawer.travel;
const state={walls:0,wallLeft:0,wallRight:0,doors:0,drawer:0,lift:0,roof:'on',explode:0,cut:total+10,porch:true,furniture:true,figures:true,printables:true,hardware:false,edges:true,xray:false,dims:false,highlight:false,thickness:false};
const target={walls:0,wallLeft:0,wallRight:0,doors:0,drawer:0,lift:0,explode:0};
const $=id=>document.getElementById(id);
$('drawer').step='any';$('drawer').max=travel;$('cut').step='any';$('cut').max=total+10;$('cut').value=total+10;
function bindSlider(id,key,fmt){const el=$(id),out=$(id+'Out');el.addEventListener('input',()=>{target[key]=+el.value;state[key]=+el.value;out.textContent=fmt(+el.value);});return v=>{el.value=v;out.textContent=fmt(v);};}
const deg=v=>`${v}°`;
function syncWallsFromSides(){
  const wl=state.wallLeft,wr=state.wallRight;
  const avg=(wl+wr)/2;
  target.walls=avg;state.walls=avg;
  $('walls').value=Math.round(avg);
  const rwl=Math.round(wl),rwr=Math.round(wr);
  $('wallsOut').textContent=(rwl===rwr)?deg(rwl):`${rwl}° / ${rwr}°`;
}
const setters={
  walls:v=>{
    $('walls').value=v;
    const wl=Math.round(state.wallLeft),wr=Math.round(state.wallRight);
    $('wallsOut').textContent=(wl===wr)?deg(v):`${wl}° / ${wr}°`;
  },
  wallLeft:bindSlider('wallLeft','wallLeft',deg),
  wallRight:bindSlider('wallRight','wallRight',deg),
  doors:bindSlider('doors','doors',deg),
  drawer:bindSlider('drawer','drawer',v=>`${Number(v.toFixed(1))} mm`),
  explode:bindSlider('explode','explode',v=>`${v}%`),
};
$('walls').addEventListener('input',e=>{
  const v=+e.target.value;
  target.walls=target.wallLeft=target.wallRight=v;
  state.walls=state.wallLeft=state.wallRight=v;
  setters.wallLeft(v);
  setters.wallRight(v);
  $('wallsOut').textContent=deg(v);
});
$('wallLeft').addEventListener('input',syncWallsFromSides);
$('wallRight').addEventListener('input',syncWallsFromSides);
$('cut').addEventListener('input',e=>{state.cut=+e.target.value;$('cutOut').textContent=state.cut>=total?'off':`Z${state.cut}`;});
function setRoof(mode){
  state.roof=mode;target.lift=mode==='on'?0:350;
  document.querySelectorAll('#roofSeg button').forEach(b=>b.classList.toggle('on',b.dataset.roof===mode));
}
document.querySelectorAll('#roofSeg button').forEach(b=>b.addEventListener('click',()=>setRoof(b.dataset.roof)));
$('openAll').addEventListener('click',()=>{
  const openAngle=derived.views.open_angle;
  target.walls=target.wallLeft=target.wallRight=openAngle;
  target.doors=90;target.drawer=travel;setRoof('lifted');
});
$('closeAll').addEventListener('click',()=>{
  target.walls=target.wallLeft=target.wallRight=0;
  target.doors=0;target.drawer=0;target.explode=0;setRoof('on');
});
for(const [id,key] of [['showPorch','porch'],['showFurniture','furniture'],['showFigures','figures'],['showPrintables','printables'],['showHardware','hardware'],['showEdges','edges'],['xray','xray'],['showDims','dims']])
  $(id)?.addEventListener('change',e=>{state[key]=e.target.checked;if(key==='xray')recolour();apply();});
for(const text of derived.changes??[]){const li=document.createElement('li');li.textContent=text;$('changes').appendChild(li);}

const thicknessColours=[...new Map(Object.values(parts).filter(p=>p.dxf).map(p=>[p.dxf.layer,{...p.dxf,thickness:p.thickness}])).values()].sort((a,b)=>a.thickness-b.thickness);
for(const c of thicknessColours){
  const row=document.createElement('p'),swatch=document.createElement('span');swatch.className='key';swatch.style.background=c.color;
  row.append(swatch,`${c.thickness} mm · ${c.layer}`);$('thicknessLegend').appendChild(row);
}
const colourNote=document.createElement('p');colourNote.textContent='Supplier cut file colors. Other items keep their usual colors.';$('thicknessLegend').appendChild(colourNote);
function setColourMode(key,checked){
  state[key]=checked;
  if(checked){const other=key==='thickness'?'highlight':'thickness';state[other]=false;$(other==='thickness'?'showThickness':'highlight').checked=false;}
  $('thicknessLegend').hidden=!state.thickness;recolour();
}
$('showThickness').addEventListener('change',e=>setColourMode('thickness',e.target.checked));
$('highlight').addEventListener('change',e=>setColourMode('highlight',e.target.checked));
function displayMaterial(mesh){
  if(searchMatches.has(mesh))return searchMaterial;
  const rev=mesh.userData.part?.revision;
  const normal=state.thickness&&mesh.userData.dxf?mesh.userData.dxf:state.highlight&&flagged[rev]?flagged[rev]:mesh.userData.base;
  if(searchMatches.size&&state.xray){
    if(!ghostMaterials.has(normal)){const ghost=normal.clone();ghost.transparent=true;ghost.opacity=.12;ghost.depthWrite=false;ghostMaterials.set(normal,ghost);}
    return ghostMaterials.get(normal);
  }
  return normal;
}
function recolour(){for(const m of meshes)m.material=m===picked&&!searchMatches.size?pickMaterial:displayMaterial(m);}

const cutPlane=new THREE.Plane(new THREE.Vector3(0,0,-1),total);
function apply(){
  const rad=THREE.MathUtils.degToRad;
  nodes.WallRight.pivot.rotation.z=hingeRadians(state.wallRight);nodes.WallLeft.pivot.rotation.z=hingeRadians(state.wallLeft,-1);
  for(const d of Object.values(doors))d.pivot.rotation.z=hingeRadians(state.doors,d.sign);
  nodes.Drawer.pivot.position.set(...drawerOffset(derived.drawer.direction,state.drawer));
  // The roof rises after both catches turn inward by 90 degrees.
  const release=Math.min(1,state.lift/20);for(const c of Object.values(catches))c.pivot.rotation.z=rad(90*release);
  nodes.Roof.pivot.position.z=Math.max(0,state.lift-20)*1.1;
  nodes.Roof.explode.visible=!(state.roof==='off'||state.roof==='attic');
  for(const m of attic)m.visible=state.roof!=='attic'&&(m.userData.kind!=='fastener'||state.hardware);
  for(const [g,offset] of Object.entries(derived.views.exploded))if(nodes[g])nodes[g].explode.position.set(...offset.map(v=>v*state.explode/100));
  if(nodes.Printables&&derived.views.exploded.Furniture)nodes.Printables.explode.position.set(...derived.views.exploded.Furniture.map(v=>v*state.explode/100));
  nodes.Porch.explode.visible=state.porch;nodes.Furniture.explode.visible=state.furniture;nodes.Garden.explode.visible=state.furniture;nodes.Figures.explode.visible=state.figures;
  if(nodes.Printables)nodes.Printables.explode.visible=state.printables;
  for(const h of hardwareObjects)if(!h.userData.owners?.some(id=>atticIds.has(id))||state.roof!=='attic')h.visible=state.hardware;
  for(const l of lines)l.visible=state.edges&&l.userData.mesh.visible;
  for(const o of dimObjects)o.visible=state.dims;
  const showIds=$('showPieceIds').checked,labelPosition=new THREE.Vector3();
  for(const tag of pieceLabels)tag.visible=(showIds||searchMatches.has(tag.parent))&&visibleChain(tag.parent)&&(state.cut>=total||tag.getWorldPosition(labelPosition).z<=state.cut+.01);
  for(const [key,m] of Object.entries(materials))if(key.endsWith(':wall')){m.transparent=state.xray;m.opacity=state.xray?.22:1;m.depthWrite=!state.xray;}
  cutPlane.constant=state.cut;renderer.clippingPlanes=state.cut>=total?[]:[cutPlane];
}

// ---------- picking ----------
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let downAt=null,picked=null;
recolour();
function visibleChain(o){for(let p=o;p;p=p.parent)if(!p.visible)return false;return true;}
renderer.domElement.addEventListener('pointerdown',e=>{downAt=[e.clientX,e.clientY];});
renderer.domElement.addEventListener('pointerup',e=>{
  if(!downAt||Math.hypot(e.clientX-downAt[0],e.clientY-downAt[1])>4)return;
  const rect=host.getBoundingClientRect();
  pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);
  const hit=ray.intersectObjects(meshes,false).find(h=>visibleChain(h.object)&&(state.cut>=total||h.point.z<=state.cut+.01));
  select(hit?hit.object:null);
});
addEventListener('keydown',e=>{if(e.key==='Escape'&&!e.defaultPrevented&&!$('housePanel').hidden){clearElementSearch();select(null);}});
function select(mesh){
  const prev=picked;picked=mesh;if(prev)prev.material=displayMaterial(prev);const box=$('info');
  if(!mesh){box.style.display='none';return;}
  mesh.material=searchMatches.has(mesh)?searchMaterial:pickMaterial;box.style.display='block';
  if(mesh.userData.kind==='fastener'){const f=mesh.userData.fastener;box.innerHTML=`<b>${f.type}</b> · ${f.diameter} x ${f.length} mm<div class="meta">${f.id}</div><div class="note">${f.note}</div>`;return;}
  if(mesh.userData.kind==='figure'){
    const f=mesh.userData.figure,c=mesh.userData.part.clay,colours=Object.entries(c.grams_by_colour).filter(([,g])=>g>=.5).map(([k,g])=>`${k} ${Math.round(g)} g`).join(', ');
    box.innerHTML=`<b>${f.id}</b><span class="tag">thermo-clay</span>${f.revision?`<span class="tag">${f.revision}</span>`:''}<div>${f.name}</div>`+
      `<div class="meta">${f.room} · X${f.x} Y${f.y} · ${c.height.toFixed(0)} tall, ${c.length.toFixed(0)} long, ${c.width.toFixed(0)} wide · ${(c.volume_mm3/1000).toFixed(1)} cm³</div>`+
      `<div class="note">Clay to buy: about ${Math.round(c.grams)} g (${colours}); about ${Math.round(c.grams_with_core)} g with a foil core. Book page 3 shows it from four sides.</div>`;return;
  }
  if(mesh.userData.kind==='printable'){
    const p=mesh.userData.printable;
    box.innerHTML=`<b>${p.title}</b><span class="tag">3D print</span>`+
      `<div class="meta">${p.size?.map(v=>Number(v.toFixed(1))).join(' × ')} mm${p.grams?.estimate ? ` · ≈ ${p.grams.estimate} g PLA` : ''}</div>`+
      `<div class="note">${p.notes || '3D-printable object. Download STL / 3MF in Prints tab.'}</div>`;return;
  }
  const {inst:i,part:p}=mesh.userData;
  const tags=(p.render_only?'<span class="tag">view only</span>':p.optional?'<span class="tag">optional</span>':'')+(p.revision?`<span class="tag">${p.revision}</span>`:'');
  if(p.render_only){
    box.innerHTML=`<b>${p.id}</b>${tags}<div>${p.name}</div>`+
      `<div class="meta">${p.width.toFixed(1)} x ${p.height.toFixed(1)} x ${p.thickness} mm · ${p.quantity} shown<br>${i.label} · ${LABEL[i.group]??i.group}</div>`+
      '<div class="note">Example for the 3D view only.</div>';return;
  }
  box.innerHTML=`<b>${p.id}</b>${tags}<div>${p.name}</div>`+
    `<div class="meta">${p.thickness} mm · ${p.width.toFixed(1)} x ${p.height.toFixed(1)} mm outline · ${p.quantity} required<br>${i.label} · ${LABEL[i.group]??i.group} · ${p.category}</div>`+
    (p.note?`<div class="note">${p.note}</div>`:'');
}

// ---------- exact element search ----------
function clearElementSearch(){
  searchMatches.clear();
  for(const mesh of meshes)mesh.renderOrder=0;
  if(searchRestore){state.xray=searchRestore.xray;$('xray').checked=state.xray;searchRestore=null;}
  select(null);recolour();$('elementId').value='';$('elementId').removeAttribute('aria-invalid');
  $('searchStatus').textContent='Exact ID → X-ray, yellow highlight and camera focus.';
}
function findElement(){
  const query=$('elementId').value.trim().toUpperCase();
  if(!query){clearElementSearch();return;}
  const exact=meshes.filter(m=>m.userData.inst?.id.toUpperCase()===query);
  const matches=exact.length?exact:meshes.filter(m=>m.userData.part?.id.toUpperCase()===query);
  if(!matches.length){
    clearElementSearch();$('elementId').value=query;$('elementId').setAttribute('aria-invalid','true');
    $('searchStatus').textContent=`No exact match for ${query}. Enter a full part or instance ID.`;return;
  }
  searchRestore??={xray:state.xray};searchMatches.clear();matches.forEach(m=>searchMatches.add(m));
  state.xray=true;$('xray').checked=true;
  state.cut=total+10;$('cut').value=state.cut;$('cutOut').textContent='off';
  for(const mesh of matches){
    const group=mesh.userData.inst?.group;
    if(group==='Porch'){state.porch=true;$('showPorch').checked=true;}
    if(group==='Furniture'||group==='Garden'){state.furniture=true;$('showFurniture').checked=true;}
    if(group==='Figures'){state.figures=true;$('showFigures').checked=true;}
    if(group==='Roof'||group==='RoofLocks'||attic.includes(mesh)){setRoof('on');state.lift=target.lift=0;}
  }
  apply();root.updateMatrixWorld(true);
  matches.forEach(m=>{m.renderOrder=100;});
  for(const m of meshes)if(!searchMatches.has(m))m.renderOrder=0;
  select(matches[0]);recolour();
  const box=new THREE.Box3();matches.forEach(m=>box.union(new THREE.Box3().setFromObject(m)));
  const centre=box.getCenter(new THREE.Vector3()),radius=Math.max(5,box.getBoundingSphere(new THREE.Sphere()).radius);
  const vertical=THREE.MathUtils.degToRad(camera.fov/2),horizontal=Math.atan(Math.tan(vertical)*camera.aspect);
  const distance=Math.max(35,radius/Math.sin(Math.min(vertical,horizontal))*1.2);
  const direction=camera.position.clone().sub(controls.target).normalize();if(direction.lengthSq()===0)direction.set(-1,-1,.6).normalize();
  flight={from:camera.position.clone(),to:centre.clone().addScaledVector(direction,distance),fromT:controls.target.clone(),toT:centre,t:0};
  $('elementId').removeAttribute('aria-invalid');
  $('searchStatus').textContent=`${query} · ${matches.length} ${matches.length===1?'piece':'pieces'} highlighted in yellow. X-ray on.`;
}
$('elementSearch').addEventListener('submit',e=>{e.preventDefault();findElement();});
$('elementId').addEventListener('input',findElement);
$('clearSearch').addEventListener('click',clearElementSearch);

// ---------- camera views ----------
const VIEWS={iso:[-60,22],front:[-90,8],back:[90,8],left:[180,8],right:[0,8],top:[-90,89],veranda:[-75+(Number(config.veranda.facet.slice(1))-1)*30,16]};
let flight=null;
function view(name){
  if(name!=='fit')for(const button of document.querySelectorAll('[data-view]')){const selected=button.dataset.view===name;button.classList.toggle('on',selected);button.setAttribute('aria-pressed',String(selected));}
  const box=new THREE.Box3();meshes.forEach(m=>{if(visibleChain(m)&&m.userData.kind==='part')box.union(new THREE.Box3().setFromObject(m));});
  const centre=box.getCenter(new THREE.Vector3()),radius=box.getBoundingSphere(new THREE.Sphere()).radius;
  const vertical=THREE.MathUtils.degToRad(camera.fov/2);
  const horizontal=Math.atan(Math.tan(vertical)*camera.aspect);
  const dist=radius/Math.sin(Math.min(vertical,horizontal))*1.05;
  const [az,el]=name==='fit'?(()=>{const d=camera.position.clone().sub(controls.target);return [THREE.MathUtils.radToDeg(Math.atan2(d.y,d.x)),THREE.MathUtils.radToDeg(Math.asin(d.z/d.length()))];})():VIEWS[name];
  const a=THREE.MathUtils.degToRad(az),b=THREE.MathUtils.degToRad(el);
  const to=centre.clone().add(new THREE.Vector3(Math.cos(a)*Math.cos(b),Math.sin(a)*Math.cos(b),Math.sin(b)).multiplyScalar(dist));
  flight={from:camera.position.clone(),to,fromT:controls.target.clone(),toT:centre,t:0};
}
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));

// ---------- loop ----------
const count=instances.filter(i=>nodes[i.group]&&!parts[i.part].render_only).length;
const profileCount=Object.values(parts).filter(p=>!p.render_only).length;
$('stats').textContent=`${profileCount} build part profiles · ${count} build pieces · ${total} mm tall · walls open to ${derived.views.open_angle}°`;
camera.position.set(1300,-1700,1100);controls.target.set(0,0,total/2);view('iso');flight.t=1;camera.position.copy(flight.to);controls.target.copy(flight.toT);
const clock=new THREE.Clock();
renderer.setAnimationLoop(()=>{
  const dt=Math.min(clock.getDelta(),.05),k=1-Math.exp(-dt*6);
  if(document.hidden||$('housePanel').hidden)return;
  for(const key of ['walls','wallLeft','wallRight','doors','drawer','lift','explode']){
    if(Math.abs(state[key]-target[key])>.05)state[key]+=(target[key]-state[key])*k;else state[key]=target[key];
    if(setters[key])setters[key](key==='drawer'?state[key]:Math.round(state[key]));
  }
  if(flight&&flight.t<1){flight.t=Math.min(1,flight.t+dt*1.8);const s=flight.t*flight.t*(3-2*flight.t);camera.position.lerpVectors(flight.from,flight.to,s);controls.target.lerpVectors(flight.fromT,flight.toT,s);}
  apply();controls.update();renderer.render(scene,camera);labels.render(scene,camera);
  document.getElementById('loading')?.remove();
  host.dataset.ready='true';
});
// The canvas now lives beside the tools, so its own bounds drive the camera.
let previousSize='';
new ResizeObserver(()=>{
  const w=host.clientWidth,h=host.clientHeight;
  if(!w||!h||previousSize===`${w},${h}`)return;
  previousSize=`${w},${h}`;camera.aspect=w/h;camera.updateProjectionMatrix();
  renderer.setSize(w,h);labels.setSize(w,h);
  if(!searchMatches.size)view('fit');
}).observe(host);
