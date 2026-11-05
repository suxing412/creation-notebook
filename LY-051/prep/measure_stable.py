# LY-051 prep: read-only measurement of m-luoyang-stable A/B GLB.
# Usage: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P measure_stable.py -- <in.glb> <out.json> <A|B>
# Blender coords after glTF import: X = bay axis, Y = depth (front open side is -Y, rear wall +Y), Z = up.
# Nothing is written back to the GLB.
import bpy, bmesh, sys, json, re, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
src, out, var = argv[0], argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sha = hashlib.sha256(open(src, 'rb').read()).hexdigest()

objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
def bb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]
boxes = {n: bb(o) for n, o in objs.items()}
r = lambda v: round(v, 4)

def bvh_of(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); return t
scene_bm = bmesh.new()
for o in objs.values():
    tmp = bmesh.new(); tmp.from_mesh(o.data); tmp.transform(o.matrix_world)
    me = bpy.data.meshes.new('tmp'); tmp.to_mesh(me); scene_bm.from_mesh(me); tmp.free()
scene_bvh = BVHTree.FromBMesh(scene_bm)

res = {"variant": var, "glb": src, "sha256": sha, "meshCount": len(objs)}
# 1. keyword search for tether / partition / drain components
kw = re.compile(r'tether|ring|hitch|peg|rail|bar|partition|divider|stall|screen|drain|gutter|ditch|halter|rope|系|栏|隔|排水', re.I)
res["keywordNodes"] = sorted(n for n in objs if kw.search(n))

posts = sorted([n for n in objs if '_post_' in n], key=lambda n: (boxes[n][0][1], boxes[n][0][0]))
troughs = sorted([n for n in objs if 'trough' in n], key=lambda n: boxes[n][0][0])
wall = [n for n in objs if 'rear_wall' in n][0]
plat = [n for n in objs if 'platform' in n][0]
rear_posts = [n for n in posts if boxes[n][0][1] > 0]
front_posts = [n for n in posts if boxes[n][0][1] < 0]
res["posts"] = {n: {"min": [r(v) for v in boxes[n][0]], "max": [r(v) for v in boxes[n][1]]} for n in posts}
res["troughs"] = {n: {"min": [r(v) for v in boxes[n][0]], "max": [r(v) for v in boxes[n][1]]} for n in troughs}
res["rearWall"] = {"min": [r(v) for v in boxes[wall][0]], "max": [r(v) for v in boxes[wall][1]]}
res["platform"] = {"min": [r(v) for v in boxes[plat][0]], "max": [r(v) for v in boxes[plat][1]]}

# 2. bays: clear width between post inner faces (front row), trough end gaps to posts
fx = sorted(front_posts, key=lambda n: boxes[n][0][0])
bays = []
for i in range(len(fx) - 1):
    a, b = boxes[fx[i]], boxes[fx[i + 1]]
    clear = b[0][0] - a[1][0]
    centre = (a[1][0] + b[0][0]) / 2
    t = [n for n in troughs if boxes[n][0][0] < centre < boxes[n][1][0]]
    tb = boxes[t[0]] if t else None
    bays.append({
        "bay": i, "postAxisSpacing": r((b[0][0] + b[1][0]) / 2 - (a[0][0] + a[1][0]) / 2),
        "clearWidthBetweenPostFaces": r(clear),
        "trough": t[0] if t else None,
        "troughToLeftPostFace": r(tb[0][0] - a[1][0]) if tb else None,
        "troughToRightPostFace": r(b[0][0] - tb[1][0]) if tb else None,
        "troughBackToRearWallFace": r(boxes[wall][0][1] - tb[1][1]) if tb else None,
        "troughFrontFaceY": r(tb[0][1]) if tb else None,
        "stallDepthTroughFrontToFrontPostInnerFace": r(tb[0][1] - a[1][1]) if tb else None,
        "stallDepthTroughFrontToPlatformFrontEdge": r(tb[0][1] - boxes[plat][0][1]) if tb else None,
    })
