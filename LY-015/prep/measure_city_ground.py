# LY-015 prep: what existing city ground/wall lies under the Kaiyang gate footprint (read-only).
#   blender -b --factory-startup --python-exit-code 1 -P measure_city_ground.py -- <lab_docs_dir> <placement.json> <out_json>
# Gate local (Blender z-up) -> world via placement.json engineering origin + rotation_z. World Blender (x,y,z) = glTF (x,-z,y).
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; DOCS, PL, OUT = Path(a[0]), Path(a[1]), Path(a[2])
pl = json.loads(PL.read_text()); T = Matrix.Translation(Vector(pl['engineering_origin_from_existing_wall_caps'])) @ Matrix.Rotation(pl['rotation_z_rad'], 4, 'Z')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
res = {'placement_origin': pl['engineering_origin_from_existing_wall_caps'], 'rotation_z_rad': pl['rotation_z_rad'], 'layers': {}}
for key, rel in [('ground-network-ground-stitched', 'cities/luoyang/assets/ground-atomic/network-ground-stitched.glb'),
                 ('wall-A-wall-04', 'cities/luoyang/assets/city-wall/A/wall-04.glb'), ('wall-A-wall-05', 'cities/luoyang/assets/city-wall/A/wall-05.glb')]:
    bpy.ops.wm.read_factory_settings(use_empty=True); p = DOCS / rel
    bpy.ops.import_scene.gltf(filepath=str(p)); objs = [o for o in bpy.data.objects if o.type == 'MESH']
    dg = bpy.context.evaluated_depsgraph_get(); vs = []; fs = []
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); off = len(vs)
        vs += [o.matrix_world @ v.co for v in me.vertices]; fs += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
    bvh = BVHTree.FromPolygons(vs, fs); grid = []; hit_n = 0; zs = []
    for ix in range(-40, 41):
        for iy in range(-20, 21):
            lx, ly = ix * 0.5, iy * 0.5; w = T @ Vector((lx, ly, 30.0))
            h = bvh.ray_cast(w, Vector((0, 0, -1)), 60)
            if h[0] is not None:
                hit_n += 1; lz = (T.inverted() @ h[0]).z; zs.append(lz)
                if ix % 8 == 0 and iy % 4 == 0: grid.append([lx, ly, round(lz, 3)])
    # wall end-face x positions along local y=0 (horizontal rays from gate centre outward at local z=3)
    ends = {}
    for s in (-1, 1):
        o = T @ Vector((0, 0, 3.0)); d = (T.to_3x3() @ Vector((s, 0, 0))).normalized(); h = bvh.ray_cast(o, d, 60)
        ends[str(s)] = None if h[0] is None else round((T.inverted() @ h[0]).x, 4)
    res['layers'][key] = {'path': rel, 'sha256': sha(p), 'bytes': p.stat().st_size, 'samples': 81 * 41, 'hits': hit_n,
                          'local_top_z_min': round(min(zs), 4) if zs else None, 'local_top_z_max': round(max(zs), 4) if zs else None,
                          'sparse_grid_local_xyz': grid, 'horizontal_hit_local_x_from_centre_z3': ends}
OUT.write_text(json.dumps(res, indent=1)); print('LY015_CITY_OK')
