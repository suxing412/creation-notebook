"""Build a portable, dependency-free gallery from manifest.json and public study notes."""
from pathlib import Path
import json,html,re,os
ROOT=Path(__file__).resolve().parent; D=(ROOT/'dist') if (ROOT/'dist').is_dir() else ((ROOT.parent/'dist') if (ROOT.parent/'dist').is_dir() else ROOT.parents[1]/'docs'); esc=html.escape
manifest=json.loads((ROOT/'manifest.json').read_text())
items=[x for x in manifest['studies'] if x.get('status','published') not in ('draft','in-progress')]
regular=[x for x in items if x.get('kind','regular')=='regular']
fusion=[x for x in items if x.get('kind')=='fusion']

def inline(s):
 s=esc(s)
 s=re.sub(r'\[([^\]]+)\]\((https://[^ )]+|[^ :)]*\.(?:md|png|json|py))\)',lambda m:'<a href="'+m[2].replace('.md','.html')+'">'+m[1]+'</a>' if not m[2].startswith('https://') else '<a href="'+m[2]+'" rel="noopener">'+m[1]+'</a>',s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
 return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)

def md(s):
 lines=[]; code=False; table=False
 for line in s.splitlines():
  if not code and line.startswith('|'):
   if not table: lines.append('<table>'); table=True
   cells=[x.strip() for x in line.strip().strip('|').split('|')]
   if all(re.fullmatch(r':?-+:?',x) for x in cells): continue
   lines.append('<tr>'+''.join('<td>'+inline(x)+'</td>' for x in cells)+'</tr>');continue
  if table:lines.append('</table>');table=False
  if line.startswith("```"):
   lines.append("</code></pre>" if code else "<pre><code>"); code=not code; continue
  if code: lines.append(esc(line)); continue
  if not line.strip():continue
  match=re.match(r'^(#{1,4}) (.+)',line)
  if match:lines.append(f'<h{len(match[1])}>{inline(match[2])}</h{len(match[1])}>')
  elif line.startswith('- '):lines.append('<p class="bullet">'+inline(line[2:])+'</p>')
  else:lines.append('<p>'+inline(line)+'</p>')
 if table:lines.append('</table>')
 return '\n'.join(lines)

def shell(title,body,base='./'):
 return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f2eee5"><meta name="description" content="伊苏里亚的三维造物练习：原创 Blender 模型、Three.js 观察原型与诚实的制作复盘。"><title>{esc(title)} · 伊苏里亚造物手记</title><link rel="stylesheet" href="{base}gallery.css"></head><body><a class="skip" href="#main">跳至内容</a><header class="mast"><a class="wordmark" href="{base}"><span class="seal">伊</span> 伊苏里亚 <small>造物手记</small></a><nav aria-label="主导航"><a href="{base}#works">作品</a><a href="{base}#fusions">融合</a><a href="{base}#recipes">配方</a><a href="{base}#research">研究</a></nav></header>{body}<footer><span>ISURIYA / FORM STUDIES</span><p>记录真实完成的作品，也记录尚未解决的问题。<br>Blender 建模 · Three.js 展示 · 持续修订</p><a href="{base}">返回作品集 ↑</a></footer></body></html>'''

cards=[]
for pos,x in enumerate(regular):
 kind=x.get('kind','regular'); badge='常规双轨' if kind=='regular' else '三维网页融合'
 metrics=f"<dl><div><dt>{x.get('triangleLabel','三角面')}</dt><dd>{x['triangles']:,}</dd></div><div><dt>源构件</dt><dd>{x['components']}</dd></div><div><dt>模型版本</dt><dd>{x['version']}</dd></div></dl>" if kind=='regular' else '<p class="fusion-pair">关联练习：'+esc(' / '.join(x.get('pairedStudyIds',[])))+'</p>'
 links=f'<a href="{x.get("modelView",x["path"])}">3D 作品 ↗</a><a href="{x.get("webPrototype",x["path"])}">网页作品 ↗</a><a href="{x.get("modelReflection",x["path"]+"study-notes.html")}">建模复盘 →</a><a href="{x.get("designCase",x["path"]+"design-case.html")}">网页评审 →</a>' if kind=='regular' else f'<a href="{x["path"]}">进入融合网页 ↗</a><a href="{x.get("designCase",x["path"]+"design-case.html")}">设计与复盘 →</a>'
 cards.append(f'''<article class="study" data-kind="{kind}"><a class="plate {x['theme']}" href="{x['path']}"><img src="{x['image']}" alt="{esc(x['alt'])}" loading="{'eager' if pos==0 else 'lazy'}" width="1440" height="1080"><span class="plate-label">STUDY {x['id']} / ORIGINAL RENDER</span><span class="open">进入作品 ↗</span></a><div class="study-copy"><div class="kicker"><span class="kind-badge">{badge}</span> {x['id']} — {x['category']}</div><h3><a href="{x['path']}">{x['name']} <em>{x['english']}</em></a></h3><p class="description">{x['description']}</p>{metrics}<p class="qa"><span>模型已改</span>{x['qa']}</p><p class="pending"><span>仍待改进</span>{x['pending']}</p><div class="web-track"><b>{esc(x.get('webStatus','网页评审待补充'))}</b><p>{esc(x.get('webBrief',''))}</p></div><div class="card-links">{links}</div><p class="route-note">{esc(x.get('routeNote','3D 作品定位到观察区；网页作品打开同一实现的完整页面，不冒充两份独立页面。'))}</p></div></article>''')