res["bays"] = bays
# gap between adjacent troughs = where a divider would pass at post line
res["troughGaps"] = [{"between": [troughs[i], troughs[i + 1]], "gapX": r(boxes[troughs[i + 1]][0][0] - boxes[troughs[i]][1][0]),
                      "centreX": r((boxes[troughs[i + 1]][0][0] + boxes[troughs[i]][1][0]) / 2)} for i in range(len(troughs) - 1)]

# 3. trough cavity: ray down at trough centre from above
cav = {}
for n in troughs:
    (lo, hi) = boxes[n]
    c = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2] + 1.0))
    hit = bvh_of(objs[n]).ray_cast(c, Vector((0, 0, -1)))
    cav[n] = {"rimZ": r(hi[2]), "innerBottomZ": r(hit[0].z) if hit[0] else None,
              "cavityDepth": r(hi[2] - hit[0].z) if hit[0] else None}
res["troughCavity"] = cav

# 4. rear post embed in rear wall (box-box overlap volume; posts and wall are simple boxes, 12 tris)
emb = {}
wl, wh = boxes[wall]
for n in rear_posts:
    lo, hi = boxes[n]
    d = [max(0.0, min(hi[i], wh[i]) - max(lo[i], wl[i])) for i in range(3)]
    emb[n] = {"overlapXYZ": [r(v) for v in d], "overlapVolume_m3": r(d[0] * d[1] * d[2]),
              "postVolume_m3": r((hi[0]-lo[0])*(hi[1]-lo[1])*(hi[2]-lo[2]))}
res["rearPostWallOverlap"] = emb

# 5. headroom: ray up from platform top+0.01 along front post line, mid-stall, and platform front edge
head = []
for b in bays:
    i = b["bay"]
    a, c = boxes[fx[i]], boxes[fx[i + 1]]
    x = (a[1][0] + c[0][0]) / 2
    for label, y in [("platformFrontEdge", boxes[plat][0][1] + 0.01), ("frontPostLine", (a[0][1] + a[1][1]) / 2),
                     ("midStall", (a[1][1] + boxes[troughs[i]][0][1]) / 2 if i < len(troughs) else 0.0),
                     ("troughFront", boxes[troughs[i]][0][1] - 0.01 if i < len(troughs) else 0.0)]:
        o = Vector((x, y, 0.01))
        hit = scene_bvh.ray_cast(o, Vector((0, 0, 1)))
        head.append({"bay": i, "at": label, "x": r(x), "y": r(y), "clearHeightAbovePlatform": r(hit[0].z) if hit[0] else None})
res["headroom"] = head

# 6. support: every non-platform, non-roof object's lowest z vs platform top
ptop = boxes[plat][1][2]
res["platformTopZ"] = r(ptop); res["platformBottomZ"] = r(boxes[plat][0][2])
res["groundContact"] = {n: r(boxes[n][0][2] - ptop) for n in objs if n != plat and boxes[n][0][2] < 1.0}

# 7. mounting faces available for a C tether/divider kit (geometry only; NOT an animal-safety statement)
res["mountCandidates"] = {
    "frontPostInnerFaces_heightRange": [0.0, r(boxes[fx[0]][1][2])],
    "rearWallFrontFaceY": r(wl[1]), "rearWallTopZ": r(wh[2]),
    "troughRimZ": r(boxes[troughs[0]][1][2]),
    "wallplateUndersideZ": r(min(boxes[n][0][2] for n in objs if 'wallplate' in n)),
}
# 8. trough-vs-rear-post and trough-vs-wall surface intersections (BVH overlap; surface only)
inter = {}
for n in troughs:
    tb_ = bvh_of(objs[n])
    for m in rear_posts + [wall, plat]:
        ov = tb_.overlap(bvh_of(objs[m]))
        if ov: inter[f"{n}|{m}"] = len(ov)
res["troughSurfaceIntersections"] = inter
json.dump(res, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('MEASURED', out)
