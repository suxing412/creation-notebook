import {test,expect} from '@playwright/test';
import {createHash} from 'node:crypto';
import {displayGroundId as id} from '../../docs/cities/luoyang/ground-content.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
test('independent ground rollback renders 86 to 87 to 86 to 87, restoring full manifest and fixed-view pixels',async({page},info)=>{
 test.setTimeout(480000);const touch=info.project.name==='mobile',session=touch?await page.context().newCDPSession(page):null;const captures=[],errors=[],bad=[];page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)bad.push({status:r.status(),url:r.url()});});
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('/cities/luoyang/ground-qa.html');
 const state=()=>page.evaluate(()=>groundQA.state),metrics=()=>page.evaluate(()=>groundQA.metrics.at(-1));
 async function ready(){await expect.poll(()=>page.evaluate(()=>{const q=window.groundQA,m=q?.metrics.at(-1);return !!q?.ready&&q.state&&!q.state.moving&&q.state.pendingSceneLoads===0&&m?.epoch===q.epoch&&!m.contextLost;})).toBe(true);const s=await state();expect(s.target[1]).toBe(0);return s;}
 async function click(selector){const serial=await page.evaluate(()=>groundQA.actionSerial);if(touch)await page.locator(selector).tap();else await page.locator(selector).click();await expect.poll(()=>page.evaluate(()=>groundQA.actionSerial)).toBeGreaterThan(serial);return ready();}
 async function shot(name){const b=await page.locator('#ground-qa-canvas').screenshot();captures.push({name,sha256:hash(b),state:await state(),metrics:await metrics()});await info.attach(name,{body:b,contentType:'image/png'});return b;}
 try{
  const base=await ready();expect(base.modelNodeIds).toHaveLength(86);expect(base.modelNodeIds).not.toContain(id);const manifest=await page.evaluate(()=>groundQA.manifest);
  await click('[data-focus="qa-ground-wide"]');await click('#redraw');const baselinePNG=await shot('baseline'),baselineMetrics=await metrics();
  const installed=await click('#install');expect(installed.modelNodeIds).toHaveLength(87);expect(installed.modelNodeIds.filter(n=>n!==id)).toEqual(base.modelNodeIds);
  await click('[data-focus="qa-ground-wide"]');await click('#redraw');const installedPNG=await shot('installed'),installedMetrics=await metrics();expect(hash(installedPNG)).not.toBe(hash(baselinePNG));expect(installedMetrics.downloadBytes-baselineMetrics.downloadBytes).toBe(56416);expect(installedMetrics.representedNodes).toBe(87);expect(installedMetrics.triangles-baselineMetrics.triangles).toBe(1024);expect(installedMetrics.drawCalls-baselineMetrics.drawCalls).toBe(2);
  for(const focus of ['qa-ground-wall','qa-ground-market','qa-ground-road','qa-ground-well']){
   await click('[data-focus="'+focus+'"]');const plain=await shot(focus+'-still');await click('#redraw');expect(await page.locator('#ground-qa-canvas').screenshot()).toEqual(plain);
   await click('#evidence');await shot(focus+'-evidence');await click('#evidence');expect(await page.locator('#ground-qa-canvas').screenshot()).toEqual(plain);
   await page.locator('#ground-qa-canvas').scrollIntoViewIfNeeded();const box=await page.locator('#ground-qa-canvas').boundingBox(),point={x:box.x+box.width*.5,y:box.y+box.height*.5,id:1};
   if(touch)await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});else{await page.mouse.move(point.x,point.y);await page.mouse.down();}
   try{for(let k=1;k<=6;k++){await page.waitForTimeout(50);const next={x:point.x+k*3,y:point.y+k,id:1};if(touch)await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[next]});else await page.mouse.move(next.x,next.y);await shot(focus+'-motion-'+k);}}finally{if(touch)await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});else await page.mouse.up();}
   await ready();expect((await state()).modelNodeIds).toHaveLength(87);expect((await state()).target[1]).toBe(0);expect(new Set(captures.filter(c=>c.name.startsWith(focus+'-motion-')).map(c=>c.sha256)).size,'Motion views must show geometry rather than an obstructed blank wall').toBeGreaterThan(1);
   if(touch)await page.touchscreen.tap(box.x+box.width*.5,box.y+box.height*.6);else await page.mouse.click(box.x+box.width*.5,box.y+box.height*.6);expect(await page.evaluate(()=>groundQA.selected?.id)).not.toBe(id);
  }
  await click('#research');expect((await state()).modelNodeIds).not.toContain(id);await click('#city');expect((await state()).modelNodeIds).toHaveLength(87);
  const withdrawn=await click('#withdraw');expect(withdrawn.modelNodeIds).toEqual(base.modelNodeIds);expect(await page.evaluate(()=>groundQA.manifest)).toEqual(manifest);
  await click('[data-focus="qa-ground-wide"]');await click('#redraw');expect(await shot('withdrawn')).toEqual(baselinePNG);const restored=await metrics();for(const k of ['downloadBytes','drawCalls','triangles','representedNodes'])expect(restored[k]).toBe(baselineMetrics[k]);
  await click('#install');await click('[data-focus="qa-ground-wide"]');await click('#redraw');expect(await shot('reinstalled')).toEqual(installedPNG);
  expect(errors).toEqual([]);expect(bad).toEqual([]);expect(await page.evaluate(()=>groundQA.errors)).toEqual([]);expect(await page.evaluate(()=>groundQA.actions.every(a=>a.trusted&&a.finished&&!a.error))).toBe(true);
 }finally{await info.attach('ground-browser-evidence',{body:JSON.stringify({captures,errors,bad,runtime:await page.evaluate(()=>window.groundQA||null),limits:'Sampled software-rendered views only; no hardware GPU or all-angle flicker certification.'},null,2),contentType:'application/json'});}
});
