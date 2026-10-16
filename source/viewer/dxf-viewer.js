// A small, offline DXF workspace for the actual supplier cutting file.
const $=id=>document.getElementById(id);
const colours={1:'#ff0000',2:'#ffff00',3:'#00ff00',4:'#00ffff',5:'#4f8fff',6:'#ff00ff',7:'#ffffff'};

export function parseDxf(text){
  const lines=text.replace(/^\uFEFF/,'').replace(/\r/g,'').trimEnd().split('\n');
  if(lines.length%2)throw new Error('Invalid DXF: incomplete group code pair.');
  const records=[];let record=null;
  for(let i=0;i<lines.length;i+=2){
    const code=Number(lines[i].trim()),value=lines[i+1].trim();
    if(!Number.isInteger(code)||lines[i].trim()==='')throw new Error('Invalid DXF group code.');
    if(code===0){record={type:value,fields:[]};records.push(record);}
    else if(record)record.fields.push([code,value]);
  }
  const get=(r,c,fallback)=>r.fields.find(([code])=>code===c)?.[1]??fallback;
  const number=(r,c,fallback=0)=>{const n=Number(get(r,c,fallback));if(!Number.isFinite(n))throw new Error('Invalid DXF coordinate.');return n;};
  const point=r=>[number(r,10),number(r,20)];
  const layers=new Map(),entities=[],unsupported=new Set();let inEntities=false;
  for(let i=0;i<records.length;i++){
    const r=records[i];
    if(r.type==='LAYER'){const name=get(r,2,'0'),aci=Math.abs(number(r,62,7));layers.set(name,{name,color:colours[aci]??'#b8cbd3'});}
    if(r.type==='SECTION'){inEntities=get(r,2)==='ENTITIES';continue;}
    if(r.type==='ENDSEC'){inEntities=false;continue;}
    if(!inEntities)continue;
    const layer=get(r,8,'0');if(!layers.has(layer))layers.set(layer,{name:layer,color:colours[Math.abs(number(r,62,7))]??'#b8cbd3'});
    let entity;
    if(r.type==='CIRCLE'||r.type==='ARC'){
      const radius=number(r,40);if(radius<=0)throw new Error('Invalid DXF circle radius.');
      entity={type:r.type,center:point(r),radius,start:number(r,50)*Math.PI/180,end:number(r,51)*Math.PI/180};
    }else if(r.type==='LINE')entity={type:'POLYLINE',points:[point(r),[number(r,11),number(r,21)]],closed:false};
    else if(r.type==='POLYLINE'){
      const points=[];let bulge=false;
      while(records[i+1]?.type==='VERTEX'){const vertex=records[++i];points.push(point(vertex));bulge||=number(vertex,42)!==0;}
      if(records[i+1]?.type!=='SEQEND')throw new Error('Invalid DXF: polyline has no end.');
      i++;if(bulge)throw new Error('Curved polyline segments are not supported.');
      if(points.length<2)throw new Error('Invalid DXF polyline.');
      entity={type:'POLYLINE',points,closed:Boolean(number(r,70)&1)};
    }else if(r.type==='LWPOLYLINE'){
      const points=[];
      for(const [code,value] of r.fields){if(code===10)points.push([Number(value),0]);if(code===20&&points.length)points.at(-1)[1]=Number(value);if(code===42&&Number(value)!==0)throw new Error('Curved polyline segments are not supported.');}
      if(points.length<2||points.some(p=>p.some(n=>!Number.isFinite(n))))throw new Error('Invalid DXF polyline.');
      entity={type:'POLYLINE',points,closed:Boolean(number(r,70)&1)};
    }else unsupported.add(r.type);
    if(entity)entities.push({...entity,layer});
  }
  if(unsupported.size)throw new Error(`Unsupported DXF entities: ${[...unsupported].join(', ')}. Open a drawing with lines, polylines, circles or arcs.`);
  if(!entities.length)throw new Error('This DXF contains no supported drawing paths.');
  // The project drawing uses millimeters. Preserve the unit label when opening other DXF files.
  let units='drawing units';
  for(let i=0;i<lines.length-3;i+=2)if(lines[i].trim()==='9'&&lines[i+1].trim()==='$INSUNITS')units=({'0':'drawing units','1':'in','4':'mm','5':'cm','6':'m'})[lines[i+3].trim()]??'drawing units';
  return {entities,layers,units};
}

const panel=$('dxfPanel'),viewport=$('dxfViewport'),status=$('dxfStatus');
let canvas,ctx,drawing,sourceText='',fileName='Lanternwood-House-Supplier-Cut.dxf',pending,needsFit=false;
let scale=1,tx=0,ty=0,fitScale=1,width=1,height=1;
let pieceLabels=[];
const hidden=new Set(),pointers=new Map();
const world=(x,y)=>[(x-tx)/scale,(ty-y)/scale];
const local=e=>{const rect=canvas.getBoundingClientRect();return [e.clientX-rect.left,e.clientY-rect.top];};
const visible=()=>drawing?.entities.filter(e=>!hidden.has(e.layer))??[];

