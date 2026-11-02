'use strict';
(() => {
  const dataNode = document.querySelector('#variant-data');
  if (!dataNode) return;
  const stage = document.querySelector('#hero-plate');
  const poster = document.querySelector('#hero-image');
  const status = document.querySelector('#view-status');
  const switches = [...document.querySelectorAll('[data-variant]')];
  const error = document.querySelector('#hero-error');
  let variants;
  try { variants = JSON.parse(dataNode.textContent); } catch (_) { return; }
  if (!stage || !poster || !status || !variants.poise) return;
  let current = 'poise';
  let request = 0;
  let hasValidImage = !!(poster.complete && poster.naturalWidth > 0);
  const setStatus = message => { status.textContent = message; };
  poster.addEventListener('load', () => {
    hasValidImage = true;
    if (error) error.hidden = true;
    if (request === 0) setStatus('Poise / 平衡比例。已显示实际 Blender CPU 离线渲染；不是实时三维。');
  });
  poster.addEventListener('error', () => {
    hasValidImage = false;
    if (error) error.hidden = false;
    setStatus('首页图像未能载入；规格与下载仍可使用，可选择其他变体重试。');
  });
  if (poster.complete && !poster.naturalWidth) {
    if (error) error.hidden = false;
    setStatus('Poise 首页图像未能载入；规格与下载仍可使用，可选择其他变体重试。');
  }
  const select = id => {
    const item = variants[id];
    if (!item) return;
    const ownRequest = ++request;
    stage.setAttribute('aria-busy', 'true');
    setStatus(`正在载入 ${item.name} 的实际离线图；${hasValidImage ? '载入前保留上一张图。' : '规格与下载仍可使用。'}`);
    const next = new Image();
    next.onload = () => {
      if (ownRequest !== request) return;
      poster.src = item.image;
      poster.alt = item.alt;
      poster.hidden = false;
      if (error) error.hidden = true;
      document.querySelector('#hero-original').href = item.image;
      document.querySelector('#hero-name').textContent = item.name;
      document.querySelector('#hero-dimensions').textContent = item.dimensions;
      document.querySelector('#hero-model').href = item.model;
      document.querySelector('#hero-model').textContent = `下载 ${item.name} GLB ↓`;
      switches.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.variant === id)));
      current = id;
      hasValidImage = true;
      stage.setAttribute('aria-busy', 'false');
      setStatus(`${item.name} / ${item.character}。已显示实际 Blender CPU 离线渲染；不是实时三维。`);
    };
    next.onerror = () => {
      if (ownRequest !== request) return;
      stage.setAttribute('aria-busy', 'false');
      setStatus(`${item.name} 图像未能载入；${hasValidImage ? `保留 ${variants[current].name} 与已选规格。` : '首页尚无成功载入的图像，规格与下载仍可使用。'}可重试，或使用下方独立原图与模型下载。`);
    };
    next.src = item.image;
  };
  switches.forEach(b => {
    if (!variants[b.dataset.variant]) return;
    b.hidden = false;
    b.addEventListener('click', () => select(b.dataset.variant));
  });
  document.querySelectorAll('.js-only').forEach(el => { el.hidden = false; });
  document.querySelectorAll('img[data-error]').forEach(img => {
    const target = document.getElementById(img.dataset.error);
    const fail = () => { if (target) target.hidden = false; };
    img.addEventListener('error', fail);
    if (img.complete && !img.naturalWidth) fail();
  });
  const copy = document.querySelector('#copy-command');
  if (copy) copy.addEventListener('click', async () => {
    const message = document.querySelector('#copy-status');
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(document.querySelector('#reproduction-command').textContent);
      message.textContent = '命令已复制。请在已解压的配方根目录运行。';
    } catch (_) {
      message.textContent = '浏览器未允许复制；命令仍完整显示，可手动选中复制。';
    }
  });
})();