fusion_html='<section id="fusions" class="fusion-section"><div class="section-heading"><h2>三维网页融合 <em>Space as navigation</em></h2><span>每两轮之后 · 单独评审</span></div>'
for x in fusion:
 scene_link=f'<a href="{x["scene"]}" download>原始三维场景 ↓</a>' if x.get("scene") else ''
 fusion_html+=f'''<article class="fusion-feature"><a class="fusion-image" href="{x['path']}"><img src="{x['image']}" alt="{esc(x['alt'])}" loading="lazy" width="1440" height="960"></a><div class="fusion-copy"><p class="kicker">{x['id']} / FUSION · 配对 {' / '.join(x['pairedStudyIds'])}</p><h3>{x['name']} <em>{x['english']}</em></h3><p>{x['description']}</p><p class="proof-note"><b>局部已验</b> {x['qa']}</p><p class="proof-note"><b>仍待验证</b> {x['pending']}</p><div class="card-links"><a href="{x['path']}">进入空间网页 ↗</a><a href="{x['designCase']}">设计与修订 →</a><a href="{x['qaReport']}">验收记录 →</a><a href="{x['source']}" download>源文件 ↓</a>{scene_link}</div></div></article>'''
fusion_html+='</section>'
recipe_html='<section id="recipes" class="recipe-section"><div class="section-heading"><h2>可复用方法 <em>Make a family, not a copy</em></h2><span>RECIPE / 不计作新练习轮</span></div>'
for x in manifest.get('recipes',[]):
 recipe_html+=f'''<article class="recipe-feature"><div><p class="eyebrow">DERIVED FROM STUDY 002 / VERSION 1</p><h3>{x['name']}</h3><p>同一生成器，三组确实不同的几何参数。保存构造约束、摄影棚、参数契约和检验结果，让下一次变体有可追溯的起点。</p><p class="proof-note">固定 Blender 4.3.2；非法输入拒绝生成；baseline 重复生成 GLB 字节一致。三组预设通过的证据<strong>不等于整个连续参数域安全</strong>。</p><div class="card-links"><a href="{x['path']}">比较三个变体 ↗</a><a href="{x['method']}">复现条件与方法 →</a><a href="{x['reflection']}">修订与反思 →</a><a href="{x['source']}" download>下载源码配方 ↓</a></div></div><a href="{x['path']}" class="recipe-image"><img src="{x['image']}" alt="陶瓷翼 baseline、broad、swept 三组实际几何的多视图对照图版" loading="lazy" width="1800" height="1200"></a></article>'''
recipe_html+='</section>'
research_html='<section id="research" class="research-section"><p class="eyebrow">RESEARCH / DATED, NOT TIMELESS</p><h2>新技术先观察，<br>有效果再采用。</h2>'
for x in manifest.get('research',[]):
 research_html+=f'''<div class="research-entry"><time>{x['date']}</time><h3><a href="{x['path']}">{x['title']} ↗</a></h3><p>Blender、Three.js / WebGPU、glTF 与网页可用性。区分原站正文、搜索索引和工程推论；无法核实的最新版本、未运行的能力都保留边界。不等于升级生产线，也不是全球最佳排名。</p><a href="{x['source']}" download>下载原始研究笔记 ↓</a></div>'''
