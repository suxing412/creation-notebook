// Incremental Z13 installation. Original frontage and all existing city data remain unchanged.
const clone = value => structuredClone(value);
const equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
const guard = (ok,message) => { if (!ok) throw new Error(message); };
export const z13Records = [
  {
    "id": "z13-frontage-original-v21",
    "nodeId": "Z13-FRONTAGE-V21-C01",
    "title": "八铺四棚市街 · C级设计",
    "path": "../../library/models/m-luoyang-market-frontage/files/street_frontage-LOD0.glb",
    "bytes": 1932544,
    "sha256": "46f08f41aa290218e9a3ec4e4de4e2cb676f10a80a035e9b6d3e1f8a0c5bf6f2",
    "tier": "C"
  },
  {
    "id": "z13-frontage-support-C",
    "nodeId": "Z13-FRONTAGE-SUPPORT-C01",
    "title": "市街支承与踏步 · C级设计",
    "path": "progress-assets/z13-market-C-v1/z13-frontage-support-and-steps-C.glb",
    "bytes": 35928,
    "sha256": "2c626c2aca1ea534d2f6df1ce14ccae2e6ee2c75e2cd01ee52aae9539298e8dd",
    "tier": "C"
  },
  {
    "id": "z13-continuous-display-ground-C-v1",
    "nodeId": "Z13-DISPLAY-GROUND-C01",
    "title": "市街连续展示地表 · C级设计",
    "path": "progress-assets/z13-market-C-v1/z13-continuous-display-C.glb",
    "bytes": 1196,
    "sha256": "80f8cfc4f9ca1c743ecfca7fed89806db1476bf7e77288e3c9b6e61bfb5c749b",
    "tier": "C"
  },
  {
    "id": "z13-road-edge-visual-infill-C-v1",
    "nodeId": "Z13-ROAD-EDGE-INFILL-C01",
    "title": "市街路缘视觉收边 · C级设计",
    "path": "progress-assets/z13-market-C-v1/z13-road-edge-visual-infill-C.glb",
    "bytes": 1052,
    "sha256": "1ecf18181776e38ec53e2b9c6dbcb1ad41b0e32c6c2b6d57afc76e48e119d526",
    "tier": "C"
  },
  {
    "id": "z13-grey-pottery-bowl-C",
    "nodeId": "market_bowl_C01",
    "title": "市街灰陶碗 · C级设计",
    "path": "progress-assets/z13-market-C-v1/bowl-C-LOD0.glb",
    "bytes": 36716,
    "sha256": "0014e893fb5ae5630b32e755548c2cb3ed7191d7f3441654fdff7d6bb83cf8bd",
    "tier": "C"
  }
];
export const z13NodeIds = z13Records.map(a=>a.nodeId);
const matrix = [0,0,-1,0,0,1,0,0,1,0,0,0,300,0.2,-2000,1];
const identity = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const beforeChapter = {"id": "market", "title": "市肆街景", "subtitle": "五店三摊 · 交易与储货样板", "nodeIds": ["market-main", "market-N2"], "loadNodeIds": ["market-main", "market-N2"], "bounds": {"min": [184.285995, 0, -1981.18396], "max": [244.285995, 4.53, -1937.18396]}, "tier": "推测", "basis": "金市位置取自既有研究示意点，现有功能组的街面与内部安排为设计研究。", "sourceIds": ["region_jin_B"]};
const sourceContract = 'progress-assets/z13-market-C-v1/source.json';
const source = {path:sourceContract,sha256:'3dab7d3e124903a9f31eb27bbc4514a9cf29d59666741cb0e18a73b7c64b87c0'};
const budget = z13Records.reduce((sum,a)=>sum+a.bytes,0);
const description = [
 '既有v2.1八铺四棚原件在Z13落位；方向、位置与使用安排为C设计，不替代旧五店三摊。',
 '街段配套支承和踏步，沿用市街同一矩阵；尺寸和结构为C设计，不作承载认证。',
 '约3868.96平方米连续展示面，避开既有支承与道路；不是全城地基或考古地层。',
 '60米路缘视觉补缝，仅补展示接缝，不承担通行碰撞、地基或结构承载。',
 '参考异地东汉灰陶平底碗类型；完整形状、厚度、材料和W1台面摆放均为C设计，非洛阳出土器复原。'
];
export function installZ13(input) {
 guard(input?.assets && input?.nodes && input?.chapters && input?.provenance,'Missing city manifest');
 const m=clone(input), index=m.chapters.findIndex(c=>c.id==='market');
 guard(index>=0 && equal(m.chapters[index],beforeChapter),'Market chapter changed; rebase Z13 explicitly');
 guard(!m.provenance.z13Market,'Z13 already installed');
 for(const a of z13Records) {
  guard(!m.assets.some(x=>x.id===a.id) && !m.nodes.some(n=>n.id===a.nodeId),'Duplicate Z13 identity');
 }
 const addedAssets=z13Records.map(({nodeId,title,path,...a})=>({...a,sourcePath:path,url:new URL(path,import.meta.url).href,sourceContract}));
 const addedNodes=z13Records.map((a,i)=>({id:a.nodeId,asset:a.id,title:a.title,summary:description[i],basis:description[i],
  tier:'C',chapter:'market',zoneId:'Z13',countAsCourtyard:false,initial:true,sourceContract,
  ...(i===4?{position:[294,1.2099999904632568,-1979],scale:[1,1,1],kind:'vessel'}:{matrix:clone(i<2?matrix:identity)})}));
 const after={...clone(beforeChapter),subtitle:'五店三摊与八铺四棚 · Z13市街设计',
  nodeIds:[...beforeChapter.nodeIds,...z13NodeIds],loadNodeIds:[...beforeChapter.loadNodeIds,...z13NodeIds],
  bounds:{min:[184.285995,0,-2050],max:[330,5.1301219,-1937.18396]},
  basis:beforeChapter.basis+' 新街段、支承、连续地表、视觉收边及一只灰陶碗为C级设计，保留既有市肆。'};
 const receipt={version:1,assets:clone(addedAssets),nodes:clone(addedNodes),chapterBefore:clone(beforeChapter),chapterAfter:clone(after),source:clone(source),budget};
 m.assets.push(...addedAssets);m.nodes.push(...addedNodes);m.chapters[index]=after;
 m.provenance.sourceContracts.push(clone(source));
 m.provenance.initialModelBytes+=budget;m.provenance.allCityModelBytes+=budget;
 m.provenance.z13Market={cityNodes:5,newDefaultBytes:budget,newCourtyards:0,originalCourtyards:47,automaticLOD:false};
 receipt.provenance=clone(m.provenance.z13Market);
 return {manifest:m,receipt};
}
export function withdrawZ13(input,receipt) {
 const canonical=installZ13({assets:[],nodes:[],chapters:[clone(beforeChapter)],provenance:{sourceContracts:[],initialModelBytes:0,allCityModelBytes:0}}).receipt;
 guard(equal(receipt,canonical),'Invalid or altered Z13 receipt');
 const m=clone(input), index=m.chapters.findIndex(c=>c.id==='market');
 guard(index>=0 && equal(m.chapters[index],receipt.chapterAfter),'Market chapter changed; withdrawal refused');
 guard(equal(m.provenance.z13Market,receipt.provenance),'Z13 provenance changed; withdrawal refused');
 for(const a of receipt.assets) guard(equal(m.assets.find(x=>x.id===a.id),a),'Z13 asset changed; withdrawal refused');
 for(const n of receipt.nodes) guard(equal(m.nodes.find(x=>x.id===n.id),n),'Z13 node changed; withdrawal refused');
 const ids=new Set(z13NodeIds),assetIds=new Set(receipt.assets.map(a=>a.id));
 guard(!m.nodes.some(n=>!ids.has(n.id)&&(assetIds.has(n.asset)||(n.replaces||[]).some(id=>ids.has(id)))),'New dependency on Z13; withdrawal refused');
 guard(!m.chapters.some(c=>c.id!=='market'&&[...(c.nodeIds||[]),...(c.loadNodeIds||[])].some(id=>ids.has(id))),'New chapter depends on Z13');
 guard(!m.researchModels?.some(n=>assetIds.has(n.asset)),'Research depends on Z13');
 const sources=m.provenance.sourceContracts.filter(s=>s.path===sourceContract);
 guard(sources.length===1 && equal(sources[0],receipt.source),'Z13 source changed; withdrawal refused');
 // Reverse dependency order: bowl, edge, then the street/support/ground group.
 for(const n of [...receipt.nodes].reverse()) m.nodes=m.nodes.filter(x=>x.id!==n.id);
 m.assets=m.assets.filter(a=>!assetIds.has(a.id));m.chapters[index]=clone(receipt.chapterBefore);
 m.provenance.sourceContracts=m.provenance.sourceContracts.filter(s=>s.path!==sourceContract);
 m.provenance.initialModelBytes-=receipt.budget;m.provenance.allCityModelBytes-=receipt.budget;delete m.provenance.z13Market;
 return m;
}
