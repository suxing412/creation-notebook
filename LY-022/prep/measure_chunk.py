# LY-022 prep (read-only): continuity / hole / overlay measurements on the actual placed chunk
# chunks/market_frontage_well_routes.glb (city-visible-web-handoff-v1-public, sha 0193ebc0...). No transform applied.
# usage: blender -b --factory-startup --python-exit-code 1 -P measure_chunk.py -- <chunk.glb> <market-cluster.glb> <out.json>
import bpy, sys, json, bmesh, math, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; ch,mc,out=a
CX,CZ=214.286,-1959.184
def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=p)
    return {o.name:o for o in bpy.data.objects if o.type=='MESH'}
def fingerprint(o):
    M=o.matrix_world; vs=sorted({(round((M@v.co).x,4),round((M@v.co).z,4),round(-(M@v.co).y,4)) for v in o.data.vertices})
    return hashlib.sha256(json.dumps(vs).encode()).hexdigest(), len(vs)
# --- reference fingerprints from in-city market-cluster
objs=load(mc); ref={n:fingerprint(o) for n,o in objs.items() if n.startswith(('route_','boundary','sample_ground'))}
# --- chunk
objs=load(ch)
R={'chunk':ch}
fp={n:fingerprint(o) for n,o in objs.items() if n.startswith(('route_','boundary','C_market_ground'))}
R['fingerprints']={n:{'chunk':fp[n][0],'vertsUnique':fp[n][1],'marketCluster':ref.get(n,(None,))[0],'equal':ref.get(n,(None,))[0]==fp[n][0]} for n in fp}
def bvh(o):
    bm=bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); t=BVHTree.FromBMesh(bm); bm.free(); return t
T={n:bvh(o) for n,o in objs.items()}
def g2b(X,Y,Z): return Vector((X,-Z,Y))
def down(X,Z,top=2.5,only=None,skip=()):
    best=None
    for n,t in T.items():
        if only and not n.startswith(only): continue
        if n.startswith(skip): continue
        h=t.ray_cast(g2b(X,top,Z),Vector((0,0,-1)),20)
        if h[0] is not None and (best is None or h[0].z>best[0]): best=(round(h[0].z,4),n)
    return best
# 1 street grid: local x -24..24, z -5..5, rays from 2.5 m, skipping roof (tile) & timber to read walking surface
hist={};miss=[];grid={}
xs=[round(-24+0.25*i,2) for i in range(int(48/0.25)+1)]; zs=[round(-4.875+0.25*i,3) for i in range(40)]
for x in xs:
    for z in zs:
        h=down(CX+x,CZ+z,skip=('C_MARKET_ENTRY_V21_LOD0__layout__LY_P01_tile','A_LOD0__'))
        grid[(x,z)]=h; k=f'{h[0]}@{h[1]}' if h else 'MISS'; hist[k]=hist.get(k,0)+1
        if not h: miss.append((x,z))
R['streetGrid']={'localX':[-24,24],'localZ':[-4.875,4.875],'step':0.25,'n':len(grid),'hist':hist,'miss':miss[:20]}
J=[]
for (x,z),h in grid.items():
    for k in ((round(x+0.25,2),z),(x,round(z+0.25,3))):
        g=grid.get(k)
        if h and g and abs(h[0]-g[0])>0.005: J.append(round(abs(h[0]-g[0]),4))
R['streetGrid']['adjacentJumps>5mm']={'n':len(J),'values':sorted(set(J))}
# 2 eave clearance over the street band: lowest tile/timber underside above street (ray up from 0.25)
low=None
for x in xs[::2]:
    for z in zs[::2]:
        for n,t in T.items():
            if not n.startswith('C_MARKET_ENTRY'): continue
            h=t.ray_cast(g2b(CX+x,0.25,CZ+z),Vector((0,0,1)),20)
            if h[0] is not None and (low is None or h[0].z<low[0]): low=(round(h[0].z,4),n,x,z)
