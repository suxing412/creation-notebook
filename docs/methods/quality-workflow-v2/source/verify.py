"""校验方法包与既有证据身份；不检验任意模型，不运行旧模型、渲染或浏览器。"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import argparse, hashlib, json, re, sys
sys.dont_write_bytecode=True
from zipfile import ZipFile
from build import P, dump, manifest

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=[];self.tags=[];self.lang=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append(tag)
        if tag=='html':self.lang=a.get('lang')
        if 'id' in a:self.ids.append(a['id'])
        for key in ('href','src'):
            if key in a:self.links.append(a[key])

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--evidence-root',required=True,type=Path);a=ap.parse_args();root=a.evidence_root.resolve();checks=[]
    def check(condition,label):
        if not condition:raise AssertionError(label)
        checks.append(label)
    def read(rel):return json.loads((root/rel).read_text())
    d=json.loads((P/'methods.json').read_text());idx=json.loads((P/'evidence-index.json').read_text());t=json.loads((P/'contract-template.json').read_text())
    check(len(d['rules'])==16 and len(d['groups'])==6,'16 条准则、6 类契约数量一致')
    check(len(set(r['id'] for r in d['rules']))==16,'规则标识无重复')
    evidence_ids={e['id'] for e in idx['entries']}
    check(len(evidence_ids)==30,'30 项证据身份无重复')
    for r in d['rules']:
        for k in ('decision','case','adopt','avoid','applicable','not_applicable','cost','evidence'):assert r[k],(r['id'],k)
        assert set(r['evidence'])<=evidence_ids
    checks.append('每条规则都有实际案例、采用／不采用、适用／不适用、成本及有效证据标识')
    for e in idx['entries']:
        f=(root/e['path']).resolve();assert f.is_relative_to(root) and f.is_file(),e['path'];b=f.read_bytes()
        assert e['bytes']==len(b) and e['sha256']==hashlib.sha256(b).hexdigest(),e['id']
        if e.get('member'):
            with ZipFile(f) as z: mb=z.read(e['member'])
            assert len(mb)==e['member_bytes'] and hashlib.sha256(mb).hexdigest()==e['member_sha256']
    checks.append('30 项既有公开证据及指定 ZIP 成员的当前字节与 SHA-256 对应索引一致')
    h=Links();h.feed((P/'index.html').read_text())
    check(h.lang=='zh-CN','页面声明中文')
    check(not {'script','img','video','audio','iframe','canvas'}&set(h.tags),'方法页没有脚本、图片、媒体、iframe 或 canvas 依赖')
    check(len(set(h.ids))==len(h.ids),'页面锚点无重复')
    for link in h.links:
        u=urlsplit(link);assert not u.scheme and not u.netloc,link
        if not u.path:
            assert unquote(u.fragment) in h.ids,link
        elif u.path.startswith('../../'):
            target=(root/u.path[6:]).resolve();assert target.is_relative_to(root) and target.is_file(),link
        elif u.path=='verification.json':pass
        else:
            target=(P/unquote(u.path)).resolve();assert target.is_relative_to(P) and target.is_file(),link
    checks.append('页面原生锚点、本地文档、返回图库与所有既有证据目标存在；没有外部请求链接')
    check(t['可发布'] is False and t['当前状态']=='未填写，不可放行','契约模板保持未填写／不可放行')
    check(t['构件对契约']['未声明构件对的处理']=='拒绝' and t['构件对契约']['含糊allowedPairs的处理'].startswith('拒绝'),'模板明确拒绝未声明构件对及含糊 allowedPairs')
    check(all(x['状态']=='未验' for x in t['分层状态']),'模板分层状态没有预填通过')
    # 以下仅复核旧报告已经存在的事实，不重新执行报告对应的测试。
    before=read('studies/006/review/gate-world-inversion-before.json');after=read('studies/006/review/gate-world-inversion-after.json')
    check(before['passed'] is True and after['passed'] is False and bool(after['non_positive_world_volume']),'既有证据核对：006 世界反向旧错误 PASS 与修复后专用拒绝均保留')
    q=read('studies/006/review/gate-coplanar-quantization-reproduction.json')
    check([r['coplanar_count'] for r in q['cases']]==[0,1,0],'既有证据核对：共面专项旧 0／新 1／移离控制 0')
    check(q['cases'][1]['thresholds']['coplanar_plane_distance_m']==5e-8 and q['cases'][1]['thresholds']['positive_overlap_axis_m']==1e-8,'既有证据核对：50 nm 双向距离与 10 nm 投影轴重叠，不混称面积')
    f=read('studies/006/review/gate-fault-tests.json')
    check(len(f['tests'])==18 and all(x['rejected'] and x['dedicated_detector_triggered'] for x in f['tests']),'既有证据核对：006 的 18 项真实故障均记录拒绝及专用命中')
    s=read('fusions/F03/reports/scene-tests.json');frow=next(x for x in s['tests'] if x['check']=='assembled world geometry / folio')
    check(frow['sourceVertices']==6072 and frow['assembledVertices']==6098 and frow['topologyIndexIdentityClaimed'] is False,'既有证据核对：F03 拆点数量与不宣称拓扑索引同一')
    sb=read('fusions/F03/reports/independent-state-before.json');sa=read('fusions/F03/reports/independent-state-after.json')
    check(any(x['passed'] is False for x in sb['results']) and all(x['passed'] for x in sa['results']),'既有证据核对：异步旧失败与分离会话后的有限状态回归')
    allowed={'.html','.css','.json','.md','.py'}
    banned=[chr(47)+'workspace'+chr(47),chr(47)+'home'+chr(47),chr(47)+'tmp'+chr(47),'file'+':'+chr(47)*3]
    files=[x for x in P.rglob('*') if x.is_file() and '__pycache__' not in x.parts]
    for f in files:
        assert f.suffix in allowed, f.name
        txt=f.read_text();assert not any(x in txt for x in banned),f.name
    checks.append('本包仅文本 HTML／CSS／JSON／Markdown／Python；未带模型、图片、日志、坏二进制或私有绝对路径')
    report={'date':'2026-11-01','passed':True,'scope':'本方法包静态结构、链接、证据身份与少量既有报告事实复核。不是重新执行模型／GPU／浏览器／渲染测试。','checks':checks,'html_reference_count':len(h.links),'evidence_count':len(evidence_ids),'native_browser':{'status':'未验','reason':'未启动服务、未占用共享浏览器；应在图库接入后单独进行原生桌面／窄屏／键盘展开与导航检查。'},'unverified':['本方法页原生浏览器布局','本方法页打印展开样式','旧模型及旧报告对应的测试重跑','GPU／真实手机／制造性能'],'budget_bytes':1000000}
    report['total_bytes_at_check']=0
    for _ in range(10):
        dump(P/'verification.json',report);manifest()
        all_files=[x for x in P.rglob('*') if x.is_file() and '__pycache__' not in x.parts]
        total=sum(x.stat().st_size for x in all_files)
        assert total<1000000,total
        if report['total_bytes_at_check']==total:break
        report['total_bytes_at_check']=total
    else:raise AssertionError('最终体积记录未收敛')
    # 再核对最终清单本身列出的真实内容，避免修改报告后沿用旧哈希。
    m=json.loads((P/'manifest.json').read_text())
    for row in m['files']:
        b=(P/row['path']).read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
    final_total=sum(x.stat().st_size for x in all_files)
    print(json.dumps({'方法包静态检查':'通过','最终合计字节':final_total,'文件数':len(all_files),'证据项':len(evidence_ids),'说明':'不代表模型、浏览器或 GPU 重新验收。'},ensure_ascii=False))
if __name__=='__main__':main()
