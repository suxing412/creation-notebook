"""Build the reader only from a verified, frozen complete model import."""
from pathlib import Path
import json,html,shutil,argparse
R=Path(__file__).resolve().parents[1];M=R/'model-stage';D=R/'dist'
V=['slot','span','rise'];W=['beauty','exploded','joint'];names={'slot':'栖格','span':'横展','rise':'高序'}
def e(x):return html.escape(str(x),quote=True)
def mm(x):return f'{x*1000:g}'
def triptych(a,lazy=False,live=False):
 out=[]
 for i,v in enumerate(W):
  b=a['views'][v];tag=lambda k:f' data-{k}="{v}"' if live else ''
  out.append(f'''<figure><div class="image-frame"{tag('frame')}><img src="{e(b['image'])}" width="960" height="960" alt="{e(b['alt'])}" {'loading="lazy"' if lazy else ''}></div><figcaption><strong>0{i+1} / {['看整体','拆开读','看槽口'][i]}</strong><p{tag('caption')}>{e(b['caption'])}</p><a class="original" href="{e(b['image'])}"{tag('original')}>打开真实渲染原图 ↗</a></figcaption></figure>''')
 return '<div class="triptych">'+''.join(out)+'</div>'
def facts(a):return ''.join(f'<div><dt>{e(f["label"])}</dt><dd>{e(f["value"])}</dd></div>' for f in a['facts'])
def build():
 if not(M/'manifest.json').is_file():raise ValueError('Frozen model not imported')
 data={'schema':'slot-reader-1','variants':{}};atlas=[]
 for v in V:
  base=f'assets/{v}';a=json.loads((M/base/'model-info.json').read_text());c=a['config'];ac=a['assembly_contract'];b=a['bounds_m']
  assert a['variant']==v and len(a['parts'])==2+c['dividers'] and ac['engineering_validated'] is False
  for key in ['length','depth','divider_height','thickness','rail_height','clearance']:assert isinstance(c[key],(int,float)) and c[key]>0
  views={}
  captions={'beauty':f'两根纵轨与 {c["dividers"]} 块横隔板。开放底部，用于纸册直立陈列的数字概念；不是零碎收纳盒。','exploded':'横隔板竖直抽离的静态示意。这个画面本身不能证明连续装配轨迹、制造公差或稳定性。','joint':f'接点抬升静态示意：纵轨上开槽，横隔板下开槽；名义槽宽 {mm(ac["nominal_slot_width"])} mm。接点机位局部定位，不用于跨款尺寸比较。'}
  for w in W:
   filename='joint-exploded' if w=='joint' else w
   assert (M/base/f'{filename}.png').is_file();views[w]={'image':f'model/{base}/{filename}.png','alt':f'{names[v]} / {v.upper()} · '+{'beauty':'实际完整器物','exploded':'实际几何静态分解','joint':'实际槽口抬升静态近景'}[w]+' · CPU 渲染','caption':captions[w]}
  fs=[{'label':'构件','value':f'2 纵轨 + {c["dividers"]} 横隔板'},{'label':'名义板厚 / 槽宽','value':f'{mm(c["thickness"])} / {mm(ac["nominal_slot_width"])} mm'},{'label':'世界外包长 × 宽 × 高','value':' × '.join(f'{(x[1]-x[0])*1000:.2f}' for x in b)+' mm'},{'label':'名义总侧隙','value':mm(ac['nominal_total_lateral_clearance'])+' mm'}]
  item={'title':names[v]+' / '+v.upper(),'facts':fs,'views':views};data['variants'][v]=item
  atlas.append(f'''<details {'open' if v=='slot' else ''}><summary>{e(item['title'])} · 2 纵轨 / {c['dividers']} 横隔板</summary>{triptych(item,True)}<dl class="facts" data-static-facts="{v}">{facts(item)}</dl><p><a href="model/{base}/model.glb" download>GLB 模型</a> · <a href="model/{base}/model.blend" download>原生 BLEND</a> · <a href="model/{base}/model-info.json">原始配置与身份</a> · <a href="model/{base}/joint.png">完整接点原图</a></p></details>''')
 if D.exists():shutil.rmtree(D) # Generated projection only; immutable model-stage is retained.
 D.mkdir(parents=True,exist_ok=True)
 for f in M.rglob('*'):
  if f.is_file():o=D/'model'/f.relative_to(M);o.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,o)
 for f in ['app.js','reader-state.js','style.css']:shutil.copyfile(R/f,D/f)
 (D/'web-assets').mkdir(exist_ok=True);(D/'web-assets/reader-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 for directory in ['review','web-source']:
  for f in (R/directory).rglob('*'):
   if f.is_file() and '__pycache__'not in f.parts and f.suffix!='.pyc':o=D/directory/f.relative_to(R/directory);o.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,o)
 a=data['variants']['slot'];buttons=''.join(f'<button hidden type="button" data-variant="{v}" aria-pressed="false">{names[v]} / {v.upper()}</button>' for v in V)
 (D/'index.html').write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>栖格 · 装配读本 — 造物手记 010</title><meta name="description" content="用整体、分解与接点三联图，读懂参数化厚板插接关系及有限复用条件。"><link rel="stylesheet" href="style.css"><script defer src="reader-state.js"></script><script defer src="app.js"></script></head><body><a class="skip" href="#reader">跳到三联图</a><header><a href="../../index.html">造物手记 / CREATION NOTEBOOK</a><span>010 · 常规研究</span></header><main><section class="intro"><p class="eyebrow">SLOT / 栖格 · AN ASSEMBLY READER</p><h1>把一处连接，拆开来读。</h1><p>两根纵轨，一组横隔板。不是把物件藏进盒子，而是让纸册在桌面形成秩序。这里研究真实厚板的互补槽口，以及换一种比例后仍然成立的几何条件。</p></section><nav class="section-nav" aria-label="阅读章节"><a href="#reader">三联图</a><a href="#parts">连接逻辑</a><a href="#atlas">全部静态图版</a><a href="#limits">验证边界</a><a href="#reproduce">复现资料</a></nav><section class="reader" id="reader" data-reader aria-busy="false"><div class="reader-top"><h2 data-title>{e(a['title'])}</h2><div class="variants" role="group" aria-label="选择几何变体">{buttons}</div></div><p class="status" data-status role="status" aria-live="polite">当前静态图版：栖格 / SLOT。无脚本时请在下方展开其他几何。</p><button class="retry" data-retry hidden type="button">重新读取这一组</button>{triptych(a,False,True)}<dl class="facts" data-facts data-static-facts="slot">{facts(a)}</dl></section><noscript><p class="noscript">JavaScript 未运行。这里保留栖格图版；下方“全部静态图版”含三种几何、匹配参数与原始模型，不需要交互脚本。</p></noscript><section class="chapter" id="parts"><div class="chapter-head"><p class="eyebrow">CONNECTION / 先读关系，再读数字</p><h2>厚度、开口、相遇的位置。</h2><p>这些是模型的几何组织方式，不是已经通过实物试验的装配说明。</p></div><div class="steps"><article><span class="step-number">01</span><h3>先分清两类板</h3><p>纵轨沿长度方向延伸；横隔板跨过两根纵轨。底部开放，不存在一块封闭托盘底面。三种变体改变比例与隔板数量，而不只换色。</p></article><article><span class="step-number">02</span><h3>两个槽方向相反</h3><p>纵轨从顶部开槽，横隔板从底部开槽；它们在中部互补相遇。槽宽根据对穿板厚加名义间隙生成，而不是把两张实心板直接穿在一起。</p></article><article><span class="step-number">03</span><h3>间隙不是公差认证</h3><p>页面展示名义总侧隙，不能误读为单侧间隙或制造许可。倒角会改变局部边界，必须结合导出几何、接点近景和检查报告看实际结果。</p></article></div></section><section class="chapter atlas" id="atlas"><div class="chapter-head"><p class="eyebrow">STATIC ATLAS / 无脚本也完整</p><h2>三种几何，同一套连接语言。</h2><p>展开每组即可阅读实际图与对应数字。整体图固定摄影条件；接点图按局部位置取景。世界外包尺寸由原生模型世界坐标记录计算，不把纵轨间距误写为器物总宽。</p></div>{''.join(atlas)}</section><section class="chapter" id="limits"><div class="chapter-head"><p class="eyebrow">EVIDENCE / 结论的边界</p><h2>可复现的几何，不是可制造的承诺。</h2></div><div class="limits"><article><h3>本页确实做了什么</h3><p>实际模型的三联图、构件数、板厚与槽宽来自同一冻结资产。切换时三图全部解码后才替换图文，失败保留旧组；首次失败则明确没有已确认完整组。</p><p>静态分解图只解释构件关系。任何有限运动样本检查须按模型原报告的对象、方向、采样与局限理解，不推导任意装配次序。</p></article><article class="warning"><h3>仍不成立的保证</h3><p>没有验证实体材料、承载、抗倾覆、摩擦、胶接、加工公差或使用安全。基面需按每件实际最低点校正；仅写名义 z=0 不能证明倒角后的真实位置。实际校正量、上下界与中部间隙以最终元数据和检查报告为准。</p><p>CPU 图与代码测试不等于实时 GPU 闪烁测试。云浏览器 GL 禁用；真实 GPU 与 iPhone 尚未验收。</p></article></div></section><section class="chapter" id="reproduce"><div class="chapter-head"><p class="eyebrow">REPRODUCE / 把条件留下来</p><h2>作品之外，还有一份可追溯手记。</h2><p>原模型包保留在 model/，网页未重导出或压损模型。有限变体只证明这些样本能复现同一语言，不证明连续参数全集。</p></div><div class="resources"><a href="model/README.md">模型说明、复现条件与失败边界 ↗</a><a href="model/manifest.json">原模型文件身份清单 ↗</a><a href="review/model-parity.json">网页导入字节核验 ↗</a><a href="review/reference-notes.md">首版后的真实案例对标 ↗</a><a href="review/reflection.md">网页改进、验收与仍未验证 ↗</a><a href="web-assets/reader-data.json">本页图文数据契约 ↗</a></div></section></main><footer>造物手记 · Creation Notebook<p>把想象做成有形之物，把经验留下来。</p><p>010 / 网页与模型归档、总览集成、公开部署及实际访问分开记录；发布状态以总览为准。</p></footer></body></html>''')
 return data
if __name__=='__main__':build()
