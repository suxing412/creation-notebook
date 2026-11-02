import assert from 'node:assert/strict';import fs from 'node:fs';import {validateCatalog} from '../../docs/catalog-contract.js';
const data=JSON.parse(fs.readFileSync(new URL('../../docs/catalog.json',import.meta.url)));assert.equal(validateCatalog(data).length,20);
for(const [key,value]of [['countsAsAcceptedSpatialDesign',true],['acceptance','accepted'],['designStatus','已验收']]){const x=structuredClone(data);x.find(i=>i.kind==='space-design')[key]=value;assert.throws(()=>validateCatalog(x));}
const x=structuredClone(data);x.find(i=>i.kind==='space-design').designStatus='新空间设计原型／待实时与用户方向验收';assert.equal(validateCatalog(x).length,20);console.log('5 recovered catalog contract cases passed');

const h=data.find(x=>x.id==='012');assert.ok(h.evidenceContext.period.includes('东汉'));assert.ok(h.evidenceContext.region.includes('河南'));assert.ok(!data.some(x=>x.id==='011'));const bad=structuredClone(data);bad.find(x=>x.id==='012').evidenceContext.url='javascript:alert(1)';assert.throws(()=>validateCatalog(bad));

const wu=data.find(x=>x.id==='013');assert.ok(wu.evidenceContext.period.includes('孙吴'));assert.ok(wu.evidenceContext.region.includes('鄂州'));assert.ok(wu.architecturalType.includes('院心'));assert.equal(data.filter(x=>x.kind==='regular').length,12);

assert.equal(data.filter(x=>x.kind==='space-design').length,2);assert.equal(data.find(x=>x.featured).id,'SD02');const two=structuredClone(data);two.find(x=>x.id==='SD01').featured=true;assert.throws(()=>validateCatalog(two));
