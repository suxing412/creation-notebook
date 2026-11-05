# LY-084 prep: screen three reconstructed north-east long-connection candidates
# (R1/R2/R3) against the geometry the city actually loads, plus the frozen B
# evidence layer. Read-only: imports GLBs, writes one JSON report, never exports.
#
#   blender -b --factory-startup --python-exit-code 1 -P measure_routes.py -- \
#       <lab_root> <city-nodes-ne.json> <northeast_C_access.glb> <out.json>
#
# Frame: Blender glTF import gives native Z-up metres (x east, y north, z up),
# the same frame as evidence-geometry.json (luoyang-local-schematic-v01) and the
# mother source-node-manifest. City node `position` is glTF (X, Y-up, Z=-north)
# and is converted once: native = (px, -pz, py).
#
# What this is NOT: no continuous body / cart sweep, no solid-volume collision
# (surface BVH + bbox containment only), no structural or historical claim.
import bpy, sys, json, math, hashlib, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
lab, nodes_p, road_p, out_p = argv[:4]
LUO = os.path.join(lab, 'docs', 'cities', 'luoyang')

STEP = 1.0          # m along centreline
W_ROAD = 3.0        # width of the existing C_NE_APPROACH_LOCAL strip
W_NET = 6.0         # width of the current 6 m network
CLEAR_Z = (0.25, 2.5)  # clearance prism above ground (ground tops are 0..0.21)
RAY_Z = 40.0


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def load(path, t_native=(0, 0, 0)):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    roots = [o for o in bpy.data.objects if o not in before and o.parent is None]
    for r in roots:
        r.location = Vector(r.location) + Vector(t_native)
    bpy.context.view_layer.update()
    return objs


def tris_of(objs):
    verts, tris, owner = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        base = len(verts)
        M = o.matrix_world
        verts.extend([M @ v.co for v in me.vertices])
        for t in me.loop_triangles:
            tris.append(tuple(base + i for i in t.vertices))
            owner.append(o.name)
        ev.to_mesh_clear()
    return verts, tris, owner


class Layer:
    def __init__(self, name, objs):
        self.name = name
        self.objs = objs
        self.v, self.t, self.owner = tris_of(objs)
        self.bvh = BVHTree.FromPolygons(self.v, self.t) if self.t else None

    def bbox(self):
        if not self.v:
            return None
        return [[round(min(p[i] for p in self.v), 4) for i in range(3)],
                [round(max(p[i] for p in self.v), 4) for i in range(3)]]


bpy.ops.wm.read_factory_settings(use_empty=True)
cn = json.load(open(nodes_p, encoding='utf-8'))
rep = {'frame': 'native Z-up metres (x east, y north, z up) = evidence-geometry frame',
       'params': {'step_m': STEP, 'w_road': W_ROAD, 'w_net': W_NET, 'clear_z': CLEAR_Z},
       'inputs': {}, 'layers': {}}

ground_layers, obstacle_objs = {}, []
taicang_ground, storage_obst = [], []
for n in cn['nodes']:
    p = os.path.join(LUO, n['sourcePath'])
    px, py, pz = n.get('position') or [0, 0, 0]
    objs = load(p, (px, -pz, py))
    rep['inputs'][n['id']] = {'path': 'docs/cities/luoyang/' + n['sourcePath'], 'sha256': sha(p),
                             'expected_sha256': n['sha256'], 'objects': sorted(o.name for o in objs),
                             'native_translation': [px, -pz, py]}
    if n['id'].startswith('ground-'):
        ground_layers[n['id']] = objs
    elif n['id'] == 'storage-main':
        for o in objs:
            (taicang_ground if 'ground' in o.name.lower() else storage_obst).append(o)
    else:
        obstacle_objs.extend(objs)
road = load(road_p)
rep['inputs']['ne-road-chunk'] = {'path': 'zip:chunks/northeast_C_access.glb', 'sha256': sha(road_p),
                                  'objects': [o.name for o in road], 'in_city': False}

