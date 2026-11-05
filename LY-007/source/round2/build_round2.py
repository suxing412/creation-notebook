# -*- coding: utf-8 -*-
"""round2 风格验证：只用 ly_style 库函数 + 量到的尺寸，复刻她的 S84（市肆单铺，三档）与 G10（普通住屋房型中面数最少者，
LOD0 必交，LOD1/2 一并导出对照）。不读入、不拷贝她的任何几何；数字后注明出处：
  measure/orig_parts.txt（部件包围盒，measure_orig.py）、measure/orig_gltfjson.txt（节点/extras/顺序）、
  ../round1/measure/g10_earth_verts.txt 与 round1 评审（review_geo / review_lod / review_color）的顶点转储。
用法: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P build_round2.py -- <outdir>
坐标：Blender（X 面阔、Y 进深向后为 +、Z 上）。她的 glTF (x, y, z) = Blender (x, -z, y)。
"""
import sys, os, json
LIB = r'C:/Users/suxin/AppData/Local/Temp/claude/bfd0867865ae17cc/14ddfcf2-ca06-49dc-95f8-4586da1502c1/scratchpad/mq/style'
sys.path.insert(0, LIB)
import ly_style as ly  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)

D = ly.DIMS['house']
# 住屋/店铺屋面（S84、G10 实测相同，只差檐口标高 0.2）
RISE = 1.10           # 板底：檐口 3.0 -> 脊 4.1（S84）；3.2 -> 4.3（G10）；坡 1.1/2.45 = 24.18°
SLAB_T = 0.13         # 板顶 - 板底 = 3.13-3.0（S84 tile 板 max y 4.23 - 脊 4.1）
OV = 0.45             # 板边 x ±4.45 / 墙外皮 ±4.0；前后 glTF z 0.45 / -4.45，墙 0 / -4
RIBS = dict(d=0.11,             # 瓦垄包围盒宽 0.11（orig_parts：dims [0.11, 1.199, 2.367]）
            pitch=0.28, sides=8,  # 逐段排：0.75→2、7.4→26、9.4→33（库默认 'segments' 排法，pitch 0.28 为推断值）
            inset=0.06,           # 管心起点 glTF z=0.39（檐口 0.45 内收 0.06）
            lift=0.05, lift_ridge=0.05, lift_ref='edge',   # 起点 y 3.18 = 檐口板顶 3.13+0.05；终点 4.28 = 脊板顶 4.23+0.05
            ridge_gap=0.07)       # 终点 glTF z=-1.93，离脊线 -2.0 有 0.07
T = D['wall_t']       # 0.28：山墙 x -4..-3.72、后墙 glTF z -4..-3.72
FH = D['floor_h']     # 0.22：地坪顶 y 0.22
R_POST = D['post_d'] / 2
VERSION = 'claude-round2'


def gables(a, roof, x0, x1, DEP):
    """两山墙：墙身盒 FH..z_eave + 山尖（z_eave -> 板底 3.202 -> 脊 4.1），她的 S84/G10 山墙两面都有檐口线一圈顶点。"""
    ub = roof.bottom_z
    for side, face, inward in (('L', x0, 1), ('R', x1, -1)):
        a.gable_wall('Y', 0.0, DEP, face, T, FH, ub(face, 0.0), ub(face, DEP), DEP / 2, ub(face, DEP / 2), inward=inward,
                     name=f'gable_{side}', z_shoulder=roof.z_eave)


def build_s84():
    """S84 市肆单铺：8.0×4.0 夯土地坪 + 两山墙 + 后墙（前面敞开）；2 檐柱 + 檐枋；柜台（板 + 2 腿）；悬山顶 3 段板。"""
    a = ly.Assembly('s84', 'A', profile='house', naming='market', prototype='S84',
                    modules={'earth': 'body', 'timber': 'frontframe_counter', 'tile': 'roof_left'},
                    evidence='C Claude round-2 style replica of market shop S84 (open front, counter with staff passage); '
                             'rebuilt from measured sizes, not a surveyed building',
                    extras={'version': VERSION})
    W, DEP = 8.0, 4.0
    x0, x1 = -W / 2, W / 2
    PX = 3.6                                                                      # 柱心 x ±3.6（柱包围盒 -3.7..-3.5）
    a.floor_slab(x0, 0.0, x1, DEP, h=FH, name='floor')                            # earth x±4、glTF z -4..0、y 0..0.22
    roof = a.roof_gable(x0 - OV, x1 + OV, -OV, DEP + OV, z_eave=3.0, rise=RISE, t=SLAB_T, ribs=RIBS,
                        name='roof', slab_name='roof_left', splits=(-PX - R_POST, PX + R_POST))   # 板断在 ±3.70（柱外皮）
    gables(a, roof, x0, x1, DEP)
    # 后墙 x ±3.72、glTF z -4..-3.72，顶平 3.0（= 檐口线；板底 3.202/3.328，留缝）
    a.eave_wall(roof, 'X', x0 + T, x1 - T, DEP, T, FH, inward=-1, name='back_wall')
    # 檐柱：12 边 Ø0.20，柱心 x ±3.6、glTF z -0.16（Blender y 0.16），从 y=0 起穿过地坪，柱顶斜切贴板底（3.229 / 3.319）
    for px, nm in ((-PX, 'frontpost_sloped_cap'), (PX, 'frontpost_sloped_cap_r')):
        a.post(px, 0.16, 0.0, None, d=D['post_d'], sides=D['post_sides'], cap_roof=roof, lod2_shape='diamond', name=nm)
    # 檐枋：7.3×0.18×0.20，x ±3.65（伸进柱 0.15），y 3.0..3.2，glTF z -0.25..-0.07
    a.beam((-3.65, 0.16, 3.0), (3.65, 0.16, 3.0), 0.18, 0.20, name='eave_beam')
    # 柜台：台面 4.8×0.70×0.12（x ±2.4、y 0.96..1.08、glTF z -1.15..-0.45）+ 2 腿 0.14×0.50×0.80（x ±2.25、y 0.16..0.96，
    # 埋进地坪 0.06）。柜台 LOD2 删除（她的 S84-LOD2 timber 只剩柱 + 枋，36 三角）
    a.box((-2.4, 0.45, 0.96), (2.4, 1.15, 1.08), 'timber', lod='lod01', name='counter_top', tags=('counter',))
    for cx in (-2.25, 2.25):
        a.box((cx - 0.07, 0.55, FH - 0.06), (cx + 0.07, 1.05, 0.96), 'timber', lod='lod01',
              name=f'counter_leg_{"L" if cx < 0 else "R"}', tags=('counter',))
    door = {'center': (3.06, 0.80, FH), 'direction': (0, 1, 0), 'min_width': 0.8, 'min_height': 1.9}
    return a, roof, door


