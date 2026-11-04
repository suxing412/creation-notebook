import manifest from './city-data.mjs';

const $ = (selector) => document.querySelector(selector);
const query = new URLSearchParams(location.search);
const cityRoot = new URL('../../cities/luoyang/', import.meta.url);
const legacyView = ['mode', 'c01stage', 'c02stage'].some(key => query.has(key));
if (legacyView) location.replace(new URL(`v1/${location.search}${location.hash}`, cityRoot).href);
const chapterMap = new Map(manifest.chapters.map(chapter => [chapter.id, chapter]));
const mobile = matchMedia('(max-width: 700px), (pointer: coarse)');
const stage = $('#stage');
let canvas = $('#scene');
let viewer = null;
let controller = null;
let opening = null;
let generation = 0;
let navigation = 0;
let selected = null;
let currentChapter = chapterMap.has(query.get('chapter')) ? query.get('chapter') : 'residential';
let readyAt = null;
let lastMetrics = null;
let drawerOpener = null;

const chapterDescriptions = {
  walls: '沿着已建城垣近看广阳门，再单独打开旄门等六座城门研究模型。位置和形制的依据可在便签中展开。',
  residential: '44 座院落已经布置在城中。先看南侧的 14 座，点选一座，再走近看屋檐与门前。',
  market: '五间店铺、三处摊位，以及交易和储货空间，组成目前已建的市肆样板。',
  storage: '已建仓房、收纳棚和作业场地组成一处完整的仓储研究组。',
  ritual: '灵台与太学已有独立研究模型。在这里转动细看它们，城市落位仍在研究中。',
  terrain: '查看已经制作的道路与地面，沿现有连接从城门走向住宅街区。',
};

function setStatus(message) { $('#status').textContent = message; }

function showError(error) {
  $('#error').textContent = `这次模型载入未完成。${error.message || error}，可以重新打开。`;
  $('#error').hidden = false;
}

function setLevel(level) {
  stage.dataset.level = level;
  document.querySelectorAll('[data-level]').forEach(button => {
    if (button.tagName === 'BUTTON') button.setAttribute('aria-pressed', String(button.dataset.level === level));
  });
}

function updateMetrics() {
  if (!lastMetrics) return;
  const entries = [...performance.getEntriesByType('navigation'), ...performance.getEntriesByType('resource')]
    .filter(entry => readyAt !== null && entry.startTime <= readyAt && entry.responseEnd > 0);
  const bytes = entries.reduce((sum, entry) => sum + (entry.encodedBodySize || 0), 0);
  $('#metrics').textContent = [
    `${lastMetrics.drawCalls} 次绘制 · ${lastMetrics.triangles.toLocaleString('zh-CN')} 个提交三角形`,
    `当前画面含 ${lastMetrics.representedNodes} 个已建模型实例`,
    `本次已载入模型 ${(lastMetrics.downloadBytes / 1e6).toFixed(2)} MB`,
    `首次进入交互前发起的资源 ${(bytes / 1e6).toFixed(2)} MB · ${entries.length} 项`,
    `显示缓冲 ${lastMetrics.bufferWidth} × ${lastMetrics.bufferHeight}`,
    '下载按文件体积记录。集显帧率与真实手机性能待实机验收。',
  ].join('\n');
}

function showNote(node) {
  selected = node;
  const residences = manifest.nodes.filter(item => item.chapter === 'residential');
  const index = residences.findIndex(item => item.id === node.id);
  const title = index >= 0 ? `住宅院落 · 第 ${index + 1} 院` : node.chapter === 'terrain' ? '道路与地面' : node.title.replace(/^N2 /, '市肆 ');
  $('#place-title').textContent = title;
  $('#place-summary').textContent = node.summary || chapterDescriptions[node.chapter] || '已交付的建筑研究模型，可转动观察。';
  $('#place-progress').textContent = node.space === 'local-study' ? '已建模 · 独立研究' : '已入城';
  $('#place-tier').textContent = node.tier || '推测';
  $('#place-basis').textContent = node.basis || '';
  const sources = $('#place-sources');
  sources.replaceChildren();
  const identity = document.createElement('li');
  identity.textContent = `制作记录 ${node.id}`;
  sources.append(identity);
  if (node.sourceContract) {
    const item = document.createElement('li');
    const link = document.createElement('a');
    link.href = new URL(node.sourceContract, cityRoot).href;
    link.textContent = '模型与布置来源';
    item.append(link);
    sources.append(item);
  }
  $('#place-details').open = false;
  $('#place-note').hidden = false;
}

