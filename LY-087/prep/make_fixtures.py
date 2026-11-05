# LY-087 prep: fixtures for check_port_graph.py (synthetic) + the measured current state (bce3211).
import os, json, copy
HERE = os.path.dirname(os.path.abspath(__file__)); FX = os.path.join(HERE, 'fixtures'); os.makedirs(FX, exist_ok=True)
REG = json.load(open(os.path.join(HERE, 'out', 'port-registry-current-state.json'), encoding='utf-8'))


def port(pid, seat, kind, inv, src='channel', dst='connected', nodes=(), world=None, adm=False, **kw):
    d = {'portId': pid, 'version': 1, 'ownerSeat': seat, 'ownerNodes': list(nodes), 'kind': kind, 'invert_m': inv,
         'sourceState': src, 'destState': dst, 'world': world, 'admittedOutlet': adm}
    d.update(kw); return d


pos = {'expect': 'pass', 'ports': [
    port('LY-046:trial:in', 'LY-046', 'drain-inlet', 0.232, src='roof-drip', nodes=['ly046_drip_trial_a']),
    port('LY-046:trial:out', 'LY-046', 'drain-outlet', 0.205, nodes=['ly046_outlet_port']),
    # 2026-11-06: sump moved from LY-087 to LY-046 -- LY-006 registry v1 gives LY-087 no write zone (R9)
    port('LY-046:sump:a', 'LY-046', 'drain-inlet', 0.180, src='upstream-port', dst='local-sump', nodes=['ly046_sump_a'])],
    'edges': [{'from': 'LY-046:trial:in', 'to': 'LY-046:trial:out', 'length_m': 18.0},
              {'from': 'LY-046:trial:out', 'to': 'LY-046:sump:a', 'length_m': 2.0, 'animated': False}],
    'seams': []}
neg_back = copy.deepcopy(pos); neg_back['expect'] = 'R2'; neg_back['ports'][2]['invert_m'] = 0.210
neg_anim = copy.deepcopy(neg_back); neg_anim['expect'] = 'R2,R5'; neg_anim['edges'][1]['animated'] = True
neg_cycle = copy.deepcopy(pos); neg_cycle['expect'] = 'R3'
neg_cycle['edges'].append({'from': 'LY-046:sump:a', 'to': 'LY-046:trial:in', 'length_m': 20.0})
neg_river = copy.deepcopy(pos); neg_river['expect'] = 'R4'
neg_river['ports'].append(port('river:luo-modern', 'none', 'river', 0.0, src='unknown', dst='unknown'))
neg_river['edges'].append({'from': 'LY-046:sump:a', 'to': 'river:luo-modern', 'length_m': 500.0})
neg_owner = copy.deepcopy(pos); neg_owner['expect'] = 'R6'; neg_owner['ports'][2]['ownerSeat'] = 'LY-052'; neg_owner['ports'][2]['ownerNodes'] = ['ly046_outlet_port']
neg_seam = copy.deepcopy(pos); neg_seam['expect'] = 'R7'
neg_seam['seams'] = [{'a': port('LY-052:槽前:out', 'LY-052', 'drain-outlet', 0.10, world=[1, 0.10, 2]),
                      'b': port('LY-052:槽前:out', 'LY-087', 'drain-outlet', 0.11, world=[1.02, 0.11, 2])}]
neg_void = copy.deepcopy(pos); neg_void['expect'] = 'R1'; neg_void['ports'][1]['destState'] = 'void'; neg_void['edges'] = neg_void['edges'][:1]
neg_nostate = copy.deepcopy(pos); neg_nostate['expect'] = 'R1'; del neg_nostate['ports'][0]['sourceState']

# ---- registry mode (LY-006 registry v1): plain synthetic fixtures do not carry the 4 consumed ports -> R8
for g in (pos, neg_back, neg_anim, neg_cycle, neg_river, neg_owner, neg_seam, neg_void, neg_nostate):
    g['expectRegistry'] = ('R8' if g['expect'] == 'pass' else g['expect'] + ',R8')
CONSUMED = [('C02-010:drip-outlet:drain', 'LY-046'), ('stable:drain-outlet:drain', 'LY-052'),
            ('kiln:front-drain:drain', 'LY-054'), ('biyong:bank-outlet:drain', 'LY-073')]
