"""Compose static exhibit HTML from actual model/projection data. No build-time network.
--draft permits candidate-only preview and marks it prominently. Final requires frozen manifest.
"""
from pathlib import Path
import argparse,json,html,shutil
ROOT=Path(__file__).resolve().parents[1]
E=html.escape
NAMES={'orison':('Orison','回环','一个偏心的直立开口。内缘向下收拢，外缘却并不跟着等距收拢。'),'latitude':('Latitude','横境','横向展开的空处。更宽、更低的路径与扁厚截面，让观看的重心向两侧延伸。'),'ascend':('Ascend','上行','向上拉长的空处。窄高路径、较厚截面与更明显的纵深起伏改变同一圈的视觉重心。')}
def compose(dest,draft):
 infos={k:json.loads((dest/'assets'/k/'model-info.json').read_text()) for k in NAMES}
 projection=json.loads((dest/'web-assets'/'projection-data.json').read_text());records={(r['file'].split('-')[0],r['view']):r for r in projection['records']}
 if not draft:
  assert (dest/'manifest.json').exists() and (dest/'viewer'/'index.html').exists(), 'Final requires original model manifest and viewer'
  assert not any(v.get('phase')=='draft' for v in infos.values())
 def image(src,alt,**kw):
  return f'<img src="{E(src)}" alt="{E(alt)}" width="1000" height="1000"'+(' loading="lazy"' if kw.get('lazy',True) else '')+'>'
 def projection_img(key,view):
  label='正面' if view=='front' else '侧面';return image(f'web-assets/{key}-{view}-projection.png',f'{NAMES[key][1]}{label}的真实GLB投影：深色为实体覆盖，浅绿色为被围住且未被遮挡的二维空白；固定500毫米画幅')
 dims=infos['orison']['dimensions_mm']; diag=infos['orison']['construction']['diagnostics']; con=infos['orison']['construction']
 front=records['orison','front'];side=records['orison','side']; area=lambda x:f'{x["interior_blank_area_cm2"]:.0f}'
 views=[('beauty','整体斜视','Orison 回环的整体斜视CPU渲染，暖白闭合扫掠形体围出偏心开口','01 / 整体斜视 · Cycles CPU'),('front','正面图版','Orison 回环的正面正交CPU渲染，显示向下收拢的内部开口','02 / 正面正交 · 500 mm 画幅'),('side','侧面图版','Orison 回环的侧面正交CPU渲染，前后实体表面重叠遮住内部开口','03 / 侧面正交 · 500 mm 画幅')]
 buttons=''.join(f'<button type="button" data-view="{key}" data-src="assets/orison/{key}.png" data-alt="{E(alt)}" data-caption="{E(cap)}" aria-pressed="false">{label}</button>' for key,label,alt,cap in views)
 static=''.join(f'<figure><div class="plate">{image(f"assets/orison/{key}.png",alt)}</div><figcaption>{cap}</figcaption></figure>' for key,label,alt,cap in views)
 family=''
 for k,(en,cn,description) in NAMES.items():
  i=infos[k];d=i['dimensions_mm'];cfg=i['config'];r=records[k,'front']
  family+=f'''<article class="variant"><p class="number">{en.upper()} / {len(family) and ('02' if k=='latitude' else '03') or '01'}</p><h3>{cn} <span class="latin">{en}</span></h3><div class="plate">{projection_img(k,'front')}</div><p>{description}</p><dl class="variant-data"><div><dt>宽 × 高</dt><dd>{d['width']:.1f} × {d['height']:.1f} mm</dd></div><div><dt>正面内空投影</dt><dd>约 {area(r)} cm²</dd></div><div><dt>截面名义宽 × 深</dt><dd>{cfg['section_width']*1000:.0f} × {cfg['section_depth']*1000:.0f} mm</dd></div></dl><p class="variant-link">{('<a href="viewer/index.html?variant='+k+'">单独观察 '+cn+' ↗</a>') if not draft else '候选形体 · 未冻结'}</p></article>'''
 download=''
 for k,(en,cn,_) in NAMES.items():
  download+=f'<li><span>{cn} / {en}</span><span><a download href="assets/{k}/model.glb">GLB</a> · <a download href="assets/{k}/model.blend">Blender</a> · <a download href="assets/{k}/config.json">参数</a></span></li>'
 actions='<a class="action" href="#looking">比较正面与侧面 <span aria-hidden="true">↓</span></a>'
 actions+= '<span class="pending">真实候选 · 未冻结，不可交付</span>' if draft else '<a class="action ghost" href="viewer/index.html">独立三维观察 <span aria-hidden="true">↗</span></a>'
 boundary='三组模型与最终文件身份请见模型原始检查；下述图像读数是二维投影分析，不替代几何门禁。'
 if draft:boundary='当前使用真实候选文件开发网页，几何仍可能修改。投影读数尚非最终结果，不可用于交付。'
 s=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="ORISON 回环：从正面与侧面的实际几何投影，观察闭合扫掠雕塑围住的空处。"><title>空处也是形体 · ORISON 007</title><link rel="stylesheet" href="style.css"><script src="gallery-state.js" defer></script><script src="app.js" defer></script></head>
