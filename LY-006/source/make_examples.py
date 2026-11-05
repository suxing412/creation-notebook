# -*- coding: utf-8 -*-
# LY-006: build two validator fixtures from the template (one valid, one with injected violations)
# and run the validator on both -> qa/interface-validator-selftest.json. Usage (from LY-006/):
#   python -I source/make_examples.py .
import json, copy, os, sys, math, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from validate_interface import validate
W6 = sys.argv[1]
J = lambda *p: os.path.join(W6, *p)
load = lambda p: json.load(open(p, encoding='utf-8'))
Z = [z for z in load(J('registry/zones.json'))['zones'] if z['seat'] == 'LY-013']
F = load(J('registry/zones.json'))['frames']['local:kaiyang-K-v1']['placement']
tpl = load(J('templates/interface.template.json'))
ex = copy.deepcopy(tpl); ex.pop('_howTo')
c, s = math.cos(F['yaw']), math.sin(F['yaw'])
loc = [0.0, 5.34, 0.0]
wpos = [c * loc[0] + s * loc[2] + F['t'][0], loc[1] + F['t'][1], -s * loc[0] + c * loc[2] + F['t'][2]]
ex.update({
    'seat': 'LY-013', 'frames': ['local:kaiyang-K-v1'],
    'claims': {'sourceObjects': [{'objectId': 'kaiyang-K-v1:C_upper_deck', 'mode': 'replace'}], 'cityNodes': [], 'groundPieces': [], 'cuts': [],
               'cardFields': [{'field': 'm-luoyang-kaiyang-gate#notes.限制与待解决', 'proposal': '（示例）单一楼板替换 C_upper_deck；荷载未验。'}],
               'components': [{'id': 'K013-deck', 'class': 'fixed'}, {'id': 'K013-surface', 'class': 'fixed'}]},
    'zonesUsed': [{'zoneId': Z[0]['zoneId'], 'boxesWritten': [[[-12.4, 5.0, -5.0], [12.4, 5.34, 5.0]]]}],
    'portsProduced': [{'portId': 'kaiyang-K-v1:deck-top:floor', 'version': 1, 'kind': 'floor', 'producer': 'LY-013', 'steward': 'LY-013', 'consumers': ['LY-014', 'LY-015'],
                       'frames': {'local': 'local:kaiyang-K-v1', 'world': 'luoyang-local-schematic-v01'},
                       'local': {'position': loc, 'up': [0, 1, 0], 'forward': [0, 0, -1]},
                       'world': {'position': wpos, 'up': [0, 1, 0], 'forward': [-s, 0, -c]},
                       'nodeMatrixColumnMajor': [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, F['t'][0], F['t'][1], F['t'][2], 1],
                       'measuredFrom': {'file': '(example) models/kaiyang-deck-LOD0.glb', 'sha256': '0' * 64, 'method': '(example) deck top face'},
                       'elevationClass': 'C-engineering', 'tolerance_m': {'position': 0.005, 'elevation': 0.002}}],
    'portsConsumed': [{'portId': 'kaiyang-K-v1:central-frame-top:floor', 'version': 1, 'ack': 'accepted', 'measuredResidual_m': 0.0}],
    'newGroundPieces': [],
    'install': {'order': ['(example) mask C_upper_deck triangle range, add K013-deck'], 'replaces': ['kaiyang-K-v1:C_upper_deck'], 'hides': [],
                'rollback': ['(example) remove K013-deck, restore range'], 'exclusiveWith': []},
    'evidence': {'原始考古/原文': [], '异地异期类比': [], 'C工程设计': ['（示例）楼板厚度沿用 K-v1 0.34 m'], '未知': ['真实楼板构造']},
    'files': [], '_note': 'EXAMPLE FIXTURE for the validator self-test only; values are illustrative, not an LY-013 delivery'})
bad = copy.deepcopy(ex)
bad['claims']['sourceObjects'].append({'objectId': 'kaiyang-K-v1:C_door_head_1', 'mode': 'modify'})   # owned by LY-011
bad['zonesUsed'][0]['boxesWritten'][0][1][1] = 5.6                                                     # leaves the deck zone
bad['portsConsumed'][0]['version'] = 2                                                                 # version mismatch
bad['portsProduced'][0]['world']['position'][1] += 0.2                                                 # world != placement*local
bad['claims']['components'].append({'id': 'K012-leaf-C-W', 'class': 'moving'})                         # another seat's moving part
bad['newGroundPieces'] = [{'id': 'gp:LY-014:deck-skirt', 'zoneId': Z[0]['zoneId']}]                    # wrong namespace
bad['_note'] = 'NEGATIVE FIXTURE: six injected violations; the validator must report each'
os.makedirs(J('templates/examples'), exist_ok=True)
for name, obj in (('LY-013.example.pass.json', ex), ('LY-013.example.fail.json', bad)):
    json.dump(obj, open(J('templates/examples', name), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
res = {}
for name in ('LY-013.example.pass.json', 'LY-013.example.fail.json'):
    p = J('templates/examples', name)
    e = validate(J('registry'), load(p))
    res[name] = {'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(), 'errors': e, 'pass': not e}
res['expect'] = {'LY-013.example.pass.json': 'pass', 'LY-013.example.fail.json': 'fail with >= 6 errors'}
res['ok'] = res['LY-013.example.pass.json']['pass'] and (not res['LY-013.example.fail.json']['pass']) and len(res['LY-013.example.fail.json']['errors']) >= 6
json.dump(res, open(J('qa/interface-validator-selftest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
