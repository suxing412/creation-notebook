export const POSES=['default','folded','extended'];
export const OFFSETS=[0,.012,.024,.048,.08,.12];
export const taskInitial=()=>({active:null,pose:'default',slotStep:0,busy:false,error:null,poseSeen:['default'],completed:[]});
export function taskReduce(s,a){switch(a.type){
 case'ENTER':return ['hinge','slot'].includes(a.id)?{...s,active:a.id,busy:false,error:null}:s;
 case'EXIT':return{...s,active:null,busy:false,error:null};
 case'BUSY':return{...s,busy:true,error:null};
 case'ERROR':return{...s,busy:false,error:a.message};
 case'POSE':{if(!POSES.includes(a.id))return s;const seen=[...new Set([...s.poseSeen,a.id])];return{...s,pose:a.id,busy:false,error:null,poseSeen:seen,completed:seen.length>=2?[...new Set([...s.completed,'hinge'])]:s.completed};}
 case'SLOT':{if(!Number.isInteger(a.step)||a.step<0||a.step>=OFFSETS.length)return s;return{...s,slotStep:a.step,busy:false,error:null,completed:a.step===OFFSETS.length-1?[...new Set([...s.completed,'slot'])]:s.completed};}
 default:return s;
}}
