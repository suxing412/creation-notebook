// CI only, after assemble_site. Never invoke this from Pages deployment.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const site=new URL('../../_site/cities/luoyang/',import.meta.url),fixture=new URL('../fixtures/pre-display-ground/',import.meta.url);
const identities=JSON.parse(readFileSync(new URL('identities.json',fixture)));
assert.equal(identities.commit,'cf9defa04c293033ba07f063f7d7721197a58461');
for(const record of identities.files){
 const b=readFileSync(new URL(record.path,fixture));assert.equal(b.length,record.bytes);assert.equal(createHash('sha256').update(b).digest('hex'),record.sha256);
 let s=b.toString();for(const dependency of identities.files)s=s.replaceAll("'./"+dependency.path+"'","'./ground-baseline-"+dependency.path+"'");
 writeFileSync(new URL('ground-baseline-'+record.path,site),s);
}
const html=readFileSync(new URL('../../_site/asset.html',import.meta.url),'utf8'),found=html.match(/<script type="importmap">([\s\S]*?)<\/script>/);
assert.ok(found,'Built project import map missing');const map=JSON.parse(found[1]);
for(const key of Object.keys(map.imports)){const u=new URL(map.imports[key],'https://qa.invalid/asset.html');assert.equal(u.origin,'https://qa.invalid');map.imports[key]=u.pathname+u.search+u.hash;}
writeFileSync(new URL('ground-qa.mjs',site),readFileSync(new URL('ground-harness.mjs',import.meta.url)));
writeFileSync(new URL('ground-qa.html',site),`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Display-ground verification only</title>
<script type="importmap">${JSON.stringify(map)}</script>
<style>body{margin:0;font:14px sans-serif}nav{min-height:70px}button{padding:10px}#stage{width:100vw;height:650px}canvas{display:block;width:100%;height:100%}</style>
<nav><button id="install">Install</button><button id="withdraw">Withdraw</button><button data-focus="qa-ground-wide">Wide</button><button data-focus="qa-ground-wall">Wall low view</button><button data-focus="qa-ground-market">Market low view</button><button data-focus="qa-ground-road">Road joint</button><button data-focus="qa-ground-well">Well</button><button id="research">Research</button><button id="city">City</button><button id="evidence">Evidence</button><button id="redraw">Redraw</button></nav>
<div id="stage"></div><script type="module" src="./ground-qa.mjs"></script>`);
console.log('Prepared independent 86-node display-ground harness; browser not executed.');
