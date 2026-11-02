#!/usr/bin/env python3
"""Compose the technical editorial page from frozen assets (or clearly marked draft inputs)."""
import sys,json,html,argparse,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from diagrams import make_all,profile,bend
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group();m.add_argument('--draft',action='store_true');m.add_argument('--candidate',action='store_true');a=p.parse_args()
infos={v:json.loads((R/'assets'/v/'model-info.json').read_text()) for v in ['folio','atlas','spire']}
if not a.draft:
 manifest=json.loads((R/'manifest.json').read_text())
 if not a.candidate and manifest.get('status')!='frozen-static-validated':raise SystemExit('Refusing final page until model package is frozen-static-validated')
 required=['recipe-source.zip','manifest.json','config.schema.json','README.html','view.html','viewer.js','viewer.css','design-case.html','source/generate.py']
 for v in infos:
  required += [f'assets/{v}/{n}' for n in ['model.blend','model.glb','model-info.json','validation.json','section-measurements.json','beauty.png','front.png','side.png','top.png','bend-detail.png','contact-detail.png']]
 missing=[x for x in required if not (R/x).is_file()]
 if missing:raise SystemExit('Refusing final compose; missing: '+', '.join(missing))
 for v,d in infos.items():
  report=json.loads((R/'assets'/v/'validation.json').read_text());assert report['passed'],v+' validation must pass'
  assert report['model_sha256']==hashlib.sha256((R/'assets'/v/'model.blend').read_bytes()).hexdigest(),v+' model/check identity mismatch'
  assert json.loads((R/'assets'/v/'section-measurements.json').read_text())['passed'],v+' section measurements must pass'
  assert d['config']==json.loads((R/'configs'/f'{v}.json').read_text()),'Config mismatch'
make_all(R);info=infos['folio'];c=info['config'];b=info['construction']['bends'];esc=lambda s:html.escape(str(s),quote=True)

def mm(x,n=2):return f'{x*1000:.{n}f}'
def size(v):
 d=infos[v]['dimensions_mm'];return ' × '.join(f'{d[k]:.1f}' for k in ['width','depth','height'])+' mm'
def link(path,label,attrs=''):
 return f'<a href="{esc(path)}" {attrs}>{label}</a>' if (R/path.split('#')[0]).exists() else f'<span>{label} · 待接入</span>'
def figure(path,alt,caption,cls=''):
 if (R/path).exists():return f'<figure class="{cls}"><a href="{path}"><img src="{path}" alt="{esc(alt)}" width="960" height="960" loading="lazy"></a><figcaption>{caption}</figcaption></figure>'
 return f'<div class="asset-await"><p>{caption}</p><small>真实图版尚未接入，本栏不是完成证明。</small></div>'

titles={'folio':('FOLIO','均衡','以中等宽度与阅读面倾角建立基准。'),'atlas':('ATLAS','低展','以低而宽的轮廓，把视觉重心放在横向。'),'spire':('SPIRE','高立','较高且较窄的轮廓，让阅读面更接近直立。')}
status='<div class="draft-notice" role="note"><strong>布局复评 / 非冻结稿</strong> 已接入真实草稿渲染和路径坐标；最终图、检查与下载尚未冻结。</div>' if a.draft else '<p class="release-line">原创模型研究 · 006 <span>名义参数 / 派生轮廓 / 离散检查分列</span></p>'
if a.candidate:status='<div class="draft-notice" role="note"><strong>完整候选 / 非冻结稿</strong> 三款真实资产已齐，正在做浏览器与身份复检；未冻结、未发布。</div>'
views=[]
for key,label,alt,cap in [('beauty','整体视角','FOLIO 均衡变体：一件连续金属外观厚壳，前缘抬起、阅读面回折到后足。','整体 / 固定正交产品机位。图中材质为视觉代理，不代表金属制造测试。'),('bend-detail','顶弯细节','FOLIO 顶部B3弯折局部，展示连续表面与边缘。','B3顶弯 / 实际模型近景；不能凭高光推导厚度处处相等。'),('contact-detail','接地细节','FOLIO 前托面与前缘折弯近景，展示接地平段和连续厚壳。','前托面 / 实际模型近景；接地几何不等于载荷稳定性已验证。')]:
 path=f'assets/folio/{key}.png'
 if (R/path).exists():views.append({'id':key,'label':label,'src':path,'alt':alt,'caption':cap})
