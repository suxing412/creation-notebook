"""Sanitized complete offline delivery, inside this study only; never deploys or mutates old studies."""
import argparse,hashlib,json,shutil,zipfile,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ALLOW_DIRS={'assets','configs','source','review','vendor','viewer'}
ALLOW_FILES={'README.md','schema.json','parameter-contract.json'}
VARIANTS=['veil','horizon','fold']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allowed(p):
 rel=p.relative_to(ROOT)
 if not p.is_file() or '__pycache__' in rel.parts or p.suffix in {'.pyc','.log','.blend1','.blend2'}:return False
 if rel.parts[0]=='assets' and (len(rel.parts)<2 or rel.parts[1] not in VARIANTS):return False
 # The invalid first binary is retained privately, never presented as a working model.
 if len(rel.parts)>2 and rel.parts[:2]==('review','first-version') and p.suffix in {'.blend','.glb'}:return False
 return rel.parts[0] in ALLOW_DIRS or str(rel) in ALLOW_FILES

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='delivery');p.add_argument('--zip',default='veil-008-complete.zip');p.add_argument('--identity-map',required=True);a=p.parse_args();out=(ROOT/a.output).resolve();archive=(ROOT/a.zip).resolve()
 if not out.is_relative_to(ROOT) or not archive.is_relative_to(ROOT) or out.exists() or archive.exists():raise ValueError('Use new output/archive paths inside this study')
 identity=json.loads(Path(a.identity_map).read_text())
 if set(identity)!=set(VARIANTS):raise ValueError('Exactly three final identity mappings required')
 for variant,rel in identity.items():
  info=json.loads((ROOT/'assets'/variant/'model-info.json').read_text())
  if info['construction']['edge_steps']!=16 or info['construction']['hole_loop_vertices']!=64:raise ValueError('Only final 64-point production assets may be packaged')
  report=ROOT/rel;r=json.loads(report.read_text())
  if (ROOT/'assets'/variant/info.get('final_identity_report','')).resolve()!=report.resolve():raise ValueError('Metadata report reference differs from explicit manifest mapping')
  if not r.get('passed') or not r.get('inputs_stable_during_checks'):raise ValueError('Final identity is not a pass: '+rel)
  for key,path in {'native':f'assets/{variant}/model.blend','glb':f'assets/{variant}/model.glb','info':f'assets/{variant}/model-info.json','native_checker':'source/check.py','glb_checker':'source/check_glb.py','recipe':'source/recipe.py','comparison_checker':'source/compare_exports.py'}.items():
   if r['input_sha256'][key]!=sha(ROOT/path):raise ValueError('Stale final identity '+variant+' '+key)
  if r['wrapper_sha256']!=sha(ROOT/'source/run_gates.py'):raise ValueError('Stale wrapper identity')
 rows=[]
 for path in sorted(q for q in ROOT.rglob('*') if allowed(q)):
  rel=path.relative_to(ROOT);data=path.read_bytes()
  if path.suffix in {'.blend','.glb','.png','.json','.md','.html','.css','.js','.mjs','.cjs','.py'}:
   if re.search(rb'/workspace/(?:scratch|shared)/[A-Za-z0-9_-]{6,}',data):raise ValueError('Private workspace identifier in '+str(rel))
   if path.suffix in {'.blend','.glb','.png','.json'} and any(m in data for m in [b'/workspace/',b'/home/agent/',b'/tmp/',b'file://']):raise ValueError('Private path marker in '+str(rel))
  if path.suffix=='.png':
   im=Image.open(path);im.load()
   if im.info:raise ValueError('Unstripped PNG metadata '+str(rel))
  rows.append({'path':str(rel),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'purpose':{'assets':'Final actual native / GLB / CPU photographs','configs':'Finite reusable configuration','source':'Executable recipe and QA source','review':'Method review, finite gate evidence, before/after images','vendor':'Pinned Three r180 dependency and MIT license','viewer':'Independent observer and static fallback'}.get(rel.parts[0],'Reproduction or parameter contract')})
 manifest={'schema_version':'1.0','study':'008','name':'VEIL / 透幕','version':'1.0.0','recipe_version':'1.0.0','date_utc':'2026-11-02','files':rows,'total_bytes_excluding_manifest':sum(q['bytes'] for q in rows),'final_identity_reports':identity,'manifest_does_not_hash_itself':True,'contains_source_archive_itself':False,'entrypoints':{'independent_model_viewer':'viewer/index.html','independent_web_design':'index.html supplied by separate web author'},'excluded':['work/**','delivery/**','archives themselves','raw logs','counterexample binaries','invalid original first-version binaries','external reference images'],'unverified':['GPU playback','dynamic flicker','physical phone/touch','manufacture/load/stability']}
 text=json.dumps(manifest,ensure_ascii=False,indent=2);(ROOT/'manifest.json').write_text(text);out.mkdir()
 for q in rows:
  target=out/q['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/q['path'],target)
 (out/'manifest.json').write_text(text)
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for path in sorted(out.rglob('*')):
   if path.is_file():
    zi=zipfile.ZipInfo(str(path.relative_to(out)),date_time=(2026,11,2,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o644<<16;z.writestr(zi,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 with zipfile.ZipFile(archive) as z:
  if z.testzip() is not None:raise ValueError('ZIP CRC error')
  for q in rows:
   if hashlib.sha256(z.read(q['path'])).hexdigest()!=q['sha256']:raise ValueError('ZIP entry mismatch')
 result={'passed':True,'directory':str(out.relative_to(ROOT)),'file_count':len(rows)+1,'uncompressed_bytes':sum(q['bytes'] for q in rows)+(out/'manifest.json').stat().st_size,'manifest_sha256':sha(ROOT/'manifest.json'),'archive':archive.name,'zip_bytes':archive.stat().st_size,'zip_sha256':sha(archive),'zip_crc_and_entry_sha_verified':True}
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
