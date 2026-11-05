# LY-033 prep: fixed-camera CPU (Workbench) renders of the two granary doorways in CITY coordinates.
# The SAME camera table is used for "before" (current city GLB), "installed" and "restored" renders,
# so before/after are pixel-comparable. Camera table is frozen here; do not change between runs.
# D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P render_fixed.py -- <outdir> <prefix> <glb> [glb ...]
import bpy, sys, os, json, hashlib
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
outdir, prefix, glbs = argv[0], argv[1], argv[2:]
os.makedirs(outdir, exist_ok=True)


def g2b(x, y, z):  # glTF (X east, Y up, Z south) -> Blender (X, -Z, Y)
    return Vector((x, -z, y))


CX, CZ = 2285.714111328125, -3673.468994140625
A = (CX - 12, CZ - 6 + 3.0, 0.85)   # door centre x, front plane z, floor y
B = (CX + 12, CZ - 6 + 2.5, 1.10)
CAMS = {
    'A-front':  (g2b(A[0], A[2] + 1.5, A[1] + 7.0), g2b(A[0], A[2] + 1.0, A[1])),
    'A-oblique': (g2b(A[0] + 5.0, A[2] + 2.5, A[1] + 6.0), g2b(A[0], A[2] + 0.8, A[1])),
    'A-inside': (g2b(A[0], A[2] + 1.6, A[1] - 4.5), g2b(A[0], A[2] + 1.0, A[1])),
    'B-front':  (g2b(B[0], B[2] + 1.5, B[1] + 7.0), g2b(B[0], B[2] + 1.0, B[1])),
    'B-oblique': (g2b(B[0] - 5.0, B[2] + 2.5, B[1] + 6.0), g2b(B[0], B[2] + 0.8, B[1])),
    'B-inside': (g2b(B[0], B[2] + 1.6, B[1] - 4.0), g2b(B[0], B[2] + 1.0, B[1])),
    'pair':     (g2b(CX, 24.0, CZ + 12.0), g2b(CX, 0.5, CZ - 5.0)),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
for g in glbs:
    bpy.ops.import_scene.gltf(filepath=g)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_object_outline = True; sh.show_shadows = True
sh.background_type = 'VIEWPORT'; sh.background_color = (0.93, 0.93, 0.92)
sc.view_settings.view_transform = 'Standard'
sc.display.render_aa = '8'
sc.render.resolution_x, sc.render.resolution_y = 1000, 750
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd)
sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 28; cd.clip_start = 0.05; cd.clip_end = 500
log = dict(engine='BLENDER_WORKBENCH (CPU, not browser/GPU)', inputs={}, cams={})
for g in glbs:
    log['inputs'][os.path.basename(g)] = hashlib.sha256(open(g, 'rb').read()).hexdigest()
for name, (loc, tgt) in CAMS.items():
    sh.show_shadows = not name.endswith('inside')  # interior: shadows off so the doorway is legible
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, '%s-%s.png' % (prefix, name))
    bpy.ops.render.render(write_still=True)
    log['cams'][name] = dict(loc=list(loc), target=list(tgt), lens=28)
json.dump(log, open(os.path.join(outdir, prefix + '-render-log.json'), 'w'), indent=1)
