# -*- coding: utf-8 -*-
"""
ly_style —— 「造物之匣 · 洛阳城」伊苏里亚风格 Blender 工具库（Blender 4.3.2 / 5.2.1 均可运行）

用途
    让新模型（包括 Claude 子代理批量铺量的模型）与伊苏里亚已交付的东汉雒阳（约公元 180 年）
    低多边形研究性复原模型，在材质、几何做法、LOD、命名、导出上完全一致。
    规范正文见同目录 LY-style-bible.md；本库的每个默认值都对应规范里的一条实测证据。

坐标约定（建模一律用 Blender 世界坐标，单位米）
    X = 面阔（左右），Z = 竖直向上，-Y = 正面（导出后即 glTF 的 +Z）。地面 z = 0。
    导出时 export_yup=True 把 Blender (x, y, z) 变成 glTF (x, z, -y)。

基本用法
    import sys; sys.path.insert(0, r'<本文件所在目录>')
    import ly_style as ly
    a = ly.Assembly('demohut', 'A', evidence='C ... not a surveyed building', profile='house')
    a.floor_slab(...); a.wall(...); roof = a.roof_gable(...); ...
    ly.report_checks(a)                 # 悬空 / 穿插 / 共面 / 落地
    ly.check_clearance(a, ...)          # 入口净空
    ly.export_lods(a, outdir)           # 一次导出 LOD0/1/2 并逐个自检

设计要点
    * 每个构件 = 一个「组件记录」（种类、材料、参数、LOD 规则），LOD0 时同时生成一个
      Blender 物体供检查和预览（物体上存 obj['ly'] = JSON 记录）。
    * LOD1 / LOD2 不做 decimate，而是按她的做法用同一组参数重新生成：圆木 16/12 边 -> 8 边 -> 2r 方盒；
      瓦垄 8 边 -> 抽稀 + 4 边菱形 -> 删除；正脊 16 -> 8 -> 方盒；小件按规则删除；夯土不变；
      材质 __PBR(512) -> __PBR(256) -> __FLAT。
    * 导出时按材质合并成一个网格一个节点，命名按卡片家族（NAMING：default <slug>-<变体>-static_<材料>；
      market S84-static-LY_P01_<mat>__PBR；house_types layout__LY_P01_<mat>__PBR）；节点无 TRS；
      导出后 reorder_glb 把节点/网格/材质/贴图/二进制改排为 earth→timber→tile（她的顺序）；
      UV = 世界坐标盒式投影（1 UV 单位 = 1 m，X/Y 并列取 (y,z)）；全部平直着色。

round2 修订（validate/round2/）：住屋/店铺屋面板按檐柱外皮分 3 段、瓦垄逐段排（pitch 0.28）、LOD1 逐段重排一半；
    檐墙平顶在檐口线（eave_wall）；山墙在檐口线分墙身盒 + 山尖（gable_wall z_shoulder）；檐柱穿地坪从 0 起；
    UV X/Y 并列取 (y,z)；命名/extras/文件名按家族；导出后改排材质顺序。
"""
import bpy
import bmesh
import math
import json
import os
import re
import struct
import hashlib
import collections
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

LIB_DIR = os.path.dirname(os.path.abspath(__file__))
TEX_DIR = os.path.join(LIB_DIR, 'textures')
EPS = 1e-6

# --------------------------------------------------------------------------------------------
# 0. 调色板 / 规范常数
# --------------------------------------------------------------------------------------------
#: 材料表。flat = __FLAT 的 baseColorFactor（线性，float32 原值照抄她的 GLB）；rough = __FLAT 粗糙度；
#: tex = 贴图文件名前缀（木材在贴图里叫 wood）；base_texture=False 表示 __PBR 只有底色因子不挂底色图。
PALETTE = {
    'earth': dict(flat=(0.3762621283531189, 0.2581828534603119, 0.13013647496700287), rough=0.88, tex='earth', hex='#A58B65'),
    'timber': dict(flat=(0.09305896610021591, 0.06480326503515244, 0.0423114113509655), rough=0.88, tex='wood', hex='#56483A'),
    'tile': dict(flat=(0.09530746936798096, 0.10224173218011856, 0.08865558356046677), rough=0.88, tex='tile', hex='#575A54'),
    'path': dict(flat=(0.4677838087081909, 0.35640013217926025, 0.21952620148658752), rough=0.88, tex='earth', hex='#B6A181'),
    'paper__stone': dict(flat=(0.8069522380828857, 0.7379103899002075, 0.5840784311294556), rough=0.90, tex='stone',
                         base_texture=False, hex='#E8DFC9'),
}
MAT_ORDER = ['earth', 'path', 'paper__stone', 'timber', 'tile']
TEX_RES = {0: 512, 1: 256}          # LOD0 512²、LOD1 256²、LOD2 无贴图

#: LOD 规则档：house = 普通住屋/门房（G10、H72、S84）；hall = 殿堂/复道（deyang、yutang、gallery）；
#: gate = 试做城门（kaiyang、pingcheng、shangxi、yong、que）。
#: rib_layout：'segments' = 瓦垄按屋面板分段逐段居中排（她的 S84/G10：n = floor(段宽 / pitch)，心距 = 段宽 / n）；
#:             'even' = 全长等距居中（殿堂、城门沿用 round0 做法，未按段复核）。
#: rib_lod1：'relay' = LOD1 每段重新排 n0//2 根（她的 S84-LOD1：段 2→1、26→13；G10 33→16），不是 LOD0 子集；
#:           'keep_every' = LOD0 中以中间一根为基准每 k 根留 1（rib_keep_every）。round2 验证改。
LOD_PROFILES = {
    'house': dict(round_lod1=8, rib_keep_every=2, rib_sides_lod1=4, thin_keep_every=2, ridge_lod1=8,
                  rib_layout='segments', rib_lod1='relay'),
    'hall': dict(round_lod1=8, rib_keep_every=2, rib_sides_lod1=8, thin_keep_every=2, ridge_lod1=8,
                 rib_layout='even', rib_lod1='keep_every'),
    'gate': dict(round_lod1=8, rib_keep_every=4, rib_sides_lod1=4, thin_keep_every=2, ridge_lod1=8,
                 rib_layout='even', rib_lod1='keep_every'),
}

#: 命名与 extras 预设（round2：按她的卡片家族写法）。
#:   node / mesh / file 为 str.format 模板，可用字段：prefix（<slug>-<V>）、proto（Assembly.prototype）、
#:   mat（earth/timber/…）、material（该 LOD 的材质名 LY_P01_<mat>__PBR|FLAT）、first（该材质组第一个组件名）、lod。
#:   extras：节点 extras 的键顺序；值来源见 node_extras。
NAMING = {
    # 城门 / 礼制 / 宫殿 23 张卡：kaiyang-K-static_tile
    'default': dict(node='{prefix}-static_{mat}', mesh='{prefix}-static_{mat}', file='{prefix}-LOD{lod}.glb',
                    extras=('evidence', 'metres_per_unit', 'LOD')),
    # 市肆模块（S84/S86）：节点 S84-static-LY_P01_earth__PBR，网格 S84_floor，文件 S84-LOD0.glb；
    # extras {prototype, module, unit:'metres', evidence, version, meters_per_unit:1}（validate/round2/measure/gltfjson.txt）
    'market': dict(node='{proto}-static-{material}', mesh='{proto}_{first}', file='{proto}-LOD{lod}.glb',
                   extras=('prototype', 'module', 'unit', 'evidence', 'version', 'meters_per_unit')),
    # 普通住屋房型（G10）：节点 layout__LY_P01_earth__PBR，网格 G10_floor，文件 G10-LOD0.glb；
    # extras {prototype, module, unit:'metres', evidence}（无 version、meters_per_unit）
    'house_types': dict(node='layout__{material}', mesh='{proto}_{first}', file='{proto}-LOD{lod}.glb',
                        extras=('prototype', 'module', 'unit', 'evidence')),
}

#: 典型尺寸（米）。house 取 H72 / G10 / S84 实测，hall 取 palace 家族（deyang、sidehall、gallery、yutang）。
DIMS = {
    'house': dict(wall_t=0.28, floor_h=0.22, eave_wall_h=2.8, overhang=0.45, pitch_deg=24.2, slab_t=0.13,
                  rib_d=0.11, rib_pitch=0.28, rib_lift=0.02, rib_inset=0.06, post_d=0.20, post_sides=12,
                  door_w=1.76, door_h=2.16, door_jamb=0.08, door_head=0.08, window_w=0.8, window_h=0.8, window_sill=1.2,
                  window_member=0.05, bar=0.035, bars=3, leaf_t=0.06, purlin=(0.08, 0.055)),
    'hall': dict(column_d=0.32, column_sides=16, base_ratio=1.6, base_h=0.2, slab_t=0.12, rib_d=0.07, rib_pitch=0.43,
                 rib_lift=0.02, ridge_d=0.15, ridge_sides=16, ridge_lift=0.04, hip_ridge_d=0.16, riser_max=0.15, going=0.32,
                 beam=(0.24, 0.30), overhang=1.0),
    'gate': dict(column_d=0.34, column_sides=16, slab_t=0.16, rib_d=0.066, rib_pitch=0.243, rib_lift=0.02, ridge_d=0.18,
                 ridge_sides=16, ridge_lift=0.04, leaf_t=0.14),
}

#: 允许的穿插（她的做法里有意埋入的组合，按 tag 两两配对）
ALLOWED_INTERSECT = {
    frozenset(('rib', 'slab')), frozenset(('rib', 'ridge')), frozenset(('ridge', 'slab')), frozenset(('hip_ridge', 'slab')),
    frozenset(('hip_ridge', 'rib')), frozenset(('hip_ridge', 'ridge')), frozenset(('rib',)), frozenset(('hip_ridge',)),
    frozenset(('purlin', 'slab')), frozenset(('purlin', 'gable')), frozenset(('beam', 'slab')), frozenset(('wall', 'slab')),
    frozenset(('gable', 'slab')), frozenset(('eave_tile',)), frozenset(('eave_tile', 'slab')),
    # round1 验证补：S84 檐枋 x±3.65 伸进 Ø0.20 檐柱（柱心 x±3.6）0.15，她的埋入做法（validate/round1/measure）
    frozenset(('beam', 'post')),
    # round2 验证补：她的檐柱从 y=0 起穿过 0.22 地坪（S84 timber 最低 y 0.000），柜台腿底 0.16 埋进地坪 0.06
    frozenset(('post', 'floor')), frozenset(('counter', 'floor')),
}

# --------------------------------------------------------------------------------------------
# 1. 材质工厂
# --------------------------------------------------------------------------------------------
_IMG_CACHE = {}


def texture_path(stem, kind, res):
    """返回她的共享贴图在本库 textures/ 下的路径（相对本文件定位）。

    stem: 'earth' | 'wood' | 'tile' | 'stone'；kind: 'basecolor' | 'normal' | 'orm'；res: 512 | 256。
    文件名与她 GLB 里的 image.name 相同（如 earth-basecolor.png），导出器据此命名 glTF image。"""
    return os.path.join(TEX_DIR, str(res), f'{stem}-{kind}.png')


def _image(stem, kind, res):
    """加载（或复用）一张共享贴图；底色 sRGB，法线与 ORM 用 Non-Color。贴图不修改，保证导出时原字节嵌入。"""
    key = (stem, kind, res)
    im = _IMG_CACHE.get(key)
    if im is not None:
        try:
            im.name  # noqa: B018  # 检查是否已被删除
            return im
        except ReferenceError:
            pass
    p = texture_path(stem, kind, res)
    if not os.path.exists(p):
        raise FileNotFoundError(f'缺少共享贴图 {p}；先运行 extract_textures.py')
    im = bpy.data.images.load(p, check_existing=True)
    im.colorspace_settings.name = 'sRGB' if kind == 'basecolor' else 'Non-Color'
    _IMG_CACHE[key] = im
    return im


def _principled(nt):
    """新建 Principled BSDF 并接到材质输出；IOR 1.5、Specular IOR Level 0.5、无自发光，避免导出多余扩展。"""
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (100, 0)
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    # 与 glTF 默认一致，避免导出 KHR_materials_ior / specular 扩展
    for k, v in (('IOR', 1.5), ('Specular IOR Level', 0.5), ('Alpha', 1.0)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    if 'Emission Strength' in b.inputs:
        b.inputs['Emission Strength'].default_value = 0.0
    return b


def _new_material(name):
    """按名取或新建材质，清空节点树并关闭背面剔除（导出 doubleSided: true）。"""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    m.use_backface_culling = False          # -> doubleSided: true（她的全部材质都是双面）
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt


def pbr_material(mat, res=512):
    """生成/重配 LY_P01_<mat>__PBR：底色图 -> Base Color，ORM 图 G -> Roughness、B -> Metallic，法线图 -> Normal Map。

    与她的 GLB 一致：不写 metallicFactor/roughnessFactor（导出为默认 1，靠 ORM 的 B=0 得到非金属），
    不引用 occlusionTexture，normalTexture 不写 scale。res=512 用于 LOD0，256 用于 LOD1。
    paper__stone 例外：不挂底色图，只写 baseColorFactor（与 foot-pestle 相同）。"""
    spec = PALETTE[mat]
    m, nt = _new_material(f'LY_P01_{mat}__PBR')
    b = _principled(nt)
    stem = spec['tex']
    if spec.get('base_texture', True):
        tb = nt.nodes.new('ShaderNodeTexImage'); tb.location = (-500, 300)
        tb.image = _image(stem, 'basecolor', res); tb.interpolation = 'Linear'; tb.extension = 'REPEAT'
        nt.links.new(tb.outputs['Color'], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*spec['flat'], 1.0)
    to = nt.nodes.new('ShaderNodeTexImage'); to.location = (-500, 0)
    to.image = _image(stem, 'orm', res); to.interpolation = 'Linear'; to.extension = 'REPEAT'
    sep = nt.nodes.new('ShaderNodeSeparateColor'); sep.location = (-200, 0)
    nt.links.new(to.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], b.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.location = (-500, -300)
    tn.image = _image(stem, 'normal', res); tn.interpolation = 'Linear'; tn.extension = 'REPEAT'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.location = (-200, -300); nm.inputs['Strength'].default_value = 1.0
    nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m


def flat_material(mat):
    """生成 LY_P01_<mat>__FLAT：baseColorFactor = 她的线性色值（= PBR 底色图均值转线性），metallic 0，roughness 0.88
    （paper__stone 为 0.90）。用于 LOD2。"""
    spec = PALETTE[mat]
    m, nt = _new_material(f'LY_P01_{mat}__FLAT')
    b = _principled(nt)
    b.inputs['Base Color'].default_value = (*spec['flat'], 1.0)
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Roughness'].default_value = spec['rough']
    return m


_MAT_STATE = {}


def material_for(mat, lod):
    """按 LOD 取材质：LOD0 -> __PBR(512)，LOD1 -> __PBR(256)，LOD2 -> __FLAT。同名 __PBR 在两档之间重配贴图；
    分辨率没变时直接复用（批量铺量时不必每个构件都重建节点树）。"""
    if mat not in PALETTE:
        raise KeyError(f'未知材料 {mat}；可用 {list(PALETTE)}')
    key = f'LY_P01_{mat}__' + ('FLAT' if lod >= 2 else 'PBR')
    want = 'flat' if lod >= 2 else TEX_RES[lod]
    m = bpy.data.materials.get(key)
    if m is not None and _MAT_STATE.get(key) == want and m.node_tree and len(m.node_tree.nodes) > 1:
        return m
    m = flat_material(mat) if lod >= 2 else pbr_material(mat, TEX_RES[lod])
    _MAT_STATE[key] = want
    return m


def srgb_to_linear(c):
    """sRGB(0-1) -> 线性。FLAT 色值 = 底色贴图均值经此换算（earth #A58B65 -> 0.3763/0.2582/0.1301）。"""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


# --------------------------------------------------------------------------------------------
# 2. 几何原语（纯 Python：顶点列表 + 面；均为闭合体，法线朝外）
# --------------------------------------------------------------------------------------------
class Geo:
    """一块几何：verts = [(x,y,z)...]，faces = [(i,j,k,...)...]，Blender 世界坐标（米）。"""
    __slots__ = ('verts', 'faces')

    def __init__(self, verts=None, faces=None):
        """用顶点列表与面列表建一块几何。"""
        self.verts = [tuple(map(float, v)) for v in (verts or [])]
        self.faces = [tuple(f) for f in (faces or [])]

    def add(self, other):
        """把另一块几何并进来（顶点不焊接）。"""
        o = len(self.verts)
        self.verts.extend(other.verts)
        self.faces.extend(tuple(i + o for i in f) for f in other.faces)
        return self

    def transformed(self, M):
        """返回经 4x4 矩阵变换后的副本。"""
        return Geo([tuple(M @ Vector(v)) for v in self.verts], list(self.faces))

    def bbox(self):
        """返回 (最小角, 最大角)。"""
        xs, ys, zs = zip(*self.verts)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def tri_count(self):
        """三角数（n 边形按 n-2 计，与导出后的三角数一致）。"""
        return sum(len(f) - 2 for f in self.faces)


_BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def geo_box(lo, hi):
    """轴对齐方盒（8 顶点、6 面、12 三角）。她的梁、枋、板、墩台、柱础、踏步都是这种盒，任何 LOD 都不倒角。"""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    if x1 - x0 < EPS or y1 - y0 < EPS or z1 - z0 < EPS:
        raise ValueError(f'退化方盒 {lo} {hi}')
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return Geo(v, _BOX_FACES)


def geo_hexa(c):
    """任意六面体（8 角点，顺序同 geo_box：底面 x0y0,x1y0,x1y1,x0y1 后接顶面同序）。用于斜顶墙段、收分台体。"""
    return Geo(c, _BOX_FACES)


def _perp_basis(a):
    """给管/柱轴线 a 选截面基 (u, v)：u 取 X、Z、Y 中第一个与轴足够垂直的世界轴（她的做法：首顶点在轴线方向上，
    竖柱与沿坡瓦垄的首顶点朝 X，沿 X 的正脊首顶点朝 Z）。全程双精度（mathutils.Vector 是单精度，会让
    -3.6-0.1 变成 -3.6999998，而她的是 float32(-3.7) = -3.70000005；45° 并列面的 UV 取向取决于这一位）。"""
    L = math.sqrt(sum(c * c for c in a))
    a = [c / L for c in a]
    for ref in ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)):
        d = sum(a[k] * ref[k] for k in range(3))
        if abs(d) < 0.9:
            u = [ref[k] - a[k] * d for k in range(3)]
            lu = math.sqrt(sum(c * c for c in u))
            u = [c / lu for c in u]
            v = [a[1] * u[2] - a[2] * u[1], a[2] * u[0] - a[0] * u[2], a[0] * u[1] - a[1] * u[0]]
            return u, v
    raise ValueError('axis')


