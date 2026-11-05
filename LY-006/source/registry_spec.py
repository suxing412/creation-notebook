# -*- coding: utf-8 -*-
# LY-006 registry specification: the hand-made ownership decisions for seats LY-011..LY-090.
# Everything numeric here is either (a) a reference to a measured file that build_registry.py
# resolves and hashes, or (b) an explicit C-partition box chosen by LY-006 to split write space.
# C-partition boxes are engineering allocations, not historical or archaeological claims.
#
# Conventions (inherit LY-005 coordinate contract v1.0): glTF metres, right-handed, +X east, +Y up,
# -Z north. Boxes are [[xmin,ymin,zmin],[xmax,ymax,zmax]] in the named frame.

REGISTRY_VERSION = 1
BASELINE = 'bce3211f818ee5a8bef1773539da70695ba37b17'

# ---------------------------------------------------------------- frames
# placement: world = T(t) * RotY(yaw) * local ; status tells whether it is a city fact or a proposal.
FRAMES = {
    'world': {'placement': None, 'status': 'luoyang-local-schematic-v01 (LY-005)'},
    'local:kaiyang-K-v1': {'placement': {'t': [2010.3973388671875, 0.17000000178813934, 21.3011474609375], 'yaw': -0.020743634087871412},
                           'status': 'hidden-trial placement (activation=false) from source ZIP city/placement.json; not in city',
                           'evidence': 'qa/source-objects/kaiyang-K-v1.placement.json (Blender Z-up origin (x,y,z)->(x,z,-y); rotation_z -> yaw)'},
    'local:pingcheng-P-v1': {'placement': {'t': [1622.80908203125, 0.17000000178813934, 13.259963035583496], 'yaw': -0.0207437532713328},
                             'status': 'hidden-trial placement (activation=false); not in city',
                             'evidence': 'qa/source-objects/pingcheng-P-v1.placement.json'},
    'local:gu-G-v1': {'placement': None, 'status': 'unplaced; slot envelope only (wall seam 00/01)'},
    'local:xia-B-v1': {'placement': None, 'status': 'unplaced; slot envelope only (wall seam 00/11)'},
    'local:market-site': {'placement': {'t': [214.286, 0.0, -1959.184], 'yaw': 0.0},
                          'status': 'C: centre of market-main bounds; frontage v2.1 assumed at (0,0.2,0) in this frame as in the mother-scene chunk (LY-025/028 prep). LY-029 must confirm before any city use',
                          'evidence': 'market-cluster.glb sample_ground AABB [184.286..244.286]x[-1981.184..-1937.184]'},
    'local:frontage-v2.1': {'placement': {'t': [214.286, 0.2, -1959.184], 'yaw': 0.0}, 'status': 'C assumption = market-site + (0,0.2,0); unconfirmed'},
    'local:storage-site': {'placement': {'t': [2285.714, 0.0, -3673.469], 'yaw': 0.0},
                           'status': 'in city: granary-city-LOD0 (storage-main) internal translation (LY-005 note)'},
    'local:wuku-B-v2.2': {'placement': None, 'status': 'unplaced (LY-003 gate); old trial support near NE road end'},
    'local:wuku-A-v2': {'placement': None, 'status': 'unplaced; A/B exclusive (LY-038)'},
    'court:C02-010': {'placement': {'t': [531.0, 0.0, -818.45], 'yaw': 0.0},
                      'status': 'city node C02-010 (courtyard-A2, calt) = candidate demonstration court (LY-041 prep); LY-010 freezes the choice. If another court is chosen this frame and all 041-050 zones are re-issued as registry v2',
                      'evidence': 'docs/cities/luoyang/data/far44/instances-calt.json via LY-001 dump'},
    'local:stable-A': {'placement': None, 'status': 'unplaced'}, 'local:stable-B': {'placement': None, 'status': 'unplaced'},
    'local:kiln-A': {'placement': None, 'status': 'unplaced'}, 'local:kiln-B': {'placement': None, 'status': 'unplaced'},
    'local:hand-mill': {'placement': None, 'status': 'unplaced (A and B share this local frame; A/B exclusive)'},
    'local:foot-pestle': {'placement': None, 'status': 'unplaced'},
    'local:workshed': {'placement': None, 'status': 'unplaced'},
    'local:work-site': {'placement': None, 'status': 'composed frame defined by LY-058/LY-060 (selected work sample); unplaced'},
    'local:admission-court': {'placement': None, 'status': 'unplaced (LY-003)'},
    'local:paired-que': {'placement': None, 'status': 'unplaced'},
    'local:deyang': {'placement': None, 'status': 'unplaced; A(5-bay)/B(7-bay) exclusive'},
    'local:yutang': {'placement': None, 'status': 'unplaced; A/B exclusive'},
    'local:gallery-A': {'placement': None, 'status': 'unplaced'}, 'local:gallery-B': {'placement': None, 'status': 'unplaced'},
    'local:palace-composite': {'placement': None, 'status': 'composed frame defined by LY-069/LY-070; unplaced'},
    'local:biyong': {'placement': None, 'status': 'unplaced; hall A origin; enclosure joined by LY-071 locked transform'},
    'local:mingtang': {'placement': None, 'status': 'unplaced; A/B exclusive'},
    'local:lingtai-A': {'placement': None, 'status': 'unplaced'},
    'local:taixue-A': {'placement': None, 'status': 'unplaced'},
    'local:stoneclassic': {'placement': None, 'status': 'unplaced'},
    'local:south-altar': {'placement': None, 'status': 'unplaced (south suburb); A/B exclusive'},
    'local:north-altar': {'placement': None, 'status': 'unplaced (north suburb, never grouped with south)'},
    'local:waterway': {'placement': None, 'status': 'unplaced wall research block'},
}

# ---------------------------------------------------------------- sites (assembly envelopes)
# A site groups the seats that may write inside its envelope. World envelopes of different sites must
# not overlap; write zones of a seat may only fall inside envelopes of its own site.
GAP_HALF = 16.0  # wall gate slots are 32.0 m between facing caps (qa/wall-end-ports.json)
SITES = {
    'S-KAIYANG': {'seats': ['LY-011', 'LY-012', 'LY-013', 'LY-014', 'LY-015', 'LY-085'], 'owner': 'LY-015',
                  'envelope': {'frame': 'local:kaiyang-K-v1', 'box': [[-GAP_HALF, -0.3, -11.0], [GAP_HALF, 10.6, 7.0]]}},
    'S-PINGCHENG': {'seats': ['LY-016', 'LY-017', 'LY-085'], 'owner': 'LY-017',
                    'envelope': {'frame': 'local:pingcheng-P-v1', 'box': [[-GAP_HALF, -0.3, -14.0], [GAP_HALF, 10.6, 14.0]]}},
    'S-GU': {'seats': ['LY-018'], 'owner': 'LY-018', 'envelope': {'frame': 'wallseam:wall-A-wall-00/wall-A-wall-01', 'halfDepth': 8.0, 'y': [-0.3, 10.6]}},
    'S-XIA': {'seats': ['LY-019'], 'owner': 'LY-019', 'envelope': {'frame': 'wallseam:wall-A-wall-00/wall-A-wall-11', 'halfDepth': 8.0, 'y': [-0.3, 10.6]}},
    'S-MARKET': {'seats': ['LY-021', 'LY-022', 'LY-023', 'LY-024', 'LY-025', 'LY-026', 'LY-027', 'LY-028', 'LY-029', 'LY-030'], 'owner': 'LY-030',
                 'envelope': {'frame': 'local:market-site', 'box': [[-30.0, -0.8, -22.0], [30.0, 5.0, 22.0]]}},
    'S-STORAGE': {'seats': ['LY-031', 'LY-032', 'LY-033', 'LY-034', 'LY-035', 'LY-039', 'LY-040'], 'owner': 'LY-040',
                  'envelope': {'frame': 'local:storage-site', 'box': [[-36.0, -0.3, -26.0], [36.0, 5.5, 26.0]]}},
    'S-NE-ROAD': {'seats': ['LY-039'], 'owner': 'LY-040',
                  'envelope': {'frame': 'world', 'boxes': [[[2283.714, -0.3, -3647.469], [2287.714, 0.6, -3484.0]], [[2287.714, -0.3, -3490.5], [2318.327, 0.6, -3484.0]]]}},
    'S-WUKU': {'seats': ['LY-036', 'LY-037', 'LY-038', 'LY-040'], 'owner': 'LY-040', 'envelope': None},
    'S-COURT': {'seats': ['LY-041', 'LY-042', 'LY-043', 'LY-044', 'LY-045', 'LY-046', 'LY-047', 'LY-048', 'LY-049', 'LY-050'], 'owner': 'LY-050',
                'envelope': {'frame': 'court:C02-010', 'box': [[-9.0, -1.6, -12.0], [9.0, 5.6, 12.0]]}},
    'S-COURT-LANE': {'seats': ['LY-082'], 'owner': 'LY-082', 'envelope': {'frame': 'world', 'box': [[526.0, -0.3, -806.45], [530.0, 0.6, -796.45]]}},
    'S-MARKET-STREET': {'seats': ['LY-083'], 'owner': 'LY-083', 'envelope': {'frame': 'world', 'box': [[244.286, -0.3, -1981.184], [274.286, 0.6, -1937.184]]}},
    'S-WORK': {'seats': ['LY-051', 'LY-052', 'LY-053', 'LY-054', 'LY-055', 'LY-056', 'LY-057', 'LY-058', 'LY-059', 'LY-060'], 'owner': 'LY-060', 'envelope': None},
    'S-PALACE': {'seats': ['LY-061', 'LY-062', 'LY-063', 'LY-064', 'LY-065', 'LY-066', 'LY-067', 'LY-068', 'LY-069', 'LY-070'], 'owner': 'LY-070', 'envelope': None},
    'S-BIYONG': {'seats': ['LY-071', 'LY-072', 'LY-073'], 'owner': 'LY-073', 'envelope': None},
    'S-MINGTANG': {'seats': ['LY-074', 'LY-075'], 'owner': 'LY-075', 'envelope': None},
    'S-LINGTAI': {'seats': ['LY-076'], 'owner': 'LY-076', 'envelope': None},
    'S-TAIXUE': {'seats': ['LY-077', 'LY-078'], 'owner': 'LY-078', 'envelope': None},
    'S-SOUTH-ALTAR': {'seats': ['LY-079'], 'owner': 'LY-079', 'envelope': None},
    'S-NORTH-ALTAR': {'seats': ['LY-080'], 'owner': 'LY-080', 'envelope': None},
    'S-WATERWAY': {'seats': ['LY-086'], 'owner': 'LY-086', 'envelope': None},
    'S-WALLS': {'seats': ['LY-020'], 'owner': 'LY-020', 'envelope': None},
    'S-CITYGROUND': {'seats': ['LY-081', 'LY-084', 'LY-087', 'LY-088', 'LY-089', 'LY-090'], 'owner': 'LY-090', 'envelope': None},
}

