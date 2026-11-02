/** Route and 3D lifetimes are independent. show/commit are synchronous atomic commits. */
export class ObservationState {
 constructor({decode,commit,parse,show,dispose,hide=()=>{},status=()=>{}}){Object.assign(this,{decode,commit,parse,show,dispose,hide,status});this.route=0;this.session=0;this.current={id:'veil',view:'beauty'};this.requested={...this.current};this.hasCommit=false;this.want3d=false;this.dead=false;}
 invalidateLive(){++this.session;this.abort?.abort();this.abort=undefined;this.hide();}
 cancel3d(message='已回到静态图；模型读取与实时渲染已停止。'){this.want3d=false;this.invalidateLive();if(!this.dead)this.status(message);}
 async navigate(next,context={}){
  if(this.dead)return false;
  const generation=++this.route;this.requested={...next};this.invalidateLive();this.status('正在读取新视图；上一组正确图文与下载暂时保留。');
  try{
   const image=await this.decode(next);
   if(this.dead||generation!==this.route)return false;
   this.invalidateLive(); // A new activation may have begun while this image was decoding.
   this.current={...next};this.hasCommit=true;
   this.commit(this.current,image,context,generation);
   this.status('静态渲染已就绪。可按需载入同一变体的真实 GLB。');
   if(this.want3d)void this.activate();
   return true;
  }catch(error){
   if(!this.dead&&generation===this.route){this.requested={...this.current};this.status(this.hasCommit?'新图读取失败；仍保留上一组正确图文与下载。':'正式静态图暂时不可读。下方正文与文件入口仍保留；未显示替代模型。');}
   return false;
  }
 }
 async activate(){
  if(this.dead||!this.hasCommit)return false;
  this.want3d=true;const generation=++this.session;this.abort?.abort();const abort=this.abort=new AbortController(),route={...this.current};
  this.status('读取真实 GLB；静态图继续可见。');let object;
  try{
   object=await this.parse(route.id,abort.signal);
   if(this.dead||generation!==this.session||!this.want3d||route.id!==this.current.id){this.dispose(object);return false;}
   this.show(object,route);
   this.status('真实 GLB 已载入。材质来自文件；实时光照不等同于 Cycles 渲染。');
   return true;
  }catch(error){
   if(object)this.dispose(object);
   if(this.dead||generation!==this.session||error.name==='AbortError')return false;
   this.want3d=false;this.hide();this.status('实时不可用：'+error.message+'。静态图、正文与下载仍可使用。');return false;
  }
 }
 contextLost(){this.cancel3d('WebGL 上下文丢失，已回静态图；不更改浏览器安全设置。');}
 failLive(message){this.cancel3d('实时渲染中断：'+message+'。静态阅读保留。');}
 destroy(){this.dead=true;++this.route;this.want3d=false;this.invalidateLive();}
}
