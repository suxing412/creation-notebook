from pathlib import Path
import json,html
R=Path(__file__).resolve().parent;D=(R/'dist') if (R/'dist').is_dir() else ((R.parent/'dist') if (R.parent/'dist').is_dir() else R.parents[1]/'docs');e=html.escape
m=json.loads((R/'manifest.json').read_text()); ledger=json.loads((R/'publication-ledger.json').read_text())
items=[]
for x in m['studies']:
 kind=x.get('kind','regular'); links=[['作品网页',x.get('webPrototype',x['path'])],['模型／观察',x.get('modelView',x['path'])],['设计复盘',x['designCase']]]
 if kind=='regular':links.append(['建模复盘',x.get('modelReflection',x['path']+'study-notes.html')])
 if kind=='fusion':links=[v for v in links if v[0]!='模型／观察']
 if x.get('qaReport'):links.append(['检查证据',x['qaReport']])
 if x.get('evidenceContext'):links.append(['时代地域与来源',x['evidenceContext']['url']])
 if x.get('referenceCatalog'):links.append(['汉代建筑参考库',x['referenceCatalog']])
 if kind=='regular':
  links += [['关联空间 '+q['id']+' · '+q['title'],q['entry']] for q in m.get('spaceDesigns',[]) if x['id'] in q.get('pairedStudyIds',[])]
 if x.get('source'):links.append(['源文件',x['source']])
 items.append(dict(id=x['id'],kind=kind,evidenceContext=x.get('evidenceContext'),architecturalType=x.get('architecturalType'),designStatus=x.get('designStatus',''),name=x['name'],english=x['english'],path=x['path'],image=x['image'],alt=x['alt'],description=x['description'],qa=x['qa'],pending=x['pending'],links=links,archive='已归档',publication=ledger['items'].get(x['id'],{}).get('state','pending'),webStatus=x.get('webStatus','限定检查；未覆盖GPU与真机')))
for x in m.get('spaceDesigns',[]):
 paired=[a for a in m['studies'] if a['id'] in x.get('pairedStudyIds',[])]
 items.append(dict(id=x['id'],kind='space-design',designStatus=x['status'],acceptance=x['acceptance'],countsAsAcceptedSpatialDesign=x['countsAsAcceptedSpatialDesign'],name=x['title'],english='SPATIAL DESIGN PROTOTYPE',path=x['entry'],image=x['poster'],alt=x['title']+' · Blender CPU离线场景图，非GPU运行截图',experienceIntent=x.get('experienceIntent',''),pairedStudyIds=x.get('pairedStudyIds',[]),description=x['subtitle'],qa='检查范围及身份见原型评审；CPU/模拟/无GL备用模式各自限定。',pending='；'.join(x['limits']),links=[['进入空间原型',x['entry']],['设计评审与检查',x['designReview']],['完整源包',x['source']]]+[['历史 '+h['version'],h['entry']] for h in x.get('history',[])]+[['配对模型 '+a['id']+' · '+a['name'],a['path']] for a in paired]+[['复用条件',x['reuse']]],version=x.get('version',''),archive='已归档',publication=ledger['items'].get(x['id'],{}).get('state','pending')))
for x in m['recipes']:
 items.append(dict(id=x['id'],kind='recipe',name=x['name'],english='REUSABLE RECIPE',path=x['path'],image=x['image'],alt='三种真实陶瓷翼几何参数对照',description='同一生成器，三种几何；保留输入条件、构造不变量与失败边界。',qa='有限预设和重复生成检查，不是连续参数域证明。',pending='实体制造及任意几何迁移未验。',links=[['配方',x['path']],['复现条件',x['method']],['复盘',x['reflection']],['源文件',x['source']]],archive='已归档',publication=ledger['items'].get(x['id'],{}).get('state','pending')))
for x in m['methods']:
 items.append(dict(id=x['id'],kind='method',name=x['title'],english='QUALITY WORKFLOW',path=x['path'],image='',alt='',description='16条条件化准则与30项证据，逐项记录几何、导出、网页和发布边界。',qa='工作法与执行清单，不是通用检查器。',pending='新形体仍需针对性测试；不计作新作品或配方。',links=[['阅读工作法',x['path']],['执行清单',x['path']+'checklist.md']]+[[q['label']+('（新附录待核验）' if q.get('publicationKey') and ledger.get('supplements',{}).get(q['publicationKey'],{}).get('state')!='verified' else ''),q['path']] for q in x.get('research',[])],archive='已归档',publication=ledger['items'].get(x['id'],{}).get('state','pending')))
