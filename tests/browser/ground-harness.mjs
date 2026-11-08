import baseline from './ground-baseline-city-data.mjs';
import {installDisplayGround,withdrawDisplayGround} from './ground-content.mjs';
import {createCityRenderer} from './city-navigation-renderer.mjs';
const stage=document.querySelector('#stage');let current=structuredClone(baseline),receipt,renderer,evidence=false;
const views=[{id:'qa-ground-wide',camera:{position:[3200,2800,-4400],target:[1300,0,-1950]}},{id:'qa-ground-wall',camera:{position:[-12,1.4,-1398],target:[-20,0,-1400]}},{id:'qa-ground-market',camera:{position:[310,2,-1990],target:[300,0,-2000]}}];
views.push({id:'qa-ground-road',camera:{position:[297,.7,-1959],target:[297,.16,-1962.18396]}},{id:'qa-ground-well',camera:{position:[801.2,1.6,-1048.8],target:[800,-.15,-1050]}});
const qa=window.groundQA={ready:false,epoch:0,serial:0,actionSerial:0,state:null,states:[],metrics:[],selected:null,selectionSerial:0,actions:[],errors:[],mode:'baseline'};
async function mount(){
 qa.ready=false;renderer?.dispose();stage.replaceChildren();qa.selected=null;
 const epoch=++qa.epoch,canvas=document.createElement('canvas');canvas.id='ground-qa-canvas';stage.append(canvas);
 const manifest=structuredClone(current);manifest.chapters.push(...views.map(v=>({...v,nodeIds:[],loadNodeIds:[]})));
 renderer=await createCityRenderer({canvas,manifest,onViewChange:s=>{qa.state=s;qa.serial++;qa.states.push({epoch,time:performance.now(),...structuredClone(s)});if(qa.states.length>300)qa.states.shift();},onMetrics:m=>{qa.metrics.push({epoch,time:performance.now(),...m});if(qa.metrics.length>300)qa.metrics.shift();},onSelect:n=>{qa.selected=n;qa.selectionSerial++;}});
 renderer.setPlanningVisible(false);renderer.setEvidenceVisible(evidence);qa.manifest=structuredClone(current);qa.ready=true;
}
async function act(event,fn){const a={id:event.currentTarget.id||event.currentTarget.dataset.focus,trusted:event.isTrusted,start:performance.now()};qa.actions.push(a);try{await fn();a.finished=performance.now();qa.actionSerial++;}catch(e){a.error=String(e);qa.errors.push(String(e));throw e;}}
document.querySelector('#install').onclick=e=>act(e,async()=>{const x=installDisplayGround(current);current=x.manifest;receipt=x.receipt;qa.mode='installed';await mount();});
document.querySelector('#withdraw').onclick=e=>act(e,async()=>{current=withdrawDisplayGround(current,receipt);qa.mode='withdrawn';await mount();});
for(const b of document.querySelectorAll('[data-focus]'))b.onclick=e=>act(e,()=>renderer.focusChapter(b.dataset.focus));
document.querySelector('#research').onclick=e=>act(e,()=>renderer.focusResearchModel('research-lingtai'));
document.querySelector('#city').onclick=e=>act(e,()=>renderer.resetView());
document.querySelector('#evidence').onclick=e=>act(e,()=>{evidence=!evidence;renderer.setEvidenceVisible(evidence);});
document.querySelector('#redraw').onclick=e=>act(e,()=>renderer.setEvidenceVisible(evidence));
await mount();
