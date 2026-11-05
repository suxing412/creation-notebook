# LY-078 prep: partition every connected part of the stoneclassic GLB into 4 candidate install units
# (cover / enclosure / south_gate / ground) by position rules; report ambiguous parts, opening, reserve.
# python -I classify.py qa/parts-<lod>.json qa/classify-<lod>.json
import sys, json
d = json.load(open(sys.argv[1], encoding='utf-8'))
def inside(p, lo, hi, eps=1e-3):
    return all(p['lo'][i] >= lo[i]-eps and p['hi'][i] <= hi[i]+eps for i in range(3))
def overlap(p, lo, hi, eps=1e-6):
    return all(p['lo'][i] < hi[i]-eps and p['hi'][i] > lo[i]+eps for i in range(3))
RULES = {
 'ground':      lambda m,p: m == 'LY_P01_earth',
 'cover':       lambda m,p: m in ('LY_P01_tile','LY_P01_plaster') or (m=='LY_P01_timber' and inside(p,[-12.2,0,-7.1],[12.2,6.6,7.1])),
 'south_gate':  lambda m,p: m=='LY_P01_timber' and inside(p,[-2.4,0,9.7],[2.4,3.6,10.4]) and p['hi'][1] > 1.8,  # fence-end posts (h=1.5) stay with enclosure
 'enclosure':   lambda m,p: m=='LY_P01_timber' and not inside(p,[-12.2,0,-7.1],[12.2,6.6,7.1]) and inside(p,[-14.2,0,-10.2],[14.2,1.8,10.4]),
}
res = {k: {'parts':0,'tris':0} for k in RULES}; amb=[]; unc=[]
south_fence=[]
for m, M in d['materials'].items():
    for p in M['partList']:
        hits=[k for k,f in RULES.items() if f(m,p)]
        if len(hits)==1:
            res[hits[0]]['parts']+=1; res[hits[0]]['tris']+=p['tris']
        elif len(hits)>1: amb.append((m,p,hits))
        else: unc.append((m,p))
        if m=='LY_P01_timber' and p['hi'][2]>9.6 and p['lo'][2]<10.4 and p['hi'][1]<1.8:
            south_fence.append(p)
# south fence gap: x-intervals covered by south-line fence parts
iv=sorted((p['lo'][0],p['hi'][0]) for p in south_fence)
merged=[]
for a,b in iv:
    if merged and a<=merged[-1][1]+1e-3: merged[-1][1]=max(merged[-1][1],b)
    else: merged.append([a,b])
gaps=[(merged[i][1],merged[i+1][0]) for i in range(len(merged)-1)]
gate=[p for m,M in d['materials'].items() for p in M['partList'] if m=='LY_P01_timber' and inside(p,[-2.4,0,9.7],[2.4,3.6,10.4]) and p['hi'][1]>1.8]
posts=[p for p in gate if p['hi'][1]-p['lo'][1]>2]
lintels=[p for p in gate if p['hi'][0]-p['lo'][0]>3]
clear_w = (min(p['lo'][0] for p in posts if p['lo'][0]>0) - max(p['hi'][0] for p in posts if p['hi'][0]<0)) if len(posts)==2 else None
clear_h = min(p['lo'][1] for p in lintels) if lintels else None
# reserve: Blender x[-8,8], y[-3,3] -> glTF x[-8,8], z[-3,3]; check anything non-ground below roof underside
roof_lo=min(p['lo'][1] for p in d['materials']['LY_P01_tile']['partList'])
res_hits=[(m,p) for m,M in d['materials'].items() if m!='LY_P01_earth' for p in M['partList'] if overlap(p,[-8,0.0,-3],[8,3.9,3])]
out={'src':sys.argv[1],'units':res,'ambiguous':[(m,p['lo'],p['hi'],h) for m,p,h in amb],'unclassified':[(m,p['lo'],p['hi']) for m,p in unc],
     'southFenceCoveredX':merged,'southFenceGapsX':gaps,'gateParts':len(gate),'gatePosts':[(p['lo'],p['hi']) for p in posts],
     'lintels':[(p['lo'],p['hi']) for p in lintels],'gateClearWidth_m':clear_w,'gateClearHeight_m':clear_h,
     'reserve_box_gltf':{'x':[-8,8],'z':[-3,3],'y':[0,3.9]},'reserveHits':len(res_hits),'reserveHitList':[(m,p['lo'],p['hi']) for m,p in res_hits],
     'roofTileUndersideY':roof_lo}
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(json.dumps({k:out[k] for k in out if k not in('reserveHitList','unclassified','ambiguous')},ensure_ascii=False))
print('ambiguous',len(amb),'unclassified',len(unc))
for u in unc[:20]: print('  UNC',u[0],u[1]['lo'],u[1]['hi'])
