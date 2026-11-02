#!/usr/bin/env python3
"""Verify projected SVG paths against the input model-info coordinate contract."""
import json,math,re,xml.etree.ElementTree as ET,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];WR=R/'web-review' if (R/'web-review').exists() else R/'review';records=[];NS={'s':'http://www.w3.org/2000/svg'}
def xy(d):return [(float(a),float(b)) for a,b in re.findall(r'[ML]([-0-9.]+),([-0-9.]+)',d)]
def compare(pairs,points,scale,origin,center=(0,0)):
 assert len(pairs)==len(points),(len(pairs),len(points))
 err=max(math.hypot((x-origin[0])/scale+center[0]-p[0],-(y-origin[1])/scale+center[1]-p[1]) for (x,y),p in zip(pairs,points))
 assert err<1e-7,err
 return err
for v in ['folio','atlas','spire']:
 source=R/f'assets/{v}/model-info.json';info=json.loads(source.read_text());stations=info['construction']['stations'];t=info['config']['thickness']/2
 plus=[(s['point'][0]+s['normal'][0]*t,s['point'][1]+s['normal'][1]*t) for s in stations];minus=[(s['point'][0]-s['normal'][0]*t,s['point'][1]-s['normal'][1]*t) for s in stations]
 for kind,scale,origin in [('profile',1720,(380,412)),('small',970,(230,232))]:
  file=R/f'assets/diagrams/{v}-{kind}.svg';svg=ET.fromstring(file.read_text());center=svg.find('s:path[@class="center-line"]',NS);shell=svg.find('s:path[@class="shell-boundary"]',NS)
  ce=compare(xy(center.attrib['d']),[s['point'] for s in stations],scale,origin);se=compare(xy(shell.attrib['d']),plus+minus[::-1],scale,origin)
  records.append({'svg':file.relative_to(R).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'stations':len(stations),'inverse_projection_max_error_m':max(ce,se),'scale_svg_units_per_m':scale})
info=json.loads((R/'assets/folio/model-info.json').read_text());b=info['construction']['bends'][2];stations=info['construction']['stations'][b['first_station']:b['last_station']+1];t=info['config']['thickness']/2;plus=[(s['point'][0]+s['normal'][0]*t,s['point'][1]+s['normal'][1]*t) for s in stations];minus=[(s['point'][0]-s['normal'][0]*t,s['point'][1]-s['normal'][1]*t) for s in stations];svg=ET.fromstring((R/'assets/diagrams/folio-bend.svg').read_text());shell=svg.findall('s:path',NS)[0];scale=220/(b['center_radius_mm']/1000+t);err=compare(xy(shell.attrib['d']),plus+minus[::-1],scale,(310,270),b['center_yz_m']);records.append({'svg':'assets/diagrams/folio-bend.svg','stations':len(stations),'inverse_projection_max_error_m':err,'source_bend_corner':3,'station_range_inclusive':[b['first_station'],b['last_station']]})
report={'passed':True,'scope':'SVG source projection identity only; not independent validation of the model or all-point mesh thickness','tolerance_m':1e-7,'records':records};(WR/'diagram-tests.json').write_text(json.dumps(report,indent=2));print('7 SVG source-projection checks passed')
