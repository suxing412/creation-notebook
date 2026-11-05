# -*- coding: utf-8 -*-
"""LY-007 基准球与 1 m UV 标定块（LY_P01 五种材料 × 三档）。

用法: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P build_refsphere.py -- <LY-007 目录>
产物: models/refsphere/lyref-A-LOD0/1/2.glb、qa/refsphere-build.json、native/lyref-A.blend（源工程，不进 git）

做法（全部走冻结库 source/lib/ly_style.py，库文件不改；贴图目录改指本席位 textures/）：
  * 每种材料一组：基准球 + 1.000 m 立方标定块。顺序与间距按 MAT_ORDER：earth, path, paper__stone, timber, tile，
    沿 X 每 2.0 m 一组（Blender 坐标；导出后 glTF X 不变）。
  * 基准球：经纬球，极区截成平底/平顶 n 边形封口（θ0 = 12°，三档相同），保证三档包围盒逐值相同、平底落在 z=0。
    赤道环三档都有（环数取奇数），边数取 4 的倍数，所以 X/Y 向半径三档都等于 r。
      LOD0 24 边 × 11 环；LOD1 12 边 × 7 环；LOD2 8 边 × 5 环。
    这是「同一包围盒、逐档减环减边」的示范件，不是建筑构件，不套用圆木 16→8→方盒规则。
  * 标定块：1.000 m 方盒（keep 规则，三档几何相同）。盒式 UV 下每个面 UV 跨度恰为 1.0，
    用来读回核对「1 UV 单位 = 1 m」与「LOD0 512 px/m、LOD1 256 px/m」。
证据等级：C 工程设计（本席位自造的基准件，不是她的模型，也不是任何历史构件）。
"""
import sys, os, json, math
argv = sys.argv[sys.argv.index('--') + 1:]
W = os.path.abspath(argv[0])
sys.path.insert(0, os.path.join(W, 'source', 'lib'))
import bpy  # noqa: E402
import ly_style as ly  # noqa: E402

ly.TEX_DIR = os.path.join(W, 'textures')          # 只改模块变量，不改库文件
OUT = os.path.join(W, 'models', 'refsphere')
os.makedirs(OUT, exist_ok=True)

R = 0.5
THETA0 = math.radians(12.0)
TIERS = {0: (24, 11), 1: (12, 7), 2: (8, 5)}
SPACING = 2.0


def _c(a):
    """cos/sin 的 0、±1 取精确值（同库 geo_prism 的做法）。"""
    for t in (0.0, 1.0, -1.0, 0.5, -0.5):
        if abs(a - t) < 1e-12:
            return t
    return a


def geo_sphere(cx, cy, r, sides, rings, theta0):
    zc = r * math.cos(theta0)
    verts, faces = [], []
    for k in range(rings):
        th = theta0 + k * (math.pi - 2 * theta0) / (rings - 1)
        z = zc + r * _c(math.cos(th)); rr = r * _c(math.sin(th))
        if k == (rings - 1) // 2:
            z, rr = zc, r                                   # 赤道环精确
        if k == rings - 1:
            z = 0.0                                         # 平底精确落地
        if k == 0:
            z = 2 * zc
        for i in range(sides):
            ph = 2 * math.pi * i / sides
            verts.append((cx + rr * _c(math.cos(ph)), cy + rr * _c(math.sin(ph)), z))
    faces.append(tuple(range(sides - 1, -1, -1)))          # 顶封口（_oriented 会统一朝外）
    for k in range(rings - 1):
        a0, b0 = k * sides, (k + 1) * sides
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((a0 + i, b0 + i, b0 + j, a0 + j))
    faces.append(tuple(range((rings - 1) * sides, rings * sides)))
    return ly.Geo(verts, faces)


ly.clear_scene()
a = ly.Assembly('lyref', 'A',
                evidence='C LY-007 material reference sphere and 1 m UV calibration cube; engineering test object, '
                         'not an architectural asset and not a historical component',
                profile='hall', extras={'version': 'LY-007-baseline-1'})
log = {'materials': ly.MAT_ORDER, 'R': R, 'theta0_deg': 12.0, 'tiers': TIERS, 'components': []}
for i, mat in enumerate(ly.MAT_ORDER):
    x = i * SPACING
    for lod, (sides, rings) in TIERS.items():
        g = ly._oriented(geo_sphere(x, 0.0, R, sides, rings, THETA0))
        c = a.add('mesh', mat, {'verts': [ly._v(p) for p in g.verts], 'faces': [list(f) for f in g.faces], 'lod_set': [lod]},
                  name=f'sphere_{mat}_L{lod}', tags=('refsphere',))
        log['components'].append(dict(name=c['name'], mat=mat, lod_set=[lod], sides=sides, rings=rings,
                                      tris=g.tri_count(), bbox=g.bbox()))
    c = a.box((x - 0.5, 0.9, 0.0), (x + 0.5, 1.9, 1.0), mat, name=f'uvcube_{mat}', tags=('uvcube',))
    log['components'].append(dict(name=c['name'], mat=mat, lod='keep', size=1.0))

checks = ly.report_checks(a, verbose=True)
log['checks_lod0'] = {k: (dict(count=len(v), items=json.loads(json.dumps(v[:20], default=str)))
                          if isinstance(v, list) else json.loads(json.dumps(v, default=str)))
                      for k, v in (checks or {}).items()}
res = ly.export_lods(a, OUT, lods=(0, 1, 2), keep_objects=True)
log['export'] = {str(k): {kk: vv for kk, vv in v.items() if kk not in ('extras',)} for k, v in res.items()}
os.makedirs(os.path.join(W, 'native'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'native', 'lyref-A.blend'), compress=False)
json.dump(log, open(os.path.join(W, 'qa', 'refsphere-build.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1,
          default=str)
print('REFSPHERE DONE', {k: (v['triangles'], v['ratio_to_lod0'], v['issues']) for k, v in res.items()})
