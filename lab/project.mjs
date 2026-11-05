// Detail page for large projects: a live scene up top, then chapters, build progress, research notes and member assets.
// The scene module comes from the project card ("scene") and follows the contract in docs/asset-spec/README.md §6.
export function renderProject({ main, a, c, d, esc, img, card, date }) {
  const chapters = a.chapters || [], progress = a.progress || [], journal = a.journal || [], evidence = a.evidence || [];
  const members = (a.members || []).map(id => d.assets.find(x => x.id === id)).filter(Boolean);
  const sum = s => progress.filter(p => p.status === s).length;
  const figs = [['模型文件', a.stats?.['模型文件'] ?? '—', '个'], ['章节', chapters.length, '章'], ['已入城', sum('已入城'), '项'], ['已建模', sum('已建模'), '项']];
  const chip = s => `<span class="pj-chip" data-s="${esc(s)}">${esc(s)}</span>`;
  const num = i => String(i + 1).padStart(2, '0');
  const coarse = matchMedia('(max-width: 700px), (pointer: coarse)').matches;
  const props = [['资产 ID', a.id], ['分类', c.zh], ['类型', a.kind], ['状态', a.status || '—'], ['最近更新', date(a.updated)]];
  const notes = Object.entries(a.notes || {});

  main.innerHTML = `<article class="ad pj">
<nav class="crumbs" aria-label="位置"><a href="index.html">总览</a> / <a href="index.html#${c.id}">${esc(c.zh)}</a> / ${esc(a.title)}</nav>
<header class="ad-head">
  <div>
    <div class="meta"><span>${esc(c.en)}</span><span>·</span><span>${esc(a.kind)}</span>${a.state ? `<span class="ad-state" data-s="${esc(a.state)}">${esc(a.state)}</span>` : ''}</div>
    <h1>${esc(a.title)}</h1>${a.english ? `<div class="en">${esc(a.english)}</div>` : ''}
    <p class="sum">${esc(a.summary)}</p>
  </div>
  <dl class="ad-figs">${figs.map(([k, v, u]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}<small>${esc(u)}</small></dd></div>`).join('')}</dl>
</header>

<section class="pj-view" aria-label="实时城景">
  <div class="pj-stage" id="pj-stage" data-state="poster">
    ${img(a.cover, { alt: a.alt || a.title, sizes: '100vw', eager: true, cls: 'pj-poster' })}
    <canvas id="pj-canvas" tabindex="0" aria-label="${esc(a.title)}实时城景：拖动转动，滚轮缩放，点选建筑看便签"></canvas>
    <div class="pj-status" id="pj-status" role="status">${coarse ? '' : '正在打开城景…'}</div>
    ${coarse ? `<button class="btn solid pj-open" id="pj-open">打开三维城景<span aria-hidden="true">◇</span></button>` : ''}
    <aside class="pj-note" id="pj-note" hidden aria-live="polite">
      <button class="pj-x" id="pj-x" aria-label="关闭便签">×</button>
      <div class="pj-note-k">一处建筑的手记</div>
      <h3 id="pj-nt"></h3>
      <div class="pj-note-tags"><span id="pj-ns"></span><span id="pj-nl"></span></div>
      <p id="pj-nm"></p><p class="pj-basis" id="pj-nb"></p>
    </aside>
  </div>
  <div class="pj-bar">
    <div class="pj-chips" role="group" aria-label="飞到章节">
      <button data-focus="city" aria-pressed="false">全城</button>
      ${chapters.map((ch, i) => `<button data-focus="${esc(ch.focus || ch.id)}" data-ch="${esc(ch.id)}" aria-pressed="false"><i>${num(i)}</i>${esc(ch.title)}</button>`).join('')}
    </div>
    <label class="pj-tier"><input type="checkbox" id="pj-tier"> 显示史料等级</label>
  </div>
  <p class="pj-hint" id="pj-hint">拖动转动 · 滚轮缩放 · 点选建筑看便签</p>
</section>

<section class="ad-sect pj-chapters"><h2>章节<small>${chapters.length}</small></h2>
  <ol class="pj-grid">${chapters.map((ch, i) => `<li class="pj-ch">
    <figure>${ch.image ? img(ch.image, { alt: ch.title, sizes: '(max-width: 760px) 100vw, 33vw' }) : ''}<span class="pj-n">${num(i)}</span></figure>
    <div class="pj-ch-b"><div class="pj-ch-h"><h3>${esc(ch.title)}</h3>${chip(ch.status)}</div>
      ${ch.statusNote ? `<div class="pj-ch-s">${esc(ch.statusNote)}</div>` : ''}
      <p class="pj-line">${esc(ch.line)}</p>${ch.text ? `<p class="pj-text">${esc(ch.text)}</p>` : ''}
      <button class="pj-go" data-focus="${esc(ch.focus || ch.id)}" data-ch="${esc(ch.id)}">在城中看<span aria-hidden="true">↑</span></button></div>
  </li>`).join('')}</ol>
</section>

