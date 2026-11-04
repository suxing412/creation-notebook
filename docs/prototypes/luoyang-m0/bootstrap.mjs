// Keep the poster-only mobile path free of Three.js and model requests.
const $ = (selector) => document.querySelector(selector);
let canvas = $('#scene');
const poster = $('#poster');
const stage = $('#stage');
const startButton = $('#start3d');
const closeButton = $('#close3d');
const status = $('#status');
const error = $('#error');
const controls = $('#live-controls');
const metrics = $('#metrics');
const lineWidthInput = $('#line-width');
const paperStrengthInput = $('#paper-strength');
const mobile = matchMedia('(max-width:700px), (pointer:coarse)');
const modelUrl = new URL('../../cities/luoyang/assets/r01/R01-A-LOD0-prototype.glb', import.meta.url).href;
const query = new URLSearchParams(location.search);
const validMethod = ['compare', 'hull', 'edge'].includes(query.get('method'));
const options = {
  method: validMethod ? query.get('method') : mobile.matches ? 'edge' : 'compare',
  brush: query.get('brush') === 'pencil' ? 'pencil' : 'ink',
  lineWidth: Number(lineWidthInput.value),
  paperStrength: Number(paperStrengthInput.value),
};

let generation = 0;
let controller = null;
let prototype = null;
let phase = 'poster';
let explicitlyOpened = false;
let deliberatelyClosed = false;
let lastMetrics = null;
let readyAt = null;
let resourceObserver = null;
let pendingCreation = Promise.resolve();

// The budget counts file bodies as well as actual transfer: a warm cache is
// useful to visitors, but must not make an oversized cold load appear free.
function resourceTotals() {
  if (readyAt === null) return null;
  const entries = [
    ...performance.getEntriesByType('navigation'),
    ...performance.getEntriesByType('resource'),
  ].filter((entry) => entry.startTime <= readyAt && entry.responseEnd > 0);
  const totals = { body: 0, transfer: 0, count: entries.length, unknown: 0 };
  for (const entry of entries) {
    totals.body += entry.encodedBodySize || 0;
    totals.transfer += entry.transferSize || 0;
    if (!entry.encodedBodySize && !entry.transferSize) totals.unknown += 1;
  }
  return totals;
}

const megabytes = (bytes) => `${(bytes / 1_000_000).toFixed(2)} MB`;
const integer = (value) => Number.isFinite(value) ? Math.round(value).toLocaleString('zh-CN') : '—';

function updateMetrics() {
  const lines = ['M0 · 单座住宅院落实测'];
  if (lastMetrics) {
    const methodLabel = { compare: '并排比较', hull: '反向外壳', edge: '边缘检测' }[lastMetrics.method];
    lines.push(`已绘制画面 · ${lastMetrics.brush === 'pencil' ? '铅笔淡彩' : '墨线实色'} · ${methodLabel}`);
    for (const [key, label] of [['hull', '反向外壳'], ['edge', '边缘检测']]) {
      const sample = lastMetrics.methods?.[key];
      lines.push(sample
        ? `${label}：${integer(sample.drawCalls)} 次绘制 · ${integer(sample.triangles)} 个三角形`
        : `${label}：尚未运行`);
    }
    if (lastMetrics.bufferWidth && lastMetrics.bufferHeight) {
      lines.push(`绘制缓冲：${integer(lastMetrics.bufferWidth)} × ${integer(lastMetrics.bufferHeight)} · 像素比 ${Number(lastMetrics.pixelRatio).toFixed(2)}`);
    }
    if (lastMetrics.methods?.edge && lastMetrics.edgeBufferWidth && lastMetrics.edgeBufferHeight) {
      lines.push(`描边内部缓冲 · ${integer(lastMetrics.edgeBufferWidth)} × ${integer(lastMetrics.edgeBufferHeight)} · 线性降采样抗锯齿`);
    }
    if (Number.isFinite(lastMetrics.downloadBytes)) lines.push(`院落模型：${megabytes(lastMetrics.downloadBytes)}`);
  } else {
    lines.push('打开 3D 后显示本机数据。');
  }
  const resources = resourceTotals();
  if (resources) {
    lines.push(`进入交互前发起的资源：${megabytes(resources.body)} 文件体积 · ${megabytes(resources.transfer)} 实际传输`);
    lines.push(`已完成 ${resources.count} 项，含 HTML、脚本、字体与图片；此前发起而尚未完成的请求会继续补记。`);
    lines.push(`下载预算 8 MB：${resources.body > 8_000_000 ? '已超出' : resources.unknown ? '有未能计量的资源，请结合网络面板核查' : '已计量部分在预算内'}`);
    if (resources.unknown) lines.push(`${resources.unknown} 项未返回字节大小；缓存命中时实际传输可能为 0。`);
  } else {
    lines.push('尚未进入交互，下载统计待记录。');
  }
  lines.push('全城目标：鸟瞰 ≤ 300 次绘制、≤ 150 万三角形。');
  lines.push('当前统计范围为一座院落。全城与集显 30 fps 将在规模化阶段验收。');
  metrics.textContent = lines.join('\n');
}

