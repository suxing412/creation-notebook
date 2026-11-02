import {ObservationState} from './state.js';
import {VARIANTS,VIEWS,readRoute,routeURL,cycleView} from './routes.js';
import {deliveryFor} from './delivery-links.js';
import {cameraSpec,validateInfo} from './camera.js';
const $=id=>document.getElementById(id);
let THREE,GLTFLoader,OrbitControls,RoomEnvironment,renderer,scene,camera,controls,root,envTarget,raf,activeInfo,baseScale=.76;
let infoCache=new Map(),released=new WeakSet();
function applyLink(a,spec){a.href=spec.href;a.textContent=spec.label;if(spec.download)a.setAttribute('download',spec.download);else a.removeAttribute('download');}
function updateDelivery(id){for(const a of document.querySelectorAll('[data-current-download]')){applyLink(a,deliveryFor(id)[a.dataset.currentDownload]);a.dataset.deliveryVariant=id;}}
for(const a of document.querySelectorAll('[data-delivery-variant]'))applyLink(a,deliveryFor(a.dataset.deliveryVariant)[a.dataset.deliveryKey]);
function dispose(bundle){if(!bundle||released.has(bundle))return;released.add(bundle);bundle.object?.traverse(o=>{o.geometry?.dispose();for(const m of(Array.isArray(o.material)?o.material:[o.material])){if(!m)continue;for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}});}
function staticMode(){if(raf!==undefined)cancelAnimationFrame(raf);raf=undefined;$('live').hidden=true;$('fallback').hidden=false;$('mode-label').textContent='静态图 · Cycles CPU';for(const id of ['wireframe','rotate','reset'])$(id).disabled=true;}
function teardown(){staticMode();if(root){scene?.remove(root.object);dispose(root);root=undefined;}controls?.dispose();envTarget?.dispose();renderer?.dispose();controls=envTarget=renderer=scene=camera=activeInfo=undefined;$('live').replaceChildren();}
async function libraries(){if(THREE)return;const modules=await Promise.all([import('../vendor/three.module.js'),import('../vendor/addons/loaders/GLTFLoader.js'),import('../vendor/addons/controls/OrbitControls.js'),import('../vendor/addons/environments/RoomEnvironment.js')]);[THREE,{GLTFLoader},{OrbitControls},{RoomEnvironment}]=modules;if(THREE.REVISION!=='180')throw Error('Three.js 版本不符合固定 r180 契约');}
async function readInfo(id,signal){if(infoCache.has(id))return infoCache.get(id);const r=await fetch(`../assets/${id}/model-info.json`,{signal});if(!r.ok)throw Error('模型记录 HTTP '+r.status);const info=validateInfo(await r.json(),id);infoCache.set(id,info);return info;}
function updateDimensions(id,epoch){const apply=info=>{if(state.dead||state.route!==epoch||state.current.id!==id)return;const d=info.dimensions_mm;$('dimensions').textContent=`${d.width} × ${d.depth} × ${d.height} mm · 宽 × 深 × 高`;};if(infoCache.has(id))apply(infoCache.get(id));else readInfo(id).then(apply).catch(()=>{});}
function resize(){if(!renderer||!camera)return;const width=$('stage').clientWidth,height=$('stage').clientHeight;if(!width||!height)return;renderer.setSize(width,height);const aspect=width/height;camera.left=-baseScale*aspect/2;camera.right=baseScale*aspect/2;camera.top=baseScale/2;camera.bottom=-baseScale/2;camera.updateProjectionMatrix();}
function resetCamera(view=state.current.view){if(!camera||!activeInfo)return;const spec=cameraSpec(activeInfo,view);camera.position.fromArray(spec.position);camera.up.fromArray(spec.up);controls.target.fromArray(spec.target);baseScale=spec.scale;camera.zoom=1;camera.lookAt(controls.target);controls.update();resize();}
function animate(){if(!renderer||$('live').hidden||document.hidden)return;try{controls.update();renderer.render(scene,camera);raf=requestAnimationFrame(animate);}catch(error){state.failLive(error.message);}}
function setup(){if(renderer)return;const canvas=document.createElement('canvas');try{renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'default'});}catch(error){throw Error('当前环境没有可用的 WebGL 上下文');}renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.AgXToneMapping;renderer.toneMappingExposure=1;scene=new THREE.Scene();scene.background=new THREE.Color('#c4c7c1');camera=new THREE.OrthographicCamera(-.38,.38,.38,-.38,.001,20);controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.minZoom=.3;controls.maxZoom=10;controls.autoRotateSpeed=.5;const pmrem=new THREE.PMREMGenerator(renderer),room=new RoomEnvironment();try{envTarget=pmrem.fromScene(room,.04);scene.environment=envTarget.texture;}finally{room.dispose();pmrem.dispose();}scene.add(new THREE.HemisphereLight(0xfff6e5,0x626d68,1.6));const key=new THREE.DirectionalLight(0xfff8eb,2.6);key.position.set(-.7,1.1,1);scene.add(key);const fill=new THREE.DirectionalLight(0xf0f4ff,.7);fill.position.set(.8,.6,-.4);scene.add(fill);$('live').replaceChildren(canvas);const own=renderer;canvas.addEventListener('webglcontextlost',()=>{if(renderer===own)state.contextLost();});}
const state=new ObservationState({
 decode:async route=>{const image=new Image();image.width=960;image.height=960;image.id='fallback';image.alt=`${VARIANTS[route.id].label} · ${VIEWS[route.view]}的真实 Blender CPU 渲染`;image.src=`../assets/${route.id}/${route.view}.png`;await image.decode();if(!image.naturalWidth||!image.naturalHeight)throw Error('图片没有有效像素');return image;},
 commit:(route,image,context,epoch)=>{
  // This is one synchronous commit: decoded image, labels, selector values, delivery identity and URL.
  $('fallback').replaceWith(image);$('stage').classList.add('is-ready');$('variant-title').textContent=VARIANTS[route.id].label;$('description').textContent=VARIANTS[route.id].text;$('variant').value=route.id;$('view').value=route.view;
  $('committed-label').textContent=`${route.id.toUpperCase()} / ${VARIANTS[route.id].short}`;$('view-label').textContent=`0${Object.keys(VIEWS).indexOf(route.view)+1} / ${VIEWS[route.view]}`;updateDelivery(route.id);$('dimensions').textContent='米制原尺寸 · 精确包围尺寸见模型记录';$('activate').disabled=false;
  const url=routeURL(location.href,route);if(context.history==='push')history.pushState({variant:route.id,view:route.view},'',url);else history.replaceState({variant:route.id,view:route.view},'',url);
  updateDimensions(route.id,epoch);
 },
 parse:async(id,signal)=>{await libraries();if(signal.aborted)throw new DOMException('Aborted','AbortError');const [response,info]=await Promise.all([fetch(`../assets/${id}/model.glb`,{signal}),readInfo(id,signal)]);if(!response.ok)throw Error('GLB HTTP '+response.status);const bytes=await response.arrayBuffer();if(signal.aborted)throw new DOMException('Aborted','AbortError');const gltf=await new GLTFLoader().parseAsync(bytes,new URL(`../assets/${id}/`,location.href).href);return {object:gltf.scene,info,id};},
 show:(bundle,route)=>{try{setup();if(bundle.id!==route.id||bundle.info.variant!==route.id)throw Error('GLB 会话身份不匹配');if(root){scene.remove(root.object);dispose(root);}root=bundle;activeInfo=bundle.info;root.object.traverse(o=>{if(o.isMesh)for(const m of(Array.isArray(o.material)?o.material:[o.material]))m.wireframe=$('wireframe').checked;});scene.add(root.object);resetCamera(route.view);controls.autoRotate=$('rotate').checked;$('live').hidden=false;$('fallback').hidden=true;$('mode-label').textContent='真实 GLB · 实时光照';for(const id of ['wireframe','rotate','reset'])$(id).disabled=false;resize();renderer.render(scene,camera);if(raf!==undefined)cancelAnimationFrame(raf);raf=requestAnimationFrame(animate);}catch(error){teardown();throw error;}},
 dispose,hide:teardown,status:message=>{$('status').textContent=message;}
});
async function navigate(route,mode='push'){
 const generation=state.route+1;const okay=await state.navigate(route,{history:mode});
 if(!okay&&!state.dead&&state.route===generation){$('variant').value=state.current.id;$('view').value=state.current.view;if(state.hasCommit&&mode==='history')history.replaceState({variant:state.current.id,view:state.current.view},'',routeURL(location.href,state.current));}
 return okay;
}
for(const el of document.querySelectorAll('.enhanced-controls'))el.hidden=false;
$('variant').addEventListener('change',()=>void navigate({id:$('variant').value,view:$('view').value}));$('view').addEventListener('change',()=>void navigate({id:$('variant').value,view:$('view').value}));
$('activate').addEventListener('click',()=>void state.activate());$('offline').addEventListener('click',()=>state.cancel3d());$('reset').addEventListener('click',()=>resetCamera());
$('wireframe').addEventListener('change',event=>root?.object.traverse(o=>{if(o.isMesh)for(const m of(Array.isArray(o.material)?o.material:[o.material]))m.wireframe=event.target.checked;}));$('rotate').addEventListener('change',event=>{if(controls)controls.autoRotate=event.target.checked;});
for(const link of document.querySelectorAll('[data-route]'))link.addEventListener('click',event=>{if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();void navigate(readRoute(link.href)).then(okay=>{if(okay){$('workbench').scrollIntoView({block:'start',behavior:'auto'});$('stage').focus({preventScroll:true});}});});
$('stage').addEventListener('keydown',event=>{
 if(event.key==='Escape'){event.preventDefault();state.cancel3d();return;}
 if(!renderer||$('live').hidden){if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();void navigate({id:state.requested.id,view:cycleView(state.requested.view,event.key==='ArrowRight'?1:-1)});}return;}
 if(event.key==='Home'){event.preventDefault();resetCamera();return;}
 if(['+','=','-','_'].includes(event.key)){event.preventDefault();camera.zoom=Math.max(controls.minZoom,Math.min(controls.maxZoom,camera.zoom*(event.key==='+'||event.key==='='?1.12:1/1.12)));camera.updateProjectionMatrix();return;}
 if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();const offset=camera.position.clone().sub(controls.target),q=new THREE.Quaternion().setFromUnitVectors(camera.up,new THREE.Vector3(0,1,0));offset.applyQuaternion(q);const spherical=new THREE.Spherical().setFromVector3(offset);if(event.key==='ArrowLeft')spherical.theta-=.08;if(event.key==='ArrowRight')spherical.theta+=.08;if(event.key==='ArrowUp')spherical.phi-=.08;if(event.key==='ArrowDown')spherical.phi+=.08;spherical.makeSafe();offset.setFromSpherical(spherical).applyQuaternion(q.invert());camera.position.copy(controls.target).add(offset);controls.update();}
});
window.addEventListener('popstate',()=>void navigate(readRoute(location.href),'history'));
if(typeof ResizeObserver==='function')new ResizeObserver(resize).observe($('stage'));else window.addEventListener('resize',resize);
document.addEventListener('visibilitychange',()=>{if(raf!==undefined)cancelAnimationFrame(raf);raf=undefined;if(!document.hidden)animate();});
window.addEventListener('pagehide',()=>state.cancel3d('已回到静态图。'));window.addEventListener('pageshow',event=>{if(event.persisted)void navigate(readRoute(location.href),'history');});
const initial=$('fallback');initial.addEventListener('error',()=>{if($('fallback')===initial&&!state.hasCommit){initial.hidden=true;$('stage').classList.remove('is-ready');}});
void navigate(readRoute(location.href),'replace');
