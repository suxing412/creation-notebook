"""Stdlib-only GLB auditor: structure, geometry stats, materials, textures, basic hygiene."""
import json, struct, sys, os, hashlib, math

CT = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}


def mat_mul(a, b):
    return [sum(a[r + 4 * k] * b[k + 4 * c] for k in range(4)) for c in range(4) for r in range(4)]


def trs(n):
    if 'matrix' in n:
        return n['matrix']
    t = n.get('translation', [0, 0, 0]); r = n.get('rotation', [0, 0, 0, 1]); s = n.get('scale', [1, 1, 1])
    x, y, z, w = r
    m = [1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w), 0,
         2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w), 0,
         2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y), 0,
         0, 0, 0, 1]
    for c in range(3):
        for rr in range(3):
            m[rr + 4 * c] *= s[c]
    m[12], m[13], m[14] = t
    return m


def xf(m, p):
    return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
            m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
            m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]]


def det3(m):
    return (m[0] * (m[5] * m[10] - m[9] * m[6]) - m[4] * (m[1] * m[10] - m[9] * m[2]) + m[8] * (m[1] * m[6] - m[5] * m[2]))


def audit(path):
    raw = open(path, 'rb').read()
    out = {'path': path.replace('\\', '/'), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'issues': []}
    if raw[:4] != b'glTF':
        out['issues'].append('NOT_GLB_MAGIC'); return out
    ver, length = struct.unpack_from('<II', raw, 4)
    if length != len(raw):
        out['issues'].append(f'LENGTH_MISMATCH header={length}')
    off = 12; js = None; bin_ = b''
    while off < len(raw):
        clen, ctype = struct.unpack_from('<II', raw, off); off += 8
        chunk = raw[off:off + clen]; off += clen
        if ctype == 0x4E4F534A: js = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942: bin_ = chunk
    g = js
    out['generator'] = g.get('asset', {}).get('generator')
    out['version'] = g.get('asset', {}).get('version')
    out['extUsed'] = g.get('extensionsUsed', [])
    out['extReq'] = g.get('extensionsRequired', [])
    acc = g.get('accessors', []); bvs = g.get('bufferViews', [])

    def read(ai, limit=None):
        a = acc[ai]
        if 'bufferView' not in a:
            return None
        bv = bvs[a['bufferView']]
        n = NC[a['type']]; fmt = CT[a['componentType']]; cs = struct.calcsize(fmt)
        stride = bv.get('byteStride') or cs * n
        base = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        cnt = a['count'] if limit is None else min(a['count'], limit)
        res = []
        for i in range(cnt):
            res.append(struct.unpack_from('<' + fmt * n, bin_, base + i * stride))
        return res

    meshes = g.get('meshes', [])
    tri = 0; verts = 0; prims = 0; nouv = 0; nonorm = 0; degen = 0; nonindexed = 0; modes = set()
    no_minmax = 0
    mesh_tri = []
    for mi, m in enumerate(meshes):
        mt = 0
        for p in m.get('primitives', []):
            prims += 1
            mode = p.get('mode', 4); modes.add(mode)
            at = p['attributes']
            pa = acc[at['POSITION']]
            if 'min' not in pa or 'max' not in pa: no_minmax += 1
            verts += pa['count']
            if 'TEXCOORD_0' not in at: nouv += 1
            if 'NORMAL' not in at: nonorm += 1
            if mode == 4:
                if 'indices' in p:
                    ic = acc[p['indices']]['count']; t = ic // 3
                    # degenerate check (index-level + zero area) on up to 200k indices
                    if ic <= 600000:
                        idx = [v[0] for v in read(p['indices'])]
                        pos = read(at['POSITION'])
                        for k in range(0, len(idx) - 2, 3):
                            a_, b_, c_ = idx[k], idx[k + 1], idx[k + 2]
                            if a_ == b_ or b_ == c_ or a_ == c_:
                                degen += 1; continue
                            A, B, C = pos[a_], pos[b_], pos[c_]
                            u = [B[i] - A[i] for i in range(3)]; v = [C[i] - A[i] for i in range(3)]
                            cx = u[1] * v[2] - u[2] * v[1]; cy = u[2] * v[0] - u[0] * v[2]; cz = u[0] * v[1] - u[1] * v[0]
                            if cx * cx + cy * cy + cz * cz < 1e-20: degen += 1
                else:
                    nonindexed += 1; t = pa['count'] // 3
                mt += t
        tri += mt; mesh_tri.append(mt)
    out.update(meshes=len(meshes), primitives=prims, triangles=tri, vertices=verts,
               primsNoUV=nouv, primsNoNormal=nonorm, degenerateTris=degen, nonIndexedPrims=nonindexed,
               modes=sorted(modes), posNoMinMax=no_minmax)
    mats = g.get('materials', [])
    out['materials'] = len(mats)
    out['texturedMaterials'] = sum(1 for m in mats if any(k in json.dumps(m) for k in ('baseColorTexture', 'normalTexture', 'metallicRoughnessTexture', 'occlusionTexture', 'emissiveTexture')))
    out['images'] = len(g.get('images', []))
    out['imageBytes'] = sum(bvs[i['bufferView']]['byteLength'] for i in g.get('images', []) if 'bufferView' in i)
    out['imageMimes'] = sorted({i.get('mimeType', 'uri') for i in g.get('images', [])})
    out['primsNoMaterial'] = sum(1 for m in meshes for p in m.get('primitives', []) if 'material' not in p)
    unnamed_mats = sum(1 for m in mats if not m.get('name'))
    out['unnamedMaterials'] = unnamed_mats
    out['doubleSidedMaterials'] = sum(1 for m in mats if m.get('doubleSided'))
    out['nodes'] = len(g.get('nodes', []))
    out['unnamedNodes'] = sum(1 for n in g.get('nodes', []) if not n.get('name'))
    out['animations'] = len(g.get('animations', []))
    out['skins'] = len(g.get('skins', []))
    # world bbox via accessor min/max corners
    nodes = g.get('nodes', [])
    lo = [math.inf] * 3; hi = [-math.inf] * 3; negdet = 0
    scene = g.get('scenes', [{}])[g.get('scene', 0)] if g.get('scenes') else {'nodes': list(range(len(nodes)))}

    def walk(ni, pm):
        nonlocal negdet
        n = nodes[ni]; m = mat_mul(pm, trs(n))
        if 'mesh' in n:
            if det3(m) < 0: negdet += 1
            for p in meshes[n['mesh']]['primitives']:
                a = acc[p['attributes']['POSITION']]
                if 'min' in a:
                    mn, mx = a['min'], a['max']
                    for cx in (mn[0], mx[0]):
                        for cy in (mn[1], mx[1]):
                            for cz in (mn[2], mx[2]):
                                q = xf(m, [cx, cy, cz])
                                for i in range(3):
                                    lo[i] = min(lo[i], q[i]); hi[i] = max(hi[i], q[i])
        for c in n.get('children', []):
            walk(c, m)
    I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for r in scene.get('nodes', []):
        walk(r, I)
    if lo[0] != math.inf:
        out['bboxMin'] = [round(x, 3) for x in lo]; out['bboxMax'] = [round(x, 3) for x in hi]
        out['size'] = [round(hi[i] - lo[i], 3) for i in range(3)]
        out['center'] = [round((hi[i] + lo[i]) / 2, 3) for i in range(3)]
    out['mirroredMeshNodes'] = negdet
    # issues
    if out['extReq']: out['issues'].append('EXT_REQUIRED:' + ','.join(out['extReq']))
    if degen: out['issues'].append(f'DEGENERATE_TRIS:{degen}')
    if nonorm: out['issues'].append(f'PRIMS_NO_NORMAL:{nonorm}')
    if out['primsNoMaterial']: out['issues'].append(f'PRIMS_NO_MATERIAL:{out["primsNoMaterial"]}')
    if no_minmax: out['issues'].append(f'POSITION_NO_MINMAX:{no_minmax}')
    if negdet: out['issues'].append(f'MIRRORED_NODES:{negdet}')
    if prims > 300: out['issues'].append(f'HIGH_DRAWCALLS:{prims}')
    return out


if __name__ == '__main__':
    root = sys.argv[1]; listfile = sys.argv[2]; outp = sys.argv[3]
    res = []
    for rel in open(listfile, encoding='utf-8').read().split():
        p = os.path.join(root, rel)
        try:
            r = audit(p); r['path'] = rel
        except Exception as e:
            r = {'path': rel, 'issues': ['PARSE_ERROR:' + repr(e)]}
        res.append(r)
        print(rel, r.get('triangles'), r.get('issues'), flush=True)
    json.dump(res, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
