# -*- coding: utf-8 -*-
"""LY-007 三档差异量化：每档的三角数、按材质的连通块数（= 构件数近似）、包围盒、正/侧/顶三向轮廓与 LOD0 的 IoU，
以及「LOD0 复制改名」负例判据（字节、几何、贴图分辨率三项都与 LOD0 相同即判为复制）。
用法: python -I lod_diff.py <输出 json> <组名>=<目录>:<文件模板含{lod}> ...
例:   python -I lod_diff.py qa/lod-diff.json S84=models/samples:S84-LOD{lod}.glb G10=models/samples:G10-LOD{lod}.glb
轮廓：glTF 坐标正交投影，2 cm 栅格，三角形逐个光栅化（CPU，numpy），front = XY（看 -Z 方向），side = ZY，top = XZ。
"""
import sys, os, json, struct, hashlib, collections
import numpy as np

OUT = sys.argv[1]
GROUPS = [a.split('=', 1) for a in sys.argv[2:]]
CELL = 0.02
CT = {5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}


def read(p):
    b = open(p, 'rb').read(); jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl]); o = 20 + jl; bl = struct.unpack('<I', b[o:o + 4])[0]
    return b, j, b[o + 8:o + 8 + bl]


def acc(j, bn, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    return np.frombuffer(bn, CT[a['componentType']], count=a['count'] * NC[a['type']],
                         offset=bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], -1).astype(np.float64)


def components(P, I):
    """按位置焊接（1e-5 m）后求连通块数。"""
    key = np.round(P / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    par = list(range(inv.max() + 1))

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in I:
        a, b, c = f(inv[t[0]]), f(inv[t[1]]), f(inv[t[2]])
        par[b] = a; par[f(c)] = a
    return len({f(inv[i]) for i in np.unique(I)})


def raster(T, ax, lo, shape):
    """T: (n,3,3) 三角；ax: 投影的两个轴；返回布尔栅格。"""
    img = np.zeros(shape, bool)
    Q = (T[:, :, ax] - lo[ax]) / CELL
    for q in Q:
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, shape[0] - 1), min(y1, shape[1] - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5, indexing='ij')
        (ax_, ay), (bx, by), (cx, cy) = q
        d = (by - cy) * (ax_ - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12:
            continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
        l2 = ((cy - ay) * (xs - cx) + (ax_ - cx) * (ys - cy)) / d
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
        img[x0:x1 + 1, y0:y1 + 1] |= m
    return img


def load(path):
    b, j, bn = read(path)
    per = collections.OrderedDict(); allT = []; geoh = hashlib.sha256()
    for nd in j['nodes']:
        if 'mesh' not in nd:
            continue
        pr = j['meshes'][nd['mesh']]['primitives'][0]
        P = acc(j, bn, pr['attributes']['POSITION']); I = acc(j, bn, pr['indices']).reshape(-1, 3).astype(np.int64)
        T = P[I]; allT.append(T)
        geoh.update(np.round(T, 5).tobytes())
        mat = j['materials'][pr['material']]['name']
        per[nd['name']] = dict(material=mat, triangles=int(len(I)), parts=components(P, I),
                               bbox_min=[round(float(x), 4) for x in P.min(0)], bbox_max=[round(float(x), 4) for x in P.max(0)])
    T = np.concatenate(allT)
    px = sorted({struct.unpack('>I', bn[j['bufferViews'][im['bufferView']].get('byteOffset', 0) + 16:
                                     j['bufferViews'][im['bufferView']].get('byteOffset', 0) + 20])[0] for im in j.get('images', [])})
    return dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b), triangles=int(len(T)), nodes=per,
                bbox_min=[round(float(x), 4) for x in T.reshape(-1, 3).min(0)], bbox_max=[round(float(x), 4) for x in T.reshape(-1, 3).max(0)],
                geometry_hash=geoh.hexdigest(), texture_px=px, materials=[m['name'] for m in j['materials']]), T


res = {}
for name, spec in GROUPS:
    d, tmpl = spec.split(':', 1)
    tiers = {}; tris = {}
    for lod in (0, 1, 2):
        p = os.path.join(d, tmpl.format(lod=lod))
        info, T = load(p)
        info['file'] = p.replace('\\', '/')
        tiers[lod] = info; tris[lod] = T
    allp = np.concatenate([tris[k].reshape(-1, 3) for k in tris])
    lo = allp.min(0) - CELL; hi = allp.max(0) + CELL
    views = {'front_XY': (0, 1), 'side_ZY': (2, 1), 'top_XZ': (0, 2)}
    sil = {}
    for v, ax in views.items():
        shape = tuple(int(np.ceil((hi[a] - lo[a]) / CELL)) + 1 for a in ax)
        imgs = {k: raster(tris[k], list(ax), lo, shape) for k in tris}
        sil[v] = {}
        for k in (1, 2):
            inter = (imgs[0] & imgs[k]).sum(); uni = (imgs[0] | imgs[k]).sum()
            sil[v][f'LOD{k}_vs_LOD0'] = dict(iou=round(float(inter / uni), 4), lod0_px=int(imgs[0].sum()), lodk_px=int(imgs[k].sum()),
                                             only_in_lod0_px=int((imgs[0] & ~imgs[k]).sum()), only_in_lodk_px=int((imgs[k] & ~imgs[0]).sum()))
    copy_check = {}
    for k in (1, 2):
        same_bytes = tiers[k]['sha256'] == tiers[0]['sha256']
        same_geo = tiers[k]['geometry_hash'] == tiers[0]['geometry_hash']
        same_px = tiers[k]['texture_px'] == tiers[0]['texture_px']
        same_mat = tiers[k]['materials'] == tiers[0]['materials']
        copy_check[f'LOD{k}'] = dict(same_bytes=same_bytes, same_geometry=same_geo, same_texture_px=same_px, same_material_names=same_mat,
                                     is_lod0_copy=bool(same_bytes or (same_geo and same_px and same_mat)))
    bb = {k: (np.array(tiers[k]['bbox_max']) - np.array(tiers[k]['bbox_min'])) for k in tiers}
    res[name] = dict(tiers=tiers, ratio={f'LOD{k}': round(tiers[k]['triangles'] / tiers[0]['triangles'], 3) for k in tiers},
                     bbox_size_delta_vs_lod0_m={f'LOD{k}': [round(float(x), 4) for x in bb[k] - bb[0]] for k in (1, 2)},
                     silhouette=sil, copy_check=copy_check, raster_cell_m=CELL)
    print(name, res[name]['ratio'], {v: {kk: vv['iou'] for kk, vv in s.items()} for v, s in sil.items()}, copy_check)
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
