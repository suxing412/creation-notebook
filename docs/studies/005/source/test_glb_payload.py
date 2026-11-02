"""Regression tests for corrupted GLB payloads; failures never enter asset folders."""
import json,struct,subprocess,sys,copy
from pathlib import Path
source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);checker=Path(__file__).with_name('check_glb.py');data=source.read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);binary=bytearray(data[28+n:]);prim=doc['meshes'][0]['primitives'][0]
def pack(d,b):
 raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);b=bytes(b)+b'\0'*((-len(b))%4);return struct.pack('<III',0x46546C67,2,12+8+len(raw)+8+len(b))+struct.pack('<II',len(raw),0x4E4F534A)+raw+struct.pack('<II',len(b),0x004E4942)+b
cases=[]
for name in ['nan-position','out-of-range-index','stride-overrun','false-bounds']:
 d=copy.deepcopy(doc);b=bytearray(binary)
 if name=='nan-position':
  a=d['accessors'][prim['attributes']['POSITION']];v=d['bufferViews'][a['bufferView']];struct.pack_into('<f',b,v.get('byteOffset',0)+a.get('byteOffset',0),float('nan'))
 elif name=='out-of-range-index':
  a=d['accessors'][prim['indices']];v=d['bufferViews'][a['bufferView']];fmt={5121:'B',5123:'H',5125:'I'}[a['componentType']];bad={5121:255,5123:65535,5125:4294967295}[a['componentType']];struct.pack_into('<'+fmt,b,v.get('byteOffset',0)+a.get('byteOffset',0),bad)
 elif name=='stride-overrun':
  a=d['accessors'][prim['attributes']['POSITION']];d['bufferViews'][a['bufferView']]['byteStride']=124
 else:d['accessors'][prim['attributes']['POSITION']]['max'][0]+=1
 model=out/(name+'.glb');model.write_bytes(pack(d,b));q=subprocess.run([sys.executable,str(checker),str(model),str(out/(name+'-report.json'))],capture_output=True,text=True);cases.append({'case':name,'rejected':q.returncode!=0,'final_error':q.stderr.strip().splitlines()[-1] if q.stderr.strip() else None})
r={'passed':all(c['rejected'] for c in cases),'cases':cases};(out/'summary.json').write_text(json.dumps(r,indent=2));assert r['passed'];print(json.dumps(r,indent=2))
