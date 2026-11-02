(function(){'use strict';
const group=document.querySelector('[data-gallery]');if(!group||!window.OrisonGallery)return;
let visible=group.querySelector('[data-current-image]');const initialImage=visible;
const buttons=Array.from(group.querySelectorAll('[data-view]'));
const views=Object.fromEntries(buttons.map(b=>[b.dataset.view,{src:b.dataset.src,alt:b.dataset.alt,caption:b.dataset.caption,label:b.textContent.trim()}]));
const caption=group.querySelector('[data-caption]'),original=group.querySelector('[data-original]'),status=group.querySelector('[data-status]'),fallback=group.querySelector('[data-fallback]'),retry=group.querySelector('[data-retry]');
const first=group.dataset.initial;
const control=OrisonGallery.controller({initialKey:first,
 load:key=>new Promise((resolve,reject)=>{const img=new Image();img.decoding='async';img.alt=views[key].alt;img.width=960;img.height=960;img.dataset.currentImage='';img.onload=()=>img.decode().then(()=>resolve(img),reject);img.onerror=reject;img.src=views[key].src;}),
 commit:(key,img)=>{visible.replaceWith(img);visible=img;caption.textContent=views[key].caption;original.href=views[key].src;original.textContent='原图 ↗';},
 render:s=>{
  const has=Boolean(s.committed);visible.hidden=!has;fallback.hidden=has;
  buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===s.committed)));
  retry.hidden=!s.error;retry.dataset.retry=s.error||'';
  if(s.pending)status.textContent='正在加载'+views[s.pending.key].label+'；'+(has?'仍显示上一张成功图版。':'正文与轮廓比较仍可阅读。');
  else if(s.error)status.textContent=views[s.error].label+'加载失败。'+(has?'保留上一张成功图版及其图注。':'尚无可加载主图；正文与轮廓比较仍可阅读。');
  else if(has)status.textContent=views[s.committed].label+'已加载。';
  else status.textContent='主图加载中；正文可直接阅读。';
  fallback.textContent=s.error?'主图暂不可用。下方保留文字观察与独立轮廓图，亦可打开原图或重试。':'主图加载中。下方正文不依赖图版切换。';
 }
});
initialImage.addEventListener('load',()=>control.initialOK(),{once:true});
initialImage.addEventListener('error',()=>control.initialError(),{once:true});
if(initialImage.complete){if(initialImage.naturalWidth>0)control.initialOK();else control.initialError();}
buttons.forEach(b=>b.addEventListener('click',()=>control.request(b.dataset.view)));
retry.addEventListener('click',()=>{if(retry.dataset.retry)control.request(retry.dataset.retry);});
group.querySelector('[data-controls]').hidden=false;document.documentElement.classList.add('enhanced');
})();
