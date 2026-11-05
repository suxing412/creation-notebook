# LY-022 prep: read-only GLB node inventory (bbox in glTF coords X east, Y up, Z south(-north)).
# usage: blender -b --factory-startup --python-exit-code 1 -P measure_nodes.py -- <in.glb> <out.json>
import bpy, sys, json, bmesh
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
dg=bpy.context.evaluated_depsgraph_get()
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH': continue
    me=o.data; M=o.matrix_world
    vs=[M@v.co for v in me.vertices]
    if not vs: continue
    # Blender Z-up -> glTF: X=x, Y=z, Z=-y
    xs=[v.x for v in vs]; ys=[v.z for v in vs]; zs=[-v.y for v in vs]
    bm=bmesh.new(); bm.from_mesh(me); bm.transform(M)
    try: vol=bm.calc_volume(signed=False)
    except Exception: vol=None
    nm=sum(1 for e in bm.edges if not e.is_manifold)
    # top face area (normal up) and its height(s)
    tops={}
    for f in bm.faces:
        if f.normal.z>0.99:
            h=round(sum(v.co.z for v in f.verts)/len(f.verts),3); tops[h]=tops.get(h,0)+f.calc_area()
    bm.free()
    rows.append(dict(name=o.name, gltfName=o.get('name',o.name), tris=sum(len(p.vertices)-2 for p in me.polygons),
        mats=[s.material.name for s in o.material_slots if s.material],
        min=[round(min(xs),4),round(min(ys),4),round(min(zs),4)], max=[round(max(xs),4),round(max(ys),4),round(max(zs),4)],
        volume=round(vol,5) if vol is not None else None, nonmanifoldEdges=nm,
        upFaces={str(k):round(v,4) for k,v in sorted(tops.items())}))
json.dump(dict(src=src,count=len(rows),nodes=rows),open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('OK',len(rows))
