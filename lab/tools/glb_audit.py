"""GLB auditor; compressed views additionally require Node and the vendored decoder."""
import json, struct, sys, os, hashlib, math
# Keep the standalone `python -I lab/tools/glb_audit.py` entrypoint usable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb_audit_io import Accessors, AuditError, MAX_FILE, load_glb, require

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
    path = os.fspath(path)
    # Bound reads before allocation. Hash the original transport bytes, never a
    # reconstructed GLB or decoded buffer.
    with open(path, 'rb') as source:
        raw = source.read(MAX_FILE + 1)
    out = {'path': path.replace('\\', '/'), 'bytes': len(raw),
           'sha256': hashlib.sha256(raw).hexdigest(), 'issues': [], 'fatalErrors': []}
    if len(raw) > MAX_FILE:
        # Oversized input is not fully read: do not mislabel a prefix digest.
        out.update(bytes=os.path.getsize(path), sha256=None)
        out['fatalErrors'] = ['FILE_LIMIT']; out['issues'] = ['FILE_LIMIT']; return out
    try:
        # Commit computed statistics only after the whole audit succeeds.
        return _audit(raw, {**out, 'issues': [], 'fatalErrors': []})
    except (AuditError, ValueError, KeyError, IndexError, TypeError, AttributeError, struct.error, OverflowError, RecursionError) as error:
        out['fatalErrors'] = [str(error) or type(error).__name__]
        out['issues'].append('PARSE_ERROR:' + out['fatalErrors'][0])
        return out


def _audit(raw, out):
    g, bin_ = load_glb(raw)
    out['generator'] = g.get('asset', {}).get('generator')
    out['version'] = g.get('asset', {}).get('version')
    out['extUsed'] = g.get('extensionsUsed', [])
    out['extReq'] = g.get('extensionsRequired', [])
    data = Accessors(g, bin_)
    acc = g.get('accessors', []); bvs = g.get('bufferViews', [])
    read = data.read
    out['decodedViews'] = data.decoded_views
    out['decodedBytes'] = data.decoded_bytes

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
        require(all(math.isfinite(v) for v in m), 'NONFINITE_WORLD_TRANSFORM')
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
                                require(all(math.isfinite(v) for v in q), 'NONFINITE_WORLD_BOUNDS')
                                for i in range(3):
                                    lo[i] = min(lo[i], q[i]); hi[i] = max(hi[i], q[i])
        for c in n.get('children', []):
            walk(c, m)
    I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    for r in scene.get('nodes', []):
        walk(r, I)
    if lo[0] != math.inf:
        out['bboxMin'] = [round(x, 3) for x in lo]; out['bboxMax'] = [round(x, 3) for x in hi]
        size = [hi[i] - lo[i] for i in range(3)]
        center = [hi[i] / 2 + lo[i] / 2 for i in range(3)]
        require(all(math.isfinite(v) for v in size + center), 'NONFINITE_WORLD_BOUNDS')
        out['size'] = [round(v, 3) for v in size]
        out['center'] = [round(v, 3) for v in center]
    out['mirroredMeshNodes'] = negdet
    # issues
    # Supported required extensions have been fully decoded/handled above.
    # Unknown required extensions are fatal, never silently removed.
    if degen: out['issues'].append(f'DEGENERATE_TRIS:{degen}')
    if nonorm: out['issues'].append(f'PRIMS_NO_NORMAL:{nonorm}')
    if out['primsNoMaterial']: out['issues'].append(f'PRIMS_NO_MATERIAL:{out["primsNoMaterial"]}')
    if no_minmax: out['issues'].append(f'POSITION_NO_MINMAX:{no_minmax}')
    if negdet: out['issues'].append(f'MIRRORED_NODES:{negdet}')
    if prims > 300: out['issues'].append(f'HIGH_DRAWCALLS:{prims}')
    return out


if __name__ == '__main__':
    root = sys.argv[1]; listfile = sys.argv[2]; outp = sys.argv[3]
    res = []; failed = False
    for rel in open(listfile, encoding='utf-8').read().split():
        p = os.path.join(root, rel)
        try:
            r = audit(p); r['path'] = rel
        except Exception as e:
            r = {'path': rel, 'issues': ['PARSE_ERROR:' + repr(e)]}
        failed = failed or bool(r.get('fatalErrors')) or any(i.startswith('PARSE_ERROR:') for i in r.get('issues', []))
        res.append(r)
        print(rel, r.get('triangles'), r.get('issues'), flush=True)
    json.dump(res, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    sys.exit(1 if failed else 0)
