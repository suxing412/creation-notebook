# LY-072 prep: does the LY-006 registry v1 write zone / port / ownership cover the crossing that the
# trial-fit actually has, and do the existing four crossings agree with LY-002 E-R05?
# Pure python, read-only.  python -I zone_evidence_check.py <workpacks_root> <out.json>
#
# Inputs (SHA-bound in output):
#   LY-006/registry/{zones,ports,seats,ownership}.json, LY-002/tables/evidence-ledger.md,
#   LY-072/prep/qa/measure-trialfit.json (bboxes, Blender Z-up trial local frame; island top Z=0, hall top Z=1.2),
#   LY-072/prep/qa/side-water.json (measure_side_water.py)
# Frame conversion to local:biyong (LY-006: "hall A origin", glTF Y-up; LY-005: Blender +Y = north = glTF -z):
#   pre-N  reading: x = X, y = Z - 1.2, z = -Y   (hall A own origin, platform top y = 0)
#   post-N reading: x = X, y = Z,       z = -Y   (trial-fit frame, island top y = 0)
import json, sys, hashlib, os

root, outp = sys.argv[1], sys.argv[2]
P = lambda *a: os.path.join(root, *a)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
files = {k: P(*v) for k, v in {
    'zones': ('LY-006', 'registry', 'zones.json'), 'ports': ('LY-006', 'registry', 'ports.json'),
    'seats': ('LY-006', 'registry', 'seats.json'), 'ownership': ('LY-006', 'registry', 'ownership.json'),
    'ledger': ('LY-002', 'tables', 'evidence-ledger.md'),
    'trialfit': ('LY-072', 'prep', 'qa', 'measure-trialfit.json'),
    'sidewater': ('LY-072', 'prep', 'qa', 'side-water.json')}.items()}
J = lambda k: json.load(open(files[k], encoding='utf-8'))
zones, ports, seats, own, tf, sw = J('zones'), J('ports'), J('seats'), J('ownership'), J('trialfit'), J('sidewater')
ledger = open(files['ledger'], encoding='utf-8').read()

z72 = [z for z in zones['zones'] if z['seat'] == 'LY-072']
site = [z for z in zones['zones'] if z['site'] == 'S-BIYONG']


def conv(b, dz):
    (X0, Y0, Z0), (X1, Y1, Z1) = b
    return [[X0, Z0 - dz, -Y1], [X1, Z1 - dz, -Y0]]


def inter(a, b):
    lo = [max(a[0][i], b[0][i]) for i in range(3)]; hi = [min(a[1][i], b[1][i]) for i in range(3)]
    return (lo, hi) if all(hi[i] > lo[i] for i in range(3)) else None


vol = lambda b: (b[1][0] - b[0][0]) * (b[1][1] - b[0][1]) * (b[1][2] - b[0][2])
out = {'tool': 'zone_evidence_check.py', 'inputs': {k: {'path': v, 'sha256': sha(v)} for k, v in files.items()},
       'LY-072_zones': z72, 'readings': {}}
for label, dz in (('pre-N', 1.2), ('post-N', 0.0)):
    rows = {}
    for g in ('crossing_0_1', 'crossing_0_-1', 'crossing_1_1', 'crossing_1_-1'):
        b = conv(tf['groups'][g]['bbox'], dz)
        hits = {}
        for z in site:
            r = inter(b, z['box'])
            if r: hits[z['zoneId']] = round(vol(r), 4)
        rows[g] = {'local_biyong_box': [[round(v, 3) for v in p] for p in b], 'volume_m3': round(vol(b), 4),
                   'zoneOverlap_m3': hits,
                   'fractionInsideLY-072:write:001': round(hits.get('LY-072:write:001', 0) / vol(b), 4)}
    out['readings'][label] = rows

