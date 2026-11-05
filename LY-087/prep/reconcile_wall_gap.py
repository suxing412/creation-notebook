# LY-087 prep: reconcile "drain low end -> front wall" distance with the LY-046 prep figure (3.0 m).
# Read-only. Works in the GLB's local frame (the 6 city nodes only translate / rotate it).
# Reports, along the drain flow axis at the drain's lateral position: drain low-end face, wall
# triangles' near face, far face and centre, and the wall's thickness and top.
import sys, os, json, hashlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbread as G
LAB = 'D:/GitHub/creation-notebook-lab/docs/cities/luoyang/assets/'
CASES = [('d08/TC03-LOD1-prototype.glb', 'architecture_C_drain_stone', 'architecture_C_earth_wall'),
         ('c02v/TC03-2-LOD1-prototype.glb', 'architecture_C_drain_stone.001', 'architecture_C_earth_wall.001')]
out = []
for rel, dn, wn in CASES:
    p = LAB + rel
    g = G.load(p)
    tri = {name: (V, F) for _, name, _, V, F in G.node_tris(g)}
    Vd, _ = tri[dn]
    ext = Vd.max(0) - Vd.min(0)
    ax = int(np.argmax([ext[0], 0, ext[2]]))           # flow axis (x or z) = long axis
    lat = 2 - ax                                         # other horizontal axis
    # low end: end with lower minimum y
    lo_end_min = Vd[np.isclose(Vd[:, ax], Vd[:, ax].min(), atol=1e-4)][:, 1].min()
    hi_end_min = Vd[np.isclose(Vd[:, ax], Vd[:, ax].max(), atol=1e-4)][:, 1].min()
    sgn = -1 if lo_end_min < hi_end_min else 1         # flow toward min (sgn -1) or max (+1)
    low_face = Vd[:, ax].min() if sgn < 0 else Vd[:, ax].max()
    lat_c = 0.5 * (Vd[:, lat].min() + Vd[:, lat].max())
    Vw, Fw = tri[wn]
    # wall triangles whose lateral span covers the drain centreline and that lie downstream
    T = Vw[Fw]
    cover = (T[:, :, lat].min(1) <= lat_c) & (T[:, :, lat].max(1) >= lat_c)
    down = ((T[:, :, ax] - low_face) * sgn).min(1) > -1e-6
    low = T[:, :, 1].min(1) < 0.5
    S = T[cover & down & low]
    d = (S[:, :, ax] - low_face) * sgn
    near, far = float(d.min()), float(d.max())
    # wall slab nearest the drain: keep triangles whose near distance is within thickness of 'near'
    out.append({'glb': rel, 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'drainNode': dn, 'wallNode': wn,
                'flowAxisLocal': 'xz'[ax // 2], 'flowSign': sgn, 'drainLowFaceLocal': round(float(low_face), 4),
                'drainLowFloorY': round(float(min(lo_end_min, hi_end_min)), 4),
                'wallNearFace_m': round(near, 3), 'wallFarFace_m': round(far, 3),
                'wallThickness_m': round(far - near, 3), 'wallCentre_m': round(0.5 * (near + far), 3),
                'wallTopY': round(float(S[:, :, 1].max()), 3)})
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'E-wall-gap-reconcile.json'), 'w', encoding='utf-8'), indent=1)
for o in out:
    print(json.dumps(o))
