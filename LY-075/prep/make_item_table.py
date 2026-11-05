# LY-075 prep: per-item result table (test-plan.md section 4) from rooms_reach.py + check_invariants.py output.
# Rows: 9 rooms, 16 doorways, 16 sills, 16 post sides, 3 fixed unknowns. Reference config H2.0 r0.25 s0.20.
# Usage: python make_item_table.py <reach.json> <check.json> <posts.log> <glb-name> <out.md>
import json, sys
reach, check, posts_log, glb, out = sys.argv[1:6]
R = json.load(open(reach, encoding='utf-8')); K = json.load(open(check, encoding='utf-8'))
lod = R['label'].split('-')[-1]
gsha = K['bound'].get(lod, {}).get('sha256', '?')
ref = [x for x in R['reach'] if (x['body_height_m'], x['body_radius_m'], x['max_step_m']) == (2.0, 0.25, 0.2)][0]
pos = [x for x in R['reach'] if x['body_height_m'] <= 2.3 and x['body_radius_m'] <= 0.45 and x['max_step_m'] >= 0.16]
L = ['# %s per-item result (LY-075 prep, NOT acceptance: synthetic ground y=0 until LY-074 ports exist)' % R['label'], '',
     'GLB `%s` sha256 `%s`; reach.json sha256 `%s`; reference config H2.0/r0.25/s0.20; positive configs %d.' % (glb, gsha, K['bound'][lod]['reach_sha256'], len(pos)), '',
     '| item | result | basis | bound SHA |', '|---|---|---|---|']
short = gsha[:12]
names = ['room-NW', 'room-NC', 'room-NE', 'room-CW', 'room-centre', 'room-CE', 'room-SW', 'room-SC', 'room-SE']
rooms = {r['name']: r for r in R['regions']}
for n in names:
    allpos = all(n in x['rooms_reached'] for x in pos); seeds = sorted(s for s, v in ref['per_seed'].items() if n in v)
    r = rooms[n]
    L.append('| %s | %s | %d/%d positive configs; ref seeds %s; net %.2fx%.2f m; headroom min %.3f m | %s |' % (
        n, '可达' if allpos else '受阻', sum(n in x['rooms_reached'] for x in pos), len(pos), ''.join(seeds),
        r['x'][1] - r['x'][0], r['z'][1] - r['z'][0], r['headroom_min'], short))
for d in R['doors']:
    npass = sum(x['door_pass'][str(d['id'])] == 'pass' if str(d['id']) in x['door_pass'] else x['door_pass'][d['id']] == 'pass' for x in pos)
    L.append('| D%d doorway %s | %s | local subgraph pass %d/%d; w %.2f, depth %.2f, head %.3f m | %s |' % (
        d['id'], '–'.join(d['connects']), '可达' if npass == len(pos) else '受阻', npass, len(pos), d['clear_width_m'], d['wall_depth_m'], d['head_clear_min'], short))
for d in R['doors']:
    L.append('| D%d sill | 模型无门槛几何（%.3f m），门道平地可达；历史门槛形态未知 | floor_min=floor_max=%.3f | %s |' % (d['id'], d['sill_height_above_room_m'], d['floor_min'], short))
cur = None; plist = []
for line in open(posts_log, encoding='utf-8'):
    if line.startswith(glb): cur = 'timber' in line; continue
    if not line.startswith(' '): cur = None; continue
    if cur: plist.append(line.split())
for p in plist:
    x, z, dia = float(p[1]), float(p[3]), float(p[5])
    L.append('| post (%.2f, %.2f) side | 不构成独立通道：位于墙交点，九室/回廊无独立柱 | diam %.3f; T8 min post-to-door-edge %s m | %s |' % (
        x, z, dia, [c for c in K['checks'] if c['id'] == 'T8'][0]['detail']['min_post_to_door_edge_m'], short))
for item in ('重屋上层（中室上方）', '门扇开闭/互斥状态', '台缘跌落安全（无护栏，落差 %.1f m）' % R['platform_floor_y']):
    L.append('| %s | 未知（未建模） | not modelled; not counted as reachable or blocked | %s |' % (item, short))
L += ['', 'Exterior arrival: seeds sit on a synthetic flat ground at y=0 (C assumption). Real arrival = LY-074 ports mingtang:side-{N,E,S,W}:ground (not delivered).',
      'Scope: model-readable + local passage only. Not city install, not structural safety, not historical reconstruction.']
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print(out, len(L))
