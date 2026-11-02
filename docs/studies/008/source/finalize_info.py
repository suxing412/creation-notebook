"""Write descriptive report references BEFORE locked gates; a prose field is never a PASS."""
import argparse,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--asset',required=True);p.add_argument('--identity-report');a=p.parse_args();d=Path(a.asset).resolve();path=d/'model-info.json';i=json.loads(path.read_text());name=i['variant']
if not d.is_relative_to(ROOT):raise ValueError('Asset must be in this study')
if i['construction']['hole_loop_vertices']!=64 or i['construction']['edge_steps']!=16:raise ValueError('Final production requires 64-point apertures')
if a.identity_report is None:
 if d!=ROOT/'assets'/name:raise ValueError('Rebuilt outputs must provide their own --identity-report, never point at the original release report')
 report=ROOT/'review'/('gate-locked-'+name+'-v1-identity.json')
else:report=(ROOT/a.identity_report).resolve()
if not report.is_relative_to(ROOT/'review') or report.suffix!='.json':raise ValueError('Report reference must be within review/')
i['validation_status']='external_report_required';i['final_identity_report']=os.path.relpath(report,d);i['normal_semantics']='Analytic face-corner normals on explicit curved surface and real roundover; native storage/GLB corner vector tolerance is in the bound comparison report.';i['sampling_semantics']='64 vertices per aperture ring, 16 per shared cell edge; historical 32-point files and reports are not final production identities.'
path.write_text(json.dumps(i,ensure_ascii=False,separators=(',',':')))
