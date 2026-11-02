/** Independent route and GPU-session lifetimes. No DOM dependencies; testable with deferred work. */
export class ObservationState {
 constructor({decode,commit,parse,show,dispose,status}){Object.assign(this,{decode,commit,parse,show,dispose,status});this.route=0;this.session=0;this.current={id:'orison',view:'beauty'};this.want3d=false;this.dead=false;}
 cancel3d(message='已取消实时读取；离线图保留。'){this.want3d=false;this.session++;this.abort?.abort();this.abort=undefined;this.status(message);}
 async navigate(next){const generation=++this.route;this.session++;this.abort?.abort();this.status('正在验证新视图；当前图文保持不变。');try{const image=await this.decode(next);if(this.dead||generation!==this.route)return false;this.current={...next};this.commit(this.current,image);if(this.want3d)void this.activate();return true;}catch(e){if(!this.dead&&generation===this.route)this.status('新图读取失败；仍保留上一组正确图文和下载。');return false;}}
 async activate(){if(this.dead)return;this.want3d=true;const generation=++this.session;this.abort?.abort();const abort=this.abort=new AbortController();const id=this.current.id;this.status('读取真实 GLB；离线图片继续可见。');let object;try{object=await this.parse(id,abort.signal);if(this.dead||generation!==this.session||!this.want3d||id!==this.current.id){this.dispose(object);return;}await this.show(object,id);if(this.dead||generation!==this.session||!this.want3d){this.dispose(object);return;}this.status('真实 GLB 已载入；实时光照与离线渲染不同。');}catch(e){if(object)this.dispose(object);if(this.dead||generation!==this.session||e.name==='AbortError')return;this.want3d=false;this.status('实时不可用：'+e.message+'。离线图、文字与下载仍可使用。');}}
 contextLost(){this.cancel3d('WebGL 上下文丢失；离线证据继续可用，不修改安全设置。');}
 destroy(){this.dead=true;++this.route;this.cancel3d('');}
}
