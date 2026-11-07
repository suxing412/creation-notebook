// Pure, reversible additive manifest adapter. Preparing a manifest is not scope admission.
// No network, filesystem, frontend, global camera, road or existing-model writes.
import { galleryRecords as rawRecords } from './gallery-records.mjs';
const clone = value => structuredClone(value);
const freeze = value => { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };
export const galleryRecords = freeze(clone(rawRecords));
export const galleryScopes = freeze(['six-plus-prefix', 'all-eight']);
export const defaultGalleryScope = 'all-eight'; // Caller selects the bounded assembly; this module cannot grant admission.
const key = 'galleryLocalC1', chapterId = 'gallery-local-c', sourcePath = 'progress-assets/gallery-local-C-v1/source.json';
const sourceSHA = 'd9776eed9a8d5dfc039210d319610a786d37e66b12b5667da245795c9e4a5467';
const equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
const guard = (condition,message) => { if (!condition) throw new Error('Gallery: '+message); };
const selected = scope => { guard(galleryScopes.includes(scope),'Unknown scope'); return galleryRecords.slice(0,scope === 'all-eight' ? 8 : 7); };
// Old library pages served slimmed bytes at these paths; isolate the original city payload from that cache.
const runtimeURL = r => { const url=new URL(r.path,import.meta.url);if(r.reusesPublishedFile)url.searchParams.set('v',r.sha256);return url.href; };
const unavailable = tier => ['U','X','unknown','excluded','未知','排除'].includes(tier);
function checkShape(m) {
 guard(m && ['assets','nodes','chapters','researchModels'].every(k=>Array.isArray(m[k])) && m.provenance && Array.isArray(m.provenance.sourceContracts),'Missing manifest collections');
 for (const name of ['assets','nodes','chapters','researchModels']) {
  const ids=m[name].map(o=>o.id);guard(ids.every(x=>typeof x==='string') && new Set(ids).size===ids.length,'Duplicate or invalid '+name+' identity');
 }
 guard(new Set([...m.nodes,...m.researchModels].map(n=>n.id)).size===m.nodes.length+m.researchModels.length,'City/research node ID collision');
 for(const k of ['initialModelBytes','allCityModelBytes'])guard(Number.isFinite(m.provenance[k])&&m.provenance[k]>=0,'Invalid '+k);
}
export function describeProjectRuntime(m) {
 const assets=new Map(m.assets.map(a=>[a.id,a]));
 const active=m.nodes.filter(n=>n.space!=='local-study'&&!unavailable(n.tier??assets.get(n.asset)?.tier));
 const replaced=new Set(active.flatMap(n=>n.replaces||[]));
 const drawn=active.filter(n=>!replaced.has(n.id));
 const urls=new Map();
 for(const n of drawn){const a=assets.get(n.asset);guard(a,'Unknown asset '+n.asset);if(urls.has(a.url))guard(urls.get(a.url).bytes===a.bytes && urls.get(a.url).sha256===a.sha256,'Conflicting same URL');urls.set(a.url,{bytes:a.bytes,sha256:a.sha256});}
 return {manifestNodes:m.nodes.length,manifestAssets:m.assets.length,locatedNodes:active.length,replacementSuppressedNodes:active.length-drawn.length,drawnNodes:drawn.length,uniqueRuntimeURLs:urls.size,selectedDefaultGLBBytes:[...urls.values()].reduce((n,a)=>n+a.bytes,0),drawnNodeIds:drawn.map(n=>n.id)};
}
function expectedAsset(r) {
 return {id:r.id,sourcePath:r.path,url:runtimeURL(r),bytes:r.bytes,sha256:r.sha256,bounds:clone(r.bounds),tier:'C',...(r.reusesPublishedFile?{}:{sourceContract:sourcePath})};
}
function matchingOriginal(m,r) {
 const found=m.assets.filter(a=>a.sha256===r.sha256 || a.url===runtimeURL(r) || a.sourcePath===r.path);
 guard(found.length<=1,'Duplicate SHA records require explicit deduplication: '+r.component);
 if(!found.length)return null;
 const a=found[0];
 guard(r.reusesPublishedFile,'Supplemental asset already present without gallery receipt');
 guard(a.sha256===r.sha256 && a.bytes===r.bytes && a.url===runtimeURL(r) && equal(a.bounds,r.bounds) && !(a.excludeNodes?.length),'Original record changed: '+r.component);
 return a;
}
function combinedBounds(records){return {min:[0,1,2].map(i=>Math.min(...records.map(r=>r.worldBounds.min[i]))),max:[0,1,2].map(i=>Math.max(...records.map(r=>r.worldBounds.max[i])))};}
function chapterFor(scope,records) {
 return {id:chapterId,title:'复道局部接近地表',subtitle:'C级空间装配研究 · 原件近景质量',tier:'C',
 nodeIds:records.map(r=>r.nodeId),loadNodeIds:records.map(r=>r.nodeId),bounds:combinedBounds(records),
 basis:'Z23内的局部示意装配，不是两宫端点、史实名门、已确定出入口或公共穿行路线。绝对高程、下部土体承载和门禁未知。'+(scope==='all-eight'?' 后段为可撤回的路缘接近地表设计，保留原道路；不证明通行权。':' 前段端部开放，未接路。')};
}
function nodeFor(r,assetId) {
 return {id:r.nodeId,asset:assetId,title:r.title,summary:r.summary,basis:r.summary,tier:'C',chapter:chapterId,zoneId:'Z23',matrix:clone(r.matrix),bounds:clone(r.worldBounds),initial:true,countAsCourtyard:false,sourceContract:sourcePath,kind:'gallery-local-C-assembly',replaces:[]};
}
export function installGallery(input,{scope=defaultGalleryScope}={}) {
 checkShape(input);const m=clone(input), records=selected(scope);
 guard(!m.provenance[key],'Already installed; withdraw before changing scope');
 guard(!m.chapters.some(c=>c.id===chapterId),'Chapter identity occupied');
 guard(!m.provenance.sourceContracts.some(s=>s.path===sourcePath),'Source identity occupied');
 for(const r of galleryRecords)guard(![...m.nodes,...m.researchModels].some(n=>n.id===r.nodeId),'Node identity occupied: '+r.nodeId);
 const before=describeProjectRuntime(m), ownedAssets=[],reusedAssets=[],addedNodes=[];
 for(const r of records){
  const reusable=matchingOriginal(m,r);let a;
  if(reusable){a=reusable;reusedAssets.push(clone(a));}
  else {a=expectedAsset(r);guard(!m.assets.some(x=>x.id===a.id),'Asset ID occupied: '+a.id);ownedAssets.push(clone(a));m.assets.push(a);}
  const n=nodeFor(r,a.id);addedNodes.push(clone(n));m.nodes.push(n);
 }
 const chapter=chapterFor(scope,records);m.chapters.push(chapter);
 const source={path:sourcePath,sha256:sourceSHA};m.provenance.sourceContracts.push(source);
 const after=describeProjectRuntime(m),budget=after.selectedDefaultGLBBytes-before.selectedDefaultGLBBytes;
 guard(budget>=0,'Negative incremental runtime budget');
 const provenance={scope,ownedAssetIds:ownedAssets.map(a=>a.id),reusedAssetIds:reusedAssets.map(a=>a.id),newCityNodes:records.length,newResidentialCourtyards:0,defaultQuality:'LOD0',automaticLOD:false,initiallyVisible:true,selectedRuntimeBytes:records.reduce((n,r)=>n+r.bytes,0),incrementalUniqueRuntimeBytes:budget,newSupplementalGLBBytes:records.filter(r=>!r.reusesPublishedFile).reduce((n,r)=>n+r.bytes,0),scopeAdmission:'NOT_CLAIMED_BY_THIS_MANIFEST',installationStatus:'INSTALLED_MANIFEST',coordinateGrade:'C',wholeRouteOrPublicEntryClaim:false};
 m.provenance[key]=provenance;m.provenance.initialModelBytes+=budget;m.provenance.allCityModelBytes+=budget;
 const receipt={schema:1,adapter:'gallery-local-C-v1',scope,ownedAssets:clone(ownedAssets),reusedAssets:clone(reusedAssets),nodes:clone(addedNodes),chapter:clone(chapter),source:clone(source),budget,provenance:clone(provenance)};
 return {manifest:m,receipt};
}
export function withdrawGallery(input,receipt) {
 checkShape(input);guard(receipt?.schema===1 && receipt.adapter==='gallery-local-C-v1','Invalid receipt');
 const records=selected(receipt.scope),m=clone(input);
 guard(Array.isArray(receipt.ownedAssets)&&Array.isArray(receipt.reusedAssets)&&Array.isArray(receipt.nodes),'Malformed receipt');
 const allowedAssetIds=new Set(records.map(r=>r.id)), ids=new Set(records.map(r=>r.nodeId));
 guard(receipt.ownedAssets.every(a=>allowedAssetIds.has(a.id)),'Receipt owns unrelated asset');
 guard(receipt.nodes.length===records.length && receipt.nodes.every((n,i)=>n.id===records[i].nodeId),'Receipt node list altered');
 for(const a of receipt.ownedAssets)guard(equal(m.assets.find(x=>x.id===a.id),a),'Owned asset changed');
 for(const a of receipt.reusedAssets)guard(equal(m.assets.find(x=>x.id===a.id),a),'Reused original asset changed');
 for(const n of receipt.nodes)guard(equal(m.nodes.find(x=>x.id===n.id),n),'Owned node changed');
 guard(equal(m.chapters.find(c=>c.id===chapterId),receipt.chapter),'Owned chapter changed or depended upon');
 guard(equal(m.provenance[key],receipt.provenance),'Owned provenance changed');
 guard(equal(receipt.ownedAssets.map(a=>a.id),m.provenance[key].ownedAssetIds)&&equal(receipt.reusedAssets.map(a=>a.id),m.provenance[key].reusedAssetIds),'Receipt asset ownership changed');
 const sources=m.provenance.sourceContracts.filter(s=>s.path===sourcePath);guard(sources.length===1&&equal(sources[0],receipt.source),'Source changed or duplicated');
 const ownedAssets=new Set(receipt.ownedAssets.map(a=>a.id));
 const ownedSHAs=new Set(receipt.ownedAssets.map(a=>a.sha256));
 const relatedAssetIds=new Set(m.assets.filter(a=>ownedAssets.has(a.id)||ownedSHAs.has(a.sha256)).map(a=>a.id));
 for(const n of [...m.nodes,...m.researchModels].filter(n=>!ids.has(n.id)))guard(!relatedAssetIds.has(n.asset)&&n.sourceContract!==sourcePath&&!(n.replaces||[]).some(id=>ids.has(id)),'New node/research dependency');
 for(const c of m.chapters.filter(c=>c.id!==chapterId))guard(![...(c.nodeIds||[]),...(c.loadNodeIds||[]),...(c.researchModelIds||[]),c.defaultResearchModel].some(id=>ids.has(id)),'New chapter dependency');
 guard(!m.assets.some(a=>!ownedAssets.has(a.id)&&(ownedSHAs.has(a.sha256)||a.sourceContract===sourcePath)),'New same-model/source asset dependency');
 m.nodes=m.nodes.filter(n=>!ids.has(n.id));m.assets=m.assets.filter(a=>!ownedAssets.has(a.id));m.chapters=m.chapters.filter(c=>c.id!==chapterId);
 m.provenance.sourceContracts=m.provenance.sourceContracts.filter(s=>s.path!==sourcePath);delete m.provenance[key];
 guard(Number.isFinite(receipt.budget)&&receipt.budget>=0,'Invalid budget receipt');
 m.provenance.initialModelBytes-=receipt.budget;m.provenance.allCityModelBytes-=receipt.budget;
 const canonical=installGallery(m,{scope:receipt.scope}).receipt;
 guard(equal(receipt,canonical),'Receipt altered, originals changed or new dependency; explicit reconciliation required');
 return m;
}
