# LY-006: vertical-ray probes on existing public GLBs to freeze port positions that sit on
# existing geometry (not on future parts). Read-only. Usage:
#   python -I measure_ports.py <lab docs dir> <out json>
import json, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from glbio import read_glb, mesh_items, apply
from vray import VSampler

DOCS, OUT = sys.argv[1], sys.argv[2]
cache = {}
def load(rel):
    if rel not in cache:
        g = read_glb(os.path.join(DOCS, rel))
        T = []
        for i, name, w, pos, tri, anc in mesh_items(g):
            V = apply(w, pos); T.append(V[tri])
        cache[rel] = (g['sha256'], g['size'], VSampler(np.concatenate(T), cell=2.0))
    return cache[rel]

def top_up(rel, x, z, below=1e9):
    sha, size, s = load(rel)
    hs = [(y, ny) for y, ny in s.heights(x, z) if ny > 0.5 and y < below]
    return (max(hs)[0] if hs else None), sha

res = {'probes': [], 'files': {}}
def probe(pid, rel, x, z, below=1e9, note=''):
    y, sha = top_up(rel, x, z, below)
    res['probes'].append({'id': pid, 'file': 'docs/' + rel, 'sha256': sha, 'x': x, 'z': z, 'below': None if below == 1e9 else below,
                          'topUpwardY': None if y is None else round(float(y), 5), 'note': note})
    res['files']['docs/' + rel] = {'sha256': sha, 'bytes': cache[rel][1]}
    return y

K_G = 'library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD0.glb'
for nm, x in (('C', 0.0), ('W', -7.6), ('E', 7.6)):
    probe(f'kaiyang-ground passage-{nm}', K_G, x, 0.0, note='kaiyang passage centre (local), ground strip top')
    probe(f'kaiyang-ground outer-edge-{nm}', K_G, x, 6.95, note='just inside outer edge z=+7')
P_G = 'library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD0.glb'
for nm, x in (('C', 0.0), ('W', -7.9), ('E', 7.9)):
    probe(f'pingcheng-ground passage-{nm}', P_G, x, 0.0, note='pingcheng passage centre (local)')
    probe(f'pingcheng-ground outer-edge-{nm}', P_G, x, 9.95, note='just inside outer edge z=+10')
# frontage v2.1 thresholds: openings from Blender-plan list (x, y=front) -> glTF z = -y; probe 0.30 m inside the front line
FR = 'library/models/m-luoyang-market-frontage/files/street_frontage-LOD0.glb'
shops = json.load(open(sys.argv[3], encoding='utf-8')) if len(sys.argv) > 3 else []
for s in shops:
    zf = -s['frontY']; inward = -1.0 if s['frontY'] > 0 else 1.0  # N row front at y=+5 -> z=-5, interior towards -z
    for k, (x0, x1) in enumerate(s['openings']):
        xc = (x0 + x1) / 2
        probe(f"frontage shop{s['idx']} door{k} inside", FR, xc, zf + inward * 0.30, below=1.0, note='plinth/floor top 0.30 m inside front line (frontage-local, ground y=0)')
        probe(f"frontage shop{s['idx']} door{k} outside", FR, xc, zf - inward * 0.30, below=1.0, note='0.30 m outside front line; None = no frontage ground (street ground is the city slab)')
# granary step feet in storage-site frame (world - (2285.714,0,-3673.469)); scan from house face outward (+z)
GR = 'cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb'
TX, TZ = 2285.714, -3673.469
for nm, xl in (('A', -12.0), ('B', 12.0)):
    prof = []
    for k in range(0, 121):
        zl = -2.0 + 0.05 * k
        y, sha = top_up(GR, TX + xl, TZ + zl, below=3.0)
        prof.append([round(zl, 3), None if y is None else round(float(y), 4)])
    res['probes'].append({'id': f'granary-{nm} front profile', 'file': 'docs/' + GR, 'sha256': sha, 'x_local': xl,
                          'profile_zlocal_topY': prof, 'note': 'top upward surface below y=3.0 along x_local; storage-site frame'})
    res['files']['docs/' + GR] = {'sha256': sha, 'bytes': cache[GR][1]}
json.dump(res, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for p in res['probes']:
    if 'profile_zlocal_topY' in p:
        pr = p['profile_zlocal_topY']; ch = [pr[0]] + [pr[i] for i in range(1, len(pr)) if pr[i][1] != pr[i - 1][1]]
        print(p['id'], ch)
    else:
        print(p['id'], p['topUpwardY'])
