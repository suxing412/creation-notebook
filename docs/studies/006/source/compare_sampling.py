"""Finite image-patch high-frequency indicator, NOT an unbiased noise or geometry measure."""
from PIL import Image,ImageFilter
import numpy as np,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];rows=[]
for samples in [48,128]:
 p=R/'review'/('sampling-'+str(samples)+'.png');im=Image.open(p).convert('RGB');ary=np.asarray(im).astype(float)/255;blur=np.asarray(im.filter(ImageFilter.GaussianBlur(1.2))).astype(float)/255;result={}
 for label,(x0,y0,x1,y1) in {'front_flat_patch':(215,235,345,320),'ground_patch':(35,500,170,535)}.items():result[label]={'roi_xyxy':[x0,y0,x1,y1],'high_frequency_residual_std':float((ary-blur)[y0:y1,x0:x1].std())}
 rows.append({'samples_cap':samples,'image':str(p.relative_to(R)),'resolution':[560,560],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'measurements':result})
report={'comparison':rows,'selection':'256 max adaptive samples at 960 x 960 for the final seven views, after visual review of 48 and 128 previews. Not 1024 by default.','denoising':False,'adaptive_sampling':True,'adaptive_threshold':.01,'scope':'High-frequency residual after Gaussian blur is a finite image-patch indicator, not an unbiased noise estimator or geometry validation. Camera/material/seed match between the 560px previews. Do not compare this raw residual to the 960px final as if resolutions match.'};(R/'review/render-comparison.json').write_text(json.dumps(report,indent=2));print('SAMPLING',rows[0]['measurements'],rows[1]['measurements'])
