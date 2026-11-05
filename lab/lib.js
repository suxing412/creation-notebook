// Shared data + UI helpers for the asset library.
export const data = fetch('data/assets.json').then(r => r.json());
export const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
export const size = b => !b ? '—' : b >= 1e6 ? (b / 1e6).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
export const tris = t => !t ? '—' : t >= 1e6 ? (t / 1e6).toFixed(1) + 'M' : t >= 1e3 ? (t / 1e3).toFixed(1) + 'k' : String(t);
export const date = s => s ? s.slice(0, 10) : '—';

export function img(p, { alt = '', sizes = '(max-width: 700px) 100vw, 25vw', eager = false, cls = '' } = {}) {
  if (!p) return '';
  return `<img${cls ? ` class="${cls}"` : ''} src="${p.small.src}" srcset="${p.small.src} ${p.small.w}w, ${p.large.src} ${p.large.w}w" sizes="${sizes}"
    width="${p.small.w}" height="${p.small.h}" alt="${esc(alt)}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
}

/** One-line spec summary for an asset, used on cards, tooltips and lists. */
export function specs(a) {
  const out = [];
  if (a.files.length) out.push(`${a.files.length} 个 GLB`, size(a.bytes), `${tris(a.triangles)} 面`);
  if (a.stats) Object.entries(a.stats).forEach(([k, v]) => out.push(`${v} ${k}`));
  if (!a.files.length && a.category === 'web') out.push('HTML 页面');
  return out;
}

export function card(a) {
  const badge = a.files.length ? `GLB × ${a.files.length}` : a.category === 'web' ? 'HTML' : a.category === 'projects' ? 'PROJECT' : 'SPACE';
  return `<a class="card" href="asset.html?id=${encodeURIComponent(a.id)}">
    <div class="ph">${img(a.cover, { alt: a.alt || a.title, cls: a.coverIsShot ? 'shot' : '' })}<span class="badge">${badge}</span><span class="badge r">${esc(a.kind)}</span></div>
    <div class="body"><h3>${esc(a.title)}<span>${esc(a.english)}</span></h3>
    <div class="specs">${specs(a).map(s => `<span>${esc(s)}</span>`).join('')}</div>
    <p>${esc(a.summary)}</p></div></a>`;
}

export function header(d, current, { onSearch } = {}) {
  // every page wears the skin of the era last chosen in the overview
  try { document.documentElement.dataset.era = sessionStorage.getItem('lab-era') || 'ancient'; } catch { document.documentElement.dataset.era = 'ancient'; }
  const counts = Object.fromEntries(d.categories.map(c => [c.id, d.assets.filter(a => a.category === c.id).length]));
  const tabs = [{ id: '', zh: '总览', n: d.assets.length }, ...d.categories.map(c => ({ ...c, n: counts[c.id] }))];
  document.body.insertAdjacentHTML('afterbegin', `<a class="skip" href="#main">跳到内容</a>
  <header class="app-head">
    <div class="row"><a class="brand" href="index.html"><i class="seal" aria-hidden="true">造</i><b>造物手记</b><span>造物之匣 · 数字资产库</span></a>
      <a class="spec-link" href="spec.html"${current === 'spec' ? ' aria-current="page"' : ''}>投稿规范</a>
      <label class="gsearch"><input id="gsearch" type="search" placeholder="搜索全部资产" aria-label="搜索全部资产"></label></div>
    <nav class="tabs" aria-label="资产分类">${tabs.map(t => `<a class="tab" href="index.html${t.id ? '#' + t.id : ''}" data-tab="${t.id}"${t.id === current ? ' aria-current="page"' : ''}>${esc(t.zh)}<small>${t.n}</small></a>`).join('')}</nav>
  </header>`);
  const q = document.getElementById('gsearch');
  q.addEventListener('keydown', e => { if (e.key === 'Enter') { if (onSearch) onSearch(q.value); else location.href = 'index.html#all?q=' + encodeURIComponent(q.value); } });
  if (onSearch) q.addEventListener('input', () => onSearch(q.value));
  const setCurrent = id => document.querySelectorAll('.tab').forEach(t => t.dataset.tab === id ? t.setAttribute('aria-current', 'page') : t.removeAttribute('aria-current'));
  return { setCurrent, search: q };
}
