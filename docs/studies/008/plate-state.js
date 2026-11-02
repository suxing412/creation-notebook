/* Images, captions, numeric inputs and detail crop form one transaction. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.VeilPlate=api;})(typeof window!=='undefined'?window:this,function(){
'use strict';
const variants=['veil','horizon','fold'],views=['beauty','hole-detail','top'];
function valid(key){return !!key&&variants.includes(key.variant)&&views.includes(key.view);}
function initial(){return{serial:0,committed:null,pending:null,error:null,initialSettled:false};}
function reduce(s,e){
 if(e.type==='request'){if(!valid(e.key))return s;return{...s,serial:s.serial+1,pending:{id:s.serial+1,key:{...e.key}},error:null};}
 if(e.type==='initial-ok'){if(s.initialSettled)return s;return{...s,initialSettled:true,committed:s.committed||{...e.key}};}
 if(e.type==='initial-error'){if(s.initialSettled)return s;return{...s,initialSettled:true,error:(!s.committed&&!s.pending&&!s.error)?{...e.key}:s.error};}
 if(!s.pending||e.id!==s.pending.id)return s;
 if(e.type==='resolve')return{...s,committed:s.pending.key,pending:null,error:null};
 if(e.type==='reject')return{...s,error:s.pending.key,pending:null};
 return s;
}
function controller({load,render,commit,initialKey}){
 let state=initial();const send=e=>{state=reduce(state,e);render(state);};
 async function request(key,context={}){if(!valid(key))return false;send({type:'request',key});const id=state.serial;
  try{const payload=await load(key);if(state.pending&&state.pending.id===id){commit(key,payload,context);send({type:'resolve',id});return true;}}
  catch(error){send({type:'reject',id});}return false;
 }
 return{request,initialOK:()=>send({type:'initial-ok',key:initialKey}),initialError:()=>send({type:'initial-error',key:initialKey}),snapshot:()=>JSON.parse(JSON.stringify(state))};
}
function route(search){const params=new URLSearchParams(search),variant=params.get('variant'),view=params.get('view');return{variant:variants.includes(variant)?variant:'veil',view:views.includes(view)?view:'beauty'};}
return{valid,initial,reduce,controller,route};});
