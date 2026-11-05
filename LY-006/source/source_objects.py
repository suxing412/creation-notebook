# LY-006: map generator source objects (qa/source-object-ranges.json from the public sanitized source ZIP)
# onto the actual public GLB triangles and report per-object AABB in the asset-local glTF frame.
import json, sys, os, re, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from glbio import read_glb, mesh_items, apply

def objects(ranges_path, glbs):
    rng = json.load(open(ranges_path, encoding='utf-8'))
    out = {}
    for lod, path in glbs.items():
        g = read_glb(path)
        meshes = {}
        for i, name, w, pos, tri, anc in mesh_items(g):
            meshes.setdefault(name, []).append((apply(w, pos), tri))
        for key, lst in rng.items():
            if not key.startswith(lod + '_'):
                continue
            mat = key.split('_', 1)[1]
            cand = [n for n in meshes if n.endswith('static_' + mat)]
            assert len(cand) == 1, (key, list(meshes))
            parts = meshes[cand[0]]
            P = np.concatenate([p for p, t in parts]); T = np.concatenate([t for p, t in parts])  # single prim expected
            assert len(parts) == 1, (key, len(parts))
            for e in lst:
                a, b = e['triangle_range']
                v = P[T[a:b].reshape(-1)]
                out.setdefault(e['source_object'], {})[lod] = {
                    'mesh': cand[0], 'material': mat, 'triangle_range': [a, b],
                    'aabb': [v.min(0).round(4).tolist(), v.max(0).round(4).tolist()]}
        out.setdefault('__glb__', {})[lod] = {'path': path, 'sha256': g['sha256'], 'bytes': g['size']}
    return out

if __name__ == '__main__':
    ranges, outp = sys.argv[1], sys.argv[2]
    glbs = dict(a.split('=', 1) for a in sys.argv[3:])
    o = objects(ranges, glbs)
    import hashlib
    o['__ranges__'] = {'path': ranges, 'sha256': hashlib.sha256(open(ranges, 'rb').read()).hexdigest()}
    json.dump(o, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(o) - 2, 'objects')