function bounds(entities){
  let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
  for(const e of entities){
    const points=e.points??[[e.center[0]-e.radius,e.center[1]-e.radius],[e.center[0]+e.radius,e.center[1]+e.radius]];
    for(const [x,y] of points){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
  }
  return [x0,y0,x1,y1];
}
function draw(){
  if(!ctx)return;
  const dpr=Math.min(devicePixelRatio||1,2);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);
  if(!drawing)return;
  // Choose a grid interval with roughly 70 pixels between lines.
  const rough=70/scale,power=10**Math.floor(Math.log10(rough)),step=[1,2,5,10].find(n=>n*power>=rough)*power;
  const [left,top]=world(0,0),[right,bottom]=world(width,height);
  ctx.strokeStyle='#22343e';ctx.lineWidth=1;ctx.beginPath();
  for(let x=Math.ceil(left/step)*step;x<=right;x+=step){const px=tx+x*scale;ctx.moveTo(px,0);ctx.lineTo(px,height);}
  for(let y=Math.ceil(bottom/step)*step;y<=top;y+=step){const py=ty-y*scale;ctx.moveTo(0,py);ctx.lineTo(width,py);}
  ctx.stroke();ctx.save();ctx.translate(tx,ty);ctx.scale(scale,-scale);ctx.lineWidth=1.3/scale;
  for(const e of visible()){
    ctx.strokeStyle=drawing.layers.get(e.layer).color;ctx.beginPath();
    if(e.points){e.points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));if(e.closed)ctx.closePath();}
    else ctx.arc(...e.center,e.radius,e.type==='ARC'?e.start:0,e.type==='ARC'?e.end:Math.PI*2);
    ctx.stroke();
  }
  ctx.restore();
  const labels=$('dxfPieceIds').checked?pieceLabels.filter(label=>!hidden.has(label.layer)):[];
  ctx.font='600 11px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';
  for(const label of labels){
    const x=tx+label.x*scale,y=ty-label.y*scale;if(x<0||x>width||y<0||y>height)continue;
    const w=ctx.measureText(label.id).width+8;ctx.fillStyle='rgba(16,28,35,.9)';ctx.fillRect(x-w/2,y-8,w,16);
    ctx.fillStyle='#edf5fa';ctx.fillText(label.id,x,y);
  }
  ctx.textAlign='left';ctx.textBaseline='alphabetic';ctx.fillStyle='#9cafbb';ctx.font='11px system-ui';ctx.fillText(`Grid ${Number(step.toPrecision(4))} ${drawing.units}`,12,height-12);
  $('dxfZoom').value=`${Math.round(scale/fitScale*100)}%`;
  canvas.dataset.scale=String(scale);canvas.dataset.pan=`${tx},${ty}`;canvas.dataset.labels=String(labels.length);
}
function fit(){
  const entities=visible();if(!entities.length){draw();return;}
  const [x0,y0,x1,y1]=bounds(entities);
  scale=fitScale=Math.max(.0001,Math.min((width-48)/Math.max(x1-x0,1),(height-48)/Math.max(y1-y0,1)));
  tx=width/2-(x0+x1)/2*scale;ty=height/2+(y0+y1)/2*scale;draw();
}
function zoom(factor,x=width/2,y=height/2){
  if(!drawing)return;
  const [wx,wy]=world(x,y);scale=Math.min(fitScale*250,Math.max(fitScale*.05,scale*factor));
  tx=x-wx*scale;ty=y+wy*scale;draw();
}
function resize(){
  if(!canvas||panel.hidden)return;
  const center=world(width/2,height/2);width=viewport.clientWidth;height=viewport.clientHeight;
  const dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
  tx=width/2-center[0]*scale;ty=height/2+center[1]*scale;draw();
}
function init(){
  if(canvas)return;
  canvas=document.createElement('canvas');canvas.tabIndex=0;canvas.setAttribute('aria-label','DXF drawing. Drag to pan, scroll to zoom, or use the keyboard.');viewport.appendChild(canvas);ctx=canvas.getContext('2d');
  canvas.addEventListener('wheel',e=>{e.preventDefault();zoom(Math.exp(-Math.max(-200,Math.min(200,e.deltaY))*.002),...local(e));},{passive:false});
  canvas.addEventListener('pointerdown',e=>{if(e.button!==0&&e.button!==1&&e.button!==2)return;e.preventDefault();canvas.focus();canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,local(e));});
  canvas.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId))return;
    const old=[...pointers.values()],from=pointers.get(e.pointerId),to=local(e);pointers.set(e.pointerId,to);
    if(pointers.size===1){tx+=to[0]-from[0];ty+=to[1]-from[1];draw();}
    else if(pointers.size===2){
      const next=[...pointers.values()],mid=p=>[(p[0][0]+p[1][0])/2,(p[0][1]+p[1][1])/2];
      const before=mid(old),after=mid(next),distance=p=>Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);
      zoom(distance(next)/Math.max(distance(old),1),...before);tx+=after[0]-before[0];ty+=after[1]-before[1];draw();
    }
  });
  for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>pointers.delete(e.pointerId));
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('keydown',e=>{
    const moves={ArrowLeft:[50,0],ArrowRight:[-50,0],ArrowUp:[0,50],ArrowDown:[0,-50]};
    if(moves[e.key]){e.preventDefault();tx+=moves[e.key][0];ty+=moves[e.key][1];draw();}
    else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1.3);}
    else if(e.key==='-'){e.preventDefault();zoom(1/1.3);}
    else if(e.key.toLowerCase()==='f'){e.preventDefault();fit();}
  });
  new ResizeObserver(resize).observe(viewport);
}
function load(text,name,labels=[]){
  const parsed=parseDxf(text);drawing=parsed;sourceText=text;fileName=name;pieceLabels=labels;
  $('dxfPieceIds').disabled=!pieceLabels.length;$('dxfPieceIds').title=pieceLabels.length?'Show the build ID of each piece':'Piece IDs are available for the house drawing';
  hidden.clear();$('dxfLayers').replaceChildren();
  for(const layer of drawing.layers.values()){
    if(!drawing.entities.some(e=>e.layer===layer.name))continue;
    const label=document.createElement('label'),checkbox=document.createElement('input'),swatch=document.createElement('span');
    checkbox.type='checkbox';checkbox.checked=true;checkbox.setAttribute('aria-label',`Show ${layer.name}`);
    checkbox.addEventListener('change',()=>{if(checkbox.checked)hidden.delete(layer.name);else hidden.add(layer.name);draw();});
    swatch.className='key';swatch.style.background=layer.color;label.append(checkbox,swatch,document.createTextNode(layer.name));$('dxfLayers').appendChild(label);
  }
  const [x0,y0,x1,y1]=bounds(drawing.entities);
  status.textContent=`${name} · ${drawing.entities.length} paths · ${(x1-x0).toFixed(1)} × ${(y1-y0).toFixed(1)} ${drawing.units}`;
  status.setAttribute('role','status');viewport.setAttribute('aria-busy','false');viewport.dataset.ready='true';$('dxfDownload').disabled=false;
  needsFit=true;if(!panel.hidden){resize();fit();needsFit=false;}
}
function error(message){status.textContent=message;status.setAttribute('role','alert');viewport.setAttribute('aria-busy','false');}
async function open(){
  init();resize();
  if(drawing){if(needsFit){fit();needsFit=false;}return;}
  status.textContent='Loading the supplier drawing…';status.setAttribute('role','status');viewport.setAttribute('aria-busy','true');
  pending??=Promise.all([
    fetch('./data/house.dxf').then(async response=>{if(!response.ok)throw new Error(`Could not load the DXF (HTTP ${response.status}).`);return response.text();}),
    fetch('./data/dxf-labels.json').then(async response=>{if(!response.ok)throw new Error(`Could not load the piece IDs (HTTP ${response.status}).`);return response.json();})
  ]).finally(()=>{pending=null;});
  try{const [text,labels]=await pending;if(!drawing)load(text,'Lanternwood-House-Supplier-Cut.dxf',labels);}catch(e){error(`${e.message} Switch tabs to retry, or open a DXF file.`);}
}
addEventListener('previewchange',event=>{
  pointers.clear();
  if(event.detail.preview==='dxf')open();
});
if(!panel.hidden)open();
$('dxfZoomIn').addEventListener('click',()=>zoom(1.3));$('dxfZoomOut').addEventListener('click',()=>zoom(1/1.3));$('dxfFit').addEventListener('click',fit);
$('dxfPieceIds').addEventListener('change',draw);
$('dxfOpen').addEventListener('click',()=>$('dxfFile').click());
$('dxfFile').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file)return;
  try{if(file.size>10*1024*1024)throw new Error('Choose a DXF smaller than 10 MB.');load(await file.text(),file.name);}catch(e){error(e.message);}finally{$('dxfFile').value='';}
});
$('dxfDownload').addEventListener('click',()=>{
  const url=URL.createObjectURL(new Blob([sourceText],{type:'application/dxf'})),link=document.createElement('a');link.href=url;link.download=fileName;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
