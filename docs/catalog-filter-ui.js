import {matchesCatalogFilter} from './catalog-filter.js';
export function initCatalogFilter(document,window){
 const form=document.querySelector('#catalog-filter'),input=document.querySelector('#work-search'),kind=document.querySelector('#work-kind');
 const cards=[...document.querySelectorAll('article.work[data-id]')];
 function apply(){
  let count=0;
  for(const card of cards){card.hidden=!matchesCatalogFilter({kind:card.dataset.kind,search:card.dataset.search},input.value,kind.value);if(!card.hidden)count++;}
  for(const group of document.querySelectorAll('.collection')){
   const all=[...group.querySelectorAll('article.work')],visible=all.filter(c=>!c.hidden).length;group.hidden=visible===0;
   const heading=group.querySelector('.section-heading h2 span');if(heading){heading.dataset.originalCount??=heading.textContent;heading.textContent=input.value.trim()||kind.value!=='all'?`${visible} / ${all.length} 项匹配`:heading.dataset.originalCount;}
  }
  document.querySelector('#filter-status').textContent=`显示 ${count} / ${cards.length} 项${input.value.trim()?'，关键词：'+input.value.trim():''}。`;
  document.querySelector('#filter-empty').hidden=count!==0;
 }
 function reset(){input.value='';kind.value='all';apply();}
 form.addEventListener('submit',e=>e.preventDefault());form.addEventListener('input',apply);form.addEventListener('change',apply);
 form.addEventListener('reset',e=>{e.preventDefault();reset();});
 for(const a of document.querySelectorAll('a[href^="#"]'))a.addEventListener('click',()=>{if(document.getElementById(a.getAttribute('href').slice(1))?.closest('.collection'))reset();});
 window.addEventListener('hashchange',()=>{if(document.getElementById(window.location.hash.slice(1))?.closest('.collection'))reset();});
 document.querySelector('#find-works').hidden=false;apply();
}
