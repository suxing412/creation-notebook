(function(){'use strict';
const api=window.VeilPlate;if(!api)return;
const frame=document.querySelector('[data-image-frame]'),controls=document.querySelector('[data-controls]');if(!frame||!controls)return;
const initialImage=frame.querySelector('img'),strip=document.querySelector('.strip-plate'),fallback=document.querySelector('[data-fallback]'),status=document.querySelector('[data-status]'),retry=document.querySelector('[data-retry]');
const names={veil:'透幕',horizon:'横幕',fold:'曲幕'},viewNames={beauty:'整体斜视','hole-detail':'孔缘局部',top:'俯视正交'};
let desired={variant:'veil',view:'beauty'},dataPromise;
function getData(){if(!dataPromise)dataPromise=fetch('web-assets/plate-data.json').then(r=>{if(!r.ok)throw Error('metadata HTTP '+r.status);return r.json();}).then(data=>{for(const key of ['veil','horizon','fold']){const d=data&&data.variants&&data.variants[key];if(!d||typeof d.title!=='string'||['width','height','thickness','hole_count'].some(k=>!d.stats||typeof d.stats[k]!=='string')||['beauty','hole-detail','top'].some(k=>!d.images||typeof d.images[k]!=='string'||!d.images[k]))throw Error('invalid plate data');}return data;}).catch(e=>{dataPromise=null;throw e;});return dataPromise;}
function image(url,alt){return new Promise((resolve,reject)=>{const im=new Image();im.alt=alt;im.width=960;im.height=960;im.onload=async()=>{try{if(im.decode)await im.decode();if(!im.naturalWidth)throw Error('empty image');resolve(im);}catch(e){reject(e);}};im.onerror=()=>reject(Error('image unavailable'));im.src=url;});}
async function load(key){const data=await getData(),d=data.variants[key.variant];if(!d||!d.stats)throw Error('metadata missing');
 const [main,crop]=await Promise.all([image(d.images[key.view],`${names[key.variant]} · ${viewNames[key.view]}真实CPU图`),image(d.images['hole-detail'],`${names[key.variant]}孔缘CPU近景的竖幅裁片；完整原图另有入口`)]);
 return{main,crop,data:d};
}
function render(s){
 const k=s.committed;controls.hidden=false;fallback.hidden=!!k;frame.hidden=!k;strip.setAttribute('data-unavailable',String(!k));
 document.querySelectorAll('[data-variant]').forEach(b=>b.setAttribute('aria-pressed',String(!!k&&b.dataset.variant===k.variant)));
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(!!k&&b.dataset.view===k.view)));
 retry.hidden=!s.error;controls.setAttribute('aria-busy',String(!!s.pending));
 status.textContent=s.pending?`正在读取${names[s.pending.key.variant]} · ${viewNames[s.pending.key.view]}…`:(s.error?`${names[s.error.variant]} · ${viewNames[s.error.view]}未载入。${k?'仍显示上次完整图版与数值。':'正文和下载仍可用。'}`:'');
}
function commit(key,payload,context){
 frame.replaceChildren(payload.main);const old=strip.querySelector('img');if(old)old.replaceWith(payload.crop);else strip.prepend(payload.crop);
 document.querySelector('[data-title]').textContent=payload.data.title;
 document.querySelector('[data-image-tag]').textContent=key.variant.toUpperCase();
 document.querySelector('[data-caption]').textContent=`${names[key.variant]} · ${viewNames[key.view]} / Cycles CPU`;
 document.querySelector('[data-original]').href=payload.data.images[key.view];
 document.querySelector('[data-crop-original]').href=payload.data.images['hole-detail'];
 document.querySelector('[data-viewer]').href=`viewer/index.html?variant=${encodeURIComponent(key.variant)}`;
 for(const [name,value] of Object.entries(payload.data.stats)){const el=document.querySelector(`[data-stat="${name}"]`);if(el)el.textContent=value;}
 if(context.history){const url=new URL(location.href);url.searchParams.set('variant',key.variant);url.searchParams.set('view',key.view);history.pushState({},'',url);}
}
const controller=api.controller({load,render,commit,initialKey:{variant:'veil',view:'beauty'}});
function start(key,writeHistory){desired={...key};controller.request(desired,{history:writeHistory});}
controls.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.dataset.variant)start({...desired,variant:b.dataset.variant},true);else if(b.dataset.view)start({...desired,view:b.dataset.view},true);else if(b===retry){const e=controller.snapshot().error;if(e)start(e,true);}});
window.addEventListener('popstate',()=>start(api.route(location.search),false));
// Initial HTML is a useful no-script fallback, not an assumed successful image load.
const initialPair=[initialImage,strip.querySelector('img')];let initialRemaining=initialPair.length,initialFailed=false;
for(const im of initialPair){let settled=false;const finish=ok=>{if(settled)return;settled=true;initialRemaining--;if(!ok){initialFailed=true;controller.initialError();}else if(initialRemaining===0&&!initialFailed)controller.initialOK();};
 if(!im)finish(false);else if(im.complete)finish(!!im.naturalWidth);else{im.addEventListener('load',()=>finish(true),{once:true});im.addEventListener('error',()=>finish(false),{once:true});}}
controls.hidden=false;document.documentElement.classList.add('js');
const routed=api.route(location.search);if(routed.variant!=='veil'||routed.view!=='beauty')start(routed,false);
// A separately scoped delivery map can change native-download URLs/labels without touching geometry or async state.
fetch('web-delivery.json').then(r=>{if(!r.ok)throw Error('delivery map unavailable');return r.json();}).then(d=>{for(const[key,item]of Object.entries(d.downloads||{})){if(typeof item.href!=='string'||!item.href||/^\w+:/.test(item.href)||item.href.startsWith('/')||item.href.split('/').includes('..'))continue;const a=document.querySelector(`[data-download="${key}"]`);if(a){a.href=item.href;if(typeof item.label==='string')a.textContent=item.label;}}}).catch(()=>{});
})();
