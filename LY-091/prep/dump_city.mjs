// LY-091 prep: dump city-data.mjs nodes/assets (read-only import).
import { pathToFileURL } from 'node:url';
const root = process.argv[2] || 'D:/GitHub/creation-notebook-lab';
const m = await import(pathToFileURL(root + '/docs/cities/luoyang/city-data.mjs').href);
const out = { nodes: m.nodes, assets: m.assets, chapters: m.chapters, researchModels: m.researchModels, provenance: m.provenance };
process.stdout.write(JSON.stringify(out, null, 1));
