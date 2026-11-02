export function validateCatalog(data){
 if(!Array.isArray(data)||data.length===0||data.length>60)throw Error('目录条目数量无效');
 const ids=new Set();const kinds=new Set(['regular','fusion','space-design','recipe','method']);
 const url=s=>typeof s==='string'&&s.length>0&&!/[\\\u0000-\u0020]/.test(s)&&!s.startsWith('//')&&!s.startsWith('/')&&!s.split('/').includes('..')&&(!s.includes(':')||s.startsWith('https://'));
 for(const x of data){
  if(!x||typeof x!=='object'||typeof x.id!=='string'||! /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(x.id)||ids.has(x.id)||!kinds.has(x.kind))throw Error('目录标识无效');ids.add(x.id);
  if(!['name','description','archive'].every(k=>typeof x[k]==='string'&&x[k].length>0)||!['verified','pending'].includes(x.publication)||!url(x.path))throw Error('目录文字或状态无效');
  if(x.kind==='space-design'&&(x.countsAsAcceptedSpatialDesign!==false||x.acceptance!=='prototype-pending-realtime-and-user-review'||x.designStatus!=='新空间设计原型／待实时与用户方向验收'))throw Error('空间原型验收状态无效');
  if(!Array.isArray(x.links)||x.links.length===0||x.links.some(v=>!Array.isArray(v)||v.length!==2||typeof v[0]!=='string'||!v[0]||!url(v[1])))throw Error('目录链接无效');
 }
 return data;
}
