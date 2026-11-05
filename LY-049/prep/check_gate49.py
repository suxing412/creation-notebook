# LY-049 acceptance checker (prep version). Reads a measure_gate49.py JSON and judges it.
#   python check_gate49.py measure-gate-LOD0.json                    -> exit 0 on PASS
#   python check_gate49.py neg-no-ground-LOD0.json --neg             -> exit 0 if the case FAILS as expected
#   python check_gate49.py X.json --declared-steps 0.03               -> a declared step of 3 cm (+-2 mm) is allowed
#   python check_gate49.py --selftest                                 -> runs all positive / negative cases, writes selftest-check.json
# Tolerances are C values (LY-006 port tolerance: position 5 mm, elevation 2 mm).
import json, sys, os, argparse

EXPECT_SHA = {
    'assets/c02v/A2-LOD0-prototype.glb': '19b052022b2f6955e4a72f1a48280f7f8c229e11f001aa02ac95e357b890d9c7',
    'assets/c02v/A2-LOD1-prototype.glb': '277e9e73e8f2d8b8e07ec828671d37cc7c9e3f1653dcebfe4290c51de412d85d',
    'assets/ground-atomic/south.glb': '4313826ddf5fbe0c0d8dcb4983d6cdbd647713d49faa1980cd34f587a3273a0e',
    'assets/ground-atomic/retained.glb': 'aed8b3d4cb12aeaddf5c696a8a86355b15b7cb4fc8ebd76cc364d23789d630cc',
    'assets/ground-atomic/network-ground-stitched.glb': 'fdfc3ce5c63305f79aa746b31c3be60f3d11a6acb75f190886124f2d3446db60',
    'assets/ground-atomic/D08.glb': '3ab933108b88c5c359fc7512d324e14f15157eaa54fb17f80f2adeb6c4626d9a',
}
PORT_Y = 0.2            # C02-010:ground-base world y (LY-006 ports.json, imported from LY-005)
TOL_ELEV = 0.002
TOL_STEP = 0.005        # undeclared step tolerance (C)
BODY_W, BODY_H = 0.60, 1.80


def judge(d, declared_steps=()):
    r = {}
    sha_ok = d['inputs']['prototypeSha256'] == EXPECT_SHA.get(d['inputs']['prototype'])
    for k, (f, s) in d['inputs']['grounds'].items():
        sha_ok &= EXPECT_SHA.get(f) == s
    r['K0_sha_bound'] = sha_ok and len(d['inputs']['grounds']) == 4
    c6, g = d['corridor_court_z6_9'], d['corridor_gate_z9_12']
    r['K1_support_complete'] = c6['unsupported'] == 0 and g['unsupported'] == 0 and g['cells'] > 0
    r['K2_single_ground_layer'] = g['maxLayers'] == 1 and c6['maxLayers'] == 1
    r['K3_no_layer_beyond_boundary'] = d['beyondBoundary_z12_12p6']['maxLayers'] <= 1 and d['beyondBoundary_z12_12p6']['unsupported'] == 0
    step = max(c6['maxAdjStep_m'], g['maxAdjStep_m'])
    if declared_steps:
        r['K4_steps_declared'] = step <= TOL_STEP or any(abs(step - s) <= TOL_ELEV for s in declared_steps)
    else:
        r['K4_steps_declared'] = step <= TOL_STEP and g['buildingStepCells'] == 0
    r['K5_clearance'] = g['minClear_m'] is not None and g['minClear_m'] >= BODY_H and d['bodySweep']['ok']
    r['K6_width'] = d['gatePassage']['minFreeWidth_m'] >= BODY_W
    br = d.get('boundaryRows', [])
    r['K7_boundary_elevation'] = bool(br) and all(x['footMin'] is not None and abs(x['footMin'] - PORT_Y) <= TOL_ELEV and abs(x['footMax'] - PORT_Y) <= TOL_ELEV for x in br)
    r['PASS'] = all(r.values())
    r['numbers'] = dict(maxStep_m=step, minClear_m=g['minClear_m'], minFreeWidth_m=d['gatePassage']['minFreeWidth_m'],
                        unsupportedCells=c6['unsupported'] + g['unsupported'], maxLayers=max(c6['maxLayers'], g['maxLayers']),
                        beyondLayers=d['beyondBoundary_z12_12p6']['maxLayers'])
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?')
    ap.add_argument('--neg', action='store_true')
    ap.add_argument('--declared-steps', type=float, nargs='*', default=())
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    if a.selftest:
        cases = [('measure-gate-LOD0.json', True, ()), ('measure-gate-LOD1.json', True, ()),
                 ('neg-no-ground-LOD0.json', False, ()), ('neg-threshold-LOD0.json', False, ()),
                 ('neg-threshold-LOD0.json', True, (0.03,)),
                 ('neg-double-slab-LOD0.json', False, ()), ('neg-overrun-LOD0.json', False, ()),
                 ('standalone-LOD0.json', False, ())]
        out, ok = [], True
        for f, expect, ds in cases:
            d = json.load(open(os.path.join(here, f), encoding='utf8'))
            j = judge(d, ds)
            good = j['PASS'] == expect
            ok &= good
            out.append(dict(file=f, declaredSteps=list(ds), expectPass=expect, got=j['PASS'], asExpected=good,
                            failed=[k for k, v in j.items() if v is False], numbers=j['numbers']))
        json.dump(dict(selftestOK=ok, cases=out), open(os.path.join(here, 'selftest-check.json'), 'w', encoding='utf8'), indent=1)
        print(json.dumps(dict(selftestOK=ok, cases=[(c['file'], c['declaredSteps'], c['got'], c['asExpected'], c['failed']) for c in out])))
        sys.exit(0 if ok else 1)
    d = json.load(open(a.file, encoding='utf8'))
    j = judge(d, a.declared_steps)
    print(json.dumps(j, indent=1))
    sys.exit(0 if (j['PASS'] != a.neg) else 1)


if __name__ == '__main__':
    main()
