"""Compose only from a separately verified immutable model-stage snapshot."""
from pathlib import Path
import json,shutil,html,argparse
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';M=ROOT/'model-stage'
V=['hinge','reach','poise'];P=['default','folded','extended'];titles={'hinge':'折光','reach':'伸展','poise':'挺立'};pt={'default':'基准姿态','folded':'收拢样本','extended':'展开样本'}
def esc(s):return html.escape(str(s),quote=True)
def info(v,p):return 'assets/'+v+('/poses/'+p if p!='default' else '')
def read(p):return json.loads((M/p).read_text())
def mm(n):return f'{n*1000:g}'
def build():
 D.mkdir(parents=True,exist_ok=True)
 if not (M/'manifest.json').is_file():raise ValueError('Model import has not been approved')
 data={'schema':'hinge-web-1','variants':{}};cards=[];downloads={};compare=[]
 for v in V:
  default=read(info(v,'default')+'/model-info.json');c=default['config'];stats={'arms':f"{mm(c['lower_length'])} / {mm(c['upper_length'])} mm",'base':f"Ø {mm(c['base_radius']*2)} mm",'head':f"Ø {mm(c['head_radius']*2)} mm"};poses={}
  for p in P:
   base=info(v,p);d=read(base+'/model-info.json');angles=d['pose']['angles_degrees'];center=d['pose']['head_center'];image='model/'+base+'/front.png'
   if not (M/base/'front.png').is_file():raise ValueError('Missing official pose image '+base)
   note='本姿态的实际角度来自生成记录；并非运动域极值或制造安全建议。'
   poses[p]={'title':pt[p],'note':note,'image':image,'angles':angles,'headCenter':center}
   cards.append(f'''<article class="atlas-card" id="{v}-{p}"><h3>{esc(titles[v])} <span>{esc(pt[p])}</span></h3><a href="{image}"><img loading="lazy" src="{image}" width="960" height="960" alt="{esc(titles[v]+' · '+pt[p])}真实front机位CPU图"></a><p>肩 {angles[0]}° · 相对肘 {angles[1]}° · 灯头世界角 {angles[2]}°</p><p>灯头中心 x / z：{center[0]*1000:.1f} / {center[2]*1000:.1f} mm</p><a href="model/{base}/model.glb" download data-download="{v}-{p}-glb">GLB 模型</a> · <a href="model/{base}/model.blend" download data-download="{v}-{p}-blend">原生 BLEND</a></article>''')
   for ext in ['glb','blend']:downloads[f'{v}-{p}-{ext}']={'href':f'model/{base}/model.{ext}','label':('GLB 模型' if ext=='glb' else '原生 BLEND')}
  data['variants'][v]={'title':titles[v]+' / '+v.upper(),'stats':stats,'poses':poses}
  compare.append(f'''<article><p class="eyebrow">{v.upper()}</p><h3>{titles[v]}</h3><dl><div><dt>下臂 / 上臂</dt><dd>{stats['arms']}</dd></div><div><dt>底座直径</dt><dd>{stats['base']}</dd></div><div><dt>灯头直径</dt><dd>{stats['head']}</dd></div></dl><p>相机与摄影尺度固定。比较的是几何比例，不代表照明覆盖或抗倾覆性能。</p></article>''')
 # Keep original model names and bytes below one prefix; originals are never overwritten by webpage files.
 (D/'model').mkdir(parents=True,exist_ok=True)
 for f in M.rglob('*'):
  if f.is_file():out=D/'model'/f.relative_to(M);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out)
 (D/'web-assets').mkdir(exist_ok=True);(D/'web-assets/pose-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');(D/'web-delivery.json').write_text(json.dumps({'downloads':downloads},ensure_ascii=False,indent=2)+'\n')
 for f in ['app.js','pose-state.js','style.css']:shutil.copyfile(ROOT/f,D/f)
 for directory in ['web-review','web-source']:
  if(ROOT/directory).is_dir():
   for f in(ROOT/directory).rglob('*'):
    if f.is_file()and '__pycache__'not in f.parts and f.suffix!='.pyc':
     out=D/directory/f.relative_to(ROOT/directory);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,out)
 for name in ['README-WEB.md','WEB-FROZEN.json','delivery-contract.json']:
  if(ROOT/name).is_file():shutil.copyfile(ROOT/name,D/name)
 a=data['variants']['hinge'];p=a['poses']['default'];s=a['stats'];q=p['angles'];c=p['headCenter']
 variants=''.join(f'<button type="button" data-variant="{v}" aria-pressed="{str(v=="hinge").lower()}"><span>0{i+1}</span><b>{titles[v]}</b><small>{v.upper()}</small></button>'for i,v in enumerate(V))
 poses=''.join(f'<button type="button" data-pose="{v}" aria-pressed="{str(v=="default").lower()}">{pt[v]}</button>'for v in P)
 (D/'index.html').write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="009折光：用三种真实几何与有限姿态样本研究关节、比例和复现边界。"><title>折光 HINGE · 姿态工作台 · 造物手记</title><link rel="stylesheet" href="style.css"><script defer src="pose-state.js"></script><script defer src="app.js"></script></head><body><a class="skip" href="#main">跳到工作台</a><header><a href="#main">造物手记 <span>CREATION NOTEBOOK</span></a><span>009 / FORM IN MOTION</span></header><main id="main"><section class="intro"><div><p class="eyebrow">HINGE / 折光</p><h1>把关节说清楚。</h1></div><p class="lede">三种比例，九个真实姿态样本。<br>同机位对照，不以美图代替验证。</p></section><section class="workbench" aria-label="姿态工作台"><div class="visual"><div class="plate-label"><span data-plate-tag>HINGE</span><span>FRONT / CPU</span></div><div data-image-frame><img src="{p['image']}" alt="折光基准姿态，固定front机位的CPU渲染" width="960" height="960"></div><div class="image-fallback" data-fallback hidden><strong>姿态图片未载入</strong><p>没有把空白视为验收通过。可重新载入，或打开下方静态图册。</p><a href="#atlas">查看图册与数据</a></div><p class="image-foot"><span data-caption>折光 / 基准姿态 / front同机位等幅裁片 / Cycles CPU</span><a data-original href="{p['image']}">原图 ↗</a></p></div><aside data-controls hidden><p class="eyebrow">01 / 选择几何</p><div class="variant-list" role="group" aria-label="几何变体">{variants}</div><p class="eyebrow pose-label">02 / 选择姿态</p><div class="pose-list" role="group" aria-label="有限姿态样本">{poses}</div><div class="statusline"><p data-status role="status" aria-live="polite"></p><button type="button" data-retry hidden>重新载入</button></div><div data-current-panel><h2 class="current-title"><span data-title>{a['title']}</span><small data-pose-title>{p['title']}</small></h2><dl class="current-stats"><div><dt>下臂 / 上臂</dt><dd data-stat="arms">{s['arms']}</dd></div><div><dt>底座 / 灯头直径</dt><dd><span data-stat="base">{s['base']}</span> / <span data-stat="head">{s['head']}</span></dd></div><div><dt>肩角（世界）</dt><dd data-angle="0">{q[0]}°</dd></div><div><dt>肘角（相对下臂）</dt><dd data-angle="1">{q[1]}°</dd></div><div><dt>灯头角（世界）</dt><dd data-angle="2">{q[2]}°</dd></div><div><dt>灯头中心 x / z</dt><dd data-center>{c[0]*1000:.1f} / {c[2]*1000:.1f} mm</dd></div></dl><p class="pose-note" data-note>{p['note']}</p></div><a class="text-link" href="#limits">这组数据能证明什么？ ↓</a></aside></section><noscript><p class="noscript">JavaScript 未运行。上方显示折光基准图；下方九个姿态图与对应数字、下载仍可用。交互切换不影响阅读完整内容。</p></noscript><nav class="section-nav" aria-label="页面章节"><a href="#proportions">比例对照</a><a href="#atlas">九幅姿态</a><a href="#limits">验证边界</a><a href="#process">复现与复盘</a></nav><section id="proportions"><div class="section-heading"><p class="eyebrow">FORM / 比例</p><h2>不只换一种颜色。</h2><p>下臂、上臂、底座和灯头共同定义几何变体。数值是生成输入，不是受力或照明指标。</p></div><div class="comparison">{''.join(compare)}</div></section><section class="editorial"><div><p class="eyebrow">DETAIL / 接点</p><h2>转轴要能被看见，<br>接触也要能被解释。</h2><p>模型的相邻构件需要局部检查。一个合法铰接不能成为整对构件穿插的通行证。图中的间隙与装配关系属于几何研究，不代表轴承、公差或耐久测试。</p><a href="model/assets/hinge/joint.png">打开接点原图 ↗</a></div><img loading="lazy" src="model/assets/hinge/joint.png" width="960" height="960" alt="折光实际关节近景CPU渲染"></section><section id="atlas"><div class="section-heading"><p class="eyebrow">POSE ATLAS / 有限样本</p><h2>同一机位，逐幅比较。</h2><p>肩角和灯头角以世界 x 轴为参考；肘角相对下臂。x 为水平、z 为高度，原点与模型一致。灯头中心坐标不等于灯具的外包尺寸，更不是最大伸展范围。这里只切换离散渲染，不提供已验实时动画。</p></div><div class="atlas">{''.join(cards)}</div></section><section id="limits" class="limits"><p class="eyebrow">EVIDENCE / 结论的边界</p><h2>能复现，不等于能制造。</h2><div class="limit-grid"><div><h3>本页可复现</h3><p>三种几何与九个摄影姿态、角度和参数。实际图与数值一起提交；读取失败时保留上一组完整结果。</p></div><div><h3>按报告理解检查</h3><p>几何门禁、实际GLB导出一致性与运动样本的覆盖是不同证据。请查原始报告，不把有限采样推广为连续角度范围保证。</p></div><div><h3>仍未验证</h3><p>真实GPU渲染和闪烁、实体手机、负载平衡、抗倾覆、照度、电气安全和制造公差。本作不是可投入使用的灯具设计。</p></div></div></section><section id="process"><div class="section-heading"><p class="eyebrow">REPRODUCE / 复现与复盘</p><h2>把条件也一起留下。</h2><p>原模型包全量保留在 model/，原件字节不变。正式源包另随造物手记归档交付；下面提供可直接读取的输入、脚本与检查入口。</p></div><div class="resource-list"><a href="model/README.md">模型说明与复现条件 ↗</a><a href="model/manifest.json">模型文件身份清单 ↗</a><a href="web-review/model-parity.json">网页导入字节核验 ↗</a><a href="web-review/reference-notes.html">网页对标与具体改进 ↗</a><a href="web-review/reflection.html">交互验收与剩余不足 ↗</a></div></section></main><footer><span>造物手记 · Creation Notebook</span><span>把想象做成有形之物，把经验留下来。</span><p>009 / 本地已归档；发布状态以总览为准。CPU 图不代表 GPU 验收。</p></footer></body></html>''',encoding='utf8')
 if (D/'web-assets/draft-beauty.png').exists():(D/'web-assets/draft-beauty.png').unlink()
 return data
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--model-dir',type=Path);parser.add_argument('--output',type=Path);a=parser.parse_args()
 if a.model_dir:M=a.model_dir.resolve()
 elif not M.exists():M=ROOT/'model'
 if a.output:D=a.output.resolve()
 elif not(ROOT/'model-stage').exists():D=ROOT/'rebuilt'
 if D==ROOT or D==M or M.is_relative_to(D):raise ValueError('Use a separate output directory, not the original model or source root')
 build();print('009 composed from approved model snapshot')
