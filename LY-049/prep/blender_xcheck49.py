# LY-049 prep: independent Blender cross-check (read-only import; nothing is saved).
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P blender_xcheck49.py -- <out.json> [LOD0|LOD1]
# Blender axes after glTF import: (bx, by, bz) = (gx, -gz, gy).
import bpy, sys, json, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]; LOD = argv[1] if len(argv) > 1 else 'LOD0'
LAB = 'D:/GitHub/creation-notebook-lab/docs/cities/luoyang/'
PROTO = LAB + f'assets/c02v/A2-{LOD}-prototype.glb'
SOUTH = LAB + 'assets/ground-atomic/south.glb'
EXCL = {'site_lot', 'site_neutral_lane', 'designed_hardpacked_activity_ground'}
TX, TZ = 531.0, -818.45


def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=PROTO)
court = list(bpy.context.selected_objects)
for o in court:
    if o.name in EXCL:
        bpy.data.objects.remove(o, do_unlink=True)
court = [o for o in bpy.context.scene.objects]
root = [o for o in court if o.parent is None]
for o in root:
    o.location = (o.location.x + TX, o.location.y - TZ, o.location.z)  # gz -> -by
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.gltf(filepath=SOUTH)
south = [o for o in bpy.context.selected_objects if o.type == 'MESH']
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
kept = sorted(o.name for o in sc.objects if o.type == 'MESH')


def ray(origin, d):
    hit, loc, nrm, idx, obj, _ = sc.ray_cast(dg, Vector(origin), Vector(d))
    return (round(loc.z, 5), obj.name, round(nrm.z, 3), round(loc.x, 5), round(-loc.y, 5)) if hit else None


res = dict(seat='LY-049', lod=LOD, blender=bpy.app.version_string, protoSha256=sha(PROTO), southSha256=sha(SOUTH),
           meshObjects=kept, down=[], up=[], lateral=[])
# downward rays: centre line and the two post-clear edges, local z 6..12.4 (world gz)
for xl in (-4.55, -3.5, -2.45):
    for k in range(0, 33):
        zl = 6.0 + 0.2 * k
        gx, gz = TX + xl, TZ + zl
        h = ray((gx, -gz, 5.0), (0, 0, -1))
        # walk down through roof/lintel to the walkable surface (first hit below 0.6)
        o = 5.0; first = h
        while h and h[0] > 0.6:
            o = h[0] - 1e-4; h = ray((gx, -gz, o), (0, 0, -1))
        res['down'].append(dict(xl=xl, zl=round(zl, 3), firstHit=first, floor=h))
# upward rays from just above floor: clear height under lintels
for zl in (9.55, 10.0, 11.0, 11.65, 11.9):
    h = ray((TX - 3.5, -(TZ + zl), 0.21), (0, 0, 1))
    res['up'].append(dict(zl=zl, hit=h, clear_m=None if not h else round(h[0] - 0.2, 4)))
# lateral rays at y 1.0 from the centre line: free half-widths
for zl in (9.6, 10.6, 11.0, 11.7, 11.9):
    for sgn in (-1, 1):
        h = ray((TX - 3.5, -(TZ + zl), 1.0), (sgn, 0, 0))
        res['lateral'].append(dict(zl=zl, dir=sgn, hitX=None if not h else h[3], obj=None if not h else h[1]))
floors = [d['floor'] for d in res['down']]
res['summary'] = dict(nDown=len(floors), allFloorOnSouth=all(f and f[1] in [o.name for o in south] for f in floors),
                      floorY=sorted({f[0] for f in floors if f}),
                      clearUnderLintel=[u['clear_m'] for u in res['up']])
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps(res['summary']))
