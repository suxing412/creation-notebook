// CI-only. Run AFTER assemble_site; Pages must never invoke this preparation.
import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
const baseline='047e39d207d264739d22bfb68a9a378b6646767f';
const city='docs/cities/luoyang/',site=new URL('../../_site/cities/luoyang/',import.meta.url);
const original=execFileSync('git',['show',`${baseline}:${city}city-data.mjs`],{encoding:'utf8'});
const dependency=execFileSync('git',['show',`${baseline}:${city}z13-content.mjs`]);
// The independent 78-node baseline also freezes its transitive installation module.
const imports=[...original.matchAll(/^import\s+[^;]+\s+from\s+['"]([^'"]+)['"];?$/gm)];
if(imports.length!==1||imports[0][1]!=='./z13-content.mjs')throw new Error('Reconcile immutable baseline module dependencies explicitly');
if(!readFileSync(new URL('../../docs/cities/luoyang/z13-content.mjs',import.meta.url)).equals(dependency))throw new Error('Existing Z13 installer changed');
writeFileSync(new URL('gallery-baseline-data.mjs',site),original.replace("'./z13-content.mjs'","'./gallery-baseline-z13.mjs'"));
writeFileSync(new URL('gallery-baseline-z13.mjs',site),dependency);
const asset=readFileSync(new URL('../../_site/asset.html',import.meta.url),'utf8');
const found=asset.match(/<script type="importmap">([\s\S]*?)<\/script>/);
if(!found)throw new Error('Built project import map missing');
const map=JSON.parse(found[1]);
for(const key of Object.keys(map.imports)){
  const url=new URL(map.imports[key],'https://qa.invalid/asset.html');
  if(url.origin!=='https://qa.invalid')throw new Error('Unexpected external import-map dependency');
  map.imports[key]=url.pathname+url.search+url.hash;
}
for(const [source,target] of [['gallery-harness.mjs','gallery-qa.mjs'],['gallery-geometry.mjs','gallery-qa-geometry.mjs']])writeFileSync(new URL(target,site),readFileSync(new URL(source,import.meta.url)));
writeFileSync(new URL('gallery-qa.html',site),`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gallery browser verification</title>
<script type="importmap">${JSON.stringify(map)}</script>
<style>body{margin:0;font:14px sans-serif}nav{min-height:70px}button{padding:10px}#stage{width:100vw;height:650px}canvas{display:block;width:100%;height:100%}</style>
<nav><button id="install">Install eight parts</button><button id="withdraw">Withdraw</button><button data-focus="qa-gallery-wide">Wide view</button><button data-focus="qa-gallery-finite">Finite ground</button><button data-focus="qa-gallery-prefix">Approach front</button><button data-focus="qa-gallery-rear">Approach rear</button><button data-focus="qa-gallery-road-joint">Road joint</button><button id="evidence">Evidence</button><button id="redraw">Redraw</button><output id="picked"></output></nav>
<div id="stage"></div><script type="module" src="./gallery-qa.mjs"></script>`);