def build_g10():
    """G10 普通住屋（面数最少的房型）：10.0×4.0，夯土四面墙，前后墙正中各开 2.2×2.08 通门，前檐 2 柱，悬山顶 3 段板。"""
    a = ly.Assembly('g10', 'A', profile='house', naming='house_types', prototype='G10',
                    modules={'earth': 'body', 'timber': 'front_supports', 'tile': 'roof_left'},
                    evidence='C Claude round-2 style replica of house type G10 (through-passage functional variation); '
                             'rebuilt from measured sizes, not archaeological house')
    W, DEP = 10.0, 4.0
    x0, x1 = -W / 2, W / 2
    PX = 4.6                                                                      # 柱心 x ±4.6（柱包围盒 -4.7..-4.5）
    a.floor_slab(x0, 0.0, x1, DEP, h=FH, name='floor')                            # earth x±5、glTF z -4..0
    roof = a.roof_gable(x0 - OV, x1 + OV, -OV, DEP + OV, z_eave=3.2, rise=RISE, t=SLAB_T, ribs=RIBS,
                        name='roof', slab_name='roof_left', splits=(-PX - R_POST, PX + R_POST))   # 3.2 -> 4.3，板断在 ±4.70
    gables(a, roof, x0, x1, DEP)
    door = (-1.1, 1.1, FH, 2.30)                                                  # 洞 x ±1.1、y 0.22..2.30（g10_earth_verts）
    # 前后墙 x ±4.72，顶平 3.2（= 檐口线；板底外皮 3.402、内皮 3.528，留缝）
    a.eave_wall(roof, 'X', x0 + T, x1 - T, 0.0, T, FH, openings=[door], inward=1, name='front_wall')
    a.eave_wall(roof, 'X', x0 + T, x1 - T, DEP, T, FH, openings=[door], inward=-1, name='back_wall')
    # 檐柱：12 边 Ø0.20，柱心 x ±4.6、glTF z +0.18（墙外 0.18，Blender y -0.18），立在地面 0，柱顶斜切贴板底（3.276 / 3.366）
    for px, nm in ((-PX, 'frontpost_sloped_cap'), (PX, 'frontpost_sloped_cap_r')):
        a.post(px, -0.18, 0.0, None, d=D['post_d'], sides=D['post_sides'], cap_roof=roof, lod2_shape='diamond', name=nm)
    door_ck = {'center': (0.0, T / 2, FH), 'direction': (0, 1, 0), 'min_width': 0.8, 'min_height': 1.9}
    return a, roof, door_ck


def slim(c):
    """检查结果里只留可 JSON 化的摘要。"""
    return {'floating': c['floating'], 'intersections_unexpected': c['intersections_unexpected'],
            'intersections_allowed': len(c['intersections_allowed']), 'coplanar': c['coplanar'], 'grounded': c['grounded']}


def main():
  report = {}
  for builder in (build_s84, build_g10):
      ly.clear_scene()
      a, roof, door = builder()
      print(f'===== {a.prototype}  构件 {len(a.components)}  坡度 {roof.pitch_deg:.3f}°  板段 {roof.segments}')
      chk0 = ly.report_checks(a, lod=0)
      chk1 = ly.report_checks(a, lod=1)
      cl = ly.check_clearance(a, door['center'], door['direction'], min_width=door['min_width'], min_height=door['min_height'])
      print('  通道净空', cl)
      res = ly.export_lods(a, OUT, lods=(0, 1, 2))
      report[a.prototype] = {
          'components': len(a.components), 'pitch_deg': round(roof.pitch_deg, 3), 'segments': roof.segments,
          'checks_lod0': slim(chk0), 'checks_lod1': slim(chk1), 'clearance': cl,
          'glb': {f'LOD{k}': {kk: v.get(kk) for kk in ('file', 'triangles', 'vertices', 'materials', 'images', 'nodes', 'meshes',
                                                       'extras', 'size', 'bbox_min', 'flat_normals', 'uv_world_box', 'uv_ties',
                                                       'degenerate', 'issues', 'ratio_to_lod0', 'generator')}
                  for k, v in res.items()},
      }
  json.dump(report, open(os.path.join(OUT, 'round2_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
  bad = [(k, lod, v['issues']) for k, r in report.items() for lod, v in r['glb'].items() if v['issues']]
  chk_bad = [(k, n, r[n][f]) for k, r in report.items() for n in ('checks_lod0', 'checks_lod1')
             for f in ('floating', 'intersections_unexpected', 'coplanar') if r[n][f]]
  print('ROUND2 DONE', OUT, 'GLB 问题:', bad if bad else '无', '检查问题:', chk_bad if chk_bad else '无')


if not globals().get('LY_NO_MAIN'):
    main()
