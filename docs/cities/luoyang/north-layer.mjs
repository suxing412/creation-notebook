const B='north_palace_extent_gao2023_B';
export function createNorthLayer(ctx,isCity){
 let data=null,error=null,visible=false,closed=false,controller=null;const box=document.createElement('details');box.id='north-conflict';box.style.cssText='width:100%;border-top:1px solid #756e54;padding-top:8px';box.open=false;
 function refresh(){ctx.updateEvidenceVisibility?.();ctx.redraw();ctx.layout();}
 function draw(){
 box.replaceChildren();const title=document.createElement('summary');title.textContent='北宫证据待核 · '+(visible?'旧B对照已开启':'旧B对照已关闭');box.append(title);
 if(!data){const p=document.createElement('p');p.textContent=error?'北宫说明载入失败：旧B保持关闭，A无坐标；不生成修正宫域。':'正在读取北宫冲突说明；旧B保持关闭。';box.append(p);if(error){const b=document.createElement('button');b.textContent='重试北宫说明';b.onclick=load;box.append(b);}const a=document.createElement('a');a.href='research/2026-11-03/';a.textContent='已保存研究/来源';box.append(a);return;}
 const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=visible;input.onchange=()=>{visible=input.checked;draw();refresh()};label.append(input,document.createTextNode(data.ui_contract.toggle_label));box.append(label);
 const status=document.createElement('p');status.setAttribute('role','status');status.textContent=(visible?'旧B虚线仅供对照；':'旧B轮廓已关闭；')+'新东/南墙A尚未配准，内部布局未知，东掖门始建魏晋、不能纳入东汉门址。';box.append(status);
 for(const layer of data.layers){const p=document.createElement('p'),b=document.createElement('strong');b.textContent=layer.label+'：';p.append(b,document.createTextNode(layer.limits.join('；')));box.append(p);}
 const p=document.createElement('p');p.textContent='42项冻结证据不变；这些说明不新增坐标、模型、作品。未配准，不能计算新旧面积/偏移或绘精确差异区。';box.append(p);
 for(const source of data.sources){const a=document.createElement('a');a.href=source.url;a.textContent=source.title+'（'+source.date+'）';a.target='_blank';a.rel='noopener';const p=document.createElement('p');p.append(a,document.createTextNode(' — '+source.read_status));box.append(p);}
 }
 async function load(){controller?.abort();controller=new AbortController();data=null;error=null;visible=false;draw();refresh();try{const r=await fetch('./data/west/north-palace-conflict-layer.json',{signal:controller.signal});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(d.frozen_baseline.feature_count!==42||d.layers.some(l=>l.id!=='legacy_B'&&l.geometry_policy!=='none')||d.layers.find(l=>l.id==='legacy_B')?.feature_ref!==B)throw Error('说明层契约不匹配');if(closed)return;data=d;draw();refresh();}catch(e){if(closed||e.name==='AbortError')return;error=e;draw();refresh();}}
 draw();queueMicrotask(load);
 return{visible:id=>id!==B||visible,mount(){if(isCity()&&!box.isConnected)document.getElementById('choices').append(box);else if(!isCity())box.remove()},dispose(){closed=true;controller?.abort();box.remove()}};
}
