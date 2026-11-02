"""Malformed GLB controls for the 009 reader. Corrupt payloads remain in work only."""
import copy,struct,json,hashlib,datetime
from pathlib import Path
import audit_payload
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'work/qa-controls-final/valid/model.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];base=json.loads(raw[20:20+n]);binary=raw[28+n:];out=ROOT/'work/qa-payload-controls-final';out.mkdir(exist_ok=True)
def pack(j,b):
 text=json.dumps(j,separators=(',',':')).encode();text+=b' '*(-len(text)%4);b+=b'\0'*(-len(b)%4);return struct.pack('<III',0x46546c67,2,28+len(text)+len(b))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(b),0x004e4942)+b
rows=[]
for name,expected in [('valid',None),('header_length','header'),('view_overrun','view_bounds'),('bad_stride','stride'),('bad_index','index_range'),('position_nan','nonfinite'),('normal_nan','nonfinite'),('bound_mismatch','bounds'),('external_buffer','buffer')]:
 j=copy.deepcopy(base);b=bytearray(binary);prim=j['meshes'][0]['primitives'][0]
 if name=='view_overrun':j['bufferViews'][0]['byteLength']=len(b)+100
 if name=='bad_stride':j['bufferViews'][0]['byteStride']=3
 if name in('position_nan','normal_nan','bad_index'):
  ai=prim['indices']if name=='bad_index'else prim['attributes']['POSITION'if name=='position_nan'else'NORMAL'];ac=j['accessors'][ai];v=j['bufferViews'][ac['bufferView']];off=v.get('byteOffset',0)+ac.get('byteOffset',0)
  if name=='bad_index':fmt={5121:'B',5123:'H',5125:'I'}[ac['componentType']];struct.pack_into('<'+fmt,b,off,{5121:255,5123:65535,5125:4294967295}[ac['componentType']])
  else:struct.pack_into('<f',b,off,float('nan'))
 if name=='bound_mismatch':j['accessors'][prim['attributes']['POSITION']]['min'][0]-=.001
 if name=='external_buffer':j['buffers'][0]['uri']='not-allowed.bin'
 data=pack(j,bytes(b))
 if name=='header_length':data=data[:8]+struct.pack('<I',len(data)+4)+data[12:]
 target=out/(name+'.glb');target.write_bytes(data);code=None;ok=False
 try:audit_payload.decode(target);ok=True
 except Exception as e:code=getattr(e,'code',type(e).__name__)
 rows.append({'case':name,'expected_code':expected,'observed_code':code,'reader_passed':ok,'targeted_condition_observed':ok if expected is None else code==expected,'sha256':audit_payload.sha(target)})
r={'passed':all(x['targeted_condition_observed']for x in rows),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checker_sha256':audit_payload.sha(audit_payload.__file__),'control_script_sha256':audit_payload.sha(__file__),'valid_source_sha256':audit_payload.sha(p),'cases':rows};(ROOT/'review/qa-payload-controls-final.json').write_text(json.dumps(r,indent=2));print('PAYLOAD CONTROLS',r['passed']);assert r['passed']
