// Read-only: imports lab city-data.mjs and dumps its manifest to JSON (stdout).
import { pathToFileURL } from 'node:url';
const p = process.argv[2];
const m = (await import(pathToFileURL(p).href)).default;
process.stdout.write(JSON.stringify(m, null, 1));
