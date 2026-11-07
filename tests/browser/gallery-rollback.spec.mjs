import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {galleryRecords} from '../../docs/cities/luoyang/gallery-content.mjs';
import {z13NodeIds} from '../../docs/cities/luoyang/z13-content.mjs';
import {galleryPicks,galleryRoadJoint,galleryRuntimeBudget,project,corners} from './gallery-geometry.mjs';
const old=JSON.parse(readFileSync(new URL('./yong-access.json',import.meta.url)));
const previous=[...old.previousCityNodeIds,old.id,...z13NodeIds].sort(),ids=galleryRecords.map(r=>r.nodeId);
const hash=b=>createHash('sha256').update(b).digest('hex'),distance=s=>Math.hypot(...s.position.map((v,i)=>v-s.target[i]));
test('gallery installation renders eight real parts and returns exactly to the independent 78-node baseline',async({page},info)=>{
 test.setTimeout(480_000);const captures=[],errors=[],consoleErrors=[],failedRequests=[],failedResponses=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
 page.on('requestfailed',r=>failedRequests.push({url:r.url(),error:r.failure()?.errorText}));page.on('response',r=>{if(r.status()>=400)failedResponses.push({url:r.url(),status:r.status()});});
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/cities/luoyang/gallery-qa.html');
 const state=()=>page.evaluate(()=>window.galleryQA.state);
 async function ready(){
  await expect.poll(()=>page.evaluate(()=>{const q=window.galleryQA,m=q?.metrics.at(-1);return !!q?.ready&&!!q.state&&!q.state.moving&&q.state.pendingSceneLoads===0&&m?.epoch===q.epoch&&!m.contextLost;})).toBe(true);
  const s=await state();expect(s.target[1]).toBe(0);expect([...s.position,...s.target].every(Number.isFinite)).toBe(true);return s;
 }
 async function action(selector,{mode,evidence}={}){
  const button=page.locator(selector),chapter=await button.getAttribute('data-focus');
  const before=await page.evaluate(()=>({serial:galleryQA.serial,action:galleryQA.actionSerial}));await button.click();
  await expect.poll(()=>page.evaluate(({before,chapter,mode,evidence})=>{const q=galleryQA,m=q.metrics.at(-1);return q.serial>before.serial&&q.actionSerial>before.action&&(!chapter||q.state.chapter===chapter)&&(!mode||q.mode===mode)&&(evidence===undefined||m?.evidenceVisible===evidence);},{before,chapter,mode,evidence})).toBe(true);
  return ready();
 }
 async function shot(label){const png=await page.locator('#gallery-qa-canvas').screenshot();await info.attach(label,{body:png,contentType:'image/png'});captures.push({label,sha256:hash(png),state:await state(),metrics:await page.evaluate(()=>galleryQA.metrics.at(-1))});return png;}
 const assertInstalled=s=>{expect(s.modelNodeIds).toEqual([...previous,...ids].sort());expect(s.modelNodeIds).toHaveLength(86);expect(s.studyId).toBeNull();expect(s.target[1]).toBe(0);};
 try{
  const base=await ready();expect(previous).toHaveLength(78);expect(base.modelNodeIds).toEqual(previous);
  const baselineManifest=await page.evaluate(()=>galleryQA.manifest);
  await action('[data-focus="qa-gallery-wide"]');await action('#redraw');
  const baselineImage=await shot('gallery-independent-baseline'),baseMetrics=await page.evaluate(()=>galleryQA.metrics.at(-1));
  const installed=await action('#install',{mode:'installed'});assertInstalled(installed);
  expect(installed.position).toEqual(base.position);expect(installed.target).toEqual(base.target);
  await action('[data-focus="qa-gallery-wide"]');await action('#redraw');
  const wide=await state(),rect=await page.locator('#gallery-qa-canvas').boundingBox();
  for(const point of corners()){const p=project(point,wide,rect);expect(p.depth).toBeGreaterThan(.08);expect(Math.abs(p.nx)).toBeLessThan(1);expect(Math.abs(p.ny)).toBeLessThan(1);}
  const installedImage=await shot('gallery-installed-wide'),metrics=await page.evaluate(()=>galleryQA.metrics.at(-1));
  expect(hash(installedImage)).not.toBe(hash(baselineImage));expect(metrics.representedNodes).toBe(86);
  expect(metrics.downloadBytes-baseMetrics.downloadBytes).toBe(galleryRuntimeBudget.newUniqueBytes);
  expect(metrics.triangles-baseMetrics.triangles).toBe(galleryRuntimeBudget.twoPassTriangleDelta);
  expect(metrics.drawCalls-baseMetrics.drawCalls).toBeGreaterThan(0);expect(metrics.drawCalls-baseMetrics.drawCalls).toBeLessThanOrEqual(galleryRuntimeBudget.twoPassDrawCallLimit);
  for(const pick of galleryPicks){
   const view=await action(`[data-focus="${pick.viewId}"]`);assertInstalled(view);
   const box=await page.locator('#gallery-qa-canvas').boundingBox(),p=project(pick.point,view,box);
   expect(p.depth).toBeGreaterThan(.08);expect(Math.abs(p.nx)).toBeLessThan(.95);expect(Math.abs(p.ny)).toBeLessThan(.95);
   const before=await page.evaluate(()=>({time:performance.now(),selection:galleryQA.selectionSerial}));
   await page.mouse.click(p.x,p.y);
   await expect.poll(()=>page.evaluate(({pick,before})=>galleryQA.selectionSerial>before.selection&&galleryQA.selected?.id===pick.nodeId,{pick,before})).toBe(true);
   const input=await page.evaluate(t=>galleryQA.inputs.filter(e=>e.time>=t&&e.path.includes('gallery-qa-canvas')),before.time);
   const down=input.find(e=>e.type==='pointerdown'),up=input.find(e=>e.type==='pointerup');expect(down?.trusted).toBe(true);expect(up?.trusted).toBe(true);expect(up.pointerId).toBe(down.pointerId);expect(Math.hypot(up.x-down.x,up.y-down.y)).toBeLessThan(2);
   const plain=await shot(pick.viewId);await action('#redraw');expect(await page.locator('#gallery-qa-canvas').screenshot()).toEqual(plain);
   await action('#evidence',{evidence:true});expect(hash(await shot(`${pick.viewId}-evidence`))).not.toBe(hash(plain));
   await action('#evidence',{evidence:false});expect(await page.locator('#gallery-qa-canvas').screenshot()).toEqual(plain);
   const stable=await state();expect(stable.position).toEqual(view.position);expect(stable.target).toEqual(view.target);
  }
  // Keep the prefix motion check and independently inspect the actual terminal road joint.
  for(const [id,label] of [['qa-gallery-prefix','gallery-prefix'],[galleryRoadJoint.viewId,'gallery-road-joint']]){
   const beforeDrag=await action(`[data-focus="${id}"]`),box=await page.locator('#gallery-qa-canvas').boundingBox();
   if(id===galleryRoadJoint.viewId){const projected=project(galleryRoadJoint.point,beforeDrag,box);expect(projected.depth).toBeGreaterThan(.08);expect(Math.abs(projected.nx)).toBeLessThan(.9);expect(Math.abs(projected.ny)).toBeLessThan(.9);}
   const plain=await shot(`${label}-before-motion`);await action('#evidence',{evidence:true});expect(hash(await shot(`${label}-evidence-before-motion`))).not.toBe(hash(plain));
   await action('#evidence',{evidence:false});expect(await page.locator('#gallery-qa-canvas').screenshot()).toEqual(plain);
   const started=await page.evaluate(()=>performance.now());await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();
   try{for(let i=1;i<=8;i++){await page.mouse.move(box.x+box.width*.5+i*4,box.y+box.height*.5+i);await page.waitForTimeout(50);await shot(`${label}-drag-${i}`);}}finally{await page.mouse.up();}
   await expect.poll(()=>page.evaluate(before=>Math.hypot(...galleryQA.state.position.map((v,i)=>v-before[i])),beforeDrag.position)).toBeGreaterThan(.05);
   const dragged=await ready();assertInstalled(dragged);expect(dragged.target).toEqual(beforeDrag.target);
   const samples=await page.evaluate(t=>galleryQA.states.filter(s=>s.time>=t),started);expect(samples.length).toBeGreaterThan(1);expect(samples.every(s=>s.target[1]===0)).toBe(true);
   const afterMotion=await shot(`${label}-after-motion`);await action('#evidence',{evidence:true});expect(hash(await shot(`${label}-evidence-after-motion`))).not.toBe(hash(afterMotion));
   await action('#evidence',{evidence:false});expect(await page.locator('#gallery-qa-canvas').screenshot()).toEqual(afterMotion);
   await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.wheel(0,100);await expect.poll(async()=>distance(await state())).toBeGreaterThan(distance(dragged)*1.01);assertInstalled(await ready());await shot(`${label}-farther`);
  }
  const withdrawn=await action('#withdraw',{mode:'withdrawn'});expect(withdrawn.modelNodeIds).toEqual(previous);expect(await page.evaluate(()=>galleryQA.manifest)).toEqual(baselineManifest);
  await action('[data-focus="qa-gallery-wide"]');expect(await shot('gallery-withdrawn-wide')).toEqual(baselineImage);
  const restoredMetrics=await page.evaluate(()=>galleryQA.metrics.at(-1));for(const key of ['downloadBytes','triangles','drawCalls','representedNodes'])expect(restoredMetrics[key]).toBe(baseMetrics[key]);
  assertInstalled(await action('#install',{mode:'installed'}));await action('[data-focus="qa-gallery-wide"]');expect(await shot('gallery-reinstalled-wide')).toEqual(installedImage);
  const runtime=await page.evaluate(()=>galleryQA);expect(runtime.errors).toEqual([]);expect(runtime.actions.length).toBeGreaterThan(15);expect(runtime.actions.every(a=>a.trusted&&a.finished&&!a.error)).toBe(true);
  expect(errors).toEqual([]);expect(consoleErrors).toEqual([]);expect(failedRequests).toEqual([]);expect(failedResponses).toEqual([]);
 }finally{await info.attach('gallery-rollback-evidence',{body:JSON.stringify({captures,errors,consoleErrors,failedRequests,failedResponses,runtime:await page.evaluate(()=>window.galleryQA||null),budget:galleryRuntimeBudget},null,2),contentType:'application/json'});}
});
