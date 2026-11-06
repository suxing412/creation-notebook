import { test, expect } from '@playwright/test';
import { instrument, openCity, state, settled, selectZone, delta, distance, assertFullCity, attachEvidence, assertHealthy } from './helpers.mjs';
const bearingDelta=(a,b)=>Math.abs(Math.atan2(Math.sin((a-b)*Math.PI/180),Math.cos((a-b)*Math.PI/180))*180/Math.PI);
const canvas=page=>page.locator('#pj-canvas');
async function workspace(page) {
  await page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
  return canvas(page).boundingBox();
}
async function wheel(page, amount) {
  const box=await workspace(page);
  await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);
  await page.mouse.wheel(0,amount);
}
function forward(s) {
  const x=s.target[0]-s.position[0], z=s.target[2]-s.position[2], n=Math.hypot(x,z);
  return [x/n,0,z/n];
}
async function assertBlurStop(page) {
  const count=await page.evaluate(()=>window.luoyangEvidence.blurs.length);
  await page.locator('#ly-zone-group').focus();
  await expect.poll(()=>page.evaluate(()=>window.luoyangEvidence.blurs.length)).toBe(count+1);
  const blur=await page.evaluate(()=>window.luoyangEvidence.blurs.at(-1)), atBlur=blur.state;
  await expect.poll(()=>page.evaluate(()=>window.luoyangEvidence.frames)).toBeGreaterThan(blur.frame);
  expect(atBlur).toBeTruthy();
  const stopped=await settled(page);
  expect(delta(stopped.position,atBlur.position)).toBeLessThan(1e-7);
  expect(delta(stopped.target,atBlur.target)).toBeLessThan(1e-7);
  await page.waitForTimeout(180);
  expect(delta((await state(page)).position,atBlur.position)).toBeLessThan(1e-7);
  expect(delta((await state(page)).target,atBlur.target)).toBeLessThan(1e-7);
  await canvas(page).focus();
  await page.waitForTimeout(120);
  expect((await state(page)).moving).toBe(false);
  const samples=await page.evaluate(frame=>window.luoyangEvidence.samples.filter(s=>s.frame>frame),blur.frame);
  expect(samples.length).toBeGreaterThan(0);
  for(const sample of samples) {
    expect(sample.moving).toBe(false);
    expect(delta(sample.position,atBlur.position)).toBeLessThan(1e-7);
    expect(delta(sample.target,atBlur.target)).toBeLessThan(1e-7);
  }
}