L = {}
L['network'] = Layer('network', ground_layers['ground-network-ground-stitched'])
L['ground_other'] = Layer('ground_other', ground_layers['ground-retained'] + ground_layers['ground-south'] + ground_layers['ground-D08'])
L['taicang_ground'] = Layer('taicang_ground', taicang_ground)
L['ne_road'] = Layer('ne_road', road)
L['obstacles'] = Layer('obstacles', obstacle_objs + storage_obst)
for k, l in L.items():
    rep['layers'][k] = {'objects': sorted(set(l.owner)), 'triangles': len(l.t), 'bbox': l.bbox()}
GROUND_ORDER = ['ne_road', 'taicang_ground', 'network', 'ground_other']


def ground_hit(x, y, skip=()):
    best = None
    for k in GROUND_ORDER:
        if k in skip or L[k].bvh is None:
            continue
        loc, nrm, idx, dist = L[k].bvh.ray_cast(Vector((x, y, RAY_Z)), Vector((0, 0, -1)), RAY_Z + 5)
        if loc is not None and (best is None or loc.z > best[1]):
            best = (k, loc.z)
    return best


# ---------- evidence (frozen B) ----------
ev = json.load(open(os.path.join(LUO, 'data', 'evidence', 'evidence-geometry.json'), encoding='utf-8'))
F = {f['id']: f for f in ev['features']}


