import { test, expect } from '@playwright/test';
import { zones, distance, delta, state, instrument, openCity, settled, selectZone, assertFits, attachEvidence, assertHealthy, assertFullCity, assertSidebar } from './helpers.mjs';

test('touch entry, narrow layout, group navigation and orientation fitting', async ({ page }, info) => {
  const evidence = await instrument(page), gl = await openCity(page, true);
  const session = await page.context().newCDPSession(page);
  let traceActive=false;
  async function finishInputTrace() {
    if(!traceActive) return;
    const completed=new Promise(resolve=>session.once('Tracing.tracingComplete',resolve));
    await session.send('Tracing.end');
    const result=await completed; traceActive=false;
    const chunks=[];
    while(true) { const chunk=await session.send('IO.read',{handle:result.stream}); chunks.push(Buffer.from(chunk.data,chunk.base64Encoded?'base64':'utf8')); if(chunk.eof) break; }
    await session.send('IO.close',{handle:result.stream});
    await info.attach('chromium-input-trace',{body:Buffer.concat(chunks),contentType:'application/json'});
    expect(result.dataLossOccurred).not.toBe(true);
  }
  try {
  await expect(page.locator('#pj-open')).toBeHidden();
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const id of ['Z18','Z23','Z41']) {
    const s = await selectZone(page, id, true);
    await assertFits(page, zones.find(z => z.id === id), s);
    assertFullCity(s);
    await assertSidebar(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  }
  await session.send('Tracing.start',{categories:'input,latencyInfo,devtools.timeline,blink.user_timing',transferMode:'ReturnAsStream'}); traceActive=true;
  await page.setViewportSize({ width: 812, height: 375 });
  const landscape = await selectZone(page, 'Z03', true);
  await assertFits(page, zones.find(z => z.id === 'Z03'), landscape);
  await page.setViewportSize({ width: 375, height: 812 });
  await expect.poll(async () => distance(await state(page))).toBeGreaterThan(distance(landscape));
  await assertFits(page, zones.find(z => z.id === 'Z03'), await settled(page, 'Z03'));
  await page.locator('#pj-canvas').scrollIntoViewIfNeeded();
  const box = await page.locator('#pj-canvas').boundingBox(), beforeTouch = await state(page);
  const point = { x: box.x+box.width*.4, y: box.y+box.height*.5, id: 1 };
  const dragStarted = await page.evaluate(() => performance.now());
  await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [point] });
  // Sample a real drag over half a second. A single instantaneous jump made
  // Chromium's emulator infer a 17,000 px/s fling instead of this 60 px drag.
  for (let step=1; step<=12; step++) {
    await page.waitForTimeout(40);
    await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: point.x+5*step, y: point.y+step, id: 1 }] });
  }
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  const dragEvents = await page.evaluate(start => window.luoyangEvidence.inputs.filter(e => e.time >= start && e.target === 'pj-canvas' && e.pointerType === 'touch'),dragStarted);
  const dragMoves = dragEvents.filter(e => e.type === 'pointermove' && e.trusted);
  expect(new Set(dragMoves.map(e => `${e.clientX},${e.clientY}`)).size).toBeGreaterThanOrEqual(3);
  expect(dragEvents.at(-1).time-dragEvents[0].time).toBeGreaterThanOrEqual(400);
  expect(Math.hypot(dragEvents.at(-1).clientX-dragEvents[0].clientX,dragEvents.at(-1).clientY-dragEvents[0].clientY)).toBeCloseTo(Math.hypot(60,12),3);
  await expect.poll(async () => delta((await state(page)).position,beforeTouch.position)).toBeGreaterThan(1);
  const manual = await settled(page);
  await page.setViewportSize({ width: 812, height: 375 });
  await page.waitForTimeout(250);
  expect(delta((await state(page)).position,manual.position)).toBeLessThan(1e-5);
  await page.setViewportSize({ width: 375, height: 812 });
  // Emulation resize resolves before the compositor necessarily presents the new orientation.
  await expect.poll(() => page.evaluate(() => [innerWidth, innerHeight, visualViewport.width, visualViewport.height])).toEqual([375,812,375,812]);
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await page.screenshot({ path: info.outputPath('portrait-before-overview.png') });
  const overviewButton = page.locator('.ly-overview');
  // Bring the side controls below the fixed site header after orientation changes.
  await page.locator('.ly-workspace').evaluate(el => el.scrollIntoView({ block: 'start', behavior: 'instant' }));
  // The browser's compositor must present the scroll before a raw CDP tap.
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await page.screenshot({ path: info.outputPath('overview-touch-target.png') });
  expect(await overviewButton.evaluate(el => { const r = el.getBoundingClientRect(); return el === document.elementFromPoint(r.x+r.width/2,r.y+r.height/2); })).toBe(true);
  // Use the same touchscreen path as every preceding successful zone tap.
  // Aura's debugger synthesizeTapGesture bypasses its gesture recognizer.
  const overviewStarted = await page.evaluate(()=>{performance.mark('overview-touch-start');return performance.now();});
  await overviewButton.tap();
  for (const type of ['pointerdown','pointerup']) {
    expect(await page.evaluate(({type,start}) => window.luoyangEvidence.inputs.some(e => e.time >= start && e.type === type && e.target === 'city' && e.pointerType === 'touch' && e.trusted),{type,start:overviewStarted})).toBe(true);
  }
  await expect.poll(async () => page.evaluate(start => window.luoyangEvidence.inputs.some(e => e.time >= start && e.type === 'click' && e.target === 'city' && e.trusted),overviewStarted)).toBe(true);
  await page.evaluate(()=>performance.mark('overview-touch-end'));
  await finishInputTrace();
  const overview = await settled(page, null);
  expect(Math.abs(overview.compassDegrees)).toBeCloseTo(180, 5);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  assertHealthy(evidence);
  } finally {
    await finishInputTrace();
    const viewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, scale: visualViewport?.scale, scrollY }));
    await attachEvidence(page, info, evidence, { gl, viewport, device: 'Chromium mobile emulation; not a physical phone' });
  }
});
