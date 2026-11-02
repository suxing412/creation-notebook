#!/usr/bin/env python3
"""Seal a completed local directory; list exact bytes excluding this inventory itself."""
from pathlib import Path
import argparse,hashlib,json,datetime,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);a=p.parse_args();root=Path(a.directory).resolve();assert root.is_dir();out=root/'WEB-FROZEN-SHA256.json';rows=[]
# An unsuccessful reseal must not leave an older inventory looking current.
if out.exists():out.unlink()
checks=[['node','web-source/test_app.cjs'],[sys.executable,'web-source/test_diagrams.py'],[sys.executable,'web-source/verify.py'],[sys.executable,'web-source/verify_delivery.py','--directory',str(root)]]
for cmd in checks:
 result=subprocess.run(cmd,cwd=root)
 if result.returncode:raise SystemExit('Freeze refused: preflight failed '+str(cmd))
for report in ['unit-checks.json','diagram-tests.json','static-checks.json','delivery-files.json']:
 data=json.loads((root/'web-review'/report).read_text())
 if not data.get('passed'):raise SystemExit('Freeze refused: report does not pass '+report)
for f in sorted(root.rglob('*')):
 if f==out:continue
 if f.is_symlink():raise SystemExit('Refuse symlink '+str(f))
 if f.is_file():rows.append({'path':f.relative_to(root).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
r={'format':'sha256-file-inventory-v1','study':'006','frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Complete model + editorial delivery after local preflight; inventory excludes only itself; no deployment claim','files_count':len(rows),'bytes':sum(x['bytes'] for x in rows),'files':rows};out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files_count':len(rows),'bytes':r['bytes']},indent=2))
