"""A narrow AST regression guard: native failure-record append targets must be declared string keys.
This supplements, never substitutes for, actual bad-mesh dedicated-field tests.
"""
import ast,argparse,json,hashlib,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--checker',required=True);p.add_argument('--report',required=True);a=p.parse_args();checker=Path(a.checker);out=Path(a.report)
if out.exists():raise RuntimeError('Fresh report required')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();tree=ast.parse(checker.read_text());fields=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FAIL_FIELDS' for t in n.targets));issues=[];targets=[]
for n in ast.walk(tree):
 if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='r' and isinstance(n.slice,ast.Tuple):issues.append({'line':n.lineno,'reason':'tuple_report_key_is_not_allowed'})
 if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='append':
  q=n.func.value
  if isinstance(q,ast.Subscript) and isinstance(q.value,ast.Name) and q.value.id=='r':
   key=ast.literal_eval(q.slice) if isinstance(q.slice,ast.Constant) else None;targets.append({'line':n.lineno,'field':key})
   if key not in fields:issues.append({'line':n.lineno,'reason':'failure_append_key_not_declared','field':key})
r={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'passed':not issues,'checker_sha256':sha(checker),'test_script_sha256':sha(__file__),'append_targets':targets,'issues':issues,'scope':'AST key-shape/declaration regression only. Does not execute Blender, validate geometry or prove branch coverage.'};out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2));print('QA SOURCE CONTRACT',r['passed']);raise SystemExit(0 if r['passed'] else 1)
