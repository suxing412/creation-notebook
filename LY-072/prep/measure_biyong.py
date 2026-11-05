# LY-072 prep (read-only): measure the published Biyong hall A and enclosure-L GLBs.
# Nothing in the lab repo is written; only the JSON report given as <out.json>.
#
# Usage:
#   D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_biyong.py -- \
#       <out.json> <label=path.glb> [<label=path.glb> ...]
#
# Frame: Blender Z-up after glTF import (glTF -Z == Blender +Y). Each GLB is measured in its
# OWN origin; no trial-fit transform is applied (the transform is not in the repo).
import bpy, bmesh, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
SPECS = [a.split('=', 1) for a in argv[1:]]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
r3 = lambda v: [round(float(x), 4) for x in v]


def import_glb(p):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=p)
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']


def world_bm(objs):
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world)
        me = bpy.data.meshes.new('tmp'); t.to_mesh(me); t.free()
        bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    return bm


def obj_stats(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bd = sum(1 for e in bm.edges if e.is_boundary)
    vs = [v.co for v in bm.verts]
    lo = [min(v[k] for v in vs) for k in range(3)]; hi = [max(v[k] for v in vs) for k in range(3)]
    vol = sum(f.calc_area() * f.normal.dot(f.calc_center_median()) for f in bm.faces) / 3.0
    out = {'name': o.name, 'verts': len(bm.verts), 'faces': len(bm.faces), 'nonManifoldEdges': nm,
           'boundaryEdges': bd, 'bboxMin': r3(lo), 'bboxMax': r3(hi), 'signedVolume_m3': round(vol, 3),
           'materials': [m.name for m in o.data.materials if m]}
    bm.free(); return out


def up_levels(bm, min_area=0.05):
    lv = {}
    for f in bm.faces:
        if f.normal.z > 0.99:
            z = round(f.calc_center_median().z, 2)
            a = f.calc_area()
            d = lv.setdefault(z, {'area': 0.0, 'lo': [1e9, 1e9], 'hi': [-1e9, -1e9], 'n': 0})
            d['area'] += a; d['n'] += 1
            for v in f.verts:
                d['lo'] = [min(d['lo'][0], v.co.x), min(d['lo'][1], v.co.y)]
                d['hi'] = [max(d['hi'][0], v.co.x), max(d['hi'][1], v.co.y)]
    return [{'z': z, 'area_m2': round(d['area'], 3), 'faces': d['n'], 'xyMin': r3(d['lo']), 'xyMax': r3(d['hi'])}
            for z, d in sorted(lv.items()) if d['area'] >= min_area]


def ray_down(bvh, x, y, ztop=50.0):
    hit = bvh.ray_cast(Vector((x, y, ztop)), Vector((0, 0, -1)), 200.0)
    return None if hit[0] is None else round(hit[0].z, 4)


def profile(bvh, axis, sign, offset, t0, t1, step):
    # walk outward along +/-X or +/-Y at lateral offset; return [(t, z_top)]
    out = []
    n = int(round((t1 - t0) / step))
    for i in range(n + 1):
        t = t0 + i * step
        x, y = ((sign * t, offset) if axis == 'x' else (offset, sign * t))
        out.append([round(t, 3), ray_down(bvh, x, y)])
    return out


def runs(prof):
    # compress profile into runs of constant height (tol 1 mm)
    rs = []
    for t, z in prof:
        if rs and ((z is None and rs[-1]['z'] is None) or (z is not None and rs[-1]['z'] is not None and abs(z - rs[-1]['z']) < 1e-3)):
            rs[-1]['t1'] = t
        else:
            rs.append({'t0': t, 't1': t, 'z': z})
    return rs


def lateral_width(bvh, axis, sign, t, zref, half=12.0, step=0.05):
    # at distance t along axis, find lateral extent where top height == zref (+-2mm)
    pts = []
    n = int(round(2 * half / step))
    for i in range(n + 1):
        o = -half + i * step
        x, y = ((sign * t, o) if axis == 'x' else (o, sign * t))
        z = ray_down(bvh, x, y)
        if z is not None and abs(z - zref) < 0.002: pts.append(round(o, 3))
    return (min(pts), max(pts)) if pts else None


report = {'frame': 'Blender Z-up (glTF -Z = +Y); each GLB in its own origin; no trial-fit transform applied', 'files': []}
for label, path in SPECS:
    objs = import_glb(path)
    bm = world_bm(objs)
    bvh = BVHTree.FromBMesh(bm)
    rec = {'label': label, 'path': path, 'sha256': sha(path), 'objects': [obj_stats(o) for o in objs],
           'upLevels': up_levels(bm)}
    vs = [v.co for v in bm.verts]
    lo = [min(v[k] for v in vs) for k in range(3)]; hi = [max(v[k] for v in vs) for k in range(3)]
    rec['bboxMin'] = r3(lo); rec['bboxMax'] = r3(hi)
    if label.startswith('hall'):
        # support surface = earth object only (roof/timber would occlude a top-down ray)
        earth = [o for o in objs if 'earth' in o.name.lower()]
        bme = world_bm(earth); bvh = BVHTree.FromBMesh(bme)
        rec['supportObjects'] = [o.name for o in earth]
        # timber footprint near axes: lowest timber z and xy extents (posts on platform)
        tim = [o for o in objs if 'timber' in o.name.lower()]
        if tim:
            bmt = world_bm(tim)
            rec['timberBBox'] = [r3([min(v.co[k] for v in bmt.verts) for k in range(3)]),
                                 r3([max(v.co[k] for v in bmt.verts) for k in range(3)])]
            bmt.free()
        ax = {}
        for name, axis, sign in [('E+x', 'x', 1), ('W-x', 'x', -1), ('N+y', 'y', 1), ('S-y', 'y', -1)]:
            pr = profile(bvh, axis, sign, 0.0, 0.0, 22.0, 0.02)
            rs = runs(pr)
            # platform edge = end of the first run; stair foot = last run with a hit
            hits = [r for r in rs if r['z'] is not None]
            entry = {'centerlineRuns': rs if len(rs) < 60 else rs[:60]}
            if hits:
                top = hits[0]; foot = hits[-1]
                entry['platformTop_z'] = top['z']; entry['platformEdge_t'] = top['t1']
                entry['lastHit_t'] = foot['t1']; entry['lastHit_z'] = foot['z']
                treads = [r for r in hits[1:]]
                entry['treadCount'] = len(treads)
                entry['treads'] = [{'t0': r['t0'], 't1': r['t1'], 'z': r['z'], 'depth': round(r['t1'] - r['t0'] + 0.02, 3)} for r in treads]
                rises = []
                prev = top['z']
                for r in treads:
                    rises.append(round(prev - r['z'], 4)); prev = r['z']
                entry['rises'] = rises
                # stair width at the middle tread
                if treads:
                    mid = treads[len(treads) // 2]
                    w = lateral_width(bvh, axis, sign, (mid['t0'] + mid['t1']) / 2, mid['z'])
                    entry['midTreadLateral'] = w
                    entry['midTreadWidth'] = None if not w else round(w[1] - w[0] + 0.05, 3)
                    last = treads[-1]
                    w2 = lateral_width(bvh, axis, sign, (last['t0'] + last['t1']) / 2, last['z'])
                    entry['lastTreadLateral'] = w2
            ax[name] = entry
        rec['axes'] = ax
    if label.startswith('encl'):
        # footprint grid of top heights over the bbox (0.25 m)
        step = 0.25
        nx = int((hi[0] - lo[0]) / step) + 1; ny = int((hi[1] - lo[1]) / step) + 1
        tops = {}
        for i in range(nx):
            for j in range(ny):
                x = lo[0] + i * step + step / 2; y = lo[1] + j * step + step / 2
                z = ray_down(bvh, x, y)
                if z is not None: tops.setdefault(round(z, 3), 0); tops[round(z, 3)] += 1
        rec['topHeightHistogram_cells'] = dict(sorted(tops.items(), key=lambda kv: -kv[1])[:12])
        rec['footprintArea_m2_grid'] = round(sum(tops.values()) * step * step, 2)
        # cross-sections: walls along x at several y, along y at several x
        secs = {}
        for yy in [10.0, 30.0, 50.0, 66.0]:
            pr = profile(bvh, 'x', 1, yy, lo[0] - 1, hi[0] + 1, 0.02)
            secs['x-walk@y=%g' % yy] = [r for r in runs(pr) if r['z'] is not None]
        for xx in [10.0, 30.0, 50.0, 66.0]:
            pr = profile(bvh, 'y', 1, xx, lo[1] - 1, hi[1] + 1, 0.02)
            secs['y-walk@x=%g' % xx] = [r for r in runs(pr) if r['z'] is not None]
        # arm ends near axes: walk along the outer arms
        for yy in [round((lo[1] + hi[1]) / 2, 2)]:
            pass
        rec['sections'] = secs
        # along-arm walk: find gaps (openings) along each arm centerline
        arms = {}
        # guess arm centerlines from max coords minus half thickness from sections
        for key, axis, off in [('arm-alongX@y=hi', 'x', None), ('arm-alongY@x=hi', 'y', None)]:
            if axis == 'x':
                sx = secs['y-walk@x=30']
                yc = (sx[-1]['t0'] + sx[-1]['t1']) / 2 if sx else hi[1] - 0.5
                pr = profile(bvh, 'x', 1, yc, lo[0] - 1, hi[0] + 1, 0.02)
                arms[key] = {'centerline': round(yc, 3), 'runs': [r for r in runs(pr)]}
            else:
                sy = secs['x-walk@y=30']
                xc = (sy[-1]['t0'] + sy[-1]['t1']) / 2 if sy else hi[0] - 0.5
                pr = profile(bvh, 'y', 1, xc, lo[1] - 1, hi[1] + 1, 0.02)
                arms[key] = {'centerline': round(xc, 3), 'runs': [r for r in runs(pr)]}
        rec['arms'] = arms
    bm.free()
    report['files'].append(rec)

json.dump(report, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
