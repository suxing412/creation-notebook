"""LY-024 prep: TEST FIXTURES ONLY (not deliverable geometry, never published). Boxes in S84-local glTF frame.
blender -b --factory-startup --python-exit-code 1 -P make_test_fixtures.py -- <outdir>"""
import bpy, sys, os
out=sys.argv[sys.argv.index('--')+1]
def box(name, mn, mx):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    c=[(mn[i]+mx[i])/2 for i in range(3)]; s=[(mx[i]-mn[i]) for i in range(3)]
    bpy.ops.mesh.primitive_cube_add(location=(c[0],-c[2],c[1])); o=bpy.context.object
    o.scale=(s[0]/2,s[2]/2,s[1]/2); bpy.ops.object.transform_apply(scale=True); o.name=name
    bpy.ops.export_scene.gltf(filepath=os.path.join(out,name+'.glb'),export_format='GLB')
# F1 full shutter slab inset 1 mm from posts/beam/floor (should read as CLOSED, zero host overlap)
box('fx_closed_inset', (-3.499,0.221,-0.20), (3.499,2.999,-0.16))
# F2 slab pushed into counter zone (negative: host overlap must be >0)
box('fx_intrude_counter', (-3.0,0.30,-0.80), (3.0,2.9,-0.40))
# F3 slab hanging 0.10 m above floor (negative: support/float)
box('fx_floating', (-3.499,0.32,-0.20), (3.499,2.999,-0.16))
print('OK fixtures')
