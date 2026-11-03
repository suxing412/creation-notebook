import * as T from 'three';
import {GLTFLoader} from './../../fusions/F01/vendor/addons/loaders/GLTFLoader.js';
import {disposeRoot} from './r01-assets.mjs';
export function createWallLayer(ctx,isCity,reference){
 const box=document.createElement('fieldset');box.id='wall-layer';box.style.cssText='width:100%;border:1px solid #746b51;border-radius:6px;padding:8px';
 let selected='off',pending=null,group=null,controller=null,epoch=0,closed=false,error=null;const loader=new GLTFLoader();
 function url(){const u=new URL(location.href);if(selected==='off')u.searchParams.delete('wall');else u.searchParams.set('wall',selected);history.replaceState(history.state,'',u);}
 function free(g){if(g){ctx.scene?.remove(g);disposeRoot(g)}}
 function picture(){reference.setCityReference?.(selected==='off'?null:selected==='A'?['wall-city-direct-A.png','A全城direct转接后CPU参考 · 灰地为未建，非古代空城']:['wall-corner-B.png','B土垣墙角C样本 · 局部图，不冒称B全城图']);}
 function draw(){box.replaceChildren();const legend=document.createElement('legend');legend.textContent='全城土垣 · 独立C体量候选';box.append(legend);const select=document.createElement('select');select.setAttribute('aria-label','城垣体量样本');for(const [value,text]of [['off','仅证据骨架（不载墙体）'],['A','A：顶标高6.2 / 底宽8 / 顶宽5.6'],['B','B：顶标高8 / 底宽10 / 顶宽6.5']]){const o=document.createElement('option');o.value=value;o.textContent=text;select.append(o)}select.value=selected;select.onchange=()=>choose(select.value);box.append(select);
 const state=document.createElement('p');state.setAttribute('role','status');state.textContent=pending?'正在按需准备 '+pending+'；上次完整状态保留。':error?'墙体载入失败；原样本保留，可重试。':selected==='off'?'墙体关闭。冻结42/44院资产/21作品不变。':selected+' 为唯一选中样本；'+(ctx.noGL()?'无GL，仅静态CPU参考，未请求墙GLB。':'A为10原门间+direct两墙+门主体；B为12门间，GPU未验。');box.append(state);
 if(pending){const b=document.createElement('button');b.textContent='取消墙体载入';b.onclick=cancel;box.append(b)}if(error){const b=document.createElement('button');b.textContent='重试墙体样本';b.onclick=()=>choose(error.sample);box.append(b)}
 const p=document.createElement('p');p.textContent='高厚坡率全为C；南垣蓝灰段为推定闭合。12门B点不等于12门楼；普通32m断口不是历史门宽。A已接direct两墙/门主体C协调；B仍保留广阳120m未接合研究区。只测试A/B两样本，空白城内未建。';const detail=document.createElement('details'),summary=document.createElement('summary');summary.textContent='C参数边界 · 南垣推定 / A-direct与B未接合 / 12门不是12楼';detail.append(summary,p);box.append(detail);
 const a=document.createElement('a');a.href='data/west/city-wall-constraints.json';a.textContent='原始引用与制作边界';box.append(a);
 }
 function refresh(){draw();ctx.layout();}
 function cancel(){++epoch;controller?.abort();controller=null;pending=null;error=null;refresh();}
 async function choose(sample){if(closed||!['off','A','B'].includes(sample))return;cancel();const token=epoch;controller=new AbortController();const signal=controller.signal;pending=sample;refresh();let fresh=null;
 try{if(sample!=='off'){const r=await fetch('./data/west/city-wall-interface.json',{signal});if(!r.ok)throw Error('接口 '+r.status);const d=await r.json();const assets=d.assets.filter(a=>a.sample===sample);if(assets.length!==(d.expectedRoots?.[sample]||12)||d.courtyardCount!==44||!d.sourceBUnchanged)throw Error('墙体契约拒绝');
 if(!ctx.noGL()){fresh=new T.Group();for(const asset of assets){const r=await fetch('./assets/city-wall/'+asset.path.replace(/^assets\//,''),{signal});if(!r.ok)throw Error('GLB '+r.status);const b=await r.arrayBuffer();const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');if(hash!==asset.sha256)throw Error('墙体SHA不符');const parsed=await loader.parseAsync(b,'');fresh.add(parsed.scene);if(signal.aborted)throw new DOMException('Cancelled','AbortError');}}}
 if(closed||token!==epoch||signal.aborted){free(fresh);return;}free(group);group=fresh;if(group)ctx.scene?.add(group);selected=sample;pending=null;controller=null;error=null;url();picture();refresh();
 }catch(e){free(fresh);if(token===epoch&&!closed){pending=null;controller=null;error=e.name==='AbortError'?null:{sample,message:e.message};url();refresh();}}
 }
 draw();
 return{get selected(){return selected},restorePicture:picture,mount(){if(isCity()&&!box.isConnected)document.getElementById('choices').append(box);else if(!isCity())box.remove()},reset(){cancel();free(group);group=null;selected='off';url();picture();},restore(){const s=new URLSearchParams(location.search).get('wall');if(isCity()&&['A','B'].includes(s))return choose(s)},dispose(){closed=true;++epoch;controller?.abort();free(group);box.remove()}};
}
