import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { installZ13,withdrawZ13,z13Records,z13NodeIds } from '../docs/cities/luoyang/z13-content.mjs';
import { withContractIdentityCorrections } from './contract-identity-fixture.mjs';
import current, * as named from '../docs/cities/luoyang/city-data.mjs';
import { withdrawGallery } from '../docs/cities/luoyang/gallery-content.mjs';
const published=withdrawGallery(current,named.galleryReceipt);
const baselineSHA='d840a304fff11a3603fc9370360b23dc3ca1562e';
const original=execFileSync('git',['show',`${baselineSHA}:docs/cities/luoyang/city-data.mjs`],{encoding:'utf8'});
const source=original.replaceAll('import.meta.url',JSON.stringify(new URL('../docs/cities/luoyang/city-data.mjs',import.meta.url).href));
const historical=(await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)).default;
const base=withContractIdentityCorrections(historical);
const installed=installZ13(base),clone=x=>structuredClone(x);
test('independent baseline survives install, withdraw and reinstall exactly',()=>{
 assert.equal(base.nodes.length,80);assert.equal(base.assets.length,56);
 assert.equal(installed.manifest.nodes.length,85);assert.equal(installed.manifest.assets.length,61);
 assert.deepEqual(installed.manifest,published);
 for(const key of ['assets','nodes','chapters','provenance'])assert.equal(named[key],current[key]);
 assert.deepEqual(installed.manifest.nodes.slice(0,80),base.nodes);
 assert.deepEqual(installed.manifest.assets.slice(0,56),base.assets);
 for(const key of ['initialCamera','overview','researchModels'])assert.deepEqual(published[key],base[key]);
 assert.deepEqual(withdrawZ13(published,installed.receipt),base);
 assert.deepEqual(installZ13(withdrawZ13(published,installed.receipt)),installed);
 assert.throws(()=>installZ13(published));assert.deepEqual(base.nodes.length,80);
});
test('withdraw preserves unrelated additions, rejects dependencies and changed owned data',()=>{
 const good=clone(published);good.otherWork={retained:true};good.nodes.push({id:'independent',asset:base.assets[0].id});
 good.provenance.allCityModelBytes+=123;
 const restored=withdrawZ13(good,installed.receipt);assert.deepEqual(restored.otherWork,good.otherWork);
 assert.equal(restored.nodes.at(-1).id,'independent');assert.equal(restored.provenance.allCityModelBytes,base.provenance.allCityModelBytes+123);
 const changes=[m=>m.nodes.find(n=>n.id===z13NodeIds[0]).matrix[12]++,m=>m.assets.at(-1).sha256='changed',
 m=>m.chapters.find(c=>c.id==='market').nodeIds.push('later-market-node'),
 m=>m.nodes.push({id:'dependent',asset:z13Records[0].id}),
 m=>m.chapters[0].nodeIds.push(z13NodeIds[0]),m=>m.researchModels.push({id:'study',asset:z13Records[0].id}),
 m=>m.provenance.sourceContracts.find(s=>s.path.includes('z13-market')).sha256='changed'];
 for(const change of changes){const m=clone(published);change(m);const before=clone(m);assert.throws(()=>withdrawZ13(m,installed.receipt));assert.deepEqual(m,before);}
});
test('asset identity, explicit transforms and source contract match delivered GLBs',()=>{
 for(const a of z13Records){const b=readFileSync(new URL(a.path,new URL('../docs/cities/luoyang/z13-content.mjs',import.meta.url)));
 assert.equal(b.length,a.bytes);assert.equal(createHash('sha256').update(b).digest('hex'),a.sha256);}
 const ns=published.nodes.filter(n=>z13NodeIds.includes(n.id));
 assert.deepEqual(ns[0].matrix,ns[1].matrix);assert.equal(ns[0].matrix[12],300);assert.equal(ns[0].matrix[14],-2000);
 const identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];assert.deepEqual(ns[2].matrix,identity);assert.deepEqual(ns[3].matrix,identity);
 assert.deepEqual(ns[4].position,[294,1.2099999904632568,-1979]);
 assert.ok(ns.every(n=>n.countAsCourtyard===false&&n.tier==='C'&&n.zoneId==='Z13'&&!n.replaces));
 const s=published.provenance.sourceContracts.find(s=>s.path.includes('z13-market'));
 assert.equal(createHash('sha256').update(readFileSync(new URL(s.path,new URL('../docs/cities/luoyang/city-data.mjs',import.meta.url)))).digest('hex'),s.sha256);
});

test('altered receipts cannot change budgets, leave assets behind or replace the chapter',()=>{
 for(const change of [r=>r.budget=1,r=>r.assets=[],r=>r.chapterBefore.title='altered',r=>r.nodes[0].matrix[12]=1]) {
  const receipt=clone(installed.receipt);change(receipt);assert.throws(()=>withdrawZ13(published,receipt));
 }
});
test('public previews contain image data only, with no EXIF or rendering metadata',()=>{
 for(const folder of ['m-luoyang-grey-pottery-bowl','m-luoyang-z13-market-ground'])for(const file of ['cover.png','shots/context.png']){
  const b=readFileSync(new URL(`../docs/library/models/${folder}/${file}`,import.meta.url));let p=8;
  while(p<b.length){const length=b.readUInt32BE(p),type=b.toString('ascii',p+4,p+8);assert.ok(['IHDR','IDAT','IEND'].includes(type));p+=length+12;}assert.equal(p,b.length);
 }
});
