import { expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import manifest from '../../docs/cities/luoyang/city-data.mjs';
const placedNodes = manifest.nodes.filter(n => n.space !== 'local-study' && !['U','X','unknown','excluded','未知','排除'].includes(n.tier ?? manifest.assets.find(a => a.id === n.asset)?.tier));
const replaced = new Set(placedNodes.flatMap(n => n.replaces || []));
const cityNodes = placedNodes.filter(n => !replaced.has(n.id));
export const cityNodeIds = cityNodes.map(n => n.id).sort();
export const cityModelPaths = [...new Set(cityNodes.map(n => new URL(manifest.assets.find(a => a.id === n.asset).url).pathname.split('/docs/')[1]))].sort();
export const zones = JSON.parse(readFileSync(new URL('../../docs/cities/luoyang/planning-zones.json', import.meta.url))).zones;
export const distance = s => Math.hypot(...s.position.map((v, i) => v - s.target[i]));
export const delta = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));
export const state = page => page.evaluate(() => window.luoyangEvidence.last);
export async function instrument(page) {
  const evidence = { modelRequests: [], pageErrors: [], consoleErrors: [], failedResponses: [], failedRequests: [] };
  page.on('request', r => { if (/\.glb(?:\?|$)/.test(r.url())) evidence.modelRequests.push(new URL(r.url()).pathname.slice(1)); });
  page.on('pageerror', e => evidence.pageErrors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') evidence.consoleErrors.push({ text: m.text(), url: m.location().url }); });
  page.on('response', r => { if (r.url().startsWith('http://127.0.0.1:8780/') && r.status() >= 400) evidence.failedResponses.push({ url: r.url(), status: r.status() }); });
  page.on('requestfailed', r => evidence.failedRequests.push({ url: r.url(), error: r.failure()?.errorText }));
  await page.addInitScript(() => {
    window.luoyangEvidence = { instance: crypto.randomUUID(), frames: 0, flights: 0, shows: [], inputs: [], cancellations: [], dispatched: [], last: null };
    const watched = new Set(['pointerdown','pointerup','touchstart','touchend','mousedown','mouseup','click']);
    const descriptor = Object.getOwnPropertyDescriptor(Event.prototype,'preventDefault');
    Object.defineProperty(Event.prototype,'preventDefault',{...descriptor,value:function(...args) {
      const before=this.defaultPrevented, result=Reflect.apply(descriptor.value,this,args);
      try {
        if(watched.has(this.type)) window.luoyangEvidence.cancellations.push({type:this.type,time:this.timeStamp,cancelable:this.cancelable,before,after:this.defaultPrevented,target:this.target?.id || this.target?.tagName,stack:new Error().stack});
      } catch {}
      return result;
    }});
    for(const type of watched) window.addEventListener(type,event=>{
      const entry={type,time:event.timeStamp,target:event.target?.dataset?.focus || event.target?.id || event.target?.tagName,cancelable:event.cancelable,trusted:event.isTrusted,clientX:event.clientX ?? event.changedTouches?.[0]?.clientX,clientY:event.clientY ?? event.changedTouches?.[0]?.clientY,scrollY};
      window.luoyangEvidence.dispatched.push(entry);
      setTimeout(()=>{entry.defaultPreventedAfter=event.defaultPrevented;entry.targetConnected=event.target?.isConnected;},0);
    },{capture:true,passive:true});
    for (const type of ['pointerdown','pointerup','pointercancel','touchstart','touchend','touchcancel','click']) {
      document.addEventListener(type, e => {
        const target = e.target.closest?.('button,canvas,select');
        if (!target && type !== 'click') return;
        window.luoyangEvidence.inputs.push({ type, target: target?.dataset.focus || target?.id || null, element: e.target.tagName, elementId: e.target.id, clientX: e.clientX ?? e.changedTouches?.[0]?.clientX, clientY: e.clientY ?? e.changedTouches?.[0]?.clientY, scrollY, time: e.timeStamp, pointerType: e.pointerType, pointerId: e.pointerId, isPrimary: e.isPrimary, defaultPrevented: e.defaultPrevented, trusted: e.isTrusted });
        if (window.luoyangEvidence.inputs.length > 80) window.luoyangEvidence.inputs.shift();
      }, true);
    }
    addEventListener('pageshow', e => window.luoyangEvidence.shows.push({ persisted: e.persisted }));
    document.addEventListener('luoyang-view-change', e => {
      window.luoyangEvidence.last = structuredClone(e.detail);
      window.luoyangEvidence.frames++;
      if (e.detail.moving) window.luoyangEvidence.flights++;
    }, true);
  });
  return evidence;
}
export async function openCity(page, touch = false) {
  await page.goto('/asset.html?id=p-luoyang', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#pj-stage')).toBeVisible();
  const open = page.locator('#pj-open');
  if (await open.count()) { if (touch) await open.tap(); else await open.click(); }
  await expect(page.locator('#pj-stage')).toHaveAttribute('data-state', 'ready');
  await settled(page);
  await expect(page.locator('[data-zone]')).toHaveCount(41);
  assertFullCity(await state(page));
  await assertSidebar(page);
  const gl = await page.locator('#pj-canvas').evaluate(canvas => {
    const ctx = canvas.getContext('webgl2');
    return { available: !!ctx && !ctx.isContextLost(), width: canvas.width, height: canvas.height, renderer: ctx?.getParameter(ctx.RENDERER) };
  });
  expect(gl.available).toBe(true);
  expect(gl.width).toBeGreaterThan(0);
  expect(gl.height).toBeGreaterThan(0);
  return gl;
}
export async function settled(page, zoneId) {
  await expect.poll(async () => {
    const s = await state(page);
    return !!s && !s.moving && (zoneId === undefined || s.zoneId === zoneId);
  }).toBe(true);
  const s = await state(page);
  expect([...s.position, ...s.target, s.compassDegrees].every(Number.isFinite)).toBe(true);
  expect(Math.abs(s.target[1])).toBeLessThan(1e-7);
  return s;
}
export async function selectZone(page, id, tap = false) {
  const n = Number(id.slice(1));
  await page.locator('#ly-zone-group').selectOption(n <= 18 ? 'base' : n <= 23 ? 'palace' : 'outer');
  const button = page.locator(`[data-zone="${id}"]`);
  if (tap) await button.tap(); else await button.click();
  const s = await settled(page, id);
  await expect(button).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#ly-zone-note')).toContainText('设计规划');
  return s;
}
export async function assertFits(page, zone, s) {
  const rect = await page.locator('#pj-canvas').boundingBox();
  const [e0,n0,e1,n1] = zone.bboxEN;
  expect(s.target[0]).toBeCloseTo((e0+e1)/2, 5);
  expect(s.target[2]).toBeCloseTo(-(n0+n1)/2, 5);
  const norm = v => v.map(n => n / Math.hypot(...v));
  const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const dot = (a,b) => a.reduce((sum,n,i) => sum+n*b[i],0);
  const forward = norm(s.target.map((n,i) => n-s.position[i]));
  const right = norm(cross(forward,[0,1,0])), up = cross(right,forward);
  const tan = Math.tan(38*Math.PI/360);
  for (const x of [e0,e1]) for (const y of [0,15]) for (const z of [-n0,-n1]) {
    const v = [x,y,z].map((n,i) => n-s.position[i]), depth = dot(v,forward);
    expect(depth).toBeGreaterThan(0);
    expect(Math.abs(dot(v,right)/(depth*tan*rect.width/rect.height))).toBeLessThan(1);
    expect(Math.abs(dot(v,up)/(depth*tan))).toBeLessThan(1);
  }
}
export async function drag(page) {
  const before = await state(page);
  await page.locator('#pj-canvas').scrollIntoViewIfNeeded();
  const box = await page.locator('#pj-canvas').boundingBox();
  await page.mouse.move(box.x+box.width*.4, box.y+box.height*.5);
  await page.mouse.down();
  await page.mouse.move(box.x+box.width*.65, box.y+box.height*.55, { steps: 8 });
  await page.mouse.up();
  await expect.poll(async () => delta((await state(page)).position, before.position)).toBeGreaterThan(1);
  return settled(page);
}
export async function attachEvidence(page, info, evidence, extra = {}) {
  const runtime = await page.evaluate(() => window.luoyangEvidence);
  await info.attach('browser-evidence', { body: JSON.stringify({ ...evidence, ...extra, runtime }, null, 2), contentType: 'application/json' });
  await page.locator('.ly-workspace').evaluate(el => el.scrollIntoView({ block: 'start', behavior: 'instant' }));
  await page.locator('#pj-stage').screenshot({ path: info.outputPath('city.png') });
  await page.locator('.ly-workspace').screenshot({ path: info.outputPath('sidebar.png') });
}
export function assertHealthy(evidence) {
  expect(evidence.pageErrors).toEqual([]);
  expect(evidence.failedResponses).toEqual([]);
  expect(evidence.consoleErrors).toEqual([]);
  expect(evidence.failedRequests.filter(r => r.error !== 'net::ERR_ABORTED')).toEqual([]);
}

export function assertFullCity(s) {
  expect(s.studyId).toBeNull();
  expect(s.modelNodeIds).toEqual(cityNodeIds);
  expect(s.modelNodeIds).toEqual(expect.arrayContaining(['market-main','market-N2','storage-main','ground-south','ground-D08','ground-network-ground-stitched']));
  expect(s.modelNodeIds.some(id => id.startsWith('research-'))).toBe(false);
}
export async function assertSidebar(page) {
  const sidebar = await page.locator('.ly-zone-bar').boundingBox();
  const stage = await page.locator('#pj-stage').boundingBox();
  expect(sidebar.x + sidebar.width).toBeLessThanOrEqual(stage.x);
  expect(Math.abs(sidebar.y-stage.y)).toBeLessThan(2);
  expect(Math.abs(sidebar.height-stage.height)).toBeLessThan(2);
  expect(stage.width).toBeGreaterThan(150);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
}
