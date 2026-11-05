# LY-084 prep: dependency-free SVG plan of the three screened candidates over the
# frozen B layer and the built 6 m C pieces. Schematic metres, north up.
#   python -I plan_svg.py <lab_root> out/routes.json out/plan-ne.svg
import json, os, sys

lab, routes_p, out_p = sys.argv[1:4]
LUO = os.path.join(lab, 'docs', 'cities', 'luoyang')
ev = {f['id']: f for f in json.load(open(os.path.join(LUO, 'data/evidence/evidence-geometry.json'), encoding='utf-8'))['features']}
pc = {r['feature_id']: r['classification'] for r in json.load(open(os.path.join(LUO, 'data/west/road-preconstraints.json'), encoding='utf-8'))['rows']}
plan = json.load(open(os.path.join(LUO, 'data/west/road-plan.json'), encoding='utf-8'))
R = json.load(open(routes_p, encoding='utf-8'))

X0, X1, Y0, Y1 = 1500, 2700, 1650, 4000
S = 0.5
W, H = (X1 - X0) * S, (Y1 - Y0) * S


def P(x, y):
    return '%.1f,%.1f' % ((x - X0) * S, (Y1 - y) * S)


def pl(pts, **a):
    attrs = ' '.join('%s="%s"' % (k.replace('_', '-'), v) for k, v in a.items())
    return '<polyline fill="none" points="%s" %s/>' % (' '.join(P(*p) for p in pts), attrs)


o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="sans-serif" font-size="11">' % (W, H, W, H),
     '<rect width="100%" height="100%" fill="#fbf8f1"/>']
o.append(pl(ev['city_wall_schematic_B']['geometry']['coordinates'][0], stroke='#8a7a5a', stroke_width=2, stroke_dasharray='6 3'))
o.append(pl(ev['north_palace_extent_gao2023_B']['geometry']['coordinates'][0], stroke='#b03030', stroke_width=1.5, stroke_dasharray='4 3'))
o.append(pl(ev['south_palace_candidate_gao2023_B']['geometry']['coordinates'][0], stroke='#b03030', stroke_width=1.5, stroke_dasharray='4 3'))
col = {'hold_palace_interface': '#d08000', 'relation_only': '#9090c0', 'C_corridor_trial': '#40a040'}
for fid, f in ev.items():
    if f.get('kind') == 'road_relation' and f['geometry']:
        o.append(pl(f['geometry']['coordinates'], stroke=col.get(pc.get(fid), '#999'), stroke_width=1, stroke_dasharray='2 2'))
for grp in plan:
    for pc_ in grp.get('pieces', []):
        o.append(pl([pc_['a'], pc_['b']], stroke='#2a6a2a', stroke_width=max(1.5, grp['width'] * S)))
o.append(pl([(2285.714, 3647.469), (2285.714, 3486.0), (2316.327, 3486.0), (2316.327, 3490.0)], stroke='#000', stroke_width=2))
o.append('<rect x="%s" y="%s" width="%.1f" height="%.1f" fill="#c9b27c" stroke="#000"/>' % (*P(2249.714, 3699.469).split(','), 72 * S, 52 * S))
for pid, c in (('region_yongan_B', '#b03030'), ('region_wuku_B', '#000'), ('region_taicang_B', '#000'),
               ('gate_shangdong_B', '#8a7a5a'), ('gate_zhongdong_B', '#8a7a5a'), ('gate_gu_B', '#8a7a5a')):
    x, y = ev[pid]['geometry']['coordinates']
    cx, cy = P(x, y).split(',')
    o.append('<circle cx="%s" cy="%s" r="%.1f" fill="none" stroke="%s" stroke-dasharray="3 2"/>' % (cx, cy, 75 * S, c))
    o.append('<circle cx="%s" cy="%s" r="2.5" fill="%s"/><text x="%s" y="%s" fill="%s">%s</text>' % (cx, cy, c, float(cx) + 4, float(cy) - 4, c, pid))
rc = {'R1': '#1060d0', 'R2': '#a000a0', 'R3': '#d02060'}
for cid, c in R['candidates'].items():
    pts = c['polyline_to_contact']
    o.append(pl(pts, stroke=rc[cid], stroke_width=2.5, stroke_opacity=0.85))
    mx, my = pts[len(pts) // 2]
    s = c['support_w3']
    o.append('<text x="%s" y="%s" fill="%s" font-weight="bold">%s %.0f m, unsupported %.0f m</text>' % (
        *P(mx + 8, my).split(','), rc[cid], cid, s['length_m'], s['unsupported_m']))
o.append('<text x="8" y="16">LY-084 prep - schematic metres, north up. Dashed brown: city wall B; dashed red: palaces B (old); '
         'orange dashed: hold_palace_interface relations; green solid: built 6 m C pieces; black: existing 196 m road; '
         'circles: 75 m presentation envelopes (not extents).</text>')
o.append('<text x="8" y="30">Candidates R1/R2/R3 are LY-084 reconstructions (original three-plan file not found). Water: no placed geometry.</text>')
o.append('</svg>')
open(out_p, 'w', encoding='utf-8').write('\n'.join(o))
print('WROTE', out_p)
