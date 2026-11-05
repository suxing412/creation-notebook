"""LY-038 prep: per-LOD check of wuku A/B ground contact, step treads and port edge.
Blender -b --factory-startup --python-exit-code 1 -P measure_lods.py -- <out.json>
For each of the 6 library GLBs: whole bbox, down-facing z<=0.01 contact bbox+area,
up-facing levels below 0.45 m (step treads + plinth top), and the step-port edge
(lowest tread's outer edge: y-min, x-range). Read-only on inputs."""
import bpy, sys, json, hashlib
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1:][0]
LIB = "D:/GitHub/creation-notebook-lab/docs/library/models/m-luoyang-wuku/files/"
res = {}
for f in ["wuku-A-LOD0", "wuku-A-LOD1", "wuku-A-LOD2", "wuku-B-LOD0", "wuku-B-LOD1", "wuku-B-LOD2"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p = LIB + f + ".glb"
    bpy.ops.import_scene.gltf(filepath=p)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = []
    for o in objs:
        me = o.data; me.calc_loop_triangles(); M = o.matrix_world
        for t in me.loop_triangles:
            tris.append((o.name, [M @ me.vertices[i].co for i in t.vertices]))
    allp = [c for _, t in tris for c in t]
    bb = lambda P: [[round(min(q[i] for q in P), 4) for i in range(3)], [round(max(q[i] for q in P), 4) for i in range(3)]]
    contact = []; ups = {}
    for name, t in tris:
        n = (t[1] - t[0]).cross(t[2] - t[0]); a = n.length / 2
        if a < 1e-7: continue
        n.normalize(); z = sum(c.z for c in t) / 3
        if n.z < -0.98 and max(c.z for c in t) <= 0.01: contact.append((a, t))
        if n.z > 0.98 and z < 0.45:
            k = round(z, 3); e = ups.setdefault(k, [0.0, []]); e[0] += a; e[1] += t
    lv = [{"z": k, "area_m2": round(ups[k][0], 3), "xy_bbox": [bb(ups[k][1])[0][:2], bb(ups[k][1])[1][:2]]} for k in sorted(ups)]
    port = None
    if lv and lv[0]["z"] < 0.2:
        b0 = lv[0]["xy_bbox"]; port = {"edge_y": b0[0][1], "x_range": [b0[0][0], b0[1][0]], "width_m": round(b0[1][0] - b0[0][0], 3), "ground_z": 0.0}
    res[f] = {"sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "objects": sorted(o.name for o in objs), "tris": len(tris),
              "bbox": bb(allp), "min_z": round(min(c.z for c in allp), 5),
              "contact": {"tris": len(contact), "area_m2": round(sum(a for a, _ in contact), 3), "bbox": bb([c for _, t in contact for c in t]) if contact else None},
              "up_levels_below_0.45": lv, "step_port": port}
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: {"contact": v["contact"], "port": v["step_port"], "levels": [(l["z"], l["xy_bbox"]) for l in v["up_levels_below_0.45"]]} for k, v in res.items()}, indent=0))
