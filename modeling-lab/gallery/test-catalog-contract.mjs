import assert from 'node:assert/strict';import fs from 'node:fs';import {validateCatalog} from '../../docs/catalog-contract.js';
const data=JSON.parse(fs.readFileSync(new URL('../../docs/catalog.json',import.meta.url)));assert.equal(validateCatalog(data).length,17);
for(const [key,value]of [['countsAsAcceptedSpatialDesign',true],['acceptance','accepted'],['designStatus','已验收']]){const x=structuredClone(data);x.find(i=>i.kind==='space-design')[key]=value;assert.throws(()=>validateCatalog(x));}
const x=structuredClone(data);x.find(i=>i.kind==='space-design').designStatus='新空间设计原型／待实时与用户方向验收';assert.equal(validateCatalog(x).length,17);console.log('5 recovered catalog contract cases passed');