test('screen-relative keys, simultaneous mouse input, braking and immediate blur stop',async({page},info)=>{
  const evidence=await instrument(page); await openCity(page);
  const initial=await selectZone(page,'Z03'), requests=[...evidence.modelRequests];
  for(const key of ['w','d','s','a']) {
    await canvas(page).focus(); const before=await state(page), f=forward(before), r=[-f[2],0,f[0]];
    const direction=key==='w'?f:key==='s'?f.map(v=>-v):key==='d'?r:r.map(v=>-v);
    await page.keyboard.down(key);
    try { await expect.poll(async()=>delta((await state(page)).target,before.target)).toBeGreaterThan(2); }
    finally { await page.keyboard.up(key); }
    const after=await settled(page), travel=after.target.map((v,i)=>v-before.target[i]), n=Math.hypot(...travel);
    expect(travel.reduce((sum,v,i)=>sum+v*direction[i],0)/n).toBeGreaterThan(.999);
  }
  await canvas(page).focus();
  await page.keyboard.down('w');
  try {
    const before=await state(page);
    await expect.poll(async()=>delta((await state(page)).target,before.target)).toBeGreaterThan(2);
    const box=await workspace(page), turnedBefore=await state(page);
    await page.mouse.move(box.x+box.width*.4,box.y+box.height*.5);
    await page.mouse.down();
    await page.mouse.move(box.x+box.width*.6,box.y+box.height*.5,{steps:8});
    await page.mouse.up();
    await expect.poll(async()=>bearingDelta((await state(page)).compassDegrees,turnedBefore.compassDegrees)).toBeGreaterThan(5);
    await page.waitForTimeout(600);
    const afterDrag=await state(page);
    await expect.poll(async()=>delta((await state(page)).target,afterDrag.target)).toBeGreaterThan(2);
    expect((await state(page)).moving).toBe(true);
    const beforeWheel=await state(page); await wheel(page,-400);
    await expect.poll(async()=>distance(await state(page))).toBeLessThan(distance(beforeWheel)*.99);
    await page.waitForTimeout(600);
    const afterWheel=await state(page);
    await expect.poll(async()=>delta((await state(page)).target,afterWheel.target)).toBeGreaterThan(2);
    expect((await state(page)).moving).toBe(true);
  } finally { await page.keyboard.up('w'); }
  await settled(page);
  // Direction remains tied to the rendered heading after a substantial rotation.
  const rotated=await state(page), f=forward(rotated);
  await page.keyboard.down('w');
  try { await expect.poll(async()=>delta((await state(page)).target,rotated.target)).toBeGreaterThan(2); }
  finally { await page.keyboard.up('w'); }
  const after=await settled(page), travel=after.target.map((v,i)=>v-rotated.target[i]);
  expect(travel.reduce((sum,v,i)=>sum+v*f[i],0)/Math.hypot(...travel)).toBeGreaterThan(.999);
  await page.keyboard.down('w');
  try {
    await expect.poll(async()=>(await state(page)).moving).toBe(true);
    await assertBlurStop(page);
    const stopped=await state(page);
    await page.keyboard.down('w'); // Same physical key remains down: a trusted auto-repeat.
    await page.waitForTimeout(150);
    expect((await state(page)).moving).toBe(false);
    expect(delta((await state(page)).target,stopped.target)).toBeLessThan(1e-7);
  } finally { await page.keyboard.up('w'); }
  await wheel(page,-1000); await assertBlurStop(page);
  const dragBox=await workspace(page);
  await page.mouse.move(dragBox.x+dragBox.width*.4,dragBox.y+dragBox.height*.5);
  await page.mouse.down();
  try {
    await page.mouse.move(dragBox.x+dragBox.width*.5,dragBox.y+dragBox.height*.5,{steps:5});
    await assertBlurStop(page);
    const stopped=await state(page);
    await page.mouse.move(dragBox.x+dragBox.width*.6,dragBox.y+dragBox.height*.5,{steps:5});
    await page.waitForTimeout(150);
    expect(delta((await state(page)).position,stopped.position)).toBeLessThan(1e-7);
  } finally { await page.mouse.up(); }
  const beforeResume=await state(page); await wheel(page,-400);
  await expect.poll(async()=>distance(await state(page))).toBeLessThan(distance(beforeResume)*.99);
  await settled(page);
  await wheel(page,-30000);
  await expect.poll(async()=>distance(await state(page))).toBeCloseTo(5,4);
  const near=await settled(page);
  expect(distance(near)).toBeCloseTo(5,4);
  await wheel(page,30000);
  await expect.poll(async()=>distance(await state(page))).toBeGreaterThan(distance(near)*2);
  const far=await settled(page);
  expect(distance(far)).toBeCloseTo(20000,3);
  expect(delta(near.target,far.target)).toBeLessThan(1e-6);
  assertFullCity(far); expect(far.sceneRevision).toBe(initial.sceneRevision);
  expect(evidence.modelRequests).toEqual(requests);
  await page.locator('.ly-overview').click(); const reset=await settled(page,null);
  expect(bearingDelta(reset.compassDegrees,180)).toBeLessThan(1e-5);
  await attachEvidence(page,info,evidence,{checks:['direction','W+drag','W+wheel','blur','zoom limits']}); assertHealthy(evidence);
});