def B(frame, box, label, cls='write', basis='C-partition', excl=None):
    z = {'frame': frame, 'box': box, 'label': label, 'class': cls, 'basis': basis}
    if excl: z['exclusiveGroup'] = excl
    return z

def SUB(frame, box, minus, label, cls='write', basis='C-partition (box minus other seats claims)', ystep=None):
    """box minus the plan footprints of `minus` (list of seat ids, same frame); resolved by builder"""
    return {'frame': frame, 'box': box, 'minusSeats': minus, 'label': label, 'class': cls, 'basis': basis}

K, P, M, S, C = 'local:kaiyang-K-v1', 'local:pingcheng-P-v1', 'local:market-site', 'local:storage-site', 'court:C02-010'

# frontage openings (glTF z = -Blender y). Front line z=-5 for N row (interior -z), z=+5 for S row (interior +z).
SHOPS = [  # idx, x-range, z-range (glTF, market-site frame), openings x-ranges, front z, interior sign
    (0, (-15.8, -7.8), (-11.0, -5.0), [(-15.3, -14.2), (-9.4, -8.3)], -5.0, -1),
    (1, (9.8, 15.8), (-11.0, -5.0), [(12.9, 15.3)], -5.0, -1),
    (2, (-6.6, -0.6), (-9.0, -5.0), [(-3.68, -1.1)], -5.0, -1),
    (3, (0.6, 8.6), (-9.0, -5.0), [(1.1, 2.2), (7.0, 8.1)], -5.0, -1),
    (4, (-14.2, -8.2), (5.0, 9.0), [(-13.7, -11.12)], 5.0, 1),
    (5, (10.3, 18.3), (5.0, 9.0), [(10.8, 11.9), (16.7, 17.8)], 5.0, 1),
    (6, (-6.8, 1.2), (5.0, 11.0), [(-6.3, -5.2), (-0.4, 0.7)], 5.0, 1),
    (7, (2.6, 8.6), (5.0, 11.0), [(3.1, 5.5)], 5.0, 1),
]
CANOPIES = {'C00': ((-22.7, -19.3), (-7.15, -4.85)), 'C01': ((-22.15, -19.85), (-12.3, -9.7)),
            'C02': ((18.7, 21.3), (-7.15, -4.85)), 'C03': ((19.85, 22.15), (5.3, 8.7))}

def market_step_zones():
    out = []
    for (i, xr, zr, ops, zf, s) in SHOPS:
        for k, (a, b) in enumerate(ops):
            z0, z1 = sorted([zf, zf - s * 0.8])  # 0.8 m outward of the front line
            out.append(B(M, [[a - 0.3, 0.2, z0], [b + 0.3, 0.6, z1]], f'shop{i} door{k} step (outside front line)'))
    return out

def market_closure_zones():
    out = []
    for (i, xr, zr, ops, zf, s) in SHOPS:
        z0, z1 = sorted([zf, zf + s * 0.35])
        out.append(B(M, [[xr[0], 0.2, z0], [xr[1], 4.0, z1]], f'shop{i} front-plane band (closing parts)'))
    return out

def market_interior_zones():
    out = []
    for (i, xr, zr, ops, zf, s) in SHOPS:
        if s < 0: z0, z1 = zr[0], zf - 0.35
        else: z0, z1 = zf + 0.35, zr[1]
        out.append(B(M, [[xr[0], 0.42, z0], [xr[1], 3.2, z1]], f'shop{i} interior above floor (shelves/cargo proxies)'))
    return out

def canopy_zones():
    return [B(M, [[x[0] - 0.2, 0.2, z[0] - 0.2], [x[1] + 0.2, 1.3, z[1] + 0.2]], f'stall {k} feet/base (below table top 1.3)') for k, (x, z) in CANOPIES.items()]

# A2 courtyard prototype free-space (qa/court-A2-free-space.json): buildings main z[-10,-4]x[-5,4], wing x[-9,-4]z[-4,3],
# gate structure x[-5,-1]z[9,12], wall ring 1 m. C-partition of the yard below.
COURT = {
    'kitchen': [[-8.0, -0.3, 3.4], [-4.4, 3.2, 8.6]],
    'latrine': [[1.1, -1.6, -4.0], [8.0, 4.4, 3.6]],
    'storage': [[4.1, -0.3, -11.0], [8.0, 4.0, -4.0]],
    'drip': [[-3.0, -0.3, -3.6], [-2.2, 0.25, 2.9]],
    'gate': [[-5.0, -0.3, 9.0], [-1.0, 3.2, 12.0]],
}

