# LY-007 用法: python -I compare.LY007.py <复刻件目录> <她的提交字节目录> <输出 json>
# 原注释: python -I compare.py : her S84/G10 LOD0-2 vs round2 replicas, structure + vertex-level match (read-only on her files)
import json, struct, os, sys, hashlib, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
MINE = sys.argv[1] if len(sys.argv) > 1 else HERE
# LY-007 改动：她的原件改读 argv[2]（由 git show <commit>:<path> 导出的提交字节），不读检出工作树
ORIG = sys.argv[2]
SRC = {'S84': ORIG + '/', 'G10': ORIG + '/'}
def rd(p):
    b = open(p, 'rb').read(); jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl]); o = 20 + jl; bl = struct.unpack('<I', b[o:o + 4])[0]
    return j, b[o + 8:o + 8 + bl]
def acc(j, bn, i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    dt = {5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a['componentType']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a['type']]
    return np.frombuffer(bn, dt, count=a['count'] * n, offset=bv.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, n).astype(np.float64)
def corners(j, bn, nd):
    pr = j['meshes'][nd['mesh']]['primitives'][0]
    P = acc(j, bn, pr['attributes']['POSITION']); N = acc(j, bn, pr['attributes']['NORMAL']); U = acc(j, bn, pr['attributes']['TEXCOORD_0'])
    I = acc(j, bn, pr['indices']).reshape(-1).astype(int)
    return np.c_[P[I], N[I], U[I]], len(P), len(I) // 3
def key(rows, q=(1e-3, 1e-2, 1e-3)):
    f = lambda x, d: np.floor(x / d + 0.2513)          # 分箱带偏移，避免 -4.3175 这类正好落在 .5 上的值因 1 ulp 分到两边
    a = np.c_[f(rows[:, :3], q[0]), f(rows[:, 3:6], q[1]), f(rows[:, 6:], q[2])].astype(np.int64)
    return collections.Counter(map(tuple, a))
out = {}
for proto in ('S84', 'G10'):
    for lod in (0, 1, 2):
        fn = f'{proto}-LOD{lod}.glb'
        jh, bh = rd(SRC[proto] + fn); jm, bm = rd(os.path.join(MINE, fn))
        r = {'generator': (jh['asset']['generator'], jm['asset']['generator'])}
        r['nodes_equal'] = [n['name'] for n in jh['nodes']] == [n['name'] for n in jm['nodes']]
        r['meshes_equal'] = [m['name'] for m in jh['meshes']] == [m['name'] for m in jm['meshes']]
        r['materials_equal'] = [m['name'] for m in jh['materials']] == [m['name'] for m in jm['materials']]
        r['material_json_equal'] = jh['materials'] == jm['materials']
        r['images_order_equal'] = [i.get('name') for i in jh.get('images', [])] == [i.get('name') for i in jm.get('images', [])]
        def imsha(j, b):
            return [hashlib.sha1(b[j['bufferViews'][i['bufferView']].get('byteOffset', 0):][:j['bufferViews'][i['bufferView']]['byteLength']]).hexdigest()[:12] for i in j.get('images', [])]
        r['image_bytes_equal'] = imsha(jh, bh) == imsha(jm, bm)
        r['bufferview_lengths_equal'] = [bv['byteLength'] for bv in jh['bufferViews']] == [bv['byteLength'] for bv in jm['bufferViews']]
        r['bufferview_offsets_equal'] = [bv.get('byteOffset', 0) for bv in jh['bufferViews']] == [bv.get('byteOffset', 0) for bv in jm['bufferViews']]
        r['samplers_equal'] = jh.get('samplers') == jm.get('samplers')
        ex = []
        for a, b in zip(jh['nodes'], jm['nodes']):
            ka, kb = list(a.get('extras', {})), list(b.get('extras', {}))
            ex.append({'keys_equal': ka == kb, 'her_keys': ka, 'my_keys': kb,
                       'diff_values': {k: (a['extras'].get(k), b['extras'].get(k)) for k in ka if a['extras'].get(k) != b['extras'].get(k)}})
        r['extras'] = ex
        per = []
        for a, b in zip(jh['nodes'], jm['nodes']):
            ca, va, ta = corners(jh, bh, a); cb, vb, tb = corners(jm, bm, b)
            Ka, Kb = key(ca), key(cb)
            Ka_pos, Kb_pos = key(ca[:, :3].repeat(1, 0).__array__() if False else np.c_[ca[:, :3], np.zeros((len(ca), 5))]), key(np.c_[cb[:, :3], np.zeros((len(cb), 5))])
            inter = sum((Ka & Kb).values()); inter_p = sum((Ka_pos & Kb_pos).values())
            lo_a, hi_a = ca[:, :3].min(0), ca[:, :3].max(0); lo_b, hi_b = cb[:, :3].min(0), cb[:, :3].max(0)
            def tset(j, bn, nd):
                pr = j['meshes'][nd['mesh']]['primitives'][0]
                Pp = acc(j, bn, pr['attributes']['POSITION']); Ii = acc(j, bn, pr['indices']).reshape(-1, 3).astype(int)
                return collections.Counter(tuple(sorted(tuple(np.floor(Pp[i] / 1e-3 + 0.2513)) for i in t)) for t in Ii)
            Ta, Tb = tset(jh, bh, a), tset(jm, bm, b)
            per.append({'node': a['name'], 'tris': (ta, tb), 'verts': (va, vb),
                        'triangle_match': round(sum((Ta & Tb).values()) / max(sum(Ta.values()), 1), 4),
                        'corner_match_pos_normal_uv': round(inter / max(len(ca), len(cb)), 4),
                        'corner_match_pos_only': round(inter_p / max(len(ca), len(cb)), 4),
                        'bbox_her': [lo_a.round(4).tolist(), hi_a.round(4).tolist()], 'bbox_mine': [lo_b.round(4).tolist(), hi_b.round(4).tolist()]})
        r['per_node'] = per
        out[fn] = r
        print('=====', fn, r['generator'])
        print('  names nodes/meshes/materials/images-order:', r['nodes_equal'], r['meshes_equal'], r['materials_equal'], r['images_order_equal'],
              '| mat-json', r['material_json_equal'], 'img-bytes', r['image_bytes_equal'], 'bv-len', r['bufferview_lengths_equal'], 'bv-off', r['bufferview_offsets_equal'])
        for e in ex: print('  extras keys equal', e['keys_equal'], 'diff', e['diff_values'])
        for p in per: print('  %-34s tris %-12s verts %-12s corner(pos+n+uv) %.4f  corner(pos) %.4f  triangles %.4f' % (p['node'], p['tris'], p['verts'], p['corner_match_pos_normal_uv'], p['corner_match_pos_only'], p['triangle_match']))
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)  # LY-007 改动：输出路径改为 argv[3]
