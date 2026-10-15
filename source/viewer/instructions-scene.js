// A separate scene and camera; shared CAD geometry keeps both previews consistent.
import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {geometryOf,matrixOf} from './geometry.js';
import {hingeRadians,drawerOffset} from './motion.js';

export function createInstructionScene(host,data,onInspect,onPlayback){
  const renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setClearColor(0xeef2ee);
  host.append(renderer.domElement);renderer.domElement.setAttribute('aria-label','Assembly model. Drag to orbit and pinch or scroll to zoom.');
  const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(32,1,1,20000);
  camera.up.set(0,0,1);camera.position.set(900,-1200,800);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
  scene.add(new THREE.HemisphereLight(0xffffff,0x8a9a8a,2));
  const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(-700,-1100,1600);scene.add(light);
  const current=new THREE.MeshStandardMaterial({color:0xffcb28,roughness:.7,side:THREE.DoubleSide});
  const context=new THREE.MeshStandardMaterial({color:0xb1c4c5,roughness:.9,transparent:true,opacity:.35,depthWrite:false,side:THREE.DoubleSide});
  const geometry=new Map(),pieces=new Map(),byId=new Map(data.instances.map(i=>[i.id,i]));
  const edgeMaterial=new THREE.LineBasicMaterial({color:0x203c6f,transparent:true,opacity:.5});
  for(const inst of data.instances){
    const part=data.parts[inst.part];if(part.render_only)continue;
    if(!geometry.has(inst.part))geometry.set(inst.part,geometryOf(part));
    const group=new THREE.Group(),mesh=new THREE.Mesh(geometry.get(inst.part),context);
    mesh.matrixAutoUpdate=false;mesh.matrix.copy(matrixOf(inst));mesh.userData={inst,part};
    const edge=new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry),edgeMaterial);edge.matrixAutoUpdate=false;edge.matrix.copy(mesh.matrix);
    group.add(mesh,edge);scene.add(group);pieces.set(inst.id,{group,mesh,edge});
  }
  const guides=new THREE.Group();scene.add(guides);
  let step,shownProgress=null,progress=1,playing=false,active=true,last=performance.now(),close=false;
  const reduce=matchMedia('(prefers-reduced-motion: reduce)');
  const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down;
  renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
  renderer.domElement.addEventListener('pointerup',e=>{
    if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
    const rect=host.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);
    ray.setFromCamera(pointer,camera);
    const hit=ray.intersectObjects([...pieces.values()].filter(p=>p.group.visible).map(p=>p.mesh),false)[0];
    onInspect(hit?.object.userData??null);
  });
  function bounds(focused){
    const box=new THREE.Box3();
    for(const [id,piece] of pieces)if(piece.group.visible&&(!focused||step.focus.includes(id)))box.union(new THREE.Box3().setFromObject(piece.group));
    if(box.isEmpty())box.setFromCenterAndSize(new THREE.Vector3(0,0,100),new THREE.Vector3(400,400,200));
    return box;
  }
  function fit(focused=false){
    close=focused;scene.updateMatrixWorld(true);
    const box=bounds(focused),centre=box.getCenter(new THREE.Vector3()),radius=Math.max(15,box.getBoundingSphere(new THREE.Sphere()).radius);
    const fov=THREE.MathUtils.degToRad(camera.fov/2),horizontal=Math.atan(Math.tan(fov)*camera.aspect);
    const distance=radius/Math.sin(Math.min(fov,horizontal))*1.15;
    const direction=new THREE.Vector3(-.6,-1,.65).normalize();camera.position.copy(centre).addScaledVector(direction,distance);controls.target.copy(centre);controls.update();
  }
  function clearGuides(){
    for(const obj of [...guides.children]){guides.remove(obj);obj.geometry?.dispose();obj.material?.dispose();}
  }
  function setStep(next){
    step=next;playing=false;progress=1;shownProgress=null;onPlayback(false);onInspect(null);
    const installed=new Set(step.context),focus=new Set(step.focus),added=new Set(step.installs);
    for(const [id,piece] of pieces){
      piece.group.position.set(0,0,0);piece.group.rotation.set(0,0,0);piece.mesh.matrix.copy(matrixOf(byId.get(id)));piece.edge.matrix.copy(piece.mesh.matrix);piece.group.visible=installed.has(id)||focus.has(id)||added.has(id);
      // Temporary tools stay out of the assembled house, except during preparation.
      if(byId.get(id).group==='Tools'&&step.chapter!=='prepare')piece.group.visible=false;
      piece.mesh.material=focus.has(id)?current:context;
    }
    clearGuides();
    for(const joint of step.joints){
      if(!joint.outline?.length)continue;
      const points=[...joint.outline,joint.outline[0]].map(p=>new THREE.Vector3(...p));
      guides.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:0xde6c28,depthTest:false})));
    }
    for(const f of step.fasteners){
      const origin=new THREE.Vector3(...f.origin),axis=new THREE.Vector3(...f.axis).normalize();
      const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([origin,origin.clone().addScaledVector(axis,f.length)]),new THREE.LineBasicMaterial({color:0x20699f,depthTest:false}));guides.add(line);
    }
    host.dataset.step=step.id;host.dataset.visible=String([...pieces.values()].filter(p=>p.group.visible).length);fit();
  }
  function playback(){
    if(!step||(!step.installs.length&&!step.motion)||reduce.matches){progress=1;playing=false;onPlayback(false);return;}
    if(playing){playing=false;onPlayback(false);return;}
    if(progress>=1)progress=0;
    playing=true;last=performance.now();onPlayback(true);
  }
  function replay(){progress=1;playing=false;playback();}
  const observer=new ResizeObserver(()=>{
    const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;
    renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();if(step)fit(close);
  });observer.observe(host);
  renderer.setAnimationLoop(()=>{
    const now=performance.now(),dt=Math.min((now-last)/1000,.05);last=now;
    if(!active||document.hidden)return;
    if(playing){progress=Math.min(1,progress+dt/2);if(progress===1){playing=false;onPlayback(false);}}
    if(step&&shownProgress!==progress){
      shownProgress=progress;
      const ease=1-progress*progress*(3-2*progress),sweep=Math.sin(progress*Math.PI);
      for(const [id,piece] of pieces){
        piece.group.position.set(0,0,0);piece.group.rotation.set(0,0,0);piece.mesh.matrix.copy(matrixOf(byId.get(id)));piece.edge.matrix.copy(piece.mesh.matrix);
        if(!piece.group.visible)continue;
        const group=byId.get(id).group;
        if(step.motion){
          if((step.motion==='walls'||step.motion==='all')&&data.derived.hinge_axes[group]){
            const [x,y]=data.derived.hinge_axes[group];
            piece.group.position.set(x,y,0);piece.group.rotation.z=hingeRadians(data.derived.views.open_angle*sweep,group==='WallLeft'?-1:1);
            const offset=new THREE.Matrix4().makeTranslation(-x,-y,0);piece.mesh.matrix.premultiply(offset);piece.edge.matrix.copy(piece.mesh.matrix);
          }
          if((step.motion==='drawer'||step.motion==='all')&&group==='Drawer')piece.group.position.set(...drawerOffset(data.derived.drawer.direction,data.derived.drawer.travel*sweep));
          if(step.motion==='all'&&group==='Roof')piece.group.position.z=150*sweep;
        }else if(step.installs.includes(id))piece.group.position.set(...step.approach.map(v=>v*ease));
      }
    }
    controls.update();renderer.render(scene,camera);host.dataset.ready='true';host.dataset.playing=String(playing);
  });
  return {setStep,playback,replay,fit,setActive(value){active=value;if(!value){playing=false;onPlayback(false);}},dispose(){observer.disconnect();renderer.setAnimationLoop(null);controls.dispose();renderer.dispose();clearGuides();for(const g of geometry.values())g.dispose();}};
}
