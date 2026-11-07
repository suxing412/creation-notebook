// CI-only files are added AFTER assemble_site. Pages never runs this script.
import { execFileSync } from 'node:child_process';
import { readFileSync,writeFileSync } from 'node:fs';
const baseline='d840a304fff11a3603fc9370360b23dc3ca1562e';
const site=new URL('../../_site/cities/luoyang/',import.meta.url);
writeFileSync(new URL('z13-baseline-data.mjs',site),execFileSync('git',['show',`${baseline}:docs/cities/luoyang/city-data.mjs`]));
writeFileSync(new URL('z13-qa.mjs',site),readFileSync(new URL('./z13-harness.mjs',import.meta.url)));
writeFileSync(new URL('z13-qa.html',site),`<!doctype html><meta charset="utf-8"><title>Z13 browser verification</title>
<style>body{margin:0;font:14px sans-serif}nav{height:70px}button{padding:10px}#stage{width:100vw;height:650px}canvas{display:block;width:100%;height:100%}</style>
<nav><button id="install">Install</button><button id="withdraw">Withdraw</button><button data-focus="market">Market</button><button data-focus="qa-bowl">Bowl</button><button data-focus="qa-edge">Edge</button><button data-focus="qa-oblique">Oblique</button><button id="evidence">Evidence</button><button id="redraw">Redraw</button><output id="picked"></output></nav><div id="stage"></div><script type="module" src="./z13-qa.mjs"></script>`);
