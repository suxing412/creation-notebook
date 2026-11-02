"""Static contact QA, not a guarantee of realtime depth-buffer behaviour."""
import bpy,os,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import sys,argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--report',required=True)
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=args.model)
objects=[o for o in bpy.data.objects if o.type=='MESH'];data={};duplicates=[];seen={};degenerate=0
for o in objects:
 me=o.data;me.calc_loop_triangles();vv=[o.matrix_world@v.co for v in me.vertices];tt=[tuple(t.vertices) for t in me.loop_triangles]
 for k,t in enumerate(tt):
  pts=[vv[i] for i in t];area=(pts[1]-pts[0]).cross(pts[2]-pts[0]).length/2
  if area<1e-10:degenerate+=1
  key=tuple(sorted(tuple(round(c,7) for c in p) for p in pts))
  if key in seen:duplicates.append([seen[key],[o.name,k]])
  seen[key]=[o.name,k]
 data[o.name]=(vv,tt,BVHTree.FromPolygons(vv,tt,all_triangles=True))
self_intersections={}
for name,(vv,tt,tree) in data.items():
 hits=[(a,b) for a,b in tree.overlap(tree) if a<b and not set(tt[a]).intersection(tt[b])]
 if hits:self_intersections[name]=len(hits)
pairs=[];coplanar=[]
for i,a in enumerate(objects):
 for b in objects[i+1:]:
  va,ta,ba=data[a.name];vb,tb,bb=data[b.name];overlaps=ba.overlap(bb)
  if not overlaps:continue
  cp=0
  for ia,ib in overlaps:
   pa=[va[x] for x in ta[ia]];pb=[vb[x] for x in tb[ib]]
   na=(pa[1]-pa[0]).cross(pa[2]-pa[0]).normalized();nb=(pb[1]-pb[0]).cross(pb[2]-pb[0]).normalized()
   if abs(na.dot(nb))>1-1e-7 and max(abs(na.dot(q-pa[0])) for q in pb)<1e-6:cp+=1
  pairs.append({'a':a.name,'b':b.name,'intersectingTrianglePairs':len(overlaps),'coplanarPairs':cp})
  if cp:coplanar.append([a.name,b.name,cp])
report={'method':'Blender BVHTree triangle intersections + cross-object coplanar plane test; duplicate faces by world-space vertices rounded 1e-7','nonAdjacentSelfIntersectionPairs':self_intersections,'objects':len(objects),'triangles':sum(len(t) for _,t,_ in data.values()),'degenerateTriangles':degenerate,'duplicateTriangleCount':len(duplicates),'coplanarCrossObjectPairs':coplanar,'contacts':pairs,'limitations':['Not a boolean-unified fabrication mesh','Intentional embedded seams and tail root intersect wing skin','Static mesh tests cannot prove absence of WebGL z-fighting at all camera distances','BVH test does not certify absence of fully enclosed volumes']}

ALLOWED=[['A | continuous porcelain wing', 'B | leading copper seam'], ['A | continuous porcelain wing', 'B | trailing copper seam'], ['A | continuous porcelain wing', 'C | swept copper inlay -1'], ['A | continuous porcelain wing', 'C | swept copper inlay 1'], ['A | continuous porcelain wing', 'E | tapered ceramic tail'], ['A | continuous porcelain wing', 'F | tail copper spine'], ['A | continuous porcelain wing', 'G | copper dorsal midrib'], ['B | leading copper seam', 'B | trailing copper seam'], ['B | trailing copper seam', 'E | tapered ceramic tail'], ['E | tapered ceramic tail', 'F | tail copper spine']]
nonmanifold={}
for o in objects:
 edges={}
 for poly in o.data.polygons:
  v=list(poly.vertices)
  for a,b in zip(v,v[1:]+v[:1]):
   k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
 bad=sum(v!=2 for v in edges.values())
 if bad:nonmanifold[o.name]=bad
unexpected=[x for x in pairs if sorted([x['a'],x['b']]) not in ALLOWED]
missing=[x for x in ALLOWED if not any(sorted([p['a'],p['b']])==x for p in pairs)]
report.update(nonManifoldEdges=nonmanifold,unexpectedContactGroups=unexpected,missingExpectedContactGroups=missing,allowedContactPairs=ALLOWED,blenderVersion=bpy.app.version_string)
report['passed']=not any([duplicates,degenerate,coplanar,self_intersections,nonmanifold,unexpected,missing])
report['contactPolicy']='Pair allowlist inherited from original embedded seam assembly; contact counts remain measured, not zero. Does not certify penetration depth or hidden enclosing volumes.'
Path(args.report).write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if not report['passed']:raise RuntimeError('QUALITY GATE REJECTED: see report')
