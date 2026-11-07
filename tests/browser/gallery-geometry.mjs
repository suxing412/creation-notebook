// Points are barycentric interiors of top triangles in the delivered public GLBs.
// Matrices are applied once; all authored camera targets are on the ground.
export const galleryPicks = [
  {nodeId:'GALLERY-LOCAL-GALLERY-EXTERNAL-FINITE-C',viewId:'qa-gallery-finite',point:[1473.9412064294143,.2,-1853.9314498193721],triangle:0},
  {nodeId:'GALLERY-LOCAL-WEST-CONNECTOR-PREFIX-C',viewId:'qa-gallery-prefix',point:[1466.1958794889986,.2,-1843.5452844070714],triangle:4},
  {nodeId:'GALLERY-LOCAL-WEST-CONNECTOR-PROTECTED-C',viewId:'qa-gallery-rear',point:[1453.408680453107,.2,-1837.9629419023202],triangle:2},
];
// Midpoint of the public rear mesh terminal edge, at the existing road joint.
export const galleryRoadJoint={point:[1441.4914285014744,.20999999325722457,-1830.342440591617],viewId:'qa-gallery-road-joint'};
export const galleryViews = [
  {id:'qa-gallery-wide',camera:{position:[1500,78,-1800],target:[1460,0,-1856]}},
  {id:galleryRoadJoint.viewId,camera:{position:[galleryRoadJoint.point[0]+5,1.2,galleryRoadJoint.point[2]+6],target:[galleryRoadJoint.point[0],0,galleryRoadJoint.point[2]]}},
  ...galleryPicks.map(p=>({id:p.viewId,camera:{position:[p.point[0]+6,2.5,p.point[2]+5],target:[p.point[0],0,p.point[2]]}})),
];
export const galleryWorldBounds={min:[1440.8915306754132,-.1499999940395355,-1881.7542896248003],max:[1478.962961404478,8.30132884979248,-1830.331174826675]};
export const galleryRuntimeBudget={newUniqueBytes:2241292,sourceTriangles:7696,twoPassTriangleDelta:15392,twoPassDrawCallLimit:22};
const norm=v=>v.map(x=>x/Math.hypot(...v)),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export function project(point,view,rect) {
  const forward=norm(view.target.map((v,i)=>v-view.position[i])),right=norm(cross(forward,[0,1,0])),up=cross(right,forward);
  const q=point.map((v,i)=>v-view.position[i]),depth=dot(q,forward),tan=Math.tan(38*Math.PI/360),aspect=rect.aspect??Math.floor(rect.width)/Math.floor(rect.height);
  const nx=dot(q,right)/(depth*tan*aspect),ny=dot(q,up)/(depth*tan);
  return {depth,nx,ny,x:rect.x+(nx+1)*rect.width/2,y:rect.y+(1-ny)*rect.height/2};
}
export function corners(bounds=galleryWorldBounds) {
  return [bounds.min[0],bounds.max[0]].flatMap(x=>[bounds.min[1],bounds.max[1]].flatMap(y=>[bounds.min[2],bounds.max[2]].map(z=>[x,y,z])));
}
