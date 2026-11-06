import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { instrument, openCity, state, settled, selectZone, distance, assertFullCity, assertHealthy, attachEvidence, cityNodeIds } from './helpers.mjs';
const models = JSON.parse(readFileSync(new URL('./installed-models.json', import.meta.url)));
const sha256 = body => createHash('sha256').update(body).digest('hex');

for (const model of models) {
  test(`${model.id}: every delivered variant renders with exact HTTP bytes`, async ({ page }, info) => {
    const evidence = await instrument(page), responses = [];
    async function variant(index, action) {
      const file = model.files[index];
      const responsePromise = page.waitForResponse(r => new URL(r.url()).pathname === `/${file.path}`);
      await action();
      const response = await responsePromise, body = await response.body();
      expect(response.status()).toBe(200);
      expect(body.length).toBe(file.bytes);
      expect(sha256(body)).toBe(file.sha256);
      await expect(page.locator('#vs')).toHaveText('');
      await expect(page.locator('#stage .vw-ui')).toHaveCount(1);
      await expect(page.locator('#vh canvas')).toHaveCount(1);
      expect(await page.locator('#vh canvas').evaluate(c => { const gl=c.getContext('webgl2');return !!gl && !gl.isContextLost() && c.width>0 && c.height>0; })).toBe(true);
      await expect(page.locator('[data-mode="3d"]')).toHaveAttribute('aria-pressed','true');
      await expect(page.locator('#pv-k')).toHaveText(file.label);
      await expect(page.locator('.vi span').filter({hasText:new RegExp(`^${model.materials} 材质$`)})).toHaveCount(1);
      responses.push({path:file.path,status:response.status(),bytes:body.length,sha256:sha256(body)});
      await page.locator('#stage').evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}));
      await page.locator('#stage').screenshot({path:info.outputPath(`variant-${index}.png`)});
    }
    await variant(0, () => page.goto(`/asset.html?id=${model.id}`, {waitUntil:'domcontentloaded'}));
    await expect(page.locator('h1')).toHaveText(model.title);
    await expect(page.locator('#variant option')).toHaveCount(model.files.length);
    for (let i=1;i<model.files.length;i++) await variant(i, () => page.locator('#variant').selectOption(String(i)));
    await page.locator('[data-mode="image"]').click();
    await expect(page.locator('#vh canvas')).toHaveCount(0);
    await variant(model.files.length-1, () => page.locator('[data-mode="3d"]').click());
    await info.attach('model-http-evidence',{body:JSON.stringify({responses,...evidence},null,2),contentType:'application/json'});
    assertHealthy(evidence);
  });
}

function project(point, view, rect, aspect) {
  const norm=v=>v.map(n=>n/Math.hypot(...v)), cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]], dot=(a,b)=>a.reduce((sum,n,i)=>sum+n*b[i],0);
  const forward=norm(view.target.map((n,i)=>n-view.position[i])), right=norm(cross(forward,[0,1,0])), up=cross(right,forward);
  const v=point.map((n,i)=>n-view.position[i]), depth=dot(v,forward), tan=Math.tan(38*Math.PI/360);
  return {x:rect.x+rect.width*(1+dot(v,right)/(depth*tan*aspect))/2,y:rect.y+rect.height*(1-dot(v,up)/(depth*tan))/2};
}

