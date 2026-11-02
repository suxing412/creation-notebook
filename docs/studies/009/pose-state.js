/* One committed key identifies a decoded image AND its matching numeric panel. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.HingePose=api;})(typeof window!=='undefined'?window:this,function(){
'use strict';
const variants=['hinge','reach','poise'],poses=['default','folded','extended'];
function valid(k){return !!k&&variants.includes(k.variant)&&poses.includes(k.pose);}
function initial(){return{serial:0,committed:null,pending:null,error:null,errorContext:null,initialSettled:false};}
function reduce(s,e){
 if(e.type==='request'){if(!valid(e.key))return s;return{...s,serial:s.serial+1,pending:{id:s.serial+1,key:{...e.key},context:{...(e.context||{})}},error:null,errorContext:null};}
 if(e.type==='initial-ok'){if(s.initialSettled)return s;return{...s,initialSettled:true,committed:s.committed||{...e.key}};}
 if(e.type==='initial-error'){if(s.initialSettled)return s;return{...s,initialSettled:true,error:(!s.committed&&!s.pending&&!s.error)?{...e.key}:s.error};}
 if(!s.pending||e.id!==s.pending.id)return s;
 if(e.type==='resolve')return{...s,committed:s.pending.key,pending:null,error:null,errorContext:null};
 if(e.type==='reject')return{...s,error:s.pending.key,errorContext:s.pending.context,pending:null};return s;
}
function controller({load,render,commit,initialKey}){
 let state=initial();const send=e=>{state=reduce(state,e);render(state);};
 async function request(key,context={}){if(!valid(key))return false;send({type:'request',key,context});const id=state.serial;
  try{const payload=await load(key);if(state.pending&&state.pending.id===id){commit(key,payload,context);send({type:'resolve',id});return true;}}
  catch(e){send({type:'reject',id});}return false;
 }
 return{request,initialOK:()=>send({type:'initial-ok',key:initialKey}),initialError:()=>send({type:'initial-error',key:initialKey}),snapshot:()=>JSON.parse(JSON.stringify(state))};
}
function route(search){const p=new URLSearchParams(search),variant=p.get('variant'),pose=p.get('pose');return{variant:variants.includes(variant)?variant:'hinge',pose:poses.includes(pose)?pose:'default'};}
function localPath(s){return typeof s==='string'&&s.length>0&&!/\s/.test(s)&&!/^[a-z][\w+.-]*:/i.test(s)&&!s.startsWith('/')&&!/[\\%?#\x00-\x1f]/.test(s)&&s.split('/').every(p=>p&&p!=='.'&&p!=='..');}
function validateData(d){
 if(!d||d.schema!=='hinge-web-1'||!d.variants)throw Error('invalid schema');
 for(const v of variants){const a=d.variants[v];if(!a||typeof a.title!=='string'||!a.title.trim()||!a.stats||!a.poses)throw Error('invalid variant');
  for(const k of ['arms','base','head'])if(typeof a.stats[k]!=='string'||!a.stats[k].trim())throw Error('invalid dimension');
  for(const p of poses){const b=a.poses[p];if(!b||typeof b.title!=='string'||typeof b.note!=='string'||!localPath(b.image)||!Array.isArray(b.angles)||b.angles.length!==3||b.angles.some(x=>typeof x!=='number'||!Number.isFinite(x)))throw Error('invalid pose');
   if(!Array.isArray(b.headCenter)||b.headCenter.length!==3||b.headCenter.some(x=>typeof x!=='number'||!Number.isFinite(x)))throw Error('invalid head center');
  }
 }return d;
}
return{variants,poses,valid,initial,reduce,controller,route,localPath,validateData};});
