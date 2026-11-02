"""Pixel/file identity and same-condition checks after lossless PNG metadata cleanup.
Does not replace human visual inspection or saved-scene/camera audit."""
import json,argparse,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--report',required=True);a=p.parse_args();out=ROOT/a.report
if out.exists():raise ValueError('Use fresh report')
records=[];checks={};infos=[];views=['beauty','front','side','top','rear','hole-detail']
for name in ['veil','horizon','fold']:
 d=ROOT/'assets'/name;i=json.loads((d/'model-info.json').read_text());infos.append(i);hashes=[]
 for view in views+['beauty-wide']:
  f=d/(view+'.png');im=Image.open(f);im.load();filehash=hashlib.sha256(f.read_bytes()).hexdigest();pixelhash=hashlib.sha256(im.tobytes()).hexdigest();records.append({'variant':name,'view':view,'dimensions':im.size,'bytes':f.stat().st_size,'file_sha256':filehash,'pixels_sha256':pixelhash,'metadata_keys':list(im.info)});hashes.append(pixelhash);checks[name+'-'+view+'-size']=im.size==((1584,960) if view=='beauty-wide' else (960,960));checks[name+'-'+view+'-no-metadata']=not im.info
 checks[name+'-distinct-view-pixels']=len(set(hashes))==7
for key in ['samples','adaptive_sampling','denoiser','view_transform','exposure','seed','fixed_camera','resolution','views','background_linear','world_color','editorial_wide']:
 checks['three-variants-fixed-'+key]=all(i['studio'][key]==infos[0]['studio'][key] for i in infos)
checks['fixed-material']=all(i['material']==infos[0]['material'] for i in infos)
b=json.loads((ROOT/'review/comparison-before/model-info.json').read_text())
for key in ['samples','adaptive_sampling','denoiser','view_transform','exposure','seed','fixed_camera','resolution','views','background_linear','world_color']:
 checks['before-after-fixed-'+key]=b['studio'][key]==infos[0]['studio'][key]
checks['before-after-fixed-material']=b['material']==infos[0]['material']
r={'passed':all(checks.values()),'checks':checks,'images':records,'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Actual image bytes/dimensions/unique pixel identities, declared same studio settings and material. Saved scene is independently audited; human multi-view review is separately recorded. No GPU/phone or pixel-equality guarantee across hardware.'};out.write_text(json.dumps(r,indent=2));print('IMAGE AUDIT',r['passed']);raise SystemExit(0 if r['passed'] else 1)
