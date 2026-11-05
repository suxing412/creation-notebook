# LY-045 prep: measure the existing 圈厕关系 A (m-luoyang-service-court) GLBs. Read-only on inputs.
# python -I measure_service_court.py <lab_root> <out.json>     (numpy + scipy; Blender cross-check: blender_crosscheck.py)
# Axes: glTF (x right, y up, z toward viewer = local south). Metres. Model origin as exported.
# Scope: surface rasters / vertical + horizontal ray probes on the exported triangles.
#   NOT solid collision, NOT gait/body simulation, NOT structure, NOT sanitation.
import sys, os, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio

LAB, OUT = sys.argv[1], sys.argv[2]
LIB = os.path.join(LAB, 'docs/library/models/m-luoyang-service-court/files')
FILES = ['service-A-LOD0.glb', 'service-A-LOD1.glb', 'service-A-LOD2.glb']
EPS = 1e-4


def tri_normals(t):
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    a = np.linalg.norm(n, axis=1)
    return n / (a[:, None] + 1e-15), a / 2


def ray_hits_vertical(tris, x, z):
    """All y where a vertical line (x,z) crosses the triangles (barycentric, edges inclusive)."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    d = (b[:, 0] - a[:, 0]) * (c[:, 2] - a[:, 2]) - (c[:, 0] - a[:, 0]) * (b[:, 2] - a[:, 2])
    ok = np.abs(d) > 1e-12
    l1 = ((b[:, 0] - x) * (c[:, 2] - z) - (c[:, 0] - x) * (b[:, 2] - z)) / np.where(ok, d, 1)
    l2 = ((c[:, 0] - x) * (a[:, 2] - z) - (a[:, 0] - x) * (c[:, 2] - z)) / np.where(ok, d, 1)
    l3 = 1 - l1 - l2
    m = ok & (l1 >= -1e-9) & (l2 >= -1e-9) & (l3 >= -1e-9)
    return np.sort(l1[m] * a[m, 1] + l2[m] * b[m, 1] + l3[m] * c[m, 1])


def components(m):
    lab, n = ndimage.label(m)
    return lab, n


def fit_circle(xz):
    A = np.c_[2 * xz[:, 0], 2 * xz[:, 1], np.ones(len(xz))]
    bb = (xz ** 2).sum(1)
    cx, cz, k = np.linalg.lstsq(A, bb, rcond=None)[0]
    return cx, cz


def measure(path):
    d = glbio.nodes_tris(path)
    rec = {'file': os.path.relpath(path, LAB).replace('\\', '/'), 'sha256': glbio.sha256(path),
           'bytes': os.path.getsize(path), 'nodes': {}}
    allt = np.concatenate(list(d.values()))
    for k, t in d.items():
        v = t.reshape(-1, 3)
        rec['nodes'][k] = {'tris': int(len(t)), 'bboxMin': np.round(v.min(0), 4).tolist(), 'bboxMax': np.round(v.max(0), 4).tolist()}
    V = allt.reshape(-1, 3)
    rec['bboxMin'] = np.round(V.min(0), 4).tolist(); rec['bboxMax'] = np.round(V.max(0), 4).tolist()
    rec['finite'] = bool(np.isfinite(V).all())

    # ---- 1. privy floor + hole ------------------------------------------------------------
    tim = d['service-A-static_timber']; n, a = tri_normals(tim)
    fl = tim[(n[:, 1] > 0.99) & (np.abs(tim[:, :, 1].mean(1) - 1.4) < 1e-3)]
    fv = fl.reshape(-1, 3)
    fx0, fz0, fx1, fz1 = fv[:, 0].min(), fv[:, 2].min(), fv[:, 0].max(), fv[:, 2].max()
    h = 0.005
    nx, nz = int(round((fx1 - fx0) / h)), int(round((fz1 - fz0) / h))
    top, _, _ = glbio.raster(fl, fx0, fz0, h, nx, nz)
    filled = np.isfinite(top)
    lab, nlab = components(~filled)
    holes = []
    for i in range(1, nlab + 1):
        m = lab == i
        jj, ii = np.nonzero(m)
        border = jj.min() == 0 or ii.min() == 0 or jj.max() == nz - 1 or ii.max() == nx - 1
        if border or m.sum() < 4:
            continue
        hx0, hx1 = fx0 + ii.min() * h, fx0 + (ii.max() + 1) * h
        hz0, hz1 = fz0 + jj.min() * h, fz0 + (jj.max() + 1) * h
        holes.append({'x': [round(hx0, 4), round(hx1, 4)], 'z': [round(hz0, 4), round(hz1, 4)],
                      'area_m2': round(float(m.sum() * h * h), 4)})
    # exact hole edges from floor vertices inside the floor bbox interior
    rec['privyFloor'] = {'topY': 1.4, 'bbox_x': [round(fx0, 4), round(fx1, 4)], 'bbox_z': [round(fz0, 4), round(fz1, 4)],
                         'topArea_m2': round(float(a[(n[:, 1] > 0.99) & (np.abs(tim[:, :, 1].mean(1) - 1.4) < 1e-3)].sum()), 4),
                         'holes': holes, 'raster_m': h}
    # floor underside / thickness at a solid floor point and around hole
    if holes:
        H = holes[0]
        hcx, hcz = (H['x'][0] + H['x'][1]) / 2, (H['z'][0] + H['z'][1]) / 2
        H['centre'] = [round(hcx, 4), round(hcz, 4)]
        # vertical probes through the hole: everything below 1.4 within the model
        g = np.linspace(0.1, 0.9, 5)
        probes = []
        for fxs in g:
            for fzs in g:
                x = H['x'][0] + fxs * (H['x'][1] - H['x'][0]); z = H['z'][0] + fzs * (H['z'][1] - H['z'][0])
                ys = ray_hits_vertical(allt, x, z)
                probes.append([round(x, 3), round(z, 3), [round(float(y), 4) for y in ys]])
        H['verticalProbes_allNodes'] = probes
        H['modelHitsBelowFloorUnderside_1.25'] = sum(1 for p in probes for y in p[2] if y < 1.25 - 1e-4)
        H['modelHitsAboveFloor'] = sum(1 for p in probes for y in p[2] if y > 1.4 + 1e-4)
        H['probeCount'] = len(probes)
        H['dropToModelGround_m'] = 1.4  # floor top to y=0 (model has no ground surface; see groundSurfaceInModel)
        # hole lining: timber/earth tris that are vertical and lie on hole edges
        side = tim[(np.abs(n[:, 1]) < 0.01)]
        sv = side.reshape(-1, 3)
        inb = (sv[:, 0] > H['x'][0] - 0.02) & (sv[:, 0] < H['x'][1] + 0.02) & (sv[:, 2] > H['z'][0] - 0.02) & (sv[:, 2] < H['z'][1] + 0.02)
        H['liningY'] = [round(float(sv[inb, 1].min()), 4), round(float(sv[inb, 1].max()), 4)] if inb.any() else None
    # floor underside y at floor centre
    ys = ray_hits_vertical(tim, (fx0 + fx1) / 2 + 0.6, (fz0 + fz1) / 2)
    rec['privyFloor']['probeAtSolidPoint'] = [round(float(y), 4) for y in ys]

    # ---- 2. ground surface inside the model? -------------------------------------------------
    n_all, a_all = tri_normals(allt)
    gup = (n_all[:, 1] > 0.99) & (allt[:, :, 1].max(1) < 0.02)
    rec['groundSurfaceInModel'] = {'upFacingTrisAtY0': int(gup.sum()), 'area_m2': round(float(a_all[gup].sum()), 4)}
    gdn = (n_all[:, 1] < -0.99) & (allt[:, :, 1].max(1) < 1e-3)
    rec['bottomContact'] = {'downFacingTrisAtY0': int(gdn.sum()), 'area_m2': round(float(a_all[gdn].sum()), 4),
                            'byNode': {}}
    for k, t in d.items():
        nn, aa = tri_normals(t)
        m = (nn[:, 1] < -0.99) & (t[:, :, 1].max(1) < 1e-3)
        rec['bottomContact']['byNode'][k] = {'tris': int(m.sum()), 'area_m2': round(float(aa[m].sum()), 4),
                                            'minY': round(float(t[:, :, 1].min()), 5)}

    # ---- 3. pen ring ----------------------------------------------------------------------------
    ear = d['service-A-static_earth']; ne, ae = tri_normals(ear)
    ringtop = ear[(ne[:, 1] > 0.99) & (np.abs(ear[:, :, 1].mean(1) - 0.95) < 1e-3)]
    rv = np.unique(np.round(ringtop.reshape(-1, 3), 5), axis=0)
    cx, cz = fit_circle(rv[:, [0, 2]])
    r = np.hypot(rv[:, 0] - cx, rv[:, 2] - cz)
    rin, rout = float(r.min()), float(r.max())
    ang = np.degrees(np.arctan2(rv[:, 2] - cz, rv[:, 0] - cx)) % 360
    s = np.sort(ang); gaps = np.diff(np.r_[s, s[0] + 360])
    gi = int(np.argmax(gaps))
    g0, g1 = s[gi], (s[gi] + gaps[gi]) % 360
    # clear gap width: min distance between ring-wall vertices on the two sides of the gap (all heights 0..0.95)
    ringall = ear[(ear[:, :, 1].max(1) <= 0.951)]
    rav = np.unique(np.round(ringall.reshape(-1, 3), 5), axis=0)
    rr = np.hypot(rav[:, 0] - cx, rav[:, 2] - cz)
    rav = rav[(rr > rin - 0.01) & (rr < rout + 0.01)]
    aa_ = np.degrees(np.arctan2(rav[:, 2] - cz, rav[:, 0] - cx)) % 360
    near0 = rav[np.abs(((aa_ - g0) + 180) % 360 - 180) < 3]; near1 = rav[np.abs(((aa_ - g1) + 180) % 360 - 180) < 3]
    clear = float(np.min(np.linalg.norm(near0[:, None, [0, 2]] - near1[None, :, [0, 2]], axis=2))) if len(near0) and len(near1) else None
    gmid = np.radians((g0 + gaps[gi] / 2) % 360)
    rec['penRing'] = {'centre_xz': [round(cx, 4), round(cz, 4)], 'innerR': round(rin, 4), 'outerR': round(rout, 4),
                      'wallThickness': round(rout - rin, 4), 'earthTopY': 0.95,
                      'capTopY': round(float(d['service-A-static_tile'][(d['service-A-static_tile'][:, :, 1].max(1) < 1.2)][:, :, 1].max()), 4)
                      if (d['service-A-static_tile'][:, :, 1].max(1) < 1.2).any() else None,
                      'gapAngle_deg': [round(float(g0), 2), round(float(g1), 2)], 'gapSpan_deg': round(float(gaps[gi]), 2),
                      'gapMidDir_xz': [round(float(np.cos(gmid)), 4), round(float(np.sin(gmid)), 4)],
                      'gapClearWidth_m': round(clear, 4) if clear is not None else None,
                      'innerArea_m2_disc': round(float(np.pi * rin * rin), 3)}
    if holes:
        H = holes[0]
        dist = float(np.hypot(H['centre'][0] - cx, H['centre'][1] - cz))
        corners = [(x, z) for x in H['x'] for z in H['z']]
        rec['penRing']['holeCentreDistFromRingCentre'] = round(dist, 4)
        rec['penRing']['holeFullyInsideInnerR'] = bool(all(np.hypot(x - cx, z - cz) < rin for x, z in corners))

    # ---- 4. stair treads + landing ----------------------------------------------------------------
    ups = ear[(ne[:, 1] > 0.99)]
    levels = {}
    for y in sorted(set(np.round(ups[:, :, 1].mean(1), 3))):
        t = ups[np.abs(ups[:, :, 1].mean(1) - y) < 1e-3]
        v = t.reshape(-1, 3)
        levels[float(y)] = {'x': [round(float(v[:, 0].min()), 4), round(float(v[:, 0].max()), 4)],
                            'z': [round(float(v[:, 2].min()), 4), round(float(v[:, 2].max()), 4)],
                            'area_m2': round(float(ae[(ne[:, 1] > 0.99)][np.abs(ups[:, :, 1].mean(1) - y) < 1e-3].sum()), 4)}
    stair = {k: v for k, v in levels.items() if 0.1 < k < 1.45 and abs(k - 0.95) > 1e-3}
    ys = sorted(stair)
    risers = [round(ys[0], 4)] + [round(ys[i] - ys[i - 1], 4) for i in range(1, len(ys))]
    goings = []
    for i in range(1, len(ys)):
        a0, a1 = stair[ys[i - 1]], stair[ys[i]]
        goings.append(round(abs(a1['x'][0] - a0['x'][0]) if abs(a1['x'][0] - a0['x'][0]) > 1e-3 else abs(a1['z'][0] - a0['z'][0]), 4))
    rec['stair'] = {'levels': {str(k): v for k, v in stair.items()}, 'riserSequence_fromGround': risers,
                    'goingSequence': goings, 'treadCount': len(ys) - 1, 'landingY': ys[-1]}
    st = stair[ys[0]]
    rec['stair']['footTread_x'] = st['x']; rec['stair']['footTread_z'] = st['z']
    rec['stair']['width_m'] = round(st['z'][1] - st['z'][0], 4)

    # ---- 5. privy door on the stair side (+x wall) ---------------------------------------------
    # project tris with x in a slab around the privy +x wall onto (z, y) and find the uncovered opening
    wallx = fx1
    slab = allt[(allt[:, :, 0].min(1) >= wallx - 0.35) & (allt[:, :, 0].max(1) <= wallx + 0.12)]
    perm = slab[:, :, [2, 0, 1]].copy()  # raster "x"=z, "z"=y
    perm = np.stack([slab[:, :, 2], slab[:, :, 0], slab[:, :, 1]], axis=2)
    hz = 0.01
    z0w, z1w, y0w, y1w = fz0 - 0.05, fz1 + 0.05, 1.3, 3.6
    nxw, nyw = int((z1w - z0w) / hz), int((y1w - y0w) / hz)
    topw, _, _ = glbio.raster(perm, z0w, y0w, hz, nxw, nyw)
    cov = np.isfinite(topw)
    lab, nl = components(~cov)
    door = None
    for i in range(1, nl + 1):
        m = lab == i; jj, ii = np.nonzero(m)
        if jj.min() == 0 or ii.min() == 0 or ii.max() == nxw - 1 or jj.max() == nyw - 1:
            # openings touching bottom (floor level) are fine; touching sides are outside the wall
            if ii.min() == 0 or ii.max() == nxw - 1 or jj.max() == nyw - 1:
                continue
        area = m.sum() * hz * hz
        if area < 0.3:
            continue
        cand = {'z': [round(z0w + ii.min() * hz, 3), round(z0w + (ii.max() + 1) * hz, 3)],
                'y': [round(y0w + jj.min() * hz, 3), round(y0w + (jj.max() + 1) * hz, 3)], 'area_m2': round(float(area), 3)}
        if door is None or cand['area_m2'] > door['area_m2']:
            door = cand
    if door:
        door['width_m'] = round(door['z'][1] - door['z'][0], 3)
        door['clearHeightAboveFloor_m'] = round(door['y'][1] - 1.4, 3)
        door['wallPlaneX'] = round(float(wallx), 4)
        # horizontal ray through door centre along -x at y 1.9: hits
        zc = (door['z'][0] + door['z'][1]) / 2
        door['centreZ'] = round(zc, 3)
    rec['privyDoor_plusX'] = door
    lv = stair[ys[-1]]
    rec['stair']['landingOverlapsDoorZ'] = bool(door and lv['z'][0] <= door['z'][0] + 1e-3 and lv['z'][1] >= door['z'][1] - 1e-3) if door else None
    rec['stair']['landingInnerX'] = lv['x'][0]

    # ---- 6. headroom inside the privy (floor 1.4 to lowest geometry above) ---------------------
    hr = []
    for x in np.linspace(fx0 + 0.25, fx1 - 0.25, 7):
        for z in np.linspace(fz0 + 0.25, fz1 - 0.25, 9):
            ys_ = ray_hits_vertical(allt, x, z)
            above = ys_[ys_ > 1.41]
            if len(above):
                hr.append(float(above.min()) - 1.4)
    rec['privyHeadroom_m'] = {'min': round(min(hr), 3), 'max': round(max(hr), 3), 'samples': len(hr)} if hr else None

    # ---- 7. under-floor clearance inside the pen (ground 0 to privy floor underside) ----------
    und = ray_hits_vertical(tim, (fx0 + fx1) / 2, (fz0 + fz1) / 2 + 0.6)
    rec['underFloorClear_m'] = round(float(und[und > 0.01].min()), 4) if (und > 0.01).any() else None

    # ---- 8. raised components (vertex-welded): bottom-face support check -----------------------
    # For every welded component whose lowest vertex is above y=0, sample its downward faces at its
    # lowest level on a 0.02 m raster and look for any other geometry top within +-5 mm right below.
    flo = []
    for k, t in d.items():
        v = np.round(t.reshape(-1, 3), 5)
        uv, inv = np.unique(v, axis=0, return_inverse=True)
        inv = inv.reshape(-1, 3)
        parent = np.arange(len(uv))

        def f(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]; i = parent[i]
            return i
        for a_, b_, c_ in inv:
            ra = f(a_); parent[f(b_)] = ra; parent[f(c_)] = ra
        roots = np.array([f(i) for i in range(len(uv))])
        comp = roots[inv[:, 0]]
        for cid in np.unique(comp):
            ct = t[comp == cid]
            miny = float(ct[:, :, 1].min())
            if miny < 1e-3:
                continue
            rest = np.concatenate([tt for kk, tt in d.items() if kk != k] + [t[comp != cid]])
            nn, aa = tri_normals(ct)
            botm = (nn[:, 1] < -0.99) & (np.abs(ct[:, :, 1].mean(1) - miny) < 1e-3)
            nr, _ = tri_normals(rest)
            upm = (nr[:, 1] > 0.99) & (np.abs(rest[:, :, 1].mean(1) - miny) <= 0.005)
            bb = ct.reshape(-1, 3)
            hx0, hz0 = bb[:, 0].min() - 0.02, bb[:, 2].min() - 0.02
            gnx = int(np.ceil((bb[:, 0].max() - hx0 + 0.02) / 0.01)); gnz = int(np.ceil((bb[:, 2].max() - hz0 + 0.02) / 0.01))
            if botm.any():
                t1, _, _ = glbio.raster(ct[botm], hx0, hz0, 0.01, gnx, gnz)
                t2, _, _ = glbio.raster(rest[upm], hx0, hz0, 0.01, gnx, gnz) if upm.any() else (np.full((gnz, gnx), -np.inf), 0, 0)
                ov = float((np.isfinite(t1) & np.isfinite(t2)).sum() * 1e-4); ba = float(np.isfinite(t1).sum() * 1e-4)
            else:
                ov, ba = 0.0, 0.0
            flo.append({'node': k, 'tris': int(len(ct)), 'minY': round(miny, 4),
                        'bbox': [np.round(bb.min(0), 3).tolist(), np.round(bb.max(0), 3).tolist()],
                        'horizontalBottomArea_m2': round(ba, 4), 'bottomOnUpFaceWithin5mm_m2': round(ov, 4),
                        'samplesSupportedWithin5mm': 1 if ov > 0 else 0})
    rec['raisedComponents'] = flo
    rec['raisedComponentsNoBottomSupport'] = [c for c in flo if c['samplesSupportedWithin5mm'] == 0]

    # ---- 9. plan footprint mask (0.1 m) for placement search ---------------------------------------
    hh = 0.1
    bx0, bz0 = V[:, 0].min() - 0.2, V[:, 2].min() - 0.2
    nxx, nzz = int(np.ceil((V[:, 0].max() - bx0 + 0.2) / hh)), int(np.ceil((V[:, 2].max() - bz0 + 0.2) / hh))
    tp, _, _ = glbio.raster(allt, bx0, bz0, hh, nxx, nzz, edge_step=0.02)
    fm = np.isfinite(tp)
    rec['footprint'] = {'cell_m': hh, 'origin_xz': [round(float(bx0), 4), round(float(bz0), 4)], 'shape_zx': [int(nzz), int(nxx)],
                        'area_m2_cells': round(float(fm.sum() * hh * hh), 2)}
    return rec, fm


out = {'tool': 'LY-045 measure_service_court.py', 'scope': 'surface raster + ray probes on exported GLB triangles; not solid collision, gait, structure or sanitation',
       'lods': {}}
masks = {}
for f in FILES:
    r, fm = measure(os.path.join(LIB, f))
    out['lods'][f] = r
    masks[f] = fm
    np.save(os.path.join(os.path.dirname(OUT), 'footprint-' + f.replace('.glb', '.npy')), fm)
# LOD consistency on the functional numbers
keys = ['privyFloor', 'penRing', 'stair', 'privyDoor_plusX']
cons = {}
L0 = out['lods'][FILES[0]]
for f in FILES[1:]:
    Lx = out['lods'][f]
    cons[f] = {k: (json.dumps(L0.get(k, {}).get('holes') if k == 'privyFloor' else L0.get(k), sort_keys=True) ==
                   json.dumps(Lx.get(k, {}).get('holes') if k == 'privyFloor' else Lx.get(k), sort_keys=True)) for k in keys}
out['lodConsistencyVsLOD0'] = cons
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({f: {k: out['lods'][f].get(k) for k in ['privyFloor', 'penRing', 'stair', 'privyDoor_plusX', 'privyHeadroom_m', 'underFloorClear_m', 'groundSurfaceInModel', 'raisedComponentsNoBottomSupport']} for f in FILES[:1]}, ensure_ascii=False, indent=1)[:9000])
print(json.dumps(cons))
