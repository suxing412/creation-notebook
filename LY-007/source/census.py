# -*- coding: utf-8 -*-
"""LY-007 现状普查：commit 中全部洛阳 GLB 对照冻结基线（只读；读提交 blob，经 git cat-file --batch，不读检出字节）。

用法: python -I census.py <LY-007 目录> <lab 仓库> <commit>
输出: qa/census-<commit7>.csv、qa/census-<commit7>.json（逐文件 + 汇总）

逐文件量：字节、SHA256、generator、档位（文件名推断）、材质名、是否合 `LY_P01_<m>__(PBR|FLAT)`、后缀与档位是否对应、
FLAT 因子是否逐位等于基线、贴图字节是否属于共享库（新库 / 旧灰 / 不在库）、贴图分辨率、扩展、三角数、
平直法线比例、世界盒式 UV 吻合率（1 m / 2 m / 0.8 m 三种尺度取最好，45° 并列面不计）、最低点 y。
这是对照「冻结基线」的现状记录，不是改图依据：不全库换色，旧卡的例外照旧保留。
"""
import sys, os, json, struct, hashlib, subprocess, re, csv, collections
import numpy as np

W, LAB, COMMIT = sys.argv[1], sys.argv[2], sys.argv[3]
SEM = json.load(open(os.path.join(W, 'baseline', 'LY_P01-material-semantics.json'), encoding='utf-8'))
FLAT = {m['material']: m['flat']['baseColorFactor_linear'] for m in SEM['materials']}
man = json.load(open(os.path.join(W, 'textures', 'manifest.json'), encoding='utf-8'))
LIB = {m['sha256']: ('legacy_grey' if 'legacy' in m['file'] else 'LY_P01', m['file']) for m in man}
NAME_RE = re.compile(r'LY_P01_[a-z_]+__(PBR|FLAT)')
f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

ls = subprocess.run(['git', '-C', LAB, 'ls-tree', '-r', COMMIT], capture_output=True, text=True, check=True).stdout.splitlines()
items = []
for line in ls:
    meta, path = line.split('\t', 1)
    _, typ, oid = meta.split()
    if path.endswith('.glb') and 'luoyang' in path:
        items.append((path, oid))

