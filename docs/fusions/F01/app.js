import {routeFromHash,interpolate} from './state.mjs';
const poster=document.querySelector('#poster'),mode=document.querySelector('#mode'),canvas=document.querySelector('#scene');
const titles={hall:'00 / 序厅',orbit:'01 / 星轨档案',tide:'02 / 潮翼档案'};
const descriptions={hall:'展厅序厅视角：左侧星轨圣器、右侧潮翼，中央步道连接两个档案空间',orbit:'星轨档案实际相机视角：深色展台上陈列黄铜环绕玉色晶核',tide:'潮翼档案实际相机视角：暖色展台陈列连续弧面的陶瓷翼体'};
let active='hall',moveCamera=()=>{},live=false;
function select(id){active=id;poster.src=`assets/${id}.png`;poster.alt=descriptions[id];document.querySelector('#chapter-label').textContent=titles[id];document.querySelectorAll('[data-destination]').forEach(a=>{if(a.dataset.destination===id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});moveCamera(id);}
function fromURL(){const id=routeFromHash(location.hash);if(id)select(id);}
document.querySelectorAll('[data-destination]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const id=a.dataset.destination;if(location.hash!==`#${id}`)history.pushState({chapter:id},'',`#${id}`);select(id);}));
addEventListener('popstate',e=>{const id=routeFromHash(location.hash)||e.state?.chapter||(!location.hash?'hall':null);if(id)select(id)});
document.querySelectorAll('a[href="#reading"]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();history.pushState({chapter:active},'','#reading');document.querySelector('#reading').scrollIntoView({behavior:reduced.matches?'instant':'smooth'});document.querySelector('#reading-title').focus({preventScroll:true});}));addEventListener('hashchange',fromURL);fromURL();
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
reduced.addEventListener('change',()=>{moveCamera(active);document.querySelector('#motion-note').textContent=reduced.matches?'已遵循减少动态：相机直接跳转，无过渡。':'所有文字与档案始终可从下方阅读。';});
if(reduced.matches)document.querySelector('#motion-note').textContent='已遵循减少动态：相机直接跳转，无过渡。';
function fallback(reason){live=false;canvas.hidden=true;poster.hidden=false;mode.textContent=`Blender 实际渲染 · ${reason} · 静态阅读模式`;}
async function start(){try{
 const THREE=await import('three');const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
 const response=await fetch('assets/routes.json');if(!response.ok)throw Error('routes');const routes=await response.json();
 const renderer=new THREE.WebGLRenderer({canvas,antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;
 const scene=new THREE.Scene();scene.background=new THREE.Color('#293333');scene.add(new THREE.HemisphereLight(0xe3edf3,0x88745a,2.5));
 for(const p of [[-3,11,5],[9,8,1],[-8,8,-6]]){const l=new THREE.DirectionalLight(0xffedca,3);l.position.set(...p);scene.add(l);}
 const camera=new THREE.PerspectiveCamera(37.85,1,.1,100),target=new THREE.Vector3();let transition=null;
 const asset=await new GLTFLoader().loadAsync('assets/spatial-index.glb');scene.add(asset.scene);
 const hotspots=[];for(const [id,x] of [['hall',0],['orbit',-7],['tide',7]]){const hit=new THREE.Mesh(new THREE.BoxGeometry(id==='hall'?1.5:5,id==='hall'?2.5:6,id==='hall'?1:5),new THREE.MeshBasicMaterial({visible:false}));hit.position.set(x,id==='hall'?1.25:3,id==='hall'?-3.8:-2);hit.userData.chapter=id;scene.add(hit);hotspots.push(hit);}
 moveCamera=id=>{const r=routes[id];if(!live||reduced.matches){camera.position.set(...r.position);target.set(...r.target);camera.lookAt(target);transition=null;}else transition={start:performance.now(),from:camera.position.toArray(),look:target.toArray(),to:r};};
 moveCamera(active);function resize(){const b=canvas.parentElement.getBoundingClientRect();renderer.setSize(b.width,b.height,false);camera.aspect=b.width/b.height;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(canvas.parentElement);resize();
 renderer.render(scene,camera);live=true;canvas.hidden=false;poster.hidden=true;mode.textContent='Three.js 实时空间 · 选择目的地导航';
 const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();canvas.addEventListener('click',e=>{const b=canvas.getBoundingClientRect();mouse.set((e.clientX-b.left)/b.width*2-1,-(e.clientY-b.top)/b.height*2+1);ray.setFromCamera(mouse,camera);const hit=ray.intersectObjects(hotspots)[0];if(hit){const id=hit.object.userData.chapter;if(location.hash!==`#${id}`)history.pushState({chapter:id},'',`#${id}`);select(id);}});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();fallback('图形上下文已中断');});
 renderer.setAnimationLoop(()=>{if(!live)return;if(transition){const t=(performance.now()-transition.start)/1250;camera.position.fromArray(interpolate(transition.from,transition.to.position,t));target.fromArray(interpolate(transition.look,transition.to.target,t));camera.lookAt(target);if(t>=1)transition=null;}renderer.render(scene,camera);});
}catch(e){fallback('实时图形不可用');console.info('Spatial index uses offline chapter views:',e.message);}}
start();