test('Z09-A and Z14 remain in the city, select by real geometry and keep evidence visible', async ({ page }, info) => {
  const evidence=await instrument(page),gl=await openCity(page);
  await page.emulateMedia({reducedMotion:'reduce'});
  expect(cityNodeIds).toHaveLength(72);
  const initial=await state(page);
  expect(initial.modelNodeIds).toEqual(expect.arrayContaining(['Z09-CIVIC-SERVICE-C01','Z14-WELL-COURT-C01']));
  expect(initial.modelNodeIds.some(id=>/z09.*(?:-B-|layout-B)/i.test(id))).toBe(false);
  const newRequests=evidence.modelRequests.filter(p=>/\/z09-civic-service-C01\/|\/z14-well-court-C01\//.test(p));
  expect(newRequests.sort()).toEqual(['cities/luoyang/progress-assets/z09-civic-service-C01/z09-civic-A-LOD2.glb','cities/luoyang/progress-assets/z14-well-court-C01/z14-well-court-far.glb']);
  const visits=[
    {zone:'Z09',point:[2226.75,4.529999923706055,-611.3499997456869],title:'官署附属文书与接待建筑组 · C级设计'},
    {zone:'Z14',point:[800,2.921666733423869,-1051.0300000309944],title:'住宅东缘开放井台 · C级设计'},
  ];
  for (const visit of visits) {
    const view=await selectZone(page,visit.zone);
    assertFullCity(view);expect(view.sceneRevision).toBe(initial.sceneRevision);
    await page.locator('.ly-workspace').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
    let rect=await page.locator('#pj-canvas').boundingBox();
    await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);
    for (let i=0;i<12 && distance(await state(page))>1100;i++) {
      const before=distance(await state(page));await page.mouse.wheel(0,-250);
      await expect.poll(async()=>distance(await state(page))).toBeLessThan(before*.99);
    }
    const close=await settled(page);rect=await page.locator('#pj-canvas').boundingBox();
    const stage=await page.locator('#pj-stage').boundingBox();
    const hit=project(visit.point,close,rect,stage.width/stage.height);
    expect(hit.x).toBeGreaterThan(rect.x);expect(hit.x).toBeLessThan(rect.x+rect.width);
    expect(hit.y).toBeGreaterThan(rect.y);expect(hit.y).toBeLessThan(rect.y+rect.height);
    await page.mouse.click(hit.x,hit.y);
    await expect(page.locator('#pj-note')).toBeVisible();
    await expect(page.locator('#pj-nt')).toHaveText(visit.title);
    await expect(page.locator('#pj-nl [data-l="C"]')).toHaveCount(1);
    await page.locator('#pj-x').click();
    await expect(page.locator('#pj-canvas')).toHaveCSS('opacity','1');
    const stable=await settled(page);
    const assertSameScene=async()=>{ const current=await state(page); for(const key of ['position','target','sceneRevision','modelNodeIds']) expect(current[key]).toEqual(stable[key]); };
    await assertSameScene();
    const plain=await page.locator('#pj-canvas').screenshot();
    const before=await page.evaluate(()=>window.luoyangEvidence.frames);
    await page.locator('#pj-tier').check();
    await expect.poll(()=>page.evaluate(()=>window.luoyangEvidence.frames)).toBeGreaterThan(before);
    await assertSameScene();
    const marked=await page.locator('#pj-canvas').screenshot();
    expect(sha256(marked)).not.toBe(sha256(plain));
    const markedFrame=await page.evaluate(()=>window.luoyangEvidence.frames);
    await page.locator('#pj-tier').uncheck();
    await expect.poll(()=>page.evaluate(()=>window.luoyangEvidence.frames)).toBeGreaterThan(markedFrame);
    await assertSameScene();
    expect(sha256(await page.locator('#pj-canvas').screenshot())).toBe(sha256(plain));
    assertFullCity(await state(page));
    await page.locator('.ly-workspace').screenshot({path:info.outputPath(`${visit.zone}-placed.png`)});
  }
  expect(evidence.modelRequests.filter(p=>/\/z09-civic-service-C01\/|\/z14-well-court-C01\//.test(p)).sort()).toEqual(newRequests);
  await page.locator('.pj-chapters [data-ch="ritual"]').click();
  await expect.poll(async()=>(await state(page)).studyId).toBe('research-lingtai');
  assertFullCity(await selectZone(page,'Z14'));
  await page.locator('.ly-overview').click();assertFullCity(await settled(page,null));
  await attachEvidence(page,info,evidence,{gl,placedModels:visits.map(v=>v.title)});
  assertHealthy(evidence);
});