def geo_prism(p0, p1, r, n):
    """正 n 棱柱（带两端 n 边形封口，导出时扇形三角化为 n-2 个三角），轴线 p0->p1，外接半径 r。
    三角数 4n-4：16 边 60、12 边 44、8 边 28、6 边 20、4 边 12。首顶点按 _perp_basis 放在轴线方向。双精度计算。"""
    p0 = [float(c) for c in p0]; p1 = [float(c) for c in p1]
    a = [p1[k] - p0[k] for k in range(3)]
    if math.sqrt(sum(c * c for c in a)) < EPS:
        raise ValueError('零长棱柱')
    u, v = _perp_basis(a)

    def _snap(c):
        """cos/sin 的 0、±1 取精确值。"""
        return 0.0 if abs(c) < 1e-12 else (math.copysign(1.0, c) if abs(abs(c) - 1) < 1e-12 else c)
    ring = [(_snap(math.cos(2 * math.pi * i / n)), _snap(math.sin(2 * math.pi * i / n))) for i in range(n)]
    off = [[r * c * u[k] + r * s_ * v[k] for k in range(3)] for c, s_ in ring]
    verts = [tuple(p0[k] + o[k] for k in range(3)) for o in off] + [tuple(p1[k] + o[k] for k in range(3)) for o in off]
    if abs(a[2]) / math.sqrt(sum(c * c for c in a)) > 0.999:
        # 竖柱：底 (n-1..0)、顶 (0..n-1)——她的 S84/G10 12 边、8 边檐柱封口三角化与此逐个相同（validate/round2 compare）
        faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    else:
        # 斜管（瓦垄）：封口环从下一个顶点起——底 (0, n-1..1)、顶 (1..n-1, 0)。导出器按环的起点做耳切三角化，
        # 这样封口三角形与她的 S84/G10 瓦垄 8 边、4 边封口相同（round2 tess/tess_probe.py：她的顶端起点在 45°、
        # 底端起点在 0°）。正脊、戗脊等其它斜件未核对，同样套用。
        faces = [(0,) + tuple(range(n - 1, 0, -1)), tuple(range(n + 1, 2 * n)) + (n,)]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return Geo(verts, faces)


def geo_round_box(p0, p1, r):
    """圆木 LOD2 替身：轴对齐时为边长 2r 的外接方盒（她的 LOD2 柱、正脊都这样换，轮廓略胖）；
    轴线倾斜时退成 4 边菱形管（她的扫掠件 LOD2 做法）。"""
    p0, p1 = [float(c) for c in p0], [float(c) for c in p1]
    a = [p1[k] - p0[k] for k in range(3)]
    L = math.sqrt(sum(c * c for c in a))
    al = [c / L for c in a]
    for k in range(3):
        if abs(abs(al[k]) - 1.0) < 1e-6:
            lo = [min(p0[i], p1[i]) - (0 if i == k else r) for i in range(3)]
            hi = [max(p0[i], p1[i]) + (0 if i == k else r) for i in range(3)]
            return geo_box(lo, hi)
    return geo_prism(p0, p1, r, 4)


def geo_extrude(poly, origin, U, V, W, d0, d1):
    """把平面多边形 poly=[(u,v)...]（U、V 为平面两轴，W 为挤出方向）从 d0 挤到 d1。
    她的门框（10 点 Π 形）、带门洞的上层墙、山墙五边形、城台立面都用「画轮廓 + 挤出」一次成形，不做布尔。"""
    O, U, V, W = Vector(origin), Vector(U), Vector(V), Vector(W)      # 仅用于判方向；坐标在下面用双精度算
    # 保证 (U, V) 中多边形逆时针，且 U x V 与 W 同向，使封口法线朝外
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    if area < 0:
        poly = poly[::-1]
    if U.cross(V).dot(W) < 0:
        poly = [(p[0], p[1]) for p in poly[::-1]]
        U, V = V, U
        poly = [(p[1], p[0]) for p in poly]
    n = len(poly)
    o_, u_, v_, w_ = [list(map(float, X)) for X in (origin, U, V, W)]

    def pt(p, d):
        """局部 (u, v, d) -> 世界坐标（双精度）。"""
        return tuple(o_[k] + u_[k] * p[0] + v_[k] * p[1] + w_[k] * d for k in range(3))
    verts = [pt(p, d0) for p in poly] + [pt(p, d1) for p in poly]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return Geo(verts, faces)


def geo_slab_gable(x0, x1, yf, yb, yr, z_eave_f, z_eave_b, z_ridge, t):
    """悬山屋面板：倒 V 形 6 点截面（前檐、脊、后檐各上下两点，上下为竖直厚度 t）沿 X 挤出，两端平切。
    12 顶点 / 20 三角（kaiyang 实测 12U/20T）。z_* 为板底标高。
    两端面各做成两个四边形（前坡 0-1-4-5、后坡 1-2-3-4，序号按截面点），不是一个六边形：她的 S84/G10 板端三角
    (0,1,4)(0,4,5)(1,2,3)(1,3,4) 就是这两块四边形按首点对角线切开的结果（round2 tess/slab_probe.py）。"""
    sec = [(yf, z_eave_f), (yr, z_ridge), (yb, z_eave_b), (yb, z_eave_b + t), (yr, z_ridge + t), (yf, z_eave_f + t)]
    verts = [(x0, y, z) for y, z in sec] + [(x1, y, z) for y, z in sec]
    faces = [(0, 5, 4, 1), (1, 4, 3, 2),                       # x0 端（法线 -X）
             (6, 7, 10, 11), (7, 8, 9, 10)]                    # x1 端（法线 +X）
    for i in range(6):
        j = (i + 1) % 6
        # 板底三面（前坡底、后坡底、后檐立边：i=0,1,2）从 i 起，板顶三面（i=3,4,5）从 j 起——
        # 这样导出器按首点切出的对角线与她的 S84/G10 板面三角逐个相同（round2 tess，三档 60/60）
        faces.append((i, j, 6 + j, 6 + i) if i < 3 else (j, 6 + j, 6 + i, i))
    return Geo(verts, faces)


def slab_breaks(x0, x1, splits=None):
    """屋面板分段点：[x0, *splits, x1]（splits 落在板内、升序去重）。她的住屋/店铺板是 3 段，
    断在檐柱外皮（S84 x=±3.70 = 柱心 ±3.6 + r0.1；G10 ±4.70），三档 LOD 都保留 60 三角（validate/round1 review_lod）。"""
    xs = sorted({round(float(s), 6) for s in (splits or ()) if x0 + EPS < s < x1 - EPS})
    return [x0] + xs + [x1]


def geo_slab_hip(x0, x1, y0, y1, xr0, xr1, yr, z_eave, z_ridge, t):
    """庑殿（四阿）屋面板：与悬山板同为 12 顶点（檐口矩形 4 点 + 脊端 2 点，上下两层），正脊两端缩短到 xr0..xr1。
    20 三角（pingcheng/biyong/deyang 实测 12 点）。"""
    b = [(x0, y0, z_eave), (x1, y0, z_eave), (x1, y1, z_eave), (x0, y1, z_eave), (xr0, yr, z_ridge), (xr1, yr, z_ridge)]
    v = b + [(p[0], p[1], p[2] + t) for p in b]
    faces = [
        (6, 7, 11, 10), (8, 9, 10, 11), (9, 6, 10), (7, 8, 11),       # 上表面：前、后梯形，左、右三角
        (0, 4, 5, 1), (2, 5, 4, 3), (3, 4, 0), (1, 5, 2),             # 下表面
        (0, 1, 7, 6), (1, 2, 8, 7), (2, 3, 9, 8), (3, 0, 6, 9),       # 檐口四周立边
    ]
    return Geo(v, faces)


def geo_frustum(x0, y0, x1, y1, z0, z1, inset):
    """收分台体（8 顶点四棱台）：底 x0..x1 × y0..y1，顶四边各内收 inset。阙台 1:6、jin 城台前脸 1:11 用此法。"""
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0 + inset, y0 + inset, z1), (x1 - inset, y0 + inset, z1), (x1 - inset, y1 - inset, z1), (x0 + inset, y1 - inset, z1)]
    return geo_hexa(c)


# --------------------------------------------------------------------------------------------
# 3. 组件与 LOD 规则
# --------------------------------------------------------------------------------------------
def _v(p):
    """把坐标转成保留 6 位小数的 float 列表（组件记录用，便于 JSON 化）。"""
    return [round(float(x), 6) for x in p]


def component_geometry(comp, lod, profile):
    """按她的 LOD 规则生成某组件在 lod 档的几何；返回 Geo 或 None（该档删除）。

    规则（comp['lod']）：
      keep      各档相同（夯土、梁枋盒、屋面板、门框……）
      round     圆木：LOD0 原边数 -> LOD1 8 边（profile.round_lod1）-> LOD2 2r 外接方盒
      ridge     正脊：同 round
      hip_ridge 戗脊/垂脊：LOD0 -> 8 边 -> LOD2 删除
      sweep     折线扫掠件（叉手）：LOD0 -> 8 边 -> 4 边菱形
      rib       瓦垄：LOD1 按 index 每 k 根留 1（k=profile.rib_keep_every，以中间一根为基准对称抽）且截面
                改 profile.rib_sides_lod1 边；LOD2 删除
      thin      小木件（窗棂、檩条）：LOD1 每 k 根留 1（以中间为基准），LOD2 删除
      lod01     LOD0、LOD1 保留，LOD2 删除（门扇横带、小矮柱）
      lod0      只在 LOD0（门钉、纴木头、柱头小块）
    params['lod_set'] = [..]：组件只出现在列出的档（round2：住屋瓦垄 LOD0 一套、LOD1 按段重排的另一套），
              此时 rib/thin 不再做隔根抽取。
    """
    rule = comp['lod']
    P = comp['params']
    kind = comp['kind']
    prof = LOD_PROFILES[profile]
    if 'lod_set' in P and lod not in P['lod_set']:
        return None
    if rule == 'lod0' and lod > 0:
        return None
    if rule in ('lod01', 'hip_ridge', 'rib', 'thin') and lod >= 2:
        return None
    if rule in ('rib', 'thin') and lod == 1 and 'lod_set' not in P:
        k = prof['rib_keep_every'] if rule == 'rib' else prof['thin_keep_every']
        idx, n = P.get('index', 0), P.get('count', 1)
        mid = (n - 1) // 2
        if (idx - mid) % k != 0:
            return None
    if kind == 'mesh':
        return Geo(P['verts'], P['faces'])
    if kind == 'box':
        return geo_box(P['lo'], P['hi'])
    if kind == 'prism':
        g = _prism_lod(P, rule, lod, prof)
        cap = P.get('cap')
        if cap is not None:      # 柱顶斜切贴屋面板底：顶端一圈顶点 z = a + bx*x + by*y（S84/G10 frontpost_sloped_cap）
            ztop = P['p1'][2]
            g = Geo([(v[0], v[1], cap[0] + cap[1] * v[0] + cap[2] * v[1]) if abs(v[2] - ztop) < 1e-6 else tuple(v)
                     for v in g.verts], g.faces)
        return g
    if kind == 'tube':      # 折线：每段一根带封口的棱柱，折点处两段只在折轴上共点（她的瓦垄、叉手做法）
        pts = P['points']
        n0 = P['sides']
        n = n0 if lod == 0 else (prof['rib_sides_lod1'] if rule == 'rib' else min(n0, 8))
        if lod >= 2 and rule == 'sweep':
            n = 4
        g = Geo()
        for i in range(len(pts) - 1):
            g.add(geo_prism(pts[i], pts[i + 1], P['r'], n))
        return g
    raise ValueError(f'未知组件种类 {kind}')


def _prism_lod(P, rule, lod, prof):
    """棱柱组件在 lod 档的几何（component_geometry 的棱柱分支）。
    P['lod2_shape'] = 'diamond' 时圆木 LOD2 用 4 边菱形（顶点在轴向上，包围盒仍 2r），而不是 2r 方盒：
    她的 S84-LOD2、G10-LOD2 檐柱就是这样（顶点 (x±0.1, z) 与 (x, z±0.1)，12 三角；validate/round1/measure）。"""
    n0 = P['sides']
    if lod == 0:
        n = n0
    elif rule == 'rib':
        n = prof['rib_sides_lod1']
    elif rule in ('round', 'ridge', 'hip_ridge', 'sweep'):
        n = min(n0, prof['round_lod1'] if rule != 'ridge' else prof['ridge_lod1'])
    else:
        n = n0
    if lod >= 2 and rule in ('round', 'ridge'):
        if P.get('lod2_shape') == 'diamond':
            return geo_prism(P['p0'], P['p1'], P['r'], 4)
        return geo_round_box(P['p0'], P['p1'], P['r'])
    if lod >= 2 and rule == 'sweep':
        n = 4
    return geo_prism(P['p0'], P['p1'], P['r'], n)


def component_world_geo(comp, lod, profile):
    """组件在世界坐标下的几何（单独节点的门扇按其铰点矩阵变换到世界）。"""
    g = component_geometry(comp, lod, profile)
    if g is None:
        return None
    if comp.get('node'):
        g = g.transformed(Matrix(comp['node']['matrix']))
    return g


