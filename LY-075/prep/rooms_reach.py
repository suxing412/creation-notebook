# LY-075 prep: nine-room / doorway / reachability survey from floor_map.py output.
# Usage: python rooms_reach.py <prefix-floor.npz> <out.json> [label] [sect.npz|-] [inject]
#   inject (negative-control only, never a deliverable): 'x0,z0,x1,z1;...' plan boxes (model-local metres)
#   treated as full-height solid obstacles AFTER room/door classification, so door ids stay stable.
# Frame: model-local glTF, +X = plan east, -Z = plan north (LY-005 planNotation, only valid if the
# model is later installed with yaw 0; installation yaw is NOT frozen). Metres.
# Method (all from vertical multi-hit ray columns at the npz grid step):
#  * floor Z and headroom C per column; platform level = modal floor height.
#  * rooms   = connected components of platform cells with C >= ROOM_C (door heads are lower, so
#              doorway cells separate rooms automatically).
#  * doors   = connected components of platform cells with DOOR_C_MIN <= C < ROOM_C; each door is
#              attributed to the regions its 1-cell dilation touches.
#  * reach   = BFS over body-centre cells: walkable (finite Z, C >= body height) and Euclidean
#              distance to the nearest non-walkable / void cell > body radius; 8-neighbour moves
#              allowed when |dZ| <= step. Seeds = lowest stair tread cells on each side.
# Limits: discrete column sampling (cell = grid step), cylinder body, no continuous motion, no
# dynamics, no structure. A door narrower than 2*radius + step can be missed or falsely closed
# within one cell; widths are reported so the margin is visible.
import sys, json, hashlib, numpy as np
from scipy import ndimage as ndi

ROOM_C = 2.6
DOOR_C_MIN = 1.0

