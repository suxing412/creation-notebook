"""Restore the original sibling layout from a downloaded docs tree; no network."""
from pathlib import Path
import json,hashlib,shutil,argparse
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
source=Path(__file__).resolve().parent;docs=source.parents[2];meta=json.loads((source/'public-layout-map.json').read_text())
if a.output.exists():raise SystemExit('Choose a new output directory; existing files are never overwritten.')
a.output.mkdir(parents=True)
shutil.copytree(source,a.output/'luoyang-passage-wfc-study')
for row in meta['mapping']:
 b=(docs/row['published']).read_bytes()
 assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
 target=a.output/row['restored'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
shutil.copy2(docs/meta['originalContract'],a.output/'luoyang-passage-interface-modules/contract.json')
print('Restored four byte-identical modules and original contract; run solve.py/make_demo.py or Blender render.py in the restored method directory.')
