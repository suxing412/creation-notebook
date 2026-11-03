(()=>{
 const control=document.querySelector('#model-sort'),grid=document.querySelector('.cards');
 if(!control||!grid)return;
 const entries=[...grid.querySelectorAll(':scope > .card')].map((card,index)=>({card,index,name:(card.querySelector('h3')?.textContent||'').replace(/\s*↗\s*$/,'').trim()}));
 const collator=new Intl.Collator('zh-Hans-CN-u-co-pinyin',{numeric:true,sensitivity:'base'});
 control.disabled=false;
 control.addEventListener('change',()=>{
  const ordered=[...entries];
  if(control.value==='name-asc'||control.value==='name-desc'){
   const sign=control.value==='name-desc'?-1:1;
   ordered.sort((a,b)=>sign*collator.compare(a.name,b.name)||a.index-b.index);
  }
  // Move existing nodes only: filtered visibility, original links and assets remain intact.
  grid.append(...ordered.map(e=>e.card));
  const visible=entries.filter(e=>!e.card.hidden).length;
  const status=document.querySelector('#matches');
  if(status)status.textContent=visible+' 项 · '+control.selectedOptions[0].textContent;
 });
})();
