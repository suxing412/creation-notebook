import { test,expect } from '@playwright/test';
import { createHash } from 'node:crypto';
import { z13NodeIds } from '../../docs/cities/luoyang/z13-content.mjs';
import { project,bowlPoint,edgePoint } from './z13-geometry.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
test('actual Z13 renderer restores an independent baseline and exposes bowl and road edge geometry',async({page},info)=>{
 test.setTimeout(360_000);const errors=[],failures=[],captures=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)failures.push([r.url(),r.status()]);});
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.goto('/cities/luoyang/z13-qa.html');
 async function ready(){await expect.poll(()=>page.evaluate(()=>window.qa?.ready&&!!qa.state&&!qa.state.moving)).toBe(true);return page.evaluate(()=>qa.state);}
 async function action(id){const button=page.locator(id),chapter=await button.getAttribute('data-focus'),serial=await page.evaluate(()=>qa.serial);await button.click();await expect.poll(()=>page.evaluate(()=>qa.serial)).toBeGreaterThan(serial);if(chapter)await expect.poll(()=>page.evaluate(()=>qa.state.chapter)).toBe(chapter);return ready();}
 async function shot(label){const b=await page.locator('#qa-canvas').screenshot();await info.attach(label,{body:b,contentType:'image/png'});captures.push({label,sha256:hash(b),state:await page.evaluate(()=>qa.state)});return b;}
 const base=await ready(),baseManifest=await page.evaluate(()=>qa.manifest),baseMetrics=await page.evaluate(()=>qa.metrics.at(-1));
 expect(base.modelNodeIds).toHaveLength(73);await action('[data-focus="qa-oblique"]');const baseImage=await shot('independent-baseline');
 const installed=await action('#install');expect(installed.modelNodeIds).toEqual([...base.modelNodeIds,...z13NodeIds].sort());
 expect(installed.position).toEqual(base.position);expect(installed.target).toEqual(base.target);
 const metrics=await page.evaluate(()=>qa.metrics.at(-1));expect(metrics.downloadBytes-baseMetrics.downloadBytes).toBe(2007436);
 for(const [id,point,nodeId] of [['qa-bowl',bowlPoint,'market_bowl_C01'],['qa-edge',edgePoint,'Z13-ROAD-EDGE-INFILL-C01']]) {
  const view=await action(`[data-focus="${id}"]`),rect=await page.locator('#qa-canvas').boundingBox(),p=project(point,view,rect);
  expect(Math.abs(p.nx)).toBeLessThan(1);expect(Math.abs(p.ny)).toBeLessThan(1);
  await page.mouse.click(p.x,p.y);await expect.poll(()=>page.evaluate(()=>qa.selected?.id)).toBe(nodeId);
  const plain=await shot(id);await action('#redraw');expect(await page.locator('#qa-canvas').screenshot()).toEqual(plain);
  await action('#evidence');expect(hash(await page.locator('#qa-canvas').screenshot())).not.toBe(hash(plain));
  await action('#evidence');expect(await page.locator('#qa-canvas').screenshot()).toEqual(plain);
 }
 // Real slow movement, then fresh fixed poses; capture for motion-depth review.
 const dragStart=await action('[data-focus="qa-edge"]');const box=await page.locator('#qa-canvas').boundingBox();
 await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();
 for(let i=1;i<=8;i++){await page.mouse.move(box.x+box.width*(.5+i*.003),box.y+box.height*.5);await page.waitForTimeout(70);await shot(`edge-motion-${i}`);}
 await page.mouse.up();await expect.poll(()=>page.evaluate(p=>Math.hypot(...qa.state.position.map((v,i)=>v-p[i])),dragStart.position)).toBeGreaterThan(.05);await ready();
 const beforeDistance=await page.evaluate(()=>Math.hypot(...qa.state.position.map((v,i)=>v-qa.state.target[i])));
 await page.mouse.wheel(0,100);await expect.poll(()=>page.evaluate(()=>Math.hypot(...qa.state.position.map((v,i)=>v-qa.state.target[i])))).toBeGreaterThan(beforeDistance*1.01);await ready();await shot('edge-farther');
 await action('[data-focus="qa-oblique"]');const installedImage=await shot('installed-oblique');expect(hash(installedImage)).not.toBe(hash(baseImage));
 const withdrawn=await action('#withdraw');expect(withdrawn.modelNodeIds).toEqual(base.modelNodeIds);expect(await page.evaluate(()=>qa.manifest)).toEqual(baseManifest);
 await action('[data-focus="qa-oblique"]');expect(await shot('withdrawn')).toEqual(baseImage);
 const again=await action('#install');expect(again.modelNodeIds).toEqual(installed.modelNodeIds);await action('[data-focus="qa-oblique"]');expect(await shot('reinstalled')).toEqual(installedImage);
 const runtime=await page.evaluate(()=>qa);expect(runtime.errors).toEqual([]);expect(runtime.trusted.every(e=>e.isTrusted)).toBe(true);expect(errors).toEqual([]);expect(failures).toEqual([]);
 await info.attach('z13-rollback-metrics',{body:JSON.stringify({baseMetrics,metrics,captures,runtime,errors,failures},null,2),contentType:'application/json'});
});
