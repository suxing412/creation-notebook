/** Actual app setAngle + validateMotion, Three.js math, GLB TRS/accessors.
 * No renderer, browser, GPU or visual validation is used. */
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import * as THREE from '../dist/vendor/three.core.js';
const R=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),A=path.join(R,'dist/assets'),E=path.join(R,'evidence');
const bytes=fs.readFileSync(path.join(A,'iris.glb'));
assert.equal(bytes.toString('utf8',0,4),'glTF');assert.equal(bytes.readUInt32LE(4),2);assert.equal(bytes.readUInt32LE(8),bytes.length);
let gltf,bin;
for(let off=12;off<bytes.length;){const len=bytes.readUInt32LE(off),type=bytes.readUInt32LE(off+4),payload=bytes.subarray(off+8,off+8+len);if(type===0x4e4f534a)gltf=JSON.parse(payload.toString());else if(type===0x004e4942)bin=payload;off+=8+len;}
assert(gltf&&bin);assert(!gltf.skins?.length&&!gltf.animations?.length);
const info=JSON.parse(fs.readFileSync(path.join(A,'model-info.json')));
const ref=JSON.parse(fs.readFileSync(path.join(E,'transform-reference.json')));
const rb=fs.readFileSync(path.join(E,'transform-reference.bin'));
const nodes=gltf.nodes.map(n=>{const o=new THREE.Object3D();o.name=n.name;if(n.matrix)o.matrix.fromArray(n.matrix).decompose(o.position,o.quaternion,o.scale);else{if(n.translation)o.position.fromArray(n.translation);if(n.rotation)o.quaternion.fromArray(n.rotation);if(n.scale)o.scale.fromArray(n.scale);}return o;});
gltf.nodes.forEach((n,i)=>(n.children||[]).forEach(c=>nodes[i].add(nodes[c])));
const root=new THREE.Group();gltf.scenes[gltf.scene||0].nodes.forEach(i=>root.add(nodes[i]));
const app=fs.readFileSync(path.join(R,'dist/app.js'),'utf8');
function extract(name){const start=app.indexOf(`function ${name}(`);assert(start>=0);let depth=0,end;for(let i=app.indexOf('{',start);i<app.length;i++){if(app[i]==='{')depth++;if(app[i]==='}'&&--depth===0){end=i+1;break;}}assert(end);return app.slice(start,end);}
const context={THREE,info,root,pivots:[],axis:new THREE.Vector3(),slider:{},angle:27.5,healthy:true,motionReady:true,window:{umbraSelectState(){}}};vm.createContext(context);
vm.runInContext(extract('setAngle')+'\n'+extract('validateMotion'),context);
assert(context.validateMotion(info,root));
function positions(index){const ac=gltf.accessors[index],bv=gltf.bufferViews[ac.bufferView];assert.equal(ac.componentType,5126);assert.equal(ac.type,'VEC3');assert(!ac.sparse);const base=(bv.byteOffset||0)+(ac.byteOffset||0),stride=bv.byteStride||12;return Array.from({length:ac.count},(_,i)=>[0,4,8].map(d=>bin.readFloatLE(base+i*stride+d)));}
const key=v=>v.map(c=>Math.round(c*1e5)).join(',');
let localMax=0;
const blades=ref.blades.map(blade=>{const ni=gltf.nodes.findIndex(n=>n.name===blade.name),node=nodes[ni],mesh=gltf.meshes[gltf.nodes[ni].mesh];assert(mesh);const sourceMap=new Map();blade.localVertices.forEach((v,i)=>{const k=key(v);if(!sourceMap.has(k))sourceMap.set(k,[]);sourceMap.get(k).push(i);});const verts=mesh.primitives.flatMap(p=>positions(p.attributes.POSITION));const mapping=verts.map(v=>{const candidates=sourceMap.get(key(v));assert(candidates?.length,'Missing source vertex '+blade.name+' '+v);let best=-1,d=Infinity;for(const i of candidates){const q=blade.localVertices[i],err=Math.hypot(...v.map((a,k)=>a-q[k]));if(err<d){d=err;best=i;}}localMax=Math.max(localMax,d);assert(d<2e-6);return best;});return{...blade,node,verts,mapping};});
let maxError=0,sumSq=0,compared=0;const samples=[];const v=new THREE.Vector3();
for(let si=0;si<ref.angles.length;si++){const angle=ref.angles[si];context.setAngle(angle);root.updateMatrixWorld(true);let sampleMax=0;
 for(const b of blades)for(let i=0;i<b.verts.length;i++){v.fromArray(b.verts[i]).applyMatrix4(b.node.matrixWorld);const off=((si*ref.verticesPerState+b.offsetVertices+b.mapping[i])*3)*4;const err=Math.hypot(v.x-rb.readFloatLE(off),v.y-rb.readFloatLE(off+4),v.z-rb.readFloatLE(off+8));sampleMax=Math.max(sampleMax,err);sumSq+=err*err;compared++;}
 samples.push({degrees:angle,maxWorldPositionError:sampleMax});maxError=Math.max(maxError,sampleMax);
}
// Order/regression: revisiting the same state must not accumulate rotations.
context.setAngle(0);context.setAngle(55);context.setAngle(0);const repeated=context.pivots.map(p=>p.node.quaternion.toArray());context.setAngle(0);assert.deepEqual(context.pivots.map(p=>p.node.quaternion.toArray()),repeated);
assert(maxError<1e-5,`World-space parity failed: ${maxError}`);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={method:'Extract actual setAngle and validateMotion from app.js into Node VM; parse GLB positions/TRS/hierarchy; use vendored Three.js Object3D/Quaternion/Matrix4; compare every exported blade vertex against actual Blender matrix_world references, after Blender(x,y,z)->glTF(x,z,-y).',sampleCount:samples.length,exportedBladeVerticesPerState:blades.reduce((n,b)=>n+b.verts.length,0),sourceBladeVerticesPerState:ref.verticesPerState,comparedWorldVertices:compared,maxLocalMappingError:localMax,maxWorldPositionError:maxError,rmsWorldPositionError:Math.sqrt(sumSq/compared),tolerance:1e-5,passed:true,samples,repeatedStateNoAccumulation:true,appSha256:sha(app),glbSha256:sha(bytes),metadataSha256:sha(fs.readFileSync(path.join(A,'model-info.json'))),runtimeGpuRenderingVerified:false,limitations:['Mathematical transform parity only; no renderer, browser, rasterizer, depth buffer, lighting or device-performance validation.','Parser covers the actual uncompressed position accessors and TRS scene graph in this asset; not a general glTF conformance validator.']};
fs.writeFileSync(path.join(E,'transform-parity.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({...report,samples:report.samples.filter(s=>[0,27.5,55].includes(s.degrees))},null,2));
