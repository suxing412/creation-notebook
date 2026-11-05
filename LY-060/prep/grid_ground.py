# LY-060 prep: grid ray-cast ground coverage for any GLB (read-only).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P grid_ground.py -- out.json step a.glb [b.glb ...]
# For each XY cell centre inside the bbox, cast down from z=+20 and record the LOWEST hit and the highest hit
# whose z <= ground_band_top (bboxMin.z + 0.6). Reports: share of cells with no geometry at all, share with
# geometry only high up (roof/canopy, nothing near ground), and a histogram of lowest-hit z.
import bpy, sys, json, hashlib, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
out, step, srcs = argv[0], float(argv[1]), argv[2:]
res = {}
for src in srcs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    objs = [o for o in sc.objects if o.type == 'MESH']
    lo = [min((o.matrix_world @ Vector(c))[i] for o in objs for c in o.bound_box) for i in range(3)]
    hi = [max((o.matrix_world @ Vector(c))[i] for o in objs for c in o.bound_box) for i in range(3)]
    band = lo[2] + 0.6
    n = empty = highonly = 0
    hist = {}
    x = lo[0] + step / 2
    while x < hi[0]:
        y = lo[1] + step / 2
        while y < hi[1]:
            n += 1
            zs = []
            org = Vector((x, y, hi[2] + 5)); d = Vector((0, 0, -1))
            while True:
                ok, loc, nor, idx, ob, mx = sc.ray_cast(dg, org, d, distance=100.0)
                if not ok: break
                zs.append(loc.z); org = loc + d * 1e-4
            if not zs: empty += 1
            else:
                mz = round(min(zs), 2)
                hist[str(mz)] = hist.get(str(mz), 0) + 1
                if mz > band: highonly += 1
            y += step
        x += step
    res[os.path.basename(src)] = {
        'path': src.replace(os.sep, '/'), 'sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
        'step': step, 'cells': n, 'emptyCells': empty, 'emptyShare': round(empty / n, 4),
        'highOnlyCells': highonly, 'groundBandTop': round(band, 3),
        'lowestHitHistogram': dict(sorted(hist.items(), key=lambda kv: float(kv[0]))),
        'bboxMinZ': round(lo[2], 4)}
    print(os.path.basename(src), n, empty, round(empty / n, 3), highonly)
json.dump(res, open(out, 'w', encoding='utf-8'), indent=1)
