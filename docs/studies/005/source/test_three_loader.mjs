import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {GLTFLoader} from '../vendor/addons/loaders/GLTFLoader.js';
import {Box3,Vector3,REVISION} from '../vendor/three.module.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const results=[];
for(const name of ['hush','poise','reach']){const data=fs.readFileSync(path.join(root,'assets',name,'model.glb'));const gltf=await new GLTFLoader().parseAsync(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'');let count=0,triangles=0;gltf.scene.traverse(o=>{if(o.isMesh){count++;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3}});const size=new Box3().setFromObject(gltf.scene).getSize(new Vector3());const info=JSON.parse(fs.readFileSync(path.join(root,'assets',name,'model-info.json'),'utf8'));if(count!==8||triangles!==40256||Math.abs(size.y*1000-info.dimensions_mm.height)>.02)throw Error('Three parse/bounds mismatch');results.push({variant:name,meshes:count,triangles,glTF_Y_up_dimensions_m:size.toArray(),passed:true})}
const report={passed:true,three_revision:REVISION,real_GLTFLoader_parse:true,GPU_render_tested:false,WebGL_tested:false,variants:results};fs.writeFileSync(path.join(root,'review','three-loader-tests.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
