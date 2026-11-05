"""LY-015 prep: do the public K-v1 GLBs keep the native per-source-object triangle order?
If yes, the merged 3-mesh GLBs can be split/masked by qa/source-object-ranges.json (needed for old/new mutual exclusion
of deck, door heads, jambs, leaves) without the original pre-merge objects.
Usage: python -I verify_glb_ranges.py <pkg_dir> <lab_docs_dir> <out_json>
Coordinates reported in Blender z-up (x, -z_gltf, y_gltf)."""
import json, struct, sys, hashlib
from pathlib import Path
import numpy as np

PKG, DOCS, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
GLB = {0: DOCS / 'library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb',
       1: DOCS / 'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD1.glb',
       2: DOCS / 'cities/luoyang/progress-assets/north13-gates/luoyang-kaiyang-gate-study-v1/models/kaiyang-K-LOD2.glb'}
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def load(p):
    b = p.read_bytes(); jl = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + jl])
    bin0 = 20 + jl + 8; blob = b[bin0:]
    def acc(i):
        a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]; off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        n = NC[a['type']]; dt = np.dtype(CT[a['componentType']]); stride = bv.get('byteStride', 0)
        if stride and stride != dt.itemsize * n:
            raw = np.frombuffer(blob, np.uint8, count=stride * a['count'], offset=off).reshape(a['count'], stride)
            return raw[:, :dt.itemsize * n].copy().view(dt).reshape(a['count'], n)
        return np.frombuffer(blob, dt, count=a['count'] * n, offset=off).reshape(a['count'], n)
    meshes = {}
    for node in j['nodes']:
        if 'mesh' not in node: continue
        m = j['meshes'][node['mesh']]; pr = m['primitives'][0]
        pos = acc(pr['attributes']['POSITION']).astype(np.float64); idx = acc(pr['indices']).reshape(-1, 3)
        t = np.array(node.get('translation', [0, 0, 0]))
        pos = pos + t
        zup = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1]], 1)
        meshes[node['name']] = (zup, idx)
    return meshes, hashlib.sha256(b).hexdigest()

ranges = json.loads((PKG / 'qa/source-object-ranges.json').read_text())
EXPECT = {  # from source/build.py (C recipe), Blender z-up gate-local
    'C_upper_deck': [[-12.4, -5.0, 5.0], [12.4, 5.0, 5.34]],
    'C_earth_pier_0': [[-12.4, -5.0, 0.0], [-9.6, 5.0, 5.0]],
    'C_door_head_1': [[-2.6, -4.96, 4.7], [2.6, -4.64, 5.0]],
    'C_jamb_(1, -1)': [[-2.8, -4.96, 0.0], [-2.6, -4.64, 5.0]],
    'C_open_leaf_(1, -1)': [[-2.63, -4.55, 0.05], [-2.49, -1.99, 4.35]],
}
res = {'note': 'expected boxes recomputed from source/build.py; tolerance 1e-3 m', 'lods': {}}
for lod, p in GLB.items():
    meshes, digest = load(p); rows = {}; ok = True; tri_total = {}
    for role in ['earth', 'timber', 'tile']:
        name = 'kaiyang-K-static_' + role; v, f = meshes[name]; rr = ranges[f'LOD{lod}_{role}']
        tri_total[role] = [int(len(f)), int(rr[-1]['triangle_range'][1])]
        for r in rr:
            s, e = r['triangle_range']; pts = v[f[s:e].ravel()]
            bb = [pts.min(0).round(4).tolist(), pts.max(0).round(4).tolist()]
            if r['source_object'] in EXPECT:
                ex = EXPECT[r['source_object']]; good = bool(np.allclose(np.array(bb), np.array(ex), atol=1e-3))
                ok &= good; rows[r['source_object']] = {'role': role, 'range': [s, e], 'glb_bbox': bb, 'expected': ex, 'match': good}
    res['lods'][f'LOD{lod}'] = {'glb': str(p).replace('\\', '/'), 'sha256': digest, 'triangles_glb_vs_ranges': tri_total, 'checked': rows, 'all_match': ok}
OUT.write_text(json.dumps(res, indent=1)); print(json.dumps({k: (v['all_match'], v['triangles_glb_vs_ranges']) for k, v in res['lods'].items()}))
