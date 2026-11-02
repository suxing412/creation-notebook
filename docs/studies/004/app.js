import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const $=s=>document.querySelector(s),poster=$('#poster'),canvas=$('#scene'),stage=$('.stage');
let renderer,controls,ready=false,live=false;
fetch('assets/model-info.json').then(r=>r.json()).then(i=>$('#tri').innerHTML=`${i.triangles.toLocaleString()} <small>三角面</small>`).catch(()=>{});
const scene=new THREE.Scene();scene.background=new THREE.Color(0xb3c0b9);
const camera=new THREE.PerspectiveCamera(34,1,.08,100);
function reset(){camera.position.set(11,10,15);controls.target.set(0,2,-.3);controls.update();}
function staticMode(){live=false;document.querySelectorAll('[data-live]').forEach(b=>b.disabled=true);if(controls)controls.autoRotate=false;$('#rotate').setAttribute('aria-pressed','false');$('#status').textContent=ready?'当前为 Blender 离线图；可切换视角或另选实时模型。':'当前为 Blender 离线图；实时模式尚未启用或不可用。';}
window.limenStatic=staticMode;
function fail(message){ready=false;staticMode();canvas.hidden=true;poster.hidden=false;$('#live').disabled=true;$('#status').textContent=message;$('#badge').textContent='BLENDER · 预渲染';}
try{
 renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,1.8));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.1;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 const pmrem=new THREE.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;pmrem.dispose();
 scene.add(new THREE.HemisphereLight(0xe4f3ff,0x4f594e,2));const sun=new THREE.DirectionalLight(0xffefcf,3);sun.position.set(-6,10,6);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-9,right:9,top:9,bottom:-9,near:.5,far:35});sun.shadow.normalBias=.025;scene.add(sun);const ground=new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:0x879b94,roughness:.85}));ground.rotation.x=-Math.PI/2;ground.position.y=-.4;ground.receiveShadow=true;scene.add(ground);
 controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.minDistance=6;controls.maxDistance=32;controls.maxPolarAngle=Math.PI*.49;controls.autoRotateSpeed=.5;reset();
 new GLTFLoader().load('assets/limen.glb',g=>{g.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});scene.add(g.scene);ready=true;$('#live').disabled=false;$('#status').textContent='模型已加载。可选择实时绕转；日光／薄暮等按钮展示 Blender 离线图。';},undefined,()=>fail('模型加载失败，仍可浏览实际 Blender 渲染图并下载源文件。'));
 const resize=()=>{const {width,height}=stage.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();};new ResizeObserver(resize).observe(stage);resize();
 renderer.setAnimationLoop(()=>{if(live&&ready){controls.update();renderer.render(scene,camera);}});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();fail('WebGL 上下文已丢失，已回到真实离线渲染图。');});
 $('#live').onclick=()=>{if(!ready)return;live=true;canvas.hidden=false;poster.hidden=true;document.querySelectorAll('[data-live]').forEach(b=>b.disabled=false);document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed','false'));$('#badge').textContent='THREE.JS · 实时模型';$('#view-caption').textContent='实时三维：使用独立实时光照，不等同于日光或薄暮离线图。';$('#status').textContent='拖拽绕转 · 双指缩放。此视图光照与离线渲染不同。';};
 $('#rotate').onclick=()=>{controls.autoRotate=matchMedia('(prefers-reduced-motion: reduce)').matches?false:!controls.autoRotate;$('#rotate').setAttribute('aria-pressed',String(controls.autoRotate));};$('#reset').onclick=reset;
}catch(error){fail('此环境无法启用 WebGL，现展示 Blender 实际渲染图；实时控制已禁用。');}

// Keyboard orbit alternative; real GPU execution remains an explicit pending test.
canvas.addEventListener('keydown',event=>{
 if(!(live&&ready)||!controls||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
 event.preventDefault();controls.autoRotate=false;document.querySelector('#rotate').setAttribute('aria-pressed','false');
 const spherical=new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target)),step=Math.PI/24;
 if(event.key==='ArrowLeft')spherical.theta-=step;if(event.key==='ArrowRight')spherical.theta+=step;
 if(event.key==='ArrowUp')spherical.phi-=step;if(event.key==='ArrowDown')spherical.phi+=step;
 spherical.phi=THREE.MathUtils.clamp(spherical.phi,Math.max(.01,controls.minPolarAngle),Math.min(Math.PI-.01,controls.maxPolarAngle));
 camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));controls.update();
});
