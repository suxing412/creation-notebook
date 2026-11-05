"""LY-026 prep: finite (kinematic, not dynamic) pose table for container stroke / wheel angle / hauling end,
derived only from measured GLB numbers in results/ops-A-LOD0.json. Inextensible rope, no slip, no sag."""
import json, math
d = json.load(open('results/ops-A-LOD0.json', encoding='utf-8'))
R = 0.186                       # rope centre radius in groove (local-contact-checks.json, re-measured strands y=+-0.186)
AX = d['axle']['center'][2]     # 1.95
END = d['ropeStrands'][0]['bbox'][0][2]   # both strand ends z=0.52
cb = d['containerGroup']['bbox'][0][2]; ct = d['containerGroup']['bbox'][1][2]
liner = d['containerGroup']['linerBottomZ']; rim = d['liftOut']['rimTopZ']
L = 2 * (AX - END) + math.pi * R
free = d['containerStrokeFree']['contiguousFromRest']
poses = []
for name, dz in [('lowest-inside-modelled-liner', liner - cb), ('rest-as-exported', 0.0),
                 ('lift-out (bottom 0.03 above rim)', d['liftOut']['dzExit']), ('highest-free-before-wheel', free[1])]:
    poses.append({'pose': name, 'containerDz': round(dz, 4), 'containerBottomZ': round(cb + dz, 4),
                  'containerTopZ': round(ct + dz, 4), 'wheelTurnDeg': round(math.degrees(dz / R), 1),
                  'haulingEndZ_fixedLength': round(END - dz, 4),
                  'haulingEndAboveRim': (END - dz) > rim,
                  'haulingEndInsideModel': (END - dz) >= liner})
need = rim - (END - d['liftOut']['dzExit'])
res = {'ropeLengthStatic_m': round(L, 4), 'grooveRopeRadius': R, 'axleZ': AX, 'strandEndZ': END,
       'rimTopZ': rim, 'linerBottomZ': liner, 'poses': poses,
       'extraRopeForHaulingEndAtRimTopAtLiftOut_m': round(need, 4),
       'scope': 'geometry bookkeeping only: no load, friction, water level, sag or human reach modelled'}
json.dump(res, open('results/pose-table.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