def SPEC():
    s = {}
    # ======================= 11-20 gates and walls
    s['LY-011'] = dict(site='S-KAIYANG', role='component', frames=[K],
        zones=[B(K, [[-2.8, 0.0, -5.0], [2.8, 5.0, 1.99]], 'central passage bearing frame behind leaf sweep'),
               B(K, [[-2.8, 4.7, 1.99], [2.8, 5.0, 4.64]], 'central passage beam space under deck, in front of head'),
               B(K, [[-2.6, 4.7, 4.64], [2.6, 5.0, 4.96]], 'central door head C_door_head_1')],
        sourceObjects=[('kaiyang-K-v1', r'^C_door_head_1$', 'modify')],
        components=[('K011-columns', 'fixed'), ('K011-sill', 'fixed'), ('K011-beams', 'fixed')],
        produces=['kaiyang-K-v1:central-frame-top:floor', 'kaiyang-K-v1:central-jamb-seat-W:mount', 'kaiyang-K-v1:central-jamb-seat-E:mount', 'kaiyang-K-v1:central-head-soffit:mount'],
        consumes=['kaiyang-K-v1:passage-C:threshold'])
    s['LY-012'] = dict(site='S-KAIYANG', role='component', frames=[K],
        zones=[B(K, [[-2.8, 0.0, 1.99], [2.8, 4.7, 4.96]], 'central passage door plane + leaf sweep'),
               B(K, [[-2.8, 4.7, 4.64], [-2.6, 5.0, 4.96]], 'central jamb top W'), B(K, [[2.6, 4.7, 4.64], [2.8, 5.0, 4.96]], 'central jamb top E'),
               B(K, [[-9.6, 0.0, 1.99], [-5.6, 5.0, 4.96]], 'west passage door plane + leaf sweep'),
               B(K, [[5.6, 0.0, 1.99], [9.6, 5.0, 4.96]], 'east passage door plane + leaf sweep')],
        sourceObjects=[('kaiyang-K-v1', r'^C_jamb_', 'modify'), ('kaiyang-K-v1', r'^C_open_leaf_', 'replace'), ('kaiyang-K-v1', r'^C_leaf_batten_', 'replace'),
                       ('kaiyang-K-v1', r'^C_door_head_[02]$', 'modify')],
        components=[('K012-leaf-C-W', 'moving'), ('K012-leaf-C-E', 'moving'), ('K012-leaf-W-W', 'moving'), ('K012-leaf-W-E', 'moving'),
                    ('K012-leaf-E-W', 'moving'), ('K012-leaf-E-E', 'moving'), ('K012-pivot-sockets', 'fixed'), ('K012-stops', 'fixed')],
        produces=['kaiyang-K-v1:leaf-states:opening'],
        consumes=['kaiyang-K-v1:central-jamb-seat-W:mount', 'kaiyang-K-v1:central-jamb-seat-E:mount', 'kaiyang-K-v1:central-head-soffit:mount',
                  'kaiyang-K-v1:passage-C:threshold', 'kaiyang-K-v1:passage-W:threshold', 'kaiyang-K-v1:passage-E:threshold'])
    s['LY-013'] = dict(site='S-KAIYANG', role='component', frames=[K],
        zones=[B(K, [[-12.4, 5.0, -5.0], [12.4, 5.34, 5.0]], 'single upper deck slab (replaces C_upper_deck)')],
        sourceObjects=[('kaiyang-K-v1', r'^C_upper_deck$', 'replace')],
        components=[('K013-deck', 'fixed'), ('K013-surface', 'fixed')],
        produces=['kaiyang-K-v1:deck-top:floor'],
        consumes=['kaiyang-K-v1:central-frame-top:floor'])
    s['LY-014'] = dict(site='S-KAIYANG', role='component', frames=[K],
        zones=[B(K, [[-GAP_HALF, 0.0, -5.0], [-12.4, 9.0, 5.0]], 'west end bay: side opening / stair / wall-top transition'),
               B(K, [[12.4, 0.0, -5.0], [GAP_HALF, 9.0, 5.0]], 'east end bay: side opening / stair / wall-top transition'),
               B(K, [[-GAP_HALF, 0.0, -11.0], [GAP_HALF, 6.2, -5.0]], 'inner-side (city side, local -z) access strip')],
        sourceObjects=[('kaiyang-K-v1-trial', r'^kaiyang-K-static_earth:end-wedge-[WE]$', 'modify')], components=[('K014-access-W', 'fixed'), ('K014-access-E', 'fixed'), ('K014-walltop-W', 'fixed'), ('K014-walltop-E', 'fixed')],
        produces=['kaiyang-K-v1:inner-access-edge:road-end'],
        consumes=['kaiyang-K-v1:deck-top:floor', 'wall-A-wall-05:cap-0:wall-end', 'wall-A-wall-04:cap-1:wall-end',
                  'wall-A-wall-05:cap-0-top:floor', 'wall-A-wall-04:cap-1-top:floor'])
    s['LY-015'] = dict(site='S-KAIYANG', role='assembly', frames=[K, 'world'],
        zones=[B(K, [[-8.5, -0.16, -7.0], [8.5, 0.0, 7.0]], 'kaiyang ground strip layer below y=0 (strip top 0.042 is inherited contact)')],
        sourceObjects=[('kaiyang-K-v1', r'.*', 'keep')], researchModels=['research-north13-kaiyang-K'],
        groundPieces=['gp:kaiyang-ground-LOD0', 'gp:kaiyang-ground-LOD1', 'gp:kaiyang-ground-LOD2'],
        placementProposal=K, components=[],
        produces=[],  # passage thresholds / outer apron edge are LY-006 frozen ports stewarded by LY-015
        consumes=['kaiyang-K-v1:deck-top:floor', 'kaiyang-K-v1:leaf-states:opening', 'kaiyang-K-v1:inner-access-edge:road-end',
                  'wall-A-wall-05:cap-0:wall-end', 'wall-A-wall-04:cap-1:wall-end'],
        cards=['m-luoyang-kaiyang-gate'])
    s['LY-016'] = dict(site='S-PINGCHENG', role='component', frames=[P],
        zones=[B(P, [[-10.0, -0.2, -10.0], [10.0, 0.042, 10.0]], 'gate ground layer (strip + side passage support fixes)'),
               B(P, [[-10.0, 0.042, -14.0], [-5.8, 0.25, 14.0]], 'west side passage support/edge (no leaf intrusion)'),
               B(P, [[5.8, 0.042, -14.0], [10.0, 0.25, 14.0]], 'east side passage support/edge (no leaf intrusion)'),
               B(P, [[-10.0, -0.2, 10.0], [-5.8, 0.042, 14.0]], 'west outer connection ground'), B(P, [[5.8, -0.2, 10.0], [10.0, 0.042, 14.0]], 'east outer connection ground'),
               B(P, [[-10.0, -0.2, -14.0], [-5.8, 0.042, -10.0]], 'west inner connection ground'), B(P, [[5.8, -0.2, -14.0], [10.0, 0.042, -10.0]], 'east inner connection ground')],
        groundPieces=['gp:pingcheng-ground-LOD0', 'gp:pingcheng-ground-LOD1', 'gp:pingcheng-ground-LOD2'],
        components=[('P016-side-ground-W', 'fixed'), ('P016-side-ground-E', 'fixed')],
        produces=['pingcheng-P-v1:outer-edge-W:road-end', 'pingcheng-P-v1:outer-edge-E:road-end'],  # passage thresholds frozen by LY-006, stewarded by LY-016
        consumes=['pingcheng-P-v1:old-ramp:ground'])
    s['LY-017'] = dict(site='S-PINGCHENG', role='assembly', frames=[P, 'world'], zones=[],
        sourceObjects=[('pingcheng-P-v1', r'.*', 'keep'), ('pingcheng-P-v1-trial', r'.*', 'keep')], researchModels=['research-north13-pingcheng-P'], placementProposal=P,
        components=[('P017-central-leaves', 'fixed-closed'), ('P017-side-leaves', 'fixed-open')],
        produces=['pingcheng-P-v1:central:opening'],
        consumes=['pingcheng-P-v1:passage-W:threshold', 'pingcheng-P-v1:passage-E:threshold', 'pingcheng-P-v1:old-ramp:ground',
                  'wall-A-wall-06:cap-0:wall-end', 'wall-A-wall-05:cap-1:wall-end'],
        cards=['m-luoyang-pingcheng-gate'])
    s['LY-018'] = dict(site='S-GU', role='component+assembly', frames=['local:gu-G-v1'],
        zones=[B('local:gu-G-v1', [[-GAP_HALF, -0.3, -8.0], [GAP_HALF, 0.3, 8.0]], 'pier base support + threshold ground layer'),
               B('local:gu-G-v1', [[-GAP_HALF, 0.3, -5.0], [-12.0, 6.2, 5.0]], 'west wall-end adapter bay'),
               B('local:gu-G-v1', [[12.0, 0.3, -5.0], [GAP_HALF, 6.2, 5.0]], 'east wall-end adapter bay')],
        sourceObjects=[('gu-G-v1', r'.*', 'keep')], components=[('G018-base', 'fixed'), ('G018-threshold', 'fixed'), ('G018-wall-adapters', 'fixed')],
        produces=[], consumes=['wall-A-wall-00:cap-1:wall-end', 'wall-A-wall-01:cap-0:wall-end'], cards=['m-luoyang-gu-gate'])
    s['LY-019'] = dict(site='S-XIA', role='component+assembly', frames=['local:xia-B-v1'],
        zones=[B('local:xia-B-v1', [[-GAP_HALF, -0.3, -8.0], [GAP_HALF, 0.3, 8.0]], 'base support + ground seam layer'),
               B('local:xia-B-v1', [[-GAP_HALF, 0.3, -5.5], [-12.0, 6.2, 5.5]], 'west wall seam bay'),
               B('local:xia-B-v1', [[12.0, 0.3, -5.5], [GAP_HALF, 6.2, 5.5]], 'east wall seam bay')],
        sourceObjects=[('xia-B-v1', r'.*', 'keep')], components=[('X019-seams', 'fixed'), ('X019-base', 'fixed')],
        produces=[], consumes=['wall-A-wall-00:cap-0:wall-end', 'wall-A-wall-11:cap-1:wall-end'], cards=['m-luoyang-xia-gate'])
    s['LY-020'] = dict(site='S-WALLS', role='component+steward', frames=['world', 'local:earthwall'],
        zones=[{'frame': 'world', 'wallFootBands': True, 'halfWidth': 6.0, 'y': [-0.5, 1.0], 'label': 'foot/slope-foot band along every wall segment, ending at caps', 'class': 'write', 'basis': 'C-partition'},
               {'frame': 'world', 'cornerSeam': ['wall-A-wall-01', 1, 'wall-A-wall-02', 0], 'y': [-0.5, 6.4], 'label': 'NE corner seam (01/02); a gate slot, diagnosis only unless LY-010 allows a stub', 'class': 'write', 'basis': 'C-partition'}],
        cityNodes=['wall-A-wall-00', 'wall-A-wall-01', 'wall-A-wall-02', 'wall-A-wall-03', 'wall-A-wall-04', 'wall-A-wall-05', 'wall-A-wall-06', 'wall-A-wall-07', 'wall-A-wall-10', 'wall-A-wall-11'],
        sourceObjects=[('earthwall-family', r'.*', 'keep')], components=[('W020-corner-pieces', 'fixed'), ('W020-foot-pieces', 'fixed')],
        produces=[], consumes=['wall-A-wall-01:cap-1:wall-end', 'wall-A-wall-02:cap-0:wall-end'], cards=['m-luoyang-earthwall-family'])
    # ======================= 21-30 market and water
    s['LY-021'] = dict(site='S-MARKET', role='component', frames=[M], zones=market_step_zones(), components=[('M021-steps', 'fixed')],
        produces=[f'market-site:shop{i}-door{k}-step-foot:ground' for i, sh in enumerate(SHOPS) for k in range(len(sh[3]))],
        consumes=[f'market-site:shop{i}-door{k}:threshold' for i, sh in enumerate(SHOPS) for k in range(len(sh[3]))])
    s['LY-022'] = dict(site='S-MARKET', role='component', frames=[M],
        zones=[SUB(M, [[-22.7, 0.2, -4.2], [22.15, 0.26, 4.2]], ['LY-021', 'LY-023', 'LY-025', 'LY-028', '__routes__'], 'street ground patches on top of the slab, minus steps/stalls/well/routes')],
        components=[('M022-street-patches', 'fixed')], produces=['market-site:street-patch-ends:ground'],
        consumes=[f'market-site:shop{i}-door{k}-step-foot:ground' for i, sh in enumerate(SHOPS) for k in range(len(sh[3]))] +
                 [f'market-site:route-{r}:road-end' for r in ('public', 'east', 'rearN', 'rearS', 'exitPublic', 'exitN', 'exitS')])
    s['LY-023'] = dict(site='S-MARKET', role='component', frames=[M], zones=canopy_zones(), components=[('M023-stall-feet', 'removable')],
        produces=[f'market-site:canopy-{k}:ground' for k in CANOPIES], consumes=[])
    s['LY-024'] = dict(site='S-MARKET', role='component', frames=[M], zones=market_closure_zones(),
        components=[('M024-closing-panels', 'state-variant'), ('M024-side-closures', 'state-variant')],
        produces=['market-site:shop-type-closure:opening'], consumes=[f'market-site:shop{i}-door{k}:threshold' for i, sh in enumerate(SHOPS) for k in range(len(sh[3]))])
    s['LY-025'] = dict(site='S-MARKET', role='assembly-atom', frames=[M],
        zones=[B(M, [[-19.65, -0.8, 5.35], [-16.35, 0.25, 8.65]], 'well liner + collar + cut slab ring (below 0.25)'),
               B(M, [[-30.0, -0.05, -22.0], [30.0, 0.2, 22.0]], 'cut slab layer replacing sample_ground (whole market slab)'),
               B(M, [[-19.65, -0.8, 5.35], [-16.35, 0.2, 8.65]], 'well hole', cls='cut')],
        sourceObjects=[('well-A', r'.*', 'keep')], groundPieces=['gp:LY-025:C_market_ground_well_A', 'gp:well-A-LOD0:demonstration_apron_opening'],
        cuts=['cut:LY-025:market-well-A'], components=[('M025-well-A', 'fixed')],
        produces=['market-site:well-A:ground', 'cut:LY-025:market-well-A:cut'], consumes=[], cardsAdvisory=['m-well-family'])
    s['LY-026'] = dict(site='S-MARKET', role='component', frames=[M],
        zones=[B(M, [[-19.65, 0.25, 5.35], [-16.35, 3.4, 8.65]], 'well frame / windlass / guide parts above ground')],
        sourceObjects=[('well-A', r'(cross_head|drawing_container|container_|main_post|post_foot|eave_tie|axle|windlass|rope|guide)', 'modify')],
        components=[('M026-container', 'moving'), ('M026-guides', 'fixed')], produces=['market-site:well-A-windlass:mount'], consumes=['market-site:well-A:ground'])
    s['LY-027'] = dict(site='S-MARKET', role='assembly', frames=[M], zones=market_interior_zones(),
        components=[('M027-cargo-proxies', 'removable'), ('M027-load-states', 'state-variant')], produces=[], consumes=[])
    s['LY-028'] = dict(site='S-MARKET', role='component', frames=[M],
        zones=[B(M, [[-22.7, 0.2, -9.5], [-19.3, 0.26, -7.35]], 'west-end unloading / staging ground between canopies C00 and C01')],
        components=[('M028-staging-ground', 'fixed'), ('M028-staging-proxies', 'removable')],
        produces=['market-site:staging-W:ground'], consumes=['market-site:canopy-C00:ground', 'market-site:canopy-C01:ground', 'market-site:route-rearN:road-end'])
    s['LY-029'] = dict(site='S-MARKET', role='assembly', frames=[M, 'world'], zones=[],
        cityNodes=['market-main', 'market-N2'], sourceObjects=[('market-cluster', r'.*', 'keep'), ('N2-replacement', r'.*', 'keep'), ('frontage-v2.1', r'.*', 'keep')],
        placementProposal=M, components=[('M029-variant-switch', 'state-variant')],
        produces=[], consumes=['market-site:well-A:ground', 'market-site:staging-W:ground', 'market-site:street-patch-ends:ground', 'market-site:shop-type-closure:opening'])
    s['LY-030'] = dict(site='S-MARKET', role='assembly', frames=[M], zones=[],
        produces=['market-site:region-boundary-E:road-end'], consumes=['market-site:route-exitPublic:road-end'],
        cards=['m-luoyang-market-frontage', 'm-luoyang-market-modular-assembly', 'm-market-functional', 'm-well-family'])
    # ======================= 31-40 storage and armoury
    s['LY-031'] = dict(site='S-STORAGE', role='component', frames=[S],
        zones=[B(S, [[-17.0, 0.2, -2.6], [-7.0, 4.0, -1.52]], 'granary A front band (door frame / leaf / pivot / stop)')],
        components=[('S031-A-leaves', 'moving'), ('S031-A-frame', 'fixed')], produces=['granary-A:door:opening'], consumes=['granary-A:step-foot:ground'])
    s['LY-032'] = dict(site='S-STORAGE', role='component', frames=[S],
        zones=[B(S, [[5.5, 0.2, -2.6], [18.5, 4.6, -1.38]], 'granary B front band (door frame / leaf / pivot / stop)')],
        components=[('S032-B-leaves', 'moving'), ('S032-B-frame', 'fixed')], produces=['granary-B:door:opening'], consumes=['granary-B:step-foot:ground'])
    s['LY-033'] = dict(site='S-STORAGE', role='assembly', frames=[S], zones=[],
        sourceObjects=[('granary-A', r'.*', 'keep'), ('granary-B', r'.*', 'keep')], components=[],
        produces=[], consumes=['granary-A:door:opening', 'granary-B:door:opening'])
    s['LY-034'] = dict(site='S-STORAGE', role='assembly', frames=[S],
        zones=[B(S, [[-17.0, 0.2, -1.52], [5.5, 0.3, 2.5]], 'step-front strip to forecourt, A side (patches only at measured breaks)'),
               B(S, [[5.5, 0.2, -1.38], [18.5, 0.3, 2.5]], 'step-front strip to forecourt, B side (patches only at measured breaks)'),
               B(S, [[-5.0, 0.2, 2.5], [5.0, 0.3, 26.0]], 'receiving forecourt corridor to site north edge')],
        sourceObjects=[('granary-receiving', r'.*', 'keep')], components=[('S034-break-patches', 'fixed')],
        produces=['storage-site:forecourt-north:road-end'], consumes=['granary-A:step-foot:ground', 'granary-B:step-foot:ground'])
    s['LY-035'] = dict(site='S-STORAGE', role='component', frames=[S],
        zones=[B(S, [[-17.0, 0.2, 2.5], [-5.0, 0.3, 8.0]], 'west forecourt staging / turning variant (closable)')],
        components=[('S035-staging', 'removable')], produces=[], consumes=['storage-site:forecourt-north:road-end'])
    s['LY-036'] = dict(site='S-WUKU', role='component', frames=['local:wuku-B-v2.2'],
        zones=[SUB('local:wuku-B-v2.2', [[-9.5, -0.3, -9.5], [13.5, 0.3, 10.52]], ['LY-037'], 'outer arrival / support ground ring outside B footprint')],
        sourceObjects=[('wuku-B', r'.*', 'keep')], components=[('B036-outer-ground', 'fixed')],
        produces=['wuku-B:outer-arrival:ground'], consumes=[])
    s['LY-037'] = dict(site='S-WUKU', role='component', frames=['local:wuku-B-v2.2'],
        zones=[B('local:wuku-B-v2.2', [[-6.5, 0.0, -6.5], [10.5, 1.5, 7.52]], 'platform front / side shed / inspection table transitions inside B footprint')],
        sourceObjects=[], components=[('B037-transitions', 'fixed'), ('B037-leaf-state-150deg', 'state-variant')],
        produces=['wuku-B:forecourt-side:ground'], consumes=['wuku-B:outer-arrival:ground'])
    s['LY-038'] = dict(site='S-WUKU', role='assembly', frames=['local:wuku-A-v2'],
        zones=[B('local:wuku-A-v2', [[-10.0, -0.3, -8.5], [10.0, 0.6, 13.5]], 'A alternative: step base / support offset test (only if A is selected)', excl='wuku-A-or-B')],
        sourceObjects=[('wuku-A', r'.*', 'keep')], components=[], produces=[], consumes=['wuku-B:outer-arrival:ground'])
    s['LY-039'] = dict(site='S-NE-ROAD', role='assembly', frames=['world'],
        zones=[B('world', [[2283.714, -0.3, -3647.469], [2287.714, 0.6, -3484.0]], 'existing C_NE_APPROACH_LOCAL N-S leg + end-cap slopes', basis='LY-039 prep measurement of C_NE_APPROACH_LOCAL (+0.5 m)'),
               B('world', [[2287.714, -0.3, -3490.5], [2318.327, 0.6, -3484.0]], 'existing C_NE_APPROACH_LOCAL E leg + end cap', basis='LY-039 prep measurement (+0.5 m)')],
        sourceObjects=[('C_NE_APPROACH_LOCAL', r'.*', 'keep')], components=[],
        produces=[], consumes=['ne-approach:start:road-end', 'ne-approach:end-E:road-end', 'storage-site:forecourt-north:road-end', 'wuku-B:outer-arrival:ground', 'wuku-B:forecourt-side:ground'])
    s['LY-040'] = dict(site='S-STORAGE', role='assembly', frames=[S, 'world'], zones=[],
        cityNodes=['storage-main'], sourceObjects=[('granary-city', r'.*', 'keep')],
        produces=['storage-site:region-boundary:road-end'], consumes=['storage-site:forecourt-north:road-end'],
        cards=['m-storage-functional', 'm-luoyang-wuku'])
    # ======================= 41-50 demonstration courtyard (candidate C02-010)
    s['LY-041'] = dict(site='S-COURT', role='component', frames=[C],
        zones=[SUB(C, [[-9.0, -0.3, -12.0], [9.0, 0.25, 12.0]], ['LY-044', 'LY-045', 'LY-046', 'LY-047', 'LY-049'], 'base / foot / ground diff layer minus facility footprints')],
        components=[('R041-foot-patches', 'fixed')], produces=[], consumes=['C02-010:ground-base'])
    s['LY-042'] = dict(site='S-COURT', role='assembly', frames=[C],
        zones=[B(C, [[-5.0, 0.25, -4.6], [1.1, 2.6, -3.4]], 'main house front door band (west of latrine zone)'),
               B(C, [[-4.0, 0.25, -3.4], [-3.0, 2.6, 2.9]], 'west wing east-face door band')],
        sourceObjects=[('inner-door-components', r'.*', 'keep')], components=[('R042-door-leaves', 'moving'), ('R042-old-leaves-hidden', 'state-variant')],
        produces=['C02-010:inner-door-axes:mount'], consumes=['C02-010:ground-base'])
    s['LY-043'] = dict(site='S-COURT', role='component', frames=[C],
        zones=[B(C, [[-9.0, 0.25, -12.0], [-8.0, 3.3, -11.0]], 'NW corner'), B(C, [[8.0, 0.25, -12.0], [9.0, 3.3, -11.0]], 'NE corner'),
               B(C, [[-9.0, 0.25, 11.0], [-8.0, 3.3, 12.0]], 'SW corner'), B(C, [[8.0, 0.25, 11.0], [9.0, 3.3, 12.0]], 'SE corner')],
        sourceObjects=[('wall-house-court', r'.*', 'keep')], components=[('R043-junctions', 'fixed')], produces=[], consumes=[])
    s['LY-044'] = dict(site='S-COURT', role='assembly', frames=[C], zones=[B(C, COURT['kitchen'], 'kitchen: stove + preparation table + turning space (SW yard)')],
        sourceObjects=[('cooking-stove', r'.*', 'keep'), ('residential-preparation', r'.*', 'keep')], components=[('R044-stove', 'fixed'), ('R044-prep-table', 'fixed')],
        produces=[], consumes=['C02-010:ground-base'])
    s['LY-045'] = dict(site='S-COURT', role='assembly', frames=[C],
        zones=[B(C, COURT['latrine'], 'latrine / pen group with steps and pit (E yard); 6.75 x 7.56 m footprint fits only in this orientation'),
               B(C, [[1.1, -1.6, -4.0], [8.0, 0.25, 3.6]], 'latrine pit opening in city ground (ground-retained)', cls='cut')],
        sourceObjects=[('service-court', r'.*', 'keep')], cuts=['cut:LY-045:C02-010-latrine'], components=[('R045-service-A', 'fixed')],
        produces=['cut:LY-045:C02-010-latrine:cut'], consumes=['C02-010:ground-base'])
    s['LY-046'] = dict(site='S-COURT', role='component', frames=[C], zones=[B(C, COURT['drip'], 'drip / slope / shallow channel trial strip')],
        components=[('R046-drip-strip', 'removable')], produces=['C02-010:drip-outlet:drain'], consumes=['C02-010:ground-base'])
    s['LY-047'] = dict(site='S-COURT', role='assembly', frames=[C], zones=[B(C, COURT['storage'], 'storage / shed variant (NE back strip)')],
        sourceObjects=[('household-service', r'.*', 'keep')], components=[('R047-storage-module', 'removable')], produces=[], consumes=['C02-010:ground-base'])
    s['LY-048'] = dict(site='S-COURT', role='component', frames=[C],
        zones=[B(C, [[-9.0, 0.25, -11.0], [-8.0, 3.3, 11.0]], 'west wall ring segment'), B(C, [[8.0, 0.25, -11.0], [9.0, 3.3, 11.0]], 'east wall ring segment'),
               B(C, [[-8.0, 0.25, -12.0], [8.0, 3.3, -11.0]], 'north wall ring segment'),
               B(C, [[-8.0, 0.25, 11.0], [-5.0, 3.3, 12.0]], 'south ring W of gate'), B(C, [[-1.0, 0.25, 11.0], [8.0, 3.3, 12.0]], 'south ring E of gate')],
        components=[('R048-side-openings', 'state-variant'), ('R048-low-wall-closures', 'fixed')], produces=['C02-010:service-opening:opening'], consumes=[])
    s['LY-049'] = dict(site='S-COURT', role='component', frames=[C], zones=[B(C, COURT['gate'], 'gate passage to lot boundary z=12 (local)')],
        components=[('R049-gate-transition', 'fixed')], produces=['C02-010:gate-boundary:road-end'], consumes=['C02-010:ground-base', 'C02-010:service-opening:opening'])
    s['LY-050'] = dict(site='S-COURT', role='assembly', frames=[C, 'world'], zones=[], cityNodes=['C02-010'],
        produces=[], consumes=['C02-010:gate-boundary:road-end', 'C02-010:drip-outlet:drain', 'C02-010:service-opening:opening'],
        cards=['m-luoyang-inner-door-components', 'm-luoyang-wall-house-court', 'm-luoyang-cooking-stove', 'm-luoyang-residential-preparation',
               'm-luoyang-service-court', 'm-luoyang-household-service'])
    # ======================= 51-60 workshops
    for sid, fr, nm in (('LY-051', 'stable', 'tethering / partition C parts (above platform)'),):
        pass
    s['LY-051'] = dict(site='S-WORK', role='component', frames=['local:stable-A', 'local:stable-B'],
        zones=[B('local:stable-A', [[-4.5, 0.05, -2.4], [4.5, 2.7, 2.4]], 'stable A tether / partition parts above platform'),
               B('local:stable-B', [[-6.3, 0.05, -2.7], [6.3, 2.7, 2.7]], 'stable B tether / partition parts above platform')],
        components=[('W051-tethers', 'removable'), ('W051-partitions', 'removable')], produces=['stable:partition-footprint:mount'], consumes=[])
    s['LY-052'] = dict(site='S-WORK', role='component', frames=['local:stable-A', 'local:stable-B'],
        zones=[B('local:stable-A', [[-4.5, -0.3, -2.4], [4.5, 0.05, 2.4]], 'stable A floor layer'), B('local:stable-A', [[-4.5, -0.3, 2.4], [4.5, 0.3, 6.4]], 'stable A front approach'),
               B('local:stable-B', [[-6.3, -0.3, -2.7], [6.3, 0.05, 2.7]], 'stable B floor layer'), B('local:stable-B', [[-6.3, -0.3, 2.7], [6.3, 0.3, 6.7]], 'stable B front approach')],
        sourceObjects=[('stable-A', r'.*', 'keep'), ('stable-B', r'.*', 'keep')], groundPieces=['gp:stable-A:A_earth_platform', 'gp:stable-B:B_earth_platform'],
        components=[('W052-floor-diff', 'fixed')], produces=['stable:entrance:ground', 'stable:drain-outlet:drain'], consumes=['stable:partition-footprint:mount'])
    s['LY-053'] = dict(site='S-WORK', role='component', frames=['local:kiln-A', 'local:kiln-B'],
        zones=[B('local:kiln-A', [[-8.0, -1.6, -6.0], [8.0, 0.0, 6.0]], 'kiln A pit / base / cut terrain contract (below grade)', excl='kiln-A-or-B'),
               B('local:kiln-B', [[-8.0, -1.6, -6.0], [8.0, 0.0, 6.0]], 'kiln B pit / base / cut terrain contract (below grade)', excl='kiln-A-or-B'),
               B('local:kiln-A', [[-2.0, -1.1, 2.0], [2.0, 0.0, 5.4]], 'kiln A operation pit opening', cls='cut', excl='kiln-A-or-B'),
               B('local:kiln-B', [[-2.0, -1.1, 2.0], [2.0, 0.0, 5.4]], 'kiln B operation pit opening', cls='cut', excl='kiln-A-or-B')],
        sourceObjects=[('kiln-A', r'.*', 'keep'), ('kiln-B', r'.*', 'keep')], groundPieces=['gp:kiln-A:A_presentation_ground', 'gp:kiln-B:B_presentation_ground'],
        cuts=['cut:LY-053:kiln-pit'], components=[('W053-pit-walls', 'fixed')], produces=['kiln:pit-rim:cut', 'cut:LY-053:kiln-pit:cut'], consumes=[])
    s['LY-054'] = dict(site='S-WORK', role='component', frames=['local:kiln-A', 'local:kiln-B'],
        zones=[B('local:kiln-A', [[-8.0, 0.0, 6.0], [8.0, 0.4, 9.5]], 'kiln A front operation ground + staging proxies', excl='kiln-A-or-B'),
               B('local:kiln-B', [[-8.0, 0.0, 6.0], [8.0, 0.4, 9.5]], 'kiln B front operation ground + staging proxies', excl='kiln-A-or-B')],
        components=[('W054-front-ground', 'fixed'), ('W054-staging-proxies', 'removable')], produces=['kiln:front-work:ground', 'kiln:front-drain:drain'], consumes=['kiln:pit-rim:cut'])
    s['LY-055'] = dict(site='S-WORK', role='assembly', frames=['local:hand-mill'],
        zones=[B('local:hand-mill', [[-1.4, -0.12, -1.4], [1.4, 0.0, 1.4]], 'support surface replacing presentation ground'),
               B('local:hand-mill', [[-2.4, -0.12, -2.4], [2.4, 0.0, -1.4]], 'operator standing ground N'), B('local:hand-mill', [[-2.4, -0.12, 1.4], [2.4, 0.0, 2.4]], 'operator standing ground S')],
        sourceObjects=[('hand-mill-A', r'.*', 'keep'), ('hand-mill-B', r'.*', 'keep')], groundPieces=['gp:hand-mill-A:A_presentation_ground', 'gp:hand-mill-B:B_presentation_ground'],
        components=[('W055-upper-stone', 'moving-candidate (static in GLB)')], produces=['hand-mill:stand-base:ground'], consumes=[])
    s['LY-056'] = dict(site='S-WORK', role='assembly', frames=['local:foot-pestle'],
        zones=[B('local:foot-pestle', [[-1.6, -0.2, -2.6], [1.6, 0.0, 3.4]], 'selected work ground under pestle + tread + turning')],
        sourceObjects=[('foot-pestle', r'.*', 'keep')], components=[('W056-pestle-beam', 'moving')], produces=['foot-pestle:tread-base:ground', 'foot-pestle:pivot:mount'], consumes=[])
    s['LY-057'] = dict(site='S-WORK', role='component', frames=['local:workshed'],
        zones=[B('local:workshed', [[-4.05, 2.8, -4.45], [4.05, 4.2, 0.45]], 'shed roof tile seating / row joints / bearers')],
        sourceObjects=[('workshed', r'.*', 'modify')], components=[('W057-roof-revision', 'fixed')], produces=['workshed:shed-floor:floor'], consumes=[])
    s['LY-058'] = dict(site='S-WORK', role='assembly', frames=['local:work-site'],
        zones=[B('local:work-site', [[-8.0, 0.2, -11.0], [8.0, 0.3, 11.0]], 'interior circulation ground of the selected work site (C frame defined by LY-058)')],
        sourceObjects=[('workyard', r'.*', 'keep')], components=[('W058-flow-ground', 'fixed'), ('W058-staging-proxies', 'removable')],
        produces=['work-site:interior-edge:ground'], consumes=['hand-mill:stand-base:ground', 'foot-pestle:tread-base:ground', 'workshed:shed-floor:floor'])
    s['LY-059'] = dict(site='S-WORK', role='component', frames=['local:work-site'],
        zones=[B('local:work-site', [[-9.0, 0.0, -12.0], [9.0, 3.5, -11.0]], 'perimeter N'), B('local:work-site', [[-9.0, 0.0, 11.0], [9.0, 3.5, 12.0]], 'perimeter S'),
               B('local:work-site', [[-9.0, 0.0, -11.0], [-8.0, 3.5, 11.0]], 'perimeter W'), B('local:work-site', [[8.0, 0.0, -11.0], [9.0, 3.5, 11.0]], 'perimeter E')],
        components=[('W059-gaps-closures', 'fixed'), ('W059-service-gate', 'state-variant')], produces=['work-site:service-gate:opening'],
        consumes=['work-site:interior-edge:ground', 'kiln:front-work:ground'])
    s['LY-060'] = dict(site='S-WORK', role='assembly', frames=['local:work-site'], zones=[], produces=[], consumes=['work-site:service-gate:opening', 'stable:entrance:ground'],
        cards=['m-luoyang-stable', 'm-luoyang-tile-kiln', 'm-luoyang-hand-mill', 'm-luoyang-foot-pestle', 'm-luoyang-workyard-shed'])
    # ======================= 61-70 palace courts and gallery
    AC = 'local:admission-court'
    s['LY-061'] = dict(site='S-PALACE', role='component', frames=[AC],
        zones=[B(AC, [[-36.0, -0.3, -22.0], [36.0, 6.0, -20.0]], 'enclosure N side'),
               B(AC, [[-36.0, -0.3, 67.0], [-3.0, 6.0, 69.0]], 'enclosure S side W'), B(AC, [[3.0, -0.3, 67.0], [36.0, 6.0, 69.0]], 'enclosure S side E'),
               B(AC, [[-36.0, -0.3, -20.0], [-34.0, 6.0, 10.0]], 'enclosure W side N'), B(AC, [[-36.0, -0.3, 16.0], [-34.0, 6.0, 67.0]], 'enclosure W side S'),
               B(AC, [[34.0, -0.3, -20.0], [36.0, 6.0, 10.0]], 'enclosure E side N'), B(AC, [[34.0, -0.3, 16.0], [36.0, 6.0, 67.0]], 'enclosure E side S')],
        sourceObjects=[('admission-court', r'.*', 'keep')], groundPieces=['gp:admission-court:guard__guard-slice-ground-earth'],
        components=[('P061-enclosure', 'fixed'), ('P061-corners-footings', 'fixed')], produces=['admission-court:enclosure:wall-end'], consumes=[])
    s['LY-062'] = dict(site='S-PALACE', role='component', frames=[AC],
        zones=[B(AC, [[-36.0, -0.3, 10.0], [-34.0, 6.0, 16.0]], 'west side opening'), B(AC, [[34.0, -0.3, 10.0], [36.0, 6.0, 16.0]], 'east side opening'),
               B(AC, [[-3.0, -0.3, 67.0], [3.0, 6.0, 69.0]], 'rear work opening')],
        sourceObjects=[('palace-guard', r'.*', 'keep')], components=[('P062-closures', 'state-variant'), ('P062-main-leaves-state', 'state-variant')],
        produces=['admission-court:side-opening-W:opening', 'admission-court:side-opening-E:opening'], consumes=['admission-court:enclosure:wall-end'])
    s['LY-063'] = dict(site='S-PALACE', role='component', frames=[AC],
        zones=[{'frame': AC, 'fromNodes': ['library/models/m-luoyang-palace-admission-court/files/palace-admission-court-closed-LOD0.glb', r'^(west|east)_gallery__'],
                'endBand': 3.0, 'y': [-0.2, 6.4], 'label': 'side gallery end bays (3 m beyond each gallery end along its long axis)', 'class': 'write', 'basis': 'measured gallery node AABB + C 3 m'}],
        sourceObjects=[('palace-sidehall', r'.*', 'keep')], components=[('P063-end-turns', 'fixed')], produces=['sidehall:ends:floor'], consumes=['admission-court:enclosure:wall-end'])
    s['LY-064'] = dict(site='S-PALACE', role='component', frames=['local:paired-que'],
        zones=[B('local:paired-que', [[-20.5, -0.3, -12.0], [20.5, 0.3, 12.0]], 'forecourt ground layer around both que bases')],
        sourceObjects=[('paired-que', r'.*', 'keep')], components=[('P064-footings-ground', 'fixed')], produces=['paired-que:forecourt-edge:ground'], consumes=[])
    s['LY-065'] = dict(site='S-PALACE', role='component', frames=['local:deyang'],
        zones=[B('local:deyang', [[-22.3, -0.3, -13.9], [22.3, 1.6, 19.0]], 'side/back platform edge + maintenance points (must not touch main stair / column grid; LY-065 lists exact pieces)')],
        sourceObjects=[('deyang-A', r'.*', 'keep'), ('deyang-B', r'.*', 'keep')], components=[('P065-maintenance', 'fixed')], produces=['deyang:maintenance-edge:floor'], consumes=[])
    s['LY-066'] = dict(site='S-PALACE', role='assembly', frames=['local:yutang'],
        zones=[B('local:yutang', [[-19.5, -0.3, -33.5], [19.5, 0.3, 34.9]], 'grounding / outer port band of the yutang group')],
        sourceObjects=[('yutang-A', r'.*', 'keep'), ('yutang-B', r'.*', 'keep')], components=[], produces=['yutang:outer-port:ground'], consumes=[])
    s['LY-067'] = dict(site='S-PALACE', role='component', frames=['local:gallery-A'],
        zones=[B('local:gallery-A', [[-6.45, -0.6, -3.824], [6.45, 0.0, 3.824]], 'post foot support / foundation interfaces (below grade)')],
        sourceObjects=[('gallery-A', r'.*', 'keep'), ('gallery-access', r'.*', 'keep')], components=[('P067-footings', 'fixed')], produces=['gallery-A:feet:ground'], consumes=[])
    s['LY-068'] = dict(site='S-PALACE', role='component', frames=['local:gallery-B'],
        zones=[B('local:gallery-B', [[4.95, -0.2, -4.2], [12.0, 8.1, 4.2]], 'B stair / platform bay (+x end)')],
        sourceObjects=[('gallery-B', r'.*', 'keep')], components=[('P068-stair-platform', 'fixed'), ('P068-collision', 'fixed')], produces=['gallery-B:landing:floor'], consumes=[])
    s['LY-069'] = dict(site='S-PALACE', role='assembly', frames=['local:palace-composite'],
        zones=[B('local:palace-composite', [[-6.0, -0.3, -6.0], [6.0, 9.0, 6.0]], 'one gallery-end / gate-gallery junction (frame origin = chosen junction)')],
        components=[('P069-junction', 'fixed')], produces=['gallery-end:junction:floor'],
        consumes=['gallery-A:feet:ground', 'gallery-B:landing:floor', 'sidehall:ends:floor', 'admission-court:side-opening-W:opening'])
    s['LY-070'] = dict(site='S-PALACE', role='assembly', frames=['local:palace-composite'], zones=[],
        produces=[], consumes=['gallery-end:junction:floor', 'paired-que:forecourt-edge:ground', 'deyang:maintenance-edge:floor', 'yutang:outer-port:ground', 'admission-court:side-opening-E:opening'],
        cards=['m-luoyang-palace-admission-court', 'm-luoyang-palace-guard', 'm-luoyang-palace-sidehall', 'm-luoyang-palace-paired-que', 'm-luoyang-deyang-hall',
               'm-luoyang-yutang-halls', 'm-luoyang-palace-gallery', 'm-luoyang-gallery-access'])
    # ======================= 71-80 ritual south and north suburb
    BY = 'local:biyong'
    s['LY-071'] = dict(site='S-BIYONG', role='assembly', frames=[BY],
        zones=[B(BY, [[-20.4, -1.2, -20.4], [20.4, 0.0, 20.4]], 'hall platform base / enclosure interface layer (below hall grade)')],
        sourceObjects=[('biyong-A', r'.*', 'keep'), ('biyong-enclosure-L', r'.*', 'keep')], components=[], produces=['biyong:hall-enclosure:ground'], consumes=[])
    s['LY-072'] = dict(site='S-BIYONG', role='component', frames=[BY],
        zones=[B(BY, [[20.4, -1.5, -2.5], [30.0, 1.5, 2.5]], 'one crossing corridor on +x (C; re-validate against LY-071 transform)')],
        components=[('B072-crossing', 'fixed')], produces=['biyong:crossing-ends:ground'], consumes=['biyong:hall-enclosure:ground'])
    s['LY-073'] = dict(site='S-BIYONG', role='component', frames=[BY],
        zones=[B(BY, [[30.0, -1.5, -6.0], [40.0, 0.5, 6.0]], 'outer bank + arrival ground at crossing end'),
               B(BY, [[20.4, -1.5, -6.0], [30.0, 0.0, -2.5]], 'bank edge S of crossing'), B(BY, [[20.4, -1.5, 2.5], [30.0, 0.0, 6.0]], 'bank edge N of crossing')],
        components=[('B073-bank', 'fixed'), ('B073-water-material', 'removable')], produces=['biyong:bank-outlet:drain'], consumes=['biyong:crossing-ends:ground', 'biyong:hall-enclosure:ground'],
        cards=['m-luoyang-biyong'])
    s['LY-074'] = dict(site='S-MINGTANG', role='component', frames=['local:mingtang'],
        zones=[SUB('local:mingtang', [[-24.0, -0.3, -24.0], [24.0, 0.4, 24.0]], ['__mingtang_B_core__'], 'four-side arrival ground outside the selected hall footprint')],
        sourceObjects=[('mingtang-A', r'.*', 'keep'), ('mingtang-B', r'.*', 'keep')], components=[('T074-arrival', 'fixed')],
        produces=['mingtang:side-N:ground', 'mingtang:side-E:ground', 'mingtang:side-S:ground', 'mingtang:side-W:ground'], consumes=[])
    s['LY-075'] = dict(site='S-MINGTANG', role='assembly', frames=['local:mingtang'],
        zones=[B('local:mingtang', [[-16.64, 0.4, -16.64], [16.64, 10.9, 16.64]], 'interior gap diffs only (no new doors / no column removal)')],
        components=[('T075-gap-diffs', 'fixed')], produces=[], consumes=['mingtang:side-N:ground', 'mingtang:side-E:ground', 'mingtang:side-S:ground', 'mingtang:side-W:ground'],
        cards=['m-luoyang-mingtang'])
    s['LY-076'] = dict(site='S-LINGTAI', role='component+assembly', frames=['local:lingtai-A'],
        zones=[B('local:lingtai-A', [[-34.0, -0.3, -34.0], [34.0, 6.0, 34.0]], 'lingtai edge / detour fixes (excluding the five repaired steps, enforced by LY-076 list)')],
        sourceObjects=[('lingtai-A', r'.*', 'modify')], researchModels=['research-lingtai'], components=[('T076-edge-fixes', 'fixed')], produces=['lingtai:edge:ground'], consumes=[],
        cards=['m-luoyang-lingtai'])
    s['LY-077'] = dict(site='S-TAIXUE', role='component', frames=['local:taixue-A'],
        zones=[B('local:taixue-A', [[-18.8, -0.3, 4.85], [18.8, 0.5, 12.0]], 'A outer entry ground / step front / lateral merge (local +z)')],
        sourceObjects=[('taixue-A', r'.*', 'keep')], researchModels=['research-taixue-A', 'research-taixue-B'], components=[('T077-entry-ground', 'fixed')],
        produces=['taixue-A:outer-entry:ground'], consumes=[], cards=['m-luoyang-taixue-a'])
    s['LY-078'] = dict(site='S-TAIXUE', role='assembly', frames=['local:stoneclassic'],
        zones=[B('local:stoneclassic', [[-20.0, -0.3, 18.0], [20.0, 0.5, 24.0]], 'independent street-side port band + ground boundary (south)')],
        sourceObjects=[('stoneclassic', r'.*', 'keep')], components=[('T078-port-ground', 'fixed'), ('T078-stele-slots-empty', 'state-variant')],
        produces=['stoneclassic:south-mouth:road-end'], consumes=['taixue-A:outer-entry:ground'], cards=['m-luoyang-stoneclassic-access-court'])
    s['LY-079'] = dict(site='S-SOUTH-ALTAR', role='assembly', frames=['local:south-altar'],
        zones=[B('local:south-altar', [[-40.0, -0.4, -40.0], [40.0, 0.3, 40.0]], 'outer arrival ground at the eight stairs (must not reshape the platforms)')],
        sourceObjects=[('south-altar-A', r'.*', 'keep'), ('south-altar-B', r'.*', 'keep')], groundPieces=['gp:south-altar-A:A_presentation_ground', 'gp:south-altar-B:B_presentation_ground'],
        components=[('T079-arrival', 'fixed')], produces=['south-altar:stairs:ground'], consumes=[], cards=['m-luoyang-southern-altar'])
    s['LY-080'] = dict(site='S-NORTH-ALTAR', role='assembly', frames=['local:north-altar'],
        zones=[B('local:north-altar', [[-17.0, -0.3, -17.0], [17.0, 0.3, 17.0]], 'north-suburb independent arrival ground at four stairs (must not reshape the platform)')],
        sourceObjects=[('north-altar', r'.*', 'keep')], components=[('T080-arrival', 'fixed')], produces=['north-altar:stairs:ground'], consumes=[], cards=['m-luoyang-northern-altar'])
    # ======================= 81-90 roads, terrain, water
    s['LY-081'] = dict(site='S-CITYGROUND', role='data', frames=['world'], zones=[], dataObjects=['data:LY-081:ground-reachability-network'],
        produces=[], consumes=['FROZEN:*'])
    s['LY-082'] = dict(site='S-COURT-LANE', role='component', frames=['world'],
        zones=[B('world', [[526.0, -0.3, -806.45], [530.0, 0.6, -796.45]], 'short lane link from C02-010 lot boundary (C reservation 10 m; 081 sets the real target)')],
        components=[('L082-lane-link', 'removable')], produces=[], consumes=['C02-010:gate-boundary:road-end'])
    s['LY-083'] = dict(site='S-MARKET-STREET', role='component', frames=['world'],
        zones=[B('world', [[244.286, -0.3, -1981.184], [274.286, 0.6, -1937.184]], 'outer street link east of the market boundary (C reservation 30 m; 081 sets the real target)')],
        components=[('L083-street-link', 'removable')], produces=[], consumes=['market-site:region-boundary-E:road-end', 'market-site:route-exitPublic:road-end'])
    s['LY-084'] = dict(site='S-CITYGROUND', role='data', frames=['world'], zones=[], dataObjects=['data:LY-084:ne-route-candidates'],
        produces=[], consumes=['storage-site:region-boundary:road-end', 'ne-approach:end-E:road-end'])
    s['LY-085'] = dict(site='S-KAIYANG', role='component', frames=[K, P],
        zones=[B(K, [[-12.4, -0.5, 7.0], [12.4, 1.0, 40.0]], 'Kaiyang outer approach (city south, local +z) from strip edge'),
               B(P, [[-12.8, -0.5, 14.0], [12.8, 1.0, 40.0]], 'Pingcheng outer approach (city south, local +z) from connection ground')],
        components=[('L085-kaiyang-link', 'removable'), ('L085-pingcheng-link', 'removable')], produces=[],
        consumes=['kaiyang-K-v1:outer-apron-edge:road-end', 'pingcheng-P-v1:outer-edge-W:road-end', 'pingcheng-P-v1:outer-edge-E:road-end'])
    s['LY-086'] = dict(site='S-WATERWAY', role='assembly', frames=['local:waterway'],
        zones=[B('local:waterway', [[-6.0, -1.0, -4.0], [6.0, 6.2, 4.0]], 'local wall research block with opening, covers and atomic install'),
               B('local:waterway', [[-3.3, -0.18, -0.76], [3.3, 2.01, 1.86]], 'wall opening for the three waterway parts', cls='cut')],
        sourceObjects=[('waterway', r'.*', 'keep')], cuts=['cut:LY-086:waterway-wall-block'], components=[('H086-wall-block', 'fixed'), ('H086-covers', 'removable')],
        produces=['waterway:ends:drain', 'cut:LY-086:waterway-wall-block:cut'], consumes=[], cards=['m-luoyang-palace-waterway-interface'])
    s['LY-087'] = dict(site='S-CITYGROUND', role='data+assembly', frames=['world'], zones=[], dataObjects=['data:LY-087:drain-port-ledger'],
        produces=[], consumes=['C02-010:drip-outlet:drain', 'stable:drain-outlet:drain', 'kiln:front-drain:drain', 'biyong:bank-outlet:drain'])
    s['LY-088'] = dict(site='S-CITYGROUND', role='data', frames=['world'], zones=[], dataObjects=['data:LY-088:water-period-layer'], produces=[], consumes=[])
    s['LY-089'] = dict(site='S-CITYGROUND', role='component', frames=['world'], zones=[], claimProtocol=True,
        components=[('G089-support-patches', 'fixed')], produces=[], consumes=['FROZEN:*'])
    s['LY-090'] = dict(site='S-CITYGROUND', role='assembly', frames=['world'], zones=[],
        cityNodes=['ground-network-ground-stitched', 'ground-retained', 'ground-south', 'ground-D08'],
        groundPieces=['gp:market-cluster:sample_ground', 'gp:granary-city:original_city_ground_preserved'],
        produces=[], consumes=['cut:LY-025:market-well-A:cut', 'cut:LY-045:C02-010-latrine:cut', 'cut:LY-053:kiln-pit:cut', 'cut:LY-086:waterway-wall-block:cut'])
    return s

