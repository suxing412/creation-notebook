# LY-033 prep: "nothing original was cut" check between a baseline GLB and a candidate (installed / restored) GLB.
# python -I preserve_check.py <baseline.glb> <candidate.glb> [--allow-new-prefix door_] [--expect-identical]
# PASS requires, for every mesh node of the baseline:
#   * a node with the same name exists in the candidate,
#   * same world matrix (|d| <= 1e-6), same material name,
#   * POSITION / NORMAL / TEXCOORD_0 / indices decoded arrays identical (exact), same triangle count,
#   * all embedded image bytes of the baseline exist byte-identically in the candidate.
# New candidate nodes must start with an allowed prefix (default 'LY031_' / 'LY032_' / 'LY033_').
# --expect-identical: candidate must have no new nodes (used for the "restored" state).
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as R

args = sys.argv[1:]
base, cand = args[0], args[1]
prefixes = ['LY031_', 'LY032_', 'LY033_']
if '--allow-new-prefix' in args:
    prefixes = [args[args.index('--allow-new-prefix') + 1]]
identical = '--expect-identical' in args


def table(path):
    js, binc = R.load(path)
    rows = {}
    sc = js['scenes'][js.get('scene', 0)]
    stack = [(i, np.eye(4)) for i in sc['nodes']]
    while stack:
        i, P = stack.pop()
        nd = js['nodes'][i]
        W = P @ R.nmat(nd)
        for c in nd.get('children', []):
            stack.append((c, W))
        if 'mesh' not in nd:
            continue
        prims = []
        for p in js['meshes'][nd['mesh']]['primitives']:
            h = {}
            for k in ('POSITION', 'NORMAL', 'TEXCOORD_0'):
                if k in p['attributes']:
                    h[k] = hashlib.sha256(R.acc(js, binc, p['attributes'][k]).astype('<f4').tobytes()).hexdigest()
            idx = R.acc(js, binc, p['indices']).reshape(-1).astype('<u4') if 'indices' in p else None
            h['indices'] = None if idx is None else hashlib.sha256(idx.tobytes()).hexdigest()
            h['tris'] = None if idx is None else int(len(idx) // 3)
            h['material'] = js['materials'][p['material']].get('name') if 'material' in p else None
            prims.append(h)
        rows[nd.get('name')] = dict(W=W, prims=prims)
    imgs = set()
    for im in js.get('images', []):
        bv = js['bufferViews'][im['bufferView']]
        imgs.add(hashlib.sha256(binc[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]).hexdigest())
    return rows, imgs


b, bi = table(base)
c, ci = table(cand)
fails = []
for name, r in b.items():
    if name not in c:
        fails.append('missing node %s' % name); continue
    if np.abs(r['W'] - c[name]['W']).max() > 1e-6:
        fails.append('matrix changed %s' % name)
    if r['prims'] != c[name]['prims']:
        fails.append('geometry/material changed %s' % name)
for h in bi - ci:
    fails.append('image missing %s' % h[:12])
new = [n for n in c if n not in b]
bad_new = [n for n in new if not any(n.startswith(p) for p in prefixes)]
if bad_new:
    fails.append('unexpected new nodes %s' % bad_new)
if identical and new:
    fails.append('restored state still has new nodes %s' % new)
rep = dict(baseline=os.path.basename(base), baselineSha=R.sha256(base), candidate=os.path.basename(cand),
           candidateSha=R.sha256(cand), baselineNodes=len(b), newNodes=new, fails=fails, result='PASS' if not fails else 'FAIL')
print(json.dumps(rep, indent=1))
sys.exit(0 if not fails else 1)
