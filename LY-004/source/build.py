# -*- coding: utf-8 -*-
"""LY-004 生成与核对脚本（只读仓库，只写 --out）。

python -I -B build.py --lab D:/GitHub/creation-notebook-lab --commit bce3211 \
    --ly001 ../../LY-001 --ly002 ../../LY-002 --ly005 ../../LY-005 \
    --external <含 gao2023.pdf 与 gao2023_raw.txt 的目录> --out ..

退出码 0 = 全部硬检查通过；缺 --external 时版权来源引文与图1读数记为'未复核'，退出码 2。
"""
import argparse, hashlib, json, math, os, re, subprocess, sys, html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_data as SD  # noqa: E402

FAIL = []


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(p):
    with open(p, 'rb') as f:
        return sha(f.read())


def jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')


def check(name, ok, detail=None):
    if not ok:
        FAIL.append(name)
    return {"check": name, "pass": bool(ok), "detail": detail}


# ------------------------------------------------------------------ 仓库只读
class Repo:
    def __init__(self, lab, commit):
        self.lab, self.commit = lab, commit
        self.full = subprocess.run(['git', '-C', lab, 'rev-parse', commit], capture_output=True, text=True, check=True).stdout.strip()
        self.files = {}

    def show(self, path):
        b = subprocess.run(['git', '-C', self.lab, 'show', f'{self.commit}:{path}'], capture_output=True, check=True).stdout
        wt = os.path.join(self.lab, path)
        wsha = fsha(wt) if os.path.exists(wt) else None
        self.files[path] = {"commitBytesSha256": sha(b), "bytes": len(b), "worktreeSha256": wsha,
                            "worktreeEqualsCommit": wsha == sha(b)}
        return b

    def json(self, path):
        return json.loads(self.show(path).decode('utf-8'))