# ---------------------------------------------------------------- source object catalog
# key -> how to enumerate "source nodes" (generator objects or GLB nodes) and which files they live in
SOURCE_CATALOG = {
    'kaiyang-K-v1': {'kind': 'generator-objects', 'objects': 'qa/source-objects/kaiyang-K-v1.objects.json', 'card': 'm-luoyang-kaiyang-gate', 'frame': K},
    'kaiyang-K-v1-trial': {'kind': 'listed', 'objects': ['kaiyang-K-static_earth:end-wedge-W', 'kaiyang-K-static_earth:end-wedge-E'], 'evidence': 'qa/kaiyang-hidden-trial.objects.json (earth x -16..16 vs public GLB piers -12.4..12.4)', 'card': 'm-luoyang-kaiyang-gate'},
    'pingcheng-P-v1-trial': {'kind': 'listed', 'objects': ['pingcheng-P-static_earth:end-wedge-W', 'pingcheng-P-static_earth:end-wedge-E', 'pingcheng-old-ramp (not located in any public GLB/blend read by LY-006)'], 'evidence': 'qa/pingcheng-hidden-trial.objects.json', 'card': 'm-luoyang-pingcheng-gate'},
    'pingcheng-P-v1': {'kind': 'generator-objects', 'objects': 'qa/source-objects/pingcheng-P-v1.objects.json', 'card': 'm-luoyang-pingcheng-gate', 'frame': P},
    'gu-G-v1': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-gu-gate/files/'], 'card': 'm-luoyang-gu-gate'},
    'xia-B-v1': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-xia-gate/files/'], 'card': 'm-luoyang-xia-gate'},
    'earthwall-family': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-earthwall-family/files/'], 'card': 'm-luoyang-earthwall-family'},
    'well-A': {'kind': 'glb-nodes', 'glbs': [r'model-library/well-study/assets/well-A-'], 'card': 'm-well-family'},
    'market-cluster': {'kind': 'glb-nodes', 'glbs': [r'cities/luoyang/assets/market/market-cluster\.glb', r'cities/luoyang/assets/market/flowB-routes\.glb'], 'card': 'm-market-functional',
                       'except': [r'^sample_ground$']},
    'N2-replacement': {'kind': 'glb-nodes', 'glbs': [r'cities/luoyang/assets/market/N2-replacement\.glb'], 'card': 'm-market-functional'},
    'frontage-v2.1': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-market-frontage/files/', r'library/models/m-luoyang-market-modular-assembly/files/'], 'card': 'm-luoyang-market-frontage'},
    'granary-A': {'kind': 'glb-nodes', 'glbs': [r'model-library/updates/m-storage-functional/files/granary-A-'], 'card': 'm-storage-functional'},
    'granary-B': {'kind': 'glb-nodes', 'glbs': [r'model-library/updates/m-storage-functional/files/granary-B-'], 'card': 'm-storage-functional'},
    'granary-receiving': {'kind': 'glb-nodes', 'glbs': [r'model-library/updates/m-storage-functional/files/granary-(receiving|group)-'], 'card': 'm-storage-functional'},
    'granary-city': {'kind': 'glb-nodes', 'glbs': [r'cities/luoyang/progress-assets/granary-city-v1/'], 'card': 'm-storage-functional', 'except': [r'^original_city_ground_preserved$']},
    'wuku-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-wuku/files/wuku-A-'], 'card': 'm-luoyang-wuku'},
    'wuku-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-wuku/files/wuku-B-'], 'card': 'm-luoyang-wuku'},
    'C_NE_APPROACH_LOCAL': {'kind': 'external', 'note': 'object in origin/luoyang-content modeling-lab/review-batches/2026-11-04-city-visible adapter chunk northeast_C_access (not in docs); LY-039 prep measured it', 'card': None},
    'inner-door-components': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-inner-door-components/files/'], 'card': 'm-luoyang-inner-door-components'},
    'wall-house-court': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-wall-house-court/files/'], 'card': 'm-luoyang-wall-house-court'},
    'cooking-stove': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-cooking-stove/files/'], 'card': 'm-luoyang-cooking-stove'},
    'residential-preparation': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-residential-preparation/files/'], 'card': 'm-luoyang-residential-preparation'},
    'service-court': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-service-court/files/'], 'card': 'm-luoyang-service-court'},
    'household-service': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-household-service/files/'], 'card': 'm-luoyang-household-service'},
    'stable-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-stable/files/A\.glb'], 'card': 'm-luoyang-stable', 'except': [r'^A_earth_platform$']},
    'stable-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-stable/files/B\.glb'], 'card': 'm-luoyang-stable', 'except': [r'^B_earth_platform$']},
    'kiln-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-tile-kiln/files/kiln-A'], 'card': 'm-luoyang-tile-kiln', 'except': [r'^A_presentation_ground$']},
    'kiln-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-tile-kiln/files/kiln-B'], 'card': 'm-luoyang-tile-kiln', 'except': [r'^B_presentation_ground$']},
    'hand-mill-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-hand-mill/files/hand-mill-A'], 'card': 'm-luoyang-hand-mill', 'except': [r'^A_presentation_ground$']},
    'hand-mill-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-hand-mill/files/hand-mill-B'], 'card': 'm-luoyang-hand-mill', 'except': [r'^B_presentation_ground$']},
    'foot-pestle': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-foot-pestle/files/'], 'card': 'm-luoyang-foot-pestle'},
    'workshed': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-workyard-shed/files/workshed-'], 'card': 'm-luoyang-workyard-shed'},
    'workyard': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-workyard-shed/files/workyard-'], 'card': 'm-luoyang-workyard-shed'},
    'admission-court': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-admission-court/files/', r'cities/luoyang/progress-assets/palace-admission-court/'], 'card': 'm-luoyang-palace-admission-court',
                        'except': [r'^guard__guard-slice-ground-earth$']},
    'palace-guard': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-guard/files/'], 'card': 'm-luoyang-palace-guard'},
    'palace-sidehall': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-sidehall/files/'], 'card': 'm-luoyang-palace-sidehall'},
    'paired-que': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-paired-que/files/'], 'card': 'm-luoyang-palace-paired-que'},
    'deyang-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-deyang-hall/files/deyang-A'], 'card': 'm-luoyang-deyang-hall'},
    'deyang-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-deyang-hall/files/deyang-B'], 'card': 'm-luoyang-deyang-hall'},
    'yutang-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-yutang-halls/files/yutang-A'], 'card': 'm-luoyang-yutang-halls'},
    'yutang-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-yutang-halls/files/yutang-B'], 'card': 'm-luoyang-yutang-halls'},
    'gallery-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-gallery/files/gallery-A'], 'card': 'm-luoyang-palace-gallery'},
    'gallery-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-gallery/files/gallery-B'], 'card': 'm-luoyang-palace-gallery'},
    'gallery-access': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-gallery-access/files/'], 'card': 'm-luoyang-gallery-access'},
    'biyong-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-biyong/files/biyong-A'], 'card': 'm-luoyang-biyong'},
    'biyong-enclosure-L': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-biyong/files/enclosure-L'], 'card': 'm-luoyang-biyong'},
    'mingtang-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-mingtang/files/mingtang-A'], 'card': 'm-luoyang-mingtang'},
    'mingtang-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-mingtang/files/mingtang-B'], 'card': 'm-luoyang-mingtang'},
    'lingtai-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-lingtai/files/', r'cities/luoyang/progress-assets/flat/study-lingtai-'], 'card': 'm-luoyang-lingtai'},
    'taixue-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-taixue-a/files/', r'cities/luoyang/progress-assets/taixue-A-v3\.2/', r'cities/luoyang/progress-assets/flat/study-taixue-'], 'card': 'm-luoyang-taixue-a'},
    'stoneclassic': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-stoneclassic-access-court/files/'], 'card': 'm-luoyang-stoneclassic-access-court'},
    'south-altar-A': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-southern-altar/files/south-altar-A'], 'card': 'm-luoyang-southern-altar', 'except': [r'^A_presentation_ground$']},
    'south-altar-B': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-southern-altar/files/south-altar-B'], 'card': 'm-luoyang-southern-altar', 'except': [r'^B_presentation_ground$']},
    'north-altar': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-northern-altar/files/'], 'card': 'm-luoyang-northern-altar'},
    'waterway': {'kind': 'glb-nodes', 'glbs': [r'library/models/m-luoyang-palace-waterway-interface/files/'], 'card': 'm-luoyang-palace-waterway-interface'},
}

