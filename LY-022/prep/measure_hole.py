# LY-022 prep (read-only): locate the ground well opening in C_market_ground_well_A and test coverage/distances.
# usage: blender -b --factory-startup --python-exit-code 1 -P measure_hole.py -- <chunk.glb> <out.json>
import bpy, sys, json, bmesh, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; ch,out=a
CX,CZ=214.286,-1959.184
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=ch)
objs={o.name:o for o in bpy.data.objects if o.type=='MESH'}
g=objs['C_market_ground_well_A']; M=g.matrix_world
W=[M@v.co for v in g.data.vertices]
inner=[w for w in W if 184.3<w.x<244.27 and -1981.17<-w.y<-1937.2]
cx=sum(w.x for w in inner)/len(inner); cz=sum(-w.y for w in inner)/len(inner)
rr=[math.hypot(w.x-cx,-w.y-cz) for w in inner]
R={'innerVerts':len(inner),'centreGLTF':[round(cx,4),round(cz,4)],'centreLocal':[round(cx-CX,4),round(cz-CZ,4)],'rMin':round(min(rr),4),'rMax':round(max(rr),4),'yLevels':sorted({round(w.z,4) for w in inner})}
liner=objs['A_LOD0__short_liner']; L=[liner.matrix_world@v.co for v in liner.data.vertices]
lr=[math.hypot(w.x-cx,-w.y-cz) for w in L]; R['linerRadial']=[round(min(lr),4),round(max(lr),4)]
T={}
for n,o in objs.items():
    bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); T[n]=BVHTree.FromBMesh(bm); bm.free()
# does ground cover the opening? ray from 0.3 downward at r < rMin-0.02 must not hit ground top at 0.2
gh=[]; cov=[]
for ang in range(0,360,15):
    for r in (0.0,0.2,0.4,min(rr)-0.02):
        X=cx+r*math.cos(math.radians(ang)); Z=cz+r*math.sin(math.radians(ang))
        h=T['C_market_ground_well_A'].ray_cast(Vector((X,-Z,0.3)),Vector((0,0,-1)),0.2)
        if h[0] is not None: gh.append((round(X,3),round(Z,3),round(h[0].z,4)))
        for n,t in T.items():
            if n.startswith(('A_LOD0__','C_market_ground')): continue
            h=t.ray_cast(Vector((X,-Z,3.0)),Vector((0,0,-1)),3.0)
            if h[0] is not None: cov.append((n,round(X,3),round(Z,3),round(h[0].z,3)))
R['groundHitsInsideOpening(<=0.1m below y0.3)']=gh
R['nonWellGeometryAboveOpening']=cov
rects={}
for n,o in objs.items():
    if n.startswith('route_') or n.startswith('C_MARKET_ENTRY'):
        vs=[o.matrix_world@v.co for v in o.data.vertices]; rects[n]=(min(v.x for v in vs),max(v.x for v in vs),min(-v.y for v in vs),max(-v.y for v in vs))
def d(r): dx=max(r[0]-cx,0,cx-r[1]); dz=max(r[2]-cz,0,cz-r[3]); return round(math.hypot(dx,dz),3)
R['openingCentreToRect']={n:d(r) for n,r in rects.items()}
# well-structure footprint (all A_LOD0 nodes) on plan
A=[o.matrix_world@v.co for n,o in objs.items() if n.startswith('A_LOD0__') for v in o.data.vertices]
R['wellFootprintGLTF']=[round(min(w.x for w in A),3),round(max(w.x for w in A),3),round(min(-w.y for w in A),3),round(max(-w.y for w in A),3)]
R['wellFootprintLocal']=[round(R['wellFootprintGLTF'][0]-CX,3),round(R['wellFootprintGLTF'][1]-CX,3),round(R['wellFootprintGLTF'][2]-CZ,3),round(R['wellFootprintGLTF'][3]-CZ,3)]
json.dump(R,open(out,'w'),indent=1); print('OK')
