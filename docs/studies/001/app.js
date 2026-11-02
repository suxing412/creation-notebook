import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const canvas = document.querySelector('#scene');
const stage = document.querySelector('.stage');
const loading = document.querySelector('#loading');
const label = document.querySelector('#load-label');
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
let renderer, controls, object, fitDistance = 12, modelCenter = new THREE.Vector3(0,3,0);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(36, 1, .05, 150);
const lights = {};
const originals = new Map();
const clay = new THREE.MeshStandardMaterial({color:0xbec4ba,roughness:.62,metalness:.03});
const wire = new THREE.MeshBasicMaterial({color:0x93bfb3,wireframe:true,transparent:true,opacity:.65});
let running = !reduceMotion;
let floor;
let renderHealthy = false;
const poster = document.querySelector('#model-poster');
function interactive(enabled) {
  document.querySelectorAll('.control-group button,.control-group input,.motion-row button').forEach(el => { el.disabled = !enabled; });
  document.querySelector('#controls').classList.toggle('unavailable', !enabled);
  const adjustment=document.querySelector('.adjustment');
  adjustment.open=enabled;
  adjustment.querySelector('.adjustment-hint').textContent=enabled?'展开 / 收起':'当前不可用 · 查看说明';
}
interactive(false);
fetch('./assets/model-info.json').then(r=>r.json()).then(info=>{
  if (!object) document.querySelector('#model-stats').textContent=`模型源数据：${info.triangles.toLocaleString()} 三角面 · ${info.renderMeshes} 个网格`;
}).catch(()=>{});

function fail(message, kind='initialization') {
  renderHealthy = false;
  document.body.dataset.render = 'static';
  poster.hidden = false;
  canvas.hidden = true;
  interactive(false);
  document.querySelector('.gesture').textContent = 'BLENDER 实际渲染 · 非交互图片';
  loading.classList.remove('done'); loading.classList.add('error');
  label.textContent = '静态预览';
  loading.querySelector('small').textContent = message;
  window.__aetherFailure = {kind,message};
  if (!loading.querySelector('button')) {
    const retry = document.createElement('button'); retry.textContent = '重试交互'; retry.className = 'retry';
    retry.onclick = () => location.reload(); loading.append(retry);
  }
}

try {
  renderer = new THREE.WebGLRenderer({canvas, antialias:true,alpha:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  controls = new OrbitControls(camera,canvas);
  controls.enableDamping = true; controls.dampingFactor = .065;
  controls.autoRotate = running; controls.autoRotateSpeed = .45;
  controls.enablePan = false;
  controls.minPolarAngle = .12; controls.maxPolarAngle = Math.PI*.82;
  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const env = pmrem.fromScene(room,.045);
  scene.environment = env.texture; scene.environmentIntensity = .75;
  room.dispose(); pmrem.dispose();
  lights.hemisphere = new THREE.HemisphereLight(0xc0e5e4,0x17232a,1.2);scene.add(lights.hemisphere);
  lights.key = new THREE.DirectionalLight(0xffedc8,4.5); lights.key.position.set(5,9,5); lights.key.castShadow=true;
  lights.key.shadow.mapSize.set(1024,1024);lights.key.shadow.camera.left=-6;lights.key.shadow.camera.right=6;lights.key.shadow.camera.top=8;lights.key.shadow.camera.bottom=-5;lights.key.shadow.normalBias=.03;scene.add(lights.key);
  lights.rim = new THREE.DirectionalLight(0x75c9cc,3);lights.rim.position.set(-4,5,-4);scene.add(lights.rim);
  lights.fill = new THREE.DirectionalLight(0xd4d3bd,.8);lights.fill.position.set(-5,2,5);scene.add(lights.fill);
  floor = new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.ShadowMaterial({color:0x030b0c,opacity:.24}));
  floor.rotation.x=-Math.PI/2;floor.receiveShadow=true;floor.position.y=-.015;scene.add(floor);
  const loader = new GLTFLoader();
  loader.load('./assets/aether-reliquary.glb', gltf => {
    object=gltf.scene;
    let triangles=0, meshes=0;
    object.traverse(node=>{if(node.isLight||node.isCamera){node.visible=false;} if(node.isMesh){
      meshes++; triangles+=(node.geometry.index?.count??node.geometry.attributes.position.count)/3;
      originals.set(node,node.material);node.castShadow=true;node.receiveShadow=true;
      const mats=Array.isArray(node.material)?node.material:[node.material];
      mats.forEach(mat=>{if('envMapIntensity'in mat) mat.envMapIntensity=1;});
    }});
    scene.add(object);
    const bounds=new THREE.Box3().setFromObject(object);
    modelCenter=bounds.getCenter(new THREE.Vector3());
    object.userData.bounds=bounds;
    floor.position.y=bounds.min.y-.015;
    document.querySelector('#model-stats').textContent=`${Math.round(triangles).toLocaleString()} 三角面 · ${meshes} 个网格`;
    resize(true);
    loading.classList.add('done');
    poster.hidden = true; renderHealthy = true; interactive(true);
    document.body.dataset.render = 'interactive';
    window.__aetherReady = {meshes,triangles:Math.round(triangles),revision:THREE.REVISION};
  }, event=>{
    if(event.total>0) label.textContent=`正在读取星核 ${Math.round(event.loaded/event.total*100)}%`;
  }, error=>{console.error('GLB load failed',error);fail('交互模型加载失败，当前显示 Blender 渲染图。你仍可下载源文件。','model-load');});

  function render(){
    if (!document.hidden && renderHealthy) { controls.update();renderer.render(scene,camera); }
    requestAnimationFrame(render);
  }
  render();
  canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();fail('图形上下文已中断，当前显示 Blender 渲染图。','context-lost');});
} catch(error){console.error(error);fail(renderer ? '交互初始化失败，当前显示 Blender 渲染图。' : '当前环境未启用 WebGL 2，显示 Blender 渲染图。',renderer ? 'scene-setup':'webgl-unavailable');}