<body><a class="skip" href="#main">跳至正文</a><div class="shell"><header class="mast"><strong>{'造物手记 / FIELD NOTES' if draft else '<a href="../../index.html">造物手记 / FIELD NOTES</a>'}</strong><span class="edition">007 — ORISON 回环 / 观察笔记{' · 候选' if draft else ''}</span></header></div><main id="main"><div class="shell">
<section class="hero"><div class="hero-text"><p class="eyebrow">A study of form & absence</p><h1>空处<br><em>也是形体。</em></h1><p class="lede">一条闭合的曲线，围出一个开口。先看见它留下的空处，再转到侧面：有些空白，并不会一直留在视野里。</p><div class="actions">{actions}</div><p class="hero-note">常规 007 / 第四周期第一件<br>原创数字雕塑 · 暖白陶瓷外观研究，非实物烧制</p></div>
<figure class="hero-figure" data-gallery data-initial="beauty"><div class="plate"><span class="plate-label">ORISON / PLATE STUDY</span><img data-current-image src="assets/orison/beauty.png" alt="{E(views[0][2])}" width="960" height="960" fetchpriority="high"><p class="image-fallback" data-fallback hidden>主图暂不可用，正文与轮廓比较仍可阅读。</p></div><figcaption class="figline"><span data-caption>{views[0][3]}</span><a data-original href="assets/orison/beauty.png">原图 ↗</a></figcaption><div class="view-controls" data-controls hidden aria-label="选择回环图版">{buttons}<button type="button" data-retry hidden>重试失败图版</button></div><p class="status" data-status aria-live="polite" aria-atomic="true"></p></figure></section>
<nav class="subnav" aria-label="观察章节"><a href="#looking">01 / 看见空处</a><a href="#continuous">02 / 没有端点</a><a href="#family">03 / 三种开口</a><a href="#record">04 / 制作档案</a></nav>
<section class="section" id="looking"><div class="section-top"><span class="section-number">01 — OBSERVATION</span><div><h2>同一件物体，两种空处的读法。</h2><p class="section-intro">左图沿正面看，开口被完整围住；右图转过 90°，前后表面相互遮挡，投影中已没有封闭的内空。消失的是视线里的空白，不是三维模型的孔洞。</p></div></div>
<div class="pair"><figure><div class="plate projection">{projection_img('orison','front')}</div><figcaption><strong>正面 / 空处显形</strong>沿 Blender +Y 方向看向模型。浅绿色区域是这一视角中可见的内部空白，栅格估算约 <b>{area(front)} cm²</b>。</figcaption></figure><figure><div class="plate projection">{projection_img('orison','side')}</div><figcaption><strong>侧面 / 空处被遮住</strong>沿 Blender −X 方向看向模型。实体轮廓重叠，当前栅格投影没有封闭内空；不能据此说实体已填满孔洞。</figcaption></figure></div>
<div class="projection-legend"><span><i class="swatch solid" aria-hidden="true"></i>实体覆盖</span><span><i class="swatch blank" aria-hidden="true"></i>投影内部空白</span><span class="scale">同一 500 × 500 mm 画幅</span></div>
<div class="note-grid"><div class="note"><h3>① 先读内缘</h3><p>开口下部收窄，与较开阔的上部构成方向感。这里的轮廓不是另画的概念草图。</p></div><div class="note"><h3>② 再读外缘</h3><p>两图均由同一GLB的全部真实三角面投影并集得到，前后表面都参与遮挡。</p></div><div class="note"><h3>③ 别把投影当通道</h3><p>约数来自 2048² 像素的二维连通空白；它不是三维体积、最小开口或可穿过物体的尺寸。</p></div></div>
<details class="method-detail"><summary>这两张轮廓怎样得来？</summary><p>读取GLB节点的实际世界变换，将Y-up坐标转回Blender Z-up，并核对模型包围边界。正、侧两图固定500 mm画幅与205 mm垂直中心；不对每个对象单独放大。三角面覆盖像素后，从图框外部填充空白，剩余封闭空白着浅绿色。较低1024²采样与2048²结果的Orison正面面积差约 {front['convergence_absolute_difference_cm2']:.1f} cm²；这只是离散收敛观察，不是精确连续面积证明。</p><p><a href="web-assets/projection-data.json">查看投影数据与源文件哈希</a> · <a href="web-source/project.py">可复跑分析源码</a></p></details>
<div class="static-plates"><h3 class="static-heading">静态图版 / 无需脚本也可阅读</h3>{static}</div><noscript><p class="small">JavaScript未启用：三张完整静态图版在此直接列出；正文、轮廓、档案与章节锚点均保留。</p></noscript></section></div>
<section class="dark" id="continuous"><div class="shell section"><div class="section-top"><span class="section-number">02 — CONTINUITY</span><div><h2>没有端点。<br>不等于没有接缝问题。</h2></div></div><div class="void-layout"><figure class="seam-figure"><div class="plate">{image('assets/orison/seam-detail.png','Orison回环底部闭合区域的真实CPU近景渲染；图片表现外观，不是误差热图')}</div><figcaption class="small">闭合区域近景 / 外观图，不是误差热图。<a href="assets/orison/seam-detail.png">原图 ↗</a></figcaption></figure><div class="void-copy"><p>沿曲线走一圈，截面也必须回到同一朝向。这个模型让首尾共享索引，用周期截面转角保持接续；并非把两个端面藏在一起。</p><p>扫掠的转弯有多急、截面有多粗，也需要一起约束。漂亮的表面不能替代接缝、局部绕序与自交检查。</p><dl class="measure-list"><div><dt>路径采样 × 截面点</dt><dd>{con['station_count']} × {con['cross_section_vertices']}</dd></div><div><dt>曲率 × 截面半径，{diag['samples']} 样本最大值</dt><dd>{diag['max_curvature_radius_product']:.3f}</dd></div><div><dt>主变体宽 × 深 × 高</dt><dd>{dims['width']:.1f} × {dims['depth']:.1f} × {dims['height']:.1f} mm</dd></div></dl><p class="small">{boundary}</p>{'<a class="small" href="review/gate-review.md">读建模检查与边界 ↗</a>' if not draft else ''}</div></div></div></section>
<div class="shell"><section class="section" id="family"><div class="section-top"><span class="section-number">03 — THREE OPENINGS</span><div><h2>不是三种颜色。<br>是三种留白。</h2><p class="section-intro">三件使用同一材质语言，改变的是路径比例、截面与空间起伏。下面全部为正面正交投影，使用同一 500 mm 画幅；大小关系不由各自适配画框决定。</p></div></div><div class="variants">{family}</div><p class="small family-note">尺寸来自模型真实包围边界；截面宽深是名义输入，不等于每处恒定厚度。正面内空为同分辨率二维栅格估算，三者都不是体积或物理净空。</p></section>
<section class="section" id="record"><div class="section-top"><span class="section-number">04 — THE MAKING RECORD</span><div><h2>把来路也留下。</h2><p class="section-intro">观察页呈现形体，制作档案保留证据。原创建模、图版、投影分析和网页迭代各有来源，不用一个“通过”覆盖全部层级。</p></div></div><div class="archive-grid"><div><h3>三件模型 / 同一份来源</h3>{'<p class="pending">候选文件尚未冻结；下载在正式接入后开放。</p>' if draft else '<ul class="download-list">'+download+'</ul><p class="small"><a href="manifest.json">原模型manifest</a> · <a href="README.md">模型说明</a> · <a href="model-source.html">生成源与配置清单</a> · <a href="web-review/asset-parity.json">接入身份核对</a></p>'}</div><div><h3>这份网页怎样改进</h3><p>首版之后，实际看过原作者档案与美术馆页面。采用图版身份和档案分层，不采用遮住作品的巨标题，也不复制任何原作照片或模型。</p><div class="review-links"><a href="web-review/reference-notes.html">外部后评审 ↗</a><a href="web-review/design-review.html">设计改动 ↗</a><a href="design-case.html">前后与复盘 ↗</a></div><details><summary>通过、未验与不适用</summary><p>正文与原生章节锚点不依赖脚本。已做与未做的浏览器项目请看<a href="web-review/browser-qa.html">实际验收记录</a>，单元竞态不代替原生浏览器。GPU、真实iPhone/Android、200%缩放和完整屏幕阅读器检查不能由CPU图像或CSS视口担保。物理自立、烧制收缩、强度与制造性能不在本数字研究的保证内。</p></details></div></div></section></div></main><div class="shell"><footer class="footer"><span>造物手记 · 007 / ORISON 回环</span><span>{'真实候选 · 未冻结、未发布' if draft else '原创数字雕塑与独立观察网页 · <a href="../../methods/quality-workflow-v2/index.html">工作法 v2</a>'}</span></footer></div></body></html>'''
 (dest/'index.html').write_text(s)
 if not draft:
  parity=json.loads((dest/'web-review/asset-parity.json').read_text())
  rows=''.join(f'<li><a download href="{E(q["path"])}">{E(q["path"])}</a> <small>{q["bytes"]:,} bytes</small></li>' for q in parity['files'] if q['path'].startswith(('source/','configs/')) or q['path'] in ('README.md','schema.json'))
  (dest/'model-source.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>007 生成源与配置</title><link rel="stylesheet" href="style.css"></head><body class="report-page"><a href="index.html#record">← 返回制作档案</a><main><h1>生成源与配置</h1><p>以下为冻结模型原包的实际源文件。依照<a href="README.md">模型README</a>的环境与命令复现；需要同时保留脚本依赖及相应配置，不只下载单个GLB。完整离线包另行交付，此页不虚构整体ZIP入口。</p><ul>'+rows+'</ul><p><a href="web-review/asset-parity.json">全部原包文件SHA256</a></p></main></body></html>')
 for f in ['style.css','app.js','gallery-state.js']:
  if (ROOT/f).resolve()!=(dest/f).resolve():shutil.copy2(ROOT/f,dest/f)
 print('Composed','candidate' if draft else 'final',dest)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dest',type=Path,default=ROOT/'dist');p.add_argument('--draft',action='store_true');a=p.parse_args();compose(a.dest,a.draft)
