# LY-087 prep: build the current-state (bce3211) drainage/bank port ledger from out/A..D json.
# This is a DRAFT inventory of what exists now; it is not a frozen LY-006 port list.
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
A = json.load(open(os.path.join(OUT, 'A-city-drains.json'), encoding='utf-8'))
C = json.load(open(os.path.join(OUT, 'C-palace-waterway.json'), encoding='utf-8'))
D = json.load(open(os.path.join(OUT, 'D-dependency-candidates.json'), encoding='utf-8'))
ports = []
seen = {}
for it in A['instances']:
    seen.setdefault(it['cityNode'], []).append(it)
for nid, its in seen.items():
    far, near = its[0], its[1]
    same = all(far[k] == near[k] for k in ('floorHigh_m', 'floorLow_m', 'world'))
    sp = far['spillBeyondLowEnd']
    void_default = all(s['courtTop'] is None for s in sp if s['dist'] <= 2.0)
    base = {'owner': {'cityNode': nid, 'asset': far['asset'], 'node': far['drainNode']}, 'class': 'in-city (首屏 residential)',
            'glb': {'far': [far['glb'], far['sha256']], 'near': [near['glb'], near['sha256']]}, 'lodConsistent': same,
            'evidence': 'C engineering (TC03 C_drain_stone); no Eastern-Han Luoyang source for this channel'}
    ports.append(dict(base, portId=f'{nid}:drain:high', role='upstream end (source)', world=far['world']['highEnd'],
                      invert_m=far['floorHigh_m'], openEnd=not far['highEndCappedOnDrainMesh'],
                      source='none modelled: no gutter/spout/downpipe feeds this end (roof drip line not connected)',
                      state='source-undeclared'))
    ports.append(dict(base, portId=f'{nid}:drain:low', role='downstream end (outlet)', world=far['world']['lowEnd'],
                      flowDir=far['world']['flowDir'], invert_m=far['floorLow_m'], slope_pct=far['slope_pct'], openEnd=not far['lowEndCappedOnDrainMesh'],
                      landing={'defaultFirstScreen': 'no surface under 0.02-2.0 m beyond the end (site_lot excluded, ground-atomic not loaded)' if void_default else 'court surface',
                               'terrainChapterLoaded': f"city terrain {sp[1]['terrainTop']} m ({sp[1]['terrainPart']}), step {sp[1]['stepFromFloorLow_m']} m, gradient 0 within 2.9 m"},
                      obstruction=far['firstObstructionDownstream'],
                      state='ponding-flat / blocked-by-wall; NO admitted outlet; not connected'))
for f, res in C['lods'].items():
    if 'inspection' in f:
        continue
    st = {s['x']: s for s in res['stations']}
    for side, x in (('inner_end_-x', -3.3), ('outer_end_+x', 3.3)):
        ports.append({'portId': f'm-luoyang-palace-waterway-interface:{f.split("-")[-1][:-4]}:{side}', 'class': 'library only (未入城, no world pose)',
                      'glb': [f'docs/library/models/m-luoyang-palace-waterway-interface/files/{f}', res['sha256']],
                      'localPosition': [x, st[-3.0 if x < 0 else 3.0]['invert'], 0.0], 'invert_m': st[-3.0 if x < 0 else 3.0]['invert'],
                      'cavity': {'width_m': res['cavityWidthAtY0.3']['-2.0']['width'], 'roof_m': st[-3.0 if x < 0 else 3.0]['roof']},
                      'openEnd': res[side]['openToOutside'], 'slope_pct': 0.0,
                      'state': 'open-unadmitted; flow direction undefined (0 fall end to end); purpose (引/排) unknown (E-H03)',
                      'evidence': 'C design from a reported 3-part brick waterway; dims, flow, use and 180 CE status unknown'})
    ports.append({'portId': f'm-luoyang-palace-waterway-interface:{f.split("-")[-1][:-4]}:shaft_top', 'class': 'library only',
                  'glb': [f'docs/library/models/m-luoyang-palace-waterway-interface/files/{f}', res['sha256']],
                  'localPosition': [0.0, 1.8, 0.0], 'openUpward': res['shaftOpenUpward'], 'shaftFloorCrossings': res['shaftCentreCrossings'],
                  'state': 'open-unadmitted; shaft floor = channel invert 0.0 (no sump)'})
for k, v in D.items():
    if k.startswith('stable/'):
        ports.append({'portId': f'm-luoyang-stable:{k.split("/")[1]}', 'class': 'library only (LY-052 pending)', 'glb': [k, v['sha256']],
                      'state': f"no drainage element; platform top flat y={v['topY']} ({v['topVertexCount']} verts, spread {v['topYSpread_m']} m)"})
    elif k.startswith('kiln/'):
        ports.append({'portId': f'm-luoyang-tile-kiln:{k.split("/")[1]}', 'class': 'library only (LY-054 pending)', 'glb': [k, v['sha256']],
                      'state': f"no drainage-like node among {v['nodeCount']} nodes; LY-054 scope defines no drain port"})
    elif k.startswith('biyong/'):
        ports.append({'portId': 'biyong_C_relationship:A_square_water_symbol', 'class': 'modeling-lab ZIP chunk (网页未接入), via LY-073 extract',
                      'glb': [v['glb'], v['sha256']], 'bbox': [v['bboxMin'], v['bboxMax']],
                      'state': f"closed loop: water present at {v['anglesWithWater_of360']}/360 bearings; no inlet/outlet; conflicts E-R05 (北无水; 考古所见自北部涵洞分东西南流, 未见闭合)"})
# cross-reference with the frozen LY-006 registry v1 (read-only)
import hashlib
R6 = 'D:/GitHub/creation-notebook-workpacks/LY-006/registry'
r6p = json.load(open(R6 + '/ports.json', encoding='utf-8'))['ports']
r6o = json.load(open(R6 + '/ownership.json', encoding='utf-8'))['ownership']['cityNodes']
xref = {'registryFiles': {f: hashlib.sha256(open(f'{R6}/{f}', 'rb').read()).hexdigest() for f in ('ports.json', 'seats.json', 'ownership.json')},
        'drainPortsInRegistry': {k: {'producer': v['producer'], 'version': v['version'], 'consumers': v.get('consumers', []),
                                     'valuesFilled': v.get('local') is not None or v.get('world') is not None}
                                 for k, v in r6p.items() if v.get('kind') == 'drain'},
        'existingDrainNodesNotRegistered': {n: r6o.get(n) for n in seen
                                            if not any(k.startswith(n + ':') for k, v in r6p.items() if v.get('kind') == 'drain')}}
reg = {'baseline': 'bce3211f818ee5a8bef1773539da70695ba37b17',
       'status': 'prep ledger of existing geometry at bce3211 (not a frozen port list). LY-006 registry v1 has kind drain (5 declared ports, values null); '
                 'the 6 existing TC03 drain nodes carry no registry port (city nodes frozen, owner null).',
       'ly006': xref, 'ports': ports}
json.dump(reg, open(os.path.join(OUT, 'port-registry-current-state.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(ports), 'ports')
for p in ports:
    print(p['portId'], '|', p['state'][:110])
