(function(){'use strict';const api=window.HingePose;if(!api)return;
const controls=document.querySelector('[data-controls]'),frame=document.querySelector('[data-image-frame]');if(!controls||!frame)return;
const initialImage=frame.querySelector('img'),fallback=document.querySelector('[data-fallback]'),status=document.querySelector('[data-status]'),retry=document.querySelector('[data-retry]');
const names={hinge:'折光',reach:'伸展',poise:'挺立'},poseNames={'default':'基准姿态','folded':'收拢样本','extended':'展开样本'};
let desired={variant:'hinge',pose:'default'},dataPromise,navigationNotice='';
function getData(){if(!dataPromise)dataPromise=fetch('web-assets/pose-data.json').then(r=>{if(!r.ok)throw Error('metadata HTTP '+r.status);return r.json();}).then(api.validateData).catch(e=>{dataPromise=null;throw e;});return dataPromise;}
function image(src,alt){return new Promise((resolve,reject)=>{const im=new Image();im.alt=alt;im.width=960;im.height=960;im.onload=async()=>{try{if(im.decode)await im.decode();if(!im.naturalWidth)throw Error('empty image');resolve(im);}catch(e){reject(e);}};im.onerror=()=>reject(Error('image unavailable'));im.src=src;});}
async function load(k){const data=await getData(),v=data.variants[k.variant],p=v.poses[k.pose];const im=await image(p.image,`${v.title} · ${p.title}，固定front机位的真实CPU渲染`);return{im,v,p};}
function render(s){const k=s.committed;controls.hidden=false;frame.hidden=!k;fallback.hidden=!!k;document.querySelector('[data-current-panel]').hidden=!k;
 document.querySelectorAll('[data-variant]').forEach(b=>b.setAttribute('aria-pressed',String(!!k&&b.dataset.variant===k.variant)));
 document.querySelectorAll('[data-pose]').forEach(b=>b.setAttribute('aria-pressed',String(!!k&&b.dataset.pose===k.pose)));
 controls.setAttribute('aria-busy',String(!!s.pending));retry.hidden=!s.error;
 status.textContent=s.pending?`正在读取${names[s.pending.key.variant]} · ${poseNames[s.pending.key.pose]}…`:s.error?`${names[s.error.variant]} · ${poseNames[s.error.pose]}载入失败。${k?'仍显示上次完整图与对应数值。':'无脚本图册与下载仍可使用。'}`:navigationNotice;
}
function text(selector,s){document.querySelector(selector).textContent=s;}
function commit(k,{im,v,p},context){frame.replaceChildren(im);text('[data-title]',v.title);text('[data-pose-title]',p.title);text('[data-caption]',`${v.title} · ${p.title} / front同机位等幅裁片 / Cycles CPU`);text('[data-note]',p.note);text('[data-plate-tag]',k.variant.toUpperCase());document.querySelector('[data-original]').href=p.image;
 for(const name of ['arms','base','head'])text(`[data-stat="${name}"]`,v.stats[name]);
 p.angles.forEach((n,i)=>text(`[data-angle="${i}"]`,`${n}°`));text('[data-center]',`${(p.headCenter[0]*1000).toFixed(1)} / ${(p.headCenter[2]*1000).toFixed(1)} mm`);
 if(context.history){const u=new URL(location.href);u.searchParams.set('variant',k.variant);u.searchParams.set('pose',k.pose);try{history.pushState({},'',u);navigationNotice='';}catch(e){navigationNotice='画面和数值已更新，但浏览器未保存这一项导航历史。';}}
}
const controller=api.controller({load,render,commit,initialKey:desired});
function start(k,write){const s=controller.snapshot();if(write&&!s.pending&&!s.error&&s.committed&&s.committed.variant===k.variant&&s.committed.pose===k.pose)return;desired={...k};navigationNotice='';controller.request(k,{history:write});}
controls.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.dataset.variant)start({...desired,variant:b.dataset.variant},true);else if(b.dataset.pose)start({...desired,pose:b.dataset.pose},true);else if(b===retry){const s=controller.snapshot();if(s.error)start(s.error,!!(s.errorContext&&s.errorContext.history));}});
window.addEventListener('popstate',()=>start(api.route(location.search),false));
if(initialImage){if(initialImage.complete){if(initialImage.naturalWidth)controller.initialOK();else controller.initialError();}else{initialImage.addEventListener('load',()=>controller.initialOK(),{once:true});initialImage.addEventListener('error',()=>controller.initialError(),{once:true});}}else controller.initialError();
controls.hidden=false;document.documentElement.classList.add('js');const routed=api.route(location.search);if(routed.variant!=='hinge'||routed.pose!=='default')start(routed,false);
fetch('web-delivery.json').then(r=>{if(!r.ok)throw Error('delivery map');return r.json();}).then(d=>{for(const[k,v]of Object.entries(d.downloads||{})){if(!v||!api.localPath(v.href))continue;const a=document.querySelector(`[data-download="${k}"]`);if(a){a.href=v.href;if(typeof v.label==='string')a.textContent=v.label;}}}).catch(()=>{});
})();
