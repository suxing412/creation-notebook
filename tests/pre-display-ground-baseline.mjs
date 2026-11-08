// Immutable source family fetched independently from main 20d892c; not a withdrawn candidate.
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
export const baselineSHA='cf9defa04c293033ba07f063f7d7721197a58461';
const identities=JSON.parse(readFileSync(new URL('./fixtures/pre-display-ground/identities.json',import.meta.url)));
assert.equal(identities.commit,baselineSHA);
const allowed=new Map(identities.files.map(f=>[f.path,f])),cache=new Map();
function moduleURL(name){
 if(cache.has(name))return cache.get(name);
 const expected=allowed.get(name);assert.ok(expected,'Unexpected baseline dependency '+name);
 const bytes=readFileSync(new URL('./fixtures/pre-display-ground/'+name,import.meta.url));
 assert.equal(bytes.length,expected.bytes);assert.equal(createHash('sha256').update(bytes).digest('hex'),expected.sha256);
 let source=bytes.toString().replaceAll('import.meta.url',JSON.stringify(new URL('../docs/cities/luoyang/'+name,import.meta.url).href));
 source=source.replace(/from\s+(['"])\.\/([^'"]+)\1/g,(_,quote,child)=>'from '+JSON.stringify(moduleURL(child)));
 const url='data:text/javascript;base64,'+Buffer.from(source).toString('base64');cache.set(name,url);return url;
}
export const preDisplayGround=(await import(moduleURL('city-data.mjs'))).default;
