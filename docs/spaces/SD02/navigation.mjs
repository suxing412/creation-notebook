// SD02: CPU-verifiable camera and navigation contract. Original artistic units.
export const WORLD={min:[-26,0,-24],max:[26,6.6,25]};
const box=(min,max)=>({min,max});
export const NODES=[
{id:'overview',label:'全场 · 俯瞰路线',target:[0,1,1],direction:[.32,.7,1],bounds:box([-25,-1,-23],[25,6.6,24]),hint:'这是主动选择的全场俯瞰。回到入口，或选择一条支路接近建筑。'},
{id:'entry',label:'抵达 · 看屋顶选路',target:[0,1,1],direction:[.32,.7,1],bounds:box([-25,-1,-23],[25,6.6,24]),hint:'高仓在左，低院在右。选一条路，观察轮廓如何变成入口。'},
{id:'fork',label:'岔口 · 两种抵达',target:[0,1,0],direction:[.12,.6,1],bounds:box([-18,0,-13],[18,6.6,12]),hint:'左路接近开放前场；右路经过门楼，再看院心。'},
{id:'granary',label:'仓前 · 从留白到侧梯',target:[-12.7,2,-3],direction:[.75,.7,1],bounds:box([-17,0,-7.5],[-8.5,6.6,3]),hint:'在固定低位看梯脚与廊下；抬升后再辨前场、侧梯与高仓的关系。'},
{id:'courtyard',label:'院门 · 从围墙到院心',target:[10,1,-4.7],direction:[.55,.7,1],bounds:box([2.5,0,-12.5],[17.5,3.6,4]),hint:'从门外看入门洞；抬升后观察内屋、院心和墙内通隙。低位仅有限转向，室内不可进入。'},
{id:'lookback',label:'回望 · 比较开放与围合',target:[0,1,-3],direction:[-.3,.85,-1],bounds:box([-18,0,-13],[18,6.6,7]),hint:'从另一侧回望：仓体是高点，院落靠屋顶团与中央留白组织。'}
];
export function node(id){const n=NODES.find(n=>n.id===id);if(!n)throw new RangeError('Unknown observation point');return n;}
function finite(v){if(!v.every(x=>Number.isFinite(x)&&Math.abs(x)<=1e5))throw new RangeError('Non-finite or out-of-range coordinates');}
export function safeViewport(w,h){finite([w,h]);return{supported:w>=260&&h>=480,width:Math.max(1,w-32),height:Math.max(1,h-2*(w<560?150:110))};}
export const LOW={entry:{position:[1.5,3.4,29],target:[0,2.6,-2]},granary:{position:[-8.2,2.4,5.2],target:[-12.2,1.65,-2]},courtyard:{position:[10,1.45,5.8],target:[10,1.1,-2]}};
export function isLow(id,raised){return !!LOW[id]&&!raised;}
export function flightPath(a,b){return [a,[a[0],Math.max(12,a[1]),a[2]],[b[0],Math.max(12,b[1]),b[2]],b];}
export function fitNode(id,w,h,raised=false){const n=node(id),safe=safeViewport(w,h);if(!safe.supported)return{supported:false};if(isLow(id,raised))return{supported:true,low:true,position:[...LOW[id].position],target:id==='entry'&&w/h<.8?[-10,2.6,-1]:[...LOW[id].target]};const target=[...n.target],d=[...n.direction];if(raised)d[1]=2.4;const len=Math.hypot(...d);d.forEach((v,i)=>d[i]=v/len);const rl=Math.hypot(d[0],d[2]),right=[d[2]/rl,0,-d[0]/rl],up=[d[1]*right[2],d[2]*right[0]-d[0]*right[2],-d[1]*right[0]]; // cross(direction,right)
 const tv=Math.tan(42*Math.PI/360)*safe.height/h,th=Math.tan(42*Math.PI/360)*(w/h)*safe.width/w;let r=12;
 for(const x of [n.bounds.min[0],n.bounds.max[0]])for(const y of [n.bounds.min[1],n.bounds.max[1]])for(const z of [n.bounds.min[2],n.bounds.max[2]]){const p=[x-target[0],y-target[1],z-target[2]],dot=v=>p.reduce((s,q,i)=>s+q*v[i],0);r=Math.max(r,dot(d)+1.08*Math.abs(dot(right))/th,dot(d)+1.08*Math.abs(dot(up))/tv);}
 r=Math.max(r,(7.5-target[1])/d[1]);return{supported:true,target,position:target.map((v,i)=>v+d[i]*r)};}
export function constrainCamera(position,target){finite([...position,...target]);const t=[Math.max(-23,Math.min(23,target[0])),Math.max(.5,Math.min(2.5,target[1])),Math.max(-21,Math.min(22,target[2]))];const d=position.map((v,i)=>v-target[i]);let r=Math.hypot(...d)||12;const phi=Math.max(.15,Math.min(1.12,Math.acos(Math.max(-1,Math.min(1,d[1]/r))))),theta=Math.atan2(d[0],d[2]);r=Math.max(12,(7.5-t[1])/Math.cos(phi),Math.min(1200,r));return{target:t,position:[t[0]+r*Math.sin(phi)*Math.sin(theta),t[1]+r*Math.cos(phi),t[2]+r*Math.sin(phi)*Math.cos(theta)]};}
export function relativePan(p,t,dx,dz){finite([...p,...t,dx,dz]);const x=p[0]-t[0],z=p[2]-t[2],l=Math.hypot(x,z)||1;return[(z*dx+x*dz)/l,0,(-x*dx+z*dz)/l];}
export const initialState=()=>({mode:'loading',at:'entry',back:[],raised:false,free:false,error:'',visited:[]});
export function reduce(s,a){switch(a.type){case'LOAD':return{...initialState()};case'LIVE':return{...s,mode:'space'};case'TEXT':case'FAIL':return{...s,mode:'text',error:a.message||'已选择静态备用。'};case'GO':if(!NODES.some(n=>n.id===a.id))return s;return{...s,at:a.id,raised:false,free:false,back:s.at===a.id?s.back:[...s.back.slice(-19),s.at],visited:[...new Set([...s.visited,a.id])]};case'BACK':return s.back.length?{...s,at:s.back.at(-1),back:s.back.slice(0,-1),raised:false,free:false}:s;case'HOME':return{...s,at:'overview',back:[],raised:false,free:false};case'RAISE':return{...s,raised:!s.raised,free:false};case'FREE':return{...s,free:true};default:return s;}}