function syncOptions() {
  stage.dataset.method = options.method;
  for (const button of document.querySelectorAll('[data-method]')) {
    if (button.tagName === 'BUTTON') button.setAttribute('aria-pressed', String(button.dataset.method === options.method));
  }
  for (const button of document.querySelectorAll('button[data-brush]')) {
    button.setAttribute('aria-pressed', String(button.dataset.brush === options.brush));
  }
  const widthOutput = $('#line-width-value');
  const paperOutput = $('#paper-strength-value');
  if (widthOutput) widthOutput.textContent = `${options.lineWidth.toFixed(1)} px`;
  if (paperOutput) paperOutput.textContent = `${Math.round(options.paperStrength * 100)}%`;
  prototype?.setOptions(options);
}

function showPoster(message) {
  phase = 'poster';
  stage.dataset.state = 'poster';
  poster.hidden = false;
  canvas.hidden = true;
  canvas.style.visibility = '';
  controls.disabled = true;
  startButton.hidden = false;
  startButton.disabled = false;
  startButton.textContent = '打开 3D 画风对照';
  closeButton.hidden = true;
  stage.removeAttribute('aria-busy');
  if (message) status.textContent = message;
}

function dispose(instance) {
  try {
    instance?.dispose();
  } catch (cause) {
    console.warn('Luoyang M0 cleanup failed.', cause);
  }
}

function stop(message) {
  // Invalidate callbacks before dispose, which can itself trigger contextlost.
  generation += 1;
  const previous = prototype;
  prototype = null;
  const previousController = controller;
  controller = null;
  showPoster(message);
  previousController?.abort();
  dispose(previous);
}

function recover(cause) {
  stop('3D 暂时无法显示，可以继续查看海报和四张画风样张。');
  error.hidden = false;
  error.textContent = '没能打开 3D。请重试；若仍失败，可换用支持 WebGL 2 的浏览器。';
  startButton.textContent = '重新加载 3D';
  console.warn('Luoyang M0 could not render.', cause);
}

