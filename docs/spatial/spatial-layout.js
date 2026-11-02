import * as THREE from './vendor/three.module.js';
export const LIMITS = Object.freeze({maxItems:60,maxPixelRatio:1.5,maxDrawingPixels:1800000,animationMs:650});
export function validateItems(items){
 if(!Array.isArray(items)||!items.length||items.length>LIMITS.maxItems)throw new Error('目录必须包含1至60项');
 const ids=new Set();
 for(const item of items){
  if(!item||typeof item.id!=='string'||! /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(item.id)||ids.has(item.id))throw new Error('目录编号无效或重复');
  if(!['regular','fusion','space-design','recipe','method'].includes(item.kind))throw new Error('未知目录类型');
  if(typeof item.name!=='string'||!item.name.trim()||item.name.length>120)throw new Error('目录名称无效');
  ids.add(item.id);
 }
 return items;
}
export function layoutItems(items){
 validateItems(items);
 const groups=[{key:'regular',name:'模型与介绍页',x:-8,cols:3},{key:'fusion',name:'历史实验待重做',x:3,cols:2},{key:'space-design',name:'新空间原型 · 待验收',x:7,cols:1},{key:'methods',name:'复用方法',x:11,cols:2}];
 const nodes=[];
 for(const group of groups){
  const members=items.filter(x=>group.key==='methods'?['recipe','method'].includes(x.kind):x.kind===group.key);
  const rows=Math.ceil(members.length/group.cols);
  members.forEach((item,i)=>{const row=Math.floor(i/group.cols),rowCount=Math.min(group.cols,members.length-row*group.cols);nodes.push({...item,position:[group.x+(i%group.cols-(rowCount-1)/2)*3.1,0,(row-(rows-1)/2)*3.7],zone:group.key});});
 }
 return {nodes,groups};
}
const COLOR={regular:0x728f87,fusion:0xb97755,'space-design':0x3e7899,recipe:0x9388a5,method:0x9388a5};
export function buildDirectoryScene(items,makeLabel=()=>null){
 const {nodes,groups}=layoutItems(items), scene=new THREE.Scene(); scene.background=new THREE.Color(0xe8e5dc);
 const geo={box:new THREE.BoxGeometry(1,1,1),cylinder:new THREE.CylinderGeometry(.5,.5,1,24),ring:new THREE.TorusGeometry(.5,.10,8,24),sphere:new THREE.SphereGeometry(.5,12,8)};
 const shared=new THREE.MeshStandardMaterial({color:0xd8d3c7,roughness:.85}),dark=new THREE.MeshStandardMaterial({color:0x33453f,roughness:.75});
 const objects=new Map(),targets=[],labels=[],materials=[shared,dark],textures=[];
 function add(parent,g,mat,pos,scale,rot){const m=new THREE.Mesh(geo[g],mat);m.position.set(...pos);m.scale.set(...scale);if(rot)m.rotation.set(...rot);parent.add(m);return m;}
 for(const node of nodes){
  const group=new THREE.Group();group.position.set(...node.position);scene.add(group);
  const mat=new THREE.MeshStandardMaterial({color:COLOR[node.kind],roughness:.58});materials.push(mat);
  const pedestal=add(group,'box',shared,[0,.22,0],[2.25,.44,2.25]);
  const symbol=new THREE.Group();symbol.position.y=.45;group.add(symbol);
  if(node.kind==='space-design'){
   // Courtyard + comb corridor: an abstract PROTOTYPE mark, not the underlying scene.
   add(symbol,'ring',mat,[-.35,.18,0],[.95,.95,.95],[Math.PI/2,0,0]);
   add(symbol,'box',mat,[.36,.14,0],[.9,.16,.28]);
   for(const x of [.12,.4,.68])for(const z of [-.28,.28])add(symbol,'box',mat,[x,.35,z],[.1,.42,.32]);
  } else if(node.kind==='fusion'){
   add(symbol,'box',mat,[-.52,.65,0],[.16,1.3,.22]);add(symbol,'box',mat,[.52,.65,0],[.16,1.3,.22]);add(symbol,'box',mat,[0,1.22,0],[1.2,.16,.22]);add(symbol,'box',mat,[0,.2,.25],[1.35,.1,1.2]);
  } else if(['recipe','method'].includes(node.kind)){
   for(let i=0;i<3;i++)add(symbol,'box',mat,[i*.06,.2+i*.25,0],[1.25,.12,.95],[0,i*.15,0]);
  } else {
   // Abstract directory marks, not replicas or proxies of the original models.
   const n=parseInt(node.id,10)||0;
   if([1,3,7].includes(n)){add(symbol,'ring',mat,[0,.67,0],[1.3,1.3,1.3],[0,n===3?Math.PI/4:0,0]);if(n===1)add(symbol,'sphere',dark,[0,.67,0],[.45,.45,.45]);}
   else if(n===2){add(symbol,'box',mat,[-.32,.55,0],[.8,.12,1.15],[0,0,-.28]);add(symbol,'box',mat,[.32,.55,0],[.8,.12,1.15],[0,0,.28]);}
   else if(n===4){add(symbol,'box',mat,[-.45,.5,0],[.18,1,.6]);add(symbol,'box',mat,[.45,.5,0],[.18,1,.6]);add(symbol,'box',mat,[0,1,0],[1.2,.12,.9]);}
   else if(n===5){add(symbol,'cylinder',mat,[0,.55,0],[1.05,1.1,1.05]);add(symbol,'cylinder',dark,[0,1.12,0],[.4,.08,.4]);}
   else if(n===6){for(let i=0;i<3;i++)add(symbol,'box',mat,[-.48+i*.48,.62,0],[.52,1.2,.1],[0,(i%2?1:-1)*.45,0]);}
   else if(n===8){for(let i=0;i<4;i++)add(symbol,'box',mat,[-.54+i*.36,.62,0],[.12,1.2,.12]);for(let i=0;i<3;i++)add(symbol,'box',mat,[0,.1+i*.5,0],[1.2,.1,.12]);}
   else if(n===9){add(symbol,'box',mat,[-.25,.45,0],[.12,.85,.12],[0,0,-.2]);add(symbol,'box',mat,[.13,.85,0],[.8,.12,.12],[0,0,-.35]);add(symbol,'cylinder',mat,[.52,.7,0],[.48,.1,.48]);}
   else if(n===10){
    // SLOT: two low rails and three tall dividers; slots deliberately omitted in this index symbol.
    for(const z of [-.42,.42])add(symbol,'box',dark,[0,.24,z],[1.6,.48,.13]);
    for(const x of [-.48,0,.48])add(symbol,'box',mat,[x,.57,0],[.12,1.14,1.18]);
   }
   else add(symbol,'box',mat,[0,.55,0],[.8,1.1,.8],[0,.3,0]);
  }
  group.traverse(o=>{if(o.isMesh){o.userData.itemId=node.id;targets.push(o);}});
  const label=makeLabel(node.id,node.kind);
  if(label){label.position.set(0,1.95,0);group.add(label);label.userData.itemId=node.id;targets.push(label);labels.push(label);if(label.material){materials.push(label.material);if(label.material.map)textures.push(label.material.map);}}
  objects.set(node.id,{node,group,material:mat,pedestal});
 }
 const bounds=new THREE.Box3().setFromObject(scene); // Before floor, all display objects.
 const center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());
 add(scene,'box',new THREE.MeshStandardMaterial({color:0xe0ddd3,roughness:1}),[center.x,-.10,center.z],[size.x+4,.1,size.z+4]);
 scene.add(new THREE.HemisphereLight(0xffffff,0x718278,2.5));const light=new THREE.DirectionalLight(0xffffff,3.2);light.position.set(-5,12,8);scene.add(light);
 scene.updateMatrixWorld(true);
 function dispose(){const geometries=new Set(),mats=new Set(),maps=new Set();scene.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material]){mats.add(m);if(m.map)maps.add(m.map);}});geometries.forEach(g=>g.dispose());mats.forEach(m=>m.dispose());maps.forEach(t=>t.dispose());scene.clear();}
 return {scene,nodes,groups,objects,targets,bounds,center,size,dispose};
}
export function cameraPose(directory,aspect,id=null){
 if(!Number.isFinite(aspect)||aspect<=0)throw new Error('视窗比例无效');
 const fov=44,vertical=fov*Math.PI/180,horizontal=2*Math.atan(Math.tan(vertical/2)*aspect);
 if(id!==null){const obj=directory.objects.get(id);if(!obj)throw new Error('未知作品编号');const p=obj.group.position;const d=Math.max(5.8,2.4/Math.tan(Math.min(vertical,horizontal)/2));return{position:[p.x+d*.48,1.1+d*.8,p.z+d*.7],target:[p.x,1.1,p.z],fov,near:.1,far:Math.max(500,d*3)};}
 const radius=directory.size.length()/2+2;
 const d=radius/Math.sin(Math.min(vertical,horizontal)/2)*1.12;
 const direction=new THREE.Vector3(.18,1,.95).normalize();const target=directory.center.clone();target.y=.3;
 const position=target.clone().addScaledVector(direction,d);
 return {position:position.toArray(),target:target.toArray(),fov,near:.1,far:Math.max(500,d+radius*3)};
}
