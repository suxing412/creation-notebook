import {displayGroundId} from '../../docs/cities/luoyang/ground-content.mjs';
import { galleryRecords } from '../../docs/cities/luoyang/gallery-records.mjs';
import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { instrument, openCity, state, settled, selectZone, delta, distance, drag, assertFullCity, assertHealthy, attachEvidence } from './helpers.mjs';
import { z13NodeIds } from '../../docs/cities/luoyang/z13-content.mjs';
const fixture=JSON.parse(readFileSync(new URL('./yong-access.json',import.meta.url)));
const norm=v=>v.map(x=>x/Math.hypot(...v));
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function projection(point,view,aspect) {
  const forward=norm(view.target.map((x,i)=>x-view.position[i]));
  const right=norm(cross(forward,[0,1,0])),up=cross(right,forward);
  const q=point.map((x,i)=>x-view.position[i]),depth=dot(q,forward),tan=Math.tan(38*Math.PI/360);
  return {x:dot(q,right)/(depth*tan*aspect),y:dot(q,up)/(depth*tan),depth};
}
async function fitted(page) {
  const view=await settled(page),rect=await page.locator('#pj-stage').boundingBox();
  expect(view.chapter).toBe('yong-gate');assertFullCity(view);
  expect(view.target).toEqual(fixture.groundPose.target);
  const direction=norm(view.position.map((x,i)=>x-view.target[i]));
  const original=norm(fixture.groundPose.position.map((x,i)=>x-fixture.groundPose.target[i]));
  expect(delta(direction,original)).toBeLessThan(1e-7);
  expect(distance(view)).toBeGreaterThanOrEqual(distance(fixture.groundPose)-1e-7);
  for(const x of [fixture.chapterRuntimeBounds.min[0],fixture.chapterRuntimeBounds.max[0]])
    for(const y of [fixture.chapterRuntimeBounds.min[1],fixture.chapterRuntimeBounds.max[1]])
      for(const z of [fixture.chapterRuntimeBounds.min[2],fixture.chapterRuntimeBounds.max[2]]) {
        const p=projection([x,y,z],view,Math.floor(rect.width)/Math.floor(rect.height));
        expect(p.depth).toBeGreaterThan(.08);expect(Math.abs(p.x)).toBeLessThan(1);expect(Math.abs(p.y)).toBeLessThan(1);
      }
  return view;
}
async function freshAction(page,action) {
  const before=await page.evaluate(()=>window.luoyangEvidence.frames);
  await action();
  await expect.poll(()=>page.evaluate(()=>window.luoyangEvidence.frames)).toBeGreaterThan(before);
  return settled(page);
}

async function resizeAndSettle(page,viewport) {
  const serial=await page.evaluate(()=>window.yongResizeSerial||0);
  await page.setViewportSize(viewport);
  await expect.poll(()=>page.evaluate(({viewport,serial})=>{
    const r=window.yongResizeFrame;
    return !!r && r.serial>serial && r.viewport[0]===viewport.width && r.viewport[1]===viewport.height &&
      r.visual[0]===viewport.width && r.visual[1]===viewport.height &&
      r.buffer[0]===Math.floor(r.stage[0]*r.pixelRatio) && r.buffer[1]===Math.floor(r.stage[1]*r.pixelRatio) && !r.state.moving;
  },{viewport,serial})).toBe(true);
  return settled(page);
}

