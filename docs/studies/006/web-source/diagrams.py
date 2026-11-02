"""Build original SVGs exclusively from the model's exported station data.
No mesh generation occurs here. All physical coordinates remain in metres until projected.
"""
import json,hashlib,html,math
from pathlib import Path

INK='#112c52';BLUE='#194bd4'
def esc(x):return html.escape(str(x),quote=True)
def boundary(info):
    t=info['config']['thickness']/2
    s=info['construction']['stations']
    plus=[(q['point'][0]+q['normal'][0]*t,q['point'][1]+q['normal'][1]*t) for q in s]
    minus=[(q['point'][0]-q['normal'][0]*t,q['point'][1]-q['normal'][1]*t) for q in s]
    return plus,minus

def path(points,project,close=False):
    return ' '.join(('M' if i==0 else 'L')+f'{project(p)[0]:.4f},{project(p)[1]:.4f}' for i,p in enumerate(points))+(' Z' if close else '')

def profile(info,small=False,prefix='profile'):
    # Shared coordinate box for every variant: actual same scale, not per-model normalization.
    w,h=(460,280) if small else (760,460)
    scale=(w-72)/.40; ox=w/2;oy=h-48
    project=lambda q:(ox+q[0]*scale,oy-q[1]*scale)
    s=info['construction']['stations'];plus,minus=boundary(info);shape=path(plus+list(reversed(minus)),project,True);center=path([q['point'] for q in s],project)
    variant=info['variant'];title=f'{variant.upper()} 中心截面离散法向偏移轮廓'
    a=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="{prefix}-title {prefix}-desc" class="profile-svg"><title id="{prefix}-title">{title}</title><desc id="{prefix}-desc">由model-info中YZ中心线采样点及法向乘以名义厚度的一半导出。蓝色虚线是中心线，实线边界是法向偏移轮廓。不是施工图或板金展开图。</desc>',f'<path d="M24,{oy:.2f} H{w-24}" fill="none" stroke="#bdc9da" stroke-width="1"/>',f'<path class="shell-boundary" d="{shape}" fill="#d4def4" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>',f'<path class="center-line" d="{center}" fill="none" stroke="{BLUE}" stroke-width="1.35" stroke-dasharray="6 5"/>']
    if not small:
        offsets=[(-38,28),(-4,-58),(10,-42),(38,28)]
        for b,(dx,dy) in zip(info['construction']['bends'],offsets):
            x,y=project(b['center_yz_m']);lx=x+dx;ly=y+dy
            # Leader endpoints are real bend centers; label offsets are annotation layout only.
            a.append(f'<path d="M{x:.2f},{y:.2f} L{lx:.2f},{ly:.2f}" stroke="{BLUE}" stroke-width="1" fill="none"/><circle cx="{x:.2f}" cy="{y:.2f}" r="2.5" fill="{BLUE}"/><g transform="translate({lx:.2f},{ly:.2f})"><g class="label-size"><rect x="-16" y="-12" width="32" height="24" rx="2" fill="{BLUE}"/><text x="0" y="4" text-anchor="middle" fill="white" font-size="11" font-family="monospace">B{b["corner"]}</text></g></g>')
        a.append(f'<text class="svg-coordinate-note" x="24" y="{h-12}" fill="#52627a" font-size="11">YZ 中心截面 · 同一模型坐标系</text>')
    a.append('</svg>');return ''.join(a)