hero=views[0];viewjson=json.dumps(views,ensure_ascii=False).replace('</','<\\/')
buttons=''.join(f'<button type="button" data-view="{q["id"]}" aria-pressed="{str(i==0).lower()}">{q["label"]}</button>' for i,q in enumerate(views))
legend='<div class="diagram-legend"><span><i class="key-center"></i>生成中心线</span><span><i class="key-shell"></i>法向偏移边界</span><span><i class="key-label"></i>折弯位置标注</span></div>'
bendrows=''.join(f'<li><span class="bend-code">B{q["corner"]}</span><div><strong>{["落下，接住。","抬起，形成阅读面。","回折，形成后撑。","展开，落到桌面。"][i]}</strong><p>{["前缘转向前托平段。","前托平段转向倾斜阅读面。","阅读面越过顶弯转向后撑。","后撑与末端平段连续相接。"][i]}</p></div><span class="turn-value">{q["turn_deg"]:+.0f}°</span></li>' for i,q in enumerate(b))
meshcheck='检查文件待冻结' if a.draft else f'1 个连通闭壳 · {info["triangles"]:,} 三角形'
measurement='<p>厚度是配置输入，内外半径为解析派生。当前这一栏不把法向配对值写成任意网格点的最短厚度。</p>'
reportpath=R/'assets/folio/validation.json'
if reportpath.exists():
 rep=json.loads(reportpath.read_text())
 # Any richer diagnostic must be wired explicitly after its actual field contract is read.
 measurement=f'<p>离散网格报告：{rep["mesh_objects"]} 个网格对象；顶点与受约束配方比对、拓扑、局部绕序和非相邻相交候选检查{("通过" if rep["passed"] else "未通过")}。<strong>不等于制造级全域厚度证明。</strong></p>'
measurefile=R/'assets/folio/section-measurements.json'
if measurefile.exists() and not a.draft:
 sec=json.loads(measurefile.read_text());vr=sec['matched_vertex_thickness_mm'];mr=sec['longitudinal_edge_midpoint_thickness_mm']
 measurement += f'<dl class="sample-values"><div><dt>配对顶点 / {sec["matched_vertex_pair_count"]} 对</dt><dd>{vr[0]:.6f}–{vr[1]:.6f} <small>mm</small></dd></div><div><dt>纵向边中点 / {sec["longitudinal_edge_midpoint_pair_count"]} 对</dt><dd>{mr[0]:.6f}–{mr[1]:.6f} <small>mm</small></dd></div></dl><p>以上为有限样本的配对距离范围，非任意位置的全域最短厚度。圆弧相邻站点不超过 {sec["bend_arc_chord_max_angle_deg"]}°；弦中点厚度会有细微差异。</p><p><a href="assets/folio/section-measurements.json">查看站点与边中点测量 ↗</a></p>'
family=[]
for i,(v,d) in enumerate(infos.items()):
 name,sub,description=titles[v];cfg=d['config'];family.append(f'''<article id="variant-{v}" class="variant-row"><div class="variant-name"><span class="variant-order">0{i+1}</span><h3>{name}<small>{sub}</small></h3><p>{description}</p></div><figure class="variant-profile">{profile(d,True,v+'-family')}<figcaption>YZ中心截面 · 与另两件同一比例尺</figcaption></figure><div class="variant-spec"><p class="data-kind">名义输入</p><dl><div><dt>阅读面倾角</dt><dd>{cfg['display_angle']:g}°</dd></div><div><dt>厚度 t</dt><dd>{mm(cfg['thickness'])} mm</dd></div><div><dt>中心弯半径 R</dt><dd>{mm(cfg['bend_radius'])} mm</dd></div></dl><p class="data-kind measured">离散包围盒 / 宽 × 深 × 高</p><p class="dimension">{size(v)}</p><div class="row-links">{link(f'assets/{v}/beauty.png','真实渲染 ↗')}{link(f'assets/{v}/model.glb',name+' GLB ↓','download') if not a.draft else '<span>下载待冻结</span>'}{link(f'assets/{v}/model.blend',name+' Blender ↓','download') if not a.draft else ''}</div></div></article>''')
archive=[]
for path,label,desc in [('recipe-source.zip','完整复现源包','模型、配置、生成脚本和检查记录'),('manifest.json','模型清单','版本与文件身份'),('config.schema.json','输入边界','合法字段、范围与关联约束'),('README.html','复现说明','环境与实际执行命令'),('view.html','独立 3D 观察','Three.js；不支持WebGL时保留真图'),('design-case.html','本页设计评审','原站参考、前后修订与浏览器范围')]:
 exists=(R/path).exists();tag=link(path,f'<strong>{label}</strong><span>{desc}</span><b aria-hidden="true">↗</b>') if not a.draft or path=='design-case.html' else f'<span class="pending-download"><strong>{label}</strong><span>{desc} · 待冻结</span></span>';archive.append('<li>'+tag+'</li>')