proc = subprocess.Popen(['git', '-C', LAB, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def blob(oid):
    proc.stdin.write((oid + '\n').encode()); proc.stdin.flush()
    hdr = proc.stdout.readline().split()
    n = int(hdr[2]); data = proc.stdout.read(n); proc.stdout.read(1)
    return data


def tier(path):
    n = os.path.basename(path)
    m = re.search(r'LOD(\d)', n)
    if m:
        return 'LOD' + m.group(1)
    for k, v in (('near', 'near'), ('middle', 'mid'), ('-mid', 'mid'), ('far', 'far')):
        if k in n:
            return v
    return 'single'


def acc(j, bn, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    n = NC[a['type']]
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bn, CT[a['componentType']], count=a['count'] * n, offset=o).reshape(a['count'], n).astype(np.float64)


def node_mats(j):
    """世界矩阵（含父子层级）。"""
    N = j.get('nodes', [])
    parent = {}
    for i, nd in enumerate(N):
        for c in nd.get('children', []):
            parent[c] = i

    def local(nd):
        if 'matrix' in nd:
            return np.array(nd['matrix']).reshape(4, 4).T
        M = np.eye(4)
        s = nd.get('scale', [1, 1, 1]); x, y, z, w = nd.get('rotation', [0, 0, 0, 1])
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        M[:3, :3] = R * np.array(s)[None, :]
        M[:3, 3] = nd.get('translation', [0, 0, 0])
        return M
    out = {}
    for i in range(len(N)):
        M = local(N[i]); k = i
        while k in parent:
            k = parent[k]; M = local(N[k]) @ M
        out[i] = M
    return out


rows = []
for path, oid in items:
    b = blob(oid)
    r = dict(path=path, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), tier=tier(path))
    try:
        jl = struct.unpack('<I', b[12:16])[0]
        j = json.loads(b[20:20 + jl]); o = 20 + jl
        bl = struct.unpack('<I', b[o:o + 4])[0]; bn = b[o + 8:o + 8 + bl]
    except Exception as e:
        r['error'] = f'unreadable: {e}'; rows.append(r); continue
    r['generator'] = j.get('asset', {}).get('generator')
    r['extensions'] = sorted(set(j.get('extensionsUsed', [])))
    mats = [m.get('name') or '' for m in j.get('materials', [])]
    r['materials'] = mats
    r['names_ok'] = all(NAME_RE.fullmatch(m) for m in mats) if mats else None
    sfx = {m.rsplit('__', 1)[-1] if '__' in m else '' for m in mats}
    r['suffixes'] = sorted(sfx)
    want = {'LOD0': 'PBR', 'LOD1': 'PBR', 'LOD2': 'FLAT'}.get(r['tier'])
    r['suffix_matches_tier'] = (sfx == {want}) if want and mats else None
    flat_bad = []
    for m in j.get('materials', []):
        nm = m.get('name') or ''
        if nm.endswith('__FLAT'):
            base = nm[len('LY_P01_'):-len('__FLAT')] if nm.startswith('LY_P01_') else None
            got = m.get('pbrMetallicRoughness', {}).get('baseColorFactor', [None] * 3)[:3]
            if base in FLAT and got != [f32(x) for x in FLAT[base]]:
                flat_bad.append(nm)
    r['flat_factor_mismatch'] = flat_bad
    tex = collections.Counter(); res = set(); unknown = []
    for im in j.get('images', []):
        if 'bufferView' not in im:
            unknown.append((im.get('name'), 'uri')); continue
        bv = j['bufferViews'][im['bufferView']]
        d = bn[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
        h = hashlib.sha256(d).hexdigest()
        if d[:4] == b'\x89PNG':
            res.add(struct.unpack('>I', d[16:20])[0])
        cls = LIB.get(h, ('not_in_library', None))[0]
        tex[cls] += 1
        if cls == 'not_in_library':
            unknown.append((im.get('name'), h[:12]))
    r['textures'] = dict(tex); r['texture_px'] = sorted(res); r['textures_not_in_library'] = unknown
    tris = 0; flat_n = []; uvm = {1.0: [], 0.5: [], 1.25: []}; uvd = {1.0: [], 0.5: [], 1.25: []}; ymin = 1e9; has_uv = True
    if 'EXT_meshopt_compression' in r['extensions'] or 'KHR_draco_mesh_compression' in r['extensions']:
        r['geometry'] = 'compressed: not decoded'
    else:
        try:
            MW = node_mats(j)
            for ni, nd in enumerate(j.get('nodes', [])):
                if 'mesh' not in nd:
                    continue
                M = MW[ni]
                for pr in j['meshes'][nd['mesh']]['primitives']:
                    if pr.get('mode', 4) != 4:
                        continue
                    P = acc(j, bn, pr['attributes']['POSITION'])
                    I = acc(j, bn, pr['indices']).reshape(-1, 3).astype(np.int64) if 'indices' in pr else np.arange(len(P)).reshape(-1, 3)
                    wp = (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
                    ymin = min(ymin, float(wp[:, 1].min()))
                    T = wp[I]; tris += len(I)
                    fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = np.linalg.norm(fn, axis=1)
                    good = ar > 1e-10
                    fnu = fn / np.maximum(ar[:, None], 1e-12)
                    if 'NORMAL' in pr['attributes']:
                        Nn = acc(j, bn, pr['attributes']['NORMAL']) @ M[:3, :3].T
                        Nn /= np.maximum(np.linalg.norm(Nn, axis=1)[:, None], 1e-12)
                        flat_n.append((np.einsum('tij,tj->ti', Nn[I], fnu)[good] > 0.9999).all(1).astype(float))
                    if 'TEXCOORD_0' not in pr['attributes']:
                        has_uv = False; continue
                    U = acc(j, bn, pr['attributes']['TEXCOORD_0'])[I]
                    xb, yb, zb = T[..., 0], -T[..., 2], T[..., 1]
                    nb = np.stack([fnu[:, 0], -fnu[:, 2], fnu[:, 1]], 1); ax = np.abs(nb)
                    ch = np.where((ax[:, 2] >= ax[:, 0]) & (ax[:, 2] >= ax[:, 1]), 2, np.where(ax[:, 1] > ax[:, 0], 1, 0))
                    mx = ax.max(1); tie = (ax >= mx[:, None] - 1e-4).sum(1) >= 2
                    keep = good & ~tie
                    au, av = U[..., 0], 1.0 - U[..., 1]
                    for s in uvm:
                        cand = {2: (xb / s, yb / s), 1: (xb / s, zb / s), 0: (yb / s, zb / s)}
                        mt = {d: ((np.abs(au - pu) < 2e-3) & (np.abs(av - pv) < 2e-3)).all(1) for d, (pu, pv) in cand.items()}
                        okf = np.select([ch == 2, ch == 1, ch == 0], [mt[2], mt[1], mt[0]])
                        uvm[s].append(okf[keep].astype(float))
                        # 平移无关：只比较三角形内 UV 差与投影坐标差（UV 整体偏移不影响 REPEAT 贴图的尺度与方向）
                        md = {d: ((np.abs((au - au[:, :1]) - (pu - pu[:, :1])) < 2e-3) & (np.abs((av - av[:, :1]) - (pv - pv[:, :1])) < 2e-3)).all(1)
                              for d, (pu, pv) in cand.items()}
                        okd = np.select([ch == 2, ch == 1, ch == 0], [md[2], md[1], md[0]])
                        uvd[s].append(okd[keep].astype(float))
            r['triangles'] = int(tris)
            r['ymin'] = round(ymin, 4) if tris else None
            r['flat_normals'] = round(float(np.concatenate(flat_n).mean()), 4) if flat_n else None
            best = {s: (float(np.concatenate(v).mean()) if v and sum(len(x) for x in v) else None) for s, v in uvm.items()}
            r['uv_world_box_1m'] = round(best[1.0], 4) if best[1.0] is not None else None
            sc = max(((v, s) for s, v in best.items() if v is not None), default=(None, None))
            r['uv_best_scale_m'] = {1.0: 1.0, 0.5: 2.0, 1.25: 0.8}.get(sc[1]) if sc[0] and sc[0] > 0.5 else None
            r['uv_best_match'] = round(sc[0], 4) if sc[0] is not None else None
            r['has_uv'] = has_uv
            bd = {s: (float(np.concatenate(v).mean()) if v and sum(len(x) for x in v) else None) for s, v in uvd.items()}
            r['uv_box_offset_invariant'] = {({1.0: '1m', 0.5: '2m', 1.25: '0.8m'})[s]: (round(v, 4) if v is not None else None) for s, v in bd.items()}
        except Exception as e:
            r['geometry'] = f'error: {e}'
    rows.append(r)
proc.stdin.close(); proc.wait()


def compliant(r):
    """对照冻结基线（新件判据）。旧卡不符不等于要改，只是现状。"""
    why = []
    if r.get('error'):
        return False, ['unreadable']
    if r['extensions']:
        why.append('extensions:' + ','.join(r['extensions']))
    if r.get('names_ok') is False:
        why.append('material_names')
    if r.get('suffix_matches_tier') is False:
        why.append('suffix_vs_tier')
    if r.get('flat_factor_mismatch'):
        why.append('flat_factor')
    if r['textures'].get('legacy_grey'):
        why.append('legacy_grey_texture')
    if r['textures'].get('not_in_library'):
        why.append('texture_not_in_library')
    if r['tier'] in ('LOD0', 'LOD1') and r['texture_px'] and r['texture_px'] != [{'LOD0': 512, 'LOD1': 256}[r['tier']]]:
        why.append('texture_px_vs_tier')
    if r.get('flat_normals') is not None and r['flat_normals'] < 0.999:
        why.append('not_flat_shaded')
    if r.get('uv_world_box_1m') is not None and r['uv_world_box_1m'] < 0.999:
        oi = r.get('uv_box_offset_invariant', {})
        if (oi.get('1m') or 0) >= 0.999:
            why.append('uv_1m_box_with_offset')
        else:
            why.append(f'uv_not_1m_box(abs {r["uv_world_box_1m"]}; offset-free {oi})')
    if r.get('ymin') is not None and abs(r['ymin']) > 0.002:
        why.append('ymin!=0')
    if r['tier'] not in ('LOD0', 'LOD1', 'LOD2'):
        why.append('tier_naming:' + r['tier'])
    return not why, why


for r in rows:
    r['baseline_compliant'], r['deviations'] = compliant(r)

summ = dict(commit=COMMIT, files=len(rows),
            by_tier=dict(collections.Counter(r['tier'] for r in rows)),
            compliant=sum(r['baseline_compliant'] for r in rows),
            deviation_counts=dict(collections.Counter(d.split('(')[0].split(':')[0] for r in rows for d in r['deviations'])),
            generators=dict(collections.Counter(r.get('generator') for r in rows)),
            max_bytes=max(r['bytes'] for r in rows), over_15MB=[r['path'] for r in rows if r['bytes'] > 15_000_000],
            non_LY_material_names=sorted({m for r in rows for m in r.get('materials', []) if not NAME_RE.fullmatch(m)}))
c7 = COMMIT[:7]
json.dump(dict(summary=summ, files=rows), open(os.path.join(W, 'qa', f'census-{c7}.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
cols = ['path', 'tier', 'bytes', 'sha256', 'generator', 'triangles', 'materials', 'suffix_matches_tier', 'textures', 'texture_px',
        'flat_normals', 'uv_world_box_1m', 'uv_box_offset_invariant', 'uv_best_scale_m', 'ymin', 'baseline_compliant', 'deviations']
with open(os.path.join(W, 'qa', f'census-{c7}.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(cols)
    for r in rows:
        w.writerow([json.dumps(r.get(c), ensure_ascii=False) if isinstance(r.get(c), (list, dict)) else r.get(c) for c in cols])
print(json.dumps(summ, ensure_ascii=False, indent=1))