def bend(info,prefix='bend'):
    b=info['construction']['bends'][2];r=b['center_radius_mm']/1000;t=info['config']['thickness'];s=info['construction']['stations'][b['first_station']:b['last_station']+1]
    center=b['center_yz_m'];w=620;h=350;scale=220/(r+t/2);project=lambda q:(310+(q[0]-center[0])*scale,270-(q[1]-center[1])*scale)
    plus=[(q['point'][0]+q['normal'][0]*t/2,q['point'][1]+q['normal'][1]*t/2) for q in s];minus=[(q['point'][0]-q['normal'][0]*t/2,q['point'][1]-q['normal'][1]*t/2) for q in s];mid=s[len(s)//2];pa=plus[len(s)//2];pb=minus[len(s)//2];xa,ya=project(pa);xb,yb=project(pb);cx,cy=project(center);xp,yp=project(mid['point'])
    a=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="{prefix}-title {prefix}-desc" class="bend-svg"><title id="{prefix}-title">B3顶弯中心截面局部放大</title><desc id="{prefix}-desc">局部放大源于B3首末站点范围，名义法向厚度{t*1000:g}毫米，中心半径{r*1000:g}毫米。折线只是离散弦，非连续制造公差证明。</desc>',f'<path d="{path(plus+list(reversed(minus)),project,True)}" fill="#36567d" stroke="#e3edff" stroke-width="1.5"/>',f'<path d="{path([q["point"] for q in s],project)}" fill="none" stroke="#b5cdf9" stroke-width="1.5" stroke-dasharray="7 6"/>',f'<path d="M{cx:.3f},{cy:.3f} L{xp:.3f},{yp:.3f}" stroke="#a2b7d4" stroke-width="1.2" stroke-dasharray="3 4"/>',f'<path d="M{xa:.3f},{ya:.3f} L{xb:.3f},{yb:.3f}" stroke="#fff" stroke-width="3"/>',f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="3" fill="#b5cdf9"/><text x="{cx+14:.3f}" y="{cy+5:.3f}" fill="#c4d6ed" font-size="13">圆弧中心</text>',f'<text x="{xp+22:.3f}" y="{yp+10:.3f}" fill="white" font-family="monospace" font-size="17">t {t*1000:.2f} mm</text>',f'<text x="{(cx+xp)/2+18:.3f}" y="{(cy+yp)/2+26:.3f}" fill="#c4d6ed" font-family="monospace" font-size="14">R {r*1000:.2f} mm</text>',f'<text x="22" y="28" fill="#b5cdf9" font-size="12">B3 / 中心截面局部放大</text>','</svg>']
    return ''.join(a)

def make_all(root):
    out=root/'assets/diagrams';out.mkdir(parents=True,exist_ok=True);records=[]
    for v in ['folio','atlas','spire']:
        f=root/'assets'/v/'model-info.json';info=json.loads(f.read_text());assert info['units']=='metres'
        for suffix,svg in [('profile',profile(info,False,v+'-profile')),('small',profile(info,True,v+'-small'))]:
            p=out/f'{v}-{suffix}.svg';p.write_text(svg);records.append({'path':p.relative_to(root).as_posix(),'source':f.relative_to(root).as_posix(),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'units':'m in source; annotated mm','derivation':'YZ stations.point ± stations.normal × config.thickness / 2','not_certified':'Not full all-point mesh thickness, fabrication drawings or stress simulation','bytes':p.stat().st_size})
    source=root/'assets/folio/model-info.json';info=json.loads(source.read_text());bp=out/'folio-bend.svg';bp.write_text(bend(info));b=info['construction']['bends'][2];records.append({'path':bp.relative_to(root).as_posix(),'source':source.relative_to(root).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'units':'m in source; annotated mm','station_range_inclusive':[b['first_station'],b['last_station']],'source_bend_corner':b['corner'],'projection':{'origin_svg':[310,270],'center_yz_m':b['center_yz_m'],'svg_units_per_m':220/(b['center_radius_mm']/1000+info['config']['thickness']/2)},'derivation':'Selected B3 station offsets; center radius and thickness annotations are config/analytic values, not mesh measurements','bytes':bp.stat().st_size})
    for item in records:item['svg_sha256']=hashlib.sha256((root/item['path']).read_bytes()).hexdigest()
    (out/'diagram-evidence.json').write_text(json.dumps({'coordinate_convention':'SVG x = model Y; SVG y = -model Z','profile_projection':{'small':{'scale_svg_units_per_m':970,'origin_svg':[230,232]},'large':{'scale_svg_units_per_m':1720,'origin_svg':[380,412]}},'family_shared_scale':'all small profiles use scale 970 SVG units per metre, origin (230,232)','records':records},ensure_ascii=False,indent=2));return info
