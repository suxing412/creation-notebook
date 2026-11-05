"""LY-038 prep measurement (read-only on inputs).
Blender: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_wuku.py -- <out.json>
Imports library wuku A/B LOD0 and the city-visible wuku chunks (B + C_WUKU_ISOLATED_SUPPORT_PATCH),
then measures in Blender Z-up metres:
  1. per-mesh tris/bbox, library-B vs city-B geometry identity (translated, 1 mm grid hash)
  2. horizontal up-facing levels below 1.2 m (plinth top, step treads) and ground-contact faces
  3. A and B ground-contact footprint support on the current patch, for an offset sweep
  4. A/B co-installation overlap (bbox and BVH tri overlap) -> mutual exclusion evidence
All results are written to <out.json>. Nothing in the repo is written.
"""
import bpy, bmesh, sys, json, hashlib, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
LIB = "D:/GitHub/creation-notebook-lab/docs/library/models/m-luoyang-wuku/files/"
WORK = "D:/GitHub/creation-notebook-workpacks/LY-038/prep/work/"
ORIGIN = Vector((2316.326904296875, 3500.0, 0.0))  # city placement of B (world_matrix in source-node-manifest)

bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in objs:
        o["src"] = tag
    return objs

def world_tris(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]
    tris = [tuple(vs[i] for i in t.vertices) for t in me.loop_triangles]
    ev.to_mesh_clear()
    return tris

def bbox(pts):
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return [[round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)], [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)]]

def geohash(tris, shift=Vector((0, 0, 0))):
    keys = []
    for t in tris:
        k = tuple(sorted(tuple(int(round((c - shift)[i] * 1000)) for i in range(3)) for c in t))
        keys.append(k)
    keys.sort()
    return hashlib.sha256(json.dumps(keys).encode()).hexdigest()

def tri_normal_area(t):
    n = (t[1] - t[0]).cross(t[2] - t[0])
    a = n.length / 2
    return (n.normalized() if a > 0 else Vector((0, 0, 0))), a

res = {"origin_city_B": list(ORIGIN)}
A = imp(LIB + "wuku-A-LOD0.glb", "A")
B = imp(LIB + "wuku-B-LOD0.glb", "B")
C1 = imp(WORK + "chunks__wuku_C_with_support-01.glb", "cityB1")
C2 = imp(WORK + "chunks__wuku_C_with_support-02.glb", "cityB2")
CITY = C1 + C2
PATCH = [o for o in CITY if "SUPPORT_PATCH" in o.name][0]

T = {}
for o in A + B + CITY:
    T[o.name] = world_tris(o)
res["meshes"] = {o.name: {"src": o["src"], "tris": len(T[o.name]), "bbox": bbox([c for t in T[o.name] for c in t])} for o in A + B + CITY}

# 1. library B vs city B identity (strip the .001 suffix, shift by origin)
ident = {}
for o in B:
    base = o.name.split(".")[0]
    cand = [c for c in CITY if base in c.name]
    if not cand:
        ident[o.name] = "no city counterpart"; continue
    c = cand[0]
    ident[o.name] = {"city": c.name, "lib_tris": len(T[o.name]), "city_tris": len(T[c.name]),
                     "lib_hash_mm": geohash(T[o.name]), "city_hash_mm_shifted": geohash(T[c.name], ORIGIN),
                     "equal": geohash(T[o.name]) == geohash(T[c.name], ORIGIN)}
res["libB_vs_cityB"] = ident
res["A_vs_B_same_geometry"] = {a.name: geohash(T[a.name]) == geohash(T[[b for b in B if b.name.split('-')[-1] == a.name.split('-')[-1]][0].name]) for a in A}

# 2. horizontal levels below 1.2 m
def levels(objs, zmax=1.2, sign=1):
    bins = {}
    for o in objs:
        for t in T[o.name]:
            n, a = tri_normal_area(t)
            if a < 1e-6 or n.z * sign < 0.98:
                continue
            z = sum(c.z for c in t) / 3
            if z > zmax:
                continue
            key = round(z, 3)
            b = bins.setdefault(key, {"area": 0.0, "pts": [], "objs": set()})
            b["area"] += a; b["pts"] += list(t); b["objs"].add(o.name)
    out = []
    for k in sorted(bins):
        b = bins[k]
        out.append({"z": k, "area_m2": round(b["area"], 3), "xy_bbox": [bbox(b["pts"])[0][:2], bbox(b["pts"])[1][:2]], "objs": sorted(b["objs"])})
    return out
res["A_up_levels_below_1.2"] = levels(A)
res["B_up_levels_below_1.2"] = levels(B)
res["A_down_levels_below_0.5"] = levels(A, 0.5, -1)
res["B_down_levels_below_0.5"] = levels(B, 0.5, -1)
res["patch_up"] = levels([PATCH], 1.0)

# ground-contact faces: down-facing faces with z <= 0.01 (what has to sit on support)
def contact_tris(objs, ztol=0.01):
    out = []
    for o in objs:
        for t in T[o.name]:
            n, a = tri_normal_area(t)
            if a > 1e-6 and n.z < -0.98 and max(c.z for c in t) <= ztol:
                out.append(t)
    return out