def components(centre, Z, s):
    """8-neighbour connected components over centre cells with |dZ| <= s. Returns label grid (-1 = none)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    nx, nz = centre.shape
    idx = -np.ones(centre.shape, np.int64); ii, jj = np.nonzero(centre); idx[ii, jj] = np.arange(len(ii))
    rows, cols = [], []
    for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
        A = (slice(max(0, -di), nx - max(0, di)), slice(max(0, -dj), nz - max(0, dj)))
        B = (slice(max(0, di), nx - max(0, -di)), slice(max(0, dj), nz - max(0, -dj)))
        ok = centre[A] & centre[B] & (np.abs(Z[A] - Z[B]) <= s + 1e-6)
        rows.append(idx[A][ok]); cols.append(idx[B][ok])
    r = np.concatenate(rows); c = np.concatenate(cols)
    g = coo_matrix((np.ones(len(r)), (r, c)), shape=(len(ii), len(ii)))
    n, labs = connected_components(g, directed=False)
    out = -np.ones(centre.shape, np.int64); out[ii, jj] = labs
    return out

def main(npz, out, label, sect=None, inject=None):
    d = np.load(npz)
    Z, C, xs, zs, step = d['Z'], d['C'], d['xs'], d['zs'], float(d['step'])
    P = 50  # pad 2.5 m of void (synthetic ground) around the bbox so stair feet have run-out
    Z = np.pad(Z, P, constant_values=np.nan); C = np.pad(C, P, constant_values=0.0)
    xs = np.concatenate([xs[0] - step * np.arange(P, 0, -1), xs, xs[-1] + step * np.arange(1, P + 1)])
    zs = np.concatenate([zs[0] + (zs[1] - zs[0]) * np.arange(-P, 0), zs, zs[-1] + (zs[1] - zs[0]) * np.arange(1, P + 1)])
    # C assumption (not geometry): the GLB's min y is 0 and has no ground mesh; void columns are treated
    # as a synthetic flat ground at y = 0 with open sky so the stair foot can be entered. LY-074 owns the
    # real exterior ground; this only lets the interior survey start from outside the model.
    void = np.isnan(Z)
    SO, SH = None, None
    if sect:
        sd_ = np.load(sect); SO = np.pad(sd_['OBST'], ((0, 0), (P, P), (P, P)), constant_values=False); SH = sd_['heights']
        # cut lines lying on a face already caught by vertical rays fall into the neighbouring cell
        # (sub-cell rounding, <= 1 cell). Keep only section cells > 1 cell away from vertical-ray solids.
        vsolid = (~void) & (Z > np.nanmedian(Z[~void]) + 0.3)
        SO = SO & ~ndi.binary_dilation(vsolid, iterations=1)[None]
    Z = np.where(void, 0.0, Z); C = np.where(void, 99.0, C)
    fin = ~np.isnan(Z)
    vals, cnt = np.unique(np.round(Z[fin], 3), return_counts=True)
    plat = float(vals[np.argmax(cnt)])
    onplat = fin & (np.abs(Z - plat) < 2e-3)
    roomc = onplat & (C >= ROOM_C)
    doorc = onplat & (C >= DOOR_C_MIN) & (C < ROOM_C)
    lab, n = ndi.label(roomc)
    regions = []
    for k in range(1, n + 1):
        m = lab == k
        ii, jj = np.nonzero(m)
        x0, x1 = xs[ii].min() - step / 2, xs[ii].max() + step / 2
        z0, z1 = zs[jj].min() - step / 2, zs[jj].max() + step / 2
        area = m.sum() * step * step
        regions.append(dict(id=k, cells=int(m.sum()), area_m2=round(area, 3), x=[round(x0, 3), round(x1, 3)],
                            z=[round(z0, 3), round(z1, 3)], cx=float(xs[ii].mean()), cz=float(zs[jj].mean()),
                            headroom_min=round(float(C[m].min()), 3), headroom_med=round(float(np.median(C[m])), 3),
                            sky_cells=int((C[m] > 50).sum())))
    # name the nine rooms by a 3x3 grid of centroids; the largest non-rectangular region = veranda ring
    rect = [r for r in regions if r['cells'] > 100]
    interior = sorted(rect, key=lambda r: r['area_m2'], reverse=True)
    ring = None
    if interior and (interior[0]['x'][1] - interior[0]['x'][0]) > 25:
        ring = interior.pop(0); ring['name'] = 'veranda-ring'
    nine = interior[:9]
    if len(nine) == 9:
        xsort = sorted(set(round(r['cx'], 0) for r in nine)); zsort = sorted(set(round(r['cz'], 0) for r in nine))
        colname = {0: 'W', 1: 'C', 2: 'E'}; rowname = {0: 'N', 1: 'C', 2: 'S'}  # -z = north
        cx_sorted = sorted(nine, key=lambda r: r['cx'])
        for r in nine:
            ci = int(np.argsort([abs(r['cx'] - v) for v in sorted({round(q['cx'], 1) for q in nine})])[0])
            ri = int(np.argsort([abs(r['cz'] - v) for v in sorted({round(q['cz'], 1) for q in nine})])[0])
            r['grid'] = [ri, ci]
            r['name'] = ('room-' + rowname[ri] + colname[ci]).replace('room-CC', 'room-centre')
    for r in regions:
        r.setdefault('name', 'region-%d' % r['id'])
    names = {r['id']: r['name'] for r in regions}
    # sky / stairs regions for door attribution
    skyring = fin & (C > 50)
    stairs = (~void) & (~onplat) & (Z < plat)
    # doors
    dlab, dn = ndi.label(doorc)
    doors = []
    for k in range(1, dn + 1):
        m = dlab == k
        if m.sum() < 4:
            continue
        dil = ndi.binary_dilation(m, iterations=1)
        touch = sorted({names[int(v)] for v in np.unique(lab[dil & (lab > 0)])})
        if (dil & skyring).any(): touch.append('open-sky-edge')
        ii, jj = np.nonzero(m)
        ex = (xs[ii].max() - xs[ii].min()) + step; ez = (zs[jj].max() - zs[jj].min()) + step
        orient = 'wall-along-x' if ex > ez else 'wall-along-z'
        width = max(ex, ez); depth = min(ex, ez)
        doors.append(dict(id=k, connects=touch, orientation=orient, clear_width_m=round(float(width), 3),
                          wall_depth_m=round(float(depth), 3), head_clear_min=round(float(C[m].min()), 3),
                          head_clear_max=round(float(C[m].max()), 3), floor_min=round(float(Z[m].min()), 4),
                          floor_max=round(float(Z[m].max()), 4),
                          sill_height_above_room_m=round(float(Z[m].max() - plat), 4),
                          centre=[round(float(xs[ii].mean()), 3), round(float(zs[jj].mean()), 3)]))
    # reachability
    # seeds: synthetic-ground cells 1.5-2.0 m beyond each stair foot (stair = connected tread block)
    slab, sn = ndi.label(stairs)
    seeds = []
    for k in range(1, sn + 1):
        ii, jj = np.nonzero(slab == k)
        cx, cz = xs[ii].mean(), zs[jj].mean()
        side = 'N' if cz < -5 else 'S' if cz > 5 else 'W' if cx < -5 else 'E'
        far = ndi.distance_transform_edt(~(slab == k)) * step
        seeds.append(dict(side=side, mask=void & (far > 1.5) & (far <= 2.0) & (np.abs(xs[:, None] - cx) < 3.0 if side in 'NS' else np.abs(zs[None, :] - cz) < 3.0)))
    INJ = np.zeros(Z.shape, bool); inj_boxes = []
    if inject:
        for part in inject.split(';'):
            x0, z0, x1, z1 = [float(v) for v in part.split(',')]
            inj_boxes.append([x0, z0, x1, z1])
            INJ |= ((xs[:, None] >= min(x0, x1)) & (xs[:, None] <= max(x0, x1)) & (zs[None, :] >= min(z0, z1)) & (zs[None, :] <= max(z0, z1)))
    results = []
    # positive grid + three negative controls (must fail): head above lintel, body wider than door, step below riser
    configs = [(H, r, s) for H in (1.75, 2.0, 2.3) for r in (0.0, 0.25, 0.30, 0.45) for s in (0.16, 0.20)]
    configs += [(2.40, 0.25, 0.20), (1.75, 1.15, 0.20), (1.75, 0.25, 0.14)]
    for (H, r, s) in configs:
        if True:
            if True:
                walk = fin & (C >= H) & (Z <= plat + 0.30)  # synthetic ground walkable; wall tops / roofs are obstacles
                walk &= ~INJ  # negative-control obstacle boxes (empty unless inject given)
                if SO is not None:  # horizontal-section members (uncapped posts etc.) on the platform level only
                    secblk = SO[SH <= H + 1e-9].any(0) & onplat
                    walk &= ~secblk
                # unguarded edges (|dZ| > 0.5 m between neighbours, e.g. platform rim, stair sides) count as
                # obstacles for the body envelope so a centre may not hang over a drop
                mx = ndi.maximum_filter(np.where(walk, Z, -1e9), size=3); mn = ndi.minimum_filter(np.where(walk, Z, 1e9), size=3)
                edge = walk & ((mx - Z > 0.5) | (Z - mn > 0.5))
                dist = ndi.distance_transform_edt(walk & ~edge) * step
                centre = walk & (dist > r + 1e-9) if r > 0 else walk & ~edge
                # 8-neighbour BFS with step limit
                reach_any = np.zeros_like(centre)
                per_seed = {}
                comp = components(centre, Z, s)
                for sd in seeds:
                    ids = np.unique(comp[sd['mask'] & centre]); ids = ids[ids >= 0]
                    seen = np.isin(comp, ids) & centre
                    per_seed[sd['side']] = sorted({names[int(v)] for v in np.unique(lab[seen & (lab > 0)])})
                    reach_any |= seen
                # per-door direct passage: body centres inside (room a U door U room b) only
                door_pass = {}
                for dd in doors:
                    m = (dlab == dd['id'])
                    union = m.copy()
                    for nm in dd['connects']:
                        if nm == 'open-sky-edge':
                            union |= skyring
                        else:
                            union |= (lab == [k for k, v in names.items() if v == nm][0])
                    sub = centre & union
                    cl, _ = ndi.label(sub, structure=np.ones((3, 3)))
                    sides = []
                    for nm in dd['connects']:
                        mm = skyring if nm == 'open-sky-edge' else (lab == [k for k, v in names.items() if v == nm][0])
                        sides.append(set(np.unique(cl[mm & sub]).tolist()) - {0})
                    ok = len(sides) == 2 and len(sides[0] & sides[1]) > 0
                    door_pass[dd['id']] = 'pass' if ok else 'blocked'
                if (H, r, s) == (2.0, 0.25, 0.20):
                    ref_reach = reach_any.copy(); ref_centre = centre.copy()
                rooms_reached = sorted({names[int(v)] for v in np.unique(lab[reach_any & (lab > 0)])})
                unreached = sorted(r_['name'] for r_ in nine if r_['name'] not in rooms_reached)
                results.append(dict(body_height_m=H, body_radius_m=r, max_step_m=s, seeds=[sd['side'] for sd in seeds],
                                    per_seed=per_seed, rooms_reached=rooms_reached, rooms_unreached=unreached,
                                    seed_cells_valid={sd['side']: int((sd['mask'] & centre).sum()) for sd in seeds}, door_pass=door_pass))
    sect_info = None
    if SO is not None:
        allob = SO.any(0) & onplat
        per_room = {}
        for r_ in nine + ([ring] if ring else []):
            m = (lab == r_['id']) & allob
            per_room[r_['name']] = dict(cells=int(m.sum()), area_m2=round(float(m.sum() * step * step), 4))
        sect_info = dict(file=sect, sha256=hashlib.sha256(open(sect, 'rb').read()).hexdigest(), heights=SH.tolist(),
                         blocked_cells_inside_regions_missed_by_vertical_rays=per_room)
    res = dict(label=label, section=sect_info, npz=npz, npz_sha256=hashlib.sha256(open(npz, 'rb').read()).hexdigest(), grid_step_m=step,
               platform_floor_y=plat, stair_tread_levels=sorted({round(float(v), 3) for v in np.unique(Z[stairs])}) if stairs.any() else [],
               regions=[{k: v for k, v in r.items()} for r in regions if r['cells'] > 20],
               nine_rooms_found=len(nine), veranda=ring, doors=doors, reach=results)
    if inj_boxes: res['injected_obstacles'] = dict(boxes_xz=inj_boxes, cells=int(INJ.sum()), note='negative control on measurement copy only')
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    # reference reachability map (H 2.0 m, radius 0.25 m, step 0.20 m): image top = -Z (plan north), right = +X
    from PIL import Image, ImageDraw
    img = np.full(Z.shape + (3,), 245, np.uint8)
    img[(~void) & (Z > plat + 0.3)] = (45, 45, 45)
    img[(~void) & onplat & ~ref_centre] = (205, 205, 205)
    img[stairs & ~ref_centre] = (190, 170, 220)
    img[ref_reach & onplat] = (110, 175, 110)
    img[ref_reach & stairs] = (150, 120, 200)
    img[ref_reach & void] = (200, 225, 245)
    img[(dlab > 0) & ref_reach] = (230, 160, 40)
    im = Image.fromarray(np.transpose(img, (1, 0, 2))[::-1]).resize((Z.shape[0] * 2, Z.shape[1] * 2), Image.NEAREST)
    dr = ImageDraw.Draw(im)
    def px(x, z):
        i = np.argmin(abs(xs - x)); j = np.argmin(abs(zs - z)); return (2 * i, 2 * (Z.shape[1] - 1 - j))
    for r_ in nine: dr.text(px(r_['cx'] - 1.2, r_['cz']), r_['name'].replace('room-', ''), fill=(0, 0, 0))
    for dd in doors: dr.text(px(dd['centre'][0] + 0.3, dd['centre'][1] + 0.3), 'D%d' % dd['id'], fill=(120, 40, 0))
    dr.text((8, 8), label + '  H2.0 r0.25 step0.20  top=-Z(plan N)  green=reached body centres', fill=(0, 0, 0))
    im.save(out.replace('.json', '-map.png'))
    print(label, 'plat', plat, 'regions', n, 'nine', len(nine), 'doors', len(doors))
    if sect_info: print('  section-only blocked cells in regions', sect_info['blocked_cells_inside_regions_missed_by_vertical_rays'])
    for dd in doors:
        print('  door', dd['connects'], dd['orientation'], 'w', dd['clear_width_m'], 'd', dd['wall_depth_m'], 'head', dd['head_clear_min'], dd['head_clear_max'], 'sill', dd['sill_height_above_room_m'])
    for rr in results:
        print('  H%.2f r%.2f s%.2f reached %d/9 unreached %s seeds %s doors_blocked %s' % (rr['body_height_m'], rr['body_radius_m'], rr['max_step_m'], 9 - len(rr['rooms_unreached']), rr['rooms_unreached'], rr['seed_cells_valid'], [k for k, v in rr['door_pass'].items() if v != 'pass']))

if __name__ == '__main__':
    a = sys.argv
    main(a[1], a[2], a[3] if len(a) > 3 else '', (a[4] if len(a) > 4 and a[4] != '-' else None), a[5] if len(a) > 5 else None)
