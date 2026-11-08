// Additive continuous-ground content checks against an independently frozen source baseline.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import current,* as named from '../docs/cities/luoyang/city-data.mjs';
import {installDisplayGround,withdrawDisplayGround,displayGroundRecord,displayGroundSourceSHA,displayGroundId as id} from '../docs/cities/luoyang/ground-content.mjs';
import {describeProjectRuntime} from '../docs/cities/luoyang/gallery-content.mjs';
import {preDisplayGround as base,baselineSHA} from './pre-display-ground-baseline.mjs';
const clone=x=>structuredClone(x),hash=x=>createHash('sha256').update(x).digest('hex');
const installation=installDisplayGround(base),receipt=installation.receipt;
const read=path=>readFileSync(new URL('../docs/cities/luoyang/'+path,import.meta.url));
test('independent immutable source baseline equals pre-install runtime',()=>{assert.equal(baselineSHA,'cf9defa04c293033ba07f063f7d7721197a58461');assert.deepEqual(named.preDisplayGroundManifest,base);assert.equal(describeProjectRuntime(base).drawnNodes,86);});
test('install gives the actual exported candidate and named collections',()=>{assert.deepEqual(installation.manifest,current);for(const k of ['assets','nodes','chapters','initialCamera','overview','researchModels','provenance'])assert.equal(named[k],current[k]);});
test('86 to 87 to 86 to 87 returns full manifest exactly',()=>{const before=clone(base),rollback=withdrawDisplayGround(current,named.displayGroundReceipt);assert.deepEqual(rollback,base);assert.deepEqual(installDisplayGround(rollback),installation);assert.deepEqual(base,before);assert.deepEqual([base,current,rollback,installDisplayGround(rollback).manifest].map(m=>describeProjectRuntime(m).drawnNodes),[86,87,86,87]);});
test('all 93 old manifest nodes and 69 assets are identical, never replaced',()=>{assert.equal(base.nodes.length,93);assert.equal(base.assets.length,69);assert.deepEqual(current.nodes.slice(0,-1),base.nodes);assert.deepEqual(current.assets.slice(0,-1),base.assets);});
test('chapters, research, camera, overview and courtyard counts preserved',()=>{for(const k of ['chapters','researchModels','initialCamera','overview'])assert.deepEqual(current[k],base[k]);assert.deepEqual(current.provenance.counts,base.provenance.counts);assert.equal(current.nodes.at(-1).countAsCourtyard,false);});
test('one new URL and exactly 56416 bytes added to both budget definitions',()=>{const a=describeProjectRuntime(base),b=describeProjectRuntime(current);assert.equal(b.uniqueRuntimeURLs-a.uniqueRuntimeURLs,1);assert.equal(b.selectedDefaultGLBBytes-a.selectedDefaultGLBBytes,56416);for(const k of ['initialModelBytes','allCityModelBytes'])assert.equal(current.provenance[k]-base.provenance[k],56416);});
test('new identity is nonselectable, display-only, noncollision and no bearing',()=>{const n=current.nodes.at(-1);assert.equal(n.id,id);assert.equal(n.selectable,false);assert.equal(n.displayOnly,true);assert.equal(n.walkableCollision,false);assert.equal(n.bearingSupport,false);assert.deepEqual(n.position,[0,0,0]);assert.equal(n.tier,'C');assert.equal(n.replaces,undefined);});
test('new GLB bytes and header are the frozen v6',()=>{const b=read(displayGroundRecord.path);assert.equal(b.length,56416);assert.equal(hash(b),displayGroundRecord.sha256);assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.readUInt32LE(4),2);assert.equal(b.readUInt32LE(8),b.length);});
test('new source raw bytes, adapter and independently measured GLB agree',()=>{const b=read(receipt.source.path),s=JSON.parse(b);assert.equal(hash(b),displayGroundSourceSHA);assert.equal(receipt.source.sha256,hash(b));assert.equal(s.model.sha256,displayGroundRecord.sha256);assert.equal(s.coordinateFrame,'legacy-scene-E01');assert.equal(s.model.topHoles,0);assert.equal(s.model.componentCount,1);assert.equal(s.model.closedMesh,true);assert.equal(s.model.levelTop,.16);assert.equal(s.model.patches.length,4);});
test('only complete-base display scope is recorded; other locks and physics are not released',()=>{const s=JSON.parse(read(receipt.source.path));assert.equal(receipt.provenance.scopeAdmission,'COMPLETE_BASE_DISPLAY_ONLY');assert.equal(s.scope.otherLocksReleased,false);assert.equal(s.walkableCollision,false);assert.equal(s.bearingSupport,false);assert.equal(s.geographicRegistration,null);});
test('unrelated edits and budgets survive withdrawal without mutating input',()=>{const m=clone(current);m.nodes.push({id:'independent',asset:base.assets[0].id});m.chapters[0].note='independent';m.provenance.allCityModelBytes+=123;const before=clone(m),out=withdrawDisplayGround(m,receipt),expected=clone(base);expected.nodes.push({id:'independent',asset:base.assets[0].id});expected.chapters[0].note='independent';expected.provenance.allCityModelBytes+=123;assert.deepEqual(out,expected);assert.deepEqual(m,before);});
const badInstalls={
 duplicate:()=>current,
 nodeCollision:m=>{m.nodes.push({id,asset:m.assets[0].id});return m;},
 sourceCollision:m=>{m.provenance.sourceContracts.push(receipt.source);return m;},
 duplicateAsset:m=>{m.assets.push(clone(m.assets[0]));return m;},
 missingAsset:m=>{m.nodes[0].asset='absent';return m;},
 invalidBudget:m=>{m.provenance.initialModelBytes=NaN;return m;},
 overflow:m=>{m.provenance.allCityModelBytes=Number.MAX_SAFE_INTEGER;return m;},
 duplicatePayload:m=>{m.assets.push({...clone(receipt.asset),id:'alias'});return m;},
 researchCollision:m=>{m.researchModels.push({id:m.nodes[0].id,asset:m.assets[0].id});return m;}
};
for(const [name,mutate] of Object.entries(badInstalls))test('reject installation: '+name,()=>{const m=mutate(clone(base)),before=clone(m);assert.throws(()=>installDisplayGround(m));assert.deepEqual(m,before);});
for(const url of ['javascript:alert(1)','https://user:pass@example.invalid/','https://example.invalid/?token=x','https://example.invalid/#x'])test('reject unsafe base URL '+url.split(':')[0],()=>assert.throws(()=>installDisplayGround(base,{baseURL:url})));
test('reject unreviewed source identity',()=>assert.throws(()=>installDisplayGround(base,{sourceSHA:'c56956c303a54379857890ee3e70a0dcc3f59f99439e6dd6d7ae5b3f9c81c362'})));
const corruptions={
 ownedNode:m=>m.nodes.at(-1).position[0]++,ownedAsset:m=>m.assets.at(-1).sha256='altered',ownedSource:m=>m.provenance.sourceContracts.at(-1).sha256='altered',ownedProvenance:m=>m.provenance.cityContinuousGroundC6.cityNodes++,
 nodeDependency:m=>m.nodes.push({id:'dependent',asset:id}),researchDependency:m=>m.researchModels.push({id:'dependent',asset:id}),chapterDependency:m=>m.chapters[0].nodeIds.push(id),replacementDependency:m=>m.nodes.push({id:'dependent',asset:m.assets[0].id,replaces:[id]}),assetAlias:m=>m.assets.push({...clone(receipt.asset),id:'alias'}),sourceDependency:m=>m.provenance.sourceContracts.push({path:'other.json',dependsOn:[id]}),budgetUnderflow:m=>m.provenance.initialModelBytes=0
};
for(const [name,change] of Object.entries(corruptions))test('reject withdrawal: '+name,()=>{const m=clone(current);change(m);const before=clone(m);assert.throws(()=>withdrawDisplayGround(m,receipt));assert.deepEqual(m,before);});
for(const field of ['budget','extra','sourceSHA'])test('reject altered receipt '+field,()=>{const r=clone(receipt);r[field]='altered';assert.throws(()=>withdrawDisplayGround(current,r));});
test('new PNGs contain only image chunks',()=>{for(const file of ['cover.png','shots/roads.png','shots/well.png','shots/edge.png']){const b=readFileSync(new URL('../docs/library/models/m-luoyang-city-continuous-ground/'+file,import.meta.url));assert.equal(b.subarray(0,8).toString('hex'),'89504e470d0a1a0a');let p=8;while(p<b.length){const n=b.readUInt32BE(p),type=b.toString('ascii',p+4,p+8);assert.ok(['IHDR','IDAT','IEND'].includes(type),type);p+=n+12;}assert.equal(p,b.length);}});
test('new model card is C design without a completed-deployment claim',()=>{const c=JSON.parse(readFileSync(new URL('../docs/library/models/m-luoyang-city-continuous-ground/m-luoyang-city-continuous-ground.asset.json',import.meta.url)));assert.equal(c.status,'待审');assert.equal(c.files.length,1);assert.match(c.notes['考据与推测'],/C级/);});

