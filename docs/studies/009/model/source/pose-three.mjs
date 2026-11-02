/** 009 rigid Three.js pose reuse; canonical Blender metres mapped to glTF Y-up. */
import {Matrix4,Vector3} from '../vendor/three.module.js';
const ranges=[[55,100],[-125,-70],[-25,20]], Q=new Matrix4().set(1,0,0,0, 0,0,1,0, 0,-1,0,0, 0,0,0,1),Qi=Q.clone().invert();
export function calculatePose(config,angles){
 if(!Array.isArray(angles)||angles.length!==3||angles.some((v,i)=>typeof v!=='number'||!Number.isFinite(v)||v<ranges[i][0]||v>ranges[i][1]))throw new Error('pose_range');
 for(const [k,lo,hi] of [['lower_length',.20,.28],['upper_length',.20,.29],['base_radius',.085,.12],['head_radius',.052,.075]])if(typeof config[k]!=='number'||!Number.isFinite(config[k])||config[k]<lo||config[k]>hi)throw new Error('config_range');
 const [s,e,h]=angles.map(v=>v*Math.PI/180),u=s+e,A=[0,0,.11],B=[config.lower_length*Math.cos(s),0,.11+config.lower_length*Math.sin(s)],C=[B[0]+config.upper_length*Math.cos(u),0,B[2]+config.upper_length*Math.sin(u)],E=[C[0]+.095*Math.cos(h),-.009,C[2]+.095*Math.sin(h)],D=[E[0]+.016*Math.sin(h),E[1],E[2]-.016*Math.cos(h)],floor=D[2]-config.head_radius*Math.abs(Math.sin(h))-.012*Math.abs(Math.cos(h));
 if(floor<.04)throw new Error('coupled_head_floor_clearance');return {angles_degrees:angles.slice(),shoulder:A,elbow:B,head_pivot:C,neck_end:E,head_center:D,lower_angle:s,upper_angle:u,head_angle:h,head_floor_conservative_bound_m:floor};
}
export function applyPose(root,baseInfo,angles){
 const old=baseInfo.pose,next=calculatePose(baseInfo.config,angles);
 root.traverse(ob=>{if(!ob.isMesh)return;const name=ob.userData.name||ob.name;let pivot,theta=0;
 if(name==='Lower arm'){pivot='shoulder';theta=next.lower_angle-old.lower_angle;}
 else if(name==='Upper arm'){pivot='elbow';theta=next.upper_angle-old.upper_angle;}
 else if(['Head neck','Head housing','Diffuser'].includes(name)){pivot='head_pivot';theta=next.head_angle-old.head_angle;}
 else if(name.startsWith('Elbow '))pivot='elbow';else if(name.startsWith('Head '))pivot='head_pivot';
 const transform=new Matrix4();if(pivot){const a=old[pivot],b=next[pivot];transform.makeTranslation(...b).multiply(new Matrix4().makeRotationY(-theta)).multiply(new Matrix4().makeTranslation(...a.map(x=>-x)));}
 ob.matrix.copy(Q).multiply(transform).multiply(Qi);ob.matrixAutoUpdate=false;
 });root.updateMatrixWorld(true);return next;
}