${progress.length ? `<section class="ad-sect pj-progress"><h2>建设进度<small>${progress.length} 项</small></h2>
  <div class="pj-tally">${['已入城', '已建模', '研究中', '待建'].filter(s => sum(s)).map(s => `<div style="flex:${sum(s)}" data-s="${s}"><b>${sum(s)}</b> ${s}</div>`).join('')}</div>
  <div class="tablewrap"><table class="list pj-table"><thead><tr><th>内容</th><th>状态</th><th class="n">数量</th><th>说明</th><th></th></tr></thead><tbody>
  ${progress.map(p => `<tr><td><b style="font-family:var(--serif)">${esc(p.title)}</b>${p.chapter ? `<div class="pj-sub">${esc(chapters.find(ch => ch.id === p.chapter)?.title || '')}</div>` : ''}</td><td>${chip(p.status)}</td>
    <td class="n">${p.count ?? '—'}${p.unit ? `<small> ${esc(p.unit)}</small>` : ''}</td><td class="pj-note-c">${esc(p.note || '')}</td>
    <td class="n">${p.focus ? `<button class="pj-go" data-focus="${esc(p.focus)}" data-ch="${esc(p.chapter || '')}">在城中看<span aria-hidden="true">↑</span></button>` : ''}</td></tr>`).join('')}
  </tbody></table></div>
</section>` : ''}

<div class="ad-body pj-research">
  <section><h2>研究手记</h2>
    ${evidence.length ? `<div class="pj-levels">${evidence.map(e => `<div class="pj-level" data-l="${esc(e.level)}"><b>${esc(e.level)}</b><p>${esc(e.text)}</p></div>`).join('')}</div>` : ''}
    ${journal.length ? `<ol class="pj-journal">${journal.map(j => `<li><time datetime="${esc(j.date)}">${esc(j.date.replace(/-/g, '.'))}</time><div><h3>${esc(j.title)}${j.batch ? `<small>${esc(j.batch)}</small>` : ''}</h3>${j.text ? `<p>${esc(j.text)}</p>` : ''}</div></li>`).join('')}</ol>` : ''}
    ${notes.length ? `<dl class="ad-notes pj-notes">${notes.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>` : ''}
  </section>
  <aside class="ad-card" aria-label="档案"><h2>档案</h2><dl class="props">${props.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl></aside>
</div>

${members.length ? `<section class="ad-sect"><h2>组成资产<small>${members.length}</small></h2><div class="cards">${members.map(card).join('')}</div></section>` : ''}
</article>`;

  // ---- the live scene ----
  const stage = document.getElementById('pj-stage'), canvas = document.getElementById('pj-canvas'), status = document.getElementById('pj-status');
  const note = document.getElementById('pj-note'), tier = document.getElementById('pj-tier');
  let scene = null, opening = null, ctrl = null, want = null;
  const chipsActive = (focus, ch) => main.querySelectorAll('.pj-chips button').forEach(b => b.setAttribute('aria-pressed', b.dataset.focus === focus || (ch && b.dataset.ch === ch)));
  const showNote = n => {
    document.getElementById('pj-nt').textContent = n.title;
    document.getElementById('pj-ns').innerHTML = n.status ? chip(n.status) : '';
    document.getElementById('pj-nl').innerHTML = n.tier ? `<span class="pj-tierchip" data-l="${esc(n.tier)}">${esc(n.tier)}</span>` : '';
    document.getElementById('pj-nm').textContent = n.summary || '';
    document.getElementById('pj-nb').textContent = n.basis || '';
    note.hidden = false;
  };
  const open = () => {
    if (scene) return Promise.resolve(scene);
    if (opening) return opening;
    ctrl = new AbortController(); stage.dataset.state = 'loading'; status.textContent = '正在打开城景…';
    document.getElementById('pj-open')?.setAttribute('hidden', '');
    opening = import(a.scene).then(m => m.mountScene(canvas, {
      signal: ctrl.signal,
      onSelect: showNote,
      onStatus: msg => { if (stage.dataset.state !== 'ready') status.textContent = msg; },
    })).then(s => {
      scene = s; stage.dataset.state = 'ready'; status.textContent = '';
      if (tier.checked) s.setEvidence?.(true);
      if (want) { s.focus(want.focus)?.catch?.(() => {}); chipsActive(want.focus, want.ch); }
      else chipsActive(chapters[1]?.focus || '', chapters.find(ch => ch.id === 'residential') ? 'residential' : null);
      return s;
    }).catch(err => {
      if (err?.name === 'AbortError') return null;
      // the live scene is the default; if it cannot open, the poster stays and says why
      stage.dataset.state = 'failed';
      status.textContent = /WebGL/i.test(err?.message || '') ? '这台设备无法显示三维，先看海报与章节。' : '城景没能打开，先看海报与章节。';
      document.getElementById('pj-open')?.removeAttribute('hidden');
      console.warn('scene failed', err);
      return null;
    }).finally(() => { opening = null; });
    return opening;
  };
  const go = (focus, ch, scroll) => {
    want = { focus, ch }; chipsActive(focus, ch); note.hidden = true;
    if (scroll) document.querySelector('.pj-view').scrollIntoView({ behavior: 'smooth', block: 'start' });
    open().then(s => s?.focus(focus)?.catch?.(() => {}));
  };
  main.querySelector('.pj-chips').addEventListener('click', e => { const b = e.target.closest('button'); if (b) go(b.dataset.focus, b.dataset.ch); });
  main.addEventListener('click', e => { const b = e.target.closest('.pj-go'); if (b) go(b.dataset.focus, b.dataset.ch, true); });
  document.getElementById('pj-x').addEventListener('click', () => { note.hidden = true; canvas.focus(); });
  document.getElementById('pj-open')?.addEventListener('click', () => open());
  tier.addEventListener('change', () => { scene?.setEvidence?.(tier.checked); stage.dataset.tiers = tier.checked; });
  addEventListener('keydown', e => { if (e.key === 'Escape') note.hidden = true; });
  addEventListener('pagehide', () => { ctrl?.abort(); scene?.dispose(); });
  if (!coarse) open();
}
