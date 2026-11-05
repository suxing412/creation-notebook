"""LY-024 prep: derive the S84-type front-opening numbers from measure_parts.py output.
Pure-python; AABB level only (not a solid/BVH collision test). Usage: python analyze_openings.py meas/ out.json"""
import json, sys, os
md, out = sys.argv[1], sys.argv[2]
def load(n): return json.load(open(os.path.join(md, n + '.json'), encoding='utf-8'))
def kind(p): return p['mat'][0].split('_')[2]
def ov(a0,a1,b0,b1): return round(min(a1,b1)-max(a0,b0),4)
res = {'method':'AABB of welded loose parts (glTF Y-up metres); front faces +Z in local S84 frame','models':{}}
def s84_frame(parts, cx, cz, flip):
    """return parts in S84-local frame (front edge z=0, facing +z)."""
    o=[]
    for p in parts:
        mn,mx=p['min'],p['max']
        if not flip: a=[mn[0]-cx,mn[1],mn[2]-cz]; b=[mx[0]-cx,mx[1],mx[2]-cz]
        else: a=[cx-mx[0],mn[1],cz-mx[2]]; b=[cx-mn[0],mx[1],cz-mn[2]]
        o.append({**p,'min':[round(v,4) for v in a],'max':[round(v,4) for v in b]})
    return o
def measure(parts):
    T=[p for p in parts if kind(p)=='timber']; E=[p for p in parts if kind(p)=='earth']; R=[p for p in parts if kind(p)=='tile']
    inb=lambda p: -4.6<=p['min'][0] and p['max'][0]<=4.6 and -4.6<=p['min'][2] and p['max'][2]<=0.6
    T=[p for p in T if inb(p)]; E=[p for p in E if inb(p)]; R=[p for p in R if inb(p)]
    posts=sorted([p for p in T if p['size'][1]>2.5 and p['size'][0]<0.3],key=lambda p:p['min'][0])
    beam=[p for p in T if p['size'][0]>6 and p['size'][1]<0.3 and p['max'][2]>-0.3][0]
    counter=[p for p in T if 4<p['size'][0]<5 and p['size'][2]<1][0]
    legs=[p for p in T if p['size'][0]<0.2 and 0.7<p['size'][1]<0.9]
    body=max(E,key=lambda p:p['size'][0]*p['size'][2])
    floor_top=0.22  # measured: earth slab face y=0.22 (see S84 face-level dump)
    m={}
    m['postsX']=[[p['min'][0],p['max'][0]] for p in posts]; m['postZ']=[posts[0]['min'][2],posts[0]['max'][2]]
    m['postTopY']=[p['max'][1] for p in posts]
    m['beam']={'x':[beam['min'][0],beam['max'][0]],'y':[beam['min'][1],beam['max'][1]],'z':[beam['min'][2],beam['max'][2]]}
    m['counter']={'x':[counter['min'][0],counter['max'][0]],'y':[counter['min'][1],counter['max'][1]],'z':[counter['min'][2],counter['max'][2]]}
    m['counterLegBottomY']=sorted({l['min'][1] for l in legs})
    m['body']={'min':body['min'],'max':body['max']}
    m['clearWidthBetweenPosts']=round(posts[1]['min'][0]-posts[0]['max'][0],4)
    m['clearHeightFloorToBeam']=round(beam['min'][1]-floor_top,4)
    m['sidePassageWidth']=[round(counter['min'][0]-posts[0]['max'][0],4), round(posts[1]['min'][0]-counter['max'][0],4)]
    m['postPlaneToCounterGap']=round(posts[0]['min'][2]-counter['max'][2],4)
    m['postFrontFaceToSlabEdge']=round(0-posts[0]['max'][2],4)
    m['postToWallInnerGapX']=round(posts[0]['min'][0]-(-3.72),4)
    m['contacts_AABB']={
      'postIntoFloorSlab_depth':floor_top-posts[0]['min'][1],
      'counterLegIntoFloor_depth':round(floor_top-min(m['counterLegBottomY']),4),
      'beamPostOverlapX':ov(beam['min'][0],beam['max'][0],posts[1]['min'][0],posts[1]['max'][0]),
      'postAboveBeamTop':round(posts[0]['max'][1]-beam['max'][1],4)}
    eave=[p for p in R if p['max'][2]>0.2]
    m['eaveMaxZ']=max((p['max'][2] for p in R),default=None)
    m['roofMinYoverFrontStrip']=min((p['min'][1] for p in R if p['max'][2]>-0.3),default=None)
    m['tileParts']=len(R)
    return m
s84=load('S84-LOD0'); res['models']['S84-LOD0']={'sha256':s84['sha256'],**measure(s84['parts'])}
fr=load('frontage-LOD0')
for name,cx,cz,flip in [('frontage-N-S84type',4.6,-5.0,False),('frontage-S-S84type',14.3,5.0,True)]:
    res['models'][name]={'sha256':fr['sha256'],'transformToLocal':{'tx':-cx,'tz':-cz,'rotY180':flip},**measure(s84_frame(fr['parts'],cx,cz,flip))}
for n in ['frontage-LOD1','frontage-LOD2']:
    f=load(n)
    try: res['models'][n+'-N-S84type']={'sha256':f['sha256'],**measure(s84_frame(f['parts'],4.6,-5.0,False))}
    except Exception as e: res['models'][n+'-N-S84type']={'sha256':f['sha256'],'error':repr(e)}
json.dump(res,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
for k,v in res['models'].items():
    print(k, {x:v.get(x) for x in ['clearWidthBetweenPosts','clearHeightFloorToBeam','sidePassageWidth','postPlaneToCounterGap','contacts_AABB','eaveMaxZ','roofMinYoverFrontStrip','error']})
