/** One coordinate conversion: Blender Z-up metres -> glTF Y-up metres. */
export function toGLTF([x,y,z]){return [x,z,-y];}
export function cameraSpec(info,view){
 const raw=info?.studio?.views?.[view];
 if(!raw||![...raw.location,...raw.target,raw.ortho_scale].every(Number.isFinite)||raw.ortho_scale<=0)throw Error('模型记录缺少有效的相机参数');
 const position=toGLTF(raw.location),target=toGLTF(raw.target),dx=position[0]-target[0],dy=position[1]-target[1],dz=position[2]-target[2];
 return {position,target,scale:raw.ortho_scale,up:Math.abs(dy)/Math.hypot(dx,dy,dz)>.999?[0,0,-1]:[0,1,0]};
}
export function validateInfo(info,id){
 if(info?.variant!==id||info.units!=='metres'||!info.dimensions_mm||!info.material||!info.studio?.views)throw Error('模型记录的身份或单位不匹配');
 for(const key of ['width','depth','height'])if(!Number.isFinite(info.dimensions_mm[key])||info.dimensions_mm[key]<=0)throw Error('模型尺寸记录无效');
 return info;
}
