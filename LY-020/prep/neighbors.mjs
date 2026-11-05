// LY-020 prep: which loaded city nodes have world AABBs that touch the wall footprint (coarse AABB-vs-sampled-polygon test).
// usage: node neighbors.mjs <city-data.mjs file URL> <measure-walls.json>
import fs from 'node:fs';
const m = (await import(process.argv[2])).default;
const r = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
// wall foot polygons: rebuild from station centers (A loft) is not stored for direct; use segment bounds + caps as coarse
const walls = m.nodes.filter(n => n.chapter === 'walls' && /^wall-/.test(n.id));
const out = [];
for (const n of m.nodes) {
  if (/^wall-/.test(n.id) || !n.bounds) continue;
  const b = n.bounds; // already world bounds in city-data
  for (const w of walls) {
    const wb = w.bounds;
    const ox = Math.min(b.max[0], wb.max[0]) - Math.max(b.min[0], wb.min[0]);
    const oz = Math.min(b.max[2], wb.max[2]) - Math.max(b.min[2], wb.min[2]);
    if (ox > 0 && oz > 0) out.push({ node: n.id, chapter: n.chapter, initial: n.initial !== false, wall: w.id, overlapXZ: [+ox.toFixed(2), +oz.toFixed(2)], nodeBounds: b });
  }
}
console.log(JSON.stringify(out, null, 1));
