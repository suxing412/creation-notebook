import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import published,* as named from '../docs/cities/luoyang/city-data.mjs';
import { installGallery,withdrawGallery,describeProjectRuntime,galleryRecords } from '../docs/cities/luoyang/gallery-content.mjs';
import { preGallery,gitFile,baselineSHA } from './pre-gallery-baseline.mjs';
import { withContractIdentityCorrections } from './contract-identity-fixture.mjs';
const base=withContractIdentityCorrections(preGallery);
const clone=x=>structuredClone(x),hash=b=>createHash('sha256').update(b).digest('hex'),installed=installGallery(base);
const ids=galleryRecords.map(r=>r.nodeId);
test('independent 78-node city installs, withdraws and reinstalls exactly',()=>{
 const original=clone(base);
 assert.deepEqual(installed.manifest,published);
 for(const k of ['assets','nodes','chapters','initialCamera','overview','researchModels','provenance'])assert.equal(named[k],published[k]);
 assert.deepEqual(describeProjectRuntime(base).drawnNodes,78);
 assert.equal(describeProjectRuntime(published).drawnNodes,86);
 assert.deepEqual([published.nodes.length,published.assets.length],[93,69]);
 assert.deepEqual(published.nodes.slice(0,85),base.nodes);
 assert.deepEqual(published.assets.slice(0,61),base.assets);
 assert.deepEqual(published.chapters.slice(0,base.chapters.length),base.chapters);
 for(const k of ['researchModels','initialCamera','overview'])assert.deepEqual(published[k],base[k]);
 assert.deepEqual(withdrawGallery(published,named.galleryReceipt),base);
 assert.deepEqual(installGallery(withdrawGallery(published,named.galleryReceipt)),installed);
 assert.deepEqual(base,original);
 assert.deepEqual(published.provenance.counts,base.provenance.counts);
 assert.ok(named.galleryReceipt.nodes.every(n=>n.initial&&n.tier==='C'&&n.zoneId==='Z23'&&n.countAsCourtyard===false&&n.replaces.length===0));
});
test('exact eight GLBs and source identity match measured runtime budget',()=>{
 let bytes=0;
 for(const r of galleryRecords){
  const path=new URL(r.path,new URL('../docs/cities/luoyang/gallery-records.mjs',import.meta.url));
  const b=readFileSync(path);assert.equal(b.length,r.bytes);assert.equal(hash(b),r.sha256);
  assert.equal(b.readUInt32LE(0),0x46546c67);assert.equal(b.readUInt32LE(4),2);assert.equal(b.readUInt32LE(8),b.length);
  const json=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)).toString());
  assert.ok((json.buffers||[]).every(v=>!v.uri));assert.ok((json.images||[]).every(v=>v.bufferView!==undefined&&!v.uri));
  const asset=published.assets.find(a=>a.id===r.id),url=new URL(asset.url);
  assert.equal(url.search,r.reusesPublishedFile?'?v='+r.sha256:'');assert.equal(asset.sourcePath,r.path);
  const n=published.nodes.find(n=>n.id===r.nodeId);assert.deepEqual(n.matrix,r.matrix);assert.deepEqual(n.bounds,r.worldBounds);bytes+=b.length;
 }
 assert.equal(bytes,2241292);assert.equal(galleryRecords.reduce((s,r)=>s+r.triangles,0),7696);
 assert.equal(galleryRecords.filter(r=>!r.reusesPublishedFile).reduce((s,r)=>s+r.bytes,0),21452);
 assert.equal(describeProjectRuntime(base).selectedDefaultGLBBytes,21260480);
 assert.equal(describeProjectRuntime(published).selectedDefaultGLBBytes,23501772);
 assert.equal(named.galleryReceipt.budget,2241292);
 const source=named.galleryReceipt.source;
 assert.equal(hash(readFileSync(new URL(source.path,new URL('../docs/cities/luoyang/city-data.mjs',import.meta.url)))),source.sha256);
});
test('original models, cards, roads, renderer, planning and deployment code stay byte-identical',()=>{
 const protectedPaths=['docs/library/models/m-luoyang-palace-gallery/','docs/library/models/m-luoyang-gallery-access/',
 'docs/cities/luoyang/assets/ground-atomic/','docs/cities/luoyang/progress-assets/yong-road-link-v2/',
 'docs/cities/luoyang/city-navigation-renderer.mjs','docs/cities/luoyang/navigation-scene.mjs',
 'docs/cities/luoyang/z13-content.mjs','docs/cities/luoyang/planning-zones.json',
 'lab/asset.html','lab/tools/assemble_site.py','lab/tools/slim_site.py'];
 const paths=execFileSync('git',['ls-tree','-r','--name-only',baselineSHA,'--',...protectedPaths],{encoding:'utf8'}).trim().split('\n');
 assert.ok(paths.length>20);
 for(const path of paths)assert.equal(hash(readFileSync(new URL('../'+path,import.meta.url))),hash(gitFile(path)),path);
});
test('withdraw refuses changed owned data, receipts and new dependencies without mutation',()=>{
 const changes=[m=>m.nodes.at(-1).matrix[12]++,m=>m.assets.at(-1).sha256='altered',m=>m.chapters.at(-1).title='altered',
 m=>m.nodes.push({id:'dependent',asset:galleryRecords[0].id}),m=>m.researchModels.push({id:'dependent',asset:galleryRecords[0].id}),
 m=>m.chapters[0].nodeIds.push(ids[0]),m=>m.chapters[0].loadNodeIds.push(ids[0]),
 m=>m.nodes.push({id:'replacer',asset:base.assets[0].id,replaces:[ids[0]]}),
 m=>m.assets.push({...clone(m.assets.at(-1)),id:'alias'}),m=>m.provenance.sourceContracts.at(-1).sha256='altered'];
 for(const change of changes){const m=clone(published);change(m);const before=clone(m);assert.throws(()=>withdrawGallery(m,named.galleryReceipt));assert.deepEqual(m,before);}
 for(const change of [r=>r.budget++,r=>r.ownedAssets=[],r=>r.nodes[0].matrix[12]++,r=>r.chapter.title='altered',r=>r.scope='six-plus-prefix',r=>r.extra=true,r=>r.reusedAssets.push(r.ownedAssets.shift())]){
  const r=clone(named.galleryReceipt);change(r);assert.throws(()=>withdrawGallery(published,r));
 }
 assert.throws(()=>installGallery(published));assert.throws(()=>installGallery(base,{scope:'invalid'}));
});
test('unrelated concurrent work survives withdrawal and separately selected seven-piece variant',()=>{
 const m=clone(published);m.nodes.push({id:'unrelated',asset:base.assets[0].id});m.chapters[0].subtitle='independent edit';
 m.provenance.allCityModelBytes+=123;m.provenance.independent={keep:true};
 const restored=withdrawGallery(m,named.galleryReceipt),expected=clone(base);
 expected.nodes.push({id:'unrelated',asset:base.assets[0].id});expected.chapters[0].subtitle='independent edit';
 expected.provenance.allCityModelBytes+=123;expected.provenance.independent={keep:true};
 assert.deepEqual(restored,expected);
 const seven=installGallery(base,{scope:'six-plus-prefix'});assert.equal(describeProjectRuntime(seven.manifest).drawnNodes,85);
 assert.equal(seven.receipt.budget,2237832);assert.deepEqual(withdrawGallery(seven.manifest,seven.receipt),base);
});
test('project records exactly one local assembly, keeps original families and honest limitations',()=>{
 const card=JSON.parse(readFileSync(new URL('../docs/cities/luoyang/p-luoyang.asset.json',import.meta.url)));
 const old=JSON.parse(gitFile('docs/cities/luoyang/p-luoyang.asset.json'));
 assert.deepEqual(card.members,old.members);assert.equal(card.chapters.filter(c=>c.id==='gallery-local-c').length,1);
 assert.equal(card.files.length,6);assert.ok(card.files.every(f=>f.path.startsWith('progress-assets/gallery-local-C-v1/')));
 assert.equal(card.progress.filter(p=>p.focus==='gallery-local-c').length,3);
 assert.ok(card.chapters.find(c=>c.id==='gallery-local-c').text.includes('C设计'));
 assert.equal(published.provenance.galleryLocalC1.automaticLOD,false);
 assert.equal(published.provenance.galleryLocalC1.wholeRouteOrPublicEntryClaim,false);
});

test('all source contracts bind exact raw bytes and every current usage',()=>{
 const rows=published.provenance.sourceContracts;
 assert.equal(rows.length,22);assert.equal(new Set(rows.map(r=>r.path)).size,22);
 for(const row of rows)assert.equal(hash(readFileSync(new URL('../docs/cities/luoyang/'+row.path,import.meta.url))),row.sha256,row.path);
 let usages=0;
 function walk(value){
  if(Array.isArray(value)){for(const child of value)walk(child);return;}
  if(!value||typeof value!=='object')return;
  if(Object.hasOwn(value,'sourceContract')){usages++;assert.equal(rows.filter(r=>r.path===value.sourceContract).length,1,value.sourceContract);}
  for(const child of Object.values(value))walk(child);
 }
 walk(published);assert.equal(usages,160);
 const original=clone(preGallery);withContractIdentityCorrections(preGallery);assert.deepEqual(preGallery,original);
 const broken=clone(preGallery);broken.provenance.sourceContracts[0].sha256='0'.repeat(64);
 assert.throws(()=>withContractIdentityCorrections(broken));
 assert.throws(()=>withContractIdentityCorrections(base));
});