test('Yong access stays installed, fits the chapter after orientation changes and picks real geometry',async({page},info)=>{
  const touch=info.project.name==='mobile',evidence=await instrument(page),views=[];
  await page.addInitScript(()=>{
  window.yongPickClicks=[];
  document.addEventListener('click',event=>{
    window.yongPickClicks.push({time:event.timeStamp,trusted:event.isTrusted,pointerId:event.pointerId,
      pointerType:event.pointerType,x:event.clientX,y:event.clientY,path:event.composedPath().map(el=>el.id).filter(Boolean)});
  },true);
  document.addEventListener('luoyang-view-change',event=>{
    const canvas=event.target,rect=canvas.parentElement.getBoundingClientRect();
    window.yongResizeFrame={serial:window.yongResizeSerial=(window.yongResizeSerial||0)+1,viewport:[innerWidth,innerHeight],
      visual:[visualViewport.width,visualViewport.height],stage:[Math.floor(rect.width),Math.floor(rect.height)],
      buffer:[canvas.width,canvas.height],pixelRatio:Math.min(devicePixelRatio||1,1.5),state:structuredClone(event.detail)};
  },true);
  });
  const gl=await openCity(page,touch);
  await page.emulateMedia({reducedMotion:'reduce'});
  const initial=await state(page);
  expect(initial.modelNodeIds).toEqual([...fixture.previousCityNodeIds,fixture.id,...z13NodeIds,...galleryRecords.map(r=>r.nodeId),displayGroundId].sort());
  expect(initial.modelNodeIds).toHaveLength(87);
  const chapter=page.locator('.pj-chapters [data-ch="yong-gate"]');
  const click=locator=>touch?locator.tap():locator.click();
  async function openChapter() {
    await selectZone(page,'Z14',touch);
    await freshAction(page,()=>click(chapter));
    await expect.poll(async()=>{const s=await state(page);return s.chapter==='yong-gate'&&s.zoneId===null&&!s.moving;}).toBe(true);
    return fitted(page);
  }
  try {
    views.push(await openChapter());
    if(!touch) expect(delta(views[0].position,fixture.groundPose.position)).toBeLessThan(1e-7);
    for(const viewport of [{width:375,height:812},{width:812,height:375},{width:375,height:812}]) {
      if(page.viewportSize().width!==viewport.width) await resizeAndSettle(page,viewport);
      views.push(await fitted(page));
    }
    expect(delta(views[1].position,views[3].position)).toBeLessThan(1e-7);
    expect(distance(views[1])).toBeGreaterThan(distance(views[2]));
    expect(delta(views[2].position,fixture.groundPose.position)).toBeLessThan(1e-7);
    await page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
    const view=await settled(page),rect=await page.locator('#pj-canvas').boundingBox(),stage=await page.locator('#pj-stage').boundingBox();
    const hit=projection(fixture.pickPoint,view,Math.floor(stage.width)/Math.floor(stage.height));
    expect(Math.abs(hit.x)).toBeLessThan(1);expect(Math.abs(hit.y)).toBeLessThan(1);
    const x=rect.x+rect.width*(1+hit.x)/2,y=rect.y+rect.height*(1-hit.y)/2;
    const started=await page.evaluate(()=>performance.now());
    if(touch) await page.touchscreen.tap(x,y);else await page.mouse.click(x,y);
    await expect(page.locator('#pj-note')).toBeVisible();
    await expect(page.locator('#pj-nt')).toHaveText(fixture.title);
    await expect(page.locator('#pj-nl [data-l="C"]')).toHaveCount(1);
    for(const type of ['pointerdown','pointerup']) {
      await expect.poll(()=>page.evaluate(({started,type,touch})=>window.luoyangEvidence.inputs.some(e=>
        e.time>=started&&e.target==='pj-canvas'&&e.type===type&&e.trusted&&(!touch||e.pointerType==='touch')),
        {started,type,touch})).toBe(true);
    }
    const chain=await page.evaluate(started=>window.luoyangEvidence.inputs.filter(e=>e.time>=started&&e.target==='pj-canvas'),started);
    const down=chain.find(e=>e.type==='pointerdown'),up=chain.find(e=>e.type==='pointerup');
    expect(up.pointerId).toBe(down.pointerId);
    expect(Math.hypot(up.clientX-down.clientX,up.clientY-down.clientY)).toBeLessThan(2);
    // Selection happens on pointerup. Its note can cover the hit point before the
    // browser's trusted compatibility click (observed on mobile in run 42267665826).
    await expect.poll(()=>page.evaluate(({down,up,touch})=>window.yongPickClicks.some(e=>
      e.time>=up.time&&e.trusted&&e.pointerId===down.pointerId&&(!touch||e.pointerType==='touch')&&
      Math.hypot(e.x-down.clientX,e.y-down.clientY)<2&&(e.path.includes('pj-canvas')||e.path.includes('pj-note'))),
      {down,up,touch})).toBe(true);
    await click(page.locator('#pj-x'));
    await page.locator('.ly-workspace').screenshot({path:info.outputPath('yong-portrait-installed.png')});
    // A manual gesture relinquishes automatic chapter fitting; resize must not jump.
    for(const action of touch?['touch','blur']:['drag','wheel','keys','blur']) {
      await openChapter();
      await page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
      const canvas=page.locator('#pj-canvas'),box=await canvas.boundingBox(),before=await state(page);
      if(action==='drag') await drag(page);
      if(action==='wheel') {
        await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.wheel(0,-120);
        await expect.poll(async()=>distance(await state(page))).toBeLessThan(distance(before)*.99);
      }
      if(action==='keys') {
        await canvas.focus();await page.keyboard.down('w');
        try {await expect.poll(async()=>delta((await state(page)).target,before.target)).toBeGreaterThan(.5);}
        finally {await page.keyboard.up('w');}
      }
      if(action==='touch') {
        const session=await page.context().newCDPSession(page),p={x:box.x+box.width*.4,y:box.y+box.height*.5,id:1};
        await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[p]});
        for(let i=1;i<=12;i++){await page.waitForTimeout(40);await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...p,x:p.x+4*i,y:p.y+i}]});}
        await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach();
        await expect.poll(async()=>delta((await state(page)).position,before.position)).toBeGreaterThan(1);
      }
      if(action==='blur') {await canvas.focus();await page.locator('#ly-zone-group').focus();}
      const manual=await settled(page);
      const resized=await resizeAndSettle(page,{width:812,height:375});
      expect(delta(resized.position,manual.position)).toBeLessThan(1e-7);expect(delta(resized.target,manual.target)).toBeLessThan(1e-7);
      const returned=await resizeAndSettle(page,{width:375,height:812});
      expect(delta(returned.position,manual.position)).toBeLessThan(1e-7);expect(delta(returned.target,manual.target)).toBeLessThan(1e-7);
    }
    assertFullCity(await selectZone(page,'Z14',touch));
    await click(page.locator('.ly-overview'));assertFullCity(await settled(page,null));
    expect((await state(page)).sceneRevision).toBe(initial.sceneRevision);
    expect(evidence.modelRequests.filter(p=>p.includes('/yong-upper-access-C-v1_1/'))).toEqual([fixture.defaultPath]);
    assertHealthy(evidence);
  } finally {await attachEvidence(page,info,evidence,{gl,views,fixture,pickClicks:await page.evaluate(()=>window.yongPickClicks),device:touch?'Chromium mobile emulation; not a physical phone':'Chromium SwiftShader; not hardware GPU'});}
});
