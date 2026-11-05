# LY-075 prep: negative control N4 (test-plan.md). Injects plan obstacles into ONE doorway of a measurement copy
# (rooms_reach.py inject arg; GLBs and floor npz untouched) and asserts the checker localises the failure.
#   N4a full block: box = door clear width + 0.20 m along the wall, 0.60 m across -> that door must be 'blocked'
#        for every positive config, the other 15 doors must still pass, and all 9 rooms must stay reachable.
#   N4b 0.30 x 0.30 m post in the middle of the door -> leaves two gaps of (w - 0.30)/2; the door must pass for
#        r = 0.25 (body 0.50 < gap) and be blocked for r = 0.45 when 0.90 > gap - one grid cell (B: gap 0.85).
# Usage: python neg_door_block.py <floor.npz> <sect.npz> <reach.json> <out_dir> <label>
import json, subprocess, sys, os
floor, sect, reach, outd, label = sys.argv[1:6]
R = json.load(open(reach, encoding='utf-8'))
os.makedirs(outd, exist_ok=True)
def pick(pred):
    return [d for d in R['doors'] if pred(sorted(d['connects']))][0]
targets = {'inner-CW-centre': pick(lambda c: c == ['room-CW', 'room-centre']),
           'outer-CW-veranda': pick(lambda c: c == ['room-CW', 'veranda-ring'])}
report = dict(label=label, base_reach=reach, cases=[])
ok_all = True
for tname, d in targets.items():
    cx, cz = d['centre']; w = d['clear_width_m']
    along_x = d['orientation'] == 'wall-along-x'   # door opening spans x, wall thickness along z
    for kind in ('full', 'post'):
        if kind == 'full':
            a, b = (w + 0.20) / 2, 0.30
        else:
            a, b = 0.15, 0.15
        hx, hz = (a, b) if along_x else (b, a)
        box = '%.3f,%.3f,%.3f,%.3f' % (cx - hx, cz - hz, cx + hx, cz + hz)
        out = os.path.join(outd, '%s-N4-%s-%s.json' % (label, tname, kind))
        subprocess.run([sys.executable, 'rooms_reach.py', floor, out, label + '-N4', sect, box], check=True, stdout=subprocess.DEVNULL)
        X = json.load(open(out, encoding='utf-8'))
        rows = []
        for rr in X['reach']:
            k = (rr['body_height_m'], rr['body_radius_m'], rr['max_step_m'])
            if k[0] > 2.35 or k[1] > 1.0 or k[2] < 0.15: continue  # skip N1-N3 configs
            rooms = sorted(set(rr['rooms_reached']) - {'veranda-ring'})
            rooms = [n for n in rooms if n.startswith('room-')]
            dp = rr['door_pass'][str(d['id'])] if str(d['id']) in rr['door_pass'] else rr['door_pass'][d['id']]
            others = [i for i, v in rr['door_pass'].items() if str(i) != str(d['id']) and v != 'pass']
            if kind == 'full':
                want_door = 'blocked'
            else:
                gap = (w - 0.30) / 2
                want_door = 'pass' if 2 * k[1] < gap - 0.05 else ('blocked' if 2 * k[1] > gap + 0.05 else 'either')
            ok = (len(rooms) == 9 and not others and (want_door == 'either' or dp == want_door))
            ok_all &= ok
            rows.append(dict(config=k, door=dp, want=want_door, rooms_reached=len(rooms), other_doors_blocked=others, ok=ok))
        report['cases'].append(dict(target=tname, door_id=d['id'], door_width=w, kind=kind, box_xz=box, out=out,
                                    injected_cells=X.get('injected_obstacles', {}).get('cells'), rows=rows,
                                    ok=all(r['ok'] for r in rows)))
        print(label, tname, kind, 'door', d['id'], 'w', w, 'ok', all(r['ok'] for r in rows),
              'door results', sorted({(r['config'][1], r['door']) for r in rows}))
report['verdict'] = 'pass' if ok_all else 'FAIL'
json.dump(report, open(os.path.join(outd, '%s-N4-summary.json' % label), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('N4', label, report['verdict'])
sys.exit(0 if ok_all else 1)
