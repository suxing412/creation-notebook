# Read-only GLB node lister: prints nodes (name, mesh, TRS) and mesh names; filter by regex.
import json, struct, sys, re, hashlib
def load(p):
    b=open(p,'rb').read()
    assert b[:4]==b'glTF'
    l=struct.unpack('<I',b[12:16])[0]
    return json.loads(b[20:20+l]), hashlib.sha256(b).hexdigest(), len(b)
pat=re.compile(sys.argv[1], re.I) if len(sys.argv)>2 else None
for p in (sys.argv[2:] if pat else sys.argv[1:]):
    j,sha,n=load(p)
    nodes=j.get('nodes',[]); meshes=j.get('meshes',[])
    print('##',p,sha[:12],n,'nodes',len(nodes),'meshes',len(meshes),'mats',[m.get('name') for m in j.get('materials',[])][:40])
    for i,nd in enumerate(nodes):
        nm=nd.get('name','');mn=meshes[nd['mesh']].get('name','') if 'mesh' in nd else ''
        if pat and not (pat.search(nm) or pat.search(mn)): continue
        print(i,repr(nm),'mesh=',repr(mn),'T=',nd.get('translation'),'R=',nd.get('rotation'),'S=',nd.get('scale'),'children=',len(nd.get('children',[])))
