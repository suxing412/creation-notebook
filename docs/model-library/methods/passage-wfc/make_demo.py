import pathlib,json,html
P=pathlib.Path(__file__).parent;R=json.loads((P/'results.json').read_text());T=json.loads((P/'states.json').read_text());D=[(0,-1),(1,0),(0,1),(-1,0)]
def svg(r):
 s='<svg viewBox="0 0 300 300" role="img" aria-label="通行连接图，北向上"><rect width="300" height="300" fill="#e5d6b9"/>'
 for i,t in enumerate(r['layout']):
  x=(i%3)*100+50;y=(2-i//3)*100+50;s+=f'<circle cx="{x}" cy="{y}" r="7" fill="#31554e"/>'
  for d in T[t]['ports']:
   dx,dy=D[d];s+=f'<path d="M{x},{y}L{x+dx*50},{y+dy*50}" stroke="#31554e" stroke-width="12"/>'
 return s+'</svg>'
rows=''.join(f'<tr><td>{r["seed"]}</td><td>{r["status"]}</td><td>{r["domain_contractions"]}</td><td>{r["removed_states"]}</td><td>{html.escape(str(r["validation"]["errors"]))}</td></tr>' for r in R)
p='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>通行接口试件 · WFC方法研究</title><style>body{background:#efe9da;color:#243d35;font:16px/1.7 system-ui;margin:0}main{max-width:1140px;margin:auto;padding:28px}h1{font-size:clamp(30px,5vw,54px);line-height:1.2}header{border-bottom:2px solid;padding:20px 0}section{margin:32px 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:18px}article{background:#fffaf0;padding:16px;border:1px solid #b8b7a2}img,svg{width:100%}h2{font-size:23px}table{border-collapse:collapse;width:100%}th,td{padding:7px;text-align:left;border-bottom:1px solid #ccc;font-size:13px}.scroll{overflow:auto}select{font:inherit;padding:8px}:focus-visible{outline:3px solid #a65e32}a{color:#245d59}#detail{max-width:450px}</style><main><header><p>CREATION NOTEBOOK / METHOD RESEARCH</p><h1>接得上，不代表走得通。</h1><p>四类真实3D通行试件 · 20个固定seed · 3类非同构连通图</p><strong>纯C类规则研究，不是汉代形制、住宅近景模型或洛阳城成品。未公开、未接城。</strong></header><section><h2>先登记模型，再测试组合</h2><p>薄地坪、木挡板，直/弯/T/端头共一个资产组。固定边界入口出口，不预锁内部道路。20个局部解中17个全局断连，仅7、15、18通过。全部失败保留，没有为成功重启或更换seed。</p><p>下面是真实GLB实例化的CPU渲染，不是实时三维视图，也不是2D图牌代替几何。</p></section><section class="cards">'''
for seed in [7,15,18]:
 r=R[seed];v=r['validation']['topology_invariant'];p+=f'<article><h2>Seed {seed}</h2><img src="previews/seed-{seed}-cpu.png" alt="Seed {seed}真实通行试件组合的CPU渲染" loading="lazy">{svg(r)}<p>边数 {v["edges"]}；环路秩 {v["cycle_rank_if_connected"]}；度数分布 {html.escape(str(v["degree_histogram"]))}。</p><a href="assets/seed-{seed}.glb" download>下载该组合GLB</a></article>'
p+='</section><section><h2>每个seed都可检查</h2><label for="seed">种子</label><select id="seed">'+''.join(f'<option value="{r["seed"]}">{r["seed"]} · {r["status"]}</option>' for r in R)+'</select><div id="detail"><p>无脚本仍可阅读三例、完整结果和下载链接。</p></div></section>'
p+='<section class="scroll"><h2>完整20样本</h2><table><thead><tr><th>Seed</th><th>状态</th><th>域收缩</th><th>删除候选</th><th>全局错误</th></tr></thead><tbody>'+rows+'</tbody></table></section>'
p+='''<section><h2>结论与边界</h2><p>WFC确实传播相邻端口限制，直/弯/T/端头改变真实通路；但局部规则无法排除孤立分量。下一步应评估全局路径约束或有界回溯，而不是锁死所有路。</p><p>4米格、1.6米口、0.2米地坪、2.2米预留净高均为试验参数。独立几何检查针对盒体与正交变换；相邻地坪仍有内部接触端面，未合并消除。无GPU/手机/引擎验收。</p><p>前三例度分布或环路数不同，证明至少三类非同构图，不仅旋转/镜像。样本通过率3/20不代表全部seed。</p><p><a href="https://www.boristhebrave.com/2020/02/08/wave-function-collapse-tips-and-tricks/">Boris：局部约束与全局路径</a> · <a href="https://github.com/mxgmn/WaveFunctionCollapse">Maxim Gumin原始WFC</a></p></section>'''
data=[{'seed':r['seed'],'status':r['status'],'svg':svg(r),'errors':r['validation']['errors']} for r in R]
p+='<script>const DATA='+json.dumps(data)+';const sel=document.getElementById("seed");function show(){let r=DATA[Number(sel.value)];document.getElementById("detail").innerHTML="<h2>"+r.seed+" · "+r.status+"</h2>"+r.svg+"<p>"+r.errors.join("；")+"</p>";}sel.addEventListener("change",show);show();</script></main></html>'
import re
(P/'graphs').mkdir(exist_ok=True)
for r in R:
 graph=svg(r).replace('\\"','"').replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" ',1)
 (P/'graphs'/f'seed-{r["seed"]}.svg').write_text(graph)
p=re.sub(r'<script>.*?</script>','<script src="ui-script.js" defer></script>',p,flags=re.S)
selected=iter([7,15,18])
p=re.sub(r'<svg.*?</svg>',lambda m:f'<img src="graphs/seed-{next(selected)}.svg" alt="连接图，非三维图">',p,flags=re.S)
data=[{'seed':r['seed'],'status':r['status'],'errors':r['validation']['errors']} for r in R]
js='const DATA='+json.dumps(data)+';const sel=document.getElementById("seed");function show(){const r=DATA[Number(sel.value)];const box=document.getElementById("detail");box.replaceChildren();const h=document.createElement("h2");h.textContent=r.seed+" · "+r.status;const img=document.createElement("img");img.src="graphs/seed-"+r.seed+".svg";img.alt="通行连接图，非三维渲染";const p=document.createElement("p");p.textContent=r.errors.join("；");box.append(h,img,p)}sel.addEventListener("change",show);show();'
(P/'ui-script.js').write_text(js)
p=re.sub(r'<script>.*?</script>','<script src="ui-script.js" defer></script>',p,flags=re.S)
p=p.replace('<section><h2>先登记模型，再测试组合</h2>','<section><p>三种非同构仅指连接图拓扑。真实几何为地坪/挡板盒体，内部接触面保留，不是汉代建筑、013近景品质或GPU验收。</p><h2>先登记模型，再测试组合</h2>')
(P/'index.html').write_text(p)
