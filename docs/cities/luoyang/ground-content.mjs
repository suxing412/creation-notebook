// Additive display-layer adapter. Constructing a manifest is not scope admission.
// No files, original geometry, roads, chapters, camera or existing nodes are modified.
const clone = value => structuredClone(value);
const canonical = value => value === null || typeof value !== 'object' ? JSON.stringify(value) : Array.isArray(value) ? '[' + value.map(canonical).join(',') + ']' : '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
const same = (a, b) => canonical(a) === canonical(b);
const guard = (condition, message) => { if (!condition) throw new Error('Display ground: ' + message); };
const freeze = value => { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };
export const displayGroundId = 'luoyang-city-continuous-ground-C-v6';
export const displayGroundSourceSHA = 'f801d7fd852a648b1ec45c1014732a4813e90cbfe4144b6599e848c173daf4e1';
export const displayGroundRecord = freeze({
  "id": displayGroundId,
  "path": "progress-assets/city-continuous-ground-C-v6/city-continuous-ground-C-v6.glb",
  "bytes": 56416,
  "sha256": "0bd2df3ff0ae3d55a82705e6e030d3b4164247ef6549149723451eef3a09146d",
  "triangles": 512,
  "bounds": {
    "min": [
      -69.84300231933594,
      -0.5,
      -3978.77099609375
    ],
    "max": [
      2672.0859375,
      0.17000000178813934,
      1249.5159912109375
    ]
  }
});
const sourcePath = 'progress-assets/city-continuous-ground-C-v6/source.json';
const key = 'cityContinuousGroundC6';
function normalizedBase(value) {
  guard(typeof value === 'string', 'baseURL must be an absolute directory URL');
  const supplied = new URL(value);
  guard(['file:', 'https:', 'http:'].includes(supplied.protocol) && !supplied.username && !supplied.password && !supplied.search && !supplied.hash, 'Unsupported baseURL');
  return new URL('.', supplied).href;
}
function validateInput(m) {
  guard(m && ['assets', 'nodes', 'chapters', 'researchModels'].every(name => Array.isArray(m[name])) && m.provenance && Array.isArray(m.provenance.sourceContracts), 'Missing manifest collections');
  for (const name of ['assets', 'nodes', 'chapters', 'researchModels']) {
    const ids = m[name].map(item => item?.id);
    guard(ids.every(id => typeof id === 'string' && id.length > 0) && new Set(ids).size === ids.length, 'Invalid or duplicate ' + name + ' identity');
  }
  const allNodes = [...m.nodes, ...m.researchModels];
  guard(new Set(allNodes.map(n => n.id)).size === allNodes.length, 'City/research node ID collision');
  const assetIds = new Set(m.assets.map(a => a.id));
  guard(allNodes.every(n => assetIds.has(n.asset)), 'Unknown node asset');
  for (const field of ['initialModelBytes', 'allCityModelBytes']) guard(Number.isSafeInteger(m.provenance[field]) && m.provenance[field] >= 0 && m.provenance[field] <= Number.MAX_SAFE_INTEGER, 'Invalid model budget');
  const paths = m.provenance.sourceContracts.map(s => s?.path);
  guard(paths.every(path => typeof path === 'string' && path.length > 0) && new Set(paths).size === paths.length, 'Invalid or duplicate source identity');
}
function receiptFor(baseURL, sourceSHA) {
  guard(sourceSHA === displayGroundSourceSHA, 'Unreviewed source identity');
  const base = normalizedBase(baseURL), r = displayGroundRecord;
  const asset = { id: displayGroundId, sourcePath: r.path, url: new URL(r.path, base).href, bytes: r.bytes, sha256: r.sha256, bounds: clone(r.bounds), excludeNodes: [], tier: 'C', sourceContract: sourcePath };
  const node = { id: displayGroundId, asset: displayGroundId, initial: true, chapter: 'terrain', tier: 'C', selectable: false, displayOnly: true, walkableCollision: false, bearingSupport: false, countAsCourtyard: false,
    position: [0, 0, 0], title: '全城连续展示地表 · C级，古地形水系未知',
    basis: '现状全城下方的连续封闭土体：普通顶面H=0.16贴既有路底，12墙脚按实测标高升至0.17；两处零高程薄面下微凹1毫米，井口保留至原建模深度。无贯穿孔；几何接触不是结构承托认证，古地形与地理配准未知。',
    bounds: clone(r.bounds), sourceContract: sourcePath };
  const source = { path: sourcePath, sha256: sourceSHA };
  const provenance = { version: 6, cityNodes: 1, newCourtyards: 0, newModelCards: 1, displayOnly: true, walkableCollision: false, bearingSupport: false, defaultModelBytes: r.bytes, automaticLOD: false, chapterChanges: 0, existingGroundChanges: 0, scopeAdmission: 'COMPLETE_BASE_DISPLAY_ONLY' };
  return { version: 1, adapter: 'city-continuous-ground-C-v6', baseURL: base, sourceSHA, asset, node, source, provenance, budget: r.bytes };
}
export function installDisplayGround(input, { baseURL = new URL('.', import.meta.url).href, sourceSHA = displayGroundSourceSHA } = {}) {
  validateInput(input);
  for (const field of ['initialModelBytes', 'allCityModelBytes']) guard(input.provenance[field] <= Number.MAX_SAFE_INTEGER - displayGroundRecord.bytes, 'Model budget would overflow');
  guard(!Object.hasOwn(input.provenance, key), 'Already installed');
  const receipt = receiptFor(baseURL, sourceSHA), r = receipt.asset;
  guard(![...input.nodes, ...input.researchModels].some(n => n.id === displayGroundId), 'Node identity occupied');
  guard(!input.assets.some(a => a.id === displayGroundId || a.url === r.url || a.sourcePath === r.sourcePath || a.sha256 === r.sha256), 'Asset identity or payload already present');
  guard(!input.provenance.sourceContracts.some(s => s.path === sourcePath), 'Source identity occupied');
  const manifest = clone(input);
  manifest.assets.push(clone(receipt.asset)); manifest.nodes.push(clone(receipt.node));
  manifest.provenance.sourceContracts.push(clone(receipt.source));
  manifest.provenance.initialModelBytes += receipt.budget; manifest.provenance.allCityModelBytes += receipt.budget;
  manifest.provenance[key] = clone(receipt.provenance);
  return { manifest, receipt };
}
export function withdrawDisplayGround(input, receipt) {
  validateInput(input);
  guard(receipt && same(receipt, receiptFor(receipt.baseURL, receipt.sourceSHA)), 'Invalid or altered receipt');
  guard(same(input.assets.find(a => a.id === displayGroundId), receipt.asset), 'Owned asset changed');
  guard(same(input.nodes.find(n => n.id === displayGroundId), receipt.node), 'Owned node changed');
  guard(same(input.provenance[key], receipt.provenance), 'Owned provenance changed');
  const sources = input.provenance.sourceContracts.filter(s => s.path === sourcePath);
  guard(sources.length === 1 && same(sources[0], receipt.source), 'Owned source changed');
  const related = new Set([displayGroundId, sourcePath]);
  const depends = item => item.asset === displayGroundId || item.sourceContract === sourcePath || item.projectionSourceContract === sourcePath || [...(item.dependsOn || []), ...(item.replaces || [])].some(value => related.has(value));
  guard(!input.nodes.some(n => n.id !== displayGroundId && depends(n)), 'City node depends on this layer');
  guard(!input.researchModels.some(depends), 'Research node depends on this layer');
  guard(!input.assets.some(a => a.id !== displayGroundId && (depends(a) || a.url === receipt.asset.url || a.sourcePath === receipt.asset.sourcePath || a.sha256 === receipt.asset.sha256)), 'Asset depends on this layer');
  guard(!input.provenance.sourceContracts.some(s => s.path !== sourcePath && depends(s)), 'Source depends on this layer');
  guard(!input.chapters.some(c => depends(c) || [...(c.nodeIds || []), ...(c.loadNodeIds || []), ...(c.researchModelIds || []), c.defaultResearchModel].some(id => id === displayGroundId)), 'Chapter depends on this layer');
  for (const field of ['initialModelBytes', 'allCityModelBytes']) guard(input.provenance[field] >= receipt.budget, 'Budget cannot be reversed');
  const manifest = clone(input);
  manifest.nodes = manifest.nodes.filter(n => n.id !== displayGroundId);
  manifest.assets = manifest.assets.filter(a => a.id !== displayGroundId);
  manifest.provenance.sourceContracts = manifest.provenance.sourceContracts.filter(s => s.path !== sourcePath);
  manifest.provenance.initialModelBytes -= receipt.budget; manifest.provenance.allCityModelBytes -= receipt.budget;
  delete manifest.provenance[key];
  return manifest;
}
