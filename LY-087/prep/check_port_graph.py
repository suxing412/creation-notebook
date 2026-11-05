# LY-087 prep: drainage port-graph consistency checker (data-level; geometry is re-measured separately).
# usage: python -I check_port_graph.py graph.json [more.json ...]
# graph schema (draft, to be aligned with LY-006 once frozen):
# {"ports":[{"portId","version","ownerSeat","ownerNodes":[...],"kind":"drain-inlet|drain-outlet|bank-edge|water-body|river",
#            "world":[x,y,z]|null,"invert_m":float|null,"sourceState":str,"destState":str,"admittedOutlet":bool}],
#  "edges":[{"from","to","length_m","animated":bool}],
#  "seams":[{"a","b"}]}   # a/b = two records claiming the same physical port (must agree)
#
# registry mode (added 2026-11-06 after LY-006 registry v1 froze):
#   python -I check_port_graph.py --registry D:/GitHub/creation-notebook-workpacks/LY-006/registry f.json ...
#   R8  every LY-006 drain port that lists LY-087 as consumer must appear in the graph as a port whose
#       registryPortId == portId and version == registry version; every port with registryPortId must exist
#       in the registry with kind 'drain', the same producer as ownerSeat, and a matching version.
#   R9  LY-087 owns no write zone and produces nothing in registry v1 (seats.json): any port with
#       ownerSeat 'LY-087' and non-empty ownerNodes, or any ownerNodes starting 'ly087_', fails.
#   W   ports on existing geometry (ownerSeat 'existing:*') must name city nodes that ownership.json marks
#       frozen; LY-087 may only read them.
#   In registry mode the expected result is taken from the fixture's "expectRegistry" key (falls back to "expect").
import sys, json, os
SOURCE_STATES = {'roof-drip', 'surface-runoff', 'upstream-port', 'channel', 'none-declared', 'unknown'}
DEST_STATES = {'connected', 'local-sump', 'ponding-flat', 'blocked', 'unconnected-declared', 'void', 'unknown'}
MIN_FALL_PCT = 0.0      # strictly > 0 required on every connected edge (no flat or adverse edge passes)
TOL_POS, TOL_INV = 0.005, 0.002


def check(g):
    fails, warns = [], []
    P = {p['portId']: p for p in g['ports']}
    for p in g['ports']:
        if p['kind'] in ('drain-outlet', 'drain-inlet'):
            if p.get('sourceState') not in SOURCE_STATES:
                fails.append(f"R1 {p['portId']}: sourceState missing/invalid ({p.get('sourceState')})")
            if p.get('destState') not in DEST_STATES:
                fails.append(f"R1 {p['portId']}: destState missing/invalid ({p.get('destState')})")
            if p.get('destState') == 'void':
                fails.append(f"R1 {p['portId']}: outlet lands on no surface")
            if p.get('destState') == 'connected' and not any(e['from'] == p['portId'] for e in g.get('edges', [])):
                fails.append(f"R1 {p['portId']}: destState=connected but no outgoing edge")
    adj = {}
    for e in g.get('edges', []):
        a, b = P.get(e['from']), P.get(e['to'])
        if a is None or b is None:
            fails.append(f"R0 edge {e['from']}->{e['to']}: unknown port"); continue
        adj.setdefault(e['from'], []).append(e['to'])
        if a.get('invert_m') is None or b.get('invert_m') is None:
            fails.append(f"R2 edge {e['from']}->{e['to']}: invert unknown, slope cannot be verified")
        else:
            fall = a['invert_m'] - b['invert_m']
            pct = 100 * fall / max(e.get('length_m', 1e-9), 1e-9)
            if pct <= MIN_FALL_PCT:
                fails.append(f"R2 edge {e['from']}->{e['to']}: fall {fall:+.4f} m ({pct:+.4f}%) not downhill")
                if e.get('animated'):
                    fails.append(f"R5 edge {e['from']}->{e['to']}: flow animation over a non-downhill edge")
        if b['kind'] == 'river' and not (a.get('admittedOutlet') and b.get('admittedOutlet')):
            fails.append(f"R4 edge {e['from']}->{e['to']}: connects to a river/canal without an admitted outlet")
    # R3 cycles
    color = {}

    def dfs(u, stack):
        color[u] = 1
        for v in adj.get(u, []):
            if color.get(v) == 1:
                fails.append('R3 cycle: ' + ' -> '.join(stack + [u, v]))
            elif color.get(v) is None:
                dfs(v, stack + [u])
        color[u] = 2
    for u in list(adj):
        if color.get(u) is None:
            dfs(u, [])
    for p in g['ports']:
        if p['kind'] == 'water-body' and p.get('closedLoop') and p.get('sourceState') in (None, 'none-declared') and p.get('animated'):
            fails.append(f"R3/R5 {p['portId']}: animated closed water loop with no declared source")
        if p['kind'] == 'water-body' and p.get('closedLoop'):
            warns.append(f"W {p['portId']}: closed loop water body; must stay static symbol and carry its evidence conflict")
    # R6 ownership
    owner_of = {}
    for p in g['ports']:
        for n in p.get('ownerNodes', []):
            if n in owner_of and owner_of[n] != p['ownerSeat']:
                fails.append(f"R6 node {n}: owned by {owner_of[n]} and {p['ownerSeat']}")
            owner_of.setdefault(n, p['ownerSeat'])
    # R7 seams
    for s in g.get('seams', []):
        a, b = s['a'], s['b']
        if a['portId'] != b['portId'] or a.get('version') != b.get('version'):
            fails.append(f"R7 seam {a['portId']}/{b['portId']}: id/version mismatch")
        if a.get('world') and b.get('world'):
            d = max(abs(x - y) for x, y in zip(a['world'], b['world']))
            if d > TOL_POS:
                fails.append(f"R7 seam {a['portId']}: position differs {d:.4f} m > {TOL_POS}")
        if a.get('invert_m') is not None and b.get('invert_m') is not None and abs(a['invert_m'] - b['invert_m']) > TOL_INV:
            fails.append(f"R7 seam {a['portId']}: invert differs {abs(a['invert_m'] - b['invert_m']):.4f} m > {TOL_INV}")
    return fails, warns