class Assembly:
    """一个资产（一个 slug + 变体字母）的构件集合，负责建 LOD0 预览物体、派生 LOD、导出。

    slug: 资产短名（小写、连字符，如 'kaiyang'）；variant: 变体字母（'A'、'K'…）。
    evidence: 写进节点 extras 的证据句，按她的格式以等级开头，如 'C trial hut, not a surveyed building'。
    profile: LOD 规则档 'house' | 'hall' | 'gate'（见 LOD_PROFILES）。
    extras: 额外写进每个节点 extras 的键（如 {'version': '1.0', 'semantic_group': ...}）。
    naming: NAMING 预设名（'default' | 'market' | 'house_types'）或同结构 dict；决定节点名、网格名、文件名、extras 键序。
    prototype: 原型编号（'S84'、'G10'），market / house_types 写法用；modules: {材料: module 名}，
               如 {'earth': 'body', 'timber': 'frontframe_counter', 'tile': 'roof_left'}（S84）。
    """

    def __init__(self, slug, variant='A', evidence='C reconstruction trial, not a surveyed building', profile='house',
                 extras=None, make_objects=True, naming='default', prototype=None, modules=None):
        """建资产：校验 slug，准备 LOD0 预览集合 <slug>-<V>-LOD0-parts。"""
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
            raise ValueError('slug 只用小写字母、数字、连字符')
        self.slug, self.variant, self.evidence, self.profile = slug, variant, evidence, profile
        self.naming = dict(NAMING[naming]) if isinstance(naming, str) else dict(naming)
        self.prototype = prototype
        self.modules = dict(modules or {})
        if ('{proto}' in self.naming['node'] + self.naming['mesh'] + self.naming['file']) and not prototype:
            raise ValueError('该命名写法需要 prototype=（如 S84、G10）')
        self.extras = dict(extras or {})
        self.components = []
        self.make_objects = make_objects
        self.prefix = f'{slug}-{variant}'
        self.collection = None
        if make_objects:
            name = f'{self.prefix}-LOD0-parts'
            self.collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
            if self.collection.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(self.collection)

    # ---- 底层登记 ----------------------------------------------------------------------
    def add(self, kind, mat, params, lod='keep', name=None, tags=(), node=None):
        """登记一个组件并（可选）生成 LOD0 预览物体。kind: 'box'|'prism'|'tube'|'mesh'；mat: PALETTE 键；
        lod: 见 component_geometry；tags: 检查用语义标签（'wall'、'slab'、'rib'、'leaf'…）；
        node: 单独成节点的信息 {'name': 'leaf_0_L', 'matrix': 4x4 列表, 'extras': {...}}（如可开合门扇）。"""
        if mat not in PALETTE:
            raise KeyError(mat)
        comp = dict(id=len(self.components), name=name or f'{kind}{len(self.components):03d}', kind=kind, mat=mat,
                    params=params, lod=lod, tags=list(tags), node=node)
        first = min(params.get('lod_set', [0]))
        g = component_world_geo(comp, first, self.profile)
        if g is None or not g.faces:
            raise ValueError(f'组件 {comp["name"]} 在 LOD{first} 没有几何')
        self.components.append(comp)
        if self.make_objects:
            obj = _make_object(f'{self.prefix}~{comp["name"]}', g, material_for(mat, 0), self.collection)
            obj['ly'] = json.dumps(comp, ensure_ascii=False)
            comp['_obj'] = obj.name
            if first > 0:      # 只在 LOD1 以上出现的组件（住屋 LOD1 重排瓦垄）：物体隐藏，只为 assembly_from_objects 留记录
                obj.hide_viewport = obj.hide_render = True
                obj['ly_lod_only'] = first
        return comp

    def add_geo(self, geo, mat, lod='keep', name=None, tags=(), orient=True):
        """登记一块已算好的几何（mesh 组件，默认各 LOD 不变）。登记前逐个闭合块重算法线朝外（orient=False 时
        原样登记——几何已保证朝外、且面的起点决定导出对角线时用，如屋面板）。"""
        if orient:
            geo = _oriented(geo)
        return self.add('mesh', mat, {'verts': [_v(p) for p in geo.verts], 'faces': [list(f) for f in geo.faces]},
                        lod=lod, name=name, tags=tags)

    # ---- 构件：盒、柱、梁 ---------------------------------------------------------------------
    def box(self, lo, hi, mat, lod='keep', name=None, tags=()):
        """轴对齐方盒构件（梁、枋、板、墩台、踏步层、柱础）。12 三角，各 LOD 不变（除非 lod 另指定）。"""
        return self.add('box', mat, {'lo': _v(lo), 'hi': _v(hi)}, lod=lod, name=name, tags=tags)

    def column(self, x, y, z0, z1, d=0.32, sides=16, base=True, base_ratio=1.6, base_h=0.2, base_mat='earth', name=None,
               tags=('column',), cap_roof=None, lod2_shape=None):
        """木柱：正 n 棱柱（殿堂、城门 16 边，住屋、复道 12 边），不做柱础收分卷杀。base=True 时柱下加方础
        （边长 base_ratio*d，高 base_h，earth 材质——她的柱础都并在 earth 网格里），柱身从础顶起。
        LOD：16/12 -> 8 -> 2r 外接方盒；础不变。返回 (柱组件, 础组件或 None)。"""
        nm = name or f'column{len(self.components):03d}'
        bc = None
        if base:
            s = base_ratio * d / 2
            bc = self.box((x - s, y - s, z0), (x + s, y + s, z0 + base_h), base_mat, name=nm + '_base', tags=('base',))
            z0 = z0 + base_h
        P = {'p0': _v((x, y, z0)), 'p1': _v((x, y, z1 if z1 is not None else z0 + 1.0)), 'r': d / 2, 'sides': sides}
        if lod2_shape:
            P['lod2_shape'] = lod2_shape
        if cap_roof is not None:
            # 柱顶斜切到屋面板底（她的 frontpost_sloped_cap）：在柱外接方内取板底平面，z1 参数被忽略，柱顶 = 板底
            r = d / 2
            za = cap_roof.bottom_z(x, y)
            bx = (cap_roof.bottom_z(x + r, y) - cap_roof.bottom_z(x - r, y)) / (2 * r)
            by = (cap_roof.bottom_z(x, y + r) - cap_roof.bottom_z(x, y - r)) / (2 * r)
            P['cap'] = [za - bx * x - by * y, bx, by]      # 不取整：柱顶标高与她的 float32 逐位相同（3.2738776）
            P['p1'] = _v((x, y, max(cap_roof.bottom_z(x + sx * r, y + sy * r) for sx in (-1, 1) for sy in (-1, 1))))
        c = self.add('prism', 'timber', P, lod='round', name=nm, tags=tags)
        return c, bc

    def post(self, x, y, z0, z1, d=0.20, sides=12, name=None, cap_roof=None, lod2_shape=None):
        """住屋檐柱：12 边 Ø0.20、无础（H72 / G10 / S84 实测），立在地面上。
        柱在地坪板范围内时也从 z0=0 起、穿过地坪（她的 S84 柱底 y=0.000，地坪顶 0.22；ALLOWED_INTERSECT 已放行 post/floor），
        不要从地坪顶起。
        cap_roof=roof：柱顶斜切贴合屋面板底（G10/S84 frontpost_sloped_cap，z1 忽略）；
        lod2_shape='diamond'：LOD2 用 4 边菱形（G10/S84 LOD2 实测），缺省为 2r 方盒。"""
        return self.column(x, y, z0, z1, d=d, sides=sides, base=False, name=name or f'post{len(self.components):03d}',
                           tags=('post',), cap_roof=cap_roof, lod2_shape=lod2_shape)[0]

    def beam(self, p0, p1, w, h, mat='timber', lod='keep', name=None, tags=('beam',), top=None):
        """梁/枋/檩（方木）：沿 X 或 Y 的轴对齐盒，截面 w（水平）× h（竖直），p0/p1 为两端底面中线点。
        top 给定时覆盖顶标高（用于把梁顶抵到屋面板底，见 beam_under_roof）。各 LOD 不变。"""
        p0, p1 = Vector(p0), Vector(p1)
        z0 = p0.z
        z1 = top if top is not None else z0 + h
        if abs(p0.y - p1.y) < EPS:      # 沿 X
            lo = (min(p0.x, p1.x), p0.y - w / 2, z0); hi = (max(p0.x, p1.x), p0.y + w / 2, z1)
        elif abs(p0.x - p1.x) < EPS:    # 沿 Y
            lo = (p0.x - w / 2, min(p0.y, p1.y), z0); hi = (p0.x + w / 2, max(p0.y, p1.y), z1)
        else:
            raise ValueError('方梁只沿 X 或 Y')
        return self.box(lo, hi, mat, lod=lod, name=name, tags=tags)

    def beam_under_roof(self, roof, p0, p1, w, mat='timber', name=None, tags=('beam',)):
        """把方梁顶抵到屋面板底：在梁顶面上取 9×3 网格点求板底标高，梁顶 = 最高值，于是梁与板之间不留缝，
        较低处埋入板内（她的 H72 檐枋顶 2.989 正好等于内侧板底，外侧埋入 0.135）。埋入深度超过板厚 90% 时报错。
        p0/p1 为两端底面中线点（底标高 = 柱顶）。"""
        p0, p1 = Vector(p0), Vector(p1)
        if abs(p0.y - p1.y) < EPS:
            xa, xb, ya, yb = min(p0.x, p1.x), max(p0.x, p1.x), p0.y - w / 2, p0.y + w / 2
        else:
            xa, xb, ya, yb = p0.x - w / 2, p0.x + w / 2, min(p0.y, p1.y), max(p0.y, p1.y)
        zs = [roof.bottom_z(xa + (xb - xa) * i / 8, ya + (yb - ya) * k / 2) for i in range(9) for k in range(3)]
        top, low = max(zs), min(zs)
        if top - low > 0.9 * roof.t:
            raise ValueError(f'{name}: 梁顶埋入板内 {top - low:.3f} m，超过板厚 {roof.t}，会穿出屋面；请缩短梁或加厚板')
        if top - p0.z < 0.05:
            raise ValueError('梁高不足：柱顶离屋面板底太近')
        return self.beam(p0, p1, w, top - p0.z, mat=mat, name=name, tags=tags, top=top)

    def round_beam(self, p0, p1, d, sides=12, name=None, tags=('beam',)):
        """圆木檩/梁（灵台、太学 LOD1 的 8/12 边圆檩做法），LOD 同 round。"""
        return self.add('prism', 'timber', {'p0': _v(p0), 'p1': _v(p1), 'r': d / 2, 'sides': sides}, lod='round',
                        name=name, tags=tags)

    def sweep(self, points, d, sides=16, mat='timber', name=None, tags=('sweep',)):
        """折线扫掠圆木（叉手/人字斜梁）：每段一根带封口棱柱，折点不斜切，只在折轴上共点。
        LOD：16 -> 8 -> 4 边菱形（kaiyang 叉手 120/56/24 三角）。"""
        return self.add('tube', mat, {'points': [_v(p) for p in points], 'r': d / 2, 'sides': sides}, lod='sweep',
                        name=name, tags=tags)

    def ludou(self, x, y, z, size=0.78, h=0.24, lod='keep', name=None):
        """栌斗：柱顶方块（辟雍 0.78×0.78×0.24，timber）。她的模型里没有出跳斗栱，只到这一块。
        辟雍 LOD2 删了栌斗，柱顶与圈梁之间露 0.24 缝；本库默认各档保留（每块 12 三角），需要照辟雍时传 lod='lod01'。"""
        s = size / 2
        return self.box((x - s, y - s, z), (x + s, y + s, z + h), 'timber', lod=lod, name=name, tags=('ludou',))

    # ---- 构件：台基、地坪、踏步 ---------------------------------------------------------------
    def platform(self, x0, y0, x1, y1, z0, z1, taper=0.0, mat='earth', name=None):
        """台基 / 夯土台：taper=0 为直角盒（城门墩台、殿台），taper>0 为四边内收的收分台（阙台 1:6）。各 LOD 不变。"""
        if taper <= 0:
            return self.box((x0, y0, z0), (x1, y1, z1), mat, name=name or 'platform', tags=('platform',))
        return self.add_geo(geo_frustum(x0, y0, x1, y1, z0, z1, taper * (z1 - z0)), mat, name=name or 'platform',
                            tags=('platform',))

    def floor_slab(self, x0, y0, x1, y1, h=0.22, z0=0.0, name='floor'):
        """住屋室内地坪：earth 实心板，厚 0.22（H72 / G10），墙体立在板顶。"""
        return self.box((x0, y0, z0), (x1, y1, z0 + h), 'earth', name=name, tags=('floor',))

    def ground_patch(self, x0, y0, x1, y1, top=0.04, thickness=0.2, mat='earth', name='ground'):
        """展示用局部地面补丁：顶面 +0.04、厚 0.2（kaiyang/yong/pingcheng ground：y -0.16 -> +0.04）。
        她把它放在单独的 *-ground-LOD*.glb 里；建筑本体仍落在 z=0。"""
        return self.box((x0, y0, top - thickness), (x1, y1, top), mat, name=name, tags=('ground',))

    def steps(self, u0, u1, face, z0, z1, direction=-1, axis='Y', riser_max=0.15, going=0.32, mat='earth', name='step'):
        """直跑实心踏步，按总高 z1-z0 自动分级：级数 n = ceil(H / riser_max)，踢面 = H/n，踏面 = going。
        做法：每级一块盒，第 i 层从第 i 级前沿一直伸到台基立面（层层相叠，不悬空、无内部重叠）。
        axis='Y'：踏步沿 Y 方向伸出（台基立面在 y=face，direction=-1 表示向 -Y 即正面伸出）；u0..u1 为 X 向宽度。
        axis='X'：踏步沿 X 伸出，u0..u1 为 Y 向宽度。默认 riser 0.15 / going 0.32 取宫殿家族（deyang 12 级 0.15）。
        返回组件列表。"""
        H = z1 - z0
        n = max(1, math.ceil(H / riser_max - 1e-9))
        r = H / n
        out = []
        for i in range(n):
            # 第 i 层（自下而上）：高度 z0+i*r .. z0+(i+1)*r，前沿距立面 (n-i)*going
            near, far = face, face + direction * (n - i) * going
            a, b = sorted((near, far))
            if axis == 'Y':
                lo, hi = (u0, a, z0 + i * r), (u1, b, z0 + (i + 1) * r)
            else:
                lo, hi = (a, u0, z0 + i * r), (b, u1, z0 + (i + 1) * r)
            out.append(self.box(lo, hi, mat, name=f'{name}{i:02d}', tags=('step',)))
        return out

    # ---- 构件：墙、门、窗 -----------------------------------------------------------------
    def _wall_map(self, axis, face, inward):
        """返回墙面局部坐标 (u 沿墙, w 进深, z 高) -> 世界坐标的映射函数。"""
        if axis == 'X':
            return lambda u, w, z: (u, face + inward * w, z)
        return lambda u, w, z: (face + inward * w, u, z)

    def wall(self, axis, u0, u1, face, t, z0, z1, openings=(), inward=1, mat='earth', name='wall', tags=('wall',), band=False):
        """墙段（可开门窗洞）：沿 axis（'X' 或 'Y'）从 u0 到 u1，外皮在 face，厚 t 向 inward（+1/-1）一侧。
        openings = [(ua, ub, za, zb), ...]：洞口沿墙的范围与上下标高（门洞 za 取地坪顶）。
        做法同她：不做布尔，按洞口把墙切成「墙垛 + 窗下墙 + 洞口上方过梁墙」若干相接的盒，并成一个组件。
        z1 可为 (z_外皮, z_内皮)：墙顶做成斜面贴合屋面板底。注意：她的住屋/店铺檐墙都是平顶、与板底留缝
        （S84、G10、H72），住屋/店铺请用 eave_wall；斜顶只在需要封死的场合（院墙压顶下、殿墙）由作者自定。各 LOD 不变。
        band=True（她的 G10 前后墙做法）：洞口两侧墙垛只到洞顶，洞顶以上是一条通长的墙带（洞顶 -> 墙顶，沿墙全长），
        即「墙垛 + 窗下墙 + 通长墙带」；要求所有洞口顶标高相同。G10 实测：墙带 x ±4.72、y 2.30 -> 3.20，墙垛 0.22 -> 2.30
        （round1/measure/g10_earth_verts.txt）。H72 等多洞口墙是否也如此未量到。"""
        f = self._wall_map(axis, face, inward)
        zt = z1 if isinstance(z1, (tuple, list)) else (z1, z1)
        g = Geo()

        def block(ua, ub, za, zb_pair):
            """墙段里的一块六面体（u 范围 × 全墙厚 × z 范围，顶可为斜面）。"""
            zo, zi = zb_pair
            c = [f(ua, 0, za), f(ub, 0, za), f(ub, t, za), f(ua, t, za), f(ua, 0, zo), f(ub, 0, zo), f(ub, t, zi), f(ua, t, zi)]
            g.add(_oriented(geo_hexa(_reorder_any(c))))

        ops = sorted(openings)
        cur = u0
        if band and ops:
            heads = {round(o[3], 6) for o in ops}
            if len(heads) != 1:
                raise ValueError(f'band=True 要求洞口顶标高相同：{sorted(heads)}')
            zh = ops[0][3]
            if zh > min(zt) - EPS:
                raise ValueError('洞口顶不低于墙顶，无法做通长墙带')
            for (ua, ub, za, zb) in ops:
                if ua < cur - EPS or ub > u1 + EPS:
                    raise ValueError(f'洞口 {ua}..{ub} 越界或重叠')
                if ua - cur > EPS:
                    block(cur, ua, z0, (zh, zh))
                if za - z0 > EPS:
                    block(ua, ub, z0, (za, za))
                cur = ub
            if u1 - cur > EPS:
                block(cur, u1, z0, (zh, zh))
            block(u0, u1, zh, zt)
            return self.add_geo(g, mat, name=name, tags=tags)
        for (ua, ub, za, zb) in ops:
            if ua < cur - EPS or ub > u1 + EPS:
                raise ValueError(f'洞口 {ua}..{ub} 越界或重叠')
            if ua - cur > EPS:
                block(cur, ua, z0, zt)
            if za - z0 > EPS:
                block(ua, ub, z0, (za, za))
            if (min(zt) - zb) > EPS:
                block(ua, ub, zb, zt)
            elif zb < max(zt) - EPS:
                raise ValueError('洞口顶高于墙顶')
            cur = ub
        if u1 - cur > EPS:
            block(cur, u1, z0, zt)
        return self.add_geo(g, mat, name=name, tags=tags)

    def eave_wall(self, roof, axis, u0, u1, face, t, z0, openings=(), inward=1, mat='earth', name='eave_wall',
                  tags=('wall',), band=True):
        """住屋/店铺的檐墙（前后墙）：墙顶 **平** 在檐口线板底标高 roof.z_eave，不贴坡。
        她的做法：S84 后墙顶平 3.000（板底在墙外皮 3.202、内皮 3.328），G10 前后墙顶平 3.200（板底 3.402 / 3.528），
        墙顶与板底之间留 0.20–0.33 m 的暗缝，街面视角看得到一道深色带（validate/round1 review_geo）。"""
        return self.wall(axis, u0, u1, face, t, z0, roof.z_eave, openings=openings, inward=inward, mat=mat, name=name,
                         tags=tags, band=band)

    def gable_wall(self, axis, u0, u1, face, t, z0, z_end0, z_end1, u_peak, z_peak, inward=1, mat='earth', name='gable',
                   tags=('gable', 'wall'), z_shoulder=None):
        """山墙：五边形轮廓 (u0,z0)(u1,z0)(u1,z_end1)(u_peak,z_peak)(u0,z_end0) 沿墙厚挤出，10 顶点 / 16 三角。
        山尖斜边应等于屋面板底标高。
        z_shoulder 给定时（住屋/店铺取 roof.z_eave）按她的做法分两块：墙身盒 z0..z_shoulder（12 三角）+ 山尖五边形
        (u0,z_sh)(u1,z_sh)(u1,z_end1)(u_peak,z_peak)(u0,z_end0)（16 三角），共 28 三角 / 54 导出顶点；两块在 z_shoulder
        处有一对重合的内部面（同一组件，check_coplanar 不报）。证据：S84 earth 80 三角 = 地坪 12 + 后墙 12 + 山墙 2×28，
        山墙两面都有 y=3.000 与 3.202 两圈顶点；G10 同（3.2 / 3.402）。类型门山墙 16U/28T 也是这一式。"""
        def ext(poly):
            """把 (u, z) 轮廓沿墙厚挤出。"""
            if axis == 'X':
                return geo_extrude(poly, (0, face, 0), (1, 0, 0), (0, 0, 1), (0, inward, 0), 0, t)
            return geo_extrude(poly, (face, 0, 0), (0, 1, 0), (0, 0, 1), (inward, 0, 0), 0, t)
        if z_shoulder is None:
            g = ext([(u0, z0), (u1, z0), (u1, z_end1), (u_peak, z_peak), (u0, z_end0)])
        else:
            if not (z0 < z_shoulder < min(z_end0, z_end1) + EPS):
                raise ValueError(f'z_shoulder {z_shoulder} 须在墙底 {z0} 与山尖起点 {min(z_end0, z_end1)} 之间')
            w0, w1 = sorted((face, face + inward * t))
            if axis == 'X':
                g = geo_box((min(u0, u1), w0, z0), (max(u0, u1), w1, z_shoulder))
            else:
                g = geo_box((w0, min(u0, u1), z0), (w1, max(u0, u1), z_shoulder))   # 墙身用 geo_box（对角线与她的盒相同）
            g.add(ext([(u0, z_shoulder), (u1, z_shoulder), (u1, z_end1), (u_peak, z_peak), (u0, z_end0)]))
        return self.add_geo(g, mat, name=name, tags=tags)

    def door_frame(self, axis, ua, ub, face, depth, z0, zb, jamb=0.08, head=0.08, inward=1, name='door_frame'):
        """门框：两框柱 + 门额连成一体的 10 点 Π 形轮廓，沿墙厚挤出（H72 门框 1.76×2.16、框料 0.08、深 0.28；
        kaiyang 框料 0.2、额 0.3）。ua..ub 为门洞外沿，z0 为门槛面（地坪顶），zb 为洞顶。净宽 = ub-ua-2*jamb。各 LOD 不变。"""
        hz = zb - head
        poly = [(ua, z0), (ua + jamb, z0), (ua + jamb, hz), (ub - jamb, hz), (ub - jamb, z0), (ub, z0), (ub, hz), (ub, zb),
                (ua, zb), (ua, hz)]
        if axis == 'X':
            g = geo_extrude(poly, (0, face, 0), (1, 0, 0), (0, 0, 1), (0, inward, 0), 0, depth)
        else:
            g = geo_extrude(poly, (face, 0, 0), (0, 1, 0), (0, 0, 1), (inward, 0, 0), 0, depth)
        return self.add_geo(g, 'timber', name=name, tags=('frame',))

    def door_leaf(self, hinge, width, height, t=0.06, angle_deg=0.0, axis='X', direction=1, inward=1, bands=None,
                  band_size=(0.05, 0.12), separate_node=None, name='leaf'):
        """门叶：方盒板（城门 0.14 厚，住屋/内门约 0.055-0.06），绕竖直铰轴转开。
        hinge    铰点 = 门叶底面、靠铰一侧、靠室内一面的角点（世界坐标）。
        关闭时门叶沿 axis（'X' 或 'Y'）的 direction（+1/-1）方向展开 width，厚度 t 朝室外（-inward）一侧。
        angle_deg 开启角：门叶向室内（inward 一侧）转开，90 = 垂直于墙面。
        bands    横带位置（门叶高度的比例列表；kaiyang 每扇 3 道 0.05×0.12，约 0.16/0.51/0.86 高），钉在室内一面，LOD2 删除。
        separate_node='leaf_0_L' 时门叶单独成节点（jin 做法：节点名 <slug>-<V>-leaf_0_L，原点 = 铰点，
        extras 写 hinge_axis_native / pivot_native / angle_range_deg / swing_sign），否则并入 static_timber（试做门做法）。
        返回组件列表。"""
        hinge = Vector(hinge)
        s_open = direction * inward * (1 if axis == 'X' else -1)
        R = Matrix.Rotation(math.radians(angle_deg) * s_open, 4, 'Z')
        M = Matrix.Translation(hinge) @ R

        def local_box(a0, a1, b0, b1, z0, z1):
            """a = 沿门宽（乘 direction），b = 厚度方向（乘 inward），返回局部坐标盒。"""
            A = sorted((a0 * direction, a1 * direction)); B = sorted((b0 * inward, b1 * inward))
            if axis == 'X':
                return geo_box((A[0], B[0], z0), (A[1], B[1], z1))
            return geo_box((B[0], A[0], z0), (B[1], A[1], z1))

        pieces = [(local_box(0, width, -t, 0, 0, height), 'keep', name, ('leaf',))]
        bw, bh = band_size
        for i, fz in enumerate(bands or ()):
            z = fz * height - bh / 2
            pieces.append((local_box(0.05, width - 0.05, 0, bw, z, z + bh), 'lod01', f'{name}_band{i}', ('leaf', 'band')))
        comps = []
        if separate_node:
            node = {'name': separate_node, 'matrix': [list(r) for r in M],
                    'extras': {'hinge_axis_native': [0, 0, 1], 'pivot_native': _v(hinge), 'angle_range_deg': [0, 90],
                               'swing_sign': s_open}}
            for g, rule, nm, tg in pieces:
                comps.append(self.add('mesh', 'timber', {'verts': [_v(p) for p in g.verts], 'faces': [list(f) for f in g.faces]},
                                      lod=rule, name=nm, tags=tg, node=node))
        else:
            for g, rule, nm, tg in pieces:
                comps.append(self.add_geo(g.transformed(M), 'timber', lod=rule, name=nm, tags=tg))
        return comps

    def window(self, axis, ua, ub, face, depth, za, zb, member=0.05, bars=3, bar=0.035, inward=1, name='window'):
        """直棂窗：窗框 = 两框 + 上下槛 4 根方木并成一件（H72 窗框 0.8×0.8、料 0.05、深 = 墙厚，48 三角，各 LOD 不变）；
        棂条 = bars 根 bar×bar 方棂居中立在下槛上（H72 3 根 0.035）。LOD1 以中间一根为基准隔根留，LOD2 全删。"""
        f = self._wall_map(axis, face, inward)
        g = Geo()
        for (a0, a1, b0, b1) in ((ua, ua + member, za, zb), (ub - member, ub, za, zb), (ua + member, ub - member, za, za + member),
                                 (ua + member, ub - member, zb - member, zb)):
            c = [f(a0, 0, b0), f(a1, 0, b0), f(a1, depth, b0), f(a0, depth, b0), f(a0, 0, b1), f(a1, 0, b1), f(a1, depth, b1), f(a0, depth, b1)]
            g.add(_oriented(geo_hexa(_reorder_any(c))))
        comps = [self.add_geo(g, 'timber', name=name + '_frame', tags=('frame',))]
        if bars:
            span = (ub - ua - 2 * member)
            for i in range(bars):
                uc = ua + member + span * (i + 1) / (bars + 1)
                wc = depth / 2
                c = [f(uc - bar / 2, wc - bar / 2, za + member), f(uc + bar / 2, wc - bar / 2, za + member),
                     f(uc + bar / 2, wc + bar / 2, za + member), f(uc - bar / 2, wc + bar / 2, za + member),
                     f(uc - bar / 2, wc - bar / 2, zb - member), f(uc + bar / 2, wc - bar / 2, zb - member),
                     f(uc + bar / 2, wc + bar / 2, zb - member), f(uc - bar / 2, wc + bar / 2, zb - member)]
                lo = tuple(min(p[k] for p in c) for k in range(3)); hi = tuple(max(p[k] for p in c) for k in range(3))
                comps.append(self.add('box', 'timber', {'lo': _v(lo), 'hi': _v(hi), 'index': i, 'count': bars}, lod='thin',
                                      name=f'{name}_bar{i}', tags=('bar',)))
        return comps

    # ---- 构件：屋面 -----------------------------------------------------------------------
    def roof_gable(self, x0, x1, y_front, y_back, z_eave, rise, t=0.13, ribs=None, ridge=None, name='roof', splits=None,
                   slab_name=None):
        """悬山屋面：板（每段 12 顶点 20 三角，tile）+ 瓦垄（可选）+ 正脊（可选）。
        x0..x1 为板两端（含出际），y_front < y_back 为前后檐口线，z_eave 为檐口处板底标高，rise 为板底脊高差，
        t 为板竖直厚度（住屋 0.13、城门 0.16、殿堂 0.12-0.18）。坡度 = rise / ((y_back-y_front)/2)。
        splits = [x, ...]：板沿 X 的分段点。住屋/店铺取檐柱外皮（柱心 ± r，S84 ±3.70、G10 ±4.70），得 3 段 60 三角，
        三档 LOD 都保留；瓦垄按段排（profile.rib_layout='segments'）。缺省 1 段（城门、殿堂）。
        每段一个组件，第一段名 slab_name（缺省 name+'_slab'；market / house_types 命名下取 'roof_left'，网格名
        = <原型>_<第一个组件名>），其余为 <slab_name>_seg<i>。
        ribs = dict(d=0.11, pitch=0.28, lift=0.02, inset=0.06, sides=8)：每坡一根根带封口 8 边细管，管心在板顶面上方
        lift（kaiyang 0.02），从檐口（内收 inset）直到脊线，前后两坡在脊线上共点（与她的连续瓦垄同形）。
        ridge = dict(d=0.18, sides=16, lift=0.04)：正脊圆管，管心比板脊顶高 lift，全长同板（kaiyang r0.09 高出 0.04）。
        返回 Roof 对象（可查板顶/板底标高；roof.segments = [(a, b), ...]）。"""
        yr = (y_front + y_back) / 2
        roof = Roof('gable', x0, x1, y_front, y_back, z_eave, rise, t, yr=yr)
        br = slab_breaks(x0, x1, splits)
        roof.segments = list(zip(br[:-1], br[1:]))
        sn = slab_name or name + '_slab'
        for i, (a, b) in enumerate(roof.segments):
            self.add_geo(geo_slab_gable(a, b, y_front, y_back, yr, z_eave, z_eave, z_eave + rise, t), 'tile',
                         name=sn if i == 0 else f'{sn}_seg{i}', tags=('slab',), orient=False)
        if ribs:
            self._gable_ribs(roof, ribs, name)
        if ridge:
            self._ridge(roof, ridge, x0, x1, name)
        return roof

    def _rib_xs(self, a, b, pitch, margin):
        """在 a..b 之间按 pitch 等距排瓦垄（两端各留 margin），整体居中；返回位置列表（'even' 排法，殿堂/城门）。"""
        w = b - a - 2 * margin
        n = max(1, int(math.floor(w / pitch + 1e-9)) + 1)
        c = (a + b) / 2
        return [c + (i - (n - 1) / 2) * pitch for i in range(n)]

    @staticmethod
    def rib_xs_segments(segments, pitch=0.28, divisor=1):
        """'segments' 排法（她的住屋/店铺）：每段 w 排 n = floor(w/pitch) 根（divisor=2 时 LOD1 取 max(1, n//2)），
        段内均分居中：x_i = a + (i+0.5)·w/n。pitch 0.28 复现她 S84/G10 全部 6 段根数（0.75→2、7.4→26、9.4→33）；
        (0.2765, 0.2846] 内任何值都能复现，0.28 是推断，不是量到的值。
        S84 心距 0.375 / 0.2846，最外一根离板端 0.1875；LOD1 心 ±4.075、中段 0.5692（validate/round1 orig_parts.txt）。"""
        out = []
        for a, b in segments:
            w = b - a
            n = max(1, int(math.floor(w / pitch + 1e-9)))
            if divisor > 1:
                n = max(1, n // divisor)
            out.extend(a + (i + 0.5) * w / n for i in range(n))
        return out

    def _gable_ribs(self, roof, rb, name):
        """悬山前后两坡的瓦垄：每坡每列一根 8 边管，从檐口（内收 inset）到脊线，管心比板顶高 lift。
        排法按 profile：'segments' 逐板段排，LOD1 'relay' 逐段重排一半根数（单独一套只在 LOD1 出现的组件，
        LOD0 那套标 lod_set=[0]）；'even' 全长等距、LOD1 隔根抽。rb['xs'] 给定时直接用（LOD1 仍按 profile 处理）。"""
        prof = LOD_PROFILES[self.profile]
        d, pitch = rb.get('d', 0.11), rb.get('pitch', DIMS['house']['rib_pitch'] if prof['rib_layout'] == 'segments' else 0.29)
        lift, inset, sides = rb.get('lift', 0.02), rb.get('inset', 0.0), rb.get('sides', 8)
        margin = rb.get('margin', max(0.15, 0.6 * pitch))
        layout = rb.get('layout', prof['rib_layout'])
        segs = getattr(roof, 'segments', None) or [(roof.x0, roof.x1)]
        if rb.get('xs'):
            sets = [(rb['xs'], None)]
        elif layout == 'segments':
            xs0 = self.rib_xs_segments(segs, pitch)
            if prof['rib_lod1'] == 'relay':
                sets = [(xs0, [0]), (self.rib_xs_segments(segs, pitch, divisor=2), [1])]
            else:
                sets = [(xs0, None)]
        else:
            sets = [(self._rib_xs(roof.x0, roof.x1, pitch, margin), None)]
        for xs, lod_set in sets:
            self._gable_rib_set(roof, rb, name, xs, lod_set, d, lift, inset, sides)

    def _gable_rib_set(self, roof, rb, name, xs, lod_set, d, lift, inset, sides):
        """_gable_ribs 的一组瓦垄（一套 x 位置，可限定只在 lod_set 档出现）。"""
        tag = '' if lod_set is None else f'_l{lod_set[0]}'
        # round1 验证补（缺省不变）：住屋/店铺瓦垄（G10、S84）不在脊线相会，而是各停在脊线前 ridge_gap=0.07；
        # 端点高度按「檐口板顶 + lift」「脊线板顶 + lift_ridge」取（lift_ref='edge'，两者都是 0.05），
        # 所以管身比板面略陡，上端离板 0.08、在脊上两排管头鼓起一道「假脊」。实测见 validate/round1/measure。
        gap, lift_ref = rb.get('ridge_gap', 0.0), rb.get('lift_ref', 'point')
        lift_r = rb.get('lift_ridge', lift)
        for side, (ya, yb) in (('f', (roof.y0 + inset, roof.yr - gap)), ('b', (roof.y1 - inset, roof.yr + gap))):
            for i, x in enumerate(xs):
                if lift_ref == 'edge':
                    ye = roof.y0 if side == 'f' else roof.y1
                    p0 = (x, ya, roof.top_z(x, ye) + lift); p1 = (x, yb, roof.top_z(x, roof.yr) + lift_r)
                else:
                    p0 = (x, ya, roof.top_z(x, ya) + lift); p1 = (x, yb, roof.top_z(x, yb) + lift_r)
                P = {'p0': _v(p0), 'p1': _v(p1), 'r': d / 2, 'sides': sides, 'index': i, 'count': len(xs)}
                if lod_set is not None:
                    P['lod_set'] = list(lod_set)
                self.add('prism', 'tile', P, lod='rib', name=f'{name}_rib{side}{i:03d}{tag}', tags=('rib',))

    def _ridge(self, roof, rd, xa, xb, name):
        """正脊：沿 X 的圆管，管心比板脊顶高 lift，LOD 规则 ridge。"""
        d, sides, lift = rd.get('d', 0.18), rd.get('sides', 16), rd.get('lift', 0.04)
        z = roof.top_z((xa + xb) / 2, roof.yr) + lift
        return self.add('prism', 'tile', {'p0': _v((xa, roof.yr, z)), 'p1': _v((xb, roof.yr, z)), 'r': d / 2, 'sides': sides},
                        lod='ridge', name=name + '_ridge', tags=('ridge',))

    def roof_hip(self, x0, x1, y0, y1, z_eave, rise, ridge_half=None, t=0.12, ribs=None, ridge=None, hip_ridges=None,
                 name='roof'):
        """庑殿（四阿）屋面：12 顶点板（正脊两端缩短）+ 四坡瓦垄（端坡与靠角的垄在戗脊线前截短）+ 正脊 + 戗脊。
        ridge_half 为正脊半长；缺省时取四坡等坡（= 半面阔 - 半进深，deyang 32×22、脊长 10 即等坡）。
        ribs 同 roof_gable；hip_ridges = dict(d=0.16, sides=16, lift=0.04)：沿戗脊线的圆管，LOD1 8 边、LOD2 删除。"""
        xc, yr = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        if ridge_half is None:
            ridge_half = max(0.0, hx - hy)
        if ridge_half >= hx:
            raise ValueError('正脊半长须小于半面阔')
        roof = Roof('hip', x0, x1, y0, y1, z_eave, rise, t, yr=yr, xr0=xc - ridge_half, xr1=xc + ridge_half)
        self.add_geo(geo_slab_hip(x0, x1, y0, y1, roof.xr0, roof.xr1, yr, z_eave, z_eave + rise, t), 'tile', name=name + '_slab',
                     tags=('slab',))
        if ribs:
            self._hip_ribs(roof, ribs, name)
        if ridge and ridge_half > 0:
            self._ridge(roof, ridge, roof.xr0, roof.xr1, name)
        if hip_ridges:
            dh, sides, lift = hip_ridges.get('d', 0.16), hip_ridges.get('sides', 16), hip_ridges.get('lift', 0.04)
            zt = z_eave + t
            for k, (cx, cy, ex) in enumerate(((x0, y0, roof.xr0), (x1, y0, roof.xr1), (x1, y1, roof.xr1), (x0, y1, roof.xr0))):
                p0 = (ex, yr, zt + rise + lift); p1 = (cx, cy, zt + lift)
                self.add('prism', 'tile', {'p0': _v(p0), 'p1': _v(p1), 'r': dh / 2, 'sides': sides}, lod='hip_ridge',
                         name=f'{name}_hip{k}', tags=('hip_ridge',))
        return roof

    def _hip_ribs(self, roof, rb, name):
        """庑殿四坡瓦垄：前后坡沿 Y、端坡沿 X，靠角的垄在戗脊线前截短 hip_cut。"""
        d, pitch = rb.get('d', 0.07), rb.get('pitch', 0.43)
        lift, inset, sides = rb.get('lift', 0.02), rb.get('inset', 0.0), rb.get('sides', 8)
        margin = rb.get('margin', max(0.15, 0.6 * pitch))
        cut = rb.get('hip_cut', 1.5 * d)    # 在戗脊线前截短，避免管端穿出
        r = d / 2
        # 前后坡（沿 Y 走）
        xs = self._rib_xs(roof.x0, roof.x1, pitch, margin)
        for side, ye, sgn in (('f', roof.y0, 1), ('b', roof.y1, -1)):
            for i, x in enumerate(xs):
                ya = ye + sgn * inset
                # 本坡平面与端坡平面相交处（戗脊线）或脊线
                yend = roof.yr
                if x < roof.xr0 or x > roof.xr1:
                    run_e = (x - roof.x0) if x < roof.xr0 else (roof.x1 - x)
                    yend = ye + sgn * run_e * roof.s_end / roof.s_fb - sgn * cut
                if sgn * (yend - ya) < 3 * r:
                    continue
                p0 = (x, ya, roof.top_z(x, ya) + lift); p1 = (x, yend, roof.top_z(x, yend) + lift)
                self.add('prism', 'tile', {'p0': _v(p0), 'p1': _v(p1), 'r': r, 'sides': sides, 'index': i, 'count': len(xs)},
                         lod='rib', name=f'{name}_rib{side}{i:03d}', tags=('rib',))
        # 两端坡（沿 X 走）
        ys = self._rib_xs(roof.y0, roof.y1, pitch, margin)
        for side, xe, sgn in (('l', roof.x0, 1), ('r', roof.x1, -1)):
            for i, y in enumerate(ys):
                xa = xe + sgn * inset
                run_f = min(y - roof.y0, roof.y1 - y)
                xend = xe + sgn * run_f * roof.s_fb / roof.s_end - sgn * cut
                if sgn * (xend - xa) < 3 * r:
                    continue
                p0 = (xa, y, roof.top_z(xa, y) + lift); p1 = (xend, y, roof.top_z(xend, y) + lift)
                self.add('prism', 'tile', {'p0': _v(p0), 'p1': _v(p1), 'r': r, 'sides': sides, 'index': i, 'count': len(ys)},
                         lod='rib', name=f'{name}_rib{side}{i:03d}', tags=('rib',))

    def eave_tiles(self, roof, sides=('f', 'b'), pitch=0.36, length=0.42, sag=0.025, t=0.008, cover_w=0.13, cover_h=0.06,
                   eave_lift=0.01, margin=0.02, name='eave'):
        """类型门（gu / 广阳 / 夏门 / 上东 / 中东）的檐口逐片瓦：只沿前后檐各铺一排。
        每列一片板瓦（7 点抛物线弧、下凹 sag 0.025、厚 0.008、宽 = pitch 0.36、沿坡 0.42）+ 一片筒瓦（宽 0.13、拱高 0.06）
        盖在两片板瓦的缝上；均为 7 点弧带厚度挤出，28 顶点 / 52 三角（gate-A 实测）。瓦片比板坡略平：上端贴板顶，
        檐口端抬 eave_lift（0.01）。LOD2 删除（lod01）。注意面数：22 m 宽的门约 244 片、1.27 万三角，占文件 95%。"""
        if roof.kind != 'gable':
            raise ValueError('eave_tiles 目前只做悬山（类型门都是悬山）')
        xs = self._rib_xs(roof.x0, roof.x1, pitch, pitch / 2 + margin)
        hw = pitch / 2 - 0.0005

        def arc(xc, half, amp, convex):
            """7 点抛物线弧：convex=False 为下凹板瓦，True 为上拱筒瓦；返回 [(x, z)]。"""
            pts = []
            for kk in range(7):
                dx = (kk - 3) / 3 * half
                f = (dx / half) ** 2
                pts.append((xc + dx, amp * (1 - f) if convex else amp * f))
            return pts

        n = 0
        # 筒瓦两条下沿正好落在两侧板瓦的上表面（gate-A：筒瓦最低 8.2583 = 该处板瓦顶 8.2582）
        cover_base = sag * ((pitch / 2 - cover_w / 2) / hw) ** 2 + t
        for side in sides:
            ye = roof.y0 if side == 'f' else roof.y1
            yu = ye + (length if side == 'f' else -length)
            za, zu = roof.top_z(0, ye) + eave_lift, roof.top_z(0, yu)
            for i, xc in enumerate(xs):
                for kind, half, amp, convex, base in (('pan', hw, sag, False, 0.0), ('cover', cover_w / 2, cover_h, True, cover_base)):
                    if kind == 'cover' and i == len(xs) - 1:
                        continue
                    cx = xc if kind == 'pan' else xc + pitch / 2
                    prof = arc(cx, half, amp, convex)
                    poly = [(p[0], p[1] + base) for p in prof] + [(p[0], p[1] + base + t if kind == 'pan' else p[1] + base + 0.012)
                                                                  for p in prof[::-1]]
                    vs = []
                    for (yy, zz) in ((ye, za), (yu, zu)):
                        vs += [(px, yy, zz + pz) for (px, pz) in poly]
                    m = len(poly)
                    faces = [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))] + [(k, (k + 1) % m, m + (k + 1) % m, m + k) for k in range(m)]
                    self.add_geo(Geo(vs, faces), 'tile', lod='lod01', name=f'{name}_{side}{kind}{i:03d}', tags=('eave_tile',))
                    n += 1
        return n

    def purlins(self, roof, ys, x0, x1, w=0.08, h=0.055, name='purlin'):
        """檐下檩条/椽（住屋做法：每坡 2 根细方木沿 X 通长，H72 0.054×0.08 与 0.072×0.08，穿过山墙出头）。
        ys 为檩条中线的 y 列表；顶面抵到屋面板底（取较高一侧，余量埋入板内）。LOD1 每坡留 1 根，LOD2 删除。
        注意：端头不要与屋面板端面齐平——H72 的檩条正好齐平，端面与板端面同向共面，侧看会闪烁；
        x0/x1 若落在板端 3 cm 以内，自动各缩进 0.04。"""
        if abs(x0 - roof.x0) < 0.03:
            x0 = roof.x0 + 0.04
        if abs(x1 - roof.x1) < 0.03:
            x1 = roof.x1 - 0.04
        out = []
        groups = collections.defaultdict(list)
        for y in ys:
            groups['f' if y < roof.yr else 'b'].append(y)
        for g, lst in groups.items():
            lst = sorted(lst, key=lambda y: abs(y - (roof.y0 if g == 'f' else roof.y1)))
            for i, y in enumerate(lst):
                top = max(roof.bottom_z(x, yy) for x in (x0, x1) for yy in (y - w / 2, y + w / 2))
                out.append(self.add('box', 'timber', {'lo': _v((x0, y - w / 2, top - h)), 'hi': _v((x1, y + w / 2, top)),
                                                      'index': i, 'count': len(lst)}, lod='thin', name=f'{name}_{g}{i}',
                                    tags=('purlin',)))
        return out

    # ---- 构件：栏杆、院墙 -----------------------------------------------------------------
    def railing(self, p0, p1, z0, h=1.0, post_d=0.10, post_sides=12, spacing=1.2, rail=(0.12, 0.12), name='rail'):
        """栏杆：望柱用细棱柱（shangdong 12 边 r0.05×1.0、mao 16/8 边 r0.075），扶手为方木（kaiyang 0.18×0.18，各档保留）。
        shangdong 在 LOD2 删了望柱，扶手会悬空；本库望柱按圆木规则降档（LOD2 换 2r 方盒）以保持支承。
        p0/p1 为沿 X 或 Y 的两端点（z 取 z0）。"""
        p0, p1 = Vector(p0), Vector(p1)
        L = (p1 - p0).length
        n = max(2, int(round(L / spacing)) + 1)
        out = []
        for i in range(n):
            p = p0 + (p1 - p0) * (i / (n - 1))
            out.append(self.add('prism', 'timber', {'p0': _v((p.x, p.y, z0)), 'p1': _v((p.x, p.y, z0 + h - rail[1])),
                                                    'r': post_d / 2, 'sides': post_sides}, lod='round', name=f'{name}_post{i}',
                                tags=('rail_post',)))
        out.append(self.beam((p0.x, p0.y, z0 + h - rail[1]), (p1.x, p1.y, z0 + h - rail[1]), rail[0], rail[1], name=name + '_top',
                             tags=('rail',)))
        return out

    def court_wall(self, axis, u0, u1, face, z0=0.0, t=0.35, h=2.2, coping=0.12, coping_over=0.05, inward=1, name='court'):
        """院墙：夯土墙 0.35 厚 × 2.2 高（court-layout-kit 实测）+ 顶上 tile 压顶板 coping 厚、两侧各挑 coping_over。
        压顶的细部（她在 compact_work 里用 66 片 16 三角小瓦）未细量，这里用一块 tile 方板代替。"""
        w = self.wall(axis, u0, u1, face, t, z0, z0 + h, inward=inward, name=name + '_wall', tags=('wall', 'court'))
        f = self._wall_map(axis, face, inward)
        a = f(u0, -coping_over, z0 + h); b = f(u1, t + coping_over, z0 + h + coping)
        lo = tuple(min(a[k], b[k]) for k in range(3)); hi = tuple(max(a[k], b[k]) for k in range(3))
        c = self.box(lo, hi, 'tile', name=name + '_coping', tags=('coping',))
        return w, c


