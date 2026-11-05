# -*- coding: utf-8 -*-
"""ly_style 最小示例：一间带屋面的小屋（住屋做法，尺寸取 H72 / G10）+ 一座庑殿小亭（殿堂做法）。
用法: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P demo_build.py -- <outdir>
输出: <outdir>/demohut-A-LOD{0,1,2}.glb、<outdir>/demoting-A-LOD{0,1,2}.glb、<outdir>/demo_report.json
"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ly_style as ly  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(HERE, 'demo')
os.makedirs(OUT, exist_ok=True)
report = {}


def build_hut():
    """小屋：6.0×4.0 m，前檐墙外皮在 y=0（住屋家族原点约定），夯土墙 0.28、地坪 0.22、悬山 24.2°、出檐 0.45。"""
    D = ly.DIMS['house']
    a = ly.Assembly('demohut', 'A', evidence='C ly_style demo hut, not a surveyed building', profile='house',
                    extras={'version': 'demo-1'})
    W, DEP, t = 6.0, 4.0, D['wall_t']
    x0, x1 = -W / 2, W / 2
    fh = D['floor_h']
    a.floor_slab(x0, 0.0, x1, DEP, h=fh)
    ov = D['overhang']
    run = DEP / 2 + ov
    rise = 1.10                             # H72 roof_left：板底檐口 2.8、脊 3.9，坡 1.1/2.45 = 0.449（24.2°）
    roof = a.roof_gable(x0 - ov, x1 + ov, -ov, DEP + ov, z_eave=D['eave_wall_h'], rise=rise, t=D['slab_t'],
                        ribs=dict(d=D['rib_d'], pitch=D['rib_pitch'], lift=D['rib_lift'], inset=D['rib_inset'], sides=8))
    ub = roof.bottom_z
    # 山墙（两侧，全进深），山尖斜边 = 屋面板底
    for side, face, inward in (('L', x0, 1), ('R', x1, -1)):
        a.gable_wall('Y', 0.0, DEP, face, t, fh, ub(0, 0.0), ub(0, DEP), DEP / 2, ub(0, DEP / 2), inward=inward,
                     name=f'gable_{side}')
    # 前檐墙：门 + 窗，墙顶斜面贴合板底（外皮处 3.002、内皮处 3.128）
    door = (-0.78, 0.78, fh, 2.38)
    win = (1.3, 2.1, D['window_sill'], D['window_sill'] + D['window_h'])
    a.wall('X', x0 + t, x1 - t, 0.0, t, fh, (ub(0, 0.0), ub(0, t)), openings=[door, win], inward=1, name='front_wall')
    a.wall('X', x0 + t, x1 - t, DEP, t, fh, (ub(0, DEP), ub(0, DEP - t)), inward=-1, name='back_wall')
    # 门框、门叶（开 90° 向内）、窗
    a.door_frame('X', door[0], door[1], 0.0, t, fh, door[3], jamb=D['door_jamb'], head=D['door_head'])
    clear_w = door[1] - door[0] - 2 * D['door_jamb']
    a.door_leaf((door[0] + D['door_jamb'], t, fh + 0.01), clear_w, 2.05, t=D['leaf_t'], angle_deg=90, axis='X', direction=1,
                inward=1, bands=(0.2, 0.8), name='leaf')
    a.window('X', win[0], win[1], 0.0, t, win[2], win[3], member=D['window_member'], bars=D['bars'], bar=D['bar'])
    # 檐柱 + 檐枋（12 边 Ø0.20，柱心在墙外 0.18；枋顶抵板底）
    post_top = 2.7
    for px in (-2.6, 2.6):
        a.post(px, -0.18, 0.0, post_top)
    # H72 檐枋深 0.30，靠上面另一层瓦面盖住穿出的 5 mm；本例屋面只有一块 0.13 板（G10 做法），故枋深取 0.24
    a.beam_under_roof(roof, (-2.78, -0.18, post_top), (2.78, -0.18, post_top), 0.24, name='front_beam')
    # 檐下檩条：每坡 2 根，通长伸出山墙
    a.purlins(roof, [0.55, 1.05, DEP - 0.55, DEP - 1.05], x0 - ov, x1 + ov, w=D['purlin'][0], h=D['purlin'][1])
    return a, roof, {'center': (0.0, t / 2, fh), 'direction': (0, 1, 0), 'min_width': 0.8, 'min_height': 1.9}


def build_pavilion():
    """庑殿小亭：台基 6.8×5.6×0.6、前出 4 级踏步、4 柱 16 边 Ø0.32 + earth 方础、栌斗、阑额、四阿顶等坡 22°。"""
    D = ly.DIMS['hall']
    a = ly.Assembly('demoting', 'A', evidence='C ly_style demo pavilion, not a surveyed building', profile='hall',
                    extras={'version': 'demo-1'})
    a.platform(-3.4, -2.8, 3.4, 2.8, 0.0, 0.6)
    a.steps(-1.1, 1.1, -2.8, 0.0, 0.6, direction=-1, riser_max=D['riser_max'], going=D['going'])
    col_top = 3.36
    for cx in (-2.2, 2.2):
        for cy in (-1.6, 1.6):
            a.column(cx, cy, 0.6, col_top, d=D['column_d'], sides=D['column_sides'], base=True, base_ratio=D['base_ratio'],
                     base_h=D['base_h'], name=f'col_{"L" if cx < 0 else "R"}{"F" if cy < 0 else "B"}')
            a.ludou(cx, cy, col_top, size=0.5, h=0.24, name=f'ludou_{"L" if cx < 0 else "R"}{"F" if cy < 0 else "B"}')
    beam_z = col_top + 0.24
    roof = a.roof_hip(-3.2, 3.2, -2.6, 2.6, z_eave=3.45, rise=round(2.6 * 0.404, 4), t=0.16,
                      ribs=dict(d=D['rib_d'], pitch=D['rib_pitch'], lift=D['rib_lift'], sides=8),
                      ridge=dict(d=D['ridge_d'], sides=D['ridge_sides'], lift=D['ridge_lift']),
                      hip_ridges=dict(d=D['hip_ridge_d'], sides=16, lift=0.04))
    w = D['beam'][0]
    for cy in (-1.6, 1.6):
        a.beam_under_roof(roof, (-2.2 - 0.16, cy, beam_z), (2.2 + 0.16, cy, beam_z), w, name=f'beamX_{"F" if cy < 0 else "B"}')
    for cx in (-2.2, 2.2):
        a.beam_under_roof(roof, (cx, -1.6 + w / 2, beam_z), (cx, 1.6 - w / 2, beam_z), w, name=f'beamY_{"L" if cx < 0 else "R"}')
    a.railing((-3.2, 2.7, 0.6), (3.2, 2.7, 0.6), 0.6, h=1.0, post_d=0.10, post_sides=12, spacing=1.6)
    return a, roof, {'center': (0.0, -1.6, 0.6), 'direction': (0, 1, 0), 'min_width': 2.0, 'min_height': 2.4}


for builder in (build_hut, build_pavilion):
    a, roof, door = builder()
    print(f'===== {a.prefix}  构件 {len(a.components)}  坡度 {roof.pitch_deg:.2f}°')
    chk = ly.report_checks(a)
    cl = ly.check_clearance(a, door['center'], door['direction'], min_width=door['min_width'], min_height=door['min_height'])
    print('  入口净空', cl)
    res = ly.export_lods(a, OUT)
    report[a.prefix] = {
        'components': len(a.components), 'pitch_deg': round(roof.pitch_deg, 3),
        'checks': {'floating': chk['floating'], 'intersections_unexpected': chk['intersections_unexpected'],
                   'intersections_allowed': len(chk['intersections_allowed']), 'coplanar': chk['coplanar'],
                   'grounded': chk['grounded'], 'clearance': cl},
        'glb': {f'LOD{k}': {kk: v[kk] for kk in ('file', 'triangles', 'vertices', 'materials', 'images', 'nodes', 'size', 'bbox_min',
                                                  'flat_normals', 'uv_world_box', 'degenerate', 'issues', 'ratio_to_lod0', 'generator')}
                for k, v in res.items()},
    }
json.dump(report, open(os.path.join(OUT, 'demo_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
bad = [(k, lod, v['issues']) for k, r in report.items() for lod, v in r['glb'].items() if v['issues']]
print('DEMO DONE', OUT, 'GLB 问题:', bad if bad else '无')
