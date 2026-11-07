// Explicit provenance-only delta over immutable historical fixtures.
// Never copy current manifest fields into an expected historical manifest.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const corrections = [
  {
    "path": "data/far44/instances-calt.json",
    "oldSHA256": "c830b4e37090da5e070156b7f6199f36c5d0191c339f5a9399f0becded50ff85",
    "newSHA256": "e39fdafb016c9ff7f42e25bfcbfe37152f381fac84ffe2cca11cd6fc936fdf7e",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/far44/preflight-contract.json",
    "oldSHA256": "90dfa0774643b90d61f057aed726525cfe3e18647e897d3c90eb64fa79426d6b",
    "newSHA256": "c9aafa7d22100deb141c554deffd07da67818af711a75cb6f36144fe68f9cc50",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/west/city-wall-interface.json",
    "oldSHA256": "ad18cc65915724a850d1f97b498be8b63464cd3d25116c9d615bfd79f2570da8",
    "newSHA256": "ca75d115d49d38a53c66258af12e6e455d314f0f75548899e021276c5b100543",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/west/ground-atomic-contract.json",
    "oldSHA256": "bfc7fc83c3d8f34c79e9395532b74c324987b4dbf0c4342328b7581ebc2be584",
    "newSHA256": "7f26720bf40fc8cd7f7d0b445398d889fcc70c407f7cc7e26e4acd0eb6332367",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/west/N2-contract.json",
    "oldSHA256": "10678d73111ae0d131afc3ff823162392eab339ee66bf2046e61666c2c8d9386",
    "newSHA256": "498f51fcd0723da69ab1b97c56f3de004a449a86e0e322dedc6489446a00e2cd",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/west/market-interface.json",
    "oldSHA256": "31c6786db03b1d7e4be79070abe8ea9a577207345a55703c85d2fb34bc479f4e",
    "newSHA256": "2957184accc87e5c2089987c71023cd09a8ef0274b2daab1fce4d39623606347",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/west/storage-interface.json",
    "oldSHA256": "b910896799cdbb954717df342c7dfbb794eaaa1bdba3810b206140b84aeedba8",
    "newSHA256": "4f3ccae9891c2fcd2ae3d962c3740a4b53eac7faea872b5ce28596cf1a62c2b3",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/evidence/evidence-geometry.json",
    "oldSHA256": "662562fa87cffc9de43b2c23564f1ab63fba8c01f2345891f255cb202bee2233",
    "newSHA256": "fa8b7002869e01e981d2b2679c327a2f1db957119e55537e06289ca59e5ba7c7",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "data/evidence/stage-contract.json",
    "oldSHA256": "6ade3f6e62c4779014e3d4005525b377db132b293a6e83f24817415c4422377c",
    "newSHA256": "3227460643f5c8df8345ff750b128a27a8a5a497ab426ddcaa3574f0aafa705b",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "progress-assets/north13-gates/source.json",
    "oldSHA256": "9b07b7349ef536cd0b0a15c9bfa7134d2af7cc95e8dc402b7e2bea14d20719c1",
    "newSHA256": "dc16990098026ab441455636507de821a5869e82b4576073f58a77f46fdab515",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "progress-assets/mao-gate/source.json",
    "oldSHA256": "9b3a402731826629e74cd2936079b41e210643917dcda87091aad53454ac9798",
    "newSHA256": "95589c004a939a4adcb76fe005b32a1ebf6c5645a37106d045708d0fb0c4ee12",
    "kind": "raw-byte-hash-correction"
  },
  {
    "path": "progress-assets/taixue-A-v3.2/source.json",
    "oldSHA256": "5f2a8078e2faa3c32c070c607bf65b96f191d638a4b1ef13710d3e9d972ed76d",
    "newSHA256": "535e10ae94ef57dda5bd608f0d16a8736a71370774b5b08c732c1fcbe9653083",
    "kind": "raw-byte-hash-correction"
  }
];
const additions = [
  {
    "path": "progress-assets/granary-city-v1/source.json",
    "newSHA256": "30e74bda8a965f4f7c84aaa32bdb7a179680b6163150584cdeb58de3e3f12639",
    "kind": "bind-existing-contract"
  },
  {
    "path": "progress-assets/yong-city-v1/source.json",
    "newSHA256": "325fb5caa15ee631896495c2c71b93e4b0267933c15bfc3fbd9f6be050e8f238",
    "kind": "bind-existing-contract"
  },
  {
    "path": "progress-assets/yong-road-link-v2/source.json",
    "newSHA256": "3e402679151868949efe5733ca9ebee4ad12a6bea45e4b302e4b9f2a12b1b7d5",
    "kind": "bind-existing-contract"
  }
];
const hash=b=>createHash('sha256').update(b).digest('hex');
export function withContractIdentityCorrections(original){
 const updated=structuredClone(original), contracts=updated.provenance.sourceContracts;
 assert.ok(Array.isArray(contracts)&&contracts.length>=14);
 assert.equal(new Set(contracts.map(c=>c.path)).size,contracts.length,'duplicate historical contract');
 assert.deepEqual(contracts.slice(12,14),[
  {path:'progress-assets/flat/source.json',sha256:'ddd1445c1dddabc7f2134b4dc0c3fae37484e619099ea549a4104bf483b486c1'},
  {path:'progress-assets/north-three-v1/source.json',sha256:'d2cadd21e9b5fc9a3f7cee23927681a957118734c93a047cecab1038cc39c249'}
 ]);
 for(let i=0;i<corrections.length;i++){
  const row=corrections[i];assert.equal(contracts[i].path,row.path);
  assert.equal(contracts[i].sha256,row.oldSHA256,'unexpected historical identity: '+row.path);
  const raw=readFileSync(new URL('../docs/cities/luoyang/'+row.path,import.meta.url));
  assert.equal(hash(raw),row.newSHA256,'changed source contract: '+row.path);
  contracts[i].sha256=row.newSHA256;
 }
 for(const row of additions){
  assert.ok(!contracts.some(c=>c.path===row.path),'contract already bound: '+row.path);
  assert.equal(hash(readFileSync(new URL('../docs/cities/luoyang/'+row.path,import.meta.url))),row.newSHA256);
 }
 // Insert after the original 14 literal contracts, before additive content receipts.
 contracts.splice(14,0,...additions.map(r=>({path:r.path,sha256:r.newSHA256})));
 return updated;
}
