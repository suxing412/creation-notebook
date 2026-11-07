export const streetPoint=[310.2999998728,4.0299999237,-1998.4333324432];
export const groundPoint=[275.3333333333,0,-2012.3946533203];
export const bowlPoint=[294.0719615692894,1.2476666583369174,-1979.0095170505035];
export const edgePoint=[310,.0533333321412,-1962.1839599609375];
export function project(point,view,rect) {
 const norm=v=>v.map(n=>n/Math.hypot(...v)),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],dot=(a,b)=>a.reduce((s,n,i)=>s+n*b[i],0);
 const f=norm(view.target.map((n,i)=>n-view.position[i])),r=norm(cross(f,[0,1,0])),u=cross(r,f),q=point.map((n,i)=>n-view.position[i]);
 const depth=dot(q,f),t=Math.tan(38*Math.PI/360),nx=dot(q,r)/(depth*t*Math.floor(rect.width)/Math.floor(rect.height)),ny=dot(q,u)/(depth*t);
 return {x:rect.x+rect.width*(1+nx)/2,y:rect.y+rect.height*(1-ny)/2,nx,ny,depth};
}
