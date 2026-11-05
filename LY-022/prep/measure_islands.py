# LY-022 prep: connected-island bboxes per mesh (glTF coords). Read-only.
# usage: blender -b --factory-startup --python-exit-code 1 -P measure_islands.py -- <in.glb> <out.json>
import bpy, sys, json, bmesh
a=sys.argv[sys.argv.index('--')+1:]; src,out=a[0],a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
res={}
for o in bpy.data.objects:
    if o.type!='MESH': continue
    bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    seen=set(); isl=[]
    for f0 in bm.faces:
        if f0.index in seen: continue
        st=[f0]; seen.add(f0.index); fs=[]
        while st:
            f=st.pop(); fs.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); st.append(g)
        vs={v for f in fs for v in f.verts}
        xs=[v.co.x for v in vs]; ys=[v.co.z for v in vs]; zs=[-v.co.y for v in vs]
        up={}
        for f in fs:
            if f.normal.z>0.99:
                h=round(sum(v.co.z for v in f.verts)/len(f.verts),3); up[str(h)]=round(up.get(str(h),0)+f.calc_area(),4)
        isl.append(dict(faces=len(fs),min=[round(min(xs),3),round(min(ys),3),round(min(zs),3)],max=[round(max(xs),3),round(max(ys),3),round(max(zs),3)],up=up))
    bm.free()
    res[o.name]=sorted(isl,key=lambda i:(i['min'][2],i['min'][0]))
json.dump(res,open(out,'w',encoding='utf-8'),indent=1)
print('OK',{k:len(v) for k,v in res.items()})