function resetCamera(){
  const direction=new THREE.Vector3(7,3.2,11).normalize();
  camera.position.copy(modelCenter).addScaledVector(direction,fitDistance);
  controls.target.copy(modelCenter);controls.minDistance=fitDistance*.28;controls.maxDistance=fitDistance*2.4;
  camera.near=.05;camera.far=Math.max(100,fitDistance*8);camera.updateProjectionMatrix();controls.update();
}
function resize(reset=false){
  if(!renderer||!controls)return;
  const rect=stage.getBoundingClientRect();camera.aspect=rect.width/rect.height;
  renderer.setSize(rect.width,rect.height,false);camera.updateProjectionMatrix();
  if(object){
    const size=object.userData.bounds.getSize(new THREE.Vector3());
    const fov=THREE.MathUtils.degToRad(camera.fov);
    fitDistance=Math.max(size.y/(2*Math.tan(fov/2)),Math.max(size.x,size.z)/(2*Math.tan(fov/2)*camera.aspect))*1.22;
  }
  if(reset||!object) resetCamera();
}
new ResizeObserver(()=>resize(true)).observe(stage);

document.querySelector('#panel-toggle').addEventListener('click',event=>{
  const open=document.querySelector('#controls').classList.toggle('open');
  event.currentTarget.setAttribute('aria-expanded',String(open));event.currentTarget.textContent=open?'收起 ×':'调节 ↗';
  if(open){
    const summary=document.querySelector('.adjustment summary');
    summary.focus({preventScroll:true});
    summary.scrollIntoView({block:'center',behavior:'instant'});
  }
});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){document.querySelector('#controls').classList.remove('open');const b=document.querySelector('#panel-toggle');b.setAttribute('aria-expanded','false');b.textContent='调节 ↗';if(document.activeElement?.closest('#controls'))b.focus();}});
function activeButton(group,button){group.querySelectorAll('button').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button));});}
document.querySelector('#lights').addEventListener('click',event=>{
 const b=event.target.closest('button');if(!b||!renderer)return;activeButton(event.currentTarget,b);
 const palette={gallery:[0xffedc8,4.5,0x75c9cc,3,.75],moon:[0xb8d7f4,2.8,0x5db3c8,4.5,.65],amber:[0xffce8d,4.6,0xe89a62,2.4,.8]}[b.dataset.light];
 lights.key.color.setHex(palette[0]);lights.key.intensity=palette[1];lights.rim.color.setHex(palette[2]);lights.rim.intensity=palette[3];scene.environmentIntensity=palette[4];
 document.body.dataset.light=b.dataset.light;
});
document.querySelector('#surfaces').addEventListener('click',event=>{
 const b=event.target.closest('button');if(!b||!object)return;activeButton(event.currentTarget,b);
 for(const [mesh,original] of originals) mesh.material=b.dataset.surface==='clay'?clay:b.dataset.surface==='wire'?wire:original;
});
document.querySelector('#exposure').addEventListener('input',event=>{if(renderer)renderer.toneMappingExposure=+event.target.value;document.querySelector('#exposure-value').value=(+event.target.value).toFixed(2);});
document.querySelector('#rotate').setAttribute('aria-pressed',String(running));
document.querySelector('#rotate').addEventListener('click',event=>{running=!running;if(controls)controls.autoRotate=running;event.currentTarget.setAttribute('aria-pressed',String(running));});
document.querySelector('#reset').addEventListener('click',()=>{if(controls)resetCamera();});

// Keyboard alternative to drag; disabled when the page is showing an offline render.
canvas.addEventListener('keydown',event=>{
  if(!renderHealthy||!controls||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
  event.preventDefault();
  running=false;controls.autoRotate=false;
  document.querySelector('#rotate').setAttribute('aria-pressed','false');
  const offset=camera.position.clone().sub(controls.target);
  const spherical=new THREE.Spherical().setFromVector3(offset);
  const step=Math.PI/24;
  if(event.key==='ArrowLeft')spherical.theta-=step;
  if(event.key==='ArrowRight')spherical.theta+=step;
  if(event.key==='ArrowUp')spherical.phi-=step;
  if(event.key==='ArrowDown')spherical.phi+=step;
  spherical.phi=THREE.MathUtils.clamp(spherical.phi,controls.minPolarAngle,controls.maxPolarAngle);
  camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));
  controls.update();
});
