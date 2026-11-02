"""Static asset and fallback state-machine checks. Not a browser/GPU test."""
from pathlib import Path
from html.parser import HTMLParser
import re,json,subprocess
r=Path(__file__).resolve().parents[1];d=r/'dist';html=(d/'index.html').read_text();missing=[];refs=[]
class Parser(HTMLParser):
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  for k in ['href','src']:
   v=a.get(k,'')
   if not v or v.startswith(('http','#','../../')):continue
   refs.append(v)
   if not (d/v).exists():missing.append(v)
Parser().feed(html)
views=re.findall(r'data-view="([a-z]+)"',html)
for v in views:
 if not (d/'assets'/f'{v}.png').exists():missing.append(f'view:{v}')
for p in ['vendor/three.module.js','vendor/three.core.js','vendor/addons/controls/OrbitControls.js','vendor/addons/loaders/GLTFLoader.js','vendor/addons/environments/RoomEnvironment.js','assets/model-info.json','assets/limen.glb']:
 if not (d/p).exists():missing.append(p)
subprocess.run(['node','--check',str(d/'app.js')],check=True)
script=re.findall(r'<script>(.*?)</script>',html,re.S)[0]
node="""const vm=require('vm');const assert=require('assert');const buttons=KEYS.map(key=>({dataset:{view:key},textContent:key,attributes:{},setAttribute(k,v){this.attributes[k]=v;}}));const elements={'#poster':{},'#scene':{},'#badge':{}};const context={window:{},document:{querySelectorAll:s=>buttons,querySelector:s=>elements[s]}};vm.createContext(context);vm.runInContext(SCRIPT,context);for(const b of buttons){b.onclick();assert.equal(elements['#poster'].src,'assets/'+b.dataset.view+'.png');assert.equal(elements['#poster'].hidden,false);assert.equal(elements['#scene'].hidden,true);assert.equal(b.attributes['aria-pressed'],'true');assert.equal(buttons.filter(x=>x.attributes['aria-pressed']==='true').length,1);}console.log('Seven inline static views work without Three.js');""".replace('KEYS',json.dumps(views)).replace('SCRIPT',json.dumps(script))
subprocess.run(['node','-e',node],check=True)
out={'missing':missing,'staticViews':views,'inlineFallbackStateTest':True,'nodeSyntax':True,'referencesChecked':len(refs),'browserRendered':False,'webglVerified':False,'mobileVerified':False};(d/'assets/web-check.json').write_text(json.dumps(out,indent=2));print(out);assert not missing
