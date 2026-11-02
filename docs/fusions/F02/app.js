import {resolveRoute,sampleCamera,validateConfig} from './navigation.mjs';
const links=[...document.querySelectorAll('[data-route]')],poster=document.querySelector('#poster'),status=document.querySelector('#scene-status'),button=document.querySelector('#enable');
try {
 const response=await fetch('./assets/scene.json');if(!response.ok)throw Error('Config response');const cfg=validateConfig(await response.json());if(links.length!==cfg.routes.length||links.some(a=>!cfg.routes.some(r=>r.id===a.dataset.route)))throw Error('DOM route mismatch');
 let current=cfg.routes[0].id,renderer,camera,world,animation=0,request=0;
 const route=id=>cfg.routes.find(r=>r.id===id);
 const mark=()=>links.forEach(a=>a.setAttribute('aria-current',a.dataset.route===current?'step':'false'));mark();
 async function apply(id,push=false){
  const token=++request,r=route(id);const candidate=new Image();candidate.src='assets/'+r.image;
  try{await candidate.decode();}catch(e){if(token!==request)return;status.textContent='章节图加载失败；保留「'+route(current).title+'」原图与选中状态。可重试章节，文字始终可读。';if(!push&&location.hash==='#'+id)history.replaceState(null,'','#'+current);return}
  if(token!==request)return;
  current=id;poster.src=candidate.src;poster.alt=r.title+'：同一空间中的 Blender 离线章节视图';mark();if(push&&location.hash!=='#'+id)history.pushState(null,'','#'+id);
  status.textContent=(renderer?'实时空间 · ':'Blender 离线实景 · ')+r.title+(renderer?'。GPU 视觉效果未通过云端验收。':'。离线图不代表实时验收。');
  if(camera){cancelAnimationFrame(animation);const from={position:camera.position.toArray(),target:camera.userData.target||r.target};const start=performance.now();const duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:cfg.motionMilliseconds;function tick(now){const t=duration?Math.min(1,(now-start)/duration):1;const v=sampleCamera(from,r,t);camera.position.fromArray(v.position);camera.lookAt(...v.target);camera.userData.target=v.target;renderer.render(world,camera);if(t<1)animation=requestAnimationFrame(tick)}animation=requestAnimationFrame(tick)}
 }
 links.forEach((a,i)=>{a.addEventListener('click',e=>{e.preventDefault();apply(a.dataset.route,true)});a.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const j=(i+(e.key==='ArrowRight'?1:-1)+links.length)%links.length;links[j].focus();links[j].click()})});
 window.addEventListener('hashchange',()=>apply(resolveRoute(location.hash,cfg.routes,current)));window.addEventListener('popstate',()=>apply(resolveRoute(location.hash,cfg.routes,current)));apply(resolveRoute(location.hash,cfg.routes));button.hidden=false;
 button.addEventListener('click',async()=>{button.disabled=true;button.textContent='载入空间…';let next,observer;try{
  const THREE=await import('three');const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');next=new THREE.WebGLRenderer({antialias:true,alpha:false});next.setPixelRatio(Math.min(devicePixelRatio,2));next.setClearColor(0xbfc7c5);next.outputColorSpace=THREE.SRGBColorSpace;next.toneMapping=THREE.ACESFilmicToneMapping;
  world=new THREE.Scene();world.add(new THREE.HemisphereLight(0xf5f4e6,0x536262,2));const light=new THREE.DirectionalLight(0xfff0d6,3);light.position.set(-8,12,10);world.add(light);const model=await new GLTFLoader().loadAsync('./assets/scales-scene.glb');world.add(model.scene);
  camera=new THREE.PerspectiveCamera(cfg.fov,1,cfg.near,cfg.far);renderer=next;document.querySelector('#canvas').append(next.domElement);
  const resize=()=>{const box=document.querySelector('.viewport').getBoundingClientRect();renderer.setSize(box.width,box.height,false);camera.aspect=box.width/box.height;camera.updateProjectionMatrix();renderer.render(world,camera)};observer=new ResizeObserver(resize);observer.observe(document.querySelector('.viewport'));camera.position.fromArray(route(current).position);camera.userData.target=route(current).target;apply(current);button.textContent='实时空间已启用';
 }catch(e){if(observer)observer.disconnect();if(next){next.domElement.remove();next.dispose();}renderer=null;camera=null;world=null;cancelAnimationFrame(animation);status.textContent='实时空间加载失败，可能为图形支持或资源加载问题；离线图文仍可阅读。';button.disabled=false;button.textContent='重试实时空间';}});
}catch(e){status.textContent='空间配置加载失败；已保持静态首图。章节链接仍可跳至完整文字，刷新页面可重试。';button.hidden=true;}