# existing ground pieces: id -> (file regex, node regex) resolved and hashed by builder
GROUND_PIECES = {
    'gp:kaiyang-ground-LOD0': (r'library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD0\.glb', r'.*'),
    'gp:kaiyang-ground-LOD1': (r'library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD1\.glb', r'.*'),
    'gp:kaiyang-ground-LOD2': (r'library/models/m-luoyang-kaiyang-gate/files/kaiyang-ground-LOD2\.glb', r'.*'),
    'gp:pingcheng-ground-LOD0': (r'library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD0\.glb', r'.*'),
    'gp:pingcheng-ground-LOD1': (r'library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD1\.glb', r'.*'),
    'gp:pingcheng-ground-LOD2': (r'library/models/m-luoyang-pingcheng-gate/files/pingcheng-ground-LOD2\.glb', r'.*'),
    'gp:market-cluster:sample_ground': (r'cities/luoyang/assets/market/market-cluster\.glb', r'^sample_ground$'),
    'gp:granary-city:original_city_ground_preserved': (r'cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD[012]\.glb', r'^original_city_ground_preserved$'),
    'gp:well-A-LOD0:demonstration_apron_opening': (r'model-library/well-study/assets/well-A-LOD[01]\.glb', r'demonstration_apron_opening'),
    'gp:stable-A:A_earth_platform': (r'library/models/m-luoyang-stable/files/A\.glb', r'^A_earth_platform$'),
    'gp:stable-B:B_earth_platform': (r'library/models/m-luoyang-stable/files/B\.glb', r'^B_earth_platform$'),
    'gp:kiln-A:A_presentation_ground': (r'library/models/m-luoyang-tile-kiln/files/kiln-A', r'^A_presentation_ground$'),
    'gp:kiln-B:B_presentation_ground': (r'library/models/m-luoyang-tile-kiln/files/kiln-B', r'^B_presentation_ground$'),
    'gp:hand-mill-A:A_presentation_ground': (r'library/models/m-luoyang-hand-mill/files/hand-mill-A', r'^A_presentation_ground$'),
    'gp:hand-mill-B:B_presentation_ground': (r'library/models/m-luoyang-hand-mill/files/hand-mill-B', r'^B_presentation_ground$'),
    'gp:admission-court:guard__guard-slice-ground-earth': (r'(library/models/m-luoyang-palace-admission-court/files/|cities/luoyang/progress-assets/palace-admission-court/)', r'^guard__guard-slice-ground-earth$'),
    'gp:south-altar-A:A_presentation_ground': (r'library/models/m-luoyang-southern-altar/files/south-altar-A', r'^A_presentation_ground$'),
    'gp:south-altar-B:B_presentation_ground': (r'library/models/m-luoyang-southern-altar/files/south-altar-B', r'^B_presentation_ground$'),
}
# ground pieces that exist but no seat 011-090 may touch (with reason)
GROUND_FROZEN = {
    'gp:yong-gate-apron (yong-gate-interface)': '雍门接街由原负责人继续（任务池保护清单）',
    'gp:yong-ground-LOD0..2': '雍门家族（保护）',
    'gp:life-block:C_life_block_ground_removable': '连续住宅生活片区 / 13院压缩片区（保护）',
    'gp:courtyard prototypes site_lot / site_neutral_lane / designed_* (all 44 courts)': 'excludeNodes in city; prototypes shared by many nodes — only node-specific overlays allowed (LY-041..050 use court:C02-010 frame)',
    'gp:A1-neighborhood A1__GROUND__earth': 'not in 011-090 scope',
    'gp:passage-interface *_floor (WFC study)': 'not in 011-090 scope',
    'gp:d08 D08-environment / access-D08': 'v1 / byte duplicate of ground-atomic D08 (LY-001); city uses ground-D08 node (owner LY-090)',
    'gp:main-roads / road-junction corridors (v1)': 'v1 archive entry assets; read-only reference for LY-081',
}

