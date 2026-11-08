import { galleryRecords } from '../../docs/cities/luoyang/gallery-records.mjs';
import { test,expect } from '@playwright/test';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { z13Records,z13NodeIds } from '../../docs/cities/luoyang/z13-content.mjs';
import { instrument,openCity,state,settled,selectZone,assertFullCity,assertHealthy,attachEvidence } from './helpers.mjs';
import { project,streetPoint,groundPoint } from './z13-geometry.mjs';
const old=JSON.parse(readFileSync(new URL('./yong-access.json',import.meta.url)));
const expected=[...old.previousCityNodeIds,old.id,...z13NodeIds,...galleryRecords.map(r=>r.nodeId)].sort();
const files=z13Records.map(a=>({...a,path:new URL(a.path,'https://example.test/cities/luoyang/z13-content.mjs').pathname}));
test('Z13 five-piece installation loads exact files and remains visible during chapter and zone navigation',async({page},info)=>{
 const touch=info.project.name==='mobile',evidence=await instrument(page),received=[];
 page.on('response',r=>{if(files.some(f=>new URL(r.url()).pathname===f.path))received.push(r);});
 const gl=await openCity(page,touch);await page.emulateMedia({reducedMotion:'reduce'});
 const initial=await state(page);expect(initial.modelNodeIds).toEqual(expected);expect(expected).toHaveLength(87);
 const http=[];
 for(const f of files){const matches=received.filter(r=>new URL(r.url()).pathname===f.path);expect(matches).toHaveLength(1);
  const body=await matches[0].body();expect(matches[0].status()).toBe(200);expect(body.length).toBe(f.bytes);
  expect(createHash('sha256').update(body).digest('hex')).toBe(f.sha256);http.push({path:f.path,bytes:body.length,sha256:f.sha256});}
 const requests=evidence.modelRequests.slice(),views=[];
 const click=locator=>touch?locator.tap():locator.click();
 async function market(){await selectZone(page,'Z13',touch);await click(page.locator('.pj-chapters [data-ch="market"]'));
  await expect.poll(async()=>{const s=await state(page);return s.chapter==='market'&&!s.moving;}).toBe(true);
  const view=await settled(page);assertFullCity(view);expect(view.sceneRevision).toBe(initial.sceneRevision);return view;}
 try {
  for(const viewport of touch?[{width:375,height:812},{width:812,height:375},{width:375,height:812}]:[{width:1440,height:1000}]) {
   await page.setViewportSize(viewport);const view=await market();views.push(view);
   await page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
   const rect=await page.locator('#pj-canvas').boundingBox();
   for(const x of [184.285995,330])for(const y of [0,5.131])for(const z of [-2050,-1937.18396]) {
    const p=project([x,y,z],view,rect);expect(p.depth).toBeGreaterThan(0);expect(Math.abs(p.nx)).toBeLessThan(1);expect(Math.abs(p.ny)).toBeLessThan(1);
   }
   await page.locator('#pj-stage').screenshot({path:info.outputPath(`z13-market-${viewport.width}.png`)});
  }
  for(const [point,title] of [[streetPoint,z13Records[0].title],[groundPoint,z13Records[2].title]]) {
   const view=await market();await page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
   const rect=await page.locator('#pj-canvas').boundingBox(),p=project(point,view,rect),start=await page.evaluate(()=>performance.now());
   expect(Math.abs(p.nx)).toBeLessThan(1);expect(Math.abs(p.ny)).toBeLessThan(1);
   if(touch)await page.touchscreen.tap(p.x,p.y);else await page.mouse.click(p.x,p.y);
   await expect(page.locator('#pj-note')).toBeVisible();await expect(page.locator('#pj-nt')).toHaveText(title);await expect(page.locator('#pj-nl [data-l="C"]')).toHaveCount(1);
   for(const type of ['pointerdown','pointerup'])await expect.poll(()=>page.evaluate(({start,type,touch})=>window.luoyangEvidence.inputs.some(e=>e.time>=start&&e.type===type&&e.target==='pj-canvas'&&e.trusted&&(!touch||e.pointerType==='touch')),{start,type,touch})).toBe(true);
   const chain=await page.evaluate(start=>window.luoyangEvidence.inputs.filter(e=>e.time>=start&&e.target==='pj-canvas'),start);
   const down=chain.find(e=>e.type==='pointerdown'),up=chain.find(e=>e.type==='pointerup');expect(up.pointerId).toBe(down.pointerId);
   expect(Math.hypot(up.clientX-down.clientX,up.clientY-down.clientY)).toBeLessThan(2);
   await click(page.locator('#pj-x'));assertFullCity(await settled(page));
  }
  await selectZone(page,'Z14',touch);await selectZone(page,'Z13',touch);await click(page.locator('.ly-overview'));
  await expect.poll(async()=>{const s=await state(page);return s.chapter==='city'&&!s.moving;}).toBe(true);
  const end=await settled(page);expect(end.position).toEqual(initial.position);expect(end.target).toEqual(initial.target);
  // Same viewport is restored above; every installed model stays in this scene.
  expect(end.sceneRevision).toBe(initial.sceneRevision);expect(evidence.modelRequests).toEqual(requests);assertHealthy(evidence);
 } finally {await attachEvidence(page,info,evidence,{gl,http,views});}
});
