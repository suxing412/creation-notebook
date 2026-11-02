import * as THREE from './vendor/three.module.js';
import {buildDirectoryScene,cameraPose,validateItems,LIMITS} from './spatial-layout.js';
export {LIMITS} from './spatial-layout.js';
/** Opt-in spatial index. No original model or image is fetched. All symbols are directory marks. */
export function createSpatialDirectory({container,items,onSelect=()=>{},onStatus=()=>{}}){
 validateItems(items);
 if(!container||typeof container.appendChild!=='function')throw new Error('缺少空间目录容器');
 let renderer;
 const status=(state,message)=>onStatus({state,message});
 try {renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,powerPreference:'low-power'});}
 catch(cause){status('unavailable','此环境无法启用实时3D；普通作品目录仍可完整使用。');const error=new Error('实时3D不可用',{cause});error.code='WEBGL_UNAVAILABLE';throw error;}
 renderer.setClearColor(0xe8e5dc);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
 const canvas=renderer.domElement;canvas.setAttribute('aria-label','三维作品目录，展台是目录符号，不是原模型；使用旁侧普通列表也可选择全部作品。');canvas.setAttribute('role','img');canvas.style.cssText='display:block;width:100%;height:100%;touch-action:pan-y;';
 function label(id,kind){const c=document.createElement('canvas');c.width=256;c.height=64;const ctx=c.getContext('2d');if(!ctx)throw new Error('编号绘制不可用');ctx.fillStyle='#f2eee5';ctx.fillRect(0,0,256,64);ctx.fillStyle='#253e36';ctx.font='600 27px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(id.length>16?id.slice(0,15)+'…':id,128,32);const map=new THREE.CanvasTexture(c);map.colorSpace=THREE.SRGBColorSpace;const mat=new THREE.SpriteMaterial({map,depthTest:true,depthWrite:false});const sprite=new THREE.Sprite(mat);sprite.scale.set(1.8,.45,1);return sprite;}
 let directory;
 try{directory=buildDirectoryScene(items,label);}catch(error){renderer.dispose();throw error;}
 const camera=new THREE.PerspectiveCamera(44,1,.1,500),raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2(),target=new THREE.Vector3();
 let selected=null,disposed=false,raf=0,animation=null,aspect=1,down=null;
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 container.appendChild(canvas);
 function setPose(pose){camera.position.fromArray(pose.position);target.fromArray(pose.target);camera.fov=pose.fov;camera.near=pose.near;camera.far=pose.far;camera.lookAt(target);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);}
 function draw(now){raf=0;if(disposed||document.hidden)return;
  if(animation){const t=Math.min(1,Math.max(0,(now-animation.start)/LIMITS.animationMs));const eased=t*t*(3-2*t);camera.position.lerpVectors(animation.from,animation.to,eased);target.lerpVectors(animation.fromTarget,animation.toTarget,eased);camera.lookAt(target);camera.updateMatrixWorld(true);if(t===1)animation=null;}
  try{renderer.render(directory.scene,camera);}catch(error){status('unavailable','实时绘制失败；请使用普通作品目录。');dispose();return;}
  if(animation)raf=requestAnimationFrame(draw);
 }
 function invalidate(){if(!disposed&&!raf&&!document.hidden)raf=requestAnimationFrame(draw);}
 function moveTo(pose){camera.near=pose.near;camera.far=pose.far;camera.updateProjectionMatrix();if(reduced.matches){animation=null;setPose(pose);}else animation={from:camera.position.clone(),to:new THREE.Vector3(...pose.position),fromTarget:target.clone(),toTarget:new THREE.Vector3(...pose.target),start:performance.now()};invalidate();}
 function select(id,{notify=false}={}){if(disposed)return false;const entry=directory.objects.get(id);if(!entry)return false;
  selected=id;for(const [key,obj]of directory.objects){obj.material.emissive.setHex(key===id?0x365041:0x000000);obj.material.emissiveIntensity=key===id?.3:0;}
  moveTo(cameraPose(directory,aspect,id));if(notify)onSelect(id);return true;
 }
 function reset(){if(disposed)return;selected=null;for(const obj of directory.objects.values())obj.material.emissive.setHex(0);moveTo(cameraPose(directory,aspect));status('ready','全馆目录：左侧模型与介绍页，中间历史实验待重做，右侧复用方法。');}
 function resize(){if(disposed)return;const rect=container.getBoundingClientRect();const width=Math.max(1,Math.floor(rect.width)),height=Math.max(1,Math.floor(rect.height));aspect=width/height;camera.aspect=aspect;
  const dpr=Math.min(window.devicePixelRatio||1,LIMITS.maxPixelRatio,Math.sqrt(LIMITS.maxDrawingPixels/(width*height)));renderer.setPixelRatio(dpr);renderer.setSize(width,height,false);animation=null;setPose(cameraPose(directory,aspect,selected));invalidate();
 }
 function hit(event){const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return null;pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);camera.updateMatrixWorld(true);raycaster.setFromCamera(pointer,camera);const result=raycaster.intersectObjects(directory.targets,false);return result.length?result[0].object.userData.itemId:null;}
 const pointerDown=e=>{down={x:e.clientX,y:e.clientY};};
 const pointerUp=e=>{if(!down)return;const moved=Math.hypot(e.clientX-down.x,e.clientY-down.y);down=null;if(moved>8)return;const id=hit(e);if(id)select(id,{notify:true});};
 const pointerMove=e=>{canvas.style.cursor=hit(e)?'pointer':'default';};
 const cancelPointer=()=>{down=null;};
 const visibility=()=>{if(document.hidden&&raf){cancelAnimationFrame(raf);raf=0;}else invalidate();};
 const motionChange=()=>{if(animation&&reduced.matches){const pose=cameraPose(directory,aspect,selected);animation=null;setPose(pose);invalidate();}};
 const contextLost=e=>{e.preventDefault();status('unavailable','实时图形上下文中断；普通目录仍可使用，请重新启用3D再试。');dispose();};
 const pageHide=()=>dispose();
 canvas.addEventListener('pointerdown',pointerDown);canvas.addEventListener('pointerup',pointerUp);canvas.addEventListener('pointermove',pointerMove);canvas.addEventListener('pointercancel',cancelPointer);canvas.addEventListener('webglcontextlost',contextLost);
 document.addEventListener('visibilitychange',visibility);window.addEventListener('pagehide',pageHide);window.addEventListener('resize',resize);reduced.addEventListener('change',motionChange);
 const observer=typeof ResizeObserver==='function'?new ResizeObserver(resize):null;observer?.observe(container);
 function dispose(){if(disposed)return;disposed=true;animation=null;if(raf)cancelAnimationFrame(raf);raf=0;observer?.disconnect();canvas.removeEventListener('pointerdown',pointerDown);canvas.removeEventListener('pointerup',pointerUp);canvas.removeEventListener('pointermove',pointerMove);canvas.removeEventListener('pointercancel',cancelPointer);canvas.removeEventListener('webglcontextlost',contextLost);document.removeEventListener('visibilitychange',visibility);window.removeEventListener('pagehide',pageHide);window.removeEventListener('resize',resize);reduced.removeEventListener('change',motionChange);directory.dispose();renderer.dispose();canvas.remove();status('disposed','实时目录已释放，普通作品目录不受影响。');}
 resize();status('ready','实时空间目录已准备。展台是编号符号，未加载原模型；点击选择作品。');
 return {select,reset,resize,dispose,get selectedId(){return selected;},get disposed(){return disposed;}};
}