def _reorder_any(c):
    """把竖直棱柱状六面体的 8 个角点（4 个在下、4 个在上，上下角点 x,y 相同、高度可不同）按 geo_hexa 约定重排：
    底面逆时针（自 x+y 最小的角起），顶面与底面逐点对应。"""
    c = [tuple(p) for p in c]
    bot = sorted(c, key=lambda p: p[2])[:4]
    cx = sum(p[0] for p in bot) / 4; cy = sum(p[1] for p in bot) / 4
    b = sorted(bot, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    start = min(range(4), key=lambda i: b[i][0] + b[i][1])
    b = b[start:] + b[:start]
    rest = [p for p in c if p not in b]
    tp = [min(rest, key=lambda q: (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 - 1e-9 * q[2]) for p in b]
    return b + tp


def _oriented(g):
    """对单个闭合体重算法线朝外（构造时已尽量保证，这里兜底）。"""
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in g.verts]
    for f in g.faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.verts.index_update()
    out = Geo([tuple(v.co) for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces])
    bm.free()
    return out


class Roof:
    """屋面几何查询：top_z(x, y) / bottom_z(x, y) 给出板顶 / 板底标高（米）。悬山只看前后坡；庑殿取四坡平面的下包络。"""

    def __init__(self, kind, x0, x1, y0, y1, z_eave, rise, t, yr, xr0=None, xr1=None):
        """记录屋面形状参数并算出前后坡、端坡的坡率（rise/run）。"""
        self.kind, self.x0, self.x1, self.y0, self.y1 = kind, x0, x1, y0, y1
        self.z_eave, self.rise, self.t, self.yr = z_eave, rise, t, yr
        self.xr0, self.xr1 = xr0, xr1
        self.segments = [(x0, x1)]          # roof_gable(splits=) 会改写为各板段
        self.s_fb = rise / (yr - y0)
        self.s_end = rise / (xr0 - x0) if kind == 'hip' and xr0 is not None and xr0 > x0 else None
        self.pitch_deg = math.degrees(math.atan(self.s_fb))

    def bottom_z(self, x, y):
        """板底标高（超出檐口按檐口算）。"""
        zf = self.z_eave + max(0.0, min(y - self.y0, self.yr - self.y0)) * self.s_fb
        zb = self.z_eave + max(0.0, min(self.y1 - y, self.y1 - self.yr)) * self.s_fb
        z = min(zf, zb) if y != self.yr else self.z_eave + self.rise
        if self.kind == 'hip':
            ze = self.z_eave + max(0.0, min(x - self.x0, self.x1 - x)) * self.s_end
            z = min(z, ze)
        return min(z, self.z_eave + self.rise)

    def top_z(self, x, y):
        """板顶标高。"""
        return self.bottom_z(x, y) + self.t


# --------------------------------------------------------------------------------------------
# 4. Blender 物体与导出
# --------------------------------------------------------------------------------------------
def _make_mesh(name, geo):
    """由 Geo 生成 Blender 网格数据块（名 = name），并校验。"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in geo.verts], [], [tuple(f) for f in geo.faces])
    me.validate(clean_customdata=True)
    me.update()
    return me


#: 导出前三角化方式 (quad_method, ngon_method)，None = 交给导出器（四边形 0-2 对角线、多边形 polyfill）。
TRIANGULATE = None


def _triangulate(me, methods):
    """用 bmesh.ops.triangulate 按 methods=(quad_method, ngon_method) 预先三角化网格（决定导出后的对角线走向）。"""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=methods[0], ngon_method=methods[1])
    bm.to_mesh(me)
    bm.free()
    me.update()


def _make_object(name, geo, mat, collection, location=None, mesh_name=None, triangulate=None):
    """由 Geo 生成物体并挂材质、平直着色、世界盒式 UV，链接到集合。mesh_name 缺省 = 物体名。
    triangulate=(quad_method, ngon_method) 时先三角化（UV 在三角化后按面法线重算，结果与不三角化相同）。"""
    me = _make_mesh(mesh_name or name, geo)
    if triangulate:
        _triangulate(me, triangulate)
    if mat is not None:
        me.materials.append(mat)
    obj = bpy.data.objects.new(name, me)
    if location is not None:
        obj.location = location
    (collection or bpy.context.scene.collection).objects.link(obj)
    set_flat(me)
    uv_world_box(me, offset=Vector(location) if location is not None else None)
    return obj


def set_flat(me):
    """全部面平直着色（她的 45+38 个文件角点法线 = 面法线 100%，连 16 棱柱也是棱面）。"""
    me.polygons.foreach_set('use_smooth', [False] * len(me.polygons))
    me.update()


def uv_world_box(me, scale=1.0, offset=None):
    """世界坐标盒式投影 UV（她的 LY_P01 材质 100% 吻合）：每个面按面法线主轴取坐标——
    |nz| 最大取 (x, y)，否则 |ny| 严格最大取 (x, z)，否则取 (y, z)；不按正负翻转，不展 UV，1 UV 单位 = 1 m（scale=1）。
    并列：Z 与 X/Y 并列取 Z；**X 与 Y 并列（45° 立面，如 12 边柱的 4 个斜面）取 (y, z)**——她的 S84、G10 各 16/16 个
    这类顶点都是 (y, z)，全部 LOD0 统计 1471:228 偏 X（validate/round1 review_color/ties.py）。round2 由「Y 优先」改。
    offset 用于单独节点（局部坐标 + 铰点 = 世界坐标）。"""
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uvl = me.uv_layers[0]
    off = offset or Vector((0, 0, 0))
    for p in me.polygons:
        n = p.normal
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co + off
            uv = _box_uv(n, co)
            uvl.data[li].uv = (uv[0] * scale, uv[1] * scale)


#: 取轴比较容差。0 = 严格比较 Blender 的 float32 面法线分量（她的做法）：45° 面上 |nx|、|ny| 只差 3e-7，
#: 谁大取谁，完全相等才取 (y,z)。她的 S84-LOD2 菱形柱外侧 4 面 |ny| 略大取 (x,z)、内侧取 (y,z)，G10 全 (y,z)，
#: 都是坐标末位的浮点噪声决定的；库用双精度算坐标（与她逐位相同），再严格比较，于是三档 16+16+16 个并列面全部一致
#: （validate/round2 compare.py）。
UV_TIE = 0.0


def _box_uv(n, co):
    """盒式投影的取轴规则（uv_world_box、_uv_world_for_object 共用；inspect_glb 用同一判据在 GLB 上复算）。"""
    ax, ay, az = abs(n[0]), abs(n[1]), abs(n[2])
    if az >= ax - UV_TIE and az >= ay - UV_TIE:
        return (co[0], co[1])
    if ay > ax + UV_TIE:
        return (co[0], co[2])
    return (co[1], co[2])


def _name_fields(a, mat, lod, first=None):
    """命名模板字段。"""
    return dict(prefix=a.prefix, proto=a.prototype or a.prefix, mat=mat, lod=lod, first=first or mat,
                material=f'LY_P01_{mat}__' + ('FLAT' if lod >= 2 else 'PBR'))


def node_name(a, mat, lod=0):
    """静态网格节点名，按 Assembly.naming：default <slug>-<V>-static_<mat>（城门、礼制、宫殿 23 张卡）；
    market S84-static-LY_P01_<mat>__PBR|FLAT（随 LOD 换后缀）；house_types layout__LY_P01_<mat>__PBR|FLAT。"""
    return a.naming['node'].format(**_name_fields(a, mat, lod))


def mesh_name(a, mat, lod=0, first=None):
    """网格名：default = 节点名；market / house_types = <原型>_<该材料组第一个组件名>（S84_floor、
    S84_frontpost_sloped_cap、S84_roof_left；三档同名）。"""
    return a.naming['mesh'].format(**_name_fields(a, mat, lod, first))


def file_name(a, lod):
    """GLB 文件名：default <slug>-<V>-LOD<n>.glb；market / house_types <原型>-LOD<n>.glb（S84-LOD0.glb、G10-LOD0.glb）。"""
    return a.naming['file'].format(**_name_fields(a, 'x', lod))


def node_extras(a, lod, extra=None, mat=None):
    """节点 extras，键序按 Assembly.naming['extras']：
    evidence = a.evidence；LOD = lod；metres_per_unit = 1.0（default 写法）；meters_per_unit = 1（int，market 写法）；
    unit = 'metres'；prototype = a.prototype；module = a.modules[mat]；version 等其余键取 a.extras。
    值为 None 的键不写；a.extras 里不在键序中的键接在后面。"""
    src = dict(a.extras)
    vals = {'evidence': a.evidence, 'LOD': lod, 'metres_per_unit': 1.0, 'meters_per_unit': 1, 'unit': 'metres',
            'prototype': a.prototype, 'module': a.modules.get(mat) if mat else None}
    ex = {}
    for k in a.naming['extras']:
        v = src.pop(k) if k in src else vals.get(k)
        if v is not None:
            ex[k] = v
    ex.update(src)
    if extra:
        ex.update(extra)
    return ex


def _purge(names):
    """删除同名物体与无人使用的网格，防止再次导出时出现 .001 副本后缀。"""
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None:
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
        me = bpy.data.meshes.get(n)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def build_lod_objects(a, lod):
    """按 LOD 重新生成全部组件几何，按材质合并为 <slug>-<V>-static_<mat> 物体（无变换、平直、盒式 UV），
    单独节点组件（门扇）另建物体（原点 = 铰点）。返回新建物体列表（放在集合 <slug>-<V>-LOD<n>）。"""
    cname = f'{a.prefix}-LOD{lod}'
    coll = bpy.data.collections.get(cname) or bpy.data.collections.new(cname)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    by_mat = collections.OrderedDict()
    first = {}
    nodes = collections.OrderedDict()
    for c in a.components:
        g = component_geometry(c, lod, a.profile)
        if g is None:
            continue
        if c.get('node'):
            key = c['node']['name']
            nodes.setdefault(key, {'node': c['node'], 'mat': c['mat'], 'geo': Geo()})['geo'].add(g)
        else:
            by_mat.setdefault(c['mat'], Geo()).add(g)
            first.setdefault(c['mat'], c['name'])
    objs = []
    names = ([node_name(a, m, lod) for m in by_mat] + [mesh_name(a, m, lod, first[m]) for m in by_mat]
             + [f'{a.prefix}-{k}' for k in nodes])
    _purge(names)
    for m in sorted(by_mat, key=lambda k: MAT_ORDER.index(k) if k in MAT_ORDER else 99):
        nm = node_name(a, m, lod)
        obj = _make_object(nm, by_mat[m], material_for(m, lod), coll, mesh_name=mesh_name(a, m, lod, first[m]),
                           triangulate=TRIANGULATE)
        for k, v in node_extras(a, lod, mat=m).items():
            obj[k] = v
        objs.append(obj)
    for k, d in nodes.items():
        nm = f'{a.prefix}-{k}'
        M = Matrix(d['node']['matrix'])
        loc, rot, _ = M.decompose()
        obj = _make_object(nm, d['geo'], material_for(d['mat'], lod), coll)
        obj.location = loc
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = rot
        uv_world_box(obj.data, offset=None)  # 先按局部算，再用世界坐标覆盖
        _uv_world_for_object(obj)
        for kk, v in node_extras(a, lod, d['node'].get('extras')).items():
            obj[kk] = v
        objs.append(obj)
    return objs


def _uv_world_for_object(obj):
    """带变换的单独节点（门扇）：按物体变换后的世界坐标重算盒式 UV。"""
    me = obj.data
    M = obj.matrix_basis
    uvl = me.uv_layers[0]
    R = M.to_3x3()
    for p in me.polygons:
        n = (R @ p.normal)
        for li in p.loop_indices:
            co = M @ me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = _box_uv(n, co)


#: 在 Blender 5.2 上复刻她 4.3.2（Khronos glTF Blender I/O v4.3.47）输出所需的导出参数（全部显式写死）。
EXPORT_SETTINGS = dict(
    export_format='GLB', export_yup=True, export_apply=True, export_extras=True,
    export_normals=True, export_tangents=False, export_texcoords=True,
    export_vertex_color='MATERIAL', export_attributes=False,
    export_materials='EXPORT', export_image_format='AUTO', export_keep_originals=False,
    export_unused_images=False, export_unused_textures=False,
    export_cameras=False, export_lights=False, export_animations=False, export_skins=False, export_morph=False,
    export_draco_mesh_compression_enable=False, export_meshopt_compression_enable=False, export_use_gltfpack=False,
    export_shared_accessors=False, export_gpu_instances=False, export_gn_mesh=False,
    use_mesh_edges=False, use_mesh_vertices=False, export_original_specular=False,
    use_selection=True,
)


def export_glb(objs, path, animations=False):
    """把给定物体导出为 GLB（EXPORT_SETTINGS）。只导出所选物体，不带相机灯光，不压缩。"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    kw = dict(EXPORT_SETTINGS)
    kw['export_animations'] = animations
    props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    kw = {k: v for k, v in kw.items() if k in props}      # 4.3 没有的新参数自动跳过
    bpy.ops.export_scene.gltf(filepath=path, **kw)
    reorder_glb(path)
    return path


def _mat_rank(name):
    """材质名 LY_P01_<mat>__* 在 MAT_ORDER 里的序号（未知排最后）。"""
    m = re.match(r'LY_P01_(.+?)__', name or '')
    return MAT_ORDER.index(m.group(1)) if m and m.group(1) in MAT_ORDER else len(MAT_ORDER)


def reorder_glb(path):
    """把导出的 GLB 改排成她的顺序：节点、网格、材质按 MAT_ORDER（earth→path→paper__stone→timber→tile），
    贴图、图片跟随材质，二进制块按「网格 k 的 4 个 bufferView → 该材质的 3 张图」交错重排（她的 S84/G10 布局）。
    原因：Blender 5.2.40 导出器按物体名排序（S84-static-LY_P01_tile 排在 timber 前），4.3.47 不是。
    只改排列与索引，不改任何数据字节。已是目标顺序时不动文件。返回是否改写。"""
    j, bn = _read_glb(path)
    nodes = j.get('nodes', [])
    meshes = j.get('meshes', [])
    mats = j.get('materials', [])

    def node_rank(i):
        """节点排序键：所挂网格第一个图元的材质序。"""
        nd = nodes[i]
        if 'mesh' not in nd:
            return (len(MAT_ORDER) + 1, i)
        prs = meshes[nd['mesh']]['primitives']
        mi = prs[0].get('material') if prs else None
        return (_mat_rank(mats[mi]['name']) if mi is not None else len(MAT_ORDER), i)
    n_order = sorted(range(len(nodes)), key=node_rank)
    m_order = []
    for i in n_order:
        if 'mesh' in nodes[i] and nodes[i]['mesh'] not in m_order:
            m_order.append(nodes[i]['mesh'])
    m_order += [k for k in range(len(meshes)) if k not in m_order]
    mt_order = []
    for k in m_order:
        for pr in meshes[k]['primitives']:
            if pr.get('material') is not None and pr['material'] not in mt_order:
                mt_order.append(pr['material'])
    mt_order += [k for k in range(len(mats)) if k not in mt_order]
    if n_order == list(range(len(nodes))) and m_order == list(range(len(meshes))) and mt_order == list(range(len(mats))):
        return False

    def tex_refs(m):
        """材质引用的贴图序号列表。"""
        out = []
        pb = m.get('pbrMetallicRoughness', {})
        for k in ('baseColorTexture', 'metallicRoughnessTexture'):
            if k in pb:
                out.append(pb[k]['index'])
        for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if k in m:
                out.append(m[k]['index'])
        return out
    nmat = {old: new for new, old in enumerate(mt_order)}
    texs = j.get('textures', [])
    t_first = {}
    for old in mt_order:
        for t in tex_refs(mats[old]):
            t_first.setdefault(t, nmat[old])
    t_order = sorted(range(len(texs)), key=lambda t: (t_first.get(t, 1e9), t))
    ntex = {old: new for new, old in enumerate(t_order)}
    imgs = j.get('images', [])
    i_first = {}
    for new_t, old_t in enumerate(t_order):
        i_first.setdefault(texs[old_t]['source'], new_t)
    i_order = sorted(range(len(imgs)), key=lambda i: (i_first.get(i, 1e9), i))
    nimg = {old: new for new, old in enumerate(i_order)}
    nnode = {old: new for new, old in enumerate(n_order)}
    nmesh = {old: new for new, old in enumerate(m_order)}
    # accessor 归属网格；bufferView 归属（网格的新序号, 0）或（首个引用该图的网格新序号, 1）
    acc_owner = {}
    for new_m, old_m in enumerate(m_order):
        for pr in meshes[old_m]['primitives']:
            for ai in list(pr['attributes'].values()) + ([pr['indices']] if 'indices' in pr else []):
                acc_owner.setdefault(ai, new_m)
    accs = j.get('accessors', [])
    a_order = sorted(range(len(accs)), key=lambda i: (acc_owner.get(i, 1e9), i))
    nacc = {old: new for new, old in enumerate(a_order)}
    img_mesh = {}
    for new_m, old_m in enumerate(m_order):
        for pr in meshes[old_m]['primitives']:
            if pr.get('material') is None:
                continue
            for t in tex_refs(mats[pr['material']]):
                img_mesh.setdefault(texs[t]['source'], new_m)
    bvs = j.get('bufferViews', [])
    bv_key = {}
    for ai, a_ in enumerate(accs):
        if 'bufferView' in a_:
            bv_key.setdefault(a_['bufferView'], (acc_owner.get(ai, 1e9), 0))
    for ii, im in enumerate(imgs):
        if 'bufferView' in im:
            bv_key.setdefault(im['bufferView'], (img_mesh.get(ii, 1e9), 1, nimg[ii]))
    bv_order = sorted(range(len(bvs)), key=lambda b: (*bv_key.get(b, (1e9, 2)), b))
    nbv = {old: new for new, old in enumerate(bv_order)}
    # 重写二进制（4 字节对齐，补 0），bufferView 内容逐字节不变
    blob = bytearray()
    new_bvs = []
    for old in bv_order:
        bv = dict(bvs[old])
        o = bv.get('byteOffset', 0)
        data = bn[o:o + bv['byteLength']]
        while len(blob) % 4:
            blob.append(0)
        bv['byteOffset'] = len(blob)
        blob += data
        new_bvs.append(bv)
    # 重写索引
    j['nodes'] = [nodes[i] for i in n_order]
    for nd in j['nodes']:
        if 'mesh' in nd:
            nd['mesh'] = nmesh[nd['mesh']]
        if 'children' in nd:
            nd['children'] = [nnode[c] for c in nd['children']]
    for sc in j.get('scenes', []):
        sc['nodes'] = sorted(nnode[i] for i in sc.get('nodes', []))
    j['meshes'] = [meshes[i] for i in m_order]
    for me in j['meshes']:
        for pr in me['primitives']:
            pr['attributes'] = {k: nacc[v] for k, v in pr['attributes'].items()}
            if 'indices' in pr:
                pr['indices'] = nacc[pr['indices']]
            if pr.get('material') is not None:
                pr['material'] = nmat[pr['material']]
    j['materials'] = [mats[i] for i in mt_order]
    for m in j['materials']:
        pb = m.get('pbrMetallicRoughness', {})
        for k in ('baseColorTexture', 'metallicRoughnessTexture'):
            if k in pb:
                pb[k]['index'] = ntex[pb[k]['index']]
        for k in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if k in m:
                m[k]['index'] = ntex[m[k]['index']]
    if texs:
        j['textures'] = [dict(texs[i], source=nimg[texs[i]['source']]) for i in t_order]
    if imgs:
        j['images'] = [dict(imgs[i], bufferView=nbv[imgs[i]['bufferView']]) if 'bufferView' in imgs[i] else imgs[i]
                       for i in i_order]
    j['accessors'] = [dict(accs[i], bufferView=nbv[accs[i]['bufferView']]) if 'bufferView' in accs[i] else accs[i]
                      for i in a_order]
    j['bufferViews'] = new_bvs
    while len(blob) % 4:
        blob.append(0)
    j['buffers'][0]['byteLength'] = len(blob)
    js = json.dumps(j, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    while len(js) % 4:
        js += b' '
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(path, 'wb') as fh:
        fh.write(struct.pack('<4sII', b'glTF', 2, total))
        fh.write(struct.pack('<I4s', len(js), b'JSON')); fh.write(js)
        fh.write(struct.pack('<I4s', len(blob), b'BIN\x00')); fh.write(bytes(blob))
    return True


def export_lods(a, outdir, lods=(0, 1, 2), keep_objects=False, verbose=True):
    """一次导出 LOD0/1/2 到 outdir（文件名按 Assembly.naming：<slug>-<V>-LOD<n>.glb 或 <原型>-LOD<n>.glb），
    导出后改排成 MAT_ORDER（reorder_glb），并对每个文件跑 inspect_glb 自检（含节点名、网格名、材质顺序）；返回 {lod: 报告}。"""
    res = {}
    for lod in lods:
        objs = build_lod_objects(a, lod)
        path = os.path.join(outdir, file_name(a, lod))
        export_glb(objs, path)
        expect = {'nodes': [o.name for o in objs], 'meshes': [o.data.name for o in objs]}
        rep = inspect_glb(path, expect_lod=lod, expect=expect)
        res[lod] = rep
        if verbose:
            print(format_glb_report(rep))
        if not keep_objects:
            _purge([o.name for o in objs])
    if 0 in res:
        t0 = res[0]['triangles']
        for lod in res:
            res[lod]['ratio_to_lod0'] = round(res[lod]['triangles'] / max(t0, 1), 3)
        if verbose:
            print('LOD 三角数', {k: (v['triangles'], v['ratio_to_lod0']) for k, v in res.items()})
    return res


# --------------------------------------------------------------------------------------------
# 5. 导出后自检
# --------------------------------------------------------------------------------------------
_CT = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
_NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def _read_glb(path):
    """读取 GLB，返回 (JSON dict, 二进制块)。"""
    b = open(path, 'rb').read()
    jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl]); off = 20 + jl
    bl = struct.unpack('<I', b[off:off + 4])[0]
    return j, b[off + 8: off + 8 + bl]


