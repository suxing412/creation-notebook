// Detail page for large projects: a live scene up top, then chapters, build progress, research notes and member assets.
// The scene module comes from the project card ("scene") and follows the contract in docs/asset-spec/README.md §6.
export async function renderProject({ main, a, c, d, esc, img, card, date }) {
  let plan;
  try {
    const response = await fetch(new URL('../docs/cities/luoyang/planning-zones.json', import.meta.url));
    if (!response.ok) throw new Error('规划数据加载失败');
    plan = await response.json();
    if (plan.schema !== 'luoyang-fullcity-planning-zones-v1' || plan.zones?.length !== 41) throw new Error('规划数据版本不符');
  } catch (error) {
    const original = await import('./project.mjs');
    original.renderProject({ main, a, c, d, esc, img, card, date });
    const warning = document.createElement('p'); warning.role = 'alert';
    warning.textContent = '41区规划暂未载入，当前为原有章节查看器。请刷新重试。';
    main.prepend(warning); return;
  }
  const stylesheet = document.createElement('link'); stylesheet.rel = 'stylesheet';
  stylesheet.href = new URL('./luoyang-project.css', import.meta.url).href; document.head.append(stylesheet);
  const zones = plan.zones;
  const groupOf = zone => Number(zone.id.slice(1)) <= 18 ? 'base' : Number(zone.id.slice(1)) <= 23 ? 'palace' : 'outer';

  const chapters = a.chapters || [], progress = a.progress || [], journal = a.journal || [], evidence = a.evidence || [];
  const members = (a.members || []).map(id => d.assets.find(x => x.id === id)).filter(Boolean);
  const sum = s => progress.filter(p => p.status === s).length;
  const figs = [['模型文件', a.stats?.['模型文件'] ?? '—', '个'], ['章节', chapters.length, '章'], ['已入城', sum('已入城'), '项'], ['已建模', sum('已建模'), '项']];
  const chip = s => `<span class="pj-chip" data-s="${esc(s)}">${esc(s)}</span>`;
  const num = i => String(i + 1).padStart(2, '0');
  const coarse = matchMedia('(max-width: 700px), (pointer: coarse)').matches;
  const props = [['资产 ID', a.id], ['分类', c.zh], ['类型', a.kind], ['状态', a.status || '—'], ['最近更新', date(a.updated)]];
  const notes = Object.entries(a.notes || {});

  main.innerHTML = `<article class="ad pj ly-navigation">
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
  <div class="ly-workspace">
  <nav class="ly-zone-bar" aria-label="城市分区导航">
    <button class="ly-overview" data-focus="city" aria-pressed="false">全城总览</button>
    <label class="ly-group-label">分区
      <select id="ly-zone-group" aria-label="选择分区组"><option value="base">城内基础区 · 18</option><option value="palace">宫区叠层 · 5</option><option value="outer">近远郊候选 · 18</option></select>
    </label>
    <div class="pj-chips ly-zone-chips" role="group" aria-label="镜头推向规划分区">
      ${zones.map(zone => `<button data-focus="zone:${esc(zone.id)}" data-zone="${esc(zone.id)}" data-group="${groupOf(zone)}" aria-pressed="false" ${groupOf(zone) !== 'base' ? 'hidden' : ''}><i>${esc(zone.id)}</i><span>${esc(zone.name)}</span></button>`).join('')}
    </div>
  </nav>
  <div class="pj-stage" id="pj-stage" data-state="poster">
    ${img(a.cover, { alt: a.alt || a.title, sizes: '100vw', eager: true, cls: 'pj-poster' })}
    <canvas id="pj-canvas" tabindex="0" aria-label="${esc(a.title)}实时城景：左键旋转，滚轮推拉，WASD沿地面移动，R返回全城"></canvas>
    <div class="ly-compass" role="img" aria-label="示意工程坐标方向，默认南上北下">
      <div class="ly-compass-rose"><span class="north">北 N</span><span class="south">南 S</span><span class="east">东 E</span><span class="west">西 W</span><i></i></div>
      <small>工程方位</small>
    </div>
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
  </div>
  <div class="ly-options">
    <label class="pj-tier"><input type="checkbox" id="ly-planning" checked> 规划虚线</label>
    <label class="pj-tier"><input type="checkbox" id="pj-tier"> 显示史料等级</label>
    <span>左键旋转 · 滚轮推拉 · WASD 移动 · R 全城</span>
  </div>
  <p class="pj-hint" id="pj-hint">默认南上北下；镜头围绕地面旋转。先点画面再用 WASD，松键后轻缓制动，移出焦点立即停止。</p>
  <aside class="ly-zone-note" id="ly-zone-note" aria-live="polite">
    <strong>41区规划示意，不是41个已发现历史坊</strong>
    <p>虚线是设计功能边界，已入城模型全部显示，分区只移动镜头。历史选址、绝对高程与测量注册仍有不确定；分区锚点不用于自动放置模型。</p>
  </aside>

</section>

<section class="ad-sect pj-chapters"><h2>章节<small>${chapters.length}</small></h2>
  <ol class="pj-grid">${chapters.map((ch, i) => `<li class="pj-ch">
    <figure>${ch.image ? img(ch.image, { alt: ch.title, sizes: '(max-width: 760px) 100vw, 33vw' }) : ''}<span class="pj-n">${num(i)}</span></figure>
    <div class="pj-ch-b"><div class="pj-ch-h"><h3>${esc(ch.title)}</h3>${chip(ch.status)}</div>
      ${ch.statusNote ? `<div class="pj-ch-s">${esc(ch.statusNote)}</div>` : ''}
      <p class="pj-line">${esc(ch.line)}</p>${ch.text ? `<p class="pj-text">${esc(ch.text)}</p>` : ''}
      <button class="pj-go" data-focus="${esc(ch.focus || ch.id)}" data-ch="${esc(ch.id)}">${ch.id === 'ritual' ? '独立研究（未入城）' : '看已建模型'}<span aria-hidden="true">↑</span></button></div>
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

  // Dedicated Luoyang controller. Other assets and the original project renderer are unchanged.
  const stage = document.getElementById('pj-stage'), canvas = document.getElementById('pj-canvas'), status = document.getElementById('pj-status');
  const note = document.getElementById('pj-note'), tier = document.getElementById('pj-tier');
  const zoneNote = document.getElementById('ly-zone-note'), selector = document.getElementById('ly-zone-group');
  let scene = null, opening = null, ctrl = null, pending = null, serial = 0, disposed = false;
  const showNote = n => {
    document.getElementById('pj-nt').textContent = n.title;
    document.getElementById('pj-ns').innerHTML = n.status ? chip(n.status) : '';
    document.getElementById('pj-nl').innerHTML = n.tier ? `<span class="pj-tierchip" data-l="${esc(n.tier)}">${esc(n.tier)}</span>` : '';
    document.getElementById('pj-nm').textContent = n.summary || '';
    document.getElementById('pj-nb').textContent = n.basis || '';
    note.hidden = false;
  };
  let shownZone;
  const updateView = state => {
    if (disposed) return;
    main.querySelector('.ly-compass').style.setProperty('--bearing', `${state.compassDegrees}deg`);
    const focus = state.zoneId ? `zone:${state.zoneId}` : state.studyId ? `research:${state.studyId}` : state.chapter;
    main.querySelectorAll('.ly-zone-bar button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.focus === focus)));
    if (shownZone !== state.zoneId) {
      shownZone = state.zoneId;
      const zone = zones.find(z => z.id === state.zoneId);
      if (zone) {
        selector.value = groupOf(zone); showGroup();
        zoneNote.innerHTML = `<strong>${esc(zone.id)} · ${esc(zone.name)} <small>设计规划 · 未作为历史定址</small></strong><p>${esc(zone.planning_use)}</p><p>历史证据：${esc(zone.historical_confidence.site_or_relation)}；边界：${esc(zone.historical_confidence.precise_boundary)}</p><p>${esc(zone.constraints.join(' '))}</p><p>来源：${zone.source_links.filter(s => /^https:\/\//.test(s.url)).map(s => `<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.id)}</a>`).join(' · ')}</p>`;
      } else {
        zoneNote.innerHTML = '<strong>41区规划示意，不是41个已发现历史坊</strong><p>城内基础区、宫区叠层及外围候选分开导航。虚线不是古代院墙或已建道路。既有模型不动；独立研究模型仍未入城。</p>';
      }
    }
    canvas.dispatchEvent(new CustomEvent('luoyang-view-change', { detail: state }));
  };
  function showGroup() {
    main.querySelectorAll('[data-zone]').forEach(button => { button.hidden = button.dataset.group !== selector.value; });
  }
  const open = () => {
    if (scene) return Promise.resolve(scene);
    if (opening) return opening;
    ctrl = new AbortController(); stage.dataset.state = 'loading'; status.textContent = '正在打开城景…';
    document.getElementById('pj-open')?.setAttribute('hidden', '');
    opening = import('../docs/cities/luoyang/navigation-scene.mjs').then(m => m.mountScene(canvas, {
      signal: ctrl.signal, onSelect: showNote, planningZones: zones,
      onStatus: message => { status.textContent = message; }, onViewChange: updateView,
    })).then(s => {
      if (disposed) { s.dispose(); return null; }
      scene = s; stage.dataset.state = 'ready';
      s.setEvidence?.(tier.checked); s.setPlanning?.(document.getElementById('ly-planning').checked);
      updateView(s.getViewState()); return s;
    }).catch(error => {
      if (error?.name === 'AbortError' || disposed) return null;
      stage.dataset.state = 'failed'; status.textContent = '城景未能打开，原模型和章节仍保留。可重试打开。';
      document.getElementById('pj-open')?.removeAttribute('hidden');
      console.warn('Luoyang scene failed', error); return null;
    }).finally(() => { opening = null; });
    return opening;
  };
  async function go(focus, scroll = false) {
    const token = ++serial; pending = focus; note.hidden = true;
    if (scroll) main.querySelector('.pj-view').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
    const s = await open(); if (!s || token !== serial || disposed) return;
    try {
      const moved = await s.focus(focus);
      if (token !== serial || disposed) return;
      if (!moved) status.textContent = '此视图暂不能打开，当前画面保持。';
      updateView(s.getViewState()); if (moved) canvas.focus({ preventScroll: true });
    } catch (error) {
      if (token === serial && !disposed) status.textContent = `视图加载失败，当前画面保留：${error.message}`;
    }
  }
  main.querySelector('.ly-zone-bar').addEventListener('click', event => {
    const button = event.target.closest('button[data-focus]'); if (button) go(button.dataset.focus);
  });
  main.addEventListener('click', event => {
    const button = event.target.closest('.pj-go'); if (button) go(button.dataset.focus, true);
  });
  selector.addEventListener('change', showGroup);
  document.getElementById('ly-planning').addEventListener('change', event => scene?.setPlanning?.(event.target.checked));
  document.getElementById('pj-x').addEventListener('click', () => { note.hidden = true; canvas.focus(); });
  document.getElementById('pj-open')?.addEventListener('click', () => pending ? go(pending) : open());
  tier.addEventListener('change', () => scene?.setEvidence?.(tier.checked));
  const escape = event => { if (event.key === 'Escape') note.hidden = true; };
  addEventListener('keydown', escape);
  const hide = event => {
    if (event.persisted) { ++serial; scene?.suspend(); return; }
    disposed = true; ++serial; ctrl?.abort(); scene?.dispose();
    removeEventListener('keydown', escape); removeEventListener('pagehide', hide); removeEventListener('pageshow', show); stylesheet.remove();
  };
  const show = event => { if (event.persisted && !disposed) scene?.resume(); };
  addEventListener('pagehide', hide);
  addEventListener('pageshow', show);
  if (!coarse) open();
}
