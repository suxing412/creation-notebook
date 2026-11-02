/* Progressive enhancement: only real image plates; the full editorial is static HTML. */
(() => {
  'use strict';
  const data = document.getElementById('image-data');
  const target = document.getElementById('hero-image');
  const controls = document.querySelector('.image-controls');
  if (!data || !target || !controls) return;
  let views;
  try { views = JSON.parse(data.textContent); } catch { return; }
  if (!Array.isArray(views) || !views.length || views.some(v => !v.id || !v.src || !v.alt || !v.caption)) return;
  const buttons = [...controls.querySelectorAll('button[data-view]')];
  const caption = document.getElementById('hero-caption');
  const original = document.getElementById('hero-original');
  const status = document.getElementById('image-status');
  const unavailable = document.getElementById('image-unavailable');
  const retry = document.getElementById('image-retry');
  let current = views[0], pending = null, serial = 0, hasCommitted = false, valid = target.complete && target.naturalWidth > 0;
  function showUnavailable() { unavailable.hidden = valid; target.classList.toggle('failed-image', !valid); }
  function initialState() {
    if (hasCommitted) return;
    valid = target.complete && target.naturalWidth > 0;
    showUnavailable();
    // Initial HTML image may finish while a different plate is pending.
    // Track its real success without replacing the pending request's status.
    if (serial !== 0) return;
    if (!valid) {
      pending = current; retry.hidden = false;
      status.textContent = '整体图未能加载。可重试或选择其他图版；下方路径图和资料不受影响。';
    }
  }
  target.addEventListener('load', initialState);
  target.addEventListener('error', initialState);
  if (target.complete) initialState();
  async function select(id) {
    const next = views.find(v => v.id === id);
    if (!next) return;
    if (valid && next.id === current.id && !pending) return;
    const ticket = ++serial; pending = next;
    status.textContent = `正在加载${next.label}…`;
    controls.setAttribute('aria-busy','true'); retry.hidden = true;
    const probe = new Image();
    try {
      await new Promise((resolve,reject) => { probe.onload = resolve; probe.onerror = reject; probe.src = next.src; });
      if (ticket !== serial) return;
      if (!probe.naturalWidth) throw new Error('Empty image');
      target.src = next.src; target.alt = next.alt;
      caption.textContent = next.caption; original.href = next.src;
      current = next; pending = null; hasCommitted = true; valid = true; showUnavailable();
      for (const b of buttons) b.setAttribute('aria-pressed', String(b.dataset.view === next.id));
      document.querySelector('.hero-stage .plate-id').textContent = `A / FOLIO · ${next.label}`;
      status.textContent = `已显示${next.label}。`;
    } catch {
      if (ticket !== serial) return;
      showUnavailable();
      status.textContent = valid ? `${next.label}加载失败，仍显示${current.label}；原图链接与图注未改变。可重试或选择其他图版。` : `${next.label}加载失败，目前没有成功加载的主图。下方图解仍可阅读；可重试或选择其他图版。`;
      retry.hidden = false;
    } finally {
      if (ticket === serial) controls.removeAttribute('aria-busy');
    }
  }
  for (const b of buttons) b.addEventListener('click', () => select(b.dataset.view));
  retry.addEventListener('click', () => select((pending || current).id));
  controls.hidden = false;
})();
