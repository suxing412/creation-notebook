import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
for o in bpy.context.scene.objects:
    if o.type!='MESH': continue
    me=o.data; mw=o.matrix_world
    v=np.array([tuple(mw@x.co) for x in me.vertices]); v=np.stack([v[:,0],v[:,2],-v[:,1]],1)
    print(o.name, len(me.polygons), 'x uniq', np.unique(np.round(v[:,0],2))[:30], 'z uniq', np.unique(np.round(v[:,2],2))[:30], 'y', np.unique(np.round(v[:,1],2))[:12])
