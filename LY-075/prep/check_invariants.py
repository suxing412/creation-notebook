# LY-075 prep: executable acceptance checks T1-T9, P1-P2, N1-N3 (test-plan.md) over rooms_reach.py output.
# Read-only on every input. Usage:
#   python check_invariants.py --expect A|B --reach out/A0-reach.json out/A1-reach.json out/A2-reach.json \
#          --floor out/A0-floor.npz out/A1-floor.npz out/A2-floor.npz --posts out/posts.log \
#          [--glb <LOD0.glb> <LOD1.glb> <LOD2.glb>] --out out/check-A.json
# Exit 0 only if every check passes. N5 (A/B mix-up) = run --expect A on B files and require exit 1.
import argparse, hashlib, json, re, sys
import numpy as np
from scipy import ndimage as ndi

EXPECT = {
    # post_door_min: post centre to nearest door-jamb line end, design value minus one grid cell
    # (A: 8 - 4 - 1.10 = 2.90; B: 7 - 3.5 - 1.00 = 2.50)
    'A': dict(post_door_min=2.85, room=7.75, door_w=2.20, plat=1.200, treads=[0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05], post=(4.0, 12.0),
              glb={'LOD0': 'bdcc369e765df692b755c2987053d56df5d859964d982fab41f55c535e716ee2',
                   'LOD1': '993ec375a777d825bdf39a680ea689576c33a6b50fcfbc804b55ec22dca086a9',
                   'LOD2': '275f8fe20f2e6f1d1a0ea0066447f25431e67fba2323ab3ffe76a9d1d1417cda'}),
    'B': dict(post_door_min=2.45, room=6.75, door_w=2.00, plat=0.900, treads=[0.15, 0.3, 0.45, 0.6, 0.75], post=(3.5, 10.5),
              glb={'LOD0': '7337871c488c3695bfea2c12a45ac5ad31a16512955726d5380cb797cd98dda3',
                   'LOD1': '25035eeb0583bcae69137867d466dc3ad238747b1173c8e043f338c35b43b62e',
                   'LOD2': 'd495219cb6bcf99655a5ab793ad1743c84b4c453b24f50d40c958a6fce987102'}),
}
TOL_W, TOL_H, TOL_Z, TOL_POS = 0.05, 0.005, 0.002, 0.01
HEAD, DEPTH, STAIR_W = 2.35, 0.25, 4.20
KEY10 = None  # set below
NAMES9 = ['room-NW', 'room-NC', 'room-NE', 'room-CW', 'room-centre', 'room-CE', 'room-SW', 'room-SC', 'room-SE']
GRID = {n: (i // 3, i % 3) for i, n in enumerate(NAMES9)}
POS = [(H, r, s) for H in (1.75, 2.0, 2.3) for r in (0.0, 0.25, 0.30, 0.45) for s in (0.16, 0.20)]
KEY10 = set(NAMES9) | {'veranda-ring'}
NEG = {'N1': (2.40, 0.25, 0.20), 'N2': (1.75, 1.15, 0.20), 'N3': (1.75, 0.25, 0.14)}

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def stairs_from_floor(npz, plat):
    d = np.load(npz); Z, xs, zs, step = d['Z'], d['xs'], d['zs'], float(d['step'])
    st = np.isfinite(Z) & (Z < plat - 1e-3)
    lab, n = ndi.label(st)
    out = []
    for k in range(1, n + 1):
        ii, jj = np.nonzero(lab == k)
        if len(ii) < 50: continue
        ex = xs[ii].max() - xs[ii].min() + step; ez = abs(zs[jj].max() - zs[jj].min()) + step
        ns = abs(zs[jj].mean()) > abs(xs[ii].mean())  # N/S stair: lateral = x extent, run = z extent
        out.append(dict(cx=round(float(xs[ii].mean()), 3), cz=round(float(zs[jj].mean()), 3),
                        width=round(float(ex if ns else ez), 3), run=round(float(ez if ns else ex), 3),
                        levels=sorted({round(float(v), 3) for v in Z[ii, jj]})))
    return out

def parse_posts(path):
    cur, res = None, {}
    for line in open(path, encoding='utf-8'):
        m = re.match(r'(\S+\.glb) (\S+) components', line)
        if m:
            cur = (m.group(1), m.group(2)); res.setdefault(cur, []); continue
        m = re.match(r'\s+x (\S+) z (\S+) diam (\S+) y (\S+)\.\.(\S+)', line)
        if m and cur: res[cur].append(tuple(float(v) for v in m.groups()))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--expect', required=True, choices=['A', 'B'])
    ap.add_argument('--reach', nargs=3, required=True)
    ap.add_argument('--floor', nargs=3, required=True)
    ap.add_argument('--posts', required=True)
    ap.add_argument('--glb', nargs=3)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    E = EXPECT[a.expect]
    checks = []
    def chk(cid, lod, ok, detail):
        checks.append(dict(id=cid, lod=lod, result='pass' if ok else 'FAIL', detail=detail))
    bound = {}
    if a.glb:
        for lod, g in zip(('LOD0', 'LOD1', 'LOD2'), a.glb):
            h = sha(g); bound[lod] = dict(glb=g, sha256=h)
            chk('T0-sha', lod, h == E['glb'][lod], dict(got=h, want=E['glb'][lod]))
    summ = {}
    for lod, rp, fp in zip(('LOD0', 'LOD1', 'LOD2'), a.reach, a.floor):
        R = json.load(open(rp, encoding='utf-8'))
        bound.setdefault(lod, {}).update(reach=rp, reach_sha256=sha(rp), floor=fp, floor_sha256=sha(fp))
        rooms = {r['name']: r for r in R['regions'] if r['name'] in NAMES9}
        chk('T1', lod, R['nine_rooms_found'] == 9 and sorted(rooms) == sorted(NAMES9) and R['veranda'] is not None,
            dict(found=R['nine_rooms_found'], names=sorted(rooms)))
        dims = {n: (round(r['x'][1] - r['x'][0], 3), round(r['z'][1] - r['z'][0], 3)) for n, r in rooms.items()}
        chk('T2', lod, all(abs(w - E['room']) <= TOL_W and abs(d - E['room']) <= TOL_W for w, d in dims.values()),
            dict(want=E['room'], tol=TOL_W, got=dims))
        doors = R['doors']
        inner, outer = set(), set()
        for d in doors:
            c = d['connects']
            if 'veranda-ring' in c:
                outer.add([x for x in c if x != 'veranda-ring'][0] if len(c) == 2 else tuple(c))
            elif len(c) == 2 and all(x in GRID for x in c):
                (r1, c1), (r2, c2) = GRID[c[0]], GRID[c[1]]
                if abs(r1 - r2) + abs(c1 - c2) == 1: inner.add(tuple(sorted(c)))
        want_inner = {tuple(sorted((p, q))) for p in NAMES9 for q in NAMES9
                      if p < q and abs(GRID[p][0] - GRID[q][0]) + abs(GRID[p][1] - GRID[q][1]) == 1}
        chk('T3', lod, len(doors) == 16 and inner == want_inner and outer == {'room-NC', 'room-SC', 'room-CW', 'room-CE'},
            dict(doors=len(doors), inner=len(inner), outer=sorted(map(str, outer))))
        bad4 = [d['id'] for d in doors if not (abs(d['clear_width_m'] - E['door_w']) <= TOL_W and abs(d['wall_depth_m'] - DEPTH) <= TOL_W
                                                and abs(d['head_clear_min'] - HEAD) <= TOL_H and abs(d['head_clear_max'] - HEAD) <= TOL_H)]
        chk('T4', lod, not bad4, dict(want=dict(w=E['door_w'], depth=DEPTH, head=HEAD), bad_doors=bad4,
                                      widths=sorted({d['clear_width_m'] for d in doors}), heads=sorted({d['head_clear_min'] for d in doors})))
        bad5 = [d['id'] for d in doors if not (abs(d['sill_height_above_room_m']) <= TOL_Z and abs(d['floor_min'] - E['plat']) <= TOL_Z
                                                and abs(d['floor_max'] - E['plat']) <= TOL_Z)]
        chk('T5', lod, not bad5, dict(bad_doors=bad5, sills=sorted({d['sill_height_above_room_m'] for d in doors})))
        chk('T6', lod, abs(R['platform_floor_y'] - E['plat']) <= TOL_Z, dict(got=R['platform_floor_y'], want=E['plat']))
        st = stairs_from_floor(fp, R['platform_floor_y'])
        lv_ok = len(R['stair_tread_levels']) == len(E['treads']) and all(abs(p - q) <= TOL_Z for p, q in zip(R['stair_tread_levels'], E['treads']))
        chk('T7', lod, lv_ok and len(st) == 4 and all(abs(s['width'] - STAIR_W) <= TOL_W for s in st),
            dict(levels=R['stair_tread_levels'], want_levels=E['treads'], stairs=[{k: s[k] for k in ('cx', 'cz', 'width', 'run')} for s in st]))
        # reachability
        rr = {(x['body_height_m'], x['body_radius_m'], x['max_step_m']): x for x in R['reach']}
        p1 = [k for k in POS if not all(KEY10 <= set(v) for v in rr[k]['per_seed'].values()) or sorted(rr[k]['per_seed']) != ['E', 'N', 'S', 'W']]
        extra = sorted({n for k in POS for v in rr[k]['per_seed'].values() for n in v} - KEY10)
        chk('P1', lod, not p1, dict(configs=len(POS), failing=p1, extra_sliver_regions_reached=extra))
        p2 = [k for k in POS if any(v != 'pass' for v in rr[k]['door_pass'].values()) or len(rr[k]['door_pass']) != 16]
        chk('P2', lod, not p2, dict(configs=len(POS), failing=p2))
        for nid, k in NEG.items():
            x = rr[k]; nb = sum(v != 'pass' for v in x['door_pass'].values())
            nr = len(set(x['rooms_reached']) & set(NAMES9))
            ok = nr == 0 and (nb == 16 if nid in ('N1', 'N2') else True)
            chk(nid, lod, ok, dict(config=k, rooms_reached=nr, veranda_reached='veranda-ring' in x['rooms_reached'], doors_blocked=nb))
        chk('N6-info', lod, R['section'] is not None, dict(note='section file used' if R['section'] else 'vertical rays only: post sides NOT checked'))
        summ[lod] = dict(rooms=dims, doors=sorted((tuple(sorted(d['connects'])), d['clear_width_m'], d['head_clear_min'], d['sill_height_above_room_m']) for d in doors),
                         plat=R['platform_floor_y'], treads=R['stair_tread_levels'],
                         reach={str(k): sorted(set(rr[k]['rooms_reached']) & KEY10) for k in POS + list(NEG.values())},
                         doorpass={str(k): rr[k]['door_pass'] for k in POS + list(NEG.values())})
    # T8 posts (LOD0 and LOD2 listed in posts.log); door edges from LOD0 doors
    P = parse_posts(a.posts)
    R0 = json.load(open(a.reach[0], encoding='utf-8'))
    for lod, idx in (('LOD0', 0), ('LOD1', 1), ('LOD2', 2)):
        g = a.glb[idx].replace('\\', '/').split('/')[-1] if a.glb else 'mingtang-%s-%s.glb' % (a.expect, lod)
        posts = [p for (gn, node), ps in P.items() if gn == g and 'timber' in node for p in ps]
        u, v = E['post']; want = sorted((sx * p, sz * q) for p in (u, v) for q in (u, v) for sx in (-1, 1) for sz in (-1, 1))
        got = sorted((p[0], p[1]) for p in posts)
        pos_ok = len(got) == 16 and all(abs(x - X) <= TOL_POS and abs(z - Zz) <= TOL_POS for (x, z), (X, Zz) in zip(got, want))
        dmin = 1e9
        for d in R0['doors']:
            cx, cz = d['centre']; hw = d['clear_width_m'] / 2
            ends = [(cx - hw, cz), (cx + hw, cz)] if d['orientation'] == 'wall-along-x' else [(cx, cz - hw), (cx, cz + hw)]
            for (x, z) in got:
                for (ex, ez) in ends: dmin = min(dmin, ((x - ex) ** 2 + (z - ez) ** 2) ** 0.5)
        chk('T8', lod, pos_ok and dmin >= E['post_door_min'], dict(posts=len(got), want_grid=E['post'], min_post_to_door_edge_m=round(dmin, 3), want_min=E['post_door_min'], source=g))
    # T9 three-LOD equality of T1-T7 + reach sets
    diffs = {l: sorted(k for k in summ['LOD0'] if summ[l][k] != summ['LOD0'][k]) for l in ('LOD1', 'LOD2')}
    chk('T9', 'all', not any(diffs.values()), dict(fields_differing_from_LOD0=diffs))
    fails = [c for c in checks if c['result'] == 'FAIL' and not c['id'].endswith('-info')]
    rep = dict(tool='LY-075 check_invariants.py', expect=a.expect, bound=bound, checks=checks,
               verdict='pass' if not fails else 'FAIL', failing=[(c['id'], c['lod']) for c in fails],
               scope='model-readable + local passage only (0.05 m grid, cylinder body, 8-neighbour); not city install, not structure, not history')
    json.dump(rep, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for c in checks: print(c['id'], c['lod'], c['result'])
    print('VERDICT', rep['verdict'], rep['failing'])
    sys.exit(0 if not fails else 1)

if __name__ == '__main__':
    main()
