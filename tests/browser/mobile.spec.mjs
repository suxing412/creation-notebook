import { test, expect } from '@playwright/test';
import { zones, distance, delta, state, instrument, openCity, settled, selectZone, assertFits, attachEvidence, assertHealthy, assertFullCity, assertSidebar } from './helpers.mjs';

test('touch entry, narrow layout, group navigation and orientation fitting', async ({ page }, info) => {
  const evidence = await instrument(page), gl = await openCity(page, true);
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
  await page.setViewportSize({ width: 812, height: 375 });
  const landscape = await selectZone(page, 'Z03', true);
  await assertFits(page, zones.find(z => z.id === 'Z03'), landscape);
  await page.setViewportSize({ width: 375, height: 812 });
  await expect.poll(async () => distance(await state(page))).toBeGreaterThan(distance(landscape));
  await assertFits(page, zones.find(z => z.id === 'Z03'), await settled(page, 'Z03'));
  await page.locator('#pj-canvas').scrollIntoViewIfNeeded();
  const box = await page.locator('#pj-canvas').boundingBox(), beforeTouch = await state(page);
  const session = await page.context().newCDPSession(page);
  const point = { x: box.x+box.width*.4, y: box.y+box.height*.5, id: 1 };
  await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [point] });
  await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: point.x+60, y: point.y+12, id: 1 }] });
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
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
  const overviewBox = await overviewButton.boundingBox();
  expect(await overviewButton.evaluate(el => { const r = el.getBoundingClientRect(); return el === document.elementFromPoint(r.x+r.width/2,r.y+r.height/2); })).toBe(true);
  // Ask Chromium to deliver one complete touch gesture (not a DOM click).
  // https://chromedevtools.github.io/devtools-protocol/tot/Input/#method-synthesizeTapGesture
  await session.send('Input.synthesizeTapGesture', { x: overviewBox.x+overviewBox.width/2, y: overviewBox.y+overviewBox.height/2, duration: 100, tapCount: 1, gestureSourceType: 'touch' });
  for (const type of ['pointerdown','pointerup']) {
    expect(await page.evaluate(type => window.luoyangEvidence.inputs.some(e => e.type === type && e.target === 'city' && e.pointerType === 'touch' && e.trusted),type)).toBe(true);
  }
  await expect.poll(async () => page.evaluate(() => window.luoyangEvidence.inputs.some(e => e.type === 'click' && e.target === 'city' && e.trusted))).toBe(true);
  const overview = await settled(page, null);
  expect(Math.abs(overview.compassDegrees)).toBeCloseTo(180, 5);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  assertHealthy(evidence);
  } finally {
    const viewport = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, scale: visualViewport?.scale, scrollY }));
    await attachEvidence(page, info, evidence, { gl, viewport, device: 'Chromium mobile emulation; not a physical phone' });
  }
});
