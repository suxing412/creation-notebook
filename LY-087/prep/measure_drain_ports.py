# LY-087 prep measurement (read-only). python -I measure_drain_ports.py
# A. every drainage element loaded in the city (TC03 / TC03-2 architecture_C_drain_stone, 6 nodes x 2 LODs):
#    slope, flow direction, end caps, what the low end spills onto, first obstruction downstream.
# B. the four atomic grounds: is there any fall/low line that could define a downstream direction?
# C. palace waterway interface (library only, not in city): inverts, openings, port consistency across LODs.
# D. dependency candidates (library / LY-073 extract): stable platform fall, kiln drain nodes, biyong water ring closure.
import os, sys, json, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glbread as G
from rays import vertical_hits, ray_first

LAB = 'D:/GitHub/creation-notebook-lab/docs/'
CITY = LAB + 'cities/luoyang/'
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)


def r(x, n=4):
    return None if x is None else round(float(x), n)


# ---------- city inputs (values copied from city-data.mjs @ bce3211, cross-checked with LY-001 city-data.dump.json) ----------
DUMP = json.load(open('D:/GitHub/creation-notebook-workpacks/LY-001/qa/city-data.dump.json', encoding='utf-8'))
ASSETS = {a['id']: a for a in DUMP['assets']}
for _a in ASSETS.values():
    _a['path'] = _a['sourcePath']
    if _a.get('nearUrl'):
        _a['nearPath'] = _a['nearUrl'].split('/docs/cities/luoyang/')[1]
NODES = {n['id']: n for n in DUMP['nodes']}
DRAIN_NODES = ['C02-020', 'C02-003', 'C02-008', 'C02-012', 'FROZEN-D08-NW', 'FROZEN-D08-NE']
GROUND_NODES = ['ground-network-ground-stitched', 'ground-retained', 'ground-south', 'ground-D08']


