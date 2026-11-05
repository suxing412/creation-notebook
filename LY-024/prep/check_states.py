"""LY-024 prep: state checker for a future S84-type closure kit (read-only on inputs).
blender -b --factory-startup --python-exit-code 1 -P check_states.py -- <host.glb> <out.json> [--state NAME=path.glb ...] [--expect NAME=open|closed ...]
Frame: S84 local (glTF Y-up metres, front edge z=0, street at +z). Host must be the frozen S84 GLB (SHA bound in test-plan.md).
Checks per state (host + that state's closure GLB only; states are never co-loaded):
  C1 front-plane coverage: ray grid from street (z=+1.0 -> -z) inside opening x[-3.5,3.5] y[0.22,3.0]; fraction whose FIRST hit is closure geometry.
  C2 entrance envelope: body box sweep along each side passage (x in [2.45,3.45] or mirrored, y 0.22..0.22+H, z from +0.6 to -1.6) must be free of closure geometry (open state) ; for closed state it must be blocked.
  C3 host overlap: BVH overlap pairs between closure and host parts (posts/beam/counter/legs/earth) -> listed for classification (allowed only if in the classified-contact list).
  C4 support: lowest closure verts must lie on floor top y=0.22 +-0.005 or on declared sill; none floating > 0.005.
"""
import bpy, bmesh, sys, json, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--')+1:]
host, out = a[0], a[1]; states={}; expect={}
i=2
while i < len(a):
    if a[i]=='--state': k,v=a[i+1].split('=',1); states[k]=v; i+=2
    elif a[i]=='--expect': k,v=a[i+1].split('=',1); expect[k]=v; i+=2
    else: i+=1
sha=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
G=lambda x,y,z: Vector((x,-z,y))   # glTF -> Blender
def load(path):
    before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    obs=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    bm=bmesh.new()
    for o in obs:
        t=bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world); me=bpy.data.meshes.new('t'); t.to_mesh(me); bm.from_mesh(me); t.free()
    bm.verts.ensure_lookup_table()
    for o in obs: bpy.data.objects.remove(o)
    return bm
def bvh(bm): return BVHTree.FromBMesh(bm)
bpy.ops.wm.read_factory_settings(use_empty=True)
H=bvh(load(host))
BODY={'w':0.6,'d':0.4,'h':1.75}  # C placeholder; replace with LY-006/010 frozen body envelope
def coverage(C, step=0.05):
    hit=tot=0
    x=-3.5+step/2
    while x<3.5:
        y=0.22+step/2
        while y<3.0:
            o=G(x,y,1.0); d=G(0,0,-1)-G(0,0,0)
            hc=C.ray_cast(o,d,3.0) if C else (None,)*4
            hh=H.ray_cast(o,d,3.0)
            tot+=1
            if hc[0] is not None and (hh[0] is None or hc[3]<=hh[3]+1e-6): hit+=1
            y+=step
        x+=step
    return round(hit/tot,4), tot
def body_blocked(C, side):
    """C2: body cross-section (w x h) swept along -z through side passage centred x=2.95*side, from z=+0.6 to z=-1.6.
    Horizontal rays on a 5x8 grid of the cross-section; blocked if any ray hits that tree within the sweep."""
    cx=2.95*side; res={'closure':False,'host':False,'closureHitRays':0}
    d=G(0,0,-1)-G(0,0,0)
    for i in range(5):
        x=cx-BODY['w']/2+BODY['w']*i/4
        for j in range(8):
            y=0.22+0.02+(BODY['h']-0.02)*j/7
            o=G(x,y,0.6)
            for tree,key in ((C,'closure'),(H,'host')):
                if tree is None: continue
                r=tree.ray_cast(o,d,2.2)
                if r[0] is not None:
                    res[key]=True
                    if key=='closure': res['closureHitRays']+=1
    return res
report={'host':host,'hostSha256':sha(host),'body':BODY,'baselineHostOnly':{},'states':{}}
report['baselineHostOnly']['frontCoverage']=coverage(None)
report['baselineHostOnly']['passage']={s:body_blocked(None,s) for s in (-1,1)}
for name,path in states.items():
    bm=load(path); C=bvh(bm)
    cov=coverage(C)
    pas={s:body_blocked(C,s) for s in (-1,1)}
    ov=H.overlap(C)
    ys=[ (v.co.z) for v in bm.verts]; lowest=min(ys)
    r={'path':path,'sha256':sha(path),'frontCoverage':cov,'passage':pas,'hostOverlapTriPairs':len(ov),'lowestY':round(lowest,4)}
    e=expect.get(name)
    if e=='open':  r['pass']= cov[0]<0.05 and not any(p['closure'] for p in pas.values()) and len(ov)==0
    r['supportOK']= abs(lowest-0.22)<=0.005
    if e=='closed': r['pass']= cov[0]>=0.99 and all(p['closure'] for p in pas.values()) and len(ov)==0 and r['supportOK']
    report['states'][name]=r
json.dump(report,open(out,'w',encoding='utf-8'),indent=1)
print('OK',json.dumps(report)[:800])