# ------------------------------------------------------------------ 文本
def flat_html(b, enc):
    s = b.decode(enc, 'replace')
    s = re.sub(r'(?is)<(script|style).*?</\1>', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = _html.unescape(s)
    return re.sub(r'\s+', '', s)


def flat_plain(b, enc):
    return re.sub(r'\s+', '', b.decode(enc, 'replace'))


def resolve(spec, a):
    pre, rel = spec.split(':', 1)
    if pre == 'LY002':
        return os.path.join(a.ly002, rel)
    if pre == 'LY004':
        return os.path.join(HERE, '..', rel)
    if pre == 'EXT':
        return os.path.join(a.external, rel.split('#')[0]) if a.external else None
    raise ValueError(spec)


# ------------------------------------------------------------------ 几何
def pip(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def seg_inter(p1, p2, p3, p4):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(p3, p4, p1), o(p3, p4, p2), o(p1, p2, p3), o(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def poly_inter(a, b):
    if any(pip(p, b) for p in a) or any(pip(p, a) for p in b):
        return True
    for i in range(len(a)):
        for j in range(len(b)):
            if seg_inter(a[i], a[(i + 1) % len(a)], b[j], b[(j + 1) % len(b)]):
                return True
    return False


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(a, b):
    if poly_inter(a, b):
        return 0.0
    m = float('inf')
    for p in a:
        for j in range(len(b)):
            m = min(m, seg_dist(p, b[j], b[(j + 1) % len(b)]))
    for p in b:
        for j in range(len(a)):
            m = min(m, seg_dist(p, a[j], a[(j + 1) % len(a)]))
    return m


def circle(c, r, n=32):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def glb_tris(b, node_matrix_cm):
    """读 GLB 字节，返回世界坐标三角形 (n,3,3)。只支持本仓库用到的非交错 float/uint 访问器。"""
    import struct
    import numpy as np
    off = 12; js = None; bins = None
    while off < len(b):
        cl, ct = struct.unpack('<II', b[off:off + 8]); ch = b[off + 8:off + 8 + cl]
        if ct == 0x4E4F534A:
            js = json.loads(ch.decode('utf-8'))
        elif ct == 0x004E4942:
            bins = ch
        off += 8 + cl
    COMP = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
    NC = {'SCALAR': 1, 'VEC3': 3}

    def acc(i):
        ac = js['accessors'][i]; bv = js['bufferViews'][ac['bufferView']]
        dt = np.dtype(COMP[ac['componentType']]); n = NC[ac['type']]
        st = bv.get('byteOffset', 0) + ac.get('byteOffset', 0)
        stride = bv.get('byteStride', 0) or dt.itemsize * n
        assert stride == dt.itemsize * n, 'interleaved accessor not supported'
        return np.frombuffer(bins, dtype=dt, count=ac['count'] * n, offset=st).reshape(ac['count'], n).astype(np.float64)

    def lm(nd):
        if 'matrix' in nd:
            return np.array(nd['matrix'], dtype=np.float64).reshape(4, 4).T
        x, y, z, w = nd.get('rotation', [0, 0, 0, 1])
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m = np.eye(4); m[:3, :3] = R @ np.diag(nd.get('scale', [1, 1, 1])); m[:3, 3] = nd.get('translation', [0, 0, 0])
        return m
    N = np.array(node_matrix_cm, dtype=np.float64).reshape(4, 4).T
    out = []

    def walk(i, M):
        nd = js['nodes'][i]; W = M @ lm(nd)
        if 'mesh' in nd:
            for pr in js['meshes'][nd['mesh']]['primitives']:
                if pr.get('mode', 4) != 4:
                    continue
                P = acc(pr['attributes']['POSITION'])
                I = acc(pr['indices']).astype(np.int64).reshape(-1) if 'indices' in pr else np.arange(len(P))
                Pw = (np.c_[P, np.ones(len(P))] @ W.T)[:, :3]
                out.append(Pw[I.reshape(-1, 3)])
        for c in nd.get('children', []):
            walk(c, W)
    for r in js['scenes'][js.get('scene', 0)]['nodes']:
        walk(r, N)
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def tri_zone(T, zp, feat):
    """三角形(east,north)平面足迹与约束区相交的数目。圆形标记用解析判定，其余用多边形判定。"""
    import numpy as np
    if T is None or len(T) == 0:
        return {"triangles": 0}
    E = T[:, :, 0]; Nn = -T[:, :, 2]; Y = T[:, :, 1]
    zx = [p[0] for p in zp]; zy = [p[1] for p in zp]
    pre = (E.max(1) >= min(zx)) & (E.min(1) <= max(zx)) & (Nn.max(1) >= min(zy)) & (Nn.min(1) <= max(zy))
    hit = []
    for i in np.nonzero(pre)[0]:
        pts = list(zip(E[i].tolist(), Nn[i].tolist()))
        if 'radius_m' in feat:
            c = tuple(feat['point_en']); r = feat['radius_m']
            if pip(c, pts) or min(seg_dist(c, pts[k], pts[(k + 1) % 3]) for k in range(3)) <= r:
                hit.append(i)
        elif poly_inter(pts, zp):
            hit.append(i)
    if not hit:
        return {"triangles": 0}
    h = np.array(hit)
    area = float(np.sum(0.5 * np.abs((E[h, 1] - E[h, 0]) * (Nn[h, 2] - Nn[h, 0]) - (E[h, 2] - E[h, 0]) * (Nn[h, 1] - Nn[h, 0]))))
    return {"triangles": int(len(h)), "hitTrianglesFootprintArea_m2": round(area, 1),
            "hitBounds_en": [[round(float(E[h].min()), 2), round(float(Nn[h].min()), 2)], [round(float(E[h].max()), 2), round(float(Nn[h].max()), 2)]],
            "hitY_range": [round(float(Y[h].min()), 3), round(float(Y[h].max()), 3)]}


def r3(v):
    return round(v, 3)


def to_gltf(poly):
    return [[r3(e), 0.0, r3(-n)] for e, n in poly]


# ------------------------------------------------------------------ 保守准入候选
def gate(it, *, verified_installations=()):
    """默认关闭安装；只接受独立可信验核方提供的完整条目白名单。

    verified_installations 是接口占位，不是本函数生成的史证：调用方必须先独立
    核定精确条目的东汉分期及考古控制点到世界坐标的映射，再传入原样字典 tuple。
    当前 main 不传此参数，真实已核条目数为零；测试中的白名单全部是合成例。
    候选条目内不得自带 verified/证据/坐标扩展字段冒充验核。现有条目协议没有
    世界坐标字段，因此任何新增坐标字段也拒绝，不能将本函数当几何验核器。
    本函数通过只代表消费了可信调用方的验核结果，不代表 G 冻结或城市安装许可。
    """
    keys = {'id', 'site', 'item', 'phase', 'position', 'request'}
    sites = {s['id'] for s in SD.SITES}

    def valid_shape(value):
        return (type(value) is dict and set(value) == keys
                and all(type(value[k]) is str and value[k].strip() for k in keys)
                and value['site'] in sites)

    if not valid_shape(it):
        return {"admitted": False, "reasons": ['条目字段缺失、未知、类型错误或地点未知'], "renderPoint": False}
    request = it['request']
    if request not in ('install180', 'marker'):
        return {"admitted": False, "reasons": ['未知请求类型：' + request], "renderPoint": False}
    if request == 'install180':
        reasons = []
        if it['phase'] != 'EH':
            reasons.append('安装分期不在精确 EH 白名单：' + it['phase'])
        if it['position'] != 'A-surveyed-with-control-points':
            reasons.append('无考古控制点：位置等级=' + it['position'])
        trusted = (type(verified_installations) is tuple
                   and all(valid_shape(v) and v['phase'] == 'EH'
                           and v['position'] == 'A-surveyed-with-control-points'
                           and v['request'] == 'install180'
                           for v in verified_installations))
        if not trusted or not any(it == v for v in verified_installations):
            reasons.append('缺少与完整条目匹配的独立分期及世界坐标验核记录')
        return {"admitted": not reasons, "reasons": reasons, "renderPoint": False}
    # 只保留原 P16–P21 的完整条目及三种组合，绝不转成 install180。
    marker_pairs = {('EH-figure', 'B'), ('EH', 'text-band'),
                    ('EH+Jin', 'text-band-exclusive')}
    marker_ids = {'P16', 'P17', 'P18', 'P19', 'P20', 'P21'}
    admitted = ((it['phase'], it['position']) in marker_pairs
                and any(it == v for v in SD.GATE_ITEMS
                        if v['id'] in marker_ids and v['request'] == 'marker'))
    return {"admitted": admitted,
            "reasons": [] if admitted else ['不是已支持的研究标记分期/位置组合'],
            "renderPoint": admitted and it['position'] == 'B'}


# ------------------------------------------------------------------ 主程序
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lab', required=True)
    ap.add_argument('--commit', default='bce3211')
    ap.add_argument('--ly001', required=True)
    ap.add_argument('--ly002', required=True)
    ap.add_argument('--ly005', required=True)
    ap.add_argument('--external')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)
    checks = []
    repo = Repo(a.lab, a.commit)
    checks.append(check('baseline-commit', repo.full.startswith('bce3211f818ee5a8bef1773539da70695ba37b17'), repo.full))

    # ---------------- 仓库输入
    EG = 'docs/cities/luoyang/data/evidence/evidence-geometry.json'
    eg = repo.json(EG)
    checks.append(check('evidence-geometry-commit-sha', repo.files[EG]['commitBytesSha256'].startswith('fa8b7002'), repo.files[EG]['commitBytesSha256']))
    ru = repo.json('docs/cities/luoyang/data/research-unplaced.json')
    card = repo.json('docs/cities/luoyang/p-luoyang.asset.json')
    citydata = repo.show('docs/cities/luoyang/city-data.mjs').decode('utf-8')
    asset_cards = {}
    for aid in ['m-luoyang-lingtai', 'm-luoyang-mingtang', 'm-luoyang-biyong', 'm-luoyang-taixue-a',
                'm-luoyang-stoneclassic-access-court', 'm-luoyang-southern-altar', 'm-luoyang-northern-altar']:
        asset_cards[aid] = repo.json(f'docs/library/models/{aid}/{aid}.asset.json')
    for p in ['docs/cities/luoyang/progress-assets/source.json', 'docs/cities/luoyang/progress-assets/taixue-A-v3.2/source.json',
              'docs/model-library/lingtai/metadata.json', 'docs/model-library/taixue/metadata.json']:
        repo.show(p)
    feats = {f['id']: f for f in eg['features']}

    # 现状核对：礼制件全部未入城
    rm_ritual = re.findall(r'"id": "(research-(?:lingtai|taixue-A|taixue-B))"[\s\S]{0,200}?"cityPlacement": (null|\{)', citydata)
    checks.append(check('city-ritual-research-models-unplaced', len(rm_ritual) == 3 and all(v == 'null' for _, v in rm_ritual), rm_ritual))
    ritual_south = [f for f in ru['features'] if f['id'] == 'ritual_south']
    north_in_ru = [f for f in ru['features'] if re.search('北郊|north_?suburb|northern', json.dumps(f, ensure_ascii=False))]
    eg_jiao = [f['id'] for f in eg['features'] if re.search('南郊|北郊|altar|jiao', json.dumps(f, ensure_ascii=False))]
    card_bj = [p for p in card.get('progress', []) if isinstance(p, dict) and p.get('title') == '北郊方坛四陛'] if isinstance(card.get('progress'), list) else []
    if not card_bj:
        s = json.dumps(card, ensure_ascii=False)
        m = re.search(r'\{[^{}]*"title": "北郊方坛四陛"[^{}]*\}', s)
        card_bj = [json.loads(m.group())] if m else []
    repo_state = {
        "researchModelsRitual": rm_ritual,
        "researchUnplaced_ritual_south_name": ritual_south[0]['name'] if ritual_south else None,
        "researchUnplaced_north_entries": len(north_in_ru),
        "evidenceGeometry_jiao_features": eg_jiao,
        "projectCard_beijiao_chapter": card_bj[0].get('chapter') if card_bj else None,
        "assetCardStatus": {k: v.get('statusNote') for k, v in asset_cards.items()},
    }
    checks.append(check('R-01 研究层把四所称为南郊礼制区（照实记录）', repo_state['researchUnplaced_ritual_south_name'] == '南郊礼制区', repo_state['researchUnplaced_ritual_south_name']))
    checks.append(check('R-02 研究层无北郊条目（照实记录）', repo_state['researchUnplaced_north_entries'] == 0, None))
    checks.append(check('R-03 证据层无南北郊条目（照实记录）', eg_jiao == [], eg_jiao))
    checks.append(check('R-04 项目卡北郊方坛记在ritual章（照实记录）', repo_state['projectCard_beijiao_chapter'] == 'ritual', repo_state['projectCard_beijiao_chapter']))
    checks.append(check('asset-cards-all-not-in-city', all(('未入城' in (v or '')) for v in repo_state['assetCardStatus'].values()), repo_state['assetCardStatus']))

    # ---------------- 前置席位
    pre = {}
    for base, rels in [(a.ly001, ['status.json', 'qa/family-ledger.json']),
                       (a.ly002, ['status.json', 'tables/evidence-ledger.json', 'tables/family-binding.json']),
                       (a.ly005, ['status.json', 'coordinate-contract.json', 'qa/frames-bce3211.json'])]:
        for r in rels:
            p = os.path.join(base, r)
            pre[os.path.basename(os.path.normpath(base)) + '/' + r] = fsha(p)
    ly002 = json.load(open(os.path.join(a.ly002, 'tables/evidence-ledger.json'), encoding='utf-8'))
    ly002_ids = {f['id'] for f in ly002['facts']}
    for s in SD.SITES:
        checks.append(check(f'ly002-binding-{s["id"]}', all(e in ly002_ids for e in s['ly002']), s['ly002']))
    fam = json.load(open(os.path.join(a.ly001, 'qa/family-ledger.json'), encoding='utf-8'))
    famnames = {f['family'] for f in fam['families']}
    for fn in ['F-lingtai', 'F-taixue-hall', 'C:m-luoyang-biyong', 'C:m-luoyang-mingtang', 'C:m-luoyang-southern-altar',
               'C:m-luoyang-northern-altar', 'C:m-luoyang-stoneclassic-access-court']:
        checks.append(check(f'ly001-family-{fn}', fn in famnames, None))
    ritual_fams = {f['family']: f['cityNodes'] for f in fam['families'] if f['family'] in
                   ['F-lingtai', 'F-taixue-hall', 'C:m-luoyang-biyong', 'C:m-luoyang-mingtang', 'C:m-luoyang-southern-altar', 'C:m-luoyang-northern-altar', 'C:m-luoyang-stoneclassic-access-court']}
    checks.append(check('ly001-ritual-families-zero-city-nodes', all(v == 0 for v in ritual_fams.values()), ritual_fams))

    # ---------------- 引文核对
    texts, src_meta = {}, {}
    for sid, s in SD.SOURCES.items():
        p = resolve(s['file'], a)
        if p is None or not os.path.exists(p):
            src_meta[sid] = {"path": s['file'], "available": False}
            continue
        b = open(p, 'rb').read()
        src_meta[sid] = {"path": s['file'], "available": True, "sha256": sha(b), "bytes": len(b)}
        if sid == 'G23F1':
            continue
        if s['file'].endswith('.html'):
            texts[sid] = flat_html(b, s['enc'])
        else:
            texts[sid] = flat_plain(b, s['enc'])
    if 'G23' in src_meta and src_meta['G23'].get('available'):
        pdfp = os.path.join(a.external, 'gao2023.pdf')
        src_meta['G23']['originalPdfSha256'] = fsha(pdfp) if os.path.exists(pdfp) else None
        checks.append(check('G23-pdf-sha', src_meta['G23']['originalPdfSha256'] == SD.SOURCES['G23']['externalSha256'], src_meta['G23']['originalPdfSha256']))
    qres = []
    for q in SD.QUOTES:
        t = texts.get(q['src'])
        if t is None:
            qres.append(dict(q, status='未复核（来源字节不在本机）'))
            continue
        n = t.count(q['quote'])
        one = '。' not in q['quote']
        st = '逐字找到' if n > 0 else '未找到'
        if n == 0:
            FAIL.append('quote-' + q['id'])
        qres.append(dict(q, status=st, occurrences=n, lengthChars=len(q['quote']), notLongerThanOneSentence=bool(one and len(q['quote']) <= 40)))
        if not (one and len(q['quote']) <= 40):
            FAIL.append('quote-length-' + q['id'])
    negatives_q = [("S107", "北郊在雒阳城南四里"), ("S106", "初制郊兆于雒阳城北七里"), ("S02", "明堂去平城门三里所"),
                   ("S02", "辟雍去明堂五百步"), ("SQ3", "靈臺西辟雍")]
    negq = [{"src": s, "fabricated": f, "found": (texts.get(s) or '').count(f) > 0} for s, f in negatives_q]
    checks.append(check('quote-negatives-not-found', all(not x['found'] for x in negq), negq))
    unverified_q = [q['id'] for q in qres if q['status'].startswith('未复核')]

    # ---------------- 图1 独立读数
    dig = {"source": "G23F1", "imageSha256": None, "verified": False}
    F = SD.FIG1
    if a.external and os.path.exists(os.path.join(a.external, 'gao2023.pdf')):
        import io
        import pypdf
        from PIL import Image
        import numpy as np
        r = pypdf.PdfReader(os.path.join(a.external, 'gao2023.pdf'))
        imgs = [im for im in r.pages[48].images if im.name.startswith('Im3')]
        data = imgs[0].data
        dig['imageSha256'] = sha(data)
        checks.append(check('fig1-image-sha', dig['imageSha256'] == SD.SOURCES['G23F1']['imageSha256'], dig['imageSha256']))
        arr = np.array(Image.open(io.BytesIO(data)).convert('L')) < 128
        checks.append(check('fig1-image-size', list(arr.shape[::-1]) == SD.SOURCES['G23F1']['imagePx'], list(arr.shape[::-1])))
        ev = {}

        def hfrac(row, x0, x1):
            # 线宽1–2像素且有抖动：取 row±1 三行的并集
            return float(arr[row - 1:row + 2, x0:x1 + 1].any(axis=0).mean())

        def vfrac(col, y0, y1):
            return float(arr[y0:y1 + 1, col - 1:col + 2].any(axis=1).mean())
        for bid, bx in F['boxes'].items():
            e = bx['edges']
            fr = {"top": hfrac(e['top'][0], e['top'][1], e['top'][2]), "bottom": hfrac(e['bottom'][0], e['bottom'][1], e['bottom'][2]),
                  "left": vfrac(e['left'][0], e['left'][1], e['left'][2]), "right": vfrac(e['right'][0], e['right'][1], e['right'][2])}
            ev[bid] = {k: round(v, 3) for k, v in fr.items()}
            checks.append(check(f'fig1-box-{bid}-edges-dark', min(fr.values()) >= 0.8, ev[bid]))
        sb = F['scaleBar']
        ev['scaleBar'] = {"bar": round(min(hfrac(rw, int(sb['tick0_x']), int(sb['tick500_x'])) for rw in sb['bar_rows']), 3),
                          "tick0": round(vfrac(int(sb['tick0_x']), sb['rows'][0], sb['rows'][1]), 3),
                          "tick500": round(max(vfrac(77, 564, 569), vfrac(78, 564, 569)), 3)}
        checks.append(check('fig1-scalebar-dark', min(ev['scaleBar'].values()) >= 0.6, ev['scaleBar']))
        wr = F['southWall_rows']
        ev['southWall'] = round(float(arr[wr[0]:wr[1] + 1, 200:218].mean()), 3)
        checks.append(check('fig1-southwall-dark', ev['southWall'] >= 0.9, ev['southWall']))
        for g, gv in F['gates'].items():
            light = [bool(not arr[456, c]) for c in gv['gapCols']]
            ev['gate-' + g] = light
            checks.append(check(f'fig1-gate-{g}-gap-light', all(light), light))
        for rd, rv in F['roads'].items():
            c0, c1 = min(rv['cols']), max(rv['cols'])
            fr = round(float(arr[rv['rows'][0]:rv['rows'][1] + 1, c0:c1 + 1].any(axis=1).mean()), 3)
            ev['road-' + rd] = fr
            checks.append(check(f'fig1-road-{rd}-dark', fr >= 0.95, fr))
        dig['edgeDarkFractions'] = ev
        dig['verified'] = True
    else:
        dig['note'] = '未复核：缺 --external，读数沿用 site_data.FIG1 的人工值'

    mpp_mine = F['scaleBar']['label_m'] / (F['scaleBar']['tick500_x'] - F['scaleBar']['tick0_x'])
    mpp_repo = eg['frame']['calibration']['meters_per_pixel']
    dig['metersPerPixelMine'] = mpp_mine
    dig['metersPerPixelRepo'] = mpp_repo
    dig['scaleDiffPct'] = (mpp_mine / mpp_repo - 1) * 100
    centers = {k: ((v['x'][0] + v['x'][1]) / 2, (v['y'][0] + v['y'][1]) / 2) for k, v in F['boxes'].items()}
    gpx = {'pingcheng': (F['gates']['pingcheng']['x'], F['southWall_y']), 'kaiyang': (F['gates']['kaiyang']['x'], F['southWall_y'])}
    PC = gpx['pingcheng']

    def mine_rel(px):
        return ((px[0] - PC[0]) * mpp_mine, (PC[1] - px[1]) * mpp_mine)
    pc_repo = feats['gate_pingcheng_B']['geometry']['coordinates']
    comp = {}
    offsets = []
    for k, rid in [('lingtai', 'ritual_lingtai_B'), ('mingtang', 'ritual_mingtang_B'), ('biyong', 'ritual_biyong_B'),
                   ('taixue', 'ritual_taixue_B'), ('kaiyang', 'gate_kaiyang_B'), ('pingcheng', 'gate_pingcheng_B')]:
        mp = centers.get(k) or gpx[k]
        rc = feats[rid]['geometry']['coordinates']
        rel_r = (rc[0] - pc_repo[0], rc[1] - pc_repo[1])
        rel_m = mine_rel(mp)
        rp = feats[rid]['source_pixel_geometry']['coordinates']
        offsets.append((rp[0] - mp[0], rp[1] - mp[1]))
        comp[k] = {"repoId": rid, "repoFrame_m": rc, "repoRelToPingcheng_m": [r3(v) for v in rel_r], "minePx": list(mp),
                   "mineRelToPingcheng_m": [r3(v) for v in rel_m], "residual_m": r3(math.hypot(rel_r[0] - rel_m[0], rel_r[1] - rel_m[1])),
                   "repoPx": rp, "pxOffsetRepoMinusMine": [r3(rp[0] - mp[0]), r3(rp[1] - mp[1])]}
    ox = [o[0] for o in offsets]; oy = [o[1] for o in offsets]
    dig['comparison'] = comp
    dig['pxOffsetRange'] = {"dx": [min(ox), max(ox)], "dy": [min(oy), max(oy)]}
    maxres = max(v['residual_m'] for v in comp.values())
    dig['maxResidual_m'] = maxres
    checks.append(check('fig1-independent-vs-frozen-residual<=40m', maxres <= 40, maxres))
    checks.append(check('fig1-frozen-px-is-constant-offset(<=5px spread)', (max(ox) - min(ox)) <= 5 and (max(oy) - min(oy)) <= 5, dig['pxOffsetRange']))
    boxes_m = {}
    for k, v in F['boxes'].items():
        w = (v['x'][1] - v['x'][0]) * mpp_mine; h = (v['y'][1] - v['y'][0]) * mpp_mine
        boxes_m[k] = {"symbolWidth_m": r3(w), "symbolHeight_m": r3(h), "halfDiagonal_m": r3(math.hypot(w, h) / 2)}
    dig['symbolSizes'] = boxes_m
    dig['figureCoverage'] = {"southLimitFrameNorth_m": r3((eg['frame']['origin_definition']['source_pixel'][1] - (F['frame']['bottom_y'] + sum(oy) / len(oy))) * mpp_repo),
                             "northLimitFrameNorth_m": r3((eg['frame']['origin_definition']['source_pixel'][1] - (F['frame']['top_y'] + sum(oy) / len(oy))) * mpp_repo)}
    dig['unlabeled'] = F['unlabeled']

    # ---------------- 文本距离 vs 描点
    chi = SD.UNITS['chi_m']
    li = [1800 * chi[0], 1800 * chi[1]]
    bu = [6 * chi[0], 6 * chi[1]]

    def li_iv(n, rnd=0.5):
        return {"strict": [r3(n * li[0]), r3(n * li[1])], "loose": [r3((n - rnd) * li[0]), r3((n + rnd) * li[1])]}

    def bu_iv(n, rnd=50):
        return {"strict": [r3(n * bu[0]), r3(n * bu[1])], "loose": [r3((n - rnd) * bu[0]), r3((n + rnd) * bu[1])]}

    def P(fid):
        return tuple(feats[fid]['geometry']['coordinates'])
    lt, mt, by, tx, kg, pcg = P('ritual_lingtai_B'), P('ritual_mingtang_B'), P('ritual_biyong_B'), P('ritual_taixue_B'), P('gate_kaiyang_B'), P('gate_pingcheng_B')
    d = lambda p, q: math.hypot(p[0] - q[0], p[1] - q[1])

    def within(v, iv):
        return iv[0] <= v <= iv[1]
    mt_box = F['boxes']['mingtang']
    mt_north_edge_px = mt_box['y'][0]
    near_x = min(max(PC[0], mt_box['x'][0]), mt_box['x'][1])
    d_pc_mt_edge = math.hypot(near_x - PC[0], mt_north_edge_px - PC[1]) * mpp_mine
    iv2li, iv300 = li_iv(2), bu_iv(300)
    cons = []

    def add(cid, sites, text_q, measured, iv, note, kind='distance'):
        r = {"id": cid, "sites": sites, "textQuotes": text_q, "kind": kind, "measured_m": r3(measured) if isinstance(measured, (int, float)) else measured,
             "interval_m": iv, "note": note}
        if kind == 'distance':
            r['withinStrict'] = within(measured, iv['strict'])
            r['withinLoose'] = within(measured, iv['loose'])
            r['deviationFromStrict_pct'] = [r3((measured / iv['strict'][1] - 1) * 100), r3((measured / iv['strict'][0] - 1) * 100)]
        cons.append(r)
        return r
    add('T1a', ['mingtang'], ['MT2'], d(pcg, mt), iv2li, '平城门点到明堂描点（符号中心），冻结证据层数值')
    add('T1b', ['mingtang'], ['MT2'], d_pc_mt_edge, iv2li, '平城门到图1明堂符号北缘（本席位读数）；若"去平城门二里"量到明堂外缘，与严格读法相合')
    add('T2a', ['mingtang', 'biyong'], ['BY1'], d(mt, by), iv300, '明堂描点到辟雍描点（冻结证据层）')
    add('T2b', ['mingtang', 'biyong'], ['BY1'], d(mine_rel(centers['mingtang']), mine_rel(centers['biyong'])), iv300, '同上，本席位读数')
    road = feats['road_pingcheng_south_link_B']['geometry']['coordinates']

    def road_x(y):
        (x1, y1), (x2, y2) = road
        return x1 + (y - y1) * (x2 - x1) / (y2 - y1)
    t3 = lt[0] < road_x(lt[1]) and mt[0] > road_x(mt[1])
    c3 = add('T3', ['lingtai', 'mingtang'], ['LT4'], {"lingtaiEast": lt[0], "roadEastAtLingtai": r3(road_x(lt[1])), "mingtangEast": mt[0], "roadEastAtMingtang": r3(road_x(mt[1])), "northDiff_m": r3(abs(lt[1] - mt[1]))},
             None, '灵台在平城门外大道西、明堂在东，两者南北相差很小（夹道相对）', kind='relation')
    c3['pass'] = bool(t3)
    sw = feats['south_wall_inferred_B']['geometry']['coordinates']

    def south_wall_y(x):
        (x1, y1), (x2, y2) = sw
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)
    es = feats['road_east_spine_B']['geometry']['coordinates']

    def es_x(y):
        (x1, y1), (x2, y2) = es
        return x1 + (y - y1) * (x2 - x1) / (y2 - y1)
    t4 = tx[1] < south_wall_y(tx[0]) and tx[0] > es_x(tx[1])
    c4 = add('T4', ['taixue'], ['TX1', 'TX12'], {"taixueNorth": tx[1], "southWallNorthAtTaixue": r3(south_wall_y(tx[0])), "taixueEast": tx[0], "kaiyangRoadEastAtTaixue": r3(es_x(tx[1])),
                                                 "distToKaiyangGate_m": r3(d(tx, kg))}, None, '太学在南垣外、开阳门南大道东：与"开阳门外"及北魏"开阳门御道东"相合', kind='relation')
    c4['pass'] = bool(t4)
    sp = feats['south_palace_candidate_gao2023_B']['geometry']['coordinates'][0]
    npal = feats['north_palace_extent_gao2023_B']['geometry']['coordinates'][0]

    def centroid(poly):
        pts = poly[:-1]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    iv8 = li_iv(8)
    add('T5a', ['taixue'], ['TX1'], d(tx, centroid(sp)), iv8, '太学到南宫候选包络中心：远小于八里——"去宫八里"不是以东汉南宫计')
    add('T5b', ['taixue'], ['TX1'], poly_dist([tx], [tuple(p) for p in sp[:-1]]), iv8, '太学到南宫候选包络最近边')
    add('T5c', ['taixue'], ['TX1'], d(tx, centroid(npal)), iv8, '太学到北宫旧示意范围中心：接近八里，与西晋宫城在北的格局相容（只说明该句是西晋参照，不用于定位）')
    c6 = add('T6', ['nanjiao', 'mingtang'], ['MT3', 'NJ1'], {"mingtangFromPingcheng_m": r3(d(pcg, mt)), "nanjiaoTextFromSouthWall_m": li_iv(7)['loose']}, None,
             '出平城门先历明堂乃至郊祀：南郊坛应在明堂之外；七里带（≥2.69 km）远于明堂（约1.0 km），两条记载不冲突', kind='relation')
    c6['pass'] = li_iv(7)['loose'][0] > d(pcg, mt)
    xy = feats['gate_xiaoyuan_B']['geometry']['coordinates']
    c7 = add('T7', ['mingtang', 'biyong', 'lingtai'], ['MT8', 'BY10', 'LT7'], {"mingtangIsSouthWestOfBiyong": mt[0] < by[0] and mt[1] < by[1], "biyongIsEastOfLingtai": by[0] > lt[0],
                                                                             "lingtaiFromXiaoyuanGate_m": r3(d(lt, xy))},
             None, '北魏追记（后世栏）：图1明堂正在辟雍西南，正是北魏正光明堂的相对位置；因此图1明堂点与北魏明堂可能是同一处遗址，分期必须另核', kind='relation-later')
    c7['pass'] = bool(mt[0] < by[0] and mt[1] < by[1] and by[0] > lt[0])
    for c in cons:
        if c['kind'] == 'distance':
            checks.append(check(f"text-distance-{c['id']}-within-loose" if c['id'] not in ('T5a', 'T5b') else f"text-distance-{c['id']}-outside-strict(expected)",
                                c['withinLoose'] if c['id'] not in ('T5a', 'T5b') else not c['withinLoose'], c['measured_m']))
        else:
            checks.append(check(f"relation-{c['id']}", c['pass'], None))

    # ---------------- 约束几何（luoyang-local-schematic-v01，米，(east, north)）
    wall = [tuple(p) for p in feats['city_wall_schematic_B']['geometry']['coordinates'][0][:-1]]
    north_chain = [tuple(p) for p in feats['city_wall_schematic_B']['geometry']['coordinates'][0][0:6]]
    nw_corner = north_chain[0]

    def band(chain, dmin, dmax, sign):
        lower = [(x, y + sign * dmin) for x, y in chain]
        upper = [(x, y + sign * dmax) for x, y in chain]
        return lower + upper[::-1]
    li4, li6, li7, li1 = li_iv(4), li_iv(6), li_iv(7), li_iv(1)
    NA = band(north_chain, li4['loose'][0], li4['loose'][1], +1)
    NB = band(north_chain, li6['loose'][0], li6['loose'][1], +1)
    r1, r2 = li1['loose']
    NC = [(nw_corner[0] + r1 * math.cos(math.radians(t)), nw_corner[1] + r1 * math.sin(math.radians(t))) for t in range(90, 181, 5)]
    NC += [(nw_corner[0] + r2 * math.cos(math.radians(t)), nw_corner[1] + r2 * math.sin(math.radians(t))) for t in range(180, 89, -5)]
    SA = band([tuple(sw[0]), tuple(sw[1])], li7['loose'][0], li7['loose'][1], -1)
    marker = {}
    for k, rid in [('lingtai', 'ritual_lingtai_B'), ('mingtang', 'ritual_mingtang_B'), ('biyong', 'ritual_biyong_B'), ('taixue', 'ritual_taixue_B')]:
        rad = boxes_m[k]['halfDiagonal_m'] + comp[k]['residual_m']
        marker[k] = {"center": feats[rid]['geometry']['coordinates'], "radius_m": r3(rad)}

    def feat(fid, region, layer, kind, poly, status, basis, quotes, extra=None):
        f = {"id": fid, "region": region, "layer": layer, "kind": kind, "frame": "luoyang-local-schematic-v01",
             "planNotation": "(east, north) 米；glTF x=east, z=-north（LY-005 契约）", "polygon_en": [[r3(x), r3(y)] for x, y in poly],
             "polygon_gltf_xz": [[p[0], p[2]] for p in to_gltf(poly)], "coordinateStatus": status, "basis": basis, "quotes": quotes,
             "notAHistoricalBoundary": True, "admittedTo180InstallLayer": False}
        if extra:
            f.update(extra)
        return f
    south_feats = []
    for k in ['lingtai', 'mingtang', 'biyong', 'taixue']:
        mk = marker[k]
        south_feats.append(feat(f'S-{k}-marker', 'city-south', '城南礼制四所', 'research-marker-envelope', circle(mk['center'], mk['radius_m']),
                                'B 研究示意描点（冻结证据层），只可作研究标记；无考古控制点',
                                f"圆心=冻结证据层 {SD.REPO_IDS[k]}；半径=图1符号半对角线{boxes_m[k]['halfDiagonal_m']:.1f} m＋两次独立描点差{comp[k]['residual_m']:.1f} m。示意图对实地的误差未知，不计入",
                                [q for s in SD.SITES if s['id'] == k for q in s['positionText']],
                                {"point_en": mk['center'], "radius_m": mk['radius_m']}))
    south_feats.append(feat('S-nanjiao-text-band', 'south-suburb', '南郊（与城南四所分层）', 'text-distance-band', SA,
                            '未配准：只有文本距离带，不出点；图1不覆盖此范围',
                            f"南垣推定线（south_wall_inferred_B）向南平移{li7['loose'][0]:.0f}–{li7['loose'][1]:.0f} m（6.5–7.5里×414–432 m，C）；东西只按南垣两端截取（C展示选择，文献无东西约束）",
                            ['NJ1', 'NJ3', 'MT3'], {"eastWestConstraint": None, "measuredFrom": "未知（城垣/城门/宫门），按南垣推定线（C）"}))
    north_feats = [
        feat('N-A-chengbei-4li', 'north-suburb', '北郊（单列）', 'text-distance-band-exclusive', NA, '未配准：读法A，与B、C互斥，不出点',
             f"北垣示意折线向正北平移{li4['loose'][0]:.0f}–{li4['loose'][1]:.0f} m（3.5–4.5里，C）", ['BJ1'], {"reading": "A", "textDate": "司马彪续汉志（西晋撰，记东汉制度）", "grade": "文献正文"}),
        feat('N-B-chengbei-6li', 'north-suburb', '北郊（单列）', 'text-distance-band-exclusive', NB, '未配准：读法B，与A、C互斥，不出点；晋人记，且与"迎冬北郊兆"水数六相同',
             f"北垣示意折线向正北平移{li6['loose'][0]:.0f}–{li6['loose'][1]:.0f} m（5.5–6.5里，C）", ['BJ2', 'BJ6'], {"reading": "B", "textDate": "晋（张璠）", "grade": "注引晋人记"}),
        feat('N-C-xibeijiao-1li', 'north-suburb', '北郊（单列）', 'text-distance-sector-exclusive', NC, '未配准：读法C，与A、B互斥，不出点',
             f"以城垣示意轮廓西北角({nw_corner[0]:.1f}, {nw_corner[1]:.1f})为心、半径{r1:.0f}–{r2:.0f} m（0.5–1.5里，C），方位正西至正北（C解读）", ['BJ3'],
             {"reading": "C", "textDate": "应劭《汉官仪》（东汉末，与180年最近）", "grade": "注引同期人记"}),
    ]
    geo_s = {"schema": "LY-004/constraints-geometry/1", "region": "city-south", "frame": eg['frame']['id'], "frameSourceSha256": repo.files[EG]['commitBytesSha256'],
             "note": "城南礼制四所与南郊坛分层记录；本文件不含任何北郊要素。全部要素 admittedTo180InstallLayer=false。", "features": south_feats}
    geo_n = {"schema": "LY-004/constraints-geometry/1", "region": "north-suburb", "frame": eg['frame']['id'], "frameSourceSha256": repo.files[EG]['commitBytesSha256'],
             "note": "北郊单列；三说互斥，任何一说都不出点。本文件不含任何城南要素。", "features": north_feats}

    # ---------------- 南北分离检查（含负例）
    def separation(gs, gn, wall_poly):
        errs = []
        sw_max = max(sw[0][1], sw[1][1])
        for f in gs['features']:
            if f['region'] not in ('city-south', 'south-suburb'):
                errs.append(f"{f['id']}: 南文件出现 region={f['region']}")
            if max(p[1] for p in f['polygon_en']) >= sw_max:
                errs.append(f"{f['id']}: 有顶点不在南垣以南")
        for f in gn['features']:
            if f['region'] != 'north-suburb':
                errs.append(f"{f['id']}: 北文件出现 region={f['region']}")
            if min(p[1] for p in f['polygon_en']) < nw_corner[1] - 1e-6:
                errs.append(f"{f['id']}: 有顶点在城西北角纬度以南")
            if any(pip(tuple(p), wall_poly) for p in f['polygon_en']):
                errs.append(f"{f['id']}: 有顶点落在城内")
        for fs in gs['features']:
            for fn in gn['features']:
                dd = poly_dist([tuple(p) for p in fs['polygon_en']], [tuple(p) for p in fn['polygon_en']])
                if dd < 3000:
                    errs.append(f"{fs['id']}~{fn['id']}: 南北要素相距 {dd:.0f} m <3000")
        ids_s = {f['id'] for f in gs['features']}; ids_n = {f['id'] for f in gn['features']}
        if ids_s & ids_n:
            errs.append('同一 id 同时出现在南北文件')
        return errs
    sep_errs = separation(geo_s, geo_n, wall)
    min_sn = min(poly_dist([tuple(p) for p in fs['polygon_en']], [tuple(p) for p in fn['polygon_en']]) for fs in south_feats for fn in north_feats)
    checks.append(check('south-north-separation', not sep_errs, {"errors": sep_errs, "minDistance_m": r3(min_sn)}))
    excl = {"NA~NB": r3(poly_dist(NA, NB)), "NA~NC": r3(poly_dist(NA, NC)), "NB~NC": r3(poly_dist(NB, NC))}
    checks.append(check('north-three-readings-mutually-exclusive', all(v > 0 for v in excl.values()), excl))
    # 负例1：把北郊A带镜像到城南
    import copy
    bad1 = copy.deepcopy(geo_n); bad1['features'][0]['polygon_en'] = [[x, -y] for x, y in bad1['features'][0]['polygon_en']]
    # 负例2：北郊要素混入南文件
    bad2 = copy.deepcopy(geo_s); bad2['features'].append(copy.deepcopy(north_feats[2]))
    # 负例3：南郊带改标为北郊
    bad3 = copy.deepcopy(geo_n); f3 = copy.deepcopy(south_feats[-1]); f3['region'] = 'north-suburb'; bad3['features'].append(f3)
    negs = {"mirror-north-band-to-south": separation(geo_s, bad1, wall), "north-feature-in-south-file": separation(bad2, geo_n, wall),
            "south-band-relabelled-north": separation(geo_s, bad3, wall)}
    checks.append(check('separation-negatives-all-caught', all(len(v) > 0 for v in negs.values()), {k: len(v) for k, v in negs.items()}))

    # ---------------- 180安装层准入（未接入独立验核，安装白名单保持空）
    gate_res = [dict(it, **gate(it)) for it in SD.GATE_ITEMS]
    adm180 = [g['id'] for g in gate_res if g['request'] == 'install180' and g['admitted']]
    adm_marker = [g['id'] for g in gate_res if g['request'] == 'marker' and g['admitted']]
    checks.append(check('install180-admits-nothing', adm180 == [], adm180))
    checks.append(check('markers-admitted-6', sorted(adm_marker) == ['P16', 'P17', 'P18', 'P19', 'P20', 'P21'], adm_marker))
    # 负例均记录完整输入和预期；EH+A 标签自身不是已核证据。
    base = dict(SD.GATE_ITEMS[10], position='A-surveyed-with-control-points')
    negative_inputs = [(phase, dict(base, phase=phase)) for phase in
                       ('EH', 'EH+Jin', 'EH-figure', 'NW', 'Jin', 'unknown', 'EH ', 'EHH', 'W-Jin')]
    negative_inputs += [('unknown-request', dict(base, request='install18O')),
                        ('self-verified', dict(base, verified=True)),
                        ('wrong-world-coordinate', dict(base, worldPosition=[0, 0, 1]))]
    gneg = [{"case": name, "input": value, "expected": {"admitted": False},
             "actual": gate(value)} for name, value in negative_inputs]
    checks.append(check('gate-negatives', all(n['actual']['admitted'] is False for n in gneg), gneg))
    gpos = [{"case": it['id'], "input": it, "expected": {"admitted": True},
             "actual": gate(it)} for it in SD.GATE_ITEMS if it['request'] == 'marker']
    checks.append(check('gate-positive-research-markers', all(n['actual']['admitted'] is True for n in gpos), gpos))

    # ---------------- 现有城市节点与约束区的叠合
    frames = json.load(open(os.path.join(a.ly005, 'qa/frames-bce3211.json'), encoding='utf-8'))
    zones = {f['id']: [tuple(p) for p in f['polygon_en']] for f in south_feats + north_feats}
    hits, south_of_wall, north_of_wall = [], [], []
    sw_min = min(sw[0][1], sw[1][1])
    city_nodes = [n for n in frames['nodes'] if n['space'] == 'city']
    import csv
    import numpy as np
    node_glb = {}
    with open(os.path.join(a.ly001, 'qa/city-nodes.csv'), encoding='utf-8') as fcsv:
        for row in csv.DictReader(fcsv):
            node_glb[row['nodeId']] = [p for p in (row['farPath'], row['nearPath']) if p]
    bbox_hits = []
    for n in city_nodes:
        b = n['worldBoundsComputed']
        e0, e1 = b['min'][0], b['max'][0]; n0, n1 = -b['max'][2], -b['min'][2]
        rect = [(e0, n0), (e1, n0), (e1, n1), (e0, n1)]
        for zid, zp in zones.items():
            if poly_inter(rect, zp):
                bbox_hits.append({"node": n['id'], "zone": zid})
        if n1 < sw_min:
            south_of_wall.append(n['id'])
        if n0 > max(p[1] for p in north_chain):
            north_of_wall.append(n['id'])
    # 包围盒相交的节点，逐三角形核对（GLB 取提交字节，矩阵取 LY-005 实测）
    tri_cache = {}
    for bh in bbox_hits:
        n = [x for x in city_nodes if x['id'] == bh['node']][0]
        if n['id'] not in tri_cache:
            tris, files = [], []
            for rel in node_glb.get(n['id'], []):
                gb = repo.show('docs/' + rel)
                files.append({"path": 'docs/' + rel, "sha256": sha(gb)})
                tris.append(glb_tris(gb, n['matrixColumnMajor']))
            tri_cache[n['id']] = (np.concatenate(tris) if tris else None, files)
        T3, files = tri_cache[n['id']]
        zf = [f for f in south_feats + north_feats if f['id'] == bh['zone']][0]
        res = tri_zone(T3, zones[bh['zone']], zf)
        bh['triangles'] = res['triangles']
        if res['triangles'] > 0:
            res.update({"node": bh['node'], "zone": bh['zone'], "glbFiles": files})
            hits.append(res)
    overlap = {"cityNodes": len(city_nodes), "localStudyNodes": len(frames['nodes']) - len(city_nodes), "bboxHits": bbox_hits, "hits": hits,
               "method": "先用节点世界包围盒与约束区做平面相交；相交者读GLB提交字节，按LY-005节点矩阵×GLB内节点矩阵变换，在(east,north)平面逐三角形判定与约束区相交。只判平面足迹，不是实体碰撞。",
               "nodesEntirelySouthOfSouthWall": south_of_wall, "nodesEntirelyNorthOfNorthWall": north_of_wall,
               "framesSha256": pre['LY-005/qa/frames-bce3211.json']}
    checks.append(check('city-overlap-recorded(triangle-level)', True, [{k: h[k] for k in ('node', 'zone', 'triangles')} for h in hits]))
    checks.append(check('no-city-node-in-nanjiao-or-beijiao-zones', not [h for h in hits if not h['zone'].endswith('-marker')], None))

    # ---------------- 汇总表
    qmap = {q['id']: q for q in qres}
    table = []
    for s in SD.SITES:
        own = [q for q in qres if q['id'].startswith({'lingtai': 'LT', 'mingtang': 'MT', 'biyong': 'BY', 'taixue': 'TX', 'nanjiao': 'NJ', 'beijiao': 'BJ'}[s['id']])]
        cols = {"sameLuoyang": [q for q in own if q['col'] == 'same'], "otherHan": [q for q in own if q['col'] == 'other'],
                "later": [q for q in own if q['col'] == 'later'], "unknown": s['unknown']}
        if s['region'] == 'city-south':
            mk = marker[s['id']]
            coord = {"status": "B-research-marker", "label": "B 研究示意描点（非测绘，无控制点）", "point_en": mk['center'], "markerRadius_m": mk['radius_m'],
                     "independentResidual_m": comp[s['id']]['residual_m'], "historicalPositionError_m": None,
                     "geometryFile": "geometry/city-south.json#S-" + s['id'] + "-marker"}
        elif s['id'] == 'nanjiao':
            coord = {"status": "unplaced-text-band", "label": "未配准：只有城南七里文本带，不出点", "point_en": None,
                     "band_m_south_of_south_wall": li7['loose'], "eastWest": None, "geometryFile": "geometry/city-south.json#S-nanjiao-text-band"}
        else:
            coord = {"status": "unplaced-three-exclusive-readings", "label": "未配准：三说互斥，不出点；只在城北", "point_en": None,
                     "readings": {"A": li4['loose'], "B": li6['loose'], "C_fromNWcorner": li1['loose']}, "geometryFile": "geometry/north-suburb.json"}
        adm = [g for g in gate_res if g['site'] == s['id']]
        table.append({"id": s['id'], "name": s['name'], "region": s['region'], "group": s['group'], "assets": s['assets'], "ly002Entries": s['ly002'],
                      "evidence": cols, "phase": s['phase'], "positionTextQuotes": s['positionText'], "coordinate": coord,
                      "constraintsChecked": [c['id'] for c in cons if s['id'] in c['sites']],
                      "admission180": {"install180": "不放行", "marker": "可作研究标记（B点或文本带，标明非测绘）",
                                       "items": [{k: g[k] for k in ('id', 'item', 'request', 'admitted', 'reasons')} for g in adm]}})
    checks.append(check('six-sites-each-have-own-entry', len(table) == 6 and len({t['id'] for t in table}) == 6, [t['id'] for t in table]))
    checks.append(check('each-site-has-same-period-evidence', all(len(t['evidence']['sameLuoyang']) > 0 for t in table), None))
    checks.append(check('north-suburb-has-own-region', [t['id'] for t in table if t['region'] == 'north-suburb'] == ['beijiao'], None))

    out = {
        "schema": "LY-004/site-constraints/1", "seat": "LY-004", "snapshotYearCE": SD.SNAPSHOT_YEAR, "baselineCommit": repo.full,
        "frame": eg['frame']['id'], "units": SD.UNITS, "sites": table, "constraints": cons, "repoIssues": SD.REPO_ISSUES,
        "notObtained": SD.NOT_OBTAINED, "repoState": repo_state, "altUpload": SD.ALT_UPLOAD,
        "fiveThings": {"模型能读取": "本席位不涉及", "局部通行通过": "本席位不涉及", "已入城": "六类地点的模型全部未入城（LY-001 家族 cityNodes=0；city-data 礼制研究件 cityPlacement=null）",
                       "真实结构安全": "本席位不涉及", "历史复原成立": "只给位置/分期约束：四所是B示意点，南郊与北郊未配准；没有任何一项进入约180年安装层"},
    }
    jdump(out, os.path.join(a.out, 'tables/site-constraints.json'))
    jdump(geo_s, os.path.join(a.out, 'geometry/city-south.json'))
    jdump(geo_n, os.path.join(a.out, 'geometry/north-suburb.json'))
    jdump({"quotes": qres, "negatives": negq, "unverified": unverified_q, "sources": src_meta}, os.path.join(a.out, 'qa/quote-check.json'))
    jdump(dig, os.path.join(a.out, 'qa/digitization.json'))
    jdump({"units": SD.UNITS, "constraints": cons}, os.path.join(a.out, 'qa/consistency.json'))
    jdump({"errors": sep_errs, "minSouthNorthDistance_m": r3(min_sn), "northReadingsPairwiseDistance_m": excl, "negatives": negs}, os.path.join(a.out, 'qa/separation.json'))
    jdump({"rules": {"install180": "仅精确 EH+A 位置且完整条目匹配独立分期与世界坐标验核白名单；main 保持空白名单，本轮无安装准入",
                     "marker": "仅原 P16–P21 完整条目及三种分期/位置组合可作研究标记；EH+Jin 互斥文本包络不是安装准入"}, "items": gate_res, "negatives": gneg, "positives": gpos}, os.path.join(a.out, 'qa/phase-gate.json'))
    jdump(overlap, os.path.join(a.out, 'qa/city-overlap.json'))
    write_md(out, qmap, os.path.join(a.out, 'tables/site-constraints.md'))
    draw_map(a, feats, wall, south_feats, north_feats, marker, os.path.join(a.out, 'preview/constraints-map.png'), hits, dig['figureCoverage'])
    jdump({"inputs": {"repo": repo.files, "predecessors": pre}, "sources": src_meta}, os.path.join(a.out, 'qa/inputs-hashes.json'))
    summary = {"seat": "LY-004", "baseline": repo.full, "checks": checks, "failed": FAIL, "unverified": unverified_q + ([] if dig['verified'] else ['fig1-readings']),
               "outputs": {}}
    for rel in ['tables/site-constraints.json', 'tables/site-constraints.md', 'geometry/city-south.json', 'geometry/north-suburb.json', 'qa/quote-check.json',
                'qa/digitization.json', 'qa/consistency.json', 'qa/separation.json', 'qa/phase-gate.json', 'qa/city-overlap.json', 'qa/inputs-hashes.json', 'preview/constraints-map.png']:
        summary['outputs'][rel] = fsha(os.path.join(a.out, rel))
    jdump(summary, os.path.join(a.out, 'qa/checks.json'))
    print(f"checks={len(checks)} failed={len(FAIL)} unverified={len(summary['unverified'])}")
    for c in checks:
        if not c['pass']:
            print('FAIL', c['check'], json.dumps(c['detail'], ensure_ascii=False)[:300])
    if FAIL:
        sys.exit(1)
    if summary['unverified']:
        sys.exit(2)


def write_md(out, qmap, path):
    L = []
    L.append('# LY-004｜城南礼制与北郊：位置与分期约束表\n')
    L.append(f"基线 `{out['baselineCommit']}`；坐标框架 `{out['frame']}`（示意工程米，无地理原点，x=东、z=−北）。由 `source/build.py` 生成，勿手改。\n")
    L.append('单位换算全部是 C：' + out['units']['note'] + out['units']['rounding']['note'] + '\n')
    L.append('## 总表\n')
    L.append('| 地点 | 区域 | 坐标状态 | 东汉分期（起点 / 距180年最近的在用记录） | 后世叠压风险 | 180安装层 |')
    L.append('|---|---|---|---|---|---|')
    for t in out['sites']:
        c = t['coordinate']
        L.append(f"| {t['name']} | {t['group']} | {c['label']} | {t['phase']['founded']} / {t['phase']['nearest180']} | {t['phase']['laterReuse']} | 不放行 |")
    L.append('')
    for t in out['sites']:
        L.append(f"## {t['name']}（{t['group']}）\n")
        L.append(f"相关资产：{'、'.join(t['assets'])}；LY-002 条目：{'、'.join(t['ly002Entries'])}\n")
        c = t['coordinate']
        if c['status'] == 'B-research-marker':
            L.append(f"**坐标**：{c['label']}。点 (east, north) = ({c['point_en'][0]:.1f}, {c['point_en'][1]:.1f}) m，标记半径 {c['markerRadius_m']:.0f} m（图1符号半对角线＋两次独立描点差 {c['independentResidual_m']:.0f} m）。示意图到实地的误差：未知。\n")
        elif c['status'] == 'unplaced-text-band':
            L.append(f"**坐标**：{c['label']}。南垣推定线以南 {c['band_m_south_of_south_wall'][0]:.0f}–{c['band_m_south_of_south_wall'][1]:.0f} m 的东西向带；东西位置无约束。\n")
        else:
            r = c['readings']
            L.append(f"**坐标**：{c['label']}。A 城北四里：北垣以北 {r['A'][0]:.0f}–{r['A'][1]:.0f} m；B 城北六里：{r['B'][0]:.0f}–{r['B'][1]:.0f} m；C 城西北角去城一里所：距西北角 {r['C_fromNWcorner'][0]:.0f}–{r['C_fromNWcorner'][1]:.0f} m。三者互不相交。\n")
        for colname, key in [('同期洛阳（原文/考古）', 'sameLuoyang'), ('异地汉代', 'otherHan'), ('魏晋北魏及后世', 'later')]:
            items = t['evidence'][key]
            L.append(f"**{colname}**：" + ('无' if not items else ''))
            for q in items:
                td = f"［{q['textDate']}］" if q.get('textDate') else ''
                L.append(f"- {q['id']} 「{q['quote']}」— {SD.SOURCES[q['src']]['title']}，{q['locator']}{td}。{q['supports']}。核对：{q['status']}")
            L.append('')
        L.append('**未知**：')
        for u in t['evidence']['unknown']:
            L.append(f"- {u}")
        L.append('')
        L.append(f"**分期**：始建 {t['phase']['founded']}；在用记录 {('、'.join(t['phase']['inUseBefore180'])) or '无'}；快照后 {t['phase']['afterSnapshot']}；后世 {t['phase']['laterReuse']}。\n")
        L.append('**180安装层准入**：')
        for g in t['admission180']['items']:
            L.append(f"- {g['id']} {g['item']}（{g['request']}）→ {'放行' if g['admitted'] else '不放行'}{'：' + '；'.join(g['reasons']) if g['reasons'] else ''}")
        L.append('')
    L.append('## 文本距离与描点的一致性\n')
    L.append('| 编号 | 内容 | 实测 | 严格区间 | 宽松区间 | 结论 |')
    L.append('|---|---|---|---|---|---|')
    for c in out['constraints']:
        if c['kind'] == 'distance':
            L.append(f"| {c['id']} | {c['note']} | {c['measured_m']:.0f} m | {c['interval_m']['strict'][0]:.0f}–{c['interval_m']['strict'][1]:.0f} | {c['interval_m']['loose'][0]:.0f}–{c['interval_m']['loose'][1]:.0f} | 严格{'内' if c['withinStrict'] else '外'}／宽松{'内' if c['withinLoose'] else '外'} |")
        else:
            L.append(f"| {c['id']} | {c['note']} | {json.dumps(c['measured_m'], ensure_ascii=False)} | — | — | {'相合' if c.get('pass') else '不合'} |")
    L.append('')
    L.append('## 仓库出入（只报告）\n')
    for r in out['repoIssues']:
        L.append(f"- **{r['id']}** `{r['file']}` {r['where']}：{r['found']}。{r['issue']}。建议：{r['suggest']}（交 {r['to']}）")
    L.append('')
    L.append('## 本轮没取得的资料\n')
    for n in out['notObtained']:
        L.append(f"- {n['what']}：{n['status']}")
    L.append('')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def draw_map(a, feats, wall, south_feats, north_feats, marker, path, hits=(), cover=None):
    from PIL import Image, ImageDraw, ImageFont
    E0, E1, N0, N1 = -1200, 3800, -3700, 7000
    S = 0.2
    W, H = int((E1 - E0) * S) + 360, int((N1 - N0) * S) + 40
    im = Image.new('RGB', (W, H), (250, 248, 242))
    dr = ImageDraw.Draw(im, 'RGBA')
    fp = 'C:/Windows/Fonts/msyh.ttc'
    font = ImageFont.truetype(fp, 15) if os.path.exists(fp) else ImageFont.load_default()
    small = ImageFont.truetype(fp, 12) if os.path.exists(fp) else ImageFont.load_default()

    def T(p):
        return (20 + (p[0] - E0) * S, 20 + (N1 - p[1]) * S)
    for f in north_feats:
        col = {'A': (40, 90, 200, 70), 'B': (40, 160, 200, 50), 'C': (120, 60, 200, 80)}[f['reading']]
        dr.polygon([T(p) for p in f['polygon_en']], fill=col, outline=col[:3] + (255,))
    sa = [f for f in south_feats if f['id'] == 'S-nanjiao-text-band'][0]
    dr.polygon([T(p) for p in sa['polygon_en']], fill=(210, 90, 40, 60), outline=(210, 90, 40, 255))
    dr.polygon([T(p) for p in wall], outline=(60, 50, 40), width=3)
    for fid in ['road_pingcheng_south_link_B', 'road_east_spine_B']:
        c = feats[fid]['geometry']['coordinates']
        dr.line([T(p) for p in c], fill=(120, 110, 100), width=1)
    for k, mk in marker.items():
        c = T(mk['center']); r = mk['radius_m'] * S
        dr.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(160, 30, 30, 160), width=1)
        dr.ellipse([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3], fill=(160, 30, 30))
        off = {'lingtai': (-34, 6), 'mingtang': (6, 8), 'biyong': (8, -4), 'taixue': (8, -16)}[k]
        dr.text((c[0] + off[0], c[1] + off[1]), {'lingtai': '灵台', 'mingtang': '明堂', 'biyong': '辟雍', 'taixue': '太学'}[k], fill=(160, 30, 30), font=small)
    for h in hits:
        (ea, na), (eb, nb) = h['hitBounds_en']
        dr.rectangle([T((ea, nb)), T((eb, na))], outline=(90, 90, 90), fill=(90, 90, 90, 90))
    if hits:
        (ea, na), (eb, nb) = hits[0]['hitBounds_en']
        dr.text((T((eb, na))[0] - 150, T((eb, na))[1] + 4), '现有C地面带（地形章，平城门外）', fill=(70, 70, 70), font=small)
    if cover:
        for key, txt in (('southLimitFrameNorth_m', '图1南缘（以南图上无内容）'), ('northLimitFrameNorth_m', '图1北缘（以北图上无内容）')):
            yy = T((0, cover[key]))[1]
            for xx in range(20, W - 360, 12):
                dr.line([(xx, yy), (xx + 6, yy)], fill=(120, 120, 120), width=1)
            dr.text((22, yy + 2), txt, fill=(110, 110, 110), font=small)
    for g in ['gate_pingcheng_B', 'gate_kaiyang_B', 'gate_xia_B', 'gate_gu_B']:
        c = T(feats[g]['geometry']['coordinates']); dr.rectangle([c[0] - 3, c[1] - 3, c[0] + 3, c[1] + 3], fill=(60, 50, 40))
        dr.text((c[0] + 5, c[1] + 2), feats[g]['name'], fill=(60, 50, 40), font=small)
    lab = {'N-A-chengbei-4li': '北郊读法A：城北四里（不出点）', 'N-B-chengbei-6li': '北郊读法B：城北六里（晋人记，不出点）', 'N-C-xibeijiao-1li': '北郊读法C：西北角去城一里所'}
    for f in north_feats:
        xs = [T(p) for p in f['polygon_en']]
        x = max(p[0] for p in xs) + 4 if f['reading'] != 'C' else min(p[0] for p in xs) - 4
        y = sum(p[1] for p in xs) / len(xs)
        dr.text((x if f['reading'] != 'C' else 20, y - 8 if f['reading'] != 'C' else min(p[1] for p in xs) - 20), lab[f['id']], fill=(30, 60, 150), font=small)
    xs = [T(p) for p in sa['polygon_en']]
    dr.text((max(p[0] for p in xs) + 4, sum(p[1] for p in xs) / len(xs) - 8), '南郊：城南七里文本带（不出点，东西无约束）', fill=(170, 70, 30), font=small)
    y0 = T((0, 0))[1]
    dr.line([(20, y0), (W - 340, y0)], fill=(0, 0, 0, 60), width=1)
    dr.text((W - 330, 30), 'LY-004 位置约束图（CPU绘制，示意工程米）', fill=(0, 0, 0), font=font)
    lines = ['红圈：城南四所B研究标记（非院界）', '橙带：南郊文本距离带', '蓝/青/紫：北郊三说（互斥，单列）', '黑框：城垣示意轮廓（B）', '灰带：现有C地面与红圈相交部分', '虚线：高2023图1覆盖范围',
             '框架：luoyang-local-schematic-v01', '北向上；无地理原点、无真北校正', '没有任何要素进入180安装层']
    for i, t in enumerate(lines):
        dr.text((W - 330, 60 + 20 * i), t, fill=(40, 40, 40), font=small)
    sb = T((E0 + 200, N0 + 200)); dr.line([sb, (sb[0] + 1000 * S, sb[1])], fill=(0, 0, 0), width=3)
    dr.text((sb[0], sb[1] + 4), '1000 m', fill=(0, 0, 0), font=small)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)


if __name__ == '__main__':
    main()
