# LY-045 prep: can the existing 圈厕关系 A be installed in a candidate 44-yard lot, and what real ground lies
# under its floor hole?  Read-only on inputs.  NOT a delivery placement: candidate poses only.
# python -I measure_yard_fit.py <lab_root> <prep_dir> <out.json>
# Axes glTF, metres, world = city frame (city-data matrices applied).  0.1 m grid, surface rasters only:
# NOT solid collision, NOT gait, NOT structure/sanitation.
import sys, os, json
import numpy as np
from scipy import ndimage, signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glbio
from PIL import Image

LAB, PREP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CITY = os.path.join(LAB, 'docs/cities/luoyang')
SC = os.path.join(LAB, 'docs/library/models/m-luoyang-service-court/files/service-A-LOD0.glb')
H = 0.1
BAND = 0.03          # yard geometry higher than ground + 3 cm blocks a cell (any height: the service court is 4.23 m tall)
ROUTE_HALF = 0.45    # C corridor half-width, same as LY-044 prep
EXCL = ['site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground']
GROUNDS = {'ground-south': 'assets/ground-atomic/south.glb', 'ground-retained': 'assets/ground-atomic/retained.glb',
           'ground-network': 'assets/ground-atomic/network-ground-stitched.glb', 'ground-D08': 'assets/ground-atomic/D08.glb'}
GROUND_POS = {'ground-D08': [580, 0, -960]}  # LY-041: D08 single translation; others at origin
YARDS = {
    'C02-010': {'asset': 'assets/c02v/A2-LOD0-prototype.glb', 'matrix': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 531, 0, -818.45, 1]},
    'C02-021': {'asset': 'assets/c02v/A2-LOD0-prototype.glb', 'matrix': [0, 0, 1.0, 0, 0, 1, 0, 0, -1.0, 0, 0, 0, 717.45, 0, -893.64308, 1]},
}
LOCAL_ROUTES = {"gate_to_main": [[-3.5, -15], [-3.5, -7], [0, -4], [0.6, 2.8], [0.6, 5.25]], "yard_to_side": [[0.6, 0.6], [-4.4, 0.6]]}
# NOTE layout.json localRoutes are in the layout frame (x, y_north); LY-044 converted them with z = -y.
# Service-court functional features in model-local glTF coords (from measure-service-court.json, LOD0=LOD1=LOD2)
PEN_C, PEN_RIN, PEN_ROUT = (0.0, -0.0013), 2.4987, 2.8012
HOLE = {'x': [-0.21, 0.21], 'z': [-2.47, -2.05]}
APRONS = {'stairFoot': {'x': [3.75, 4.95], 'z': [-4.0, -3.0]},      # 1.2 m run-out in front of the 1.0 m wide stair foot
          'penGap': {'x': [-0.6, 0.6], 'z': [2.85, 3.85]}}         # 1.0 m in front of the 1.2 m clear gap (+z)


def M4(m):
    return glbio.col_major(m)


def xform(t, M):
    v = t.reshape(-1, 3); p = np.c_[v, np.ones(len(v))] @ M.T
    return p[:, :3].reshape(-1, 3, 3)


def rot_y(deg):
    r = np.radians(deg); c, s = np.cos(r), np.sin(r)
    M = np.eye(4); M[0, 0] = c; M[0, 2] = s; M[2, 0] = -s; M[2, 2] = c
    return M


def clip(t, x0, z0, x1, z1):
    lo = t.min(1); hi = t.max(1)
    return t[(hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 2] >= z0) & (lo[:, 2] <= z1)]


def rect_mask(x0, z0, nx, nz, rx, rz):
    gx = x0 + (np.arange(nx) + 0.5) * H; gz = z0 + (np.arange(nz) + 0.5) * H
    X, Z = np.meshgrid(gx, gz)
    return (X >= rx[0]) & (X <= rx[1]) & (Z >= rz[0]) & (Z <= rz[1])


def seg_mask(x0, z0, nx, nz, pts, half):
    gx = x0 + (np.arange(nx) + 0.5) * H; gz = z0 + (np.arange(nz) + 0.5) * H
    X, Z = np.meshgrid(gx, gz); m = np.zeros_like(X, bool)
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        dx, dz = bx - ax, bz - az; L2 = dx * dx + dz * dz
        u = np.clip(((X - ax) * dx + (Z - az) * dz) / L2, 0, 1)
        m |= np.hypot(X - (ax + u * dx), Z - (az + u * dz)) <= half
    return m