zb = z72[0]['box']
out['zoneGeometry'] = {
    'LY-072:write:001_x': [zb[0][0], zb[1][0]], 'lateral_halfwidth': zb[1][2],
    'trialFit_axis_features_t': {'stairFoot': 20.4, 'wallInnerFoot': 67.65, 'wallOuterFoot': 68.35,
                                 'waterInner': 70.0, 'waterOuter': 78.0, 'crossing': [69.8, 78.2]},
    'note': 'zone x 20.4-30.0 lies on the flat island between stair foot and wall (trial-fit has no water there); '
            'the water band is 70-78 and the opening is |lat|<4.0, the existing crossing |lat|<=4.0',
    'zoneWidth_m': zb[1][2] - zb[0][2], 'enclosureOpening_m': 8.0, 'existingCrossingWidth_m': 8.0,
    'gapToWaterInner_m': round(70.0 - zb[1][0], 3)}

p = ports['ports']
out['ports'] = {k: {f: p[k].get(f) for f in ('producer', 'status', 'local', 'world', 'consumers')}
                for k in ('biyong:hall-enclosure:ground', 'biyong:crossing-ends:ground')}
s = json.dumps(own, ensure_ascii=False)
out['ownershipOfTrialFitNodes'] = {n: (n in s) for n in (
    'biyong-layout__A_crossing_0_1', 'biyong-layout__A_crossing_0_-1', 'biyong-layout__A_crossing_1_1',
    'biyong-layout__A_crossing_1_-1', 'biyong-layout__A_island', 'biyong-layout__A_square_water_symbol',
    'biyong_C_relationship')}
out['seatLY-072'] = {k: seats['seats']['LY-072'][k] for k in ('components', 'produces', 'consumes', 'writeZones')}

out['evidence'] = {
    'E-R05_present': '### E-R05' in ledger, 'north_no_water_text_present': '东西南有水，北无' in ledger,
    'north_gate_entry_text_present': '从北门入' in ledger,
    'E-R03_mingtang_bridge_over_dry_moat_present': '上作桥' in ledger,
    'sideWater': {k: v['waterFraction'] for k, v in sw['bands'].items()},
    'sideCrossingCells': {k: v['crossingCells'] for k, v in sw['bands'].items()},
    'conflict_north_under_LY-002_E-R05_reading': sw['E-R05_check']['conflict']}

# Re-read the primary text from LY-002's own byte snapshot (S10, hhs02.html, GB18030) to see what
# "东西南有水，北无" is attached to.
snap = P('LY-002', 'source', 'snapshots', 'hhs02.html')
t = open(snap, 'rb').read().decode('gb18030')
i = t.find('辟雍以水周其外')
seg = t[i:i + 60] if i >= 0 else ''
j = seg.find('诸侯曰泮宫'); k = seg.find('东西南有水')
out['evidence']['primaryText'] = {
    'snapshot': {'path': snap, 'sha256': sha(snap)},
    'biyong_water_all_round_phrase_present': '辟雍以水周其外' in t,
    'panGong_sentence_index_in_segment': j, 'threeSidesWater_index_in_segment': k,
    'threeSidesFollowsPanGong': 0 <= j < k,
    'reading': 'In S10 the clause 东西南有水，北无，下天子也 follows 诸侯曰泮宫 and reads as the feudal 泮宫 '
               '(half water, one rank below the emperor); the emperor\'s 辟雍 is 以水周其外. LY-002 E-R05 '
               'attributes the three-sided water to 辟雍. Dispute to LY-002 / LY-010; LY-072 does not decide it.',
    'north_crossing_under_this_reading': 'not excluded: water all round + 车驾从北门入 makes a north crossing the '
                                         'only entry the text names (still C: no bridge is mentioned for 辟雍)'}
json.dump(out, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out['readings'].items():
    print(k, {g: r['fractionInsideLY-072:write:001'] for g, r in v.items()})
print(out['zoneGeometry']['gapToWaterInner_m'], out['ownershipOfTrialFitNodes'])
print(out['evidence'])
