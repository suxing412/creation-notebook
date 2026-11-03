import * as T from 'three';
import {GLTFLoader} from './../../fusions/F01/vendor/addons/loaders/GLTFLoader.js';
import {disposeRoot} from './r01-assets.mjs';
import {assembleFar44} from './assemble-far44.mjs';
export function createFarLayer(ctx,getState,getSouthIds,reference){
 const box=document.createElement('fieldset');box.id='far44-layer';let enabled=false,pending=false,error=null,epoch=0,controller=null,cache=null,current=null,closed=false;const loader=new GLTFLoader();
 const exclusions=s=>['connection','district','junction','gate'].includes(s.level)?getSouthIds(s):[];
 function free(){if(current){ctx.scene?.remove(current.group);current.dispose();current=null}}
 function dropCache(c){c?.roots?.forEach(disposeRoot)}
 function sync(s){if(!enabled||ctx.noGL())return;const fresh=assembleFar44(T,cache.roots,cache.contract,cache.manifests[s.layout],{excludeIds:exclusions(s)});free();current=fresh;ctx.scene?.add(fresh.group)}
 function url(){const u=new URL(location.href);if(enabled)u.searchParams.set('far','1');else u.searchParams.delete('far');history.replaceState(history.state,'',u)}
 function draw(){box.replaceChildren();const l=document.createElement('legend');l.textContent='真实院落LOD1 · 可选按需层';const b=document.createElement('button');b.textContent=enabled?'关闭真实44院LOD1':'开启真实44院LOD1';b.onclick=()=>choose(!enabled);box.append(l,b);const p=document.createElement('p');p.setAttribute('role','status');p.textContent=pending?'正在读取6共享原型与44变换，旧状态保留。':error?'远景载入失败，原状态保留；可重试。':!enabled?'未加载；位置符号不等于真实模型。':ctx.noGL()?'无GL：仅静态CPU参照，未请求六原型；不能称真实模型已渲染。':`已组装${44-exclusions(getState()).length}远景实例；近区14按逻辑ID排除，GPU未验。`;box.append(p);const q=document.createElement('p');q.textContent='LOD1保留原始源，不等于近景LOD0质量；不载原全城地形，避免与C-alt南地形重叠。这里只是44已有院的共享实例，不是全城覆盖。';box.append(q);if(pending){const c=document.createElement('button');c.textContent='取消远景载入';c.onclick=cancel;box.append(c)}}
 function refresh(){draw();ctx.layout()}
 function cancel(){epoch++;controller?.abort();controller=null;pending=false;error=null;refresh()}
 async function choose(on){cancel();const token=epoch;controller=new AbortController();const signal=controller.signal;pending=true;refresh();let freshCache=null;
 try{if(on&&!cache){const read=async p=>{const r=await fetch(p,{signal});if(!r.ok)throw Error('far contract '+r.status);return r.json()};const [contract,calt,original]=await Promise.all(['preflight-contract','instances-calt','instances-original'].map(n=>read('./data/far44/'+n+'.json')));if(contract.sourceRows!==44||contract.assets.length!==6)throw Error('far44 contract');freshCache={contract,manifests:{calt,original},roots:new Map()};if(!ctx.noGL())for(const a of contract.assets){const r=await fetch(a.url,{signal});if(!r.ok)throw Error('prototype '+r.status);const bytes=await r.arrayBuffer();const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(hash!==a.sha256)throw Error('prototype SHA');const p=await loader.parseAsync(bytes,'');freshCache.roots.set(a.variant,p.scene);if(signal.aborted)throw new DOMException('Cancelled','AbortError')}}
 if(closed||signal.aborted||epoch!==token){dropCache(freshCache);return}if(freshCache)cache=freshCache;enabled=on;if(on)sync(getState());else free();pending=false;controller=null;url();if(getState().level==='city')reference.setCityReference?.(on?['far44-'+getState().layout+'.png','44院LOD1独立CPU参考 · 不含本页其他可选层，未验GPU']:null);refresh();
 }catch(e){dropCache(freshCache);if(token===epoch&&!closed){pending=false;error=e.name==='AbortError'?null:e.message;url();refresh()}}
 }
 draw();return{get enabled(){return enabled},sync,mount(){const target=document.getElementById('choices');if(!box.isConnected)target.append(box);draw()},restore(){if(new URLSearchParams(location.search).get('far')==='1')return choose(true)},dispose(){closed=true;epoch++;controller?.abort();free();dropCache(cache);box.remove()}};
}