def _acc(j, bn, i):
    """按 accessor 序号读出 numpy 数组（float64）。"""
    import numpy as np
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    dt = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a['componentType']]
    n = _NC[a['type']]
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bn, dt, count=a['count'] * n, offset=o).reshape(a['count'], n).astype(np.float64)


def _manifest():
    """读 textures/manifest.json，返回 {sha256: 记录}，用于核对贴图是否为她的共享贴图。"""
    p = os.path.join(TEX_DIR, 'manifest.json')
    if not os.path.exists(p):
        return {}
    return {m['sha256']: m for m in json.load(open(p, encoding='utf-8'))}


def inspect_glb(path, expect_lod=None, ground_tol=0.002, expect=None):
    """读回导出的 GLB 做交付自检，返回报告 dict（issues 为空即通过）：
    三角数、材质名（LOD0/1 须为 LY_P01_*__PBR，LOD2 须为 __FLAT）、材质顺序（按 MAT_ORDER，她 34/45 个 LOD0 文件是
    earth→timber→tile）、贴图（LOD0 512 / LOD1 256 且字节与她的共享贴图相同、LOD2 无图）、顶点属性只有
    POSITION/NORMAL/TEXCOORD_0、索引类型、无扩展、无退化三角、节点全部命名且静态节点无 TRS、平直法线比例、
    世界盒式 UV 吻合率（严格按 _box_uv 规则，并列面单独计数并报告用了哪种投影）、doubleSided、落地（最低点 y=0）。
    expect = {'nodes': [...], 'meshes': [...]}：节点名、网格名应等于这些（export_lods 自动传）。"""
    import numpy as np
    j, bn = _read_glb(path)
    man = _manifest()
    issues, info = [], {}
    gen = j.get('asset', {}).get('generator')
    if j.get('extensionsUsed') or j.get('extensionsRequired'):
        issues.append(f'使用了扩展 {j.get("extensionsUsed")}')
    mats = [m.get('name') for m in j.get('materials', [])]
    ranks = [_mat_rank(m) for m in mats]
    if ranks != sorted(ranks):
        issues.append(f'材质顺序不是 MAT_ORDER：{mats}')
    if expect:
        got_n = sorted(n.get('name') for n in j.get('nodes', []))
        got_m = sorted(m.get('name') for m in j.get('meshes', []))
        if 'nodes' in expect and got_n != sorted(expect['nodes']):
            issues.append(f'节点名 {got_n} ≠ 期望 {sorted(expect["nodes"])}')
        if 'meshes' in expect and got_m != sorted(expect['meshes']):
            issues.append(f'网格名 {got_m} ≠ 期望 {sorted(expect["meshes"])}')
    for m in j.get('materials', []):
        nm = m.get('name') or ''
        if not re.fullmatch(r'LY_P01_[a-z_]+__(PBR|FLAT)', nm):
            issues.append(f'材质名不合规范 {nm!r}')
        if expect_lod is not None:
            want = 'FLAT' if expect_lod >= 2 else 'PBR'
            if not nm.endswith('__' + want):
                issues.append(f'LOD{expect_lod} 应为 __{want}：{nm}')
        if not m.get('doubleSided'):
            issues.append(f'{nm} 不是 doubleSided')
        if m.get('extensions'):
            issues.append(f'{nm} 带材质扩展 {list(m["extensions"])}')
        pb = m.get('pbrMetallicRoughness', {})
        if nm.endswith('__PBR') and ('metallicFactor' in pb or 'roughnessFactor' in pb):
            issues.append(f'{nm} 写了 metallic/roughness 因子（她的 PBR 不写）')
        if 'occlusionTexture' in m or 'emissiveFactor' in m:
            issues.append(f'{nm} 多了 occlusion/emissive')
    imgs = []
    for im in j.get('images', []):
        bv = j['bufferViews'][im['bufferView']]
        data = bn[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
        sha = hashlib.sha256(data).hexdigest()
        w, h = struct.unpack('>II', data[16:24]) if data[:4] == b'\x89PNG' else (0, 0)
        imgs.append({'name': im.get('name'), 'mime': im.get('mimeType'), 'size': (w, h), 'sha12': sha[:12], 'shared': sha in man})
        if sha not in man:
            issues.append(f'贴图 {im.get("name")} 不是她的共享贴图字节')
        if expect_lod is not None and expect_lod < 2 and w != TEX_RES[expect_lod]:
            issues.append(f'LOD{expect_lod} 贴图应为 {TEX_RES[expect_lod]}²：{im.get("name")} {w}²')
    if expect_lod is not None and expect_lod >= 2 and imgs:
        issues.append('LOD2 不应带贴图')
    tris = 0; verts = 0; degen = 0; flat_ok = []; uv_ok = []; ymin = 1e9; ymax = -1e9
    ties = collections.Counter()
    lo = np.array([1e9] * 3); hi = -lo
    for nd in j.get('nodes', []):
        if not nd.get('name'):
            issues.append('有未命名节点')
        if re.search(r'\.\d{3}$', nd.get('name', '')):
            issues.append(f'节点名带 Blender 副本后缀 {nd["name"]}')
        is_static = 'hinge_axis_native' not in nd.get('extras', {})      # 只有可开合门扇节点带变换
        if is_static and any(k in nd for k in ('translation', 'rotation', 'scale', 'matrix')):
            issues.append(f'静态节点 {nd["name"]} 带变换')
        if 'mesh' not in nd:
            continue
        mesh = j['meshes'][nd['mesh']]
        if re.search(r'\.\d{3}$', mesh.get('name', '')):
            issues.append(f'网格名带 Blender 副本后缀 {mesh.get("name")}')
        M = np.eye(4)
        if 'translation' in nd:
            M[:3, 3] = nd['translation']
        if 'rotation' in nd:
            x, y, z, w = nd['rotation']
            M[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        for pr in mesh['primitives']:
            at = sorted(pr['attributes'])
            if at != ['NORMAL', 'POSITION', 'TEXCOORD_0']:
                issues.append(f'{nd["name"]} 顶点属性 {at}')
            if pr.get('mode', 4) != 4:
                issues.append('非三角图元')
            pos = _acc(j, bn, pr['attributes']['POSITION'])
            nor = _acc(j, bn, pr['attributes']['NORMAL'])
            uv = _acc(j, bn, pr['attributes']['TEXCOORD_0'])
            idx = _acc(j, bn, pr['indices']).reshape(-1).astype(np.int64)
            ct = j['accessors'][pr['indices']]['componentType']
            if len(pos) < 65535 and ct != 5123:
                issues.append(f'{nd["name"]} 顶点 <65535 却不是 uint16 索引')
            tri = idx.reshape(-1, 3)
            tris += len(tri); verts += len(pos)
            wp = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
            lo = np.minimum(lo, wp.min(0)); hi = np.maximum(hi, wp.max(0))
            P = wp[tri]
            fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); ar = np.linalg.norm(fn, axis=1)
            degen += int((ar < 1e-10).sum())
            fnu = fn / np.maximum(ar[:, None], 1e-12)
            wn = nor @ M[:3, :3].T
            flat_ok.append((np.einsum('tij,tj->ti', wn[tri], fnu) > 0.9999).mean())
            # 世界盒式 UV 吻合率（Blender 空间：xb=x, yb=-z, zb=y；v_b = 1 - v）
            xb, yb, zb = P[..., 0], -P[..., 2], P[..., 1]
            nb = np.stack([fnu[:, 0], -fnu[:, 2], fnu[:, 1]], 1); ax = np.abs(nb)
            au = uv[tri][..., 0]; av = 1.0 - uv[tri][..., 1]
            cand = {2: (xb, yb), 1: (xb, zb), 0: (yb, zb)}
            T = 1e-4                               # 只用于标记「并列面」做报告
            # 取轴判据与 _box_uv 相同：严格比较（由 float32 位置算的面法线，噪声方向与 Blender 面法线一致）
            ch = np.where((ax[:, 2] >= ax[:, 0] - UV_TIE) & (ax[:, 2] >= ax[:, 1] - UV_TIE), 2,
                          np.where(ax[:, 1] > ax[:, 0] + UV_TIE, 1, 0))
            match = {d_: ((np.abs(au - pu) < 2e-3) & (np.abs(av - pv) < 2e-3)).all(1) for d_, (pu, pv) in cand.items()}
            okf = np.select([ch == 2, ch == 1, ch == 0], [match[2], match[1], match[0]])
            mx = ax.max(1)
            ntie = ((ax >= mx[:, None] - T).sum(1) >= 2)
            # 并列面（主轴分量差 < 1e-4）不计入吻合率：取向由坐标末位的浮点噪声决定，GLB 里重算的法线与 Blender
            # 面法线（四边形按对角线算）噪声方向可能不同，这里只单独计数并报告实际用了哪种投影（uv_ties）。
            uv_ok.append(okf[~ntie].mean() if (~ntie).any() else 1.0)
            for ti in np.nonzero(ntie)[0]:        # 并列面：记下实际用的投影（她的 X/Y 并列取 yz）
                axes = ''.join('xyz'[k] for k in range(3) if ax[ti, k] >= mx[ti] - T)
                used = [nm for d_, nm in ((2, 'xy'), (1, 'xz'), (0, 'yz')) if match[d_][ti]]
                ties[f'{mat_of_node(j, nd)}:{axes}->{"/".join(used) or "none"}'] += 1
    info.update(file=os.path.basename(path), generator=gen, triangles=int(tris), vertices=int(verts), materials=mats, images=imgs,
                nodes=[n.get('name') for n in j.get('nodes', [])], bbox_min=[round(float(x), 4) for x in lo],
                bbox_max=[round(float(x), 4) for x in hi], size=[round(float(x), 4) for x in hi - lo],
                flat_normals=round(float(min(flat_ok)) if flat_ok else 0, 4), uv_world_box=round(float(min(uv_ok)) if uv_ok else 0, 4),
                degenerate=degen, scene=[s.get('name') for s in j.get('scenes', [])],
                meshes=[m.get('name') for m in j.get('meshes', [])], uv_ties=dict(ties),
                extras=[n.get('extras') for n in j.get('nodes', [])])
    if degen:
        issues.append(f'{degen} 个退化三角')
    if info['flat_normals'] < 0.999:
        issues.append(f'法线不是全平直 {info["flat_normals"]}')
    if info['uv_world_box'] < 0.999:
        issues.append(f'UV 不是世界盒式投影 {info["uv_world_box"]}')
    if abs(lo[1]) > ground_tol:
        issues.append(f'最低点 y={lo[1]:.4f}，未落在 y=0（地面补丁另出文件）')
    info['issues'] = issues
    return info


def mat_of_node(j, nd):
    """节点第一个图元的材质名缩写（earth/timber/…），供报告用。"""
    try:
        nm = j['materials'][j['meshes'][nd['mesh']]['primitives'][0]['material']]['name']
        return re.sub(r'^LY_P01_|__(PBR|FLAT)$', '', nm)
    except (KeyError, IndexError, TypeError):
        return '?'


def format_glb_report(r):
    """把 inspect_glb 的报告格式化成几行可读文字。"""
    s = [f"[GLB] {r['file']}  tris={r['triangles']} verts={r['vertices']} gen={r['generator']}",
         f"      materials={r['materials']}  nodes={r['nodes']}",
         f"      images={[(i['name'], i['size'][0], i['sha12'], 'shared' if i['shared'] else 'NEW') for i in r['images']]}",
         f"      bbox(glTF) min={r['bbox_min']} max={r['bbox_max']} flat={r['flat_normals']} uv={r['uv_world_box']} degen={r['degenerate']}",
         f"      meshes={r.get('meshes')}  uv 并列面={r.get('uv_ties')}",
         f"      {'通过' if not r['issues'] else '问题: ' + '; '.join(r['issues'])}"]
    return '\n'.join(s)


# --------------------------------------------------------------------------------------------
# 6. 检查：悬空 / 穿插 / 共面 / 落地 / 入口净空
# --------------------------------------------------------------------------------------------
def _world_parts(a, lod=0):
    """返回 [(组件, 世界坐标 Geo)]，跳过该 LOD 被删除的组件。"""
    parts = []
    for c in a.components:
        g = component_world_geo(c, lod, a.profile)
        if g is not None:
            parts.append((c, g))
    return parts


def _bvh(g):
    """由 Geo 建 BVHTree（n 边形面）。"""
    return BVHTree.FromPolygons([Vector(v) for v in g.verts], g.faces, all_triangles=False, epsilon=0.0)


def _face_info(g, fi):
    """返回第 fi 个面的顶点（Vector 列表）与单位法线（取最大叉积，适配凹多边形）。"""
    pts = [Vector(g.verts[i]) for i in g.faces[fi]]
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    for k in range(2, len(pts) - 1):
        m = (pts[k] - pts[0]).cross(pts[k + 1] - pts[0])
        if m.length > n.length:
            n = m
    return pts, (n.normalized() if n.length > 1e-12 else n)


def _tri_soup(parts):
    """把若干 (组件, Geo) 三角化（凹多边形用 tessellate_polygon）成一棵 BVH，并返回每个三角形所属的组件序号。"""
    from mathutils.geometry import tessellate_polygon
    allv, allt, owner = [], [], []
    for pi, (c, g) in enumerate(parts):
        o = len(allv)
        allv.extend(Vector(v) for v in g.verts)
        for f in g.faces:
            if len(f) == 3:
                tl = [f]
            else:
                pts = [Vector(g.verts[i]) for i in f]
                tl = [tuple(f[i] for i in t) for t in tessellate_polygon([pts])]
            for t in tl:
                allt.append(tuple(i + o for i in t)); owner.append(pi)
    return allv, allt, owner


def _grown(g, d):
    """按包围盒中心把几何各向外扩 d（接触支承判定用）。"""
    lo, hi = g.bbox()
    c = [(lo[k] + hi[k]) / 2 for k in range(3)]
    s = [(hi[k] - lo[k] + 2 * d) / max(hi[k] - lo[k], 1e-9) for k in range(3)]
    return Geo([tuple(c[k] + (v[k] - c[k]) * s[k] for k in range(3)) for v in g.verts], g.faces)


def check_floating(a, tol=0.005, spacing=0.12, exempt_tags=('leaf', 'ground'), lod=0):
    """悬空检测，两步：
    1) 底面支承：在每个构件朝下的面（法线 z < -0.3）上按 spacing 取样向下打射线。样点「被支承」当离下方构件表面 ≤ tol，
       或射线先打到朝下的面（样点埋在别的实体里，如瓦垄埋入屋面板），或样点 z ≤ tol（地面）。
    2) 接触支承：底面没有支承的构件，把它按包围盒各向外扩 tol 后与其它构件求三角面相交；相交即算接触支承
       （两端搭在别的梁上的梁、立在细望柱上的扶手）。
    两步都不成立判为悬空，报最小间隙。门扇（铰接）与地面补丁默认豁免。返回 (悬空列表, 全部记录)。"""
    parts = _world_parts(a, lod)
    sv, st, sown = _tri_soup(parts)
    o = len(sv)
    sv.extend([Vector((-1e4, -1e4, 0)), Vector((1e4, -1e4, 0)), Vector((1e4, 1e4, 0)), Vector((-1e4, 1e4, 0))])
    st.extend([(o, o + 1, o + 2), (o, o + 2, o + 3)]); sown.extend([-1, -1])
    soup = BVHTree.FromPolygons(sv, st, all_triangles=True, epsilon=0.0)
    out = check_floating_below(a, parts, tol, spacing, exempt_tags)
    for rec in out:
        rec['support'] = 'below' if rec['supported'] else 'none'
        if rec['supported']:
            continue
        pi = rec['_pi']
        gg = _grown(parts[pi][1], tol)
        gv, gt, _ = _tri_soup([(parts[pi][0], gg)])
        tb = BVHTree.FromPolygons(gv, gt, all_triangles=True, epsilon=0.0)
        hits = {sown[j] for _, j in tb.overlap(soup) if sown[j] != pi}
        if hits:
            rec['support'] = 'contact'
            rec['contacts'] = sorted(parts[h][0]['name'] if h >= 0 else 'GROUND' for h in hits)[:6]
    for rec in out:
        rec.pop('_pi', None)
        rec['floating'] = rec['support'] == 'none'
    return [r for r in out if r['floating']], out


def check_floating_below(a, parts, tol, spacing, exempt_tags):
    """check_floating 的第 1 步（底面射线），返回每个构件的取样记录。"""
    allv, allf, owner = [], [], []
    for pi, (c, g) in enumerate(parts):
        o = len(allv)
        allv.extend(Vector(v) for v in g.verts)
        for f in g.faces:
            allf.append(tuple(i + o for i in f)); owner.append(pi)
    # 地面
    o = len(allv)
    allv.extend([Vector((-1e4, -1e4, 0)), Vector((1e4, -1e4, 0)), Vector((1e4, 1e4, 0)), Vector((-1e4, 1e4, 0))])
    allf.append((o, o + 1, o + 2, o + 3)); owner.append(-1)
    tree = BVHTree.FromPolygons(allv, allf, all_triangles=False, epsilon=0.0)
    down = Vector((0, 0, -1))
    out = []
    for pi, (c, g) in enumerate(parts):
        if set(c['tags']) & set(exempt_tags):
            continue
        samples = []
        for fi in range(len(g.faces)):
            pts, n = _face_info(g, fi)
            if n.z > -0.3:
                continue
            # 在多边形上取样（扇形三角剖分；每个三角形沿两条边各按 spacing 分格，细长面也能取到细柱顶）
            for k in range(1, len(pts) - 1):
                A, B, C = pts[0], pts[k], pts[k + 1]
                mu = max(1, math.ceil((B - A).length / spacing)); mv = max(1, math.ceil((C - A).length / spacing))
                for i in range(mu + 1):
                    for jj in range(mv + 1):
                        u, v = (i + 1 / 3) / (mu + 1), (jj + 1 / 3) / (mv + 1)
                        if u + v < 1:
                            samples.append(A + (B - A) * u + (C - A) * v)
        if not samples:
            continue
        ok, gaps = 0, []
        for p in samples[:4000]:
            if p.z <= tol:
                ok += 1; continue
            start = p + Vector((0, 0, 1e-4))
            dist_acc = 0.0
            hit_ok = None
            cur = start
            for _ in range(64):
                loc, nor, idx, dist = tree.ray_cast(cur, down, 1e4)
                if loc is None:
                    hit_ok = False; gaps.append(float('inf')); break
                if owner[idx] == pi:          # 打到自己：穿过去继续
                    cur = loc + down * 1e-5; dist_acc += dist + 1e-5; continue
                d_total = dist_acc + dist - 1e-4
                if nor.z < -1e-6 or d_total <= tol:
                    hit_ok = True
                else:
                    hit_ok = False; gaps.append(d_total)
                break
            ok += 1 if hit_ok else 0
        rec = {'name': c['name'], 'tags': c['tags'], 'samples': len(samples), 'supported': ok,
               'min_gap': round(min(gaps), 4) if gaps else 0.0, '_pi': pi}
        out.append(rec)
    return out


def _shrunk(g, d=0.002):
    """按包围盒中心把几何各向内缩 d（穿插判定用，剔除正常贴面接触）。"""
    lo, hi = g.bbox()
    c = [(lo[k] + hi[k]) / 2 for k in range(3)]
    s = [max(0.0, (hi[k] - lo[k] - 2 * d) / max(hi[k] - lo[k], 1e-9)) for k in range(3)]
    return Geo([tuple(c[k] + (v[k] - c[k]) * s[k] for k in range(3)) for v in g.verts], g.faces)


def _bbox_overlap(b1, b2, pad=0.0):
    """两个包围盒是否重叠（pad 为容差）。"""
    return all(b1[0][k] - pad <= b2[1][k] and b2[0][k] - pad <= b1[1][k] for k in range(3))


def check_intersections(a, shrink=0.002, allowed=ALLOWED_INTERSECT, lod=0):
    """穿插检测：两两构件先比包围盒，再用 BVH 求三角面相交（各自先向中心收缩 shrink，以剔除正常的贴面接触）。
    返回 (意外穿插列表, 全部穿插列表)；每项含两构件名、tag、重叠包围盒尺寸、允许原因。她有意埋入的组合（瓦垄/正脊入板、
    梁顶/墙顶/檩条入板底、檩条入山墙）按 ALLOWED_INTERSECT 记为允许；两件的重叠区中心落在某块屋面板实体内
    （都埋进板里，外面看不见）也记为允许。"""
    parts = _world_parts(a, lod)
    sh = [(c, _shrunk(g, shrink)) for c, g in parts]
    boxes = [g.bbox() for _, g in sh]
    trees = [None] * len(sh)
    slabs = []
    for c, g in parts:
        if 'slab' in c['tags']:
            sv, stt, _ = _tri_soup([(c, g)])
            slabs.append((c, BVHTree.FromPolygons(sv, stt, all_triangles=True, epsilon=0.0)))
    allp, bad = [], []
    for i in range(len(sh)):
        for k in range(i + 1, len(sh)):
            if not _bbox_overlap(boxes[i], boxes[k]):
                continue
            if trees[i] is None:
                trees[i] = _bvh(sh[i][1])
            if trees[k] is None:
                trees[k] = _bvh(sh[k][1])
            pairs = trees[i].overlap(trees[k])
            if not pairs:
                continue
            ci, ck = sh[i][0], sh[k][0]
            ov = [round(min(boxes[i][1][d], boxes[k][1][d]) - max(boxes[i][0][d], boxes[k][0][d]), 4) for d in range(3)]
            ok = any(frozenset((ta, tb)) in allowed for ta in (ci['tags'] or ['?']) for tb in (ck['tags'] or ['?']))
            why = 'tags' if ok else None
            if not ok:
                # 两件都埋进同一块屋面板、相交处整个落在板内（如瓦垄底与檐枋顶在板里相碰）——看不见，记为允许
                cen = [Vector(((max(boxes[i][0][d], boxes[k][0][d]) + min(boxes[i][1][d], boxes[k][1][d])) / 2 for d in range(3)))]
                for sc, sg in slabs:
                    if all(_inside(p, sg) for p in cen):
                        ok, why = True, f'hidden in {sc["name"]}'
                        break
            rec = {'a': ci['name'], 'b': ck['name'], 'tags': (ci['tags'], ck['tags']), 'tri_pairs': len(pairs), 'overlap_box': ov,
                   'allowed': ok, 'why': why}
            allp.append(rec)
            if not ok:
                bad.append(rec)
    return bad, allp


def _inside(p, tree, tries=3):
    """点是否在闭合网格内（向上射线数交点奇偶，换几个方向取多数）。tree 为该网格的 BVH。"""
    votes = 0
    for d in (Vector((0, 0, 1)), Vector((0.31, 0.17, 0.93)).normalized(), Vector((-0.23, 0.41, 0.88)).normalized())[:tries]:
        cnt, cur = 0, Vector(p)
        for _ in range(64):
            loc, nor, idx, dist = tree.ray_cast(cur, d, 1e4)
            if loc is None:
                break
            cnt += 1
            cur = loc + d * 1e-6
        votes += cnt % 2
    return votes * 2 > tries


def _poly_area_2d(P):
    """二维多边形面积（鞋带公式）。"""
    return 0.5 * abs(sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P))))


