import { test, expect } from '@playwright/test';
import { zones, distance, delta, state, instrument, openCity, settled, selectZone, assertFits, drag, attachEvidence, assertHealthy } from './helpers.mjs';

test('first load, all 41 zones, flight, controls and compass', async ({ page }, info) => {
  const evidence = await instrument(page), gl = await openCity(page);
  const overview = await state(page);
  expect(overview.chapter).toBe('city');
  expect(overview.position[2]).toBeLessThan(overview.target[2]);
  expect(Math.abs(overview.compassDegrees)).toBeCloseTo(180, 5);
  await selectZone(page, 'Z03');
  expect(await page.evaluate(() => window.luoyangEvidence.flights)).toBeGreaterThan(0);
  // Visit every planning region, including every group and lazily loaded existing asset.
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const zone of zones) await assertFits(page, zone, await selectZone(page, zone.id));
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await selectZone(page, 'Z03');
  const before = await state(page), rotated = await drag(page);
  expect(delta(rotated.position, before.position)).toBeGreaterThan(1);
  expect(delta(rotated.target, before.target)).toBeLessThan(1e-5);
  expect(Math.abs(rotated.compassDegrees-before.compassDegrees)).toBeGreaterThan(1);
  const bearing = await page.locator('.ly-compass').evaluate(el => parseFloat(el.style.getPropertyValue('--bearing')));
  expect(bearing).toBeCloseTo(rotated.compassDegrees, 5);
  await page.mouse.wheel(0, -400);
  await expect.poll(async () => distance(await state(page))).toBeLessThan(distance(rotated)*.99);
  const zoomed = await settled(page);
  expect(delta(zoomed.target, rotated.target)).toBeLessThan(1e-5);
  for (const key of ['w','a','s','d']) {
    const start = await state(page);
    await page.locator('#pj-canvas').focus();
    await page.keyboard.down(key);
    await expect.poll(async () => delta((await state(page)).target,start.target)).toBeGreaterThan(1);
    await page.keyboard.up(key);
    const stopped = await settled(page);
    await page.waitForTimeout(150);
    expect(delta((await state(page)).target,stopped.target)).toBeLessThan(1e-5);
  }
  await page.keyboard.down('w');
  await expect.poll(async () => (await state(page)).moving).toBe(true);
  await page.locator('#ly-zone-group').focus();
  const blurred = await settled(page);
  await page.waitForTimeout(150);
  expect(delta((await state(page)).target,blurred.target)).toBeLessThan(1e-5);
  await page.keyboard.up('w');
  await page.locator('#ly-planning').uncheck();
  await expect.poll(async () => (await state(page)).overlayVisible).toBe(false);
  await page.locator('#ly-planning').check();
  await page.locator('#pj-canvas').focus();
  await page.keyboard.press('r');
  const reset = await settled(page, null);
  expect(reset.chapter).toBe('city');
  expect(Math.abs(reset.compassDegrees)).toBeCloseTo(180, 5);
  await page.locator('[data-zone="Z03"]').click();
  await page.locator('[data-zone="Z04"]').click();
  await page.locator('[data-zone="Z14"]').click();
  await settled(page, 'Z14');
  await page.locator('.ly-overview').click();
  await settled(page, null);
  await attachEvidence(page, info, evidence, { gl, visitedZones: zones.map(z => z.id) });
  assertHealthy(evidence);
});

test('late asset completion cannot override manual navigation', async ({ page }, info) => {
  const evidence = await instrument(page);
  let release, started;
  const gate = new Promise(resolve => { release = resolve; });
  const requested = new Promise(resolve => { started = resolve; });
  await page.route('**/market-cluster.glb', async route => { started(); await gate; await route.continue(); });
  await openCity(page);
  await selectZone(page, 'Z03');
  await page.locator('[data-zone="Z13"]').click();
  await requested;
  const manual = await drag(page);
  expect(manual.zoneId).toBe('Z03');
  const response = page.waitForResponse('**/market-cluster.glb');
  release();
  await response;
  await expect(page.locator('#pj-status')).toContainText('此视图暂不能打开，当前画面保持。');
  const after = await settled(page, 'Z03');
  expect(delta(after.position,manual.position)).toBeLessThan(1e-5);
  expect(delta(after.target,manual.target)).toBeLessThan(1e-5);
  await selectZone(page, 'Z13');
  await attachEvidence(page, info, evidence);
  assertHealthy(evidence);
});

test('failed lazy model keeps the current view and retries', async ({ page }, info) => {
  const evidence = await instrument(page);
  let fail = true, attempts = 0;
  await page.route('**/granary-city-LOD0.glb', route => {
    attempts++;
    return fail ? route.fulfill({ status: 503, body: 'intentional browser-test failure' }) : route.continue();
  });
  await openCity(page);
  const before = await selectZone(page, 'Z03');
  await page.locator('[data-zone="Z06"]').click();
  await expect(page.locator('#pj-status')).toContainText('失败');
  expect((await state(page)).zoneId).toBe('Z03');
  expect(delta((await state(page)).position,before.position)).toBeLessThan(1e-5);
  fail = false;
  await selectZone(page, 'Z06');
  expect(attempts).toBeGreaterThanOrEqual(2);
  await attachEvidence(page, info, evidence, { intentionalFailure: 'granary-city-LOD0.glb:503', attempts });
  const expected = r => r.url.endsWith('/granary-city-LOD0.glb') && r.status === 503;
  expect(evidence.failedResponses.filter(expected).length).toBeGreaterThanOrEqual(1);
  assertHealthy({ ...evidence,
    failedResponses: evidence.failedResponses.filter(r => !expected(r)),
    consoleErrors: evidence.consoleErrors.filter(r => !(r.url.endsWith('/granary-city-LOD0.glb') && /503/.test(r.text))),
  });
});

test('research view returns to the city and history return stays interactive', async ({ page, context }, info) => {
  const evidence = await instrument(page), reasons = [];
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  cdp.on('Page.backForwardCacheNotUsed', event => reasons.push(event));
  await openCity(page);
  await page.locator('.pj-chapters [data-ch="ritual"]').click();
  await expect.poll(async () => (await state(page)).studyId).not.toBeNull();
  await selectZone(page, 'Z03');
  expect((await state(page)).studyId).toBeNull();
  const instance = await page.evaluate(() => window.luoyangEvidence.instance);
  await page.locator('.crumbs a').first().click();
  await page.waitForURL('**/index.html');
  await page.goBack({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('#pj-stage')).toHaveAttribute('data-state', 'ready');
  await settled(page);
  const history = await page.evaluate(() => ({ instance: window.luoyangEvidence.instance, shows: window.luoyangEvidence.shows }));
  const bfcacheRestored = history.instance === instance && history.shows.some(s => s.persisted);
  await selectZone(page, 'Z14');
  await drag(page);
  await attachEvidence(page, info, evidence, { history, bfcacheRestored, bfcacheNotUsedReasons: reasons });
  // A normal reload proves functional history return, not BFCache restoration; report the distinction.
  assertHealthy(evidence);
});
