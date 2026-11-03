export const LEVELS=['city','connection','district','junction','gate','market','storage'];
export function readState(search){const p=new URLSearchParams(search);return{level:LEVELS.includes(p.get('view'))?p.get('view'):'city',layout:p.get('layout')==='original'?'original':'calt',flow:p.get('flow')==='B'?'B':'A'};}
export function urlFor(state,current){const u=new URL(current);u.searchParams.set('mode','west');u.searchParams.set('view',state.level);u.searchParams.set('layout',state.layout);if(state.level==='market'&&state.flow==='B')u.searchParams.set('flow','B');else u.searchParams.delete('flow');return u;}
/** Last successful view remains authoritative through loading, cancellation and failures. */
export class Transaction {
 constructor(initial,{load,apply,dispose=()=>{},changed=()=>{}}){this.state=initial;this.load=load;this.apply=apply;this.dispose=dispose;this.changed=changed;this.epoch=0;this.controller=null;this.resource=null;this.pending=null;this.closed=false;}
 cancel(){++this.epoch;this.controller?.abort();this.controller=null;this.pending=null;this.changed('cancelled',this.state);}
 async go(next){if(this.closed)return false;this.cancel();const epoch=this.epoch;const controller=new AbortController();this.controller=controller;this.pending=next;this.changed('loading',this.state,next);let candidate=null;
  try{candidate=await this.load(next,controller.signal);if(this.closed||epoch!==this.epoch||controller.signal.aborted){if(candidate&&candidate!==this.resource)this.dispose(candidate);return false;}await this.apply(next,candidate,controller.signal);if(this.closed||epoch!==this.epoch||controller.signal.aborted){if(candidate&&candidate!==this.resource)this.dispose(candidate);return false;}const old=this.resource;this.resource=candidate;this.state=next;this.pending=null;this.controller=null;if(old&&old!==candidate)this.dispose(old);this.changed('ready',this.state);return true;
  }catch(error){if(candidate&&candidate!==this.resource)this.dispose(candidate);if(epoch===this.epoch&&!this.closed){this.pending=null;this.controller=null;this.changed(controller.signal.aborted?'cancelled':'error',this.state,next,error);}return false;}
 }
 close(){this.cancel();this.closed=true;if(this.resource)this.dispose(this.resource);this.resource=null;}
}