cA = contact_tris(A); cB = contact_tris(B)
res["A_contact"] = {"tris": len(cA), "area_m2": round(sum(tri_normal_area(t)[1] for t in cA), 3), "bbox": bbox([c for t in cA for c in t]) if cA else None}
res["B_contact"] = {"tris": len(cB), "area_m2": round(sum(tri_normal_area(t)[1] for t in cB), 3), "bbox": bbox([c for t in cB for c in t]) if cB else None}
res["A_min_z"] = min(c.z for o in A for t in T[o.name] for c in t)
res["B_min_z"] = min(c.z for o in B for t in T[o.name] for c in t)

# sample points on contact faces (barycentric grid, ~0.1 m) plus all contact vertices
def samples(tris, step=0.1):
    pts = []
    for t in tris:
        a, b, c = t
        L = max((b - a).length, (c - a).length, (c - b).length)
        n = max(1, int(math.ceil(L / step)))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u, v = i / n, j / n
                pts.append(a + (b - a) * u + (c - a) * v)
    return pts
sA = samples(cA); sB = samples(cB)
res["A_contact_samples"] = len(sA); res["B_contact_samples"] = len(sB)

pt = T[PATCH.name]
patch_bvh = BVHTree.FromPolygons([v for t in pt for v in t], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(pt))])
def support(samples_local, dx, dy, ztol=0.01):
    miss = 0; worst = 0.0; missed = []
    for p in samples_local:
        q = ORIGIN + Vector((p.x + dx, p.y + dy, 0.05 + p.z))
        hit = patch_bvh.ray_cast(q, Vector((0, 0, -1)), 0.05 + ztol + 0.05)
        ok = hit[0] is not None and abs(hit[0].z - (ORIGIN.z + p.z)) <= ztol
        if not ok:
            miss += 1; missed.append(p)
    ov = None
    if missed:
        # overhang distance: how far outside the patch xy rectangle the missed points reach
        pb = bbox([v for t in pt for v in t])
        d = 0.0
        for p in missed:
            x = ORIGIN.x + p.x + dx; y = ORIGIN.y + p.y + dy
            d = max(d, pb[0][0] - x, x - pb[1][0], pb[0][1] - y, y - pb[1][1])
        ov = round(d, 4)
        mb = bbox([Vector((p.x + dx, p.y + dy, p.z)) for p in missed])
    return {"dx": dx, "dy": dy, "unsupported": miss, "of": len(samples_local), "unsupported_frac": round(miss / len(samples_local), 5) if samples_local else None,
            "max_overhang_m": ov, "missed_bbox_local": (mb if missed else None)}

res["support_B_at_0"] = support(sB, 0, 0)
res["support_A_at_0"] = support(sA, 0, 0)
res["support_A_north1"] = support(sA, 0, 1.0)
sAc = samples(cA, 0.5)
res["A_contact_samples_coarse"] = len(sAc)
sweep = []
for iy in range(-4, 11):
    dy = iy * 0.5
    for ix in range(-8, 17):
        dx = ix * 0.5
        r = support(sAc, dx, dy)
        sweep.append([dx, dy, r["unsupported"]])
res["A_sweep"] = {"grid": "dx -4..8, dy -2..5 step 0.5, samples 0.5 m", "ok": [[d[0], d[1]] for d in sweep if d[2] == 0],
                  "fail_count": sum(1 for d in sweep if d[2] > 0)}
ok = res["A_sweep"]["ok"]
if ok:
    res["A_sweep"]["ok_dx_range"] = [min(o[0] for o in ok), max(o[0] for o in ok)]
    res["A_sweep"]["ok_dy_range"] = [min(o[1] for o in ok), max(o[1] for o in ok)]
    res["A_sweep"]["ok_dy_range_at_dx0"] = [min(o[1] for o in ok if o[0] == 0), max(o[1] for o in ok if o[0] == 0)] if any(o[0] == 0 for o in ok) else None
# fine boundary in dy at dx=0
fine = []
for i in range(0, 121):
    dy = round(i * 0.01, 2)
    fine.append([dy, support(sA, 0, dy)["unsupported"]])
res["A_dy_fine_dx0"] = {"first_ok_dy": next((f[0] for f in fine if f[1] == 0), None), "table": fine[::5]}

# 4. overlap if A and B both installed at origin (+dy north)
def bvh_of(objs, shift):
    tris = [t for o in objs for t in T[o.name]]
    return BVHTree.FromPolygons([v + shift for t in tris for v in t], [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(tris))])
bB = bvh_of(B, Vector((0, 0, 0)))
ovl = {}
for dy in (0.0, 1.0):
    bA = bvh_of(A, Vector((0, dy, 0)))
    pairs = bA.overlap(bB)
    ba = bbox([c + Vector((0, dy, 0)) for o in A for t in T[o.name] for c in t]); bb = bbox([c for o in B for t in T[o.name] for c in t])
    inter = [max(0, min(ba[1][i], bb[1][i]) - max(ba[0][i], bb[0][i])) for i in range(3)]
    ovl[str(dy)] = {"tri_pairs_intersecting": len(pairs), "bbox_intersection_xyz_m": [round(v, 3) for v in inter],
                    "bbox_intersection_volume_m3": round(inter[0] * inter[1] * inter[2], 2)}
res["A_B_coinstall_overlap"] = ovl

json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("WROTE", OUT)
