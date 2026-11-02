/* Pure state transitions. A successful initial HTML image is a fact, not an assumption. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.OrisonGallery=api;})(typeof window!=='undefined'?window:this,function(){
'use strict';
function initial(){return{serial:0,committed:null,pending:null,error:null,initialSettled:false};}
function reduce(state,event){
 const s={...state};
 if(event.type==='request'){s.serial+=1;s.pending={id:s.serial,key:event.key};s.error=null;return s;}
 if(event.type==='initial-ok'){
  if(s.initialSettled)return s;s.initialSettled=true;
  if(!s.committed)s.committed=event.key;
  return s;
 }
 if(event.type==='initial-error'){
  if(s.initialSettled)return s;s.initialSettled=true;
  if(!s.committed&&!s.pending&&!s.error)s.error=event.key;
  return s;
 }
 if(!s.pending||s.pending.id!==event.id)return s;
 if(event.type==='resolve'){s.committed=s.pending.key;s.pending=null;s.error=null;}
 if(event.type==='reject'){s.error=s.pending.key;s.pending=null;}
 return s;
}
function controller({initialKey,load,render,commit}){
 let state=initial();
 function send(e){state=reduce(state,e);render({...state});}
 async function request(key){send({type:'request',key});const id=state.serial;
  try{const image=await load(key);if(state.pending&&state.pending.id===id){commit(key,image);send({type:'resolve',id});}}
  catch(error){send({type:'reject',id});}
 }
 return{request,initialOK:()=>send({type:'initial-ok',key:initialKey}),initialError:()=>send({type:'initial-error',key:initialKey}),snapshot:()=>({...state})};
}
return{initial,reduce,controller};});
