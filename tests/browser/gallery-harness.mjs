import baseline from './gallery-baseline-data.mjs';
import {installGallery,withdrawGallery} from './gallery-content.mjs';
import {createCityRenderer} from './city-navigation-renderer.mjs';
import {galleryViews} from './gallery-qa-geometry.mjs';
const stage=document.querySelector('#stage');
let current=structuredClone(baseline),receipt,renderer,evidence=false;
const qa=window.galleryQA={ready:false,serial:0,epoch:0,actionSerial:0,state:null,states:[],metrics:[],selected:null,selectionSerial:0,actions:[],inputs:[],errors:[],mode:'baseline'};
for(const type of ['pointerdown','pointerup','click'])document.addEventListener(type,e=>{
 qa.inputs.push({type,time:e.timeStamp,trusted:e.isTrusted,pointerId:e.pointerId,pointerType:e.pointerType,x:e.clientX,y:e.clientY,path:e.composedPath().map(n=>n.id).filter(Boolean)});
},true);
async function mount(){
 qa.ready=false;renderer?.dispose();stage.replaceChildren();qa.selected=null;
 const epoch=++qa.epoch,canvas=document.createElement('canvas');canvas.id='gallery-qa-canvas';stage.append(canvas);
 const manifest=structuredClone(current);manifest.chapters.push(...galleryViews.map(v=>({...v,nodeIds:[],loadNodeIds:[]})));
 renderer=await createCityRenderer({canvas,manifest,
  onViewChange:state=>{qa.state=state;qa.serial++;qa.states.push({epoch,time:performance.now(),...structuredClone(state)});if(qa.states.length>240)qa.states.shift();},
  onMetrics:metrics=>{qa.metrics.push({epoch,time:performance.now(),...metrics});if(qa.metrics.length>240)qa.metrics.shift();},
  onSelect:node=>{qa.selected=node;qa.selectionSerial++;document.querySelector('#picked').textContent=node.title||node.id;},
 });
 renderer.setPlanningVisible(false);renderer.setEvidenceVisible(evidence);qa.manifest=structuredClone(current);qa.ready=true;
}
async function act(event,fn){
 const action={id:event.currentTarget.id||event.currentTarget.dataset.focus,trusted:event.isTrusted,start:performance.now()};qa.actions.push(action);
 try{await fn();action.finished=performance.now();qa.actionSerial++;}catch(error){action.error=String(error);qa.errors.push(String(error));throw error;}
}
document.querySelector('#install').onclick=e=>act(e,async()=>{const installed=installGallery(current,{scope:'all-eight'});current=installed.manifest;receipt=installed.receipt;qa.mode='installed';await mount();});
document.querySelector('#withdraw').onclick=e=>act(e,async()=>{current=withdrawGallery(current,receipt);qa.mode='withdrawn';await mount();});
for(const button of document.querySelectorAll('[data-focus]'))button.onclick=e=>act(e,()=>renderer.focusChapter(button.dataset.focus));
document.querySelector('#evidence').onclick=e=>act(e,()=>{evidence=!evidence;renderer.setEvidenceVisible(evidence);});
document.querySelector('#redraw').onclick=e=>act(e,()=>renderer.setEvidenceVisible(evidence));
await mount();
