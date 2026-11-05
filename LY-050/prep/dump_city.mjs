// Read-only: import the lab city manifest (pure data module) and dump it as JSON.
// usage: node dump_city.mjs <path/to/city-data.mjs> <out.json>
import { pathToFileURL } from 'node:url';
import { writeFileSync } from 'node:fs';
const [, , src, out] = process.argv;
const m = await import(pathToFileURL(src).href);
const strip = a => { const { url, nearUrl, ...rest } = a; return rest; };
writeFileSync(out, JSON.stringify({ assets: m.assets.map(strip), nodes: m.nodes, chapters: m.chapters, researchModels: m.researchModels }, null, 1));
console.log('assets', m.assets.length, 'nodes', m.nodes.length, 'chapters', m.chapters.length, 'research', (m.researchModels||[]).length);
