import {validateCatalog} from './catalog-contract.js';
import {initCatalogFilter} from './catalog-filter-ui.js';
const entry=document.querySelector('#enter-space'), section=document.querySelector('#space'), canvas=document.querySelector('#space-canvas'), detail=document.querySelector('#selected'), status=document.querySelector('#space-status');
let api=null, loading=false, generation=0, items=null, chosen=null, renderFailed=false;
entry.hidden=false;
function say(text){status.textContent=text;}
function select(id,notify=true){
 const item=items?.find(x=>x.id===id);if(!item)return false;
 chosen=id;detail.replaceChildren();
 const title=document.createElement('h3');title.textContent=`${item.id} · ${item.name}`;detail.append(title);
 const description=document.createElement('p');description.textContent=item.description;detail.append(description);
 const state=document.createElement('p');state.textContent=`${item.archive} · ${item.publication==='verified'?'公开已核验':'公开待核验'}${item.designStatus?' · '+item.designStatus:''} · GPU/真机未验`;detail.append(state);
 const links=document.createElement('div');links.className='links';
 for(const [label,url] of item.links){const a=document.createElement('a');a.textContent=label+' ↗';a.href=url;links.append(a);}detail.append(links);
 for(const b of section.querySelectorAll('[data-select]'))b.setAttribute('aria-pressed',String(b.dataset.select===id));
 if(notify)api?.select(id,{notify:false});return true;
}
async function open(){
 if(loading||api)return;const token=++generation;loading=true;renderFailed=false;entry.disabled=true;section.hidden=false;canvas.hidden=false;document.querySelector('#reset-space').disabled=false;section.scrollIntoView({block:'start'});say('正在加载轻量空间目录；普通列表始终可用。');
 try{
  const response=await fetch('./catalog.json');
  if(!response.ok)throw Error('目录数据加载失败');const data=await response.json();
  if(token!==generation)return;
  items=validateCatalog(data);for(const b of section.querySelectorAll('[data-select]'))b.disabled=false;
  const module=await import('./spatial/spatial-directory.js');
  if(token!==generation)return;
  api=module.createSpatialDirectory({container:canvas,items,onSelect:id=>select(id,false),onStatus:s=>{if(s.state==='unavailable')renderFailed=true;if(s.state!=='disposed'||!renderFailed)say(s.message);if(s.state==='disposed'){api=null;entry.disabled=false;entry.textContent='重新开启 3D 目录索引 ↗';document.querySelector('#reset-space').disabled=true;canvas.hidden=true;}}});
  if(!chosen||!select(chosen))select(items.filter(x=>x.kind==='space-design').at(-1)?.id||items.filter(x=>x.kind==='regular').at(-1)?.id||items[0].id);
  for(const b of document.querySelectorAll('.locate'))b.hidden=false;
  say('点击展台或下方目录按钮。几何是目录符号，不是原模型；实时GPU效果尚待设备验收。');
 }catch(error){if(token!==generation)return;api?.dispose();api=null;canvas.replaceChildren();canvas.hidden=true;document.querySelector('#reset-space').disabled=true;say(items?'此处无法开启实时3D。下方目录按钮与完整列表仍可使用。':'空间目录资源加载失败。请关闭此区域，使用下方完整作品列表。');for(const b of section.querySelectorAll('[data-select]'))b.disabled=!items;if(items&&(!chosen||!select(chosen)))select(items.filter(x=>x.kind==='space-design').at(-1)?.id||items.filter(x=>x.kind==='regular').at(-1)?.id||items[0].id);entry.textContent='重试 3D 目录索引 ↗';}
 finally{if(token===generation){loading=false;entry.disabled=false;}}
}
function close(){generation++;loading=false;api?.dispose();api=null;canvas.replaceChildren();section.hidden=true;entry.disabled=false;for(const b of document.querySelectorAll('.locate'))b.hidden=true;entry.focus();}
entry.addEventListener('click',open);document.querySelector('#close-space').addEventListener('click',close);document.querySelector('#reset-space').addEventListener('click',()=>api?.reset());
for(const b of document.querySelectorAll('[data-select]'))b.addEventListener('click',()=>{select(b.dataset.select);if(b.classList.contains('locate'))section.scrollIntoView({block:'start'});});
window.addEventListener('pagehide',()=>{generation++;loading=false;api?.dispose();api=null;canvas.replaceChildren();entry.disabled=false;});
window.addEventListener('pageshow',event=>{if(event.persisted){section.hidden=true;for(const b of document.querySelectorAll('.locate'))b.hidden=true;}});

initCatalogFilter(document,window);
