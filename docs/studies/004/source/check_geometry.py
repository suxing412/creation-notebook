"""Independent triangle-plane buckets and positive-area SAT. No BVH prerequisite for coplanarity."""
import bpy,bmesh,json,sys,os
from collections import defaultdict
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:];src,out=args
bpy.ops.wm.open_mainfile(filepath=src)
obs=[o for o in bpy.data.objects if o.type=='MESH'];zero_tris=0;planes=defaultdict(list);allfaces=defaultdict(list);deg=[];top=[];bvh={};bounds={};self_hits=[]
for o in obs:
    vs=[o.matrix_world@v.co for v in o.data.vertices]
    o.data.calc_loop_triangles()
    zero_tris+=sum((vs[t.vertices[1]]-vs[t.vertices[0]]).cross(vs[t.vertices[2]]-vs[t.vertices[0]]).length<2e-10 for t in o.data.loop_triangles)
    for p in o.data.loop_triangles:
        key=tuple(sorted(tuple(round(v,6) for v in vs[i]) for i in p.vertices))
        allfaces[key].append((o.name,p.index))
        if p.area<1e-10:deg.append((o.name,p.index))
        elif p.normal.length>0:
            normal=(vs[p.vertices[1]]-vs[p.vertices[0]]).cross(vs[p.vertices[2]]-vs[p.vertices[0]]).normalized()
            if next((x for x in normal if abs(x)>1e-6),1)<0:normal=-normal
            d=normal.dot(vs[p.vertices[0]])
            if max(abs(normal.dot(vs[i])-d) for i in p.vertices)<1e-6:
                axis=max(range(3),key=lambda k:abs(normal[k]));axes=[k for k in range(3) if k!=axis]
                pts=[tuple(vs[i][k] for k in axes) for i in p.vertices]
                planes[tuple(round(x,5) for x in normal)+(round(d,5),)].append((o.name,p.index,pts,tuple(p.vertices)))
    bm=bmesh.new();bm.from_mesh(o.data)
    nonman=sum(not e.is_manifold for e in bm.edges)
    if nonman:top.append({'object':o.name,'nonmanifold_edges':nonman})
    bm.free()
    bvh[o.name]=BVHTree.FromPolygons(vs,[tuple(p.vertices) for p in o.data.polygons],all_triangles=False,epsilon=0)
    triangles=[tuple(t.vertices) for t in o.data.loop_triangles]
    tb=BVHTree.FromPolygons(vs,triangles,all_triangles=True,epsilon=0)
    for aa,bb in tb.overlap(tb):
        if aa<bb and not set(triangles[aa]).intersection(triangles[bb]):self_hits.append({'object':o.name,'triangles':[aa,bb]})
    bounds[o.name]=[(min(v[k] for v in vs),max(v[k] for v in vs)) for k in range(3)]
dups=[v for v in allfaces.values() if len(v)>1]
def area_overlap(a,b):
    # Strict convex-polygon SAT: touching edges do not count as area overlap.
    for poly in [a,b]:
        for i in range(len(poly)):
            p,q=poly[i],poly[(i+1)%len(poly)];ax,ay=-(q[1]-p[1]),q[0]-p[0];length=(ax*ax+ay*ay)**.5
            if length<1e-10:continue
            ax/=length;ay/=length
            pa=[x*ax+y*ay for x,y in a];pb=[x*ax+y*ay for x,y in b]
            if min(max(pa),max(pb))-max(min(pa),min(pb))<=1e-6:return False
    return True
def shared_edge_separated(a,b):
    if a[0]!=b[0]:return False
    common=set(a[3]).intersection(b[3])
    if len(common)!=2:return False
    points=dict(zip(a[3],a[2]));points.update(zip(b[3],b[2]));u,v=[points[i] for i in common]
    ca=points[next(i for i in a[3] if i not in common)];cb=points[next(i for i in b[3] if i not in common)]
    cross=lambda p:(v[0]-u[0])*(p[1]-u[1])-(v[1]-u[1])*(p[0]-u[0])
    return cross(ca)*cross(cb)<=0
coplanar=[]
for group in planes.values():
    for i,a in enumerate(group):
        for b in group[i+1:]:
            if not shared_edge_separated(a,b) and all(min(max(p[k] for p in a[2]),max(p[k] for p in b[2]))-max(min(p[k] for p in a[2]),min(p[k] for p in b[2]))>1e-6 for k in range(2)) and area_overlap(a[2],b[2]):coplanar.append({'a':[a[0],a[1]],'b':[b[0],b[1]]})
pairs=[]
for i,a in enumerate(obs):
    for b in obs[i+1:]:
        ba,bb=bounds[a.name],bounds[b.name]
        if any(ba[k][1]<bb[k][0] or bb[k][1]<ba[k][0] for k in range(3)):continue
        hit=bvh[a.name].overlap(bvh[b.name])
        if hit:pairs.append({'a':a.name,'b':b.name,'bvh_polygon_pairs':len(hit)})
pairs.sort(key=lambda p:-p['bvh_polygon_pairs'])
r={'source':os.path.basename(src),'mesh_objects':len(obs),'nonadjacent_self_intersection_candidates':self_hits,'zero_area_triangles':zero_tris,'coplanar_area_overlap_candidates':coplanar,'zero_area_faces':len(deg),'zero_area_by_object':dict((n,sum(x[0]==n for x in deg)) for n in sorted(set(x[0] for x in deg))),'coincident_face_groups':len(dups),'coincident_faces':dups,'nonmanifold_by_object':top,'intersecting_object_candidates':len(pairs),'bvh_candidates':pairs,'limits':'Within- and cross-object triangle SAT; plane bucketing rounded 1e-5 and positive area threshold1e-6; shared-edge triangles on opposite sides excluded analytically. BVH overlap is a geometric candidate detector; it does not classify manufacturing contact or verify runtime z-fighting. Rounded exact face keys do not detect all coplanar partial overlaps.'}
with open(out,'w') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print('AUDIT',len(obs),'zero',len(deg),'duplicates',len(dups),'nonmanifoldObjects',len(top),'BVH',len(pairs))
assert not coplanar, 'Positive-area coplanar candidates require correction or explicit review.'
assert not deg and zero_tris==0 and not dups and not top and not self_hits, 'Geometry defects require correction.'
