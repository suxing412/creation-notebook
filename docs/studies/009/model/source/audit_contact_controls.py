"""009 contact-permission metadata controls; no bad binary is exported."""
import bpy,sys,copy,json,datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import audit_native
root=Path(__file__).resolve().parents[1];source=root/'assets/hinge/model-info.json';info=json.loads(source.read_text());rows=[]
for name in['valid','widen_radius','change_pair','wrong_pose_center','missing_zone']:
 q=copy.deepcopy(info)
 if name=='widen_radius':q['contact_regions'][0]['radius']=100
 if name=='change_pair':q['contact_regions'][0]['objects']=['Diffuser','Head neck']
 if name=='wrong_pose_center':q['pose']['head_center'][0]+=.01
 if name=='missing_zone':q['contact_regions'].pop()
 failures=audit_native.contact_contract(q);target=None if name=='valid'else'pose_metadata'if name=='wrong_pose_center'else'contact_region_contract';codes=[x['code']for x in failures];rows.append({'case':name,'expected_code':target,'observed_codes':codes,'targeted_condition_observed':not failures if target is None else target in codes})
r={'passed':all(q['targeted_condition_observed']for q in rows),'kind':'metadata predicate controls, not mesh fault controls','checker_sha256':audit_native.sha(audit_native.__file__),'control_script_sha256':audit_native.sha(__file__),'input_info_sha256':audit_native.sha(source),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':rows};(root/'review/qa-contact-controls-final.json').write_text(json.dumps(r,indent=2));print('CONTACT CONTROLS',r['passed']);assert r['passed']
