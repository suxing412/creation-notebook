import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

window.__umbraStarted = true;
const $ = selector => document.querySelector(selector);
const stage = $('.stage'), canvas = $('#scene'), poster = $('#model-poster');
const status = $('#load-status'), slider = $('#aperture');
let renderer, controls, root, healthy = false, motionReady = false, info;
let angle = 27.5, fitDistance = 12, animationFrame = 0;
const pivots = [], materials = new Map();
const center = new THREE.Vector3(), axis = new THREE.Vector3();
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x151918);
const camera = new THREE.PerspectiveCamera(34, 1, .05, 120);
const clay = new THREE.MeshStandardMaterial({color:0xacaea4,roughness:.65,metalness:.03});
const wire = new THREE.MeshBasicMaterial({color:0xd6b980,wireframe:true});
const states = [{key:'closed',degrees:0},{key:'mid',degrees:27.5},{key:'open',degrees:55}];
const infoPromise = fetch('./assets/model-info.json').then(response => {
  if (!response.ok) throw new Error('Model metadata unavailable');
  return response.json();
}).then(data => {
  info = data;
  if (Number.isFinite(data.triangles)) $('#model-stats').innerHTML = `${data.triangles.toLocaleString()} <small>三角面</small>`;
  else $('#model-stats').innerHTML = '独立构件 <small>可编辑网格</small>';
  return data;
}).catch(error => {
  console.warn(error);
  $('#model-stats').innerHTML = '源文件 <small>可下载检查</small>';
  return null;
});

function enableRealtime(value) {
  document.querySelectorAll('[data-realtime]').forEach(el => {el.disabled = !value;});
  slider.disabled = !value || !motionReady;
}
function nearestState(degrees) {
  return states.reduce((a,b)=> Math.abs(b.degrees-degrees)<Math.abs(a.degrees-degrees)?b:a);
}
function fallback(reason, kind) {
  healthy = false;
  if (controls) controls.autoRotate = false;
  $('#rotate').setAttribute('aria-pressed','false');
  document.body.dataset.render = 'static';
  enableRealtime(false);
  canvas.hidden = true;
  poster.hidden = false;
  const selected = nearestState(angle);
  poster.src = `./assets/state-${selected.key}.png`;
  poster.alt = `玄瞳概念光阑 ${selected.degrees}° 状态，Blender 实际离线渲染`;
  window.umbraSelectState(selected.key, selected.degrees);
  angle = selected.degrees;
  $('#render-badge').textContent = 'BLENDER · 离线图';
  $('#state-mode').textContent = '预渲染图切换';
  $('#stage-hint').textContent = '实际渲染图 · 非实时画面';
  $('#motion-note').textContent = '实时转角不可用；上方三个按钮仍可切换实际渲染图。';
  status.classList.remove('ready');
  status.textContent = reason;
  window.__umbraFailure = {kind,reason};
}
function setAngle(degrees, state) {
  if (!motionReady || !healthy) return;
  const m = info.motion;
  angle = THREE.MathUtils.clamp(degrees,m.minDegrees,m.maxDegrees);
  const delta = new THREE.Quaternion().setFromAxisAngle(axis,THREE.MathUtils.degToRad(angle-m.referenceDegrees));
  for (const {node,base} of pivots) node.quaternion.copy(base).multiply(delta);
  window.umbraSelectState(state || 'custom',angle);
  window.__umbraAngle = angle;
}
function resetCamera() {
  if (!controls) return;
  camera.position.copy(center).addScaledVector(new THREE.Vector3(4,9,7).normalize(),fitDistance);
  controls.target.copy(center);
  controls.minDistance = fitDistance*.38;
  controls.maxDistance = fitDistance*2.4;
  camera.near = Math.max(.03,fitDistance/250);
  camera.far = fitDistance*10;
  camera.updateProjectionMatrix();
  controls.update();
}
function resize(reset = false) {
  if (!renderer || !controls) return;
  const box = stage.getBoundingClientRect();
  camera.aspect = box.width / Math.max(box.height,1);
  renderer.setSize(box.width,box.height,false);
  camera.updateProjectionMatrix();
  if (root) {
    const radius = root.userData.bounds.getSize(new THREE.Vector3()).length()*.5;
    const vfov = THREE.MathUtils.degToRad(camera.fov);
    const fov = Math.min(vfov,2*Math.atan(Math.tan(vfov/2)*camera.aspect));
    fitDistance = radius/Math.sin(fov/2)*1.06;
  }
  if (reset) resetCamera();
}
function validateMotion(metadata, object) {
  const m = metadata?.motion;
  if (!m || !Array.isArray(m.pivotNames) || m.pivotNames.length!==8 || new Set(m.pivotNames).size!==8 || !Array.isArray(m.axis) || m.axis.length!==3 || !m.axis.every(Number.isFinite)) return false;
  if (![m.referenceDegrees,m.minDegrees,m.maxDegrees].every(Number.isFinite) || m.minDegrees>=m.maxDegrees) return false;
  axis.fromArray(m.axis);
  if (axis.lengthSq()<.99 || axis.lengthSq()>1.01) return false;
  axis.normalize();
  for (const name of m.pivotNames) {
    const node = object.getObjectByName(name);
    if (!node) {pivots.length=0;return false;}
    pivots.push({node,base:node.quaternion.clone()});
  }
  slider.min=m.minDegrees;slider.max=m.maxDegrees;slider.value=m.referenceDegrees;angle=m.referenceDegrees;
  return true;
}