sc_nodes = glbio.nodes_tris(SC)
sc_all = np.concatenate(list(sc_nodes.values()))
ground_tris = {}
for gid, rel in GROUNDS.items():
    p = os.path.join(CITY, rel)
    root = np.eye(4)
    if gid in GROUND_POS:
        root[:3, 3] = GROUND_POS[gid]
    ground_tris[gid] = (np.concatenate(list(glbio.nodes_tris(p, root).values())), glbio.sha256(p))

out = {'tool': 'LY-045 measure_yard_fit.py', 'grid_m': H, 'bandAboveGround_m': BAND, 'routeHalfWidth_m': ROUTE_HALF,
       'serviceCourt': {'file': os.path.relpath(SC, LAB).replace('\\', '/'), 'sha256': glbio.sha256(SC)},
       'grounds': {k: v[1] for k, v in ground_tris.items()}, 'yards': {}}

for yid, Y in YARDS.items():
    ap = os.path.join(CITY, Y['asset'])
    MY = M4(Y['matrix'])
    nodes = glbio.nodes_tris(ap, MY)
    kept = np.concatenate([t for k, t in nodes.items() if k not in EXCL])
    lotloc = np.array([[-9, 0, -12, 1], [9, 0, -12, 1], [9, 0, 12, 1], [-9, 0, 12, 1]], float) @ MY.T
    lx0, lx1 = lotloc[:, 0].min(), lotloc[:, 0].max(); lz0, lz1 = lotloc[:, 2].min(), lotloc[:, 2].max()
    nx, nz = int(round((lx1 - lx0) / H)), int(round((lz1 - lz0) / H))
    # ground per supplier
    gtop = np.full((nz, nx), -np.inf); gsup = {}
    for gid, (gt, _) in ground_tris.items():
        t = clip(gt, lx0, lz0, lx1, lz1)
        tp, _, _ = glbio.raster(t, lx0, lz0, H, nx, nz)
        gsup[gid] = int(np.isfinite(tp).sum()); gtop = np.maximum(gtop, tp)
    hasg = np.isfinite(gtop)
    ktop, kbot, _ = glbio.raster(kept, lx0, lz0, H, nx, nz, edge_step=0.02)
    blocked = np.isfinite(ktop) & (ktop > np.where(hasg, gtop, 0.2) + BAND)
    bad = blocked | ~hasg
    # routes (layout local (x, yN) -> glTF local (x, -yN) -> world)
    routes = {}
    for k, pts in LOCAL_ROUTES.items():
        P = np.array([[x, 0, -yn, 1] for x, yn in pts], float) @ MY.T
        routes[k] = P[:, [0, 2]].tolist()
    route = np.zeros((nz, nx), bool)
    for pts in routes.values():
        route |= seg_mask(lx0, lz0, nx, nz, pts, ROUTE_HALF)
    yrec = {'lot_world': {'x': [round(lx0, 3), round(lx1, 3)], 'z': [round(lz0, 3), round(lz1, 3)]}, 'cells': int(nx * nz),
            'groundSupplierCells': gsup, 'groundCells': int(hasg.sum()),
            'groundTop_min_max': [round(float(gtop[hasg].min()), 5), round(float(gtop[hasg].max()), 5)] if hasg.any() else None,
            'blockedCells_anyHeight': int(blocked.sum()), 'openSkyGroundCells': int((~bad).sum()),
            'openSkyNonRouteCells': int((~bad & ~route).sum()), 'routesWorldXZ': routes, 'poses': {}}
    # free-space components (open sky, not route)
    lab, nl = ndimage.label(~bad & ~route)
    comps = []
    for i in range(1, nl + 1):
        m = lab == i; jj, ii = np.nonzero(m)
        comps.append({'area_m2': round(float(m.sum() * H * H), 2), 'x': [round(lx0 + ii.min() * H, 2), round(lx0 + (ii.max() + 1) * H, 2)],
                      'z': [round(lz0 + jj.min() * H, 2), round(lz0 + (jj.max() + 1) * H, 2)]})
    comps.sort(key=lambda c: -c['area_m2'])
    yrec['openSkyNonRouteComponents'] = comps[:6]
    dist_bad = ndimage.distance_transform_edt(~bad) * H
    yrec['maxInscribedRadius_openSky_m'] = round(float(dist_bad.max()), 2)
    yrec['serviceCourtNeedsDisc_r'] = round(PEN_ROUT, 3)
    best_all = []
    masks_by_rot = {}
    for rot in (0, 90, 180, 270):
        R = rot_y(rot)
        t = xform(sc_all, R)
        v = t.reshape(-1, 3)
        fx0 = np.floor(v[:, 0].min() / H) * H - H; fz0 = np.floor(v[:, 2].min() / H) * H - H
        fnx = int(np.ceil((v[:, 0].max() - fx0) / H)) + 2; fnz = int(np.ceil((v[:, 2].max() - fz0) / H)) + 2
        tp, _, _ = glbio.raster(t, fx0, fz0, H, fnx, fnz, edge_step=0.02)
        occ = np.isfinite(tp)
        # pen interior disc (open-sky inside the ring) also belongs to the installation
        gx = fx0 + (np.arange(fnx) + 0.5) * H; gz = fz0 + (np.arange(fnz) + 0.5) * H
        X, Z = np.meshgrid(gx, gz)
        Xl = X * np.cos(np.radians(rot)) - Z * np.sin(np.radians(rot)); Zl = X * np.sin(np.radians(rot)) + Z * np.cos(np.radians(rot))
        occ |= np.hypot(Xl - PEN_C[0], Zl - PEN_C[1]) <= PEN_ROUT
        apr = np.zeros_like(occ)
        for a in APRONS.values():
            apr |= (Xl >= a['x'][0]) & (Xl <= a['x'][1]) & (Zl >= a['z'][0]) & (Zl <= a['z'][1])
        apr &= ~occ
        masks_by_rot[rot] = None
        holeM = (Xl >= HOLE['x'][0]) & (Xl <= HOLE['x'][1]) & (Zl >= HOLE['z'][0]) & (Zl <= HOLE['z'][1])
        masks_by_rot[rot] = (occ, apr, holeM, fx0, fz0)
        # correlation: overlap counts for every offset (valid mode)
        def corr(A, K):
            return np.rint(signal.fftconvolve(A.astype(float), K[::-1, ::-1].astype(float), mode='valid')).astype(int)
        if occ.shape[0] > nz or occ.shape[1] > nx:
            yrec['poses'][str(rot)] = {'valid': 0, 'reason': 'footprint larger than lot'}
            continue
        ov_bad = corr(bad, occ); ov_route = corr(route, occ); ap_bad = corr(bad, apr)
        bad_d3 = ndimage.binary_dilation(bad, iterations=3)  # 0.3 m clearance
        ov_bad3 = corr(bad_d3, occ)
        ok = (ov_bad == 0) & (ov_route == 0) & (ap_bad == 0)
        ok3 = ok & (ov_bad3 == 0)
        rec = {'valid_noRoute_apronsFree': int(ok.sum()), 'valid_plus0.3mClearance': int(ok3.sum()),
               'tested': int(ov_bad.size), 'footprintOccupied_m2': round(float(occ.sum() * H * H), 2)}
        # connectivity: aprons must reach a route corridor through open ground for the best poses
        cand = np.argwhere(ok3 if ok3.any() else ok)
        scored = []
        for (j, i) in cand:
            sub = np.zeros((nz, nx), bool); sub[j:j + occ.shape[0], i:i + occ.shape[1]] = occ
            d = float(dist_bad[j:j + occ.shape[0], i:i + occ.shape[1]][occ].min())
            scored.append((d, j, i))
        scored.sort(reverse=True)
        checked = []
        for d, j, i in scored[:40]:
            sub = np.zeros((nz, nx), bool); sub[j:j + occ.shape[0], i:i + occ.shape[1]] = occ
            apw = np.zeros((nz, nx), bool); apw[j:j + occ.shape[0], i:i + occ.shape[1]] = apr
            free = ~bad & ~sub
            lb, _ = ndimage.label(free)
            ids_route = set(np.unique(lb[route & free])) - {0}
            reach = {}
            for an, a in APRONS.items():
                am = np.zeros_like(occ)
                am |= (Xl >= a['x'][0]) & (Xl <= a['x'][1]) & (Zl >= a['z'][0]) & (Zl <= a['z'][1])
                am &= ~occ
                aw = np.zeros((nz, nx), bool); aw[j:j + occ.shape[0], i:i + occ.shape[1]] = am
                reach[an] = bool(set(np.unique(lb[aw])) & ids_route)
            tx = lx0 + i * H - fx0; tz = lz0 + j * H - fz0
            hw = np.zeros((nz, nx), bool); hw[j:j + occ.shape[0], i:i + occ.shape[1]] = holeM
            checked.append({'translation_xz': [round(float(tx), 3), round(float(tz), 3)], 'rotY_deg': rot,
                            'minDistToBlocked_m': round(d, 2), 'apronsReachRoute': reach,
                            'holeGroundTop': [round(float(gtop[hw].min()), 5), round(float(gtop[hw].max()), 5)] if hw.any() else None})
            if len(checked) >= 5 and all(c['apronsReachRoute'].values() for c in checked[:1]):
                break
        rec['bestPoses'] = checked[:5]
        yrec['poses'][str(rot)] = rec
        best_all += [c for c in checked if all(c['apronsReachRoute'].values())]
    best_all.sort(key=lambda c: -c['minDistToBlocked_m'])
    yrec['representativePose'] = best_all[0] if best_all else None
    # ---- ground under the hole at the representative pose ------------------------------------------
    if best_all:
        P = best_all[0]
        MW = np.eye(4); MW[:3, 3] = [P['translation_xz'][0], 0, P['translation_xz'][1]]
        MW = MW @ rot_y(P['rotY_deg'])
        hc = np.array([[x, 0, z, 1] for x in HOLE['x'] for z in HOLE['z']], float) @ MW.T
        hx0, hx1, hz0, hz1 = hc[:, 0].min(), hc[:, 0].max(), hc[:, 2].min(), hc[:, 2].max()
        under = {}
        for gid, (gt, _) in ground_tris.items():
            t = clip(gt, hx0, hz0, hx1, hz1)
            if len(t):
                e = np.linalg.norm(t[:, [1, 2, 0]] - t, axis=2)
                under[gid] = {'trisTouchingHoleRect': int(len(t)), 'yRange': [round(float(t[:, :, 1].min()), 4), round(float(t[:, :, 1].max()), 4)],
                              'edgeLen_m_min_median_max': [round(float(e.min()), 3), round(float(np.median(e)), 3), round(float(e.max()), 3)]}
                w = clip(gt, hx0 - 1, hz0 - 1, hx1 + 1, hz1 + 1)
                under[gid]['trisWithin1mOfHole'] = int(len(w))
                under[gid]['nodeTrisTotal'] = int(len(gt))
        exres = {}
        for k in EXCL:
            t = clip(nodes[k], hx0, hz0, hx1, hz1)
            if len(t):
                exres[k] = {'tris': int(len(t)), 'yRange': [round(float(t[:, :, 1].min()), 4), round(float(t[:, :, 1].max()), 4)]}
        keptunder = clip(kept, hx0, hz0, hx1, hz1)
        # world matrix of the representative pose, with y set to the ground top 0.2 (model y=0 is its ground contact)
        gy = P['holeGroundTop'][1] if P['holeGroundTop'] else 0.2
        MWy = MW.copy(); MWy[1, 3] = gy
        yrec['holeAtRepresentativePose'] = {
            'worldRect': {'x': [round(float(hx0), 3), round(float(hx1), 3)], 'z': [round(float(hz0), 3), round(float(hz1), 3)]},
            'groundUnder': under, 'excludedPrototypeNodesUnder_if_exclusion_dropped': exres,
            'keptYardTrisUnder': int(len(keptunder)),
            'floorTopWorldY': round(1.4 + gy, 4), 'dropFloorTopToGround_m': round(1.4, 4),
            'candidateMatrix_colMajor': [round(float(x), 6) for x in MWy.T.reshape(-1)]}
    if best_all:
        P = best_all[0]; occ, apr, holeM, fx0, fz0 = masks_by_rot[P['rotY_deg']]
        i = int(round((P['translation_xz'][0] + fx0 - lx0) / H)); j = int(round((P['translation_xz'][1] + fz0 - lz0) / H))
        img = np.full((nz, nx, 3), 255, np.uint8)
        img[route] = (170, 170, 170); img[bad] = (40, 40, 40)
        for m, col in ((occ, (200, 60, 60)), (apr, (60, 90, 210)), (holeM, (40, 180, 60))):
            w = np.zeros((nz, nx), bool); w[j:j + m.shape[0], i:i + m.shape[1]] = m; img[w] = col
        im = Image.fromarray(img).resize((nx * 3, nz * 3), Image.NEAREST)
        fn = 'fit-%s.png' % yid; im.save(os.path.join(PREP, fn))
        yrec['previewPNG'] = {'file': fn, 'rows': 'z ascending top->bottom', 'cols': 'x ascending', 'px_per_cell': 3,
                              'legend': 'black blocked/no ground, grey route corridor, red service-court occupied (incl. pen disc), blue access aprons, green floor-hole projection',
                              'note': 'candidate pose only, CPU raster, not a delivery placement'}
    out['yards'][yid] = yrec

json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for yid, y in out['yards'].items():
    print(yid, {k: y[k] for k in ['groundSupplierCells', 'groundTop_min_max', 'blockedCells_anyHeight', 'openSkyNonRouteCells', 'maxInscribedRadius_openSky_m']})
    print('  comps', y['openSkyNonRouteComponents'][:3])
    for r, p in y['poses'].items():
        print('  rot', r, {k: v for k, v in p.items() if k != 'bestPoses'}, (p.get('bestPoses') or [None])[0])
    print('  rep', y.get('representativePose'))
    print('  hole', json.dumps(y.get('holeAtRepresentativePose'), ensure_ascii=False))