for item in items:
 if item['id']==m.get('featuredId'):item['featured']=True
 if item.get('evidenceContext') is None:item.pop('evidenceContext',None)
 if item.get('architecturalType') is None:item.pop('architecturalType',None)
mapping_path=D/'downloads/delivery-map.json'
if mapping_path.exists():
 mapping={a['originalPath']:a['downloadPage'] for a in json.loads(mapping_path.read_text())['archives']}
 for item in items:item['links']=[[label,mapping.get(url.removeprefix('./'),url)] for label,url in item['links']]
(D/'catalog.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
labels={'space-design':'3D空间设计原型','regular':'模型与介绍页','fusion':'历史空间网页实验','recipe':'几何配方','method':'工作方法'}
def status(x):return '<span class="badge">已归档</span><span class="badge '+('live' if x['publication']=='verified' else 'pending')+'">'+('公开已核验' if x['publication']=='verified' else '公开待核验')+'</span>'
def design_status(x):return (('<span class="badge">'+e(x['version'])+'</span>') if x.get('version') else '') + '<span class="badge pending">'+e(x['designStatus'])+'</span>' if x.get('designStatus') else ''
def links(x):return ''.join(f'<a href="{e(url)}">{e(label)} ↗</a>' for label,url in x['links'])
def card(x):
 c=x.get('evidenceContext');context=('<p class="evidence-context">'+(('<b>空间类型：</b>'+e(x['architecturalType'])+'<br>') if x.get('architecturalType') else '')+'<b>参考时期：</b>'+e(c['period'])+'<br><b>主参考地域：</b>'+e(c['region'])+'<br><b>证据边界：</b>'+e(c['level'])+'</p>') if c else ''
 img=f'<a class="cover" href="{e(x["path"])}"><img src="{e(x["image"])}" alt="{e(x["alt"])}" loading="lazy" width="960" height="720"></a>' if x['image'] else '<div class="method-cover" aria-hidden="true">条件 → 证据 → 复现</div>'
 return f'''<article class="work" id="work-{e(x['id'])}" data-id="{e(x['id'])}" data-kind="{e(x['kind'])}" data-search="{e(x['id']+' '+x['name']+' '+x['english']+' '+x['description']+' '+x.get('architecturalType','')+' '+ ' '.join(str(v) for v in (x.get('evidenceContext') or {}).values()))}">{img}<div class="work-body"><p class="eyebrow">{e(x['id'])} / {labels[x['kind']]}</p><h3>{e(x['name'])}<small>{e(x['english'])}</small></h3><div class="badges">{status(x)}{design_status(x)}</div><p>{e(x['description'])}</p>{context}{('<p class="experience-intent"><b>空间任务：</b>'+e(x['experienceIntent'])+'</p>') if x.get('experienceIntent') else ''}<div class="links">{links(x)}</div><details><summary>检查、不足与复用边界</summary><p><b>已做检查：</b>{e(x['qa'])}</p><p><b>仍未验证：</b>{e(x['pending'])}</p><p>{e(x.get('webStatus',''))}</p></details><button class="locate" data-select="{e(x['id'])}" hidden>在空间目录中定位</button></div></article>'''
regular=sorted([x for x in items if x['kind']=='regular'],key=lambda x:x['id'],reverse=True); fusion=sorted([x for x in items if x['kind']=='fusion'],key=lambda x:x['id'],reverse=True); methods=[x for x in items if x['kind'] in ('recipe','method')]
prototypes=[x for x in items if x['kind']=='space-design'];latest_prototype=prototypes[-1] if prototypes else None
sections=''
for sid,title,subtitle,group in [('works','模型与介绍页','一件模型设计，以及介绍它本身的网页设计',regular),('fusions','历史空间网页实验','4项旧版实验已公开；按新的整页三维空间要求待重做',fusion),('recipes','复用方法','条件与失败边界，比一键万能更有价值',methods)]:
 if sid=='fusions':sections+='<section id="spatial-design" class="collection"><div class="section-heading"><h2>3D空间设计 <span>0 已验收 · '+str(len(prototypes))+' 原型</span></h2></div><p>SD01以连接操作理解构件；SD02以连续场所观察比较建筑关系。两者都仍是待验原型，不因公开而提升设计验收。目标是整个页面成为可探索的三维空间：布局、导航和内容在空间内，HTML仅按需叠层。原型主体验按整视口连续空间组织，尚待实时与用户方向验收，不等于已满足要求。</p><div class="grid">'+''.join(card(x) for x in prototypes)+'</div><p>下方历史实验继续保留，不计为满足新要求的成品；公开状态和设计验收分开记录。</p></section>' 
 sections+=f'<section id="{sid}" class="collection"><div class="section-heading"><h2>{title} <span>{len(group):02}</span></h2><p>{subtitle}</p></div><div class="grid">'+''.join(card(x) for x in group)+'</div></section>'
# Optional semantic comparison is generated from the same manifest; no extra viewer/control.
comparison=''
lookup={x['id']:x for x in items}
for c in m.get('comparisons',[]):
 if not all(i in lookup for i in c['ids']):continue
 cells=''
 for i in c['ids']:
  x=lookup[i];ec=x['evidenceContext']
  cells+='<div><h3><a href="'+e(x['path'])+'">'+e(i+' · '+x['name'])+' ↗</a></h3><p><b>'+e(x.get('architecturalType',''))+'</b></p><p>'+e(ec['period'])+' · '+e(ec['region'])+'</p><p>'+e(ec['level'])+'</p><a href="'+e(ec['url'])+'">核对本件来源与解释 ↗</a></div>'
 comparison+='<section id="'+e(c['id'])+'" class="architecture-reading"><p class="eyebrow">READ THE DIFFERENCE</p><h2>'+e(c['title'])+'</h2><p>'+e(c['claim'])+'</p><div class="architecture-pair">'+cells+'</div><p class="fine">'+e(c['reuseBoundary'])+'</p></section>'

def research_links(project):
 update=project.get('researchUpdates')
 if not update:return ''
 registry=json.loads((D/update['registry']).read_text())
 links=''.join('<li><a href="'+e(update['entry']+'#'+x['id'])+'">'+e(x['name'])+'</a> — '+e(x['archiveStatus']+' / '+x['publicationStatus']+' / '+x['designStatus'])+'</li>' for x in registry['entries'])
 links+=''.join('<li><a href="'+e(update['entry']+'#'+x['id'])+'">附录：'+e(x['name'])+'</a> — '+e(x['status'])+'</li>' for x in registry.get('appendices',[]))
 return '<nav class="research-nav" aria-label="城市研究记录"><p>城市研究旁路 · 不计入作品展台</p><ul>'+links+'</ul><p>'+str(registry['currentDesignCourtyards'])+'院 / '+str(registry['standaloneArchiveItems'])+'项归档保持不变；研究不是新增作品。</p></nav>'
research_navigation=''.join(research_links(p) for p in m.get('ongoingProjects',[]))

# Projects are ongoing research entries, not accepted or completed catalog works.
projects=''
project_publication=ledger.get('projects',{}).get('luoyang',{}).get('state','pending')
for project in m.get('ongoingProjects',[]):
 update=project.get('researchUpdates')
 if update:projects+='<section class="architecture-reading"><p class="eyebrow">LATEST RESEARCH / NOT PUBLISHED</p><h2>街区研究进展</h2><p><b>全城证据：42项标记＝36 B示意＋6未定位/排除；证据标记不等于建筑完成。</b><br>另有44个C设计院落；不能换算全城完成率。下一阶段：现有街区→巷→主路→一门一段城垣。<a href="cities/luoyang/research/2026-11-03/#city-coverage">区域覆盖与里程碑 ↗</a></p><p>'+e(update['label'])+'</p><a href="'+e(update['entry'])+'">查看全部街区研究 ↗</a>'+research_links(project)+'</section>'
 projects+='<section id="'+e(project['id'])+'" class="architecture-reading ongoing-project"><p class="eyebrow">CITY PROJECT / IN PROGRESS</p><h2>'+e(project['title'])+' <small>进行中</small></h2><p class="fine">'+('公开已核验' if project_publication=='verified' else '公开待核验')+'</p><p>'+e(project['description'])+'</p><p class="fine">'+e(project['boundary'])+'</p><div class="links"><a class="primary" href="'+e(project['path'])+'">进入城市项目 ↗</a><a href="'+e(project['evidence'])+'">证据与范围说明 ↗</a></div><p class="fine">本入口独立于下方作品归档，不新增完成作品或空间验收计数。</p></section>'
latest=regular[0]; published=sum(x['publication']=='verified' for x in items)
publication_note=('全部条目的公开入口与内容访问均已有核验记录。' if published==len(items) else '其余入口在归档中可用，公开部署仍待核验。')
buttons=''.join(f'<button data-select="{e(x["id"])}" aria-pressed="false">{e(x["id"])} · {e(x["name"])}</button>' for x in items)
featured=next((x for x in items if x.get('featured')),None)
primary_actions=(('<a class="primary" href="'+e(latest['path'])+'">最新作品 '+e(latest['id'])+' · '+e(latest['name'])+' ↗</a><a href="'+e(latest['evidenceContext']['url'])+'">先看时代地域与来源 ↗</a>') if latest.get('evidenceContext') else '')
if featured and featured['kind']=='space-design':
 primary_actions='<a class="primary" href="'+e(featured['path'])+'">最新空间 '+e(featured['id'])+' · '+e(featured['name'])+' ↗</a>'
 primary_actions+='<a href="'+e(next(u for label,u in featured['links'] if label=='设计评审与检查'))+'">原理、参考与限制 ↗</a>'
 primary_actions+=''.join('<a href="'+e(a['path'])+'">返回模型 '+e(a['id'])+' · '+e(a['name'])+' ↗</a>' for a in items if a['id'] in featured.get('pairedStudyIds',[]))
if m.get('ongoingProjects'):
 primary_actions='<a href="cities/luoyang/research/2026-11-03/">最新研究 · 已公开·研究候选预览 ↗</a><a class="primary" href="cities/luoyang/">最新城市阶段 · C02固定几何变体 ↗</a><a href="cities/luoyang/project-notes.html">范围与历史版本 ↗</a>'+primary_actions
secondary_latest=('<a href="#work-'+e(latest['id'])+'">最近模型 '+e(latest['id'])+' · '+e(latest['name'])+' ↓</a>') if not primary_actions else ''
body=f'''<header><a class="brand" href="./">造物手记 <small>Creation Notebook</small></a><nav aria-label="目录">{('<a href="#city-luoyang">城市项目 · 进行中</a>') if projects else ''}<a href="#works">模型与介绍页 {len(regular)}</a><a href="#spatial-design">3D空间设计 0＋{len(prototypes)}原型</a><a href="#recipes">复用方法 {len(methods)}</a><a href="#publication">状态</a></nav></header><main id="main"><section class="hero"><div><p class="eyebrow">AN EVOLVING ARCHIVE / {e(m['updated'])}</p><h1>把想象做成有形之物，<br>把经验留下来。</h1><p class="lead">原创模型、网页与可复现的制作记录。<br>先看作品，也能直接找到它的源码、检验与不足。</p><div class="hero-actions">{primary_actions}{('<a class="'+('' if primary_actions else 'primary')+'" href="'+e(latest_prototype['path'])+'">体验 '+e(latest_prototype['id'])+' 空间原型 ↗</a>') if latest_prototype and not(featured and featured['kind']=='space-design') else ''}{secondary_latest}<a href="#works">浏览全部作品 ↓</a></div><p class="counts">{len(regular)} 项模型与介绍页 · 0 项已验收3D空间设计 · {len(prototypes)} 项空间原型 · {len(fusion)} 项历史实验待重做 · {len(methods)} 项复用方法</p><p class="cycle-guide"><b>模型与介绍页</b>：模型设计＋介绍模型本身的网页。<br><b>3D空间设计</b>：整页可探索的三维空间，而非网页内嵌3D窗口。</p></div><aside class="space-invite"><p class="eyebrow">A DIRECTORY YOU CAN ENTER</p><h2>也可以，走进目录。</h2><svg viewBox="0 0 320 130" role="img" aria-label="抽象空间目录示意（不表示实际分区数量），非实时渲染"><path d="M24 110L157 36L299 106L166 126Z" fill="#ded9ca"/><g fill="#8d4936"><path d="M50 91v-28l17-9v28zM82 74V46l17-9v28zM114 57V29l17-9v28z"/></g><g fill="#51716c"><path d="M180 46v30l20 10V56zM213 64v30l20 10V74zM246 82v30l20 10V92z"/></g><path d="M139 99l23-13 28 14-23 13zM139 94l23-13 28 14-23 13z" fill="#aa8e4e"/></svg><button id="enter-space" hidden>开启 3D 目录索引 ↗</button><noscript><p>无脚本模式：下方完整目录和所有作品入口仍可阅读。</p></noscript><p class="fine">这是作品目录索引，不是整页3D空间设计范例。轻量符号，不自动加载原模型。<br>3D 需 WebGL；真实 GPU 与手机表现未验。</p></aside></section>{projects}<section id="space" hidden aria-label="三维空间目录"><div class="space-head"><h2>目录索引 <small>模型与介绍页 · 新空间原型 · 历史实验 · 方法</small></h2><button id="close-space">关闭 3D，保留列表</button></div><p id="space-status" role="status">尚未启动。</p>{research_navigation}<div class="space-grid"><div id="space-canvas"></div><aside id="selected" aria-live="polite"><h3>选择一个展台</h3><p>展台是目录符号，不是原始模型。所有条目也可用下方按钮选择。</p></aside></div><div class="space-controls"><button id="reset-space">展区全景</button><div class="space-picks" aria-label="与展台等价的键盘目录">{buttons}</div></div></section><section id="publication" class="publication"><h2>归档与上线，分开记录。</h2><p>共 {len(items)} 项已归档，{published} 项公开状态已核验。{publication_note}发布不代表所有交互或工程性能已验证。</p><details><summary>查看公开记录与当前验收边界</summary><p>状态核验截至 {e(ledger['verifiedAt'])}。<a href="publication-ledger.json">查看状态依据</a>；实际网页应在每次部署后再次核验，未核验前不自动提升状态。</p><p>本总览的空间图形是索引符号。GPU 动态、深度闪烁、实体手机与完整读屏未验。各作品的具体限制保留在卡片及原报告中。</p></details></section><section class="find-works" id="find-works" hidden aria-label="查找作品"><div class="find-heading"><h2>找一件作品</h2><p>筛选完整列表；3D目录仍保留全部条目。</p></div><form id="catalog-filter" role="search"><label for="work-search">名称、编号或关键词<input id="work-search" name="q" type="search" placeholder="例如：010、折光、空间" autocomplete="off"></label><label for="work-kind">作品类型<select id="work-kind" name="kind"><option value="all">所有类型</option><option value="regular">模型与介绍页</option><option value="space-design">3D空间设计原型</option><option value="fusion">历史空间网页实验</option><option value="methods">复用方法</option></select></label><button type="reset">清空筛选</button></form><p id="filter-status" role="status" aria-live="polite">显示全部 {len(items)} 项。</p><p id="filter-empty" hidden>没有找到匹配条目。试试缩短关键词，或清空筛选。</p></section>{comparison}{sections}<section class="maintenance"><p class="eyebrow">THE INDEX IS PART OF THE WORK</p><h2>每一版，都把目录一起做好。</h2><p>每版产出同步清单、公开状态与链接；复查最新入口、分类、窄屏、键盘及无脚本，再部署核验。</p><div class="links"><a href="overview-review.html">本次总览评审与修订 ↗</a><a href="overview-acceptance.md">逐版总览验收清单 ↗</a><a href="research/frontier-design-watch-2026-11-01.html">技术观察 ↗</a></div></section></main><footer>造物手记 · Creation Notebook <a href="#main">回到目录顶部 ↑</a></footer>'''
(D/'index.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="原创3D模型、独立网页与空间实验的持续档案；可复现方法、公开状态与验收证据分开记录。"><title>造物手记 · Creation Notebook</title><link rel="stylesheet" href="overview.css"></head><body><a class="skip" href="#main">跳至作品目录</a>'+body+'<script type="module" src="overview-app.js"></script></body></html>')
(D/'publication-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
print('Overview built',len(items),'items',published,'verified public')
