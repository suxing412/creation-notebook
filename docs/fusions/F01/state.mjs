export const ids=['hall','orbit','tide'];
export function routeFromHash(hash){const id=hash.replace(/^#/,'');return ids.includes(id)?id:null;}
export function interpolate(a,b,t){const k=Math.max(0,Math.min(1,t));const e=k*k*(3-2*k);return a.map((v,i)=>v+(b[i]-v)*e);}
