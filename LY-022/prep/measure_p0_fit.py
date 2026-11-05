# LY-022 prep (read-only): hypothesis P0 fit test.
# P0 = frontage v2.1 LOD0 translated to market centre (214.286, Y0, -1959.184) glTF, no rotation,
#      五店三摊 shops/stalls + N2 retired (as LY-029 would), keep sample_ground + 7 route_* + boundary_*.
# P0 is NOT a frozen placement; LY-010/LY-005 own the real one. Output: gaps json.
# usage: blender -b --factory-startup --python-exit-code 1 -P measure_p0_fit.py -- <market-cluster.glb> <frontage.glb> <out.json> [Y0]
import bpy, sys, json, bmesh, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; mc,fr,out=a[0],a[1],a[2]; Y0=float(a[3]) if len(a)>3 else 0.20
CX,CZ=214.286,-1959.184
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=mc)
keep={}
for o in list(bpy.data.objects):
    if o.type!='MESH': continue
    if o.name.startswith(('route_','sample_ground','boundary')): keep[o.name]=o
    else: bpy.data.objects.remove(o)
before=set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=fr)
fobjs=[o for o in bpy.data.objects if o.name not in before and o.type=='MESH']
# glTF(X,Y,Z) -> Blender(x=X, y=-Z, z=Y)
for o in bpy.data.objects:
    if o.name not in before and o.parent is None:
        o.location=(o.location.x+CX, o.location.y-CZ, o.location.z+Y0)
bpy.context.view_layer.update()
def g2b(X,Y,Z): return Vector((X,-Z,Y))
def bvh(o):
    bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    t=BVHTree.FromBMesh(bm); bm.free(); return t
trees={n:bvh(o) for n,o in keep.items()}
for o in fobjs: trees['FR:'+o.name.split('__')[1] if '__' in o.name else 'FR:'+o.name]=bvh(o)
def down(X,Z,top=3.0):
    best=None
    for n,t in trees.items():
        h=t.ray_cast(g2b(X,top,Z),Vector((0,0,-1)),10)
        if h[0] is not None:
            y=h[0].z
            if best is None or y>best[0]: best=(round(y,4),n)
    return best
R={}
# 1) street zone grid (local x -24..24, z -5..5) — support heights
pts=[];hist={}
x=-24.0
while x<=24.0001:
    z=-4.9
    while z<=4.9001:
        h=down(CX+x,CZ+z); pts.append((round(x,2),round(z,2),h)); k=('%s@%s'%(h[0],h[1])) if h else 'MISS'; hist[k]=hist.get(k,0)+1
        z+=0.25
    x+=0.25
R['streetGrid']={'spacing':0.25,'count':len(pts),'hist':hist}
# max adjacent height jump along x and z
jumps=[]
grid={(p[0],p[1]):(p[2][0] if p[2] else None) for p in pts}
for (x,z),h in grid.items():
    for dx,dz in ((0.25,0),(0,0.25)):
        k=(round(x+dx,2),round(z+dz,2))
        if k in grid and h is not None and grid[k] is not None:
            d=abs(grid[k]-h)
            if d>0.005: jumps.append((x,z,k[0],k[1],round(d,4)))
R['streetJumps>5mm']={'count':len(jumps),'max':max([j[4] for j in jumps],default=0),'examples':jumps[:12]}
# 2) eight entrances: local (x0,x1,frontZ,sign) from islands-frontage-LOD0.json earth floor islands
ents=[(-15.8,-7.8,-5.0,-1),(-6.6,-0.6,-5.0,-1),(0.6,8.6,-5.0,-1),(9.8,15.8,-5.0,-1),
      (-14.2,-8.2,5.0,1),(-6.8,1.2,5.0,1),(2.6,8.6,5.0,1),(10.3,18.3,5.0,1)]
E=[]
for i,(x0,x1,fz,s) in enumerate(ents):
    xm=(x0+x1)/2
    inside=down(CX+xm,CZ+fz+s*0.3)   # 0.3 m inside the shop
    outside=[down(CX+xm,CZ+fz-s*d) for d in (0.1,0.5,1.0,2.0,3.0)]
    # distance from front edge to nearest route_public edge (z=+-2)
    E.append(dict(i=i+1,localX=[x0,x1],frontZ=fz,floor=inside,outside=outside,
                  riseToOutside=round(inside[0]-outside[0][0],4) if inside and outside[0] else None,
                  gapToRoutePublicEdge=round(abs(fz)-2.0,3)))
R['entrances']=E
# 3) frontage geometry intersecting route footprints / boundary (vertex-in-rectangle below y<Y0+0.3)
def rect(o):
    M=o.matrix_world; vs=[M@v.co for v in o.data.vertices]
    return (min(v.x for v in vs),max(v.x for v in vs),min(-v.y for v in vs),max(-v.y for v in vs),min(v.z for v in vs),max(v.z for v in vs))
RR={n:rect(o) for n,o in keep.items()}
hits=[]
for o in fobjs:
    M=o.matrix_world
    for n,(x0,x1,z0,z1,y0,y1) in RR.items():
        if n=='sample_ground': continue
        c=sum(1 for v in o.data.vertices if (lambda w:(x0<w.x<x1 and z0<-w.y<z1 and w.z<y1+2.4))(M@v.co))
        if c: hits.append((o.name,n,c))
R['frontageVertsInsideRouteOrBoundaryFootprint']=hits
R['routeRects']={n:[round(v,4) for v in r] for n,r in RR.items()}
# frontage overall footprint after P0
fb=[rect(o) for o in fobjs]
R['frontageFootprintP0']=[round(min(b[0] for b in fb),3),round(max(b[1] for b in fb),3),round(min(b[2] for b in fb),3),round(max(b[3] for b in fb),3),round(min(b[4] for b in fb),3)]
# 4) route fingerprints (sorted rounded world vertex positions, 1e-4 m)
fp={}
for n,o in keep.items():
    M=o.matrix_world; vs=sorted((round((M@v.co).x,4),round((M@v.co).z,4),round(-(M@v.co).y,4)) for v in o.data.vertices)
    fp[n]=hashlib.sha256(json.dumps(vs).encode()).hexdigest()
R['keptNodeVertexFingerprints']=fp
R['P0']={'translationGLTF':[CX,Y0,CZ],'rotation':'none','status':'hypothesis, not frozen'}
json.dump(R,open(out,'w',encoding='utf-8'),indent=1)
print('OK')