reg_pos = copy.deepcopy(pos); reg_pos['expect'] = 'pass'; reg_pos['expectRegistry'] = 'pass'
reg_pos['ports'][1]['registryPortId'] = 'C02-010:drip-outlet:drain'
reg_pos['ports'] += [port(pid, seat, 'drain-outlet', None, src='none-declared' if seat == 'LY-054' else 'channel',
                          dst='unconnected-declared', registryPortId=pid) for pid, seat in CONSUMED[1:]]
reg_missing = copy.deepcopy(reg_pos); reg_missing['expect'] = 'pass'; reg_missing['expectRegistry'] = 'R8'
reg_missing['ports'] = [p for p in reg_missing['ports'] if p.get('registryPortId') != 'kiln:front-drain:drain']
reg_version = copy.deepcopy(reg_pos); reg_version['expect'] = 'pass'; reg_version['expectRegistry'] = 'R8'
reg_version['ports'][1]['version'] = 2
reg_producer = copy.deepcopy(reg_pos); reg_producer['expect'] = 'pass'; reg_producer['expectRegistry'] = 'R8'
reg_producer['ports'][-1]['ownerSeat'] = 'LY-087'
reg_geom = copy.deepcopy(reg_pos); reg_geom['expect'] = 'pass'; reg_geom['expectRegistry'] = 'R9'
reg_geom['ports'].append(port('LY-087:marker:a', 'LY-087', 'drain-inlet', 0.17, src='upstream-port', dst='local-sump', nodes=['ly087_sump_a']))


def current(state):
    ports = []
    for p in REG['ports']:
        pid = p['portId']
        if ':drain:high' in pid:
            ports.append(port(pid, 'existing:' + p['owner']['asset'], 'drain-inlet', p['invert_m'], src='none-declared', dst='connected',
                              world=p['world'], nodes=[p['owner']['cityNode'] + '/' + p['owner']['node']]))
        elif ':drain:low' in pid:
            ports.append(port(pid, 'existing:' + p['owner']['asset'], 'drain-outlet', p['invert_m'], src='channel',
                              dst='void' if state == 'default' else 'ponding-flat', world=p['world'], nodes=[]))
        elif pid.startswith('biyong'):
            ports.append(port(pid, 'LY-073(draft)', 'water-body', -0.10, src='none-declared', dst='unknown', closedLoop=True, animated=False))
    edges = [{'from': p['portId'], 'to': p['portId'].replace(':high', ':low'), 'length_m': next(q for q in REG['ports'] if q['portId'] == p['portId'].replace(':high', ':low'))['slope_pct'] and
              (p['invert_m'] - next(q for q in REG['ports'] if q['portId'] == p['portId'].replace(':high', ':low'))['invert_m']) * 100 /
              next(q for q in REG['ports'] if q['portId'] == p['portId'].replace(':high', ':low'))['slope_pct']}
             for p in ports if p['portId'].endswith(':drain:high')]
    return {'expect': 'R1' if state == 'default' else 'pass', 'expectRegistry': 'R1,R8' if state == 'default' else 'R8', 'baseline': REG['baseline'], 'loadState': state, 'ports': ports, 'edges': edges, 'seams': []}


fx = {'fx-pos.json': pos, 'fx-neg-backfall.json': neg_back, 'fx-neg-anim.json': neg_anim, 'fx-neg-cycle.json': neg_cycle,
      'fx-neg-autoriver.json': neg_river, 'fx-neg-owner.json': neg_owner, 'fx-neg-seam.json': neg_seam,
      'fx-neg-void.json': neg_void, 'fx-neg-nostate.json': neg_nostate,
      'fx-reg-pos.json': reg_pos, 'fx-reg-neg-missing.json': reg_missing, 'fx-reg-neg-version.json': reg_version,
      'fx-reg-neg-producer.json': reg_producer, 'fx-reg-neg-ly087geom.json': reg_geom,
      'current-bce3211-default-firstscreen.json': current('default'),
      'current-bce3211-terrain-chapter.json': current('terrain')}
for n, g in fx.items():
    json.dump(g, open(os.path.join(FX, n), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(fx))