test('the actual GLB is one outward closed manifold with finite normals and UVs, no external payload',()=>{
 const b=read(displayGroundRecord.path),j=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString()),o=20+b.readUInt32LE(12),bin=b.subarray(o+8);
 const acc=i=>{const a=j.accessors[i],v=j.bufferViews[a.bufferView],n={VEC3:3,VEC2:2,SCALAR:1}[a.type],off=(v.byteOffset||0)+(a.byteOffset||0);return Array.from({length:a.count},(_,k)=>Array.from({length:n},(_,h)=>a.componentType===5126?bin.readFloatLE(off+(k*n+h)*4):bin.readUInt32LE(off+(k*n+h)*4)));};
 assert.ok(j.buffers.every(x=>!x.uri));assert.equal((j.images||[]).length,0);
 const p=acc(0),normal=acc(1),uv=acc(2),indices=acc(3).flat();assert.equal(indices.length/3,512);assert.equal(p.length,normal.length);assert.equal(p.length,uv.length);
 assert.ok([...p.flat(),...normal.flat(),...uv.flat()].every(Number.isFinite));for(const n of normal)assert.ok(Math.abs(Math.hypot(...n)-1)<1e-5);
 const vertices=new Map(),faces=[],edges=new Map();const vi=p.map(v=>{const k=v.join(',');if(!vertices.has(k))vertices.set(k,vertices.size);return vertices.get(k);});
 for(let i=0;i<indices.length;i+=3){const f=indices.slice(i,i+3).map(k=>vi[k]);assert.equal(new Set(f).size,3);faces.push(f);for(let k=0;k<3;k++){const a=f[k],c=f[(k+1)%3],key=[Math.min(a,c),Math.max(a,c)].join(',');if(!edges.has(key))edges.set(key,[]);edges.get(key).push([a,c]);}}
 for(const e of edges.values()){assert.equal(e.length,2);assert.deepEqual(e[0],[e[1][1],e[1][0]]);}
 assert.equal(vertices.size-edges.size+faces.length,2);
 const seen=new Set([0]);let change=true;while(change){change=false;for(const f of faces)if(f.some(v=>seen.has(v)))for(const v of f)if(!seen.has(v)){seen.add(v);change=true;}}assert.equal(seen.size,vertices.size);
 const height=(x,z)=>{const ys=[];for(let i=0;i<indices.length;i+=3){const [a,c,d]=indices.slice(i,i+3).map(k=>p[k]);const den=(c[2]-d[2])*(a[0]-d[0])+(d[0]-c[0])*(a[2]-d[2]);if(Math.abs(den)<1e-12)continue;const u=((c[2]-d[2])*(x-d[0])+(d[0]-c[0])*(z-d[2]))/den,v=((d[2]-a[2])*(x-d[0])+(a[0]-d[0])*(z-d[2]))/den;if(u>=-1e-7&&v>=-1e-7&&u+v<=1+1e-7)ys.push(u*a[1]+v*c[1]+(1-u-v)*d[1]);}return Math.max(...ys);};
 for(const [x,z,y] of [[393.312937,-2182.276204,.16],[296.987295,-1961.850627,.16],[278,-2000,-.001],[800,-1050,-.45],[800.44,-1050,-.45],[800.5,-1050,.16]])assert.ok(Math.abs(height(x,z)-y)<1e-6,JSON.stringify({x,z,want:y,got:height(x,z)}));
});

test('the full exported manifest binds all 23 source contracts to raw bytes',()=>{
 const rows=current.provenance.sourceContracts;assert.equal(rows.length,23);assert.equal(new Set(rows.map(r=>r.path)).size,23);
 for(const row of rows)assert.equal(hash(read(row.path)),row.sha256,row.path);
 let count=0;function walk(x){if(Array.isArray(x)){x.forEach(walk);return;}if(!x||typeof x!=='object')return;if(Object.hasOwn(x,'sourceContract')){assert.equal(rows.filter(r=>r.path===x.sourceContract).length,1);count++;}Object.values(x).forEach(walk);}walk(current);assert.equal(count,162);
});
