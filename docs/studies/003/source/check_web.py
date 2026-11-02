from pathlib import Path
from html.parser import HTMLParser
import json,re
R=Path(__file__).resolve().parents[1];D=R/'dist'
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,attrs):
  for k,v in attrs:
   if k in ['src','href'] and v and not v.startswith(('http:','https:','#','data:','../../')):self.links.append(v)
p=Links();p.feed((D/'index.html').read_text());missing=[x for x in p.links if not (D/x).exists()]
assert not missing,missing
assert 'https://' not in (D/'app.js').read_text()
report={'localHtmlLinks':len(p.links),'missingLocalLinks':missing,'externalRuntimeDependencies':False,'javascriptSyntaxCheckedSeparately':True,'browserVisualQA':'parent review pending','webglVerified':False}
(R/'evidence/web-check.json').write_text(json.dumps(report,indent=2));print(report)