configrows=''.join(f'<tr><th scope="row">{key}</th>'+''.join(f'<td>{d["config"][key]:g}</td>' for d in infos.values())+'</tr>' for key in ['width','height','display_angle','rear_angle','tray_depth','foot_depth','lip_height','bend_radius','thickness'])
htmlout=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="FOLIO折页：从真实弯折路径到连续厚壳，三种几何变体的制作图解与可核查源档案。"><title>FOLIO 折页 — 制作图解 006</title><link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head><body>
<a class="skip" href="#main">跳至正文</a><header class="mast"><a class="wordmark" href="../../index.html">造物手记<span>FORM STUDIES</span></a><p class="edition">006 <span>/ 制作图解</span></p><a href="#archive" class="text-link">档案索引 ↗</a></header><nav class="chapter-nav" aria-label="本页章节"><a href="#path"><span>01</span> 弯折路径</a><a href="#thickness"><span>02</span> 连续厚度</a><a href="#family"><span>03</span> 几何变体</a><a href="#archive"><span>04</span> 源与记录</a></nav>
<main id="main">{status}<section class="opening" aria-labelledby="title"><div class="opening-text"><p class="eyebrow">CONTINUOUS SURFACE / 006</p><h1 id="title">FOLIO<span>折页</span></h1><p class="standfirst">一条路径，<br>四次转向。</p><p class="intro">将前缘、托面、阅读面与后撑，做成一件连续的厚壳。不是把薄片拼在一起，而是让厚度跟着路径走。</p><dl class="opening-facts"><div><dt>对象</dt><dd>阅读 / 陈列支架</dd></div><div><dt>研究</dt><dd>曲率 · 折角 · 连续厚壳</dd></div><div><dt>边界</dt><dd>原创几何研究，非生产定案</dd></div></dl><a class="read-next" href="#path">沿路径阅读 <span>↓</span></a></div><figure class="hero-figure"><div class="hero-stage"><span class="plate-id">A / FOLIO · 整体</span><img id="hero-image" src="{hero['src']}" alt="{hero['alt']}" width="960" height="960" fetchpriority="high"><p id="image-unavailable" class="image-unavailable" hidden>当前图版未能加载。路径图、参数与其余图版仍可阅读。</p></div><div class="image-controls" hidden aria-label="FOLIO图版切换">{buttons}</div><figcaption><span id="hero-caption">{hero['caption']}</span><a id="hero-original" href="{hero['src']}">原图 ↗</a></figcaption><p id="image-status" role="status" aria-live="polite" class="image-status"></p><button type="button" id="image-retry" class="retry-button" hidden>重试图版</button><noscript><p class="nojs-note">未启用脚本：整体图、全部图解与下载仍可阅读；局部图在下方章节。</p></noscript></figure></section>
<section id="path" class="chapter path-chapter"><div class="section-heading"><p class="section-no">01 / PATH</p><h2>先读一条线。</h2><p>这不是手绘近似轮廓。每个点来自生成模型的真实YZ中心线采样；四个B标号对应四处弯段。</p></div><div class="plate-layout"><figure class="diagram-figure"><div class="diagram-surface"><span class="plate-id">B / 侧向路径</span>{profile(info,False,'main-profile')}</div>{legend}<figcaption><span>中心截面离散法向偏移轮廓；展示mm，源文件为m。</span>{link('assets/diagrams/diagram-evidence.json','坐标来源 ↗')}</figcaption></figure><aside class="reading-key"><h3>从前端走向后端</h3><ol class="bend-list">{bendrows}</ol><p class="angle-note">角度是沿路径前进时的<strong>有向转角</strong>，不是夹角，也不是钣金折弯机设定。</p></aside></div></section>
<section id="thickness" class="chapter thickness-chapter"><div class="section-heading"><p class="section-no">02 / SECTION</p><h2>转弯，仍是一件厚壳。</h2><p>先定义中心线，再沿局部法向向两侧偏移。名义厚度和网格验证是不同层次，不能互相替代。</p></div><div class="thickness-grid"><figure class="bend-figure"><div class="bend-surface">{bend(info)}</div><figcaption>图版C / 仅放大B3弯段。尺寸来自配置与解析半径，不是实物测量。</figcaption></figure><div class="thickness-copy"><p class="data-kind">名义输入 / CONFIG</p><dl class="large-values"><div><dt>法向厚度 t</dt><dd>{mm(c['thickness'])}<small>mm</small></dd></div><div><dt>中心半径 R</dt><dd>{mm(c['bend_radius'])}<small>mm</small></dd></div></dl><p class="data-kind derived">解析派生 / R ± t/2</p><dl class="derived-values"><div><dt>内半径</dt><dd>{b[2]['inside_radius_mm']:.2f} mm</dd></div><div><dt>外半径</dt><dd>{b[2]['outside_radius_mm']:.2f} mm</dd></div></dl><p class="thickness-boundary">圆弧以离散弦连接。法向配对定义不证明多边形上任意两点的最短厚度处处相等。</p></div></div><div class="evidence-strip"><div><p class="data-kind measured">离散网格检查 / MESH</p><h3>{meshcheck}</h3>{measurement}<div class="inline-links">{link('assets/folio/validation.json','FOLIO 检查报告 ↗')}{link('assets/folio/model-info.json','模型数据 ↗')}</div></div>{figure('assets/folio/bend-detail.png','FOLIO B3顶弯真实局部渲染','真实局部渲染 / 用于观察高光与轮廓，不替代数值检查。','detail-figure')}</div><div class="engineering-boundary"><strong>这里没有证明什么</strong><p>没有做板金展开、回弹、加工公差、材料强度、承载、防倾覆或人体工学验证。表面看起来像金属，不意味着已经确定合金或制造工艺。</p></div></section>
<section id="family" class="chapter family-chapter"><div class="section-heading"><p class="section-no">03 / VARIATIONS</p><h2>同一方法，<br>三种姿态。</h2><p>以下侧向轮廓使用同一比例尺，不按各自外接框放大。侧图不显示X向宽度；宽度见数值与真实渲染。</p></div><div class="family-list">{''.join(family)}</div><p class="comparison-note">倾角由输入控制；宽、深、高是生成网格的离散包围盒，并不等于全部名义尺寸。尤其顶部圆弧会使实测高度低于路径控制高度。</p><details class="config-details"><summary>查看完整三预设输入 <span>原始单位：长度m / 角度°</span></summary><div class="config-table-wrap"><table><caption>精确配置；不把合法输入范围当成全参数域已经验证</caption><thead><tr><th scope="col">参数</th><th scope="col">FOLIO</th><th scope="col">ATLAS</th><th scope="col">SPIRE</th></tr></thead><tbody>{configrows}</tbody></table></div><div class="inline-links">{''.join(link(f'configs/{v}.json',v.upper()+'配置 ↓','download') for v in infos)}</div></details></section>
<section class="contact-chapter chapter" aria-labelledby="contact-title"><div class="section-heading"><p class="section-no">DETAIL / CONTACT</p><h2 id="contact-title">接地，是几何问题；<br>稳定，是另一件事。</h2><p>前托平段和后足属于同一连续壳体。这里看真实接点，保留几何接地与受力验证之间的边界。</p></div><div class="contact-layout">{figure('assets/folio/contact-detail.png','FOLIO前托面与上翻前缘的连续弯折，底部平段与地面接近','图版D / 实际模型接地局部。地面属于摄影场景，不含在GLB中。','contact-figure')}<div><p class="data-kind">来源分开，结论清楚。</p><h3>模型 / 摄影场景 / 图解</h3><p>模型文件只包含原创厚壳。地面、灯光和摄影机属于独立场景。蓝色图解来自同一份模型数据，但不是渲染图，也不是实物试验。</p><ul class="plain-list"><li>形态：真实CPU渲染与三种几何。</li><li>构造：中心线、法向偏移和实际网格。</li><li>端部：{info["construction"].get("terminal_plan_corner_radius_mm",0):g} mm仅为平面轮廓圆角；端盖厚度边仍是硬边，不称全方向倒圆。</li><li>边界：无WebGL时也能读取，不假称实时通过。</li></ul></div></div></section>
<section id="archive" class="chapter archive-chapter"><div class="section-heading"><p class="section-no">04 / ARCHIVE</p><h2>回到可核查的文件。</h2><p>从网页到参数，再到模型。下载名称、单位与版本保持对应；实时观察不是阅读本页的前置条件。</p></div><ul class="archive-list">{''.join(archive)}</ul><div class="archive-meta"><p>参数配方 {esc(info['recipe_version'])} · Blender {esc(info['blender_version'])} · {esc(info['studio']['renderer'])}</p><p>本页不含外部原图，不依赖远程字体、CDN或分析脚本。</p></div></section></main><footer><a href="../../index.html">← 返回造物手记</a><p>006 · FOLIO 折页 <span>原创形态研究 / 制作图解 {'布局复评' if a.draft else '完整候选' if a.candidate else 'v2'}</span></p><a href="#main">回到开头 ↑</a></footer><script id="image-data" type="application/json">{viewjson}</script></body></html>'''
(R/'index.html').write_text(htmlout)
print('Composed', 'DRAFT' if a.draft else 'COMPLETE CANDIDATE / NOT FROZEN' if a.candidate else 'final-asset page')
