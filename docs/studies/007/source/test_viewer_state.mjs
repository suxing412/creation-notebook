import {ObservationState} from '../viewer/state.js';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};};
const cases=[];
function harness(){const decodes=[],parses=[],commits=[],shows=[],disposed=[],messages=[];const s=new ObservationState({decode:next=>{const d=deferred();decodes.push({...d,next});return d.promise;},commit:(r,i)=>commits.push({r,i}),parse:(id,signal)=>{const d=deferred();parses.push({...d,id,signal});return d.promise;},show:o=>shows.push(o),dispose:o=>disposed.push(o),status:m=>messages.push(m)});return{s,decodes,parses,commits,shows,disposed,messages};}
{
 const h=harness(),a=h.s.navigate({id:'latitude',view:'front'}),b=h.s.navigate({id:'ascend',view:'side'});h.decodes[1].resolve('new');await b;h.decodes[0].resolve('old');await a;assert.equal(h.commits.length,1);assert.equal(h.s.current.id,'ascend');cases.push('out-of-order image decode commits only newest image+metadata');
}
{
 const h=harness(),a=h.s.navigate({id:'latitude',view:'side'});h.decodes[0].reject(Error('broken'));await a;assert.equal(h.commits.length,0);assert.equal(h.s.current.id,'orison');cases.push('broken image preserves committed identity');
}
{
 const h=harness(),a=h.s.activate();h.s.cancel3d();h.parses[0].resolve('old3d');await a;assert.deepEqual(h.disposed,['old3d']);assert.equal(h.shows.length,0);const b=h.s.activate();h.parses[1].resolve('new3d');await b;assert.deepEqual(h.shows,['new3d']);cases.push('cancel pending parse then restart disposes stale scene and shows new');
}
{
 const h=harness(),a=h.s.navigate({id:'latitude',view:'side'});h.s.contextLost();h.decodes[0].resolve('image');await a;assert.equal(h.s.current.id,'latitude');assert.equal(h.commits.length,1);cases.push('context loss does not cancel independent pending image route');
}
{
 const h=harness(),a=h.s.activate(),b=h.s.navigate({id:'latitude',view:'front'});h.s.cancel3d();h.decodes[0].resolve('newimage');await b;h.parses[0].resolve('stale');await a;assert.equal(h.s.current.id,'latitude');assert.equal(h.shows.length,0);assert.equal(h.parses.length,1);cases.push('offline during pending route commits image without restarting GPU');
}
{
 const h=harness(),a=h.s.activate(),b=h.s.activate();assert.equal(h.parses[0].signal.aborted,true);h.parses[1].resolve('new');await b;h.parses[0].resolve('old');await a;assert.deepEqual(h.shows,['new']);assert.deepEqual(h.disposed,['old']);cases.push('repeated activation uses latest session only');
}
{
 const h=harness(),a=h.s.navigate({id:'latitude',view:'front'}),b=h.s.activate();h.s.destroy();h.decodes[0].resolve('late');h.parses[0].resolve('late3d');await Promise.all([a,b]);assert.equal(h.commits.length,0);assert.equal(h.shows.length,0);assert.deepEqual(h.disposed,['late3d']);cases.push('destroy invalidates image and GPU session');
}
{
 const h=harness(),a=h.s.activate(),b=h.s.navigate({id:'latitude',view:'side'});h.parses[0].reject(Error('GPU failure'));await a;h.decodes[0].resolve('newimage');await b;assert.equal(h.s.current.id,'latitude');assert.equal(h.commits.length,1);cases.push('GPU failure cannot invalidate pending independent image route');
}
fs.writeFileSync(new URL('../review/viewer-state-tests.json',import.meta.url),JSON.stringify({passed:true,scope:'Node deferred-promise simulation of actual state controller, not native browser or GPU',cases},null,2));console.log(cases.length+' state cases passed');
