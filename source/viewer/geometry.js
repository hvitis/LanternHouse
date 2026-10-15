// Shared CAD profile reconstruction and instance placement, in millimetres (Z up).
import * as THREE from 'three';

function profileShape(p){
  const shape=new THREE.Shape();
  if(p.outercircle){const [cx,cy,r]=p.outercircle;shape.absarc(cx,cy,r,0,Math.PI*2,false);}
  else{p.outer.forEach(([x,y],k)=>k?shape.lineTo(x,y):shape.moveTo(x,y));shape.closePath();}
  for(const cut of p.cuts){const h=new THREE.Path();cut.forEach(([x,y],k)=>k?h.lineTo(x,y):h.moveTo(x,y));h.closePath();shape.holes.push(h);}
  // Through holes only; blind pilots would need a boolean cut.
  for(const hole of p.holes){if(hole.depth==null||hole.depth>=p.thickness-1e-6){const h=new THREE.Path();h.absarc(hole.x,hole.y,hole.diameter/2,0,Math.PI*2,true);shape.holes.push(h);}}
  return shape;
}
function compoundGeometry(boxes){
  const positions=[];
  for(const box of boxes){
    const g=new THREE.BoxGeometry(...box.size).toNonIndexed();
    g.translate(...box.origin.map((value,k)=>value+box.size[k]/2));
    positions.push(...g.attributes.position.array);g.dispose();
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();return g;
}
export function geometryOf(p){
  return p.boxes?compoundGeometry(p.boxes):p.sphere?new THREE.SphereGeometry(p.sphere,48,24).rotateX(Math.PI/2).translate(p.sphere,p.sphere,p.sphere):new THREE.ExtrudeGeometry(profileShape(p),{depth:p.thickness,bevelEnabled:false,curveSegments:p.outercircle?96:20});
}
export function matrixOf(i){const [u,v,w,o]=[i.u,i.v,i.w,i.origin];return new THREE.Matrix4().set(u[0],v[0],w[0],o[0],u[1],v[1],w[1],o[1],u[2],v[2],w[2],o[2],0,0,0,1).scale(new THREE.Vector3(...(i.scale??[1,1,1])));}