def coords(fid):
    g = F[fid]['geometry']
    return g['coordinates'] if g else None


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def poly_dist(p, pts):
    return min(seg_dist(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def inside(p, ring):
    x, y = p; c = False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i], ring[i + 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def line_intersect(a, b, c, d):
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a, b, c, d
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


NEGL = coords('road_northeast_gate_link_B')          # [(1724.49,2622.449),(2479.592,2591.837)]
ENL = coords('road_east_north_link_B')               # gu gate -> ... -> (1826.531,1816.327)
X0 = 2316.327                                        # wuku B x / stub centre x
p_r1_ne = line_intersect((X0, 3484.5), (X0, 0), NEGL[0], NEGL[1])
p_ne_enl = line_intersect(NEGL[0], NEGL[1], ENL[2], ENL[3])

CANDIDATES = {
    'R1': {'label': 'direct C corridor south from stub, no B parent line (the ~1.7 km option)',
           'parent_B': [], 'pts': [(X0, 3484.5), (X0, 1700.0)]},
    'R2': {'label': 'stub south to road_northeast_gate_link_B, west along it, south along road_east_north_link_B',
           'parent_B': ['road_northeast_gate_link_B', 'road_east_north_link_B'],
           'pts': [(X0, 3484.5), p_r1_ne, p_ne_enl, tuple(ENL[3])]},
    'R3': {'label': 'west from road east-leg end to road_east_north_link_B vertex, then south along it',
           'parent_B': ['road_east_north_link_B'],
           'pts': [(2284.214, 3486.0), tuple(ENL[2]), tuple(ENL[3])]},
}


def stations(pts):
    out, s0 = [], 0.0
    for i in range(len(pts) - 1):
        a, b = Vector((*pts[i], 0)), Vector((*pts[i + 1], 0))
        seg = b - a; ln = seg.length; d = seg.normalized(); n = Vector((-d.y, d.x, 0))
        k = 0
        while k * STEP < ln - 1e-9:
            p = a + d * (k * STEP)
            out.append((s0 + k * STEP, p.x, p.y, d, n, i))
            k += 1
        s0 += ln
    last = Vector((*pts[-1], 0)); d = (last - Vector((*pts[-2], 0))).normalized()
    out.append((s0, last.x, last.y, d, Vector((-d.y, d.x, 0)), len(pts) - 2))
    return out


def march(pts, w, skip=(), stop_on_network=True):
    rows, contact = [], None
    offs = [-w / 2 + 0.05, 0.0, w / 2 - 0.05]
    for s, x, y, d, n, seg in stations(pts):
        hits = [ground_hit(x + o * n.x, y + o * n.y, skip) for o in offs]
        cats = [h[0] if h else None for h in hits]
        zs = [h[1] if h else None for h in hits]
        rows.append({'s': round(s, 3), 'x': round(x, 3), 'y': round(y, 3), 'cats': cats,
                     'z': [None if z is None else round(z, 4) for z in zs]})
        if stop_on_network and all(c == 'network' for c in cats) and s > 0:
            contact = rows[-1]
            break
    return rows, contact


def summarise(rows, contact):
    supp, unsup, longest, run = {}, 0.0, 0.0, 0.0
    first_unsup = None
    for i, r in enumerate(rows[:-1] if len(rows) > 1 else rows):
        ds = rows[i + 1]['s'] - r['s'] if i + 1 < len(rows) else 0
        if None in r['cats']:
            unsup += ds; run += ds; longest = max(longest, run)
            if first_unsup is None:
                first_unsup = r
        else:
            run = 0.0
            key = '+'.join(sorted(set(r['cats'])))
            supp[key] = supp.get(key, 0) + ds
    total = rows[-1]['s'] - rows[0]['s']
    return {'length_m': round(total, 3), 'unsupported_m': round(unsup, 3),
            'unsupported_fraction': round(unsup / total, 5) if total else None,
            'longest_unsupported_run_m': round(longest, 3), 'supported_m_by_layer': {k: round(v, 3) for k, v in supp.items()},
            'first_unsupported_station': first_unsup,
            'network_contact': contact}


def truncate(pts, s_end):
    out, s0 = [pts[0]], 0.0
    for i in range(len(pts) - 1):
        a, b = Vector((*pts[i], 0)), Vector((*pts[i + 1], 0))
        ln = (b - a).length
        if s0 + ln >= s_end - 1e-9:
            p = a + (b - a).normalized() * (s_end - s0)
            out.append((p.x, p.y)); return out
        out.append(pts[i + 1]); s0 += ln
    return out


def prism(a, b, w):
    a = Vector((*a, 0)); b = Vector((*b, 0))
    d = (b - a).normalized(); n = Vector((-d.y, d.x, 0)) * (w / 2)
    z0, z1 = CLEAR_Z
    q = [a - n, a + n, b + n, b - n]
    v = [Vector((p.x, p.y, z0)) for p in q] + [Vector((p.x, p.y, z1)) for p in q]
    f = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2),
         (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
    return v, f, (a, b, d)


def collisions(pts, w, layer):
    res = []
    for i in range(len(pts) - 1):
        v, f, (a, b, d) = prism(pts[i], pts[i + 1], w)
        bvh = BVHTree.FromPolygons(v, f)
        pairs = bvh.overlap(layer.bvh)
        own = {}
        for _, ti in pairs:
            o = layer.owner[ti]
            c = sum((layer.v[k] for k in layer.t[ti]), Vector()) / 3
            s_along = (Vector((c.x, c.y, 0)) - a).dot(d)
            r = own.setdefault(o, [1e18, -1e18, 0])
            r[0] = min(r[0], s_along); r[1] = max(r[1], s_along); r[2] += 1
        res.append({'segment': i, 'from': [round(c, 3) for c in pts[i]], 'to': [round(c, 3) for c in pts[i + 1]],
                    'overlap_pairs': len(pairs),
                    'objects': {o: {'s_min': round(r[0], 2), 's_max': round(r[1], 2), 'tris': r[2]} for o, r in own.items()}})
    return res


def containment(pts, w, layer):
    """obstacle objects with bbox fully inside any corridor prism (surface BVH misses these)."""
    hits = []
    by_obj = {}
    for vi, o in zip(range(len(layer.t)), layer.owner):
        by_obj.setdefault(o, set()).update(layer.t[vi])
    for o, vids in by_obj.items():
        P = [layer.v[k] for k in vids]
        for i in range(len(pts) - 1):
            a = Vector((*pts[i], 0)); b = Vector((*pts[i + 1], 0))
            d = (b - a).normalized(); n = Vector((-d.y, d.x, 0)); ln = (b - a).length
            ok = all(0 <= (Vector((p.x, p.y, 0)) - a).dot(d) <= ln and abs((Vector((p.x, p.y, 0)) - a).dot(n)) <= w / 2
                     and CLEAR_Z[0] <= p.z <= CLEAR_Z[1] for p in P)
            if ok:
                hits.append({'object': o, 'segment': i})
    return hits


def nearest_obstacles(pts, layer, every=5.0):
    best = {}
    st = stations(pts)
    for s, x, y, d, n, seg in st:
        if (s % every) > 1e-6 and s != st[-1][0]:
            continue
        loc, nrm, idx, dist = layer.bvh.find_nearest(Vector((x, y, 1.0)))
        if loc is None:
            continue
        o = layer.owner[idx]
        if o not in best or dist < best[o]['dist_m']:
            best[o] = {'dist_m': round(dist, 3), 'at_s': round(s, 1), 'at_xy': [round(x, 2), round(y, 2)]}
    return dict(sorted(best.items(), key=lambda kv: kv[1]['dist_m'])[:6])


def evidence_checks(pts):
    samp = [(x, y) for s, x, y, d, n, seg in stations(pts)]
    out = {}
    np_ring = coords('north_palace_extent_gao2023_B')[0]
    sp_ring = coords('south_palace_candidate_gao2023_B')[0]
    wall_ring = coords('city_wall_schematic_B')[0]
    out['north_palace_old_B'] = {'min_dist_m': round(min(poly_dist(p, np_ring) for p in samp), 2),
                                 'samples_inside': sum(inside(p, np_ring) for p in samp),
                                 'note': 'old schematic B only; new A walls unregistered -> cannot clear'}
    out['south_palace_candidate_B'] = {'min_dist_m': round(min(poly_dist(p, sp_ring) for p in samp), 2),
                                       'samples_inside': sum(inside(p, sp_ring) for p in samp)}
    out['city_wall_schematic_B'] = {'min_dist_to_outline_m': round(min(poly_dist(p, wall_ring) for p in samp), 2),
                                    'samples_outside': sum(not inside(p, wall_ring) for p in samp)}
    for pid in ('region_yongan_B', 'region_wuku_B', 'region_taicang_B', 'gate_shangdong_B', 'gate_zhongdong_B', 'gate_gu_B'):
        c = coords(pid)
        dmin = min(math.hypot(p[0] - c[0], p[1] - c[1]) for p in samp)
        out[pid] = {'point': c, 'min_dist_m': round(dmin, 2),
                    'within_75m_presentation_envelope': dmin <= F[pid].get('presentation_envelope_m', 75)}
    # proximity to B road relations (which classification it would inherit)
    pc = json.load(open(os.path.join(LUO, 'data', 'west', 'road-preconstraints.json'), encoding='utf-8'))
    cls = {r['feature_id']: r['classification'] for r in pc['rows']}
    rel = {}
    for fid, f in F.items():
        if f.get('kind') not in ('road_relation', 'palace_link') or not f['geometry']:
            continue
        line = f['geometry']['coordinates']
        near = sum(1 for p in samp if poly_dist(p, line) <= 10.0) * STEP
        dmin = min(poly_dist(p, line) for p in samp)
        if dmin < 200:
            rel[fid] = {'classification': cls.get(fid), 'min_dist_m': round(dmin, 2), 'length_within_10m_m': near}
    out['B_road_relations_within_200m'] = rel
    out['ancient_water_corridors_B_unplaced'] = {'geometry': None, 'result': 'cannot evaluate: no placed water geometry; unknown != no conflict'}
    out['north_palace_excavated_walls_A_unplaced'] = {'geometry': None, 'result': 'cannot evaluate: unregistered (LY-003)'}
    out['wall_surviving_segments_phase_unresolved'] = {'geometry': None, 'result': 'cannot evaluate: no control points'}
    return out


rep['candidates'] = {}
for cid, c in CANDIDATES.items():
    pts = [tuple(map(float, p)) for p in c['pts']]
    rows, contact = march(pts, W_ROAD)
    summ = summarise(rows, contact)
    s_end = contact['s'] if contact else rows[-1]['s']
    tpts = truncate(pts, s_end)
    start_hit = ground_hit(*pts[0])
    z0 = start_hit[1] if start_hit else None
    z1 = None if not contact else max(z for z in contact['z'] if z is not None)
    entry = {'label': c['label'], 'parent_B': c['parent_B'],
             'polyline_full': [[round(a, 3), round(b, 3)] for a, b in pts],
             'polyline_to_contact': [[round(a, 3), round(b, 3)] for a, b in tpts],
             'start_ground': {'layer': start_hit[0] if start_hit else None, 'z': z0},
             'contact_ground_z_max': z1,
             'grade_if_built': None if (z0 is None or z1 is None) else round((z1 - z0) / s_end, 6),
             'support_w3': summ,
             'collisions_w3': collisions(tpts, W_ROAD, L['obstacles']),
             'collisions_w6': collisions(tpts, W_NET, L['obstacles']),
             'containment_w6': containment(tpts, W_NET, L['obstacles']),
             'nearest_obstacles': nearest_obstacles(tpts, L['obstacles']),
             'evidence': evidence_checks(tpts)}
    # only keep sparse station rows (every 50 m + first/last) to bound report size
    entry['stations_sample'] = [r for r in rows if (r['s'] % 50) < 1e-6 or r is rows[-1] or r is rows[0]]
    rep['candidates'][cid] = entry

# ---------- negatives (must FAIL / detect) and positives ----------
neg = {}
# NEG-COLLIDE: corridor that crosses the east C wall wall-01 -> overlap must be > 0
cc = collisions([(2300.0, 3600.0), (2600.0, 3600.0)], W_NET, L['obstacles'])
neg['NEG_COLLIDE_east_wall'] = {'expect': 'overlap_pairs>0', 'overlap_pairs': sum(x['overlap_pairs'] for x in cc),
                               'objects': sorted({o for x in cc for o in x['objects']})}
# NEG-COLLIDE-STORAGE: corridor straight through the two granaries (bodies at y~3676-3683; y=3670 is open yard)
cc = collisions([(2250.0, 3680.0), (2321.0, 3680.0)], W_ROAD, L['obstacles'])
neg['NEG_COLLIDE_granary'] = {'expect': 'overlap_pairs>0', 'overlap_pairs': sum(x['overlap_pairs'] for x in cc),
                             'objects': sorted({o for x in cc for o in x['objects']})}
# NEG-NOGROUND: R1 with the network ground removed -> no contact, ~all unsupported
rows, contact = march([(X0, 3484.5), (X0, 1700.0)], W_ROAD, skip=('network',))
s = summarise(rows, contact)
neg['NEG_R1_network_removed'] = {'expect': 'network_contact None, unsupported_fraction ~1',
                                 'network_contact': contact, 'unsupported_fraction': s['unsupported_fraction'],
                                 'unsupported_m': s['unsupported_m']}
# POS-SUPPORT: march along the C_4 middle_cross piece itself -> fully supported by network
a4, b4 = (1501.6264312324367 + 20, 1826.2125149136568 - 0.3755), (2528.329 - 20, 1806.9314027982903 + 0.3755)
rows, _ = march([a4, b4], W_ROAD, stop_on_network=False)
s = summarise(rows, None)
neg['POS_C4_supported'] = {'expect': 'unsupported_fraction 0', 'unsupported_fraction': s['unsupported_fraction'],
                           'supported_m_by_layer': s['supported_m_by_layer']}
# POS-EXISTING-ROAD: the existing 196 m road centreline is supported by ne_road / taicang_ground
rows, _ = march([(2285.714, 3652.0), (2285.714, 3486.0), (2316.327, 3486.0), (2316.327, 3489.5)], W_ROAD, stop_on_network=False)
s = summarise(rows, None)
neg['POS_existing_196m_supported'] = {'expect': 'unsupported_fraction 0', 'unsupported_fraction': s['unsupported_fraction'],
                                      'supported_m_by_layer': s['supported_m_by_layer']}
# NEG-STUB-BEYOND: 10 m beyond the stub end towards wuku B -> unsupported (armory end open, LY-036)
rows, _ = march([(X0, 3490.2), (X0, 3500.0)], W_ROAD, stop_on_network=False)
s = summarise(rows, None)
neg['NEG_beyond_stub_to_wuku'] = {'expect': 'unsupported_fraction 1', 'unsupported_fraction': s['unsupported_fraction']}
rep['negatives_and_positives'] = neg

with open(out_p, 'w', encoding='utf-8') as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)
print('WROTE', out_p)