async function project(page,world) {
  const s=await state(page), box=await canvas(page).boundingBox(), stage=await page.locator('#pj-stage').boundingBox();
  const norm=v=>v.map(n=>n/Math.hypot(...v));
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const dot=(a,b)=>a.reduce((sum,n,i)=>sum+n*b[i],0);
  const f=norm(s.target.map((v,i)=>v-s.position[i])), right=norm(cross(f,[0,1,0])), up=cross(right,f);
  const v=world.map((n,i)=>n-s.position[i]), depth=dot(v,f), tan=Math.tan(38*Math.PI/360);
  const x=dot(v,right)/(depth*tan*stage.width/stage.height), y=dot(v,up)/(depth*tan);
  expect(depth).toBeGreaterThan(0); expect(Math.abs(x)).toBeLessThan(.9); expect(Math.abs(y)).toBeLessThan(.9);
  return {x:box.x+(x+1)*box.width/2,y:box.y+(1-y)*box.height/2};
}
test('an out-and-back drag never selects the courtyard beneath its starting point',async({page},info)=>{
  const evidence=await instrument(page); await openCity(page); await selectZone(page,'Z14'); await workspace(page);
  for(let i=0;i<12 && distance(await state(page))>1100;i++) { await wheel(page,-250); await settled(page); }
  const world=[717.730015807616,5.049999872843425,-982.1333320264201];
  let point=await project(page,world); await page.mouse.click(point.x,point.y);
  await expect(page.locator('#pj-nt')).toHaveText('住宅院落 01');
  await page.locator('#pj-x').click(); await expect(canvas(page)).toHaveCSS('opacity','1');
  point=await project(page,world);
  const startPose=await state(page);
  await page.mouse.move(point.x,point.y); await page.mouse.down();
  await page.mouse.move(point.x+45,point.y,{steps:5});
  await expect.poll(async()=>delta((await state(page)).position,startPose.position)).toBeGreaterThan(1);
  await page.mouse.move(point.x,point.y,{steps:5});
  // Wait while still held so pending damping cannot mask a broken trajectory guard.
  await expect.poll(async()=>{
    const current=await state(page);
    return !current.moving && delta(current.position,startPose.position)<1e-5;
  }).toBe(true);
  await page.mouse.up();
  await expect(page.locator('#pj-note')).not.toBeVisible();
  point=await project(page,world); await page.mouse.click(point.x,point.y);
  await expect(page.locator('#pj-nt')).toHaveText('住宅院落 01');
  await page.locator('#pj-x').click();
  await attachEvidence(page,info,evidence,{pick:{nodeId:'C02-018',world}}); assertHealthy(evidence);
});

test('blur invalidates a pending research navigation without moving or replacing the city',async({page},info)=>{
  const evidence=await instrument(page); let release,requested;
  const gate=new Promise(resolve=>{release=resolve;}), started=new Promise(resolve=>{requested=resolve;});
  await page.route('**/study-lingtai-*.glb',async route=>{requested();await gate;await route.continue();});
  await openCity(page); const before=await selectZone(page,'Z03');
  await page.locator('.pj-chapters [data-ch="ritual"]').click(); await started;
  await canvas(page).focus(); await page.locator('#ly-zone-group').focus();
  await expect.poll(async()=>(await state(page)).pendingSceneLoads).toBe(1);
  release();
  await expect.poll(async()=>(await state(page)).pendingSceneLoads).toBe(0);
  const after=await settled(page,'Z03'); assertFullCity(after);
  await expect(page.locator('#ly-zone-group')).toBeFocused();
  expect(after.sceneRevision).toBe(before.sceneRevision);
  expect(delta(after.position,before.position)).toBeLessThan(1e-7);
  expect(delta(after.target,before.target)).toBeLessThan(1e-7);
  await attachEvidence(page,info,evidence); assertHealthy(evidence);
});
