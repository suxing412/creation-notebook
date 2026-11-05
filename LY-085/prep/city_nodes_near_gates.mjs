// LY-085 prep: list every city-data node whose world bounds (Blender XY = gltf x, -gltf z) intersect
// the south-of-wall corridor windows of Kaiyang / Pingcheng. Read-only import of city-data.mjs.
//   node city_nodes_near_gates.mjs <lab_root> <out.json>
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
const [lab, out] = process.argv.slice(2);
const m = await import(pathToFileURL(lab + '/docs/cities/luoyang/city-data.mjs').href);
const gates = { kaiyang: [2010.397, -21.301], pingcheng: [1622.809, -13.260] };
const res = { windowsBlenderXY: {}, hits: {} };
for (const [g, [ox, oy]] of Object.entries(gates)) {
  const w = { xmin: ox - 120, xmax: ox + 120, ymin: oy - 1250, ymax: oy + 60 };
  res.windowsBlenderXY[g] = w; res.hits[g] = [];
  for (const n of m.manifest.nodes) {
    const b = n.bounds; if (!b) continue;
    const p = n.position || [0, 0, 0];
    // node bounds in city-data are already world (gltf) for city-space nodes; courtyard bounds are local -> add position
    const local = (b.max[0] - b.min[0]) < 200 && Math.abs(b.min[0]) < 200 && (p[0] !== 0 || p[2] !== 0);
    const gx0 = (local ? p[0] : 0) + b.min[0], gx1 = (local ? p[0] : 0) + b.max[0];
    const gz0 = (local ? p[2] : 0) + b.min[2], gz1 = (local ? p[2] : 0) + b.max[2];
    const by0 = -gz1, by1 = -gz0;
    if (gx1 < w.xmin || gx0 > w.xmax || by1 < w.ymin || by0 > w.ymax) continue;
    res.hits[g].push({ id: n.id, asset: n.asset, chapter: n.chapter, initial: n.initial, space: n.space || null,
      blenderX: [gx0, gx1], blenderY: [by0, by1], zRange: [b.min[1], b.max[1]] });
  }
}
res.researchModels = m.manifest.researchModels.map(r => ({ id: r.id, space: r.space || null, chapter: r.chapter, cityPlacement: r.cityPlacement ?? null, title: r.title }));
fs.writeFileSync(out, JSON.stringify(res, null, 1)); console.log('OK', Object.fromEntries(Object.entries(res.hits).map(([k, v]) => [k, v.map(x => x.id)])));