R['minOverheadInStreetBand']=low
# 3 entrances (same 8 plinth fronts as library frontage; local coords)
ents=[(-15.8,-7.8,-5.0,-1),(-6.6,-0.6,-5.0,-1),(0.6,8.6,-5.0,-1),(9.8,15.8,-5.0,-1),(-14.2,-8.2,5.0,1),(-6.8,1.2,5.0,1),(2.6,8.6,5.0,1),(10.3,18.3,5.0,1)]
E=[]
for i,(x0,x1,fz,s) in enumerate(ents):
    xm=(x0+x1)/2
    fl=down(CX+xm,CZ+fz+s*0.3,only='C_MARKET_ENTRY_V21_LOD0__layout__LY_P01_earth')
    o=[down(CX+xm,CZ+fz-s*d,skip=('C_MARKET_ENTRY_V21_LOD0__layout__LY_P01_tile','A_LOD0__')) for d in (0.05,0.5,1.0,2.0,2.95,3.05)]
    E.append(dict(i=i+1,localX=[x0,x1],frontZ=fz,floor=fl,outside=o,rise=round(fl[0]-o[0][0],4),frontToRoutePublicEdge=round(abs(fz)-2.0,3)))
R['entrances']=E
# 4 well hole: ground ring and coverage
g=objs['C_market_ground_well_A']; M=g.matrix_world
bm=bmesh.new(); bm.from_mesh(g.data); bm.transform(M); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
bnd=[e for e in bm.edges if e.is_boundary]
# inner loop = boundary edges not on outer rectangle
inner=[e for e in bnd if all(184.29<v.co.x<244.28 and -1981.18<(-v.co.y)<-1937.19 for v in e.verts)]
iv={v for e in inner for v in e.verts}
if iv:
    cx=sum(v.co.x for v in iv)/len(iv); cz=sum(-v.co.y for v in iv)/len(iv)
    rr=[math.hypot(v.co.x-cx,-v.co.y-cz) for v in iv]
    R['groundHole']={'centreGLTF':[round(cx,4),round(cz,4)],'centreLocal':[round(cx-CX,4),round(cz-CZ,4)],'rMin':round(min(rr),4),'rMax':round(max(rr),4),'loopVerts':len(iv),'yLevels':sorted({round(v.co.z,4) for v in iv})}
else: R['groundHole']=None
R['groundBoundaryEdges']=len(bnd); bm.free()
if iv:
    # any non-well geometry over the hole (routes/frontage/boundary) between y 0.0 and 0.5
    cov=[]
    for n,t in T.items():
        if n.startswith('A_LOD0__') or n.startswith('C_market_ground'): continue
        for ang in range(0,360,30):
            for r in (0.0,0.3,0.55):
                X=cx+r*math.cos(math.radians(ang)); Z=cz+r*math.sin(math.radians(ang))
                h=t.ray_cast(g2b(X,3.0,Z),Vector((0,0,-1)),5)
                if h[0] is not None and h[0].z<0.6: cov.append((n,round(X,3),round(Z,3),round(h[0].z,3)))
    R['holeCoveredByNonWell']=cov
    hc=down(cx,cz,top=0.19,only='C_market_ground')
    R['groundBelowHoleCentreFromY0.19']=hc
    # distances from hole to route rectangles
    rects={}
    for n,o in objs.items():
        if n.startswith('route_'):
            vs=[o.matrix_world@v.co for v in o.data.vertices]; rects[n]=(min(v.x for v in vs),max(v.x for v in vs),min(-v.y for v in vs),max(-v.y for v in vs))
    def dist(r):
        dx=max(r[0]-cx,0,cx-r[1]); dz=max(r[2]-cz,0,cz-r[3]); return round(math.hypot(dx,dz),3)
    R['holeToRouteDistance']={n:dist(r) for n,r in rects.items()}
    R['holeToStreetBandEdge(local|z|=5)']=round(abs(cz-CZ)-5.0,3)
# 5 route/ground stack: bottoms of route_* vs ground top
st={}
for n,o in objs.items():
    if n.startswith('route_'):
        ys=[(o.matrix_world@v.co).z for v in o.data.vertices]; st[n]=[round(min(ys),4),round(max(ys),4)]
R['routeYRange']=st
json.dump(R,open(out,'w',encoding='utf-8'),indent=1,default=str); print('OK')
