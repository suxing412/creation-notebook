import original from './z13-baseline-data.mjs';
import { installZ13,withdrawZ13 } from './z13-content.mjs';
import { createCityRenderer } from './city-navigation-renderer.mjs';
const stage=document.querySelector('#stage');
let current=structuredClone(original),receipt,renderer,evidence=false;
window.qa={ready:false,serial:0,state:null,metrics:[],selected:null,errors:[],trusted:[],mode:'baseline'};
const qa=window.qa;
const views=[
 {id:'qa-bowl',camera:{position:[296.1,2,-1979.4],target:[290.6454545454545,0,-1978.3610389610387]}},
 {id:'qa-edge',camera:{position:[310,.8,-1967.1839599609375],target:[310,0,-1961.8268171123475]}},
 {id:'qa-oblique',camera:{position:[325,7,-1972],target:[298,0,-1962.1839599609375]}}
];
async function mount(){
 qa.ready=false;renderer?.dispose();stage.replaceChildren();
 const canvas=document.createElement('canvas');stage.append(canvas);canvas.id='qa-canvas';
 const manifest=structuredClone(current);manifest.chapters.push(...views.map(v=>({...v,nodeIds:[],loadNodeIds:[]})));
 renderer=await createCityRenderer({canvas,manifest,onViewChange:s=>{qa.state=s;qa.serial++;},onMetrics:m=>qa.metrics.push(m),onSelect:n=>{qa.selected=n;document.querySelector('#picked').textContent=n.title||n.id;}});
 renderer.setPlanningVisible(false);renderer.setEvidenceVisible(evidence);
 qa.ready=true;qa.manifest=structuredClone(current);
}
async function act(event,fn){qa.trusted.push({id:event.currentTarget.id||event.currentTarget.dataset.focus,isTrusted:event.isTrusted});try{await fn();}catch(e){qa.errors.push(String(e));throw e;}}
document.querySelector('#install').onclick=e=>act(e,async()=>{const result=installZ13(current);current=result.manifest;receipt=result.receipt;qa.mode='installed';await mount();});
document.querySelector('#withdraw').onclick=e=>act(e,async()=>{current=withdrawZ13(current,receipt);qa.mode='withdrawn';await mount();});
for(const button of document.querySelectorAll('[data-focus]'))button.onclick=e=>act(e,()=>renderer.focusChapter(button.dataset.focus));
document.querySelector('#evidence').onclick=e=>act(e,()=>{evidence=!evidence;renderer.setEvidenceVisible(evidence);});
document.querySelector('#redraw').onclick=e=>act(e,()=>renderer.setEvidenceVisible(evidence));
await mount();
