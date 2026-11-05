# LY-032 prep: TEST FIXTURES ONLY (plain boxes), used to prove m04_kit_check.py can pass and fail.
# They are NOT door designs and NOT deliverable geometry; never copy them into models/.
# usage: blender -b --factory-startup --python-exit-code 1 -P m05_make_test_fixtures.py -- <outdir>
import bpy, sys, math, os
argv = sys.argv[sys.argv.index('--') + 1:]
od = argv[0]; os.makedirs(od, exist_ok=True)
JX = (2296.9641, 2298.4641); FY, LY = 1.10, 3.20; ZI = -3677.169
T = 0.06; GAP = 0.005

def box(name, cx, cy, cz, sx, sy, sz, rot_y_deg=0.0, pivot=None):
    # glTF centre/size -> Blender (x, -z, y)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, -cz, cy))
    o = bpy.context.object; o.name = name; o.scale = (sx, sz, sy)
    if pivot is not None:
        bpy.context.scene.cursor.location = (pivot[0], -pivot[2], pivot[1])
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        o.rotation_euler[2] = math.radians(rot_y_deg)
    return o

def export(fn):
    bpy.ops.export_scene.gltf(filepath=os.path.join(od, fn), export_format='GLB', use_selection=False)

w = (JX[1] - JX[0]) / 2 - GAP; h = LY - FY - 2 * GAP; zc = ZI - T / 2 - GAP
for state, ang in [('closed', 0), ('half', 45), ('open', 90)]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # left leaf hinged at west jamb, right leaf at east jamb; inward swing (toward -Z)
    box('FIXTURE_leaf_W', JX[0] + GAP + w / 2, FY + GAP + h / 2, zc, w, h, T, rot_y_deg=+ang, pivot=(JX[0] + GAP, 0, zc))
    box('FIXTURE_leaf_E', JX[1] - GAP - w / 2, FY + GAP + h / 2, zc, w, h, T, rot_y_deg=-ang, pivot=(JX[1] - GAP, 0, zc))
    export(f'FIXTURE-{state}.glb')
print('LY032 fixtures written', od)