research_html+='</section>'
body='''<main id="main"><section class="intro"><p class="eyebrow">THE FORM NOTEBOOK / 2026</p><div class="intro-grid"><h1>把想象，<br>做成有形之物<span>。</span></h1><div class="intro-note"><span class="hand">把想象做成有形之物，把经验留下来。</span><p>这是伊苏里亚的造物与网页双轨练习集。<br>每轮建模，也设计承载它的网页；<br>把作品、检查和不足放在同一张桌上。</p><a class="text-link" href="#works">翻开作品手记 <span>↓</span></a></div></div><div class="inventory"><span>已收录 <b>02</b> 轮常规双轨</span><span>建模 + 网页 / 融合 / 复用方法</span><span>最近整理 · 2026.11.01</span></div></section><section id="works" class="works"><div class="section-heading"><h2>常规双轨 <em>Form & web studies</em></h2><span>01 — 02</span></div>'''+''.join(cards)+'''</section>'''+fusion_html+recipe_html+research_html+'''<section id="quality-workflow" class="fusion-note"><p class="eyebrow">METHOD ASSET / QUALITY WORKFLOW V2</p><h2>把一次修好，变成下次可复现。</h2><p>从真实修复里整理 16 条条件化准则，链接 30 项公开证据。把参数、几何、文件身份、浏览器状态、相机投影与发布体积的适用边界写清；不是通用检查器，也不新增作品轮次或几何配方。</p><a href="./methods/quality-workflow-v2/">阅读工作法 v2 →</a> · <a href="./methods/quality-workflow-v2/checklist.md">执行清单 →</a> · <a href="./methods/quality-workflow-v2/contract-template.json" download>待填写契约模板 ↓</a> · <a href="./methods/quality-workflow-v2-integration-qa.json">接入验收范围 →</a></section><section class="method" id="method"><div><p class="eyebrow">A PRACTICE, NOT A PROMISE</p><h2>让下一件，<br>解决上一件的问题。</h2><p>模型与网页各自联网对标、修订和复盘。不把装饰数量当成质量，不把静态渲染当成实时验收。每件练习保留已修正的问题，以及下一次值得继续追问的地方。</p></div><ol><li><b>01</b><div><h3>先建立轮廓</h3><p>先检查体块、比例与负空间，再增加有理由存在的细节。</p></div></li><li><b>02</b><div><h3>分开验证几何与画面</h3><p>重复面、退化面、共面重叠、意外穿插分别检查；有意的装配接触单独记录。</p></div></li><li><b>03</b><div><h3>参考、修订、留下证据</h3><p>与方向相近的专业作品比较，说明实际看到了什么，不把参考包装成排名。</p><a href="./benchmark.html">建模对标 ↗</a> · <a href="./web-design-review.html">网页评审 ↗</a></div></li></ol></section><aside class="verification"><span class="status">验收边界</span><p>收录作品已生成真实 Blender 模型与离线渲染，并完成所述网格检查。静态降级页面已检查；当前测试环境未能启用 WebGL，<strong>实时交互、转动时的深度闪烁、真实手机性能仍待验证</strong>。不同作品的面数不是同一模型的优化对照。</p></aside></main>'''
body=body.replace('已收录 <b>02</b>',f'已收录 <b>{len(regular):02}</b>').replace('01 — 02',f"{regular[0]['id']} — {regular[-1]['id']}").replace('2026.11.01',manifest['updated'].replace('-','.')).replace('建模 + 网页 / 融合 / 复用方法',f"{len(fusion):02} 轮融合 / {len(manifest.get('recipes',[])):02} 套配方")
(D/'index.html').write_text(shell('作品集',body).replace('伊苏里亚造物手记','造物手记 · Creation Notebook').replace('伊苏里亚 <small>造物手记</small>','造物手记 <small>Creation Notebook</small>'))
for f in D.rglob('*.md'):
 if f.name.startswith('overview-'):continue
 if f.is_relative_to(D/'studies'/'009') or f.is_relative_to(D/'studies'/'008') or f.is_relative_to(D/'studies'/'007') or 'methods' in f.relative_to(D).parts or 'fusions' in f.relative_to(D).parts or f.is_relative_to(D/'studies'/'005') or (f.is_relative_to(D/'studies'/'006') and f!=D/'studies'/'006'/'review'/'reflection.md'): continue  # Preserve the frozen fusion report implementation.
 base=os.path.relpath(D,f.parent).replace(os.sep,'/')+'/'
 (f.with_suffix('.html')).write_text(shell(f.stem,'<main id="main" class="report"><a class="back" href="'+base+'">← 作品集</a>'+md(f.read_text())+'<p class="report-download"><a href="'+f.name+'" download>下载 Markdown 原文 ↓</a></p></main>',base))
(D/'manifest.json').write_text((ROOT/'manifest.json').read_text())
(D/'.nojekyll').touch()
print('Built',len(items),'studies')

from archive_delivery import apply_projection
apply_projection(D)
