// LY-040 prep: plan distance from region boxes to every city node's bounds (read-only).
import { pathToFileURL } from 'node:url';
// usage: node nearest_nodes.mjs <city-data.mjs copy>
const mod = await import(pathToFileURL(process.argv[2]).href);
const {nodes, chapters} = mod.default;
// region boxes in diagram coords (X east, N north = -glTF Z)
const R = {
  granary_ground: [2249.714, 3647.469, 2321.714, 3699.469],
  road_C_NE: [2284.214, 3484.5, 2317.827, 3647.469],
  wuku_patch: [2307.327, 3490.0, 2329.327, 3510.0],
};
function d(a, b){ const dx=Math.max(0,a[0]-b[2],b[0]-a[2]); const dy=Math.max(0,a[1]-b[3],b[1]-a[3]); return Math.hypot(dx,dy); }
const rows=[];
for (const n of nodes){ if(!n.bounds) continue; const b=[n.bounds.min[0], -n.bounds.max[2], n.bounds.max[0], -n.bounds.min[2]];
  const ds=Object.fromEntries(Object.entries(R).map(([k,r])=>[k,+d(r,b).toFixed(2)]));
  rows.push({id:n.id, chapter:n.chapter, initial:n.initial, min:Math.min(...Object.values(ds)), ...ds}); }
rows.sort((a,b)=>a.min-b.min);
console.log(JSON.stringify({nodeCount:nodes.length, withBounds:rows.length, nearest:rows.slice(0,12),
  nearestGround: rows.filter(r=>/ground|road|street|link/i.test(r.id)).slice(0,5),
  storageChapter: chapters.find(c=>c.id==='storage')}, null, 1));