async function start(manual = false) {
  if (phase !== 'poster') return;
  if (manual) {
    explicitlyOpened = true;
    deliberatelyClosed = false;
    if (mobile.matches && !validMethod && !lastMetrics) options.method = 'edge';
  }
  const current = ++generation;
  const currentController = new AbortController();
  controller = currentController;
  phase = 'loading';
  stage.dataset.state = 'loading';
  stage.setAttribute('aria-busy', 'true');
  poster.hidden = false;
  canvas.hidden = false;
  canvas.style.visibility = 'hidden';
  startButton.hidden = true;
  closeButton.hidden = false;
  closeButton.textContent = '取消加载';
  controls.disabled = true;
  error.hidden = true;
  error.textContent = '';
  status.textContent = '正在准备院落与纸上画风，海报仍可查看。';
  syncOptions();
  let candidate = null;
  let releaseCreation = null;
  try {
    const { createPrototype } = await import('./renderer.mjs');
    if (current !== generation || currentController.signal.aborted) return;
    // Finish the previous initializer's cleanup before mounting its successor.
    const previousCreation = pendingCreation;
    pendingCreation = new Promise((resolve) => { releaseCreation = resolve; });
    await previousCreation;
    if (current !== generation || currentController.signal.aborted) return;
    // forceContextLoss leaves the old canvas with a lost context. A fresh DOM
    // canvas preserves presentation and accessibility attributes, not that state.
    const nextCanvas = canvas.cloneNode(false);
    nextCanvas.hidden = false;
    nextCanvas.style.visibility = 'hidden';
    canvas.replaceWith(nextCanvas);
    canvas = nextCanvas;
    candidate = await createPrototype({
      canvas: nextCanvas,
      modelUrl,
      signal: currentController.signal,
      onStatus(message) {
        if (current === generation) status.textContent = message;
      },
      onMetrics(value) {
        if (current !== generation) return;
        lastMetrics = value;
        updateMetrics();
        if (value.contextLost) recover(new Error('WebGL context lost'));
      },
    });
    if (current !== generation || currentController.signal.aborted) {
      dispose(candidate);
      return;
    }
    prototype = candidate;
    candidate = null;
    prototype.setOptions(options);
    prototype.resize();
    phase = 'ready';
    stage.dataset.state = 'ready';
    canvas.style.visibility = '';
    poster.hidden = true;
    controls.disabled = false;
    closeButton.textContent = '收起 3D';
    stage.removeAttribute('aria-busy');
    status.textContent = mobile.matches
      ? '3D 已打开。单指旋转、双指缩放；可以随时收起回到海报。'
      : '拖动旋转、滚轮缩放。同一座院落、同一机位，比较两种描边。';
    // Freeze the first interactive instant. A later Resource Timing entry is
    // included only if its request started before this instant.
    if (readyAt === null) readyAt = performance.now();
    updateMetrics();
  } catch (cause) {
    dispose(candidate);
    if (current !== generation || currentController.signal.aborted) return;
    recover(cause);
  } finally {
    releaseCreation?.();
  }
}

for (const button of document.querySelectorAll('button[data-method]')) {
  button.addEventListener('click', () => {
    options.method = button.dataset.method;
    syncOptions();
  });
}
for (const button of document.querySelectorAll('button[data-brush]')) {
  button.addEventListener('click', () => {
    options.brush = button.dataset.brush;
    syncOptions();
  });
}
lineWidthInput.addEventListener('input', () => {
  options.lineWidth = Number(lineWidthInput.value);
  syncOptions();
});
paperStrengthInput.addEventListener('input', () => {
  options.paperStrength = Number(paperStrengthInput.value);
  syncOptions();
});
$('#reset-view').addEventListener('click', () => prototype?.reset());
startButton.addEventListener('click', () => { void start(true); });
closeButton.addEventListener('click', () => {
  deliberatelyClosed = true;
  stop('已收起 3D，回到纸上院落。可以随时重新打开。');
  startButton.focus({ preventScroll: true });
});

const resizeObserver = new ResizeObserver(() => prototype?.resize());
resizeObserver.observe(stage);
mobile.addEventListener('change', () => {
  if (mobile.matches && !explicitlyOpened && phase !== 'poster') {
    stop('小屏幕先看海报与画风样张；需要时再打开 3D。');
  } else if (!mobile.matches && !deliberatelyClosed && phase === 'poster' && !explicitlyOpened) {
    if (!validMethod && !lastMetrics) options.method = 'compare';
    void start();
  }
});

if ('PerformanceObserver' in window) {
  resourceObserver = new PerformanceObserver(() => {
    if (readyAt !== null) updateMetrics();
  });
  resourceObserver.observe({ type: 'resource', buffered: true });
}
addEventListener('pagehide', () => {
  stop('已收起 3D，可以重新打开。');
  resizeObserver.disconnect();
  resourceObserver?.disconnect();
});
addEventListener('pageshow', (event) => {
  if (!event.persisted) return;
  resizeObserver.observe(stage);
  resourceObserver?.observe({ type: 'resource', buffered: true });
});

syncOptions();
showPoster(mobile.matches
  ? '先看海报与四种画风样张。想转一转院落时，再打开 3D。'
  : '正在准备画风对照。');
updateMetrics();
if (!mobile.matches) void start();
