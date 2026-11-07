// Immutable pre-gallery city, including its exact Z13 dependency.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
export const baselineSHA='047e39d207d264739d22bfb68a9a378b6646767f';
export const gitFile=path=>execFileSync('git',['show',baselineSHA+':'+path],{maxBuffer:32*1024*1024});
const cityPath='docs/cities/luoyang/city-data.mjs',z13Path='docs/cities/luoyang/z13-content.mjs';
const city=gitFile(cityPath),z13=gitFile(z13Path);
const hash=b=>createHash('sha256').update(b).digest('hex');
assert.equal(hash(city),'d7eae1321f31dcc8e280f1d3198b69a227aaf1fb9badf93bd12f7eac7791f96c');
assert.equal(hash(z13),'035f3285bade63185272c619bdb0cc472c5e0653ffa6c6d2ed5af6dd2b34e5a4');
const data=(b,path)=>b.toString().replaceAll('import.meta.url',JSON.stringify(new URL('../'+path,import.meta.url).href));
const moduleURL=text=>'data:text/javascript;base64,'+Buffer.from(text).toString('base64');
const dep=moduleURL(data(z13,z13Path));
const source=data(city,cityPath).replace("'./z13-content.mjs'",JSON.stringify(dep));
export const preGallery=(await import(moduleURL(source))).default;
