"""Report observed asset bytes and available job wall times; no invented billing/GPU claims."""
import json,argparse,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--report',default='review/costs.json');a=p.parse_args();rows=[]
for variant in ['veil','horizon','fold']:
 d=ROOT/'assets'/variant;info=json.loads((d/'model-info.json').read_text());files=[{'path':str(q.relative_to(ROOT)),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in sorted(d.iterdir()) if q.is_file()];rows.append({'variant':variant,'native_vertices':info['vertices'],'triangles':info['triangles'],'six_view_generation_wall_seconds':info.get('elapsed_seconds'),'wide_generation_wall_seconds':info.get('editorial_wide_elapsed_seconds'),'files':files,'total_bytes':sum(q['bytes'] for q in files)})
history=[]
for rel in ['review/first-version','review/baseline-corrected','review/comparison-before','work/refined-draft','work/refined-corrected','work/horizon-draft','work/fold-draft','work/edge64-probe','work/intermediate-32-comparison-before','work/intermediate-32-assets/veil','work/intermediate-32-assets/horizon','work/intermediate-32-assets/fold']:
 q=ROOT/rel/'model-info.json'
 if q.exists():
  i=json.loads(q.read_text());history.append({'label':rel,'available_generation_wall_seconds':i.get('elapsed_seconds'),'samples':i['studio']['samples'],'resolution':i['studio']['resolution'],'note':'Intermediate/review job. Not part of final asset total; wall times can overlap with other jobs.'})
r={'study':'008','measured_asset_bytes':sum(q['total_bytes'] for q in rows),'assets':rows,'historical_available_wall_times':history,'render_environment':'Blender 4.3.2 Cycles CPU; final 128 samples at 960 squared; wide 1584x960; no denoiser, adaptive sampling or GPU','accounting_limits':['No CPU-hours or electricity telemetry collected. Job wall seconds are not summed into elapsed workflow time because jobs can run concurrently.','No external model or asset purchasing calls were made. Platform/tool dollar billing was not available and is not invented.','Complete archive CRC/SHA/byte counts are reported separately after packaging to avoid self-referential hashes.','A publication projection can use lossless ZIP and shared same-SHA vendor; full source is retained and not deleted to fit a site.'],'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(ROOT/a.report).write_text(json.dumps(r,indent=2))