def node_matrix(n):
    if 'matrix' in n:
        return G.colmajor_to_m(n['matrix'])
    M = np.eye(4); M[:3, 3] = n.get('position', [0, 0, 0])
    if n.get('rotationY'):
        c, s = np.cos(n['rotationY']), np.sin(n['rotationY'])
        M[:3, :3] = [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    if n.get('scale') not in (None, 1):
        raise SystemExit('non-unit scale on ' + n['id'])
    return M


# terrain soup (world)
terrain = []
terrain_files = {}
for gid in GROUND_NODES:
    n = NODES[gid]; a = ASSETS[n['asset']]
    g = G.load(CITY + a['path'])
    assert g['sha256'] == a['sha256'], gid
    terrain_files[gid] = {'path': 'docs/cities/luoyang/' + a['path'], 'sha256': g['sha256'], 'nodeMatrix': node_matrix(n).T.reshape(-1).tolist()}
    for i, nm, mats, V, F in G.node_tris(g, node_matrix(n), a.get('excludeNodes', [])):
        terrain.append((gid + ':' + nm, V[F]))


def terrain_near(xmin, xmax, zmin, zmax):
    out = []
    for name, T in terrain:
        lo, hi = T.min(1), T.max(1)
        m = (hi[:, 0] >= xmin) & (lo[:, 0] <= xmax) & (hi[:, 2] >= zmin) & (lo[:, 2] <= zmax)
        if m.any():
            out.append((name, T[m]))
    return out


def top_surface(parts, x, z, below):
    """highest crossing <= below among parts; returns (y, part) or (None, None)"""
    best = (None, None)
    for name, T in parts:
        ys = vertical_hits(T, x, z)
        ys = ys[ys <= below + 1e-9]
        if len(ys) and (best[0] is None or ys[-1] > best[0]):
            best = (float(ys[-1]), name)
    return best


def first_hit(parts, o, d, tmax):
    best = (None, None)
    for name, T in parts:
        t, k = ray_first(T, o, d, tmax)
        if t is not None and (best[0] is None or t < best[0]):
            best = (t, name)
    return best


# ---------- A. drains in city ----------
def drain_local(g):
    for i, nm, mats, V, F in G.node_tris(g):
        if 'drain' in nm:
            ext = V.max(0) - V.min(0)
            ax = 0 if ext[0] > ext[2] else 2
            ends = sorted(set(np.round(V[:, ax], 4)))
            e0, e1 = ends[0], ends[-1]
            prof = {}
            for e in (e0, e1):
                s = V[np.abs(V[:, ax] - e) < 1e-4]
                ymin, ymax = s[:, 1].min(), s[:, 1].max()
                inner = s[(s[:, 1] > ymin + 1e-4) & (s[:, 1] < ymax - 1e-4)]
                other = 2 - ax
                xs = sorted(set(np.round(inner[:, other], 4)))
                prof[e] = {'floorTop': float(inner[:, 1].min()), 'innerWalls': [xs[0], xs[-1]], 'rim': float(ymax), 'base': float(ymin)}
            hi_e, lo_e = (e0, e1) if prof[e0]['floorTop'] > prof[e1]['floorTop'] else (e1, e0)
            return {'node': nm, 'material': mats, 'V': V, 'F': F, 'axis': 'xz'[ax // 2], 'ax': ax,
                    'hiEnd': hi_e, 'loEnd': lo_e, 'prof': prof, 'length': abs(e1 - e0)}
    return None


A = {'method': 'channel floor = lowest interior vertex at each end face; flow = high floor end -> low floor end; '
               'end-cap test = horizontal ray at floor+0.03 from 0.05 m inside the slot along flow vs the drain mesh; '
               'spill = highest surface (non-excluded court nodes, then city terrain) <= floorLow+0.30 at points beyond the low end; '
               'obstruction = first hit of horizontal ray at floorLow+0.03 along flow vs non-excluded court nodes + terrain, 6 m max.',
     'instances': []}
proto_cache = {}
for nid in DRAIN_NODES:
    n = NODES[nid]; a = ASSETS[n['asset']]; M = node_matrix(n)
    for lod, path, sha in (('LOD1-far', a['path'], a['sha256']), ('LOD0-near', a['nearPath'], a['nearSha256'])):
        if path not in proto_cache:
            g = G.load(CITY + path); assert g['sha256'] == sha, path
            proto_cache[path] = g
        g = proto_cache[path]
        d = drain_local(g)
        ax = d['ax']; other = 2 - ax
        walls = d['prof'][d['loEnd']]['innerWalls']; c_other = (walls[0] + walls[1]) / 2
        sgn = 1.0 if d['loEnd'] > d['hiEnd'] else -1.0
        fl_lo = d['prof'][d['loEnd']]['floorTop']; fl_hi = d['prof'][d['hiEnd']]['floorTop']

        def P(axv, y):
            p = np.zeros(3); p[ax] = axv; p[other] = c_other; p[1] = y
            return p
        dir_local = np.zeros(3); dir_local[ax] = sgn
        # end cap test on the drain mesh (local)
        Td = d['V'][d['F']]
        o = P(d['loEnd'] - sgn * 0.05, fl_lo + 0.03)
        tcap, _ = ray_first(Td, o, dir_local, 0.5)
        o2 = P(d['hiEnd'] + sgn * 0.05, fl_hi + 0.03)
        tcap_hi, _ = ray_first(Td, o2, -dir_local, 0.5)
        # world
        Mw = M
        lo_w = (Mw @ np.r_[P(d['loEnd'], fl_lo), 1])[:3]
        hi_w = (Mw @ np.r_[P(d['hiEnd'], fl_hi), 1])[:3]
        dir_w = Mw[:3, :3] @ dir_local
        court_parts = []
        for i, nm, mats, V, F in G.node_tris(g, Mw, a.get('excludeNodes', [])):
            if 'drain' in nm:
                continue
            court_parts.append((nid + ':' + nm, V[F]))
        tparts = terrain_near(lo_w[0] - 8, lo_w[0] + 8, lo_w[2] - 8, lo_w[2] + 8)
        spill = []
        for dist in (0.02, 0.05, 0.10, 0.25, 0.50, 1.0, 2.0, 2.9):
            q = lo_w + dir_w * dist
            yc, pc = top_surface(court_parts, q[0], q[2], fl_lo + 0.30)
            yt, pt = top_surface(tparts, q[0], q[2], fl_lo + 0.30)
            top = max([v for v in (yc, yt) if v is not None], default=None)
            spill.append({'dist': dist, 'courtTop': r(yc), 'courtPart': pc, 'terrainTop': r(yt), 'terrainPart': pt,
                          'stepFromFloorLow_m': r(top - fl_lo) if top is not None else None})
        ob_o = lo_w - dir_w * 0.01 + np.array([0, 0.03, 0])
        tob, pob = first_hit(court_parts + tparts, ob_o, dir_w, 6.0)
        # terrain directly under the channel high/low ends (city ground is drawn under the court)
        tpart_hi = terrain_near(hi_w[0] - 2, hi_w[0] + 2, hi_w[2] - 2, hi_w[2] + 2)
        yt_lo, _ = top_surface(tparts, lo_w[0], lo_w[2], 5)
        yt_hi, _ = top_surface(tpart_hi, hi_w[0], hi_w[2], 5)
        A['instances'].append({
            'cityNode': nid, 'asset': n['asset'], 'lod': lod, 'glb': 'docs/cities/luoyang/' + path, 'sha256': sha,
            'drainNode': d['node'], 'material': d['material'], 'excludeNodes': a.get('excludeNodes', []),
            'nodeMatrixColumnMajor': n.get('matrix'),
            'localAxis': d['axis'], 'length_m': r(d['length'], 3),
            'floorHigh_m': r(fl_hi), 'floorLow_m': r(fl_lo), 'fall_m': r(fl_hi - fl_lo),
            'slope_pct': r(100 * (fl_hi - fl_lo) / d['length'], 4),
            'rim_m': r(d['prof'][d['loEnd']]['rim']), 'slotWidth_m': r(walls[1] - walls[0], 3),
            'world': {'highEnd': [r(v, 3) for v in hi_w], 'lowEnd': [r(v, 3) for v in lo_w], 'flowDir': [r(v, 3) for v in dir_w]},
            'lowEndCappedOnDrainMesh': tcap is not None and tcap < 0.06, 'lowEndCapRay_t': r(tcap),
            'highEndCappedOnDrainMesh': tcap_hi is not None and tcap_hi < 0.06,
            'terrainUnderLowEnd_m': r(yt_lo), 'terrainUnderHighEnd_m': r(yt_hi),
            'spillBeyondLowEnd': spill,
            'firstObstructionDownstream': {'dist_m': r(tob, 3), 'part': pob},
        })
# LOD identity of drain geometry
lod_id = {}
for path, g in proto_cache.items():
    d = drain_local(g)
    lod_id[path] = hashlib.sha256(np.round(d['V'][d['F']], 5).tobytes()).hexdigest()[:16]
A['drainTriangleHashByGlb'] = lod_id
json.dump(A, open(os.path.join(OUT, 'A-city-drains.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- B. terrain fall statistics ----------
B = {'files': terrain_files, 'parts': []}
for name, T in terrain:
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    nrm = np.cross(e1, e2); area2 = np.linalg.norm(nrm, axis=1)
    keep = area2 > 1e-12
    nrm, area = nrm[keep], area2[keep] / 2
    ny = nrm[:, 1] / np.linalg.norm(nrm, axis=1)
    up = ny > 0.2
    grad = np.sqrt(np.maximum(0, 1 - ny[up] ** 2)) / np.abs(ny[up])  # rise/run of the facet
    au = area[up]; tot = au.sum()
    ys = np.round(T[keep][up][:, :, 1], 4)
    bins = [0, 1e-4, 1e-3, 5e-3, 1e-2, 2e-2, 5e-2, 0.2, 1.0, np.inf]
    hist = {}
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (grad >= lo) & (grad < hi)
        hist[f'{lo:g}-{hi:g}'] = r(au[m].sum() / tot, 5)
    # vertex-level local minima (strict) on the up-facing surface graph
    Vt = T[keep][up].reshape(-1, 3)
    key = np.round(Vt, 4)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    nb_min = np.full(len(uniq), np.inf)
    for i in range(3):
        for j in range(3):
            if i != j:
                np.minimum.at(nb_min, inv[:, i], uniq[inv[:, j], 1])
    smask = uniq[:, 1] < nb_min - 1e-4
    strict_min = int(smask.sum())
    minima_pts = [[r(v, 3) for v in q] + [r(nb - q[1], 4)] for q, nb in zip(uniq[smask], nb_min[smask])]
    B['parts'].append({'part': name, 'upFacingTris': int(up.sum()), 'upArea_m2': r(tot, 1),
                       'yValues': sorted(set(ys.reshape(-1).tolist()))[:12], 'yValueCount': int(len(set(ys.reshape(-1).tolist()))),
                       'gradientAreaFraction': hist, 'maxGradient': r(grad.max(), 5),
                       'strictLocalMinimaVertices': strict_min, 'minima_xyz_and_rimRise': minima_pts, 'uniqueVertices': int(len(uniq))})
json.dump(B, open(os.path.join(OUT, 'B-terrain-fall.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- C. palace waterway (library, not in city) ----------
WW = LAB + 'library/models/m-luoyang-palace-waterway-interface/files/'
C = {'note': 'local frame of the library GLBs; no city placement exists', 'lods': {}}
for f in ['palace-waterway-interface-near.glb', 'palace-waterway-interface-mid.glb', 'palace-waterway-interface-far.glb', 'palace-waterway-interface-inspection-near.glb']:
    g = G.load(WW + f)
    parts = [(nm, V[F]) for i, nm, mats, V, F in G.node_tris(g) if 'inspection_side' not in nm]
    Tall = np.vstack([T for _, T in parts])
    stations = []
    for x in np.round(np.arange(-3.25, 3.26, 0.25), 3):
        ys = vertical_hits(Tall, x, 0.0)
        ys = np.unique(np.round(ys, 4))
        # first air gap above the first solid = cavity floor (invert) / cavity roof
        gap = None
        if len(ys) >= 3:
            gap = [float(ys[1]), float(ys[2])]
        stations.append({'x': float(x), 'crossings': ys.tolist(), 'invert': r(gap[0]) if gap else None, 'roof': r(gap[1]) if gap else None})
    inv_pts = [(s['x'], s['invert']) for s in stations if s['invert'] is not None and abs(s['x']) > 0.8]
    # openings at both ends and continuity through the shaft: horizontal rays at mid cavity height along +/-x
    lo_in = [s for s in stations if s['x'] == -3.0][0]; lo_out = [s for s in stations if s['x'] == 3.0][0]
    res = {'sha256': g['sha256'], 'nodes': [p[0] for p in parts], 'stations': stations}
    for side, s, o_x, dx in (('inner_end_-x', lo_in, -3.0, -1), ('outer_end_+x', lo_out, 3.0, 1)):
        if s['invert'] is None:
            res[side] = None; continue
        y = (s['invert'] + s['roof']) / 2
        t_out, _ = ray_first(Tall, [o_x, y, 0], [dx, 0, 0], 5)
        t_in, _ = ray_first(Tall, [o_x, y, 0], [-dx, 0, 0], 8)
        res[side] = {'probeY': r(y), 'openToOutside': t_out is None, 'hitOutward_t': r(t_out), 'freeRunInward_m': r(t_in)}
    # inspection-near carries the segment nodes; record their bounds as ports
    w = {}
    for xs in (-2.0, 0.0, 2.0):
        tp, _ = ray_first(Tall, [xs, 0.3, 0], [0, 0, 1], 3); tn, _ = ray_first(Tall, [xs, 0.3, 0], [0, 0, -1], 3)
        w[str(xs)] = {'+z_t': r(tp), '-z_t': r(tn), 'width': r((tp or 0) + (tn or 0))}
    res['cavityWidthAtY0.3'] = w
    res['shaftCentreCrossings'] = vertical_hits(Tall, 0.0, 0.0).round(4).tolist()
    tu, _ = ray_first(Tall, [0, 0.3, 0], [0, 1, 0], 5)
    res['shaftOpenUpward'] = tu is None
    res['segmentBounds'] = {nm: [np.round(T.reshape(-1, 3).min(0), 3).tolist(), np.round(T.reshape(-1, 3).max(0), 3).tolist()] for nm, T in parts}
    C['lods'][f] = res
json.dump(C, open(os.path.join(OUT, 'C-palace-waterway.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- D. dependency candidates ----------
D = {}
ST = LAB + 'library/models/m-luoyang-stable/files/'
for f in ('A.glb', 'B.glb'):
    g = G.load(ST + f)
    for i, nm, mats, V, F in G.node_tris(g):
        if nm.endswith('_earth_platform'):
            top = V[:, 1].max(); tv = V[np.abs(V[:, 1] - top) < 1e-6]
            D['stable/' + f] = {'sha256': g['sha256'], 'node': nm, 'topY': r(top, 6), 'topVertexCount': int(len(tv)),
                                'topYSpread_m': r(tv[:, 1].max() - tv[:, 1].min(), 6), 'drainNodes': [n2 for _, n2, *_ in G.node_tris(g) if 'drain' in n2.lower()]}
KI = LAB + 'library/models/m-luoyang-tile-kiln/files/'
for f in ('kiln-A.glb', 'kiln-B.glb'):
    g = G.load(KI + f)
    names = [n.get('name', '') for n in g['json']['nodes']]
    D['kiln/' + f] = {'sha256': g['sha256'], 'nodeCount': len(names),
                      'drainLikeNodes': [x for x in names if any(k in x.lower() for k in ('drain', 'gutter', 'ditch', 'channel', 'water', 'sump', 'outlet'))]}
BY = 'D:/GitHub/creation-notebook-workpacks/LY-073/prep/_extract/city-visible/chunks/biyong_C_relationship.glb'
if os.path.exists(BY):
    g = G.load(BY)
    for i, nm, mats, V, F in G.node_tris(g):
        if 'water' in nm.lower():
            T = V[F]; c = (V.min(0) + V.max(0)) / 2
            ring = []
            ext = (V.max(0) - V.min(0))
            rmid = None
            for ang in np.arange(0, 360, 1.0):
                th = np.radians(ang)
                # sample along the ray from centre and record whether any water surface exists between r=60..90
                hit = False
                for rr in np.arange(60, 115, 0.5):
                    x, z = c[0] + rr * np.cos(th), c[2] + rr * np.sin(th)
                    if len(vertical_hits(T, x, z)):
                        hit = True; break
                ring.append(hit)
            D['biyong/' + nm] = {'glb': 'workpacks/LY-073/prep/_extract/city-visible/chunks/biyong_C_relationship.glb', 'sha256': g['sha256'],
                                 'bboxMin': np.round(V.min(0), 3).tolist(), 'bboxMax': np.round(V.max(0), 3).tolist(),
                                 'anglesWithWater_of360': int(sum(ring)), 'gapAngles': [int(a) for a, h in zip(range(360), ring) if not h][:20],
                                 'closedLoop': all(ring)}
json.dump(D, open(os.path.join(OUT, 'D-dependency-candidates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- summary ----------
print('A drains')
for it in A['instances']:
    sp = it['spillBeyondLowEnd']
    print(f"{it['cityNode']:14s} {it['lod']:9s} slope {it['slope_pct']}% low {it['world']['lowEnd']} dir {it['world']['flowDir']} capLow {it['lowEndCappedOnDrainMesh']} "
          f"terrainLow {it['terrainUnderLowEnd_m']} spill0.05 {sp[1]['stepFromFloorLow_m']} ({sp[1]['courtPart'] or sp[1]['terrainPart']}) spill1.0 {sp[5]['stepFromFloorLow_m']} obstr {it['firstObstructionDownstream']}")
print('drain tri hash', A['drainTriangleHashByGlb'])
print('B terrain')
for p in B['parts']:
    print(p['part'], p['upFacingTris'], p['upArea_m2'], p['yValueCount'], p['yValues'][:6], p['gradientAreaFraction'], p['maxGradient'], 'minima', p['strictLocalMinimaVertices'])
print('C waterway')
for f, res in C['lods'].items():
    inv = [(s['x'], s['invert'], s['roof']) for s in res['stations']]
    print(f, res['sha256'][:8], res.get('inner_end_-x'), res.get('outer_end_+x'))
    print('   ', inv)
print('D', json.dumps(D, ensure_ascii=False)[:1500])
