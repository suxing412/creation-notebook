import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {galleryRecords} from '../../docs/cities/luoyang/gallery-content.mjs';
import {z13NodeIds} from '../../docs/cities/luoyang/z13-content.mjs';
import {instrument,openCity,state,settled,selectZone,assertFullCity,assertHealthy,attachEvidence,delta,distance} from './helpers.mjs';
import {galleryPicks,galleryRuntimeBudget,project,corners} from './gallery-geometry.mjs';
const old=JSON.parse(readFileSync(new URL('./yong-access.json',import.meta.url)));
const expected=[...old.previousCityNodeIds,old.id,...z13NodeIds,...galleryRecords.map(r=>r.nodeId)].sort();
const files=galleryRecords.map(r=>({...r,path:new URL(r.path,'https://site.invalid/cities/luoyang/gallery-content.mjs').pathname}));
test('gallery eight-part assembly remains in the real city and exposes finite ground and both approach sections',async({page},info)=>{
 test.setTimeout(360_000);const touch=info.project.name==='mobile',evidence=await instrument(page),received=[],views=[],http=[];let gl;
 page.on('response',r=>{if(files.some(f=>new URL(r.url()).pathname===f.path))received.push(r);});
 await page.addInitScript(()=>{
  window.galleryClicks=[];
  document.addEventListener('click',e=>window.galleryClicks.push({time:e.timeStamp,trusted:e.isTrusted,pointerId:e.pointerId,pointerType:e.pointerType,x:e.clientX,y:e.clientY,path:e.composedPath().map(n=>n.id).filter(Boolean)}),true);
  document.addEventListener('luoyang-view-change',e=>{const canvas=e.target,r=canvas.parentElement.getBoundingClientRect();window.galleryViewportFrame={serial:window.galleryViewportSerial=(window.galleryViewportSerial||0)+1,viewport:[innerWidth,innerHeight],visual:[visualViewport.width,visualViewport.height],stage:[Math.floor(r.width),Math.floor(r.height)],buffer:[canvas.width,canvas.height],ratio:Math.min(devicePixelRatio||1,1.5),state:structuredClone(e.detail)};},true);
 });
 const click=locator=>touch?locator.tap():locator.click();
 const align=()=>page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
 const canvasRect=()=>page.locator('#pj-canvas').evaluate(canvas=>{const r=canvas.getBoundingClientRect(),s=canvas.parentElement.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,aspect:Math.floor(s.width)/Math.floor(s.height)};});
 async function resize(viewport){
  const prior=page.viewportSize();if(prior.width===viewport.width&&prior.height===viewport.height)return;
  const serial=await page.evaluate(()=>window.galleryViewportSerial||0);await page.setViewportSize(viewport);
  await expect.poll(()=>page.evaluate(({viewport,serial})=>{const r=window.galleryViewportFrame;return !!r&&r.serial>serial&&r.viewport[0]===viewport.width&&r.viewport[1]===viewport.height&&r.visual[0]===viewport.width&&r.visual[1]===viewport.height&&r.buffer[0]===Math.floor(r.stage[0]*r.ratio)&&r.buffer[1]===Math.floor(r.stage[1]*r.ratio)&&!r.state.moving;},{viewport,serial})).toBe(true);
 }
 async function chapter(){
  await selectZone(page,'Z23',touch);await click(page.locator('.pj-chapters [data-ch="gallery-local-c"]'));
  await expect.poll(async()=>{const s=await state(page);return s.chapter==='gallery-local-c'&&s.zoneId===null&&!s.moving&&s.pendingSceneLoads===0;}).toBe(true);
  const s=await settled(page);assertFullCity(s);expect(s.modelNodeIds).toEqual(expected);await align();return s;
 }
 try{
  gl=await openCity(page,touch);await page.emulateMedia({reducedMotion:'reduce'});const initial=await state(page);
  expect(expected).toHaveLength(86);expect(initial.modelNodeIds).toEqual(expected);
  for(const file of files){const responses=received.filter(r=>new URL(r.url()).pathname===file.path);expect(responses).toHaveLength(1);const response=responses[0],body=await response.body();expect(response.status()).toBe(200);expect(body.length).toBe(file.bytes);const sha=createHash('sha256').update(body).digest('hex');expect(sha).toBe(file.sha256);http.push({path:file.path,bytes:body.length,sha256:sha});}
  expect(http.reduce((n,f)=>n+f.bytes,0)).toBe(galleryRuntimeBudget.newUniqueBytes);const requests=evidence.modelRequests.slice();
  const dimensions=touch?[{width:375,height:812,label:'portrait'},{width:812,height:375,label:'landscape'}]:[{width:1440,height:1000,label:'desktop'}];
  for(const viewport of dimensions){
   await resize({width:viewport.width,height:viewport.height});const view=await chapter();views.push({label:viewport.label,state:view});const rect=await canvasRect();
   for(const point of corners()){const p=project(point,view,rect);expect(p.depth).toBeGreaterThan(.08);expect(Math.abs(p.nx)).toBeLessThan(1);expect(Math.abs(p.ny)).toBeLessThan(1);}
   await page.locator('#pj-stage').screenshot({path:info.outputPath(`gallery-${viewport.label}.png`)});
  }
  // Pick in landscape on the emulated phone so the narrow finite surfaces have useful screen area.
  for(const pick of galleryPicks){
   const view=await chapter(),record=galleryRecords.find(r=>r.nodeId===pick.nodeId);
   const initialProjection=project(pick.point,view,await canvasRect());
   // A landscape viewport is shorter than this existing canvas; keep the actual hit below the fixed header.
   await page.evaluate(y=>scrollBy({top:y-innerHeight*.65,behavior:'instant'}),initialProjection.y);
   const p=project(pick.point,view,await canvasRect());
   expect(p.depth).toBeGreaterThan(.08);expect(Math.abs(p.nx)).toBeLessThan(.98);expect(Math.abs(p.ny)).toBeLessThan(.98);
   expect(await page.evaluate(({x,y})=>document.elementFromPoint(x,y)?.id==='pj-canvas',p)).toBe(true);
   const start=await page.evaluate(()=>performance.now());if(touch)await page.touchscreen.tap(p.x,p.y);else await page.mouse.click(p.x,p.y);
   await expect(page.locator('#pj-note')).toBeVisible();await expect(page.locator('#pj-nt')).toHaveText(record.title);await expect(page.locator('#pj-nl [data-l="C"]')).toHaveCount(1);
   await expect.poll(()=>page.evaluate(({start,touch})=>['pointerdown','pointerup'].every(type=>luoyangEvidence.inputs.some(e=>e.time>=start&&e.type===type&&e.target==='pj-canvas'&&e.trusted&&(!touch||e.pointerType==='touch'))),{start,touch})).toBe(true);
   const inputs=await page.evaluate(start=>luoyangEvidence.inputs.filter(e=>e.time>=start&&e.target==='pj-canvas'),start),down=inputs.find(e=>e.type==='pointerdown'),up=inputs.find(e=>e.type==='pointerup');expect(up.pointerId).toBe(down.pointerId);expect(Math.hypot(up.clientX-down.clientX,up.clientY-down.clientY)).toBeLessThan(2);
   await expect.poll(()=>page.evaluate(({down,up,touch})=>galleryClicks.some(e=>e.time>=up.time&&e.trusted&&e.pointerId===down.pointerId&&(!touch||e.pointerType==='touch')&&Math.hypot(e.x-down.clientX,e.y-down.clientY)<2&&(e.path.includes('pj-canvas')||e.path.includes('pj-note'))),{down,up,touch})).toBe(true);
   await click(page.locator('#pj-x'));assertFullCity(await settled(page));
  }
  const beforeDrag=await chapter(),rect=await canvasRect(),started=await page.evaluate(()=>performance.now());
  if(touch){
   const session=await page.context().newCDPSession(page),p={x:rect.x+rect.width*.45,y:rect.y+rect.height*.55,id:1};
   try{await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]});for(let i=1;i<=12;i++){await page.waitForTimeout(16);await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...p,x:p.x+3*i,y:p.y+i}]});}await page.waitForTimeout(120);await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}finally{await session.detach();}
  }else{
   await page.mouse.move(rect.x+rect.width*.45,rect.y+rect.height*.55);await page.mouse.down();try{for(let i=1;i<=12;i++){await page.mouse.move(rect.x+rect.width*.45+3*i,rect.y+rect.height*.55+i);await page.waitForTimeout(16);}}finally{await page.mouse.up();}
  }
  await expect.poll(async()=>delta((await state(page)).position,beforeDrag.position)).toBeGreaterThan(.2);
  const moved=await settled(page);expect(moved.target).toEqual(beforeDrag.target);expect(moved.modelNodeIds).toEqual(expected);
  const samples=await page.evaluate(t=>luoyangEvidence.samples.filter(s=>s.time>=t),started);expect(samples.length).toBeGreaterThan(1);expect(samples.every(s=>s.target[1]===0)).toBe(true);await expect(page.locator('#pj-note')).toBeHidden();
  if(!touch){await page.mouse.wheel(0,120);await expect.poll(async()=>distance(await state(page))).toBeGreaterThan(distance(moved)*1.01);assertFullCity(await settled(page));}
  // Real product evidence switch: render change and exact restoration at one settled pose.
  await chapter();const stable=await state(page),plain=await page.locator('#pj-canvas').screenshot();
  await page.locator('#pj-tier').check();await align();const marked=await page.locator('#pj-canvas').screenshot();expect(marked.equals(plain)).toBe(false);
  await page.locator('#pj-tier').uncheck();await align();expect(await page.locator('#pj-canvas').screenshot()).toEqual(plain);
  expect((await state(page)).position).toEqual(stable.position);expect((await state(page)).target).toEqual(stable.target);
  await info.attach('gallery-evidence-off',{body:plain,contentType:'image/png'});await info.attach('gallery-evidence-on',{body:marked,contentType:'image/png'});
  if(touch){await resize({width:375,height:812});await chapter();await page.locator('#pj-stage').screenshot({path:info.outputPath('gallery-portrait-return.png')});}
  await selectZone(page,'Z14',touch);await selectZone(page,'Z23',touch);await align();await click(page.locator('.ly-overview'));
  await expect.poll(async()=>{const s=await state(page);return s.chapter==='city'&&!s.moving;}).toBe(true);
  const end=await settled(page);expect(end.position).toEqual(initial.position);expect(end.target).toEqual(initial.target);expect(end.modelNodeIds).toEqual(expected);expect(end.sceneRevision).toBe(initial.sceneRevision);expect(evidence.modelRequests).toEqual(requests);assertHealthy(evidence);
 }finally{await attachEvidence(page,info,evidence,{gl,http,views,galleryClicks:await page.evaluate(()=>window.galleryClicks||[]),budget:galleryRuntimeBudget});}
});