# card fields: owner rules. Card text fields an assembly/owner seat may PROPOSE (LY-100 writes).
CARD_PROPOSAL_FIELDS = ['status', 'statusNote', 'summary', 'files', 'gallery', 'cover', 'coverAlt']
CARD_NOTES_ANY = 'notes.*'  # every notes key (existing or new) of the card
CARD_FROZEN_FIELDS = ['spec', 'id', 'category', 'kind', 'title', 'english', 'related']

# city / research nodes protected or out of scope: reason
NODE_FROZEN_REASONS = {
    'yong-gate-body': '雍门接街 / 雍门本体由原负责人继续（保护）', 'yong-gate-interface': '雍门接街由原负责人继续（保护）',
    'wall-direct-gate-body-only': '广阳门既有门体，十二门本体不在本轮补件范围', 'wall-direct-wall-08': '广阳门 direct 转接段（与门体同组，非 011-090 范围）',
    'wall-direct-wall-09': '广阳门/雍门之间 direct 转接段（雍门接墙保护）',
    'research-north13-court-A2': '13院压缩由原负责人继续（保护）', 'research-north13-court-B': '13院压缩（保护）', 'research-north13-court-B2': '13院压缩（保护）',
    'research-north13-court-TC03-2': '13院压缩（保护）', 'research-north13-court-A': '13院压缩（保护）',
    'research-north13-yong-Y': '雍门研究候选（保护；LY-001 已提请撤出或标旧档）', 'research-north13-shangxi-X': '上西门：十二门本体，不在本轮',
    'research-north13-zhongdong-Z': '中东门：十二门本体，不在本轮', 'research-mao-gate': '旄门：十二门本体，不在本轮',
}
COURT_FROZEN_REASON = '44院原矩阵与计数不变；只有 LY-010 冻结的示范院（候选 C02-010）由 LY-050 持有'

