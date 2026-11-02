from PIL import Image,ImageDraw
import numpy as np, json, os, math
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));frames=json.load(open(R+'/evidence/projected-triangles.json'));rows=[]
N=1200;S=220;c=N/2
# 720 radial rays, sampling beyond central unoccluded zone to detect peripheral leaks.
angles=np.arange(720)*2*math.pi/720;rad=np.linspace(0,2.28,502)
xx=np.rint(c+S*np.cos(angles[:,None])*rad).astype(int);yy=np.rint(c+S*np.sin(angles[:,None])*rad).astype(int)
for f in frames:
 im=Image.new('L',(N,N));d=ImageDraw.Draw(im)
 for tri in f['triangles']:d.polygon([(c+x*S,c+y*S) for x,y in tri],fill=255)
 arr=np.asarray(im)>0;covered=arr[yy,xx];first=covered.argmax(axis=1)
 outside=[]
 for i,row in enumerate(covered):
  gaps=np.flatnonzero(~row[first[i]+3:]) # allow 3 pixels near rasterized aperture edge
  if gaps.size:outside.append(i)
 rows.append({'degrees':f['degrees'],'minApertureRadiusRaster':round(float(rad[first].min()),4),'maxApertureRadiusRaster':round(float(rad[first].max()),4),'radialRaysWithPeripheralGaps':len(outside),'raysMissingCoverageAtBezel':int((~covered[:,-1]).sum())})
 if f['degrees'] in [0,27,55]:im.save(R+'/evidence/projected-coverage-%02d.png'%f['degrees'])
report={'method':'Rasterized actual mesh triangles:1200px at220px/unit,720 rays,502 radial samples from0 to2.28. Three samples tolerance beyond initial boundary. Projection only, not raytraced optical certification.','samples':rows,'maxPeripheralGapRays':max(x['radialRaysWithPeripheralGaps'] for x in rows),'maxBezelLeakRays':max(x['raysMissingCoverageAtBezel'] for x in rows)}
json.dump(report,open(R+'/evidence/aperture-projection-check.json','w'),indent=2);print({k:v for k,v in report.items() if k!='samples'});print(rows[0],rows[27],rows[-1])
assert report['maxPeripheralGapRays']==0 and report['maxBezelLeakRays']==0