function renderStudyChoices() {
  let choices = $('#study-choices');
  if (!choices) {
    choices = document.createElement('div');
    choices.id = 'study-choices';
    choices.className = 'study-choices';
    choices.setAttribute('aria-label', '已建研究模型');
    $('#view-description').after(choices);
  }
  choices.replaceChildren();
  const chapter = chapterMap.get(currentChapter);
  for (const id of chapter?.researchModelIds || []) {
    const node = manifest.researchModels.find(item => item.id === id);
    if (!node) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = node.title;
    button.addEventListener('click', () => runNavigation(async isCurrent => {
      await viewer.focusResearchModel(id, currentChapter);
      if (!isCurrent()) return;
      setLevel('courtyard');
    }));
    choices.append(button);
  }
  choices.hidden = !choices.childElementCount;
}

function updateChapter(id) {
  currentChapter = id;
  selected = null;
  document.querySelectorAll('[data-chapter]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.chapter === id)));
  $('#view-title').textContent = chapterMap.get(id)?.title || '洛阳 · 当前全城';
  $('#view-description').textContent = chapterDescriptions[id] || '按现有模型与原有位置，查看整座城的建造进度。';
  const chapterImage = document.querySelector(`[data-chapter-image="${id}"]`);
  if (chapterImage) {
    $('#poster').src = id === 'residential' ? 'assets/city-poster.webp' : chapterImage.src;
    $('#poster').alt = chapterImage.alt;
  }
  $('#place-note').hidden = true;
  renderStudyChoices();
}

async function openViewer() {
  if (viewer) return viewer;
  if (opening) return opening;
  const token = ++generation;
  controller = new AbortController();
  const signal = controller.signal;
  canvas = canvas.cloneNode(false);
  $('#scene').replaceWith(canvas);
  stage.dataset.state = 'loading';
  $('#error').hidden = true;
  $('#start3d').hidden = true;
  $('#close3d').hidden = false;
  $('#close3d').textContent = '取消加载';
  setStatus('正在打开已建街区，海报与图文仍可查看。');
  opening = (async () => {
    const { createCityRenderer } = await import('./city-renderer.mjs');
    signal.throwIfAborted();
    const result = await createCityRenderer({
      canvas, manifest, signal,
      onSelect(node) { if (token === generation) showNote(node); },
      onStatus(message) { if (token === generation) setStatus(message); },
      onMetrics(metrics) {
        if (token !== generation) return;
        if (metrics.contextLost) {
          closeViewer();
          showError(new Error('三维显示已暂停'));
          return;
        }
        lastMetrics = metrics;
        updateMetrics();
      },
    });
    if (token !== generation) { result.dispose(); return null; }
    viewer = result;
    readyAt ??= performance.now();
    viewer.setEvidenceVisible($('#show-tiers').checked);
    canvas.hidden = false;
    $('#poster').hidden = true;
    stage.dataset.state = 'ready';
    $('#view-controls').disabled = false;
    $('#close3d').textContent = '回到图文';
    updateMetrics();
    return viewer;
  })().catch(error => {
    if (token === generation && error.name !== 'AbortError') { closeViewer(); showError(error); }
    return null;
  }).finally(() => { if (token === generation) opening = null; });
  return opening;
}

function closeViewer() {
  generation++;
  navigation++;
  controller?.abort();
  viewer?.dispose();
  viewer = null;
  opening = null;
  canvas.hidden = true;
  $('#poster').hidden = false;
  stage.dataset.state = 'poster';
  $('#view-controls').disabled = true;
  $('#start3d').hidden = false;
  $('#close3d').hidden = true;
  $('#place-note').hidden = true;
  setStatus('当前城景已放回纸上。可以继续阅读建设记录，或重新打开三维。');
}

async function runNavigation(action) {
  const token = ++navigation;
  $('#error').hidden = true;
  const renderer = await openViewer();
  if (!renderer || token !== navigation) return;
  try { await action(() => token === navigation && viewer === renderer); }
  catch (error) { if (token === navigation && error.name !== 'AbortError') showError(error); }
}

function visitChapter(id, scroll = false) {
  updateChapter(id);
  setLevel('district');
  if (scroll) $('#city').scrollIntoView({ behavior: 'smooth', block: 'start' });
  return runNavigation(() => viewer.focusChapter(id));
}

function setDrawer(open, opener = null) {
  $('#research-drawer').hidden = !open;
  $('#open-research').setAttribute('aria-expanded', String(open));
  if (open) { drawerOpener = opener; $('#close-research').focus(); }
  else drawerOpener?.focus();
}

$('#start3d').addEventListener('click', () => visitChapter(currentChapter));
$('#close3d').addEventListener('click', closeViewer);
$('#close-note').addEventListener('click', () => { $('#place-note').hidden = true; canvas.focus(); });
$('#reset-view').addEventListener('click', () => visitChapter('residential'));
$('#show-tiers').addEventListener('change', () => {
  viewer?.setEvidenceVisible($('#show-tiers').checked);
  $('#evidence-legend').hidden = !$('#show-tiers').checked;
});
document.querySelectorAll('[data-chapter], [data-open-chapter]').forEach(button => {
  button.addEventListener('click', () => visitChapter(button.dataset.chapter || button.dataset.openChapter, Boolean(button.dataset.openChapter)));
});
document.querySelectorAll('button[data-level]').forEach(button => button.addEventListener('click', () => runNavigation(async isCurrent => {
  const level = button.dataset.level;
  if (level === 'city') {
    await viewer.resetView();
    if (!isCurrent()) return;
    $('#view-title').textContent = '洛阳 · 当前全城';
    $('#view-description').textContent = '城垣、门体与院落沿原有位置展开。空白的地方，留给后续建设。';
    $('#poster').src = 'assets/city-overview.webp';
    $('#poster').alt = '已有城垣和广阳门的全城位置渲染记录';
    $('#place-note').hidden = true;
    $('#study-choices').hidden = true;
  } else if (level === 'district') {
    updateChapter(currentChapter);
    await viewer.focusChapter(currentChapter);
    if (!isCurrent()) return;
  } else {
    const id = selected?.id || manifest.nodes.find(node => node.chapter === 'residential' && node.id === 'C02-001')?.id || manifest.nodes.find(node => node.chapter === 'residential')?.id;
    await viewer.focusCourtyard(id);
    if (!isCurrent()) return;
    const node = [...manifest.nodes, ...manifest.researchModels].find(item => item.id === id);
    if (node) showNote(node);
  }
  setLevel(level);
})));
document.querySelectorAll('#open-research, [data-open-research]').forEach(button => button.addEventListener('click', () => setDrawer(true, button)));
$('#close-research').addEventListener('click', () => setDrawer(false));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    setDrawer(false);
    $('#place-note').hidden = true;
  }
});

