# LY-082 acceptance checker (prep version; read-only on inputs).
# Usage:
#   python -I check_lane82.py <corridor.json> [--expect expect.json] [--neg]   -> exit 0 PASS / 1 FAIL
#   python -I check_lane82.py --selftest                                       -> synthetic positive/negative cases
# <corridor.json> is the output of measure_corridor82.py (optionally run with a patch GLB added later).
# --neg inverts the verdict: the run is expected to FAIL K2 (e.g. ground-south dropped / patch disabled).
import sys, json

DEFAULT_EXPECT = {
    # SHA binding (bce3211). A production run must re-bind to whatever LY-001/LY-010 freeze.
    'inputs': {
        'south': '4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e',
        'retained': 'aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc',
        'network-ground-stitched': 'fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60',
        'D08': '3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a'},
    'boundaryY': 0.200, 'boundaryTol': 0.002,      # LY-049 port height, to be frozen by LY-005/006
    'maxAdjacentStep_m': 0.005,                    # per 0.05 m cell; C engineering tolerance, not a norm
    'maxSlope_pct': 5.0,                           # C engineering tolerance, not a norm
    'maxStackedCells': 0,                          # no second floor from another file over the corridor
    'requireNoBodyHits': True,
}


def check(R, E):
    res = []
    def k(name, ok, detail):
        res.append({'check': name, 'pass': bool(ok), 'detail': detail})
    # K1 SHA binding
    bad = {g: R['inputs'].get(g) for g, s in E['inputs'].items() if R['inputs'].get(g) != s}
    k('K1_sha_binding', not bad, bad or 'all ground inputs match')
    # K2 continuous support gate -> reach
    k('K2_support_continuous', R.get('noGroundCells', 1) == 0, {'noGroundCells': R.get('noGroundCells'), 'firstNoGround_v_m': R.get('firstNoGround_v_m')})
    # K3 step / slope
    st = R.get('maxAdjacentStep_m'); sl = R.get('maxSlope_pct')
    k('K3_step_slope', st is not None and st <= E['maxAdjacentStep_m'] and sl <= E['maxSlope_pct'], {'maxAdjacentStep_m': st, 'maxSlope_pct': sl})
    # K4 boundary height matches LY-049 port
    b = R.get('yAtBoundary_v0')
    k('K4_boundary_height', b is not None and abs(b['min'] - E['boundaryY']) <= E['boundaryTol'] and abs(b['max'] - E['boundaryY']) <= E['boundaryTol'], b)
    # K5 no stacked floors from different files
    k('K5_no_stacked_floor', R.get('cellsWithUpFacesFromGe2Files', 0) <= E['maxStackedCells'],
      {'cells': R.get('cellsWithUpFacesFromGe2Files'), 'sep': R.get('stackedVerticalSeparation_m'), 'files': R.get('stackedFiles')})
    # K6 body box free of building triangles (both LODs)
    hits = R.get('bodyBoxHits', {})
    k('K6_body_box_clear', (not E['requireNoBodyHits']) or all(len(v) == 0 for v in hits.values()), hits)
    return res


def selftest():
    base = {'inputs': dict(DEFAULT_EXPECT['inputs']), 'noGroundCells': 0, 'maxAdjacentStep_m': 0.0017, 'maxSlope_pct': 3.49,
            'yAtBoundary_v0': {'min': 0.2, 'max': 0.2}, 'cellsWithUpFacesFromGe2Files': 0, 'bodyBoxHits': {'LOD0': [], 'LOD1': []}}
    cases = []
    def case(name, mut, expect_pass):
        R = json.loads(json.dumps(base)); mut(R)
        ok = all(r['pass'] for r in check(R, DEFAULT_EXPECT))
        cases.append({'case': name, 'expectPass': expect_pass, 'gotPass': ok, 'ok': ok == expect_pass})
    case('P0_current_C02-010', lambda R: None, True)
    case('N1_ground_south_dropped', lambda R: R.update(noGroundCells=15300, firstNoGround_v_m=0.025), False)
    case('N2_step_5cm_injected', lambda R: R.update(maxAdjacentStep_m=0.05, maxSlope_pct=100.0), False)
    case('N3_boundary_offset_15mm', lambda R: R.update(yAtBoundary_v0={'min': 0.215, 'max': 0.215}), False)
    case('N4_double_floor_patch', lambda R: R.update(cellsWithUpFacesFromGe2Files=1200, stackedVerticalSeparation_m={'max': 0.01, 'min': 0.0}), False)
    case('N5_sha_drift', lambda R: R['inputs'].update(south='0' * 64), False)
    case('N6_body_hit', lambda R: R['bodyBoxHits'].update(LOD0=[{'court': 'C02-010', 'node': 'x', 'tris': 1}]), False)
    print(json.dumps(cases, indent=1))
    return all(c['ok'] for c in cases)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--selftest':
        sys.exit(0 if selftest() else 1)
    R = json.load(open(a[0], encoding='utf-8'))
    E = DEFAULT_EXPECT
    if '--expect' in a:
        E = dict(E, **json.load(open(a[a.index('--expect') + 1], encoding='utf-8')))
    res = check(R, E)
    ok = all(r['pass'] for r in res)
    neg = '--neg' in a
    verdict = (not ok) if neg else ok
    print(json.dumps({'file': a[0], 'mode': 'negative' if neg else 'positive', 'allChecksPass': ok, 'verdict': 'PASS' if verdict else 'FAIL', 'checks': res}, ensure_ascii=False, indent=1))
    sys.exit(0 if verdict else 1)
