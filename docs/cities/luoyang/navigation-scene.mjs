// Scene contract for the asset library's project page (docs/asset-spec/README.md §6).
// mountScene(canvas, { signal, onSelect, onStatus }) → { focus(target), reset(), setEvidence(on), dispose() }
//   target: a chapter id from the card ("walls", "residential", …), "city" for the whole city,
//           or "research:<model id>" for a separately delivered study model.
//   onSelect({ title, summary, status, tier, basis }) fires when a building is picked.
// This file only adapts the existing Luoyang renderer; it adds no models or data of its own.
import manifest from './city-data.mjs';

const chapterText = {
  walls: '沿已建城垣近看广阳门，也可以单独打开旄门等六座城门研究模型。',
  residential: '47 座院落已经布置在城中。点选一座，再走近看屋檐与门前。',
  market: '五间店铺、三处摊位，以及交易和储货空间，组成目前已建的市肆样板。',
  storage: '已建仓房、收纳棚和作业场地组成一处完整的仓储研究组。',
  ritual: '灵台与太学已有独立研究模型，城市落位仍在研究中。',
  terrain: '已经制作的道路与地面，从城门连向住宅街区。',
};

function noteOf(node) {
  const homes = manifest.nodes.filter(n => n.chapter === 'residential');
  const i = homes.findIndex(n => n.id === node.id);
  const title = i >= 0 ? `住宅院落 · 第 ${i + 1} 院` : node.chapter === 'terrain' ? '道路与地面' : String(node.title || node.id).replace(/^N2 /, '市肆 ');
  return {
    id: node.id, title,
    summary: node.summary || chapterText[node.chapter] || '已交付的建筑研究模型，可转动观察。',
    status: node.space === 'local-study' ? '已建模' : '已入城',
    tier: node.tier || '推测', basis: node.basis || '',
  };
}

export async function mountScene(canvas, { signal, onSelect, onStatus, onViewChange, planningZones = [] } = {}) {
  const { createCityRenderer } = await import('./city-navigation-renderer.mjs');
  const chapterOf = id => manifest.researchModels.find(r => r.id === id)?.chapter || 'ritual';
  const view = await createCityRenderer({
    canvas, manifest, signal, planningZones, onViewChange,
    onSelect: node => onSelect?.(noteOf(node)),
    onStatus: msg => onStatus?.(msg),
    onMetrics: m => { if (m.contextLost) onStatus?.('三维显示已暂停'); },
  });
  return {
    chapters: manifest.chapters.map(c => c.id),
    focus(target) {
      if (!target || target === 'city') return view.resetView();
      if (target.startsWith('zone:')) return view.focusZone(target.slice(5));
      if (target.startsWith('research:')) { const id = target.slice(9); return view.focusResearchModel(id, chapterOf(id)); }
      return view.focusChapter(target);
    },
    reset: () => view.resetView(),
    suspend: () => view.suspend(),
    resume: () => view.resume(),
    setPlanning: value => view.setPlanningVisible(value),
    getViewState: () => view.getViewState(),
    setEvidence: on => view.setEvidenceVisible(on),
    dispose: () => view.dispose(),
  };
}
