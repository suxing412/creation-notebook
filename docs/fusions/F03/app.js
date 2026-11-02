import {resolveRoute,sampleCamera,project,validateConfig} from './navigation.mjs';
const $=s=>document.querySelector(s);
const links=[...document.querySelectorAll('[data-route]')],spots=[...document.querySelectorAll('[data-hotspot]')];
const poster=$('#poster'),status=$('#scene-status'),enable=$('#enable'),stage=$('#stage'),canvas=$('#canvas'),motion=$('#reduce-motion');
const media=matchMedia('(prefers-reduced-motion: reduce)');
let cfg,current='overview',gl=null,flight=0,routeEpoch=0,liveEpoch=0,loading=false,mode='poster',liveAbort=null;
const route=id=>cfg.routes.find(r=>r.id===id),say=s=>status.textContent=s;
function mark(){
 for(const a of [...links,...spots]){const active=(a.dataset.route||a.dataset.hotspot)===current;active?a.setAttribute('aria-current','location'):a.removeAttribute('aria-current');}
 $('#scene-number').textContent=route(current).index;$('#scene-label').textContent=route(current).short;
}
function hotspots(cameraRoute){
 const padding=Math.max(40/stage.clientWidth,.06);
 for(const a of spots){const p=project(route(a.dataset.hotspot).hotspot,cameraRoute,cfg.fov,cfg.aspect);a.hidden=!p.visible||p.x<padding||p.x>1-padding;a.style.left=p.x*100+'%';a.style.top=p.y*100+'%';}
}
function describe(){say((mode==='live'?'实时空间 · ':'Blender CPU 离线视图 · ')+route(current).short+'。'+(mode==='live'?'实时 GPU 画质、闪烁与手机性能未验。':'离线画面不代表实时 GPU 验收。'));}
function disposeScene(scene){scene?.traverse(o=>{o.geometry?.dispose();if(o.material)for(const m of[].concat(o.material)){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});}
function dispose(){cancelAnimationFrame(flight);if(gl){gl.resize.disconnect();gl.renderer.domElement.remove();disposeScene(gl.scene);gl.renderer.dispose();gl=null;}canvas.classList.remove('live');}
function exitLive(message,retry=false){
 // Renderer cancellation never invalidates a pending native chapter image.
 liveEpoch++;liveAbort?.abort();liveAbort=null;dispose();loading=false;mode='poster';
 enable.disabled=false;enable.textContent=retry?'重试实时 3D':'启用实时 3D';enable.dataset.active='false';
 $('.image-credit').textContent='BLENDER / CYCLES CPU';$('#scene-instruction').textContent='点选编号，或用目录进入相应章节。';
 hotspots(route(current));message?say(message+'；离线图、目录与全文仍可阅读。'):describe();
}
const fail=message=>exitLive(message,true);
function move(r){
 if(!gl){hotspots(r);return;}
 cancelAnimationFrame(flight);const instance=gl,from={position:instance.camera.position.toArray(),target:instance.target},start=performance.now(),duration=motion.checked?0:cfg.motionMilliseconds;
 function tick(now){if(gl!==instance)return;const t=duration?Math.min((now-start)/duration,1):1,v=sampleCamera(from,r,t);instance.camera.position.fromArray(v.position);instance.camera.lookAt(...v.target);instance.target=v.target;hotspots(v);try{instance.renderer.render(instance.scene,instance.camera);}catch{fail('实时渲染中断');return;}if(t<1)flight=requestAnimationFrame(tick);}
 flight=requestAnimationFrame(tick);
}
async function applyHash(){
 const remembered=history.state?.deskAtlasScene;
 const id=location.hash==='#reading'?(cfg.routes.some(r=>r.id===remembered)?remembered:current):resolveRoute(location.hash,cfg.routes);
 const r=route(id),token=++routeEpoch,next=new Image();next.src='assets/'+r.image;
 try{
  await next.decode();if(token!==routeEpoch)return;
  current=id;history.replaceState({...history.state,deskAtlasScene:current},'');mark();move(r);
  if(location.hash==='#reading')$('#reading').focus({preventScroll:true});else if(location.hash==='#'+current)document.getElementById(current).focus({preventScroll:true});
  poster.src=next.src;poster.alt=r.short+'：同一场景、同一相机的真实 Blender CPU 离线视图。';describe();
 }catch{if(token!==routeEpoch)return;say('本章节离线图未能载入；空间仍停留在上一章，正文已通过原生锚点定位。可刷新重试。');}
}
async function startLive(){
 const token=++liveEpoch,abort=new AbortController();liveAbort=abort;loading=true;
 enable.textContent='取消 3D 载入';say('正在载入实时空间；可取消，离线阅读不受影响。');
 let renderer,scene,resize,committed=false;
 const fresh=()=>{if(token!==liveEpoch||abort.signal.aborted)throw new DOMException('Cancelled','AbortError');};
 try{
  const THREE=await import('three'),{GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');fresh();
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'low-power'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.95;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.setClearColor(0xc5bdad);
  scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xf7f1e5,0x7f715e,1.6));
  for(const l of cfg.lights){const light=new THREE.DirectionalLight(new THREE.Color(...l.color),l.realtimeIntensity);light.position.fromArray(l.position);light.target.position.fromArray(l.target);if(l.id==='window'){light.castShadow=true;light.shadow.mapSize.set(2048,2048);Object.assign(light.shadow.camera,{left:-1.3,right:1.3,top:1.3,bottom:-1.3,near:.1,far:6});light.shadow.normalBias=.002;light.shadow.bias=-.0001;}scene.add(light,light.target);}
  const loader=new GLTFLoader(),targets=[];
  async function asset(file){const response=await fetch('assets/'+file,{signal:abort.signal});if(!response.ok)throw Error('Model response');const bytes=await response.arrayBuffer();fresh();const parsed=await loader.parseAsync(bytes,'');if(token!==liveEpoch||abort.signal.aborted){disposeScene(parsed.scene);fresh();}return parsed;}
  for(const m of cfg.models){const parsed=await asset(m.file);fresh();const root=parsed.scene;root.position.fromArray(m.position);root.rotation.y=m.rotationY;root.scale.setScalar(m.scale);root.userData.route=m.route;root.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;o.userData.route=m.route;targets.push(o);}});scene.add(root);}
  const desk=await asset(cfg.support.file);fresh();desk.scene.traverse(o=>{if(o.isMesh){o.receiveShadow=true;o.castShadow=true;}});scene.add(desk.scene);
  const g=cfg.ground,ground=new THREE.Mesh(new THREE.BoxGeometry(...g.dimensions),new THREE.MeshStandardMaterial({color:new THREE.Color(...g.color),roughness:g.roughness}));ground.position.fromArray(g.position);ground.receiveShadow=true;scene.add(ground);
  const camera=new THREE.PerspectiveCamera(cfg.fov,cfg.aspect,cfg.near,cfg.far),r=route(current);camera.position.fromArray(r.position);camera.lookAt(...r.target);
  resize=new ResizeObserver(()=>{if(gl?.renderer!==renderer)return;try{renderer.setSize(stage.clientWidth,stage.clientHeight,false);camera.aspect=cfg.aspect;camera.updateProjectionMatrix();renderer.render(scene,camera);}catch{fail('实时窗口绘制中断');}});
  fresh();renderer.setSize(stage.clientWidth,stage.clientHeight,false);renderer.render(scene,camera);fresh();
  gl={THREE,renderer,scene,camera,resize,target:r.target};committed=true;canvas.append(renderer.domElement);canvas.classList.add('live');resize.observe(stage);
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();if(gl?.renderer===renderer)fail('WebGL 上下文丢失');},{once:true});
  const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();
  function hit(event){const box=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-box.left)/box.width*2-1,-(event.clientY-box.top)/box.height*2+1);ray.setFromCamera(pointer,camera);return ray.intersectObjects(targets,false)[0];}
  renderer.domElement.addEventListener('click',event=>{if(gl?.renderer!==renderer)return;const found=hit(event);if(found){const id=found.object.userData.route;location.hash=id;if(current===id)applyHash();}});
  renderer.domElement.addEventListener('pointermove',event=>{if(gl?.renderer===renderer)renderer.domElement.style.cursor=hit(event)?'pointer':'default';});
  loading=false;mode='live';enable.textContent='回到离线图';enable.dataset.active='true';$('.image-credit').textContent='THREE.JS / LIVE · GPU 未验';$('#scene-instruction').textContent='点选物品或编号，靠近相应章节。';move(route(current));describe();
 }catch(error){
  if(!committed){resize?.disconnect();disposeScene(scene);renderer?.dispose();}
  if(token===liveEpoch)fail('实时空间不可用（图形支持或资源加载失败）');
 }
}
try{
 const response=await fetch('./assets/scene.json');if(!response.ok)throw Error('Scene config');cfg=validateConfig(await response.json());
 for(const a of [...links,...spots])if(!cfg.routes.some(r=>r.id===(a.dataset.route||a.dataset.hotspot)))throw Error('DOM routes');
 enable.hidden=false;$('#motion-control').hidden=false;motion.checked=media.matches;
 media.addEventListener('change',e=>{motion.checked=e.matches;if(gl)move(route(current));});motion.addEventListener('change',()=>{if(gl)move(route(current));});
 window.addEventListener('hashchange',applyHash);
 window.addEventListener('popstate',()=>{if(location.hash!=='#reading'&&resolveRoute(location.hash,cfg.routes)!==current)applyHash();});
 links.concat(spots).forEach(a=>a.addEventListener('click',()=>{if(location.hash===a.getAttribute('href'))applyHash();}));
 await applyHash();new ResizeObserver(()=>hotspots(gl?{position:gl.camera.position.toArray(),target:gl.target}:route(current))).observe(stage);
 enable.addEventListener('click',()=>{if(loading){exitLive('已取消 3D 载入');return;}if(gl){exitLive('已切回离线图');return;}startLive();});
}catch(error){enable.hidden=true;$('#motion-control').hidden=true;say('空间配置未能载入；已保留全景离线图与完整静态章节。原生目录仍然可用。');}
