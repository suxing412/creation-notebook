// Controls for the 3D viewer on asset pages: a quick bar (view modes, camera, screenshot), a side panel
// (light presets and colours, exposure, background, display helpers) and a live readout of the model.
import { DEFAULT_LOOK, LIGHT_PRESETS, VIEWS } from './viewer.mjs';

const KEY_COLORS = [['#fff4e6', '暖白'], ['#ffffff', '正白'], ['#ffd29a', '暖金'], ['#ff9a5a', '夕照'], ['#a9c4ff', '冷蓝']];
const FILL_COLORS = [['#cfd9ea', '天光'], ['#ffffff', '白'], ['#ffe2bf', '暖'], ['#6d7fb8', '暮蓝'], ['#34406b', '夜']];
const BGS = [['#2a2926', '墨'], ['#efe9dd', '纸'], ['#f8f8f6', '白'], ['#8e8b85', '灰'], ['#0c0c0d', '黑'], ['#d9e4ec', '雾蓝']];
const CAMS = [['persp', '斜'], ['front', '前'], ['side', '侧'], ['top', '顶']];
const STORE = 'lab-viewer-look', PANEL = 'lab-viewer-panel';
const read = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const write = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} };
const fmt = n => n >= 1e6 ? (n / 1e6).toFixed(2) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(1) + 'k' : String(n);
const m = n => n >= 10 ? n.toFixed(1) : n >= 1 ? n.toFixed(2) : n.toFixed(3);

export function savedLook() { return { ...DEFAULT_LOOK, ...read(STORE, {}) }; }