$('#revision-label').textContent = '2026.11.05';
$('#progress-summary').textContent = '44 座已入城院落 · 五店三摊与仓储 · 北侧新院与六门研究 · 灵台与太学';
document.querySelector('[data-chapter-status="walls"]').textContent = '城垣已入城 · 六门新研究';
document.querySelector('[data-chapter-status="residential"]').textContent = '44 院已入城 · 北院新研究';
for (const [id, text] of Object.entries(chapterDescriptions)) {
  document.querySelector(`[data-record-description="${id}"]`).textContent = text;
}
for (const source of manifest.provenance.sourceContracts) {
  const item = document.createElement('li');
  const link = document.createElement('a');
  link.href = new URL(source.path, cityRoot).href;
  link.textContent = source.path;
  item.append(link);
  $('#research-sources').append(item);
}
$('#research-content').textContent = '当前共用示意城市坐标。住宅落位、城墙高度及建筑形制属于设计推测。灵台与太学在独立模型视图展示。北宫新墙与古水系的配准资料仍待补充。';
updateChapter(currentChapter);
const resourceObserver = new PerformanceObserver(updateMetrics);
resourceObserver.observe({ type: 'resource', buffered: true });
window.addEventListener('pagehide', () => { closeViewer(); resourceObserver.disconnect(); });
if (!mobile.matches && !legacyView) {
  openViewer().then(renderer => {
    if (renderer && currentChapter !== 'residential') visitChapter(currentChapter);
  });
}
