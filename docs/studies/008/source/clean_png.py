"""Losslessly strip metadata from local generated PNG evidence; pixel bytes are verified unchanged."""
from pathlib import Path
from PIL import Image
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('paths',nargs='+');p.add_argument('--report',required=True);a=p.parse_args()
if Path(a.report).exists():raise ValueError('Use new report path')
rows=[]
for arg in a.paths:
 for path in sorted(Path(arg).rglob('*.png')):
  if not path.resolve().is_relative_to(ROOT):raise ValueError('Only this study may be cleaned')
  relative=path.resolve().relative_to(ROOT);backup=ROOT/'work'/'png-originals'/relative;backup.parent.mkdir(parents=True,exist_ok=True)
  if not backup.exists():shutil.copy2(path,backup)
  elif hashlib.sha256(backup.read_bytes()).hexdigest()!=hashlib.sha256(path.read_bytes()).hexdigest():
   alternate=backup.with_name(backup.stem+'-'+hashlib.sha256(path.read_bytes()).hexdigest()[:12]+'.png')
   if not alternate.exists():shutil.copy2(path,alternate)
  im=Image.open(path);im.load();mode=im.mode;size=im.size;pixelhash=hashlib.sha256(im.tobytes()).hexdigest();oldsha=hashlib.sha256(path.read_bytes()).hexdigest();metadata=list(im.info);clean=Image.frombytes(mode,size,im.tobytes());clean.save(path,format='PNG',compress_level=9);after=Image.open(path);after.load();assert hashlib.sha256(after.tobytes()).hexdigest()==pixelhash and not after.info
  rows.append({'path':str(relative),'size':size,'mode':mode,'pixels_sha256':pixelhash,'before_file_sha256':oldsha,'after_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'removed_metadata_keys':metadata,'pixel_identical':True})
Path(a.report).write_text(json.dumps({'passed':True,'images':rows,'method':'Pillow same-mode same-size same pixel bytes; metadata removed; no rescale, recolor or denoise. Exact original files retained privately under work/png-originals.'},indent=2))
