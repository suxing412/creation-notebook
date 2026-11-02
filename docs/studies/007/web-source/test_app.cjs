const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const path=require('node:path'),crypto=require('node:crypto');const root=path.resolve(__dirname,'..')+'/';
class E {constructor(dataset={}){this.dataset=dataset;this.listeners={};this.hidden=false;this.attrs={};this.textContent='';}addEventListener(type,f){(this.listeners[type]??=[]).push(f);}setAttribute(k,v){this.attrs[k]=v;}fire(type){for(const f of this.listeners[type]||[])f();} replaceWith(img){group.image=img;}}
let group,images;
function setup(complete=false,width=0){
 images=[];let a=new E();a.src='a.png';a.alt='A';a.complete=complete;a.naturalWidth=width;
 const buttons=['a','b','c'].map(key=>{let e=new E({view:key,src:key+'.png',alt:key.toUpperCase(),caption:key+' caption'});e.textContent=key;return e;});
 const caption=new E();caption.textContent='a caption'; const original=new E();original.href='a.png';const status=new E(),fallback=new E(),retry=new E(),controls=new E();
 group=new E({initial:'a'});group.image=a;
 group.querySelector=q=>({'[data-current-image]':a,'[data-caption]':caption,'[data-original]':original,'[data-status]':status,'[data-fallback]':fallback,'[data-retry]':retry,'[data-controls]':controls})[q];group.querySelectorAll=()=>buttons;
 const ctx={console,Image:class extends E {constructor(){super();images.push(this);}decode(){return Promise.resolve();}},document:{querySelector:()=>group,documentElement:{classList:{add:()=>{}}}},window:{}};ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync(root+'gallery-state.js','utf8'),ctx);vm.runInContext(fs.readFileSync(root+'app.js','utf8'),ctx);
 return{a,buttons,caption,original,status,fallback,retry};
}
async function tick(){await Promise.resolve();await Promise.resolve();await Promise.resolve();}
(async()=>{const cases=[];
 {const t=setup();t.buttons[1].fire('click');t.a.fire('load');images[0].onerror();await tick();assert.equal(group.image,t.a);assert.equal(t.a.hidden,false);assert.equal(t.caption.textContent,'a caption');assert.equal(t.buttons[0].attrs['aria-pressed'],'true');cases.push('A pending → B request → A late loaded → B error: A metadata retained');}
 {const t=setup();t.buttons[1].fire('click');images[0].onerror();await tick();t.a.fire('load');assert.equal(t.a.hidden,false);assert.match(t.status.textContent,/失败/);cases.push('B fails before A late success: A revealed while B failure retained');}
 {const t=setup(true,960);t.buttons[1].fire('click');t.buttons[2].fire('click');images[1].onload();await tick();images[0].onload();await tick();assert.equal(group.image.alt,'C');assert.equal(t.caption.textContent,'c caption');assert.equal(t.original.href,'c.png');assert.equal(t.buttons[2].attrs['aria-pressed'],'true');cases.push('B/C decode reversed: C image, alt, caption, href and selection');}
 {const t=setup();t.buttons[1].fire('click');images[0].onload();await tick();t.a.fire('error');assert.equal(group.image.alt,'B');assert.equal(group.image.hidden,false);assert.equal(t.caption.textContent,'b caption');assert.equal(t.retry.hidden,true);cases.push('B loaded → A late error: B remains');}
 {const t=setup(true,0);assert.equal(t.a.hidden,true);t.buttons[1].fire('click');images[0].onerror();await tick();t.retry.fire('click');images[1].onload();await tick();assert.equal(group.image.alt,'B');assert.equal(t.caption.textContent,'b caption');assert.equal(t.retry.hidden,true);cases.push('Initial 404 → B404 → retry B success: synchronized recovery');}
 const report={passed:true,source_sha256:{app:crypto.createHash('sha256').update(fs.readFileSync(root+'app.js')).digest('hex'),state:crypto.createHash('sha256').update(fs.readFileSync(root+'gallery-state.js')).digest('hex')},scope:'Fake DOM execution of actual app.js and state module; not native browser verification',cases};if(process.argv[2])fs.writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');console.log(report);
})().catch(e=>{console.error(e);process.exitCode=1;});
