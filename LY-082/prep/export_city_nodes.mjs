// LY-082 prep: read-only export of the city-data nodes/assets used by measure_lane82.py.
// Usage: node export_city_nodes.mjs <lab_root> <out.json>
import { pathToFileURL } from 'node:url';
import { writeFileSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const [lab, out] = process.argv.slice(2);
const p = lab + '/docs/cities/luoyang/city-data.mjs';
const m = await import(pathToFileURL(p).href);
const want = ['C02-005', 'C02-006', 'C02-009', 'C02-010', 'C02-011', 'C02-012', 'C02-021', 'C02-022', 'C02-023', 'ground-south', 'ground-retained', 'ground-network-ground-stitched', 'ground-D08'];
const nodes = {}; const assets = {};
for (const n of m.nodes) if (want.includes(n.id)) nodes[n.id] = n;
for (const n of Object.values(nodes)) { const a = m.assets.find(x => x.id === n.asset); assets[a.id] = a; }
const sha = createHash('sha256').update(readFileSync(p)).digest('hex');
const chapters = m.chapters.filter(c => ['residential', 'terrain'].includes(c.id)).map(c => ({ id: c.id, loadNodeIds: c.loadNodeIds }));
writeFileSync(out, JSON.stringify({ cityDataSha256: sha, nodes, assets, chapters }, null, 1));
console.log('ok', sha, Object.keys(nodes).length, Object.keys(assets).length);
