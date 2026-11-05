# Pure-python GLB structure dump (no Blender). usage: python -I gltf_inspect.py file.glb
import json, struct, sys, hashlib
def load(p):
    b=open(p,'rb').read()
    magic,ver,ln=struct.unpack('<III',b[:12]); assert magic==0x46546C67
    cl,ct=struct.unpack('<II',b[12:20]); j=json.loads(b[20:20+cl])
    return b,j
for p in sys.argv[1:]:
    b,j=load(p)
    print('==',p,len(b),hashlib.sha256(b).hexdigest())
    print(' asset',j.get('asset'))
    print(' scenes',j.get('scenes'))
    for i,n in enumerate(j.get('nodes',[])):
        m=n.get('mesh'); prims=[]
        if m is not None:
            for pr in j['meshes'][m]['primitives']:
                acc=j['accessors'][pr['attributes']['POSITION']]
                prims.append((j['materials'][pr['material']].get('name') if 'material' in pr else None, acc['count'], [round(x,3) for x in acc.get('min',[])],[round(x,3) for x in acc.get('max',[])]))
        print(' node',i,n.get('name'),{k:n[k] for k in ('translation','rotation','scale','matrix','children') if k in n},'mesh',m,j['meshes'][m].get('name') if m is not None else '',prims, n.get('extras',''))
    print(' materials',[ (m.get('name'), m.get('extras','')) for m in j.get('materials',[])])
    if 'extras' in j.get('asset',{}): print(' asset extras',j['asset']['extras'])
    for s in j.get('scenes',[]):
        if 'extras' in s: print(' scene extras', json.dumps(s['extras'],ensure_ascii=False)[:3000])