def _clip(subject, clipper):
    """Sutherland-Hodgman：凸多边形 clipper 裁剪 subject（2D）。"""
    def inside(p, a, b):
        """Sutherland-Hodgman：点 p 是否在有向边 a->b 左侧（含边上）。"""
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12

    def inter(p, q, a, b):
        """线段 p-q 与直线 a-b 的交点。"""
        x1, y1, x2, y2 = p[0], p[1], q[0], q[1]; x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-15:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    out = subject
    # 保证 clipper 逆时针
    if sum(clipper[i][0] * clipper[(i + 1) % len(clipper)][1] - clipper[(i + 1) % len(clipper)][0] * clipper[i][1]
           for i in range(len(clipper))) < 0:
        clipper = clipper[::-1]
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i + 1) % len(clipper)]
        inp = out; out = []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(inter(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(inter(s, e, a, b))
            s = e
    return out


def check_coplanar(a, tol=1e-4, min_area=1e-4, lod=0, ground_exempt=True):
    """共面重叠检测（z-fighting）：不同构件之间、法线同向且平面距离 < tol 的面，若投影重叠面积 > min_area 即报出。
    法线相反的贴面（盒子相接、墙顶贴屋面板底）不报。ground_exempt：z=0 上朝下的面（贴地的底面，如穿过地坪的
    檐柱底与地坪底）从下面看不到，不报（她的 S84 柱底与地坪底同在 y=0）。"""
    from mathutils.geometry import tessellate_polygon
    parts = _world_parts(a, lod)
    buckets = collections.defaultdict(list)
    for pi, (c, g) in enumerate(parts):
        for fi in range(len(g.faces)):
            pts, n = _face_info(g, fi)
            if n.length < 0.5:
                continue
            if ground_exempt and n.z < -0.9999 and all(abs(p.z) < tol for p in pts):
                continue
            d = n.dot(pts[0])
            tris = [[pts[i] for i in t] for t in tessellate_polygon([pts])] if len(pts) > 3 else [pts]
            buckets[(round(n.x, 3), round(n.y, 3), round(n.z, 3))].append((d, pi, tris, n))
    hits, seen = [], set()
    for key, lst in buckets.items():
        lst.sort(key=lambda e: e[0])
        for i in range(len(lst)):
            d, pi, TP, n = lst[i]
            k = i + 1
            while k < len(lst) and lst[k][0] - d <= tol:
                e, pk, TQ, m = lst[k]
                k += 1
                if pi == pk or n.dot(m) < 0.9999:
                    continue
                ax = max(range(3), key=lambda q: abs(n[q]))
                ia, ib = [q for q in range(3) if q != ax]
                ar = 0.0
                for P in TP:
                    for Q in TQ:
                        inter = _clip([(p[ia], p[ib]) for p in P], [(q[ia], q[ib]) for q in Q])
                        if len(inter) >= 3:
                            ar += _poly_area_2d(inter) / max(abs(n[ax]), 1e-6)
                if ar > min_area:
                    pair = tuple(sorted((parts[pi][0]['name'], parts[pk][0]['name'])))
                    if pair not in seen:
                        seen.add(pair)
                        hits.append({'a': pair[0], 'b': pair[1], 'area': round(ar, 5), 'normal': [round(x, 3) for x in n]})
    return hits


def check_grounded(a, tol=0.002, lod=0):
    """落地检测：资产最低点应在 z=0（地面补丁、基础等低于地面的构件需带 'ground'/'below_grade' 标签另计）。"""
    zmin, zmin_all = 1e9, 1e9
    for c, g in _world_parts(a, lod):
        lo, _ = g.bbox()
        zmin_all = min(zmin_all, lo[2])
        if not set(c['tags']) & {'ground', 'below_grade'}:
            zmin = min(zmin, lo[2])
    return {'zmin_building': round(zmin, 4), 'zmin_all': round(zmin_all, 4), 'grounded': abs(zmin) <= tol}


def check_clearance(a, center, direction, min_width=0.8, min_height=1.9, probe=1.2, grid=0.1, lod=0, ignore_tags=()):
    """入口净空检测。center = 门洞中线在门槛面上的点（世界坐标），direction = 通行方向（水平单位向量）。
    1) 在 center 上方 1.0 m 处沿墙面左右打射线，量出两侧框/墙的距离 -> 净宽；从门槛面向上打射线 -> 净高。
    2) 在 min_width × min_height 的通行矩形内按 grid 取样，沿 ±direction 各打 probe 米：碰到任何构件（如关着的门扇、
       伸进来的梁）即记为阻挡。返回 {'clear_width','clear_height','blocked','blockers','pass'}。"""
    parts = [(c, g) for c, g in _world_parts(a, lod) if not set(c['tags']) & set(ignore_tags)]
    allv, allf, owner = [], [], []
    for pi, (c, g) in enumerate(parts):
        o = len(allv)
        allv.extend(Vector(v) for v in g.verts)
        for f in g.faces:
            allf.append(tuple(i + o for i in f)); owner.append(pi)
    tree = BVHTree.FromPolygons(allv, allf, all_triangles=False, epsilon=0.0)
    C = Vector(center); D = Vector(direction).normalized(); T = Vector((-D.y, D.x, 0)).normalized(); Z = Vector((0, 0, 1))

    def ray(p, d, far=20.0):
        """沿方向 d 打射线，返回 (距离, 命中构件名)，未命中返回 (far, None)。"""
        loc, nor, idx, dist = tree.ray_cast(p, d, far)
        return (dist, parts[owner[idx]][0]['name']) if loc is not None else (far, None)
    mid = C + Z * 1.0
    wl, nl = ray(mid, -T); wr, nr = ray(mid, T)
    h, nh = ray(C + Z * 0.02, Z)
    h += 0.02
    blockers = collections.Counter(); blocked = 0; total = 0
    nw = max(1, int(min_width / grid)); nhh = max(1, int(min_height / grid))
    for i in range(nw + 1):
        for k in range(nhh + 1):
            p = C + T * (-min_width / 2 + min_width * i / nw) + Z * (0.03 + (min_height - 0.06) * k / nhh)
            total += 1
            hit = False
            for s in (1, -1):
                dist, nm = ray(p, D * s, probe)
                if nm is not None and dist < probe:
                    blockers[nm] += 1; hit = True
            blocked += hit
    res = {'clear_width': round(wl + wr, 4), 'left': (round(wl, 4), nl), 'right': (round(wr, 4), nr), 'clear_height': round(h, 4),
           'head': nh, 'samples': total, 'blocked': blocked, 'blockers': dict(blockers.most_common(6))}
    res['pass'] = res['clear_width'] >= min_width - 1e-6 and res['clear_height'] >= min_height - 1e-6 and blocked == 0
    return res


def report_checks(a, lod=0, verbose=True):
    """一次跑悬空 / 穿插 / 共面 / 落地四项检查并打印摘要；返回 dict。"""
    fl, _allf = check_floating(a, lod=lod)
    bad, allp = check_intersections(a, lod=lod)
    cop = check_coplanar(a, lod=lod)
    gr = check_grounded(a, lod=lod)
    rep = {'floating': fl, 'intersections_unexpected': bad, 'intersections_allowed': [p for p in allp if p['allowed']],
           'coplanar': cop, 'grounded': gr}
    if verbose:
        print(f'[检查] {a.prefix} LOD{lod}: 构件 {len(a.components)}')
        print(f'  悬空 {len(fl)}', [(r["name"], r["min_gap"]) for r in fl][:12])
        print(f'  意外穿插 {len(bad)}', [(r["a"], r["b"], r["overlap_box"]) for r in bad][:12])
        print(f'  允许的埋入 {len(rep["intersections_allowed"])} 对（瓦垄/脊入板、梁顶入板底等）')
        print(f'  共面同向重叠 {len(cop)}', cop[:8])
        print(f'  落地 {gr}')
    return rep


# --------------------------------------------------------------------------------------------
# 7. 从 LOD0 物体还原组件（用于手工修过的 LOD0 再派生 LOD1/2）
# --------------------------------------------------------------------------------------------
def assembly_from_objects(objs, slug, variant='A', evidence='C', profile='house'):
    """从 LOD0 物体还原 Assembly：带 obj['ly'] 的按记录重建（可正确派生 LOD1/2）；
    不带记录的手工物体按世界坐标几何作为 'keep' 组件收进来，材料从材质名 LY_P01_<mat>__* 或 obj['ly_mat'] 推断，
    并打印提示（手工件在各 LOD 不变——需要降档的手工件请改用库函数生成）。"""
    a = Assembly(slug, variant, evidence=evidence, profile=profile, make_objects=False)
    for o in objs:
        if o.type != 'MESH':
            continue
        if 'ly' in o.keys():
            c = json.loads(o['ly'])
            c['id'] = len(a.components)
            c.pop('_obj', None)
            a.components.append(c)
            continue
        mat = o.get('ly_mat')
        if not mat and o.data.materials:
            mm = re.match(r'LY_P01_([a-z_]+?)__', o.data.materials[0].name or '')
            mat = mm.group(1) if mm else None
        if mat not in PALETTE:
            print(f'[警告] {o.name} 材料无法识别，跳过')
            continue
        M = o.matrix_world
        g = Geo([tuple(M @ v.co) for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])
        print(f'[提示] {o.name} 无 ly 记录，作为各 LOD 不变件收入')
        a.components.append(dict(id=len(a.components), name=o.name, kind='mesh', mat=mat,
                                 params={'verts': [_v(p) for p in g.verts], 'faces': [list(f) for f in g.faces]},
                                 lod='keep', tags=['manual'], node=None))
    return a


def clear_scene():
    """清空当前场景（headless 脚本开头用）。"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _IMG_CACHE.clear()
    _MAT_STATE.clear()
