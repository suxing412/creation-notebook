# -*- coding: utf-8 -*-
# LY-006: validate a seat interface file (templates/interface.template.json) against the frozen registry.
# Usage: python -I validate_interface.py <registry dir> <interface.json> [<seat dir for files>]
import json, sys, os, re, math, hashlib
def load(p): return json.load(open(p, encoding='utf-8'))
PORT_RX = re.compile(r'^[A-Za-z0-9_.-]+(:[A-Za-z0-9_.-]+){1,3}$')
KINDS = {'ground', 'threshold', 'floor', 'wall-end', 'road-end', 'mount', 'opening', 'cut', 'drain'}
EVID = ('原始考古/原文', '异地异期类比', 'C工程设计', '未知')

def validate(regdir, f, seatdir=None):
    Z = load(os.path.join(regdir, 'zones.json')); P = load(os.path.join(regdir, 'ports.json'))['ports']
    O = load(os.path.join(regdir, 'ownership.json')); S = load(os.path.join(regdir, 'seats.json'))
    errs = []
    seat = f.get('seat')
    if f.get('schema') != 'LY-006-interface-v1': errs.append('schema != LY-006-interface-v1')
    if seat not in S['seats']: return [f'unknown seat {seat}']
    t = S['seats'][seat]; own = O['ownership']
    if f.get('registryVersion') != S['version']: errs.append(f"registryVersion {f.get('registryVersion')} != {S['version']}")
    if f.get('baseline') != S['baseline']: errs.append('baseline mismatch')
    for fr in f.get('frames', []):
        if fr not in Z['frames']: errs.append(f'unknown frame {fr}')
    c = f.get('claims', {})
    for so in c.get('sourceObjects', []):
        r = own['sourceObjects'].get(so['objectId'])
        if not r: errs.append(f"unknown source object {so['objectId']}"); continue
        if r['owner'] != seat: errs.append(f"{so['objectId']} is owned by {r['owner']}, not {seat}")
        elif so['mode'] in ('modify', 'replace') and r['mode'] == 'keep': errs.append(f"{so['objectId']}: registry grants keep only")
    for cn in c.get('cityNodes', []):
        r = own['cityNodes'].get(cn['nodeId'])
        if not r or r['owner'] != seat: errs.append(f"city node {cn['nodeId']} not owned by {seat}")
    for g in c.get('groundPieces', []):
        r = own['groundPieces'].get(g)
        if not r or r['owner'] != seat: errs.append(f'ground piece {g} not owned by {seat}')
    for cu in c.get('cuts', []):
        r = own['cuts'].get(cu)
        if not r or r['requester'] != seat: errs.append(f'cut {cu} not registered for {seat}')
    for cf in c.get('cardFields', []):
        fld = cf['field']; r = own['cardFields'].get(fld)
        if r is None and '#notes.' in fld: r = own['cardFields'].get(fld.split('#')[0] + '#notes.*')
        if not r: errs.append(f'unknown card field {fld}')
        elif r['owner'] is None: errs.append(f"card field {fld} is frozen")
        elif r['owner'] != seat and t['siteOwner'] != r['owner']:
            errs.append(f"card field {fld} owner {r['owner']} is neither this seat nor its site owner {t['siteOwner']}")
    reg_comp = {x['id']: x['class'] for x in t['components']}
    for co in c.get('components', []):
        if co['id'] not in reg_comp: errs.append(f"component {co['id']} not registered for {seat}"); continue
        if co['class'] != reg_comp[co['id']]: errs.append(f"component {co['id']} class {co['class']} != registry {reg_comp[co['id']]}")
        if co['class'] == 'moving':
            hp = co.get('hostPortId')
            if not hp or hp not in P or P[hp]['kind'] not in ('mount', 'opening') or (P[hp]['producer'] != seat and seat not in P[hp]['consumers']):
                errs.append(f"moving {co['id']} needs hostPortId = a mount/opening port this seat produces or consumes")
    zones = {z['zoneId']: z for z in Z['zones']}
    for zu in f.get('zonesUsed', []):
        z = zones.get(zu['zoneId'])
        if not z or z['seat'] != seat: errs.append(f"zone {zu['zoneId']} is not a {seat} zone"); continue
        if not z['box']: continue
        for b in zu['boxesWritten']:
            if any(b[0][i] < z['box'][0][i] - 1e-6 or b[1][i] > z['box'][1][i] + 1e-6 for i in range(3)):
                errs.append(f"written box {b} outside {zu['zoneId']} {z['box']}")
    for pp in f.get('portsProduced', []):
        pid = pp.get('portId'); r = P.get(pid)
        if not PORT_RX.match(pid or ''): errs.append(f'bad port id {pid}'); continue
        if not r or r['producer'] != seat: errs.append(f'port {pid} is not produced by {seat} in the registry'); continue
        if pp.get('version') != r['version']: errs.append(f"port {pid} version {pp.get('version')} != registry {r['version']}")
        if pp.get('kind') != r['kind'] or pp.get('kind') not in KINDS: errs.append(f'port {pid} kind mismatch')
        if not pp.get('local'): errs.append(f'port {pid} has no local pose'); continue
        if not (pp.get('measuredFrom') or {}).get('sha256'): errs.append(f'port {pid} measuredFrom lacks sha256')
        fr = pp['frames']['local']
        pl = {'t': [0, 0, 0], 'yaw': 0.0} if fr == 'world' else Z['frames'].get(fr, {}).get('placement')
        if pl:
            c_, s_ = math.cos(pl['yaw']), math.sin(pl['yaw']); p = pp['local']['position']
            w = [c_ * p[0] + s_ * p[2] + pl['t'][0], p[1] + pl['t'][1], -s_ * p[0] + c_ * p[2] + pl['t'][2]]
            if not pp.get('world'): errs.append(f'port {pid}: frame {fr} is placed, world must be filled')
            elif max(abs(a - b) for a, b in zip(w, pp['world']['position'])) > 1e-5: errs.append(f'port {pid}: world != placement*local')
        elif pp.get('world') is not None: errs.append(f'port {pid}: frame unplaced, world must stay null')
    produced = {pp.get('portId') for pp in f.get('portsProduced', [])}
    for pid in t['produces']:
        if pid not in produced: errs.append(f'registry port {pid} not delivered')
    consumed = {pc['portId']: pc for pc in f.get('portsConsumed', [])}
    for pid in t['consumes']:
        if pid == 'FROZEN:*': continue
        if pid not in consumed: errs.append(f'consumed port {pid} not acknowledged'); continue
        if consumed[pid]['version'] != P[pid]['version']: errs.append(f"consumed {pid} v{consumed[pid]['version']} != registry v{P[pid]['version']}")
    for pid in consumed:
        if pid not in P or seat not in P[pid]['consumers']: errs.append(f'{pid} consumed but not registered for {seat}')
    for g in f.get('newGroundPieces', []):
        if not g['id'].startswith(f'gp:{seat}:'): errs.append(f"new ground piece {g['id']} outside namespace gp:{seat}:")
        if g.get('zoneId') not in zones or zones[g['zoneId']]['seat'] != seat: errs.append(f"new ground piece {g['id']} zone not owned")
    for k in EVID:
        if k not in f.get('evidence', {}): errs.append(f'evidence class {k} missing')
    if seatdir:
        for fi in f.get('files', []):
            p = os.path.join(seatdir, fi['path'])
            if not os.path.exists(p): errs.append(f"listed file missing {fi['path']}"); continue
            b = open(p, 'rb').read()
            if hashlib.sha256(b).hexdigest() != fi['sha256'] or len(b) != fi['bytes']: errs.append(f"file sha/size mismatch {fi['path']}")
    return errs

if __name__ == '__main__':
    regdir, path = sys.argv[1], sys.argv[2]
    seatdir = sys.argv[3] if len(sys.argv) > 3 else None
    e = validate(regdir, load(path), seatdir)
    print('PASS' if not e else 'FAIL')
    for x in e: print(' -', x)
    sys.exit(0 if not e else 1)