# wall seams -> gate slot naming (C engineering; from current C wall layout + seat prep, not historical)
SEAM_GATES = {
    ('wall-A-wall-04', 'wall-A-wall-05'): ('开阳门 Kaiyang', 'S-KAIYANG'),
    ('wall-A-wall-05', 'wall-A-wall-06'): ('平城门 Pingcheng', 'S-PINGCHENG'),
    ('wall-A-wall-00', 'wall-A-wall-01'): ('谷门 Gu', 'S-GU'),
    ('wall-A-wall-00', 'wall-A-wall-11'): ('夏门 Xia', 'S-XIA'),
    ('wall-A-wall-06', 'wall-A-wall-07'): ('小苑门 Xiaoyuan (not in 011-090)', None),
    ('wall-A-wall-07', 'wall-direct-wall-08'): ('津门 Jin (not in 011-090)', None),
    ('wall-direct-wall-08', 'wall-direct-wall-09'): ('广阳门 Guangyang (existing, protected)', None),
    ('wall-A-wall-10', 'wall-direct-wall-09'): ('雍门 Yong (in city, protected)', None),
    ('wall-A-wall-10', 'wall-A-wall-11'): ('上西门 Shangxi (not in 011-090)', None),
    ('wall-A-wall-02', 'wall-A-wall-03'): ('中东门 Zhongdong (not in 011-090)', None),
    ('wall-A-wall-03', 'wall-A-wall-04'): ('旄门 Mao (not in 011-090)', None),
}