def load_registry(d):
    ports = json.load(open(os.path.join(d, 'ports.json'), encoding='utf-8'))['ports']
    seats = json.load(open(os.path.join(d, 'seats.json'), encoding='utf-8'))
    seats = seats.get('seats', seats) if isinstance(seats, dict) else seats
    if isinstance(seats, list):
        seats = {s['seat']: s for s in seats}
    own = json.load(open(os.path.join(d, 'ownership.json'), encoding='utf-8'))['ownership']['cityNodes']
    return ports, seats, own


def check_registry(g, reg):
    ports, seats, own = reg
    fails, warns = [], []
    me = seats.get('LY-087', {})
    consumed = {k: v for k, v in ports.items() if v.get('kind') == 'drain' and 'LY-087' in v.get('consumers', [])}
    have = {}
    for p in g['ports']:
        rid = p.get('registryPortId')
        if rid is None:
            continue
        have[rid] = p
        r = ports.get(rid)
        if r is None:
            fails.append(f"R8 {p['portId']}: registryPortId {rid} not in LY-006 registry"); continue
        if r.get('kind') != 'drain':
            fails.append(f"R8 {p['portId']}: registry kind {r.get('kind')} is not drain")
        if r.get('version') != p.get('version'):
            fails.append(f"R8 {p['portId']}: version {p.get('version')} != registry {r.get('version')}")
        if r.get('producer') != p.get('ownerSeat'):
            fails.append(f"R8 {p['portId']}: ownerSeat {p.get('ownerSeat')} != registry producer {r.get('producer')}")
    for rid in consumed:
        if rid not in have:
            fails.append(f"R8 consumed port {rid} (producer {consumed[rid].get('producer')}) missing from graph")
    may_write = bool(me.get('writeZones')) or bool(me.get('produces')) or bool(me.get('ownsCityNodes'))
    for p in g['ports']:
        nodes = p.get('ownerNodes', [])
        if not may_write and ((p.get('ownerSeat') == 'LY-087' and nodes) or any(str(n).startswith('ly087_') for n in nodes)):
            fails.append(f"R9 {p['portId']}: LY-087 has no write zone / produces nothing in registry; cannot own {nodes}")
        if str(p.get('ownerSeat', '')).startswith('existing:'):
            for n in nodes:
                cn = n.split('/')[0]
                st = own.get(cn, {}).get('status')
                if st != 'frozen':
                    warns.append(f"W {p['portId']}: existing node {cn} ownership status {st!r} (expected frozen, read-only)")
    return fails, warns


if __name__ == '__main__':
    rc = 0
    args = sys.argv[1:]
    reg = None
    if args[:1] == ['--registry']:
        reg = load_registry(args[1]); args = args[2:]
    for f in args:
        g = json.load(open(f, encoding='utf-8'))
        fails, warns = check(g)
        exp = g.get('expect')
        if reg is not None:
            f2, w2 = check_registry(g, reg)
            fails += f2; warns += w2
            exp = g.get('expectRegistry', exp)
        ok = (not fails) if exp in (None, 'pass') else bool(fails) and all(any(x.startswith(code) for x in fails) for code in exp.split(','))
        print(f"{'OK ' if ok else 'BAD'} {f}: expect={exp or 'pass'} fails={len(fails)} warns={len(warns)}")
        for x in fails + warns:
            print('    ', x)
        rc |= 0 if ok else 1
    sys.exit(rc)
