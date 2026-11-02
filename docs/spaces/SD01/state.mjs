export const initialState=()=>({mode:'loading',zone:'plaza',selected:null,panel:false,error:null,visited:[]});
export function reduce(s,a){switch(a.type){case'LIVE':return{...s,mode:'space',error:null};case'FAIL':return{...s,mode:'text',error:a.message,panel:false};case'TEXT':return{...s,mode:'text',panel:false};case'LOAD':return{...s,mode:'loading',error:null,panel:false};case'ZONE':if(!['plaza','hinge','slot'].includes(a.id))return s;return{...s,zone:a.id,selected:null,panel:false};case'SELECT':if(!['hinge','slot'].includes(a.id))return s;return{...s,zone:a.id,selected:a.id,panel:true,visited:[...new Set([...(s.visited||[]),a.id])]};case'CLOSE':return{...s,panel:false};default:return s;}}
export function constrainCamera(position,target,bounds,maxY){
 if(![...position,...target,...bounds.min,...bounds.max,maxY].every(v=>Number.isFinite(v)&&Math.abs(v)<=1e6))throw new RangeError('Camera coordinates must be finite and within ±1e6 metres');
 const t=[Math.max(bounds.min[0],Math.min(bounds.max[0],target[0])),.3,Math.max(bounds.min[2],Math.min(bounds.max[2],target[2]))];
 const d=position.map((v,i)=>v-target[i]);let r=Math.hypot(...d)||1;
 let phi=Math.acos(Math.max(-1,Math.min(1,d[1]/r)));phi=Math.max(.25,Math.min(.95,phi));const theta=Math.atan2(d[0],d[2]);
 r=Math.max(1.15,(maxY+.20-t[1])/Math.cos(phi),Math.min(24,r));
 return{target:t,position:[t[0]+r*Math.sin(phi)*Math.sin(theta),t[1]+r*Math.cos(phi),t[2]+r*Math.sin(phi)*Math.cos(theta)]};
}
export function fitCamera(position,target,bounds,fov,aspect){
 if(![...position,...target,...bounds.min,...bounds.max].every(v=>Number.isFinite(v)&&Math.abs(v)<=1e6)||![fov,aspect].every(Number.isFinite)||aspect<=0||fov<=0||fov>=170)throw new RangeError('Invalid camera input');
 const t=[target[0],.3,target[2]],delta=position.map((v,i)=>v-t[i]),len=Math.hypot(...delta);if(len<1e-9)throw new RangeError('Coincident camera and target');const d=delta.map(v=>v/len),rl=Math.hypot(d[0],d[2]);if(rl<1e-9)throw new RangeError('Camera parallel to up');const right=[d[2]/rl,0,-d[0]/rl],up=[d[1]*right[2],d[2]*right[0]-d[0]*right[2],-d[1]*right[0]];const tv=Math.tan(fov*Math.PI/360),th=tv*aspect;let distance=1.15;
 for(const x of [bounds.min[0],bounds.max[0]])for(const y of [bounds.min[1],bounds.max[1]])for(const z of [bounds.min[2],bounds.max[2]]){const p=[x-t[0],y-t[1],z-t[2]],dot=v=>p.reduce((s,q,i)=>s+q*v[i],0),depth=dot(d);distance=Math.max(distance,depth+1.16*Math.abs(dot(right))/th,depth+1.16*Math.abs(dot(up))/tv);}
 return{position:t.map((v,i)=>v+d[i]*distance),target:t};
}

// Screen-relative ground-plane translation. Camera and target move together.
export function relativePan(position,target,dx,dz,step=.15){
 if(![...position,...target,dx,dz,step].every(Number.isFinite)||step<=0)throw new RangeError('Invalid pan');
 const x=position[0]-target[0],z=position[2]-target[2],len=Math.hypot(x,z);
 if(len<1e-9)throw new RangeError('Undefined horizontal heading');
 return [(z*dx+x*dz)/len*step,0,(-x*dx+z*dz)/len*step];
}
export function nextUnseen(visited){return ['hinge','slot'].find(id=>!visited.includes(id))||'plaza';}
export function mapPoint(point,bounds){
 const w=bounds.max[0]-bounds.min[0],h=bounds.max[2]-bounds.min[2];
 if(![...point,...bounds.min,...bounds.max].every(Number.isFinite)||w<=0||h<=0)throw new RangeError('Invalid map bounds');
 return [20+(point[0]-bounds.min[0])/w*260,20+(point[2]-bounds.min[2])/h*180];
}
