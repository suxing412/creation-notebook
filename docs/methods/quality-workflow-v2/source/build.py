"""仅构建方法文档；不执行几何、浏览器或渲染验收。"""
from pathlib import Path
from html import escape
import argparse, hashlib, json
from zipfile import ZipFile
P=Path(__file__).resolve().parent.parent

def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def manifest():
    rows=[]
    for p in sorted(P.rglob('*')):
        if not p.is_file() or p.name=='manifest.json' or '__pycache__' in p.parts: continue
        data=p.read_bytes()
        rows.append({'path':p.relative_to(P).as_posix(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    dump(P/'manifest.json',{'title':'造物手记工作法 v2 文件清单','version':'2.0.0','scope':'仅本方法包；不含旧模型、图片和原始日志。清单不哈希自身。','budget_bytes':1000000,'files':rows,'bytes_excluding_manifest':sum(r['bytes'] for r in rows)})

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--evidence-root',required=True,type=Path);args=a.parse_args()
    root=args.evidence_root.resolve();d=json.loads((P/'methods.json').read_text());ev={e['id']:e for e in d['evidence']};idx=[]
    for e in ev.values():
        f=(root/e['path']).resolve()
        if not f.is_relative_to(root) or not f.is_file():raise ValueError('缺少公开证据：'+e['path'])
        b=f.read_bytes();item={**e,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
        if e.get('member'):
            with ZipFile(f) as z: mb=z.read(e['member'])
            item['member_bytes']=len(mb);item['member_sha256']=hashlib.sha256(mb).hexdigest()
        idx.append(item)
    dump(P/'evidence-index.json',{'date':d['date'],'scope':'只读核对既有公开证据的身份；不是重新运行报告中的测试。','entries':idx})
    def evidence_links(ids):return ''.join('<li><a href="../../'+escape(ev[i]['path'],quote=True)+'">'+escape(ev[i]['label'])+'</a></li>' for i in ids)
    group_ids={g:'group-'+str(i+1) for i,g in enumerate(d['groups'])}
    nav=''.join('<a href="#'+group_ids[g]+'"><span>0'+str(i+1)+'</span>'+escape(g)+'</a>' for i,g in enumerate(d['groups']))
    sections=[]
    for i,g in enumerate(d['groups']):
        cards=[]
        for r in [x for x in d['rules'] if x['group']==g]:
            cards.append('''<article class="rule" id="{id}"><div class="rule-head"><span class="rule-id">{id}</span><h3>{title}</h3></div><p class="decision">{decision}</p><p class="case"><b>真实案例</b>　{case}</p><details><summary>怎么用 · 适用边界与成本</summary><div class="detail-content"><dl><dt>采用</dt><dd>{adopt}</dd><dt>不采用</dt><dd>{avoid}</dd><dt>适用</dt><dd>{applicable}</dd><dt>不适用</dt><dd>{not_applicable}</dd><dt>成本取舍</dt><dd>{cost}</dd></dl></div></details><div class="evidence"><p>已有公开证据</p><ul>{links}</ul></div></article>'''.format(**{k:escape(str(v)) for k,v in r.items() if k!='evidence'},links=evidence_links(r['evidence'])))
        sections.append('<section class="method-group" id="'+group_ids[g]+'"><div class="section-heading"><span>0'+str(i+1)+'</span><h2>'+escape(g)+'</h2><a href="#contents">回目录 ↑</a></div>'+''.join(cards)+'</section>')
    evidence_list=''.join('<li><a href="../../'+escape(e['path'],quote=True)+'">'+escape(e['label'])+'</a><code>'+escape(e['path'])+'</code></li>' for e in d['evidence'])
    limits=''.join('<li>'+escape(x)+'</li>' for x in d['unverified'])
    html='''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="从005、006、F03与陶瓷翼真实修复中整理的16条条件化工作准则。保留错误历史，给出证据与边界，不假称通用几何证明。"><title>造物手记工作法 v2 · 方法资产</title><link rel="stylesheet" href="style.css"></head>
<body><a class="skip" href="#main">跳到正文</a><header class="top"><a class="brand" href="../../index.html">← 返回造物手记</a><span>方法资产 · v2.0</span></header>
<main id="main"><section class="hero"><p class="eyebrow">造物手记工作法 v2 · 2026.11.01</p><h1>把一次修好，<br>变成下次可复现。</h1><p class="lead">不是收集更多“通过”，而是写清<strong>在什么条件下，什么证据足以支持什么结论。</strong>从真实失败里提炼规则，换一个模型时仍知道哪些可以继承、哪些必须重做。</p><div class="hero-actions"><a class="button" href="checklist.md">执行检查清单 ↗</a><a class="button secondary" href="contract-template.json" download>下载契约模板 ↓</a><a href="methods.json" download>源 JSON ↓</a></div><p class="fine">16 条准则 · 6 类契约 · 零图片／模型复制 · 纯静态阅读<br>方法整理，不新增常规作品、融合轮或几何配方。</p></section>
<aside class="boundary"><strong>先说边界</strong><p>本轮只读审阅既有证据，没有重新跑旧模型、浏览器、GPU 或渲染测试，也没有新增联网研究。有限样本和反例回归不是全域证明；本页不是通用模型检查器。</p></aside>
<section id="contents" class="contents"><div class="section-heading"><span>路线</span><h2>从这次要做的事开始</h2></div><div class="routes"><a href="#P01"><b>生成新参数组合</b><span>先锁家族与不变量，再验真实网格。</span></a><a href="#I02"><b>把原件放进新场景</b><span>分清文件同一、几何保真与投影一致。</span></a><a href="#B01"><b>让作品成为网页</b><span>阅读不中断，异步不串扰，发布不夹带。</span></a></div><nav aria-label="六类方法">'''+nav+'''</nav></section>
<section class="memory"><div><p class="eyebrow">值得继承的不是“始终正确”</p><h2>旧错误 PASS，<br>也是资产的一部分。</h2></div><ol><li><b>005 · 合法接触旁的异常</b><span>同一 pair 仍能藏穿出体与包容岛；靠名字放行不够。</span></li><li><b>006 · 精度与坐标系</b><span>double 后处理救不回 float32 量化；局部正体积不保证世界朝外。</span></li><li><b>F03 · 独立生命周期</b><span>3D 失败不该取消用户正在打开的章节。</span></li></ol><p class="fine">新反例揭示检查器盲区，不等于原始交付件已损坏。005 未追改为 006 门禁。坏二进制与原始日志不在本包内。</p></section>
'''+''.join(sections)+'''
<section class="toolkit" id="toolkit"><p class="eyebrow">拿走流程，不拿走含糊的保证</p><h2>开始下一件之前，填一份契约。</h2><p>先定义你的家族，再把这里的准则翻译成自己的约束。所有未填字段保持“不可放行”。只写 <code>allowedPairs</code> 的整对豁免必须拒绝；模板本身不会替你检查网格。</p><div class="download-grid"><a href="checklist.md"><b>执行清单</b><span>七个步骤，每步有停止条件。</span></a><a href="contract-template.json" download><b>契约模板</b><span>参数、状态、接触、身份、分层验收。</span></a><a href="methods.json" download><b>方法源 JSON</b><span>16 条规则与逐条证据，可继续迭代。</span></a><a href="README.md"><b>使用与部署说明</b><span>轻量发布，不重复搬运旧资产。</span></a></div></section>
<section class="limits" id="limits"><h2>仍然不能承诺什么</h2><ul>'''+limits+'''</ul><p>本页的静态结构与链接检查不等于原生浏览器布局验收。F03 的浏览器测试属于 F03，不能给本页或任意新网页代领通过。</p></section>
<section class="sources" id="evidence"><div class="section-heading"><span>证据</span><h2>回到原案例，核对原结论</h2></div><p>以下链接指向已有图库公开交付路径；本页不重新包装旧图片、模型和报告。所有来源的本轮实读字节与 SHA-256 见 <a href="evidence-index.json">证据身份索引</a>。这里的“公开路径”是可随图库分发的路径，不表示该私有站点对全网开放。</p><details><summary>展开全部 30 项证据入口</summary><ol>'''+evidence_list+'''</ol></details></section>
</main><footer><a href="../../index.html">← 返回造物手记</a><p>让结论可追问，让改进可复用。</p><div><a href="manifest.json">文件清单</a> · <a href="verification.json">本包检查范围</a></div></footer></body></html>
'''
    (P/'index.html').write_text(html);manifest();print('方法页已构建；旧作品未修改。')
if __name__=='__main__':main()