export function mountViewerUI(stage0, viewer, { name = 'model' } = {}) {
  // everything lives in one layer inside the stage, so remounting for another model never stacks listeners
  const stage = document.createElement('div'); stage.className = 'vw-ui'; stage0.append(stage);
  let look = viewer.look;
  const sw = (list, k) => list.map(([c, t]) => `<button class="sw" data-set="${k}" data-v="${c}" title="${t}" aria-label="${t}"><i style="background:${c}"></i></button>`).join('');
  const slider = (k, label, min, max, step, unit = '') => `<label class="vp-row"><span>${label}</span><input type="range" data-set="${k}" min="${min}" max="${max}" step="${step}"><output data-out="${k}" data-unit="${unit}"></output></label>`;
  const toggle = (k, label, hint = '') => `<label class="vp-tog"><input type="checkbox" data-set="${k}"><span>${label}</span>${hint ? `<kbd>${hint}</kbd>` : ''}</label>`;
  const open = read(PANEL, false);
  stage.innerHTML = (`
  <div class="vq" role="toolbar" aria-label="3D 查看工具">
    <div class="vq-g" role="group" aria-label="视图">${VIEWS.map(([k, t], i) => `<button data-view="${k}" title="${t}（${i + 1}）">${t}</button>`).join('')}</div>
    <div class="vq-g" role="group" aria-label="视角">${CAMS.map(([k, t]) => `<button data-cam="${k}" title="${t}视角">${t}</button>`).join('')}<button data-cam="reset" title="复位（R）" aria-label="复位视角">⟲</button></div>
    <div class="vq-g"><button data-act="shot" title="保存当前画面为 PNG">截图</button><button data-act="panel" aria-expanded="${open}" aria-controls="vp">调节</button></div>
  </div>
  <aside class="vp" id="vp" ${open ? '' : 'hidden'} aria-label="视图调节">
    <header><b>视图调节</b><button data-act="panel" aria-label="收起调节">×</button></header>
    <section><h4>光照预设</h4><div class="vp-presets">${Object.entries(LIGHT_PRESETS).map(([k, p]) => `<button data-preset="${k}">${p.label}</button>`).join('')}</div></section>
    <section><h4>主光</h4>
      <div class="vp-sw">${sw(KEY_COLORS, 'keyColor')}<label class="vp-pick" title="自定颜色"><input type="color" data-set="keyColor"></label></div>
      ${slider('key', '强度', 0, 6, 0.1)}${slider('az', '方向', 0, 360, 5, '°')}${slider('el', '高度', 5, 88, 1, '°')}
    </section>
    <section><h4>补光与环境</h4>
      <div class="vp-sw">${sw(FILL_COLORS, 'fillColor')}<label class="vp-pick" title="自定颜色"><input type="color" data-set="fillColor"></label></div>
      ${slider('fill', '补光', 0, 2, 0.05)}${slider('env', '环境', 0, 2.5, 0.05)}${slider('exposure', '曝光', 0.3, 2.5, 0.05)}
    </section>
    <section><h4>背景</h4><div class="vp-sw">${sw(BGS, 'bg')}<label class="vp-pick" title="自定颜色"><input type="color" data-set="bg"></label></div></section>
    <section><h4>显示</h4><div class="vp-togs">${toggle('shadow', '地面阴影')}${toggle('grid', '网格', 'G')}${toggle('bbox', '包围盒', 'B')}${toggle('spin', '自动旋转')}</div></section>
    <footer><button data-act="defaults">恢复默认</button><span>快捷键：1–6 视图 · F/S/T 视角 · R 复位</span></footer>
  </aside>
  <div class="vi" aria-live="polite"></div>`);
  const q = s => stage.querySelector(s), qa = s => stage.querySelectorAll(s);
  const panel = q('.vp'), readout = q('.vi');

  const sync = () => {
    look = viewer.look;
    qa('[data-view]').forEach(b => b.setAttribute('aria-pressed', b.dataset.view === look.view));
    qa('[data-preset]').forEach(b => b.setAttribute('aria-pressed', b.dataset.preset === look.preset));
    qa('.sw[data-set]').forEach(b => b.setAttribute('aria-pressed', b.dataset.v.toLowerCase() === String(look[b.dataset.set]).toLowerCase()));
    qa('input[data-set]').forEach(i => { const v = look[i.dataset.set]; if (i.type === 'checkbox') i.checked = !!v; else i.value = v; });
    qa('output[data-out]').forEach(o => { const v = look[o.dataset.out]; o.textContent = (Number.isInteger(v) ? v : (+v).toFixed(2)) + o.dataset.unit; });
    write(STORE, { ...look, spin: undefined });
  };
  const set = (patch, manual) => { viewer.set({ ...patch, ...(manual ? { preset: 'custom' } : {}) }); sync(); };
  const showInfo = () => {
    const i = viewer.info; if (!i) { readout.textContent = ''; return; }
    readout.innerHTML = `<span>${fmt(i.triangles)} 面</span><span>${fmt(i.vertices)} 顶点</span><span>${i.materials} 材质</span><span>${i.textures} 贴图</span><span>${i.size.map(m).join(' × ')} m</span>`;
  };
  const togglePanel = () => { const show = panel.hidden; panel.hidden = !show; qa('[data-act="panel"]')[0].setAttribute('aria-expanded', show); write(PANEL, show); };

  stage.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b || !stage.contains(b)) return;
    if (b.dataset.view) set({ view: b.dataset.view });
    else if (b.dataset.cam) b.dataset.cam === 'reset' ? viewer.reset() : viewer.view(b.dataset.cam);
    else if (b.dataset.preset) { const { label, ...p } = LIGHT_PRESETS[b.dataset.preset]; set({ ...p, preset: b.dataset.preset }); }
    else if (b.classList.contains('sw')) set({ [b.dataset.set]: b.dataset.v }, b.dataset.set !== 'bg');
    else if (b.dataset.act === 'panel') togglePanel();
    else if (b.dataset.act === 'defaults') set({ ...DEFAULT_LOOK, spin: look.spin });
    else if (b.dataset.act === 'shot') {
      const { url } = viewer.screenshot(2), a = document.createElement('a');
      a.href = url; a.download = `${name}-${look.view}.png`; document.body.append(a); a.click(); a.remove();
      b.textContent = '已保存'; setTimeout(() => { b.textContent = '截图'; }, 1400);
    }
  });
  stage.addEventListener('input', e => {
    const i = e.target.closest('input[data-set]'); if (!i || !stage.contains(i)) return;
    const k = i.dataset.set, v = i.type === 'checkbox' ? i.checked : i.type === 'range' ? +i.value : i.value;
    set({ [k]: v }, ['key', 'az', 'el', 'fill', 'env', 'exposure', 'keyColor', 'fillColor'].includes(k));
  });
  viewer.onChange(() => sync());
  sync(); showInfo();
  return { refresh() { sync(); showInfo(); } };
}