try {
  renderer = new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  controls = new OrbitControls(camera,canvas);
  controls.enableDamping = true;controls.dampingFactor=.07;
  controls.enablePan=false;controls.autoRotate=false;controls.autoRotateSpeed=.45;
  controls.minPolarAngle=.05;controls.maxPolarAngle=Math.PI*.92;
  const pmrem = new THREE.PMREMGenerator(renderer), room = new RoomEnvironment();
  scene.environment=pmrem.fromScene(room,.055).texture;scene.environmentIntensity=.8;
  room.dispose();pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xdde5dc,0x25291e,1.4));
  const key=new THREE.DirectionalLight(0xffe4b6,4.2);key.position.set(-4,8,5);scene.add(key);
  const fill=new THREE.DirectionalLight(0x9dbac9,2.1);fill.position.set(5,5,-3);scene.add(fill);
  const rim=new THREE.DirectionalLight(0xf4c27c,1.4);rim.position.set(-3,3,-5);scene.add(rim);
  resize(true);
  const [gltf, metadata] = await Promise.all([new GLTFLoader().loadAsync('./assets/iris.glb'),infoPromise]);
  root=gltf.scene;
  let triangles=0, meshes=0;
  root.traverse(node=>{
    if(node.isLight||node.isCamera)node.visible=false;
    if(node.isMesh){
      meshes++;triangles+=(node.geometry.index?.count??node.geometry.attributes.position.count)/3;
      materials.set(node,node.material);
    }
  });
  scene.add(root);
  root.userData.bounds=new THREE.Box3().setFromObject(root);
  root.userData.bounds.getCenter(center);
  motionReady=validateMotion(metadata,root);
  resize(true);
  // Do not hide the real poster until a complete first frame has been submitted.
  renderer.render(scene,camera);
  healthy=true;canvas.hidden=false;poster.hidden=true;
  document.body.dataset.render='interactive';enableRealtime(true);
  $('#render-badge').textContent='THREE.JS · 实时模型';
  $('#stage-hint').textContent='拖动旋转 · 滚轮 / 双指缩放';
  status.classList.add('ready');
  $('#model-stats').innerHTML=`${Math.round(triangles).toLocaleString()} <small>三角面</small>`;
  if(motionReady){
    $('#state-mode').textContent='实时状态切换';
    $('#motion-note').textContent='转角为各叶片绕固定轴的概念位姿，不代表 f 值或物理孔径。';
    // Respect a preset selected while the model was loading.
    const chosen=$('[data-state][aria-pressed="true"]');
    setAngle(chosen?+chosen.dataset.degrees:27.5,chosen?.dataset.state||'mid');
  } else {
    $('#state-mode').textContent='预渲染图切换';
    $('#motion-note').textContent='运动元数据未能校验：转角已禁用；状态按钮可切换实际渲染图。';
  }
  window.__umbraReady={meshes,triangles:Math.round(triangles),revision:THREE.REVISION,motionReady};
  function frame(){
    animationFrame=requestAnimationFrame(frame);
    if(!healthy||document.hidden)return;
    try{controls.update();renderer.render(scene,camera);}catch(error){console.error(error);fallback('实时绘制中断，已切回 Blender 实际渲染。','render-error');}
  }
  frame();
} catch(error) {
  console.warn('UMBRA realtime unavailable:',error);
  fallback(renderer?'交互模型未能就绪，当前显示 Blender 实际渲染。':'当前环境未启用 WebGL 2，保留 Blender 实际渲染。',renderer?'load-or-setup':'webgl-unavailable');
}
canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();fallback('图形上下文已中断，已切回 Blender 实际渲染。','context-lost');});
new ResizeObserver(()=>resize(true)).observe(stage);
window.addEventListener('umbra-state',event=>{
  if(healthy&&motionReady)setAngle(event.detail.degrees,event.detail.state);
  else if(healthy&&!motionReady){
    angle=event.detail.degrees;
    fallback('运动元数据未能校验，改为查看所选状态的 Blender 实际渲染。','motion-metadata');
  }
});
slider.addEventListener('input',event=>setAngle(+event.target.value));
$('#surfaces').addEventListener('click',event=>{
  const b=event.target.closest('button');if(!b||b.disabled||!healthy)return;
  $('#surfaces').querySelectorAll('button').forEach(button=>{const selected=button===b;button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));});
  for(const [mesh,original] of materials)mesh.material=b.dataset.surface==='clay'?clay:b.dataset.surface==='wire'?wire:original;
});
$('#rotate').addEventListener('click',()=>{if(!controls||!healthy)return;controls.autoRotate=matchMedia('(prefers-reduced-motion: reduce)').matches?false:!controls.autoRotate;$('#rotate').setAttribute('aria-pressed',String(controls.autoRotate));});
$('#reset').addEventListener('click',()=>{if(healthy)resetCamera();});

// Keyboard orbit alternative; real GPU execution remains an explicit pending test.
canvas.addEventListener('keydown',event=>{
 if(!(healthy)||!controls||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
 event.preventDefault();controls.autoRotate=false;document.querySelector('#rotate').setAttribute('aria-pressed','false');
 const spherical=new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target)),step=Math.PI/24;
 if(event.key==='ArrowLeft')spherical.theta-=step;if(event.key==='ArrowRight')spherical.theta+=step;
 if(event.key==='ArrowUp')spherical.phi-=step;if(event.key==='ArrowDown')spherical.phi+=step;
 spherical.phi=THREE.MathUtils.clamp(spherical.phi,Math.max(.01,controls.minPolarAngle),Math.min(Math.PI-.01,controls.maxPolarAngle));
 camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));controls.update();
});
