# -*- coding: utf-8 -*-
"""LY-003 配准南北宫与东北约束：唯一生成/核对脚本。只读仓库与前置席位，只写 LY-003/。

usage:
  python -I -B build.py --lab D:/GitHub/creation-notebook-lab --commit bce3211 \
      --workpacks D:/GitHub/creation-notebook-workpacks [--external <外部来源目录>]

退出码 0 = 冻结SHA一致、示意坐标可由像素逐点重算、所有引文在来源字节中逐字找到（或明确记为未复核）、
负例全部按预期失败、控制点/变换/准入表与计算一致。它不表示任何宫区可以落位。
"""
import argparse, hashlib, io, json, math, re, subprocess, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ly003_data as D  # noqa: E402
import glbinfo  # noqa: E402  (LY-001/source/glbinfo.py 原样复制，SHA 记在 inputs.json)

sys.stdout.reconfigure(encoding='utf-8')
ap = argparse.ArgumentParser()
ap.add_argument('--lab', required=True)
ap.add_argument('--commit', required=True)
ap.add_argument('--workpacks', required=True)
ap.add_argument('--external', default=None)
A = ap.parse_args()
LAB, WP = Path(A.lab), Path(A.workpacks)
OUT = WP / 'LY-003'
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git_bytes(path):
    return subprocess.run(['git', '-C', str(LAB), 'show', f'{A.commit}:{path}'], capture_output=True, check=True).stdout


def wjson(rel, obj):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


FAIL = []


def check(cond, msg):
    (log('  ok  ', msg) if cond else (FAIL.append(msg), log('  FAIL', msg)))


# ---------------------------------------------------------------- inputs
full_commit = subprocess.run(['git', '-C', str(LAB), 'rev-parse', A.commit], capture_output=True, text=True, check=True).stdout.strip()
log('commit', full_commit)
check(full_commit == D.BASE_COMMIT, 'commit 解析为任务基线 bce3211f…')
repo = {}
for p in D.REPO_INPUTS:
    b = git_bytes(p)
    repo[p] = b
inputs_repo = [{'path': p, 'bytes': len(b), 'sha256_commit_bytes': sha(b)} for p, b in repo.items()]
prior = []
for p in D.PRIOR_INPUTS:
    b = (WP / p).read_bytes()
    prior.append({'path': p, 'bytes': len(b), 'sha256': sha(b)})
glbinfo_copy = sha((HERE / 'glbinfo.py').read_bytes())
glbinfo_orig = sha((WP / 'LY-001/source/glbinfo.py').read_bytes())
check(glbinfo_copy == glbinfo_orig, 'source/glbinfo.py 与 LY-001 原件字节一致')

EGP = 'docs/cities/luoyang/data/evidence/evidence-geometry.json'
check(sha(repo[EGP]) == D.FROZEN_EVIDENCE_SHA, 'evidence-geometry.json 提交字节 = 冻结 fa8b7002…')
EG = json.loads(repo[EGP].decode('utf-8'))
F = {f['id']: f for f in EG['features']}
FR = EG['frame']
cal = FR['calibration']

# ---------------------------------------------------------------- 1 坐标系重算（轴向、原点、比例）
ox, oy = FR['origin_definition']['source_pixel']
mpp = cal['meters_per_pixel']
check(abs(mpp - cal['bar_label_m'] / cal['bar_span_px']) < 1e-12, '比例 = 500米/49像素')


def px2m(px, py, s=mpp):
    return [(px - ox) * s, (oy - py) * s]


def iter_pairs(geom):
    if geom is None:
        return []
    c = geom['coordinates']
    t = geom['type']
    if t == 'Point':
        return [c]
    if t == 'LineString':
        return c
    if t == 'Polygon':
        return c[0] if isinstance(c[0][0], (list, tuple)) else c
    raise ValueError(t)


rederive = []
maxres = 0.0
for f in EG['features']:
    g, sp = f.get('geometry'), f.get('source_pixel_geometry')
    if not g:
        continue
    G, P = iter_pairs(g), iter_pairs(sp)
    assert len(G) == len(P), f['id']
    r = max(math.hypot(*(np.subtract(px2m(*p), q))) for p, q in zip(P, G))
    maxres = max(maxres, r)
    rederive.append({'id': f['id'], 'vertices': len(G), 'max_residual_m': round(r, 6)})
check(maxres < 1e-3 * 2, f'36个已置要素的示意米坐标可由像素×(500/49)、原点{ox},{oy}、像素y向下=北向上逐点重算（最大残差 {maxres:.6f} 米，即保存到千分位的舍入）')
cd = repo['docs/cities/luoyang/city-data.mjs'].decode('utf-8')
m = re.search(r'"coordinateFrame":\s*\{[^}]*"id":\s*"([^"]+)"[^}]*"axes":\s*"([^"]+)"[^}]*"geographicOrigin":\s*(\w+)[^}]*"rotationToTrueNorth":\s*(\w+)', cd)
check(m and m.group(1) == FR['id'], f'city-data.mjs coordinateFrame.id = {FR["id"]}（城景直接用示意坐标）')
check(m and m.group(3) == 'null' and m.group(4) == 'null', 'city-data.mjs 无地理原点、无真北旋转')
check(FR['three_conversion'] == '[east,height,-north]', 'glTF 换算 [东, 高, -北]')
si = json.loads(repo['docs/cities/luoyang/data/west/storage-interface.json'])
tc = F['region_taicang_B']['geometry']['coordinates']
check(abs(si['camera']['target'][0] - tc[0]) < 1e-3 and abs(-si['camera']['target'][2] - tc[1]) < 1e-3, '仓储相机目标 = region_taicang_B（换算后）')
wjson('qa/frame-rederive.json', {
    'frame': FR['id'], 'origin_px': [ox, oy], 'meters_per_pixel': mpp, 'axis': 'x=(px-258)*s 向东；y=(1385-py)*s 向北；glTF Z=-y',
    'max_residual_m': round(maxres, 6), 'features': rederive,
    'cityDataFrame': {'id': m.group(1), 'axes': m.group(2), 'geographicOrigin': m.group(3), 'rotationToTrueNorth': m.group(4)},
    'meaning': '这只证明“示意图像素→项目坐标”这一步定义一致、可重算；不证明示意图与地面的关系。'})

# ---------------------------------------------------------------- 2 城垣边长与实测长度
W = F['city_wall_schematic_B']['geometry']['coordinates'][0]
V = [tuple(p) for p in W[:-1]]


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


sides = {
    'north': {'path': 'v0→v4（西北角至东北抹角起点，含北垣折段）', 'm': plen(V[0:5])},
    'north_with_chamfer': {'path': 'v0→v5（含东北抹角）', 'm': plen(V[0:6])},
    'north_straight_span': {'path': 'v0与v5东西坐标差', 'm': V[5][0] - V[0][0]},
    'east': {'path': 'v5→v9（东北抹角止点至南垣推定闭合点，含南段推定）', 'm': plen(V[5:10])},
    'west': {'path': 'v10→v12→v0（南垣推定闭合点至西北角）', 'm': plen(V[10:13] + [V[0]])},
}
sides['ns_extent'] = {'path': '最北点与最南点南北差', 'm': max(p[1] for p in V) - min(p[1] for p in V)}
sides['ew_extent'] = {'path': '最东点与最西点东西差', 'm': max(p[0] for p in V) - min(p[0] for p in V)}
cmp_rows = []
for s in D.SURVEY_LENGTHS:
    sch = sides[s['side']]['m']
    ratio = s['m'] / sch
    if s['kind'] == 'residual':
        verdict = '矛盾：残长大于示意全边长' if ratio > 1 else '不矛盾（残长≤全边长），但不能求比例'
    else:
        verdict = f'全长比例 {ratio:.3f}'
    cmp_rows.append({**s, 'schematic_m': round(sch, 1), 'survey_over_schematic': round(ratio, 4), 'verdict': verdict})
north_ratios = [r['survey_over_schematic'] for r in cmp_rows if r['side'] == 'north']
east_lb = max(r['survey_over_schematic'] for r in cmp_rows if r['side'] == 'east')
check(any(r['verdict'].startswith('矛盾') for r in cmp_rows), f'东垣残长3895米大于示意东边全长{sides["east"]["m"]:.1f}米：示意图南北向至少偏短{(east_lb - 1) * 100:.1f}%')
wjson('qa/side-lengths.json', {
    'schematic_sides_m': {k: {'path': v['path'], 'm': round(v['m'], 1)} for k, v in sides.items()},
    'comparisons': cmp_rows,
    'north_ratio_range': [min(north_ratios), max(north_ratios)],
    'east_residual_lower_bound_ratio': east_lb,
    'reading': ('三组实测数字互相不一致（北垣2523/2820/3700，西垣3500/3510/4290），且未说明是否含金墉城、量法是沿墙还是直线；'
                '只能说明示意图边长与实测差几个到十几个百分点、各边比例不一致，不能据此反算出唯一比例。')})

# ---------------------------------------------------------------- 3 自由度与候选变换
shared = [c for c in D.CONTROL_POINTS if c['schematic'] and c['survey']]


def usable_pairs(cps):
    """只有两边都给出数值坐标的点才算共同控制点。布尔标记不算。"""
    return [c for c in cps if isinstance(c.get('schematic_xy'), (list, tuple)) and isinstance(c.get('survey_xy'), (list, tuple))]


n_shared = len(usable_pairs(D.CONTROL_POINTS))
check(n_shared == 0 and len(shared) == 0, '共同控制点（两边都有坐标）= 0')
models = [
    {'model': '平移', 'dof': 2, 'min_points': 1, 'min_points_with_check': 2},
    {'model': '刚体（平移+旋转）', 'dof': 3, 'min_points': 2, 'min_points_with_check': 3},
    {'model': '相似（+等比缩放）', 'dof': 4, 'min_points': 2, 'min_points_with_check': 3},
    {'model': '仿射', 'dof': 6, 'min_points': 3, 'min_points_with_check': 4},
]
for mm in models:
    mm['available_points'] = n_shared
    mm['status'] = '欠定，不能求解' if n_shared < mm['min_points'] else ('可解但无独立校核' if n_shared < mm['min_points_with_check'] else '可解且可校核')
cands = [
    {'id': 'T0', 'what': '恒等（现行 luoyang-local-schematic-v01）', 'dof_solved': 0, 'params': {'s': 1.0},
     'basis': '示意图比例尺500米/49像素', 'residual': None, 'independent_check': '东垣残长检验失败（见 side-lengths）',
     'admissible_for_palace_placement': False},
]
for r in cmp_rows:
    if r['side'] == 'north':
        s = r['survey_over_schematic']
        east_scaled = sides['east']['m'] * s
        ok = east_scaled >= 3895
        cands.append({'id': f'T1-{r["set"]}', 'what': f'等比缩放（只用北垣全长，数值版本{r["set"]}）', 'dof_solved': 1,
                      'params': {'s': s, 'about': '示意原点（西南推定角）'}, 'basis': f'{r["quote"]} 北垣 {r["m"]} 米',
                      'residual': '1个量定1个参数，零冗余，无残差可算',
                      'independent_check': f'东边缩放后 {east_scaled:.0f} 米 {"≥" if ok else "<"} 东垣残长 3895 米 → {"不矛盾" if ok else "矛盾"}',
                      'admissible_for_palace_placement': False})
cands.append({'id': 'T2', 'what': '东西、南北分别缩放', 'dof_solved': 2,
              'params': {'sx': [min(north_ratios), max(north_ratios)], 'sy_lower_bound': east_lb},
              'basis': '北垣三说给 sx 区间；东垣残长只给 sy 下限', 'residual': '无冗余',
              'independent_check': '西垣残长三说（3500/3510/4290）互相差 22%，无法作为第三个独立量',
              'admissible_for_palace_placement': False})
for c in cands:
    c['note'] = '只改比例，不定平移和旋转；对宫墙落位没有帮助（宫墙在任何框架里都还没有坐标）。'
wjson('tables/transforms.json', {'shared_control_points': n_shared, 'dof_table': models, 'candidates': cands,
                                 'decision': '不选任何候选替换现行框架；宫区与水系配准结论：不可落位。'})

# ---------------------------------------------------------------- 4 误差预算（只算图上读取这一步）
s_lo, s_hi = cal['scale_interval_m_per_px']
pick = cal['feature_pick_uncertainty_px_each_axis']


def interval(xy):
    px = xy[0] / mpp
    py = xy[1] / mpp
    return {'x': [round(px * s_lo - pick * s_hi, 1), round(px * s_hi + pick * s_hi, 1)],
            'y': [round(py * s_lo - pick * s_hi, 1), round(py * s_hi + pick * s_hi, 1)]}


budget = {}
for fid in ['north_palace_extent_gao2023_B', 'south_palace_candidate_gao2023_B', 'palaces_connector_B', 'region_yongan_B', 'region_taicang_B', 'region_wuku_B', 'road_northeast_gate_link_B']:
    budget[fid] = [{'xy': p, 'interval_in_frame': interval(p)} for p in iter_pairs(F[fid]['geometry'])]
NP = F['north_palace_extent_gao2023_B']['geometry']['coordinates'][0][:-1]
SP = F['south_palace_candidate_gao2023_B']['geometry']['coordinates'][0][:-1]
np_east_x = max(p[0] for p in NP)
east_wall_x_at = V[5][0]  # 东北抹角止点 x
rel_px = (east_wall_x_at - np_east_x) / mpp
rel = {'what': '旧B北宫东界到同图东垣（v5）的东西距离', 'm': round(east_wall_x_at - np_east_x, 1),
       'scale_part_m': [round(rel_px * s_lo, 1), round(rel_px * s_hi, 1)],
       'pick_part_m': round(2 * pick * s_hi, 1)}
wjson('qa/error-budget.json', {
    'components': [
        {'id': 'e1', 'what': '描点读取', 'value': f'每轴 ±{pick} 像素 ≈ ±{pick * mpp:.1f} 米', 'status': '已量化（仓库冻结参数）'},
        {'id': 'e2', 'what': '比例尺端点读取', 'value': f'{s_lo:.3f}–{s_hi:.3f} 米/像素（±{(s_hi - s_lo) / 2 / mpp * 100:.1f}%）', 'status': '已量化'},
        {'id': 'e3', 'what': '示意图与地面的偏差', 'value': f'未知；城垣边长对照显示至少 {(east_lb - 1) * 100:.1f}% 的南北向偏短，各边不一致', 'status': '未量化，只有下限迹象'},
        {'id': 'e4', 'what': '东汉墙线与示意线（及与后期宫墙）的偏差', 'value': '未知；报道只说“略有摆动”', 'status': '未量化'},
    ],
    'per_feature_e1_e2_only': budget,
    'relative_example': rel,
    'reading': '表中区间只含 e1+e2；e3、e4 没有数，所以任何“误差≤X米”的宫墙落位说法都不成立。'})

# ---------------------------------------------------------------- 5 宫区尺寸冲突
np_w = [math.dist(NP[0], NP[1]), math.dist(NP[3], NP[2])]
np_h = [math.dist(NP[1], NP[2]), math.dist(NP[0], NP[3])]
sp_w = [math.dist(SP[0], SP[1]), math.dist(SP[3], SP[2])]
sp_h = [math.dist(SP[1], SP[2]), math.dist(SP[0], SP[3])]
L = D.LATER_PALACE_DIMS
pal = {
    'north_B': {'ew_edges_m': [round(x, 1) for x in np_w], 'ns_edges_m': [round(x, 1) for x in np_h]},
    'south_B': {'ew_edges_m': [round(x, 1) for x in sp_w], 'ns_edges_m': [round(x, 1) for x in sp_h]},
    'later_palace_city': {**L},
    'ratios_B_over_later': {'ew': round(np.mean(np_w) / L['ew_m'], 3), 'ns': round(np.mean(np_h) / L['ns_m'], 3)},
    'ew_excess_m': round(np.mean(np_w) - L['ew_m'], 1),
    'ns_coincidence': {'north_B_ns_mean_m': round(float(np.mean(np_h)), 1), 'later_ns_m_Q17': 1398,
                       'diff_m': round(float(np.mean(np_h)) - 1398, 1),
                       'reading': '旧B北宫南北边长与北魏宫城南北长（Q17：1398米）相差不到1米。可能只是巧合，也可能示意图的北宫南北长本就取自后期宫城实测；'
                                  '若是后者，旧B已混入后期数据。本包未能读到制图说明，记为待核，不作结论。'},
    'reading': ('若按Q05“东汉北宫范围与后期宫城大致相同”，旧B东西宽约为后期宫城的1.8倍、多出五百余米，南北长则接近。'
                '后期尺寸是三手、无位置，旧B是研究示意，二者都不能定东墙在哪；结论只是冲突真实存在、无法用现有资料消解。'),
}
check(pal['ratios_B_over_later']['ew'] > 1.5, f'旧B北宫东西宽 / 后期宫城 = {pal["ratios_B_over_later"]["ew"]}（定性冲突）')
wjson('qa/palace-dims.json', pal)

# ---------------------------------------------------------------- 6 几何工具


def seg_dist(p, a, b):
    p, a, b = map(np.asarray, (p, a, b))
    ab = b - a
    t = 0.0 if not ab.any() else max(0.0, min(1.0, float((p - a) @ ab / (ab @ ab))))
    return float(np.linalg.norm(p - (a + t * ab)))


def inside(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def dist_to_geom(p, geom):
    pts = iter_pairs(geom)
    if geom['type'] == 'Point':
        return math.dist(p, pts[0])
    if geom['type'] == 'Polygon':
        ring = pts[:-1] if pts[0] == pts[-1] else pts
        if inside(p, ring):
            return 0.0
        return min(seg_dist(p, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))
    return min(seg_dist(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def poly_poly_dist(A_, B_geom):
    """A_ 为凸包顶点列表；返回到 B 几何的最小距离（两向顶点-边），相交返回0。"""
    gpts = iter_pairs(B_geom)
    if any(inside(p, A_) for p in gpts) or any(dist_to_geom(p, B_geom) == 0 for p in A_):
        return 0.0
    d1 = min(dist_to_geom(p, B_geom) for p in A_)
    if B_geom['type'] == 'Point':
        return d1
    ring = A_
    d2 = min(seg_dist(q, ring[i], ring[(i + 1) % len(ring)]) for q in gpts for i in range(len(ring)))
    return min(d1, d2)


# ---------------------------------------------------------------- 7 悬置区（禁用区域）
RM = json.loads(repo['docs/cities/luoyang/data/c02v/research-mask.json'])
BP = RM['buffer_policy']
HOLD = [
    {'id': 'HZ-N', 'base': 'north_palace_extent_gao2023_B', 'buffer_m': BP['B_palace_candidates_m'], 'presentation_m': 75,
     'meaning': '北宫悬置区：旧B北宫外扩200米（沿用仓库 c02v buffer_policy 的宫区筛查值）。不是宫墙位置；新东/南墙可能在其内或其外。'},
    {'id': 'HZ-S', 'base': 'south_palace_candidate_gao2023_B', 'buffer_m': BP['B_palace_candidates_m'], 'presentation_m': 75,
     'meaning': '南宫悬置区：同上；南宫位置未勘查清（Q01）。'},
    {'id': 'HZ-C', 'base': 'palaces_connector_B', 'buffer_m': BP['B_road_centerlines_m'], 'presentation_m': 75,
     'meaning': '两宫复道示意线外扩80米（仓库道路中心线筛查值）。'},
    {'id': 'HZ-Y', 'base': 'region_yongan_B', 'buffer_m': BP['regional_label_points_m'], 'presentation_m': 75,
     'meaning': '永安宫标签点外扩400米（仓库区域标签筛查值）；永安宫范围未知。'},
]
PRE = json.loads(repo['docs/cities/luoyang/data/west/road-preconstraints.json'])
held_roads = [r['feature_id'] for r in PRE['rows'] if r['classification'] == 'hold_palace_interface']
for rid in held_roads:
    HOLD.append({'id': 'HR-' + rid.replace('road_', '').replace('_B', ''), 'base': rid, 'buffer_m': BP['B_road_centerlines_m'], 'presentation_m': 75,
                 'meaning': '仓库 road-preconstraints 已列 hold_palace_interface 的示意道路；靠宫缘部分悬置，外扩80米。'})
check(BP['status'].startswith('chosen engineering screening'), '筛查外扩值是仓库已有的工程筛查值，不是历史误差（沿用其原定义）')
for h in HOLD:
    g = F[h['base']]['geometry']
    xs = [p[0] for p in iter_pairs(g)]
    ys = [p[1] for p in iter_pairs(g)]
    h['bbox_buffered'] = [round(min(xs) - h['buffer_m'], 1), round(min(ys) - h['buffer_m'], 1), round(max(xs) + h['buffer_m'], 1), round(max(ys) + h['buffer_m'], 1)]
    h['e1_e2_max_shift_m'] = round(max(max(abs(iv['interval_in_frame']['x'][0] - p[0]), abs(iv['interval_in_frame']['x'][1] - p[0]),
                                           abs(iv['interval_in_frame']['y'][0] - p[1]), abs(iv['interval_in_frame']['y'][1] - p[1]))
                                       for p, iv in ((p, {'interval_in_frame': interval(p)}) for p in iter_pairs(g))), 1)
    h['buffer_covers_e1_e2'] = h['buffer_m'] >= h['e1_e2_max_shift_m']
wjson('tables/hold-zones.json', {
    'frame': FR['id'], 'units': 'schematic_m', 'rule': '点到 base 几何的距离 ≤ buffer_m 即在悬置区内；base 为冻结 evidence-geometry 要素',
    'buffer_policy_source': {'path': 'docs/cities/luoyang/data/c02v/research-mask.json', 'buffer_policy': BP},
    'zones': HOLD,
    'forbidden_in_zone': ['任何带城市矩阵的宫殿、宫墙、宫门、复道、宫墙水道安装', '把示意线端点当宫门', '在悬置区边界上描东汉墙线'],
    'not_meaning': '悬置区外≠已证明在宫外；只说明不与旧研究示意相冲突。e3/e4 未量化。'})

# ---------------------------------------------------------------- 8 东北约束
gb = repo['docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb']
gsrc = json.loads(repo['docs/cities/luoyang/progress-assets/granary-city-v1/source.json'])
check(sha(gb) == gsrc['files'][0]['sha256'], 'granary-city-LOD0.glb 提交字节 SHA = source.json 登记值')
tmp = OUT / 'qa' / '_tmp_granary.glb'
tmp.write_bytes(gb)
info, boxes, tris = glbinfo.summarize(str(tmp), want_tris=True)
tmp.unlink()
pts2 = np.c_[tris.reshape(-1, 3)[:, 0], -tris.reshape(-1, 3)[:, 2]]
H = hull(pts2.round(3).tolist())
check(len(H) >= 3, f'仓储组实际GLB三角面 {len(tris)} 个，平面凸包 {len(H)} 点')
cityring = V
ne = {'granary': {'glb': 'granary-city-LOD0.glb', 'sha256': sha(gb), 'triangles': int(len(tris)),
                  'hull_bbox_xy': [round(min(p[0] for p in H), 2), round(min(p[1] for p in H), 2), round(max(p[0] for p in H), 2), round(max(p[1] for p in H), 2)],
                  'all_hull_points_inside_city_wall_B': all(inside(p, cityring) for p in H),
                  'min_dist_to_city_wall_line_m': round(min(dist_to_geom(p, F['city_wall_schematic_B']['geometry']) if not inside(p, cityring) else
                                                            min(seg_dist(p, cityring[i], cityring[(i + 1) % len(cityring)]) for i in range(len(cityring))) for p in H), 1)},
      'distances_m': []}
for h in HOLD:
    d = poly_poly_dist(H, F[h['base']]['geometry'])
    ne['distances_m'].append({'zone': h['id'], 'base': h['base'], 'dist_to_base_m': round(d, 1), 'buffer_m': h['buffer_m'],
                              'outside_zone': d > h['buffer_m'], 'margin_m': round(d - h['buffer_m'], 1)})
for fid in ['region_taicang_B', 'region_wuku_B', 'gate_shangdong_B']:
    ne['distances_m'].append({'zone': None, 'base': fid, 'dist_to_base_m': round(poly_poly_dist(H, F[fid]['geometry']), 1)})
# 东北C试放筛查区（栅格5米）
NPx_max = max(p[0] for p in NP)
NPy_min = min(p[1] for p in NP)
step = 5.0
xs = np.arange(NPx_max, 2700, step) + step / 2
ys = np.arange(NPy_min, 4000, step) + step / 2
cells = []
for y in ys:
    for x in xs:
        p = (float(x), float(y))
        if not inside(p, cityring):
            continue
        if any(dist_to_geom(p, F[h['base']]['geometry']) <= h['buffer_m'] for h in HOLD):
            continue
        cells.append(p)
area = len(cells) * step * step
ne['screening_area'] = {'id': 'NE-C-SCREEN', 'rule': f'城垣B内 ∩ x ≥ {NPx_max:.1f}（旧B北宫东界）∩ y ≥ {NPy_min:.1f}（旧B北宫南界）∩ 不在任何悬置区内；5米栅格',
                        'cells': len(cells), 'area_m2': area,
                        'granary_hull_inside_share': round(sum(1 for p in H if any(abs(p[0] - c[0]) <= step / 2 and abs(p[1] - c[1]) <= step / 2 for c in cells)) / len(H), 3),
                        'meaning': 'C工程筛查范围：在这里试放可回退局部包不与旧研究示意冲突。不是“宫外”的证明，不是历史位置，不是入城准入。'}
ne['C_NE_APPROACH_LOCAL'] = {'found_in_commit': 'C_NE_APPROACH_LOCAL' in cd or any(b'C_NE_APPROACH_LOCAL' in b for b in repo.values()),
                             'status': '在 bce3211 的 city-data.mjs 与本包读取的仓库文件中未找到；端点几何无法核对，交 LY-039 提供实际GLB后按 NE-C-SCREEN 与悬置区复核'}
check(not ne['C_NE_APPROACH_LOCAL']['found_in_commit'], 'C_NE_APPROACH_LOCAL 未在读取的提交文件中出现（如实记为缺件）')
check(all(r['outside_zone'] for r in ne['distances_m'] if r['zone']), '现入城仓储组凸包不在任何悬置区内（与旧示意不冲突，非“宫外”证明）')
wjson('qa/ne-checks.json', ne)
wjson('tables/ne-screening-cells.json', {'step_m': step, 'cell_centers_xy': [[round(a, 1), round(b, 1)] for a, b in cells]})

# ---------------------------------------------------------------- 9 引文逐字核对
ext = Path(A.external) if A.external else None


def norm_text(b, fname):
    if fname.endswith('.txt'):
        t = b.decode('utf-8', 'replace')
    else:
        t = b.decode('utf-8', 'replace')
        t = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
        t = re.sub(r'<[^>]+>', '', t)
        t = t.replace('&nbsp;', '').replace('&#160;', '')
    return re.sub(r'\s+', '', t)


SRC_SHA = {}
qrows = []
for k, s in D.SOURCES.items():
    if ext and (ext / s['file']).exists():
        b = (ext / s['file']).read_bytes()
        SRC_SHA[k] = {'file': s['file'], 'sha256': sha(b), 'bytes': len(b), 'text': norm_text(b, s['file'])}
        if 'pdf' in s and (ext / s['pdf']).exists():
            SRC_SHA[k]['pdf_sha256'] = sha((ext / s['pdf']).read_bytes())
for q in D.QUOTES:
    nq = re.sub(r'\s+', '', q['text'])
    row = {'id': q['id'], 'src': q['src'], 'loc': q['loc'], 'quote': q['text'], 'chars': len(nq),
           'oneSentence': not re.search(r'[。！？]', q['text'][:-1])}
    if q['src'] in SRC_SHA:
        row['sourceSha256'] = SRC_SHA[q['src']]['sha256']
        row['found'] = nq in SRC_SHA[q['src']]['text']
        row['result'] = '来源字节中逐字找到' if row['found'] else '未找到'
    else:
        row['found'] = None
        row['result'] = '未复核（缺 --external）'
    qrows.append(row)
for r in qrows:
    check(r['oneSentence'], f'{r["id"]} 不超过一句')
    if r['found'] is not None:
        check(r['found'], f'{r["id"]} {r["result"]}')
GAO_PDF_EXPECT = 'c10cd82d71a864f4441f539f178432d09a354dbe02f28bdcf97df301885d5b51'
if 'X-GAO' in SRC_SHA:
    check(SRC_SHA['X-GAO'].get('pdf_sha256') == GAO_PDF_EXPECT, '高2023 PDF SHA 与 LY-002 登记一致')
wjson('qa/quote-check.json', {'external_dir_given': bool(ext), 'total': len(qrows),
                              'found': sum(1 for r in qrows if r['found']), 'unverified': sum(1 for r in qrows if r['found'] is None), 'rows': qrows})

# ---------------------------------------------------------------- 10 负例
neg = []


def negcase(name, cond_should_be_true):
    neg.append({'case': name, 'detected': bool(cond_should_be_true)})
    check(cond_should_be_true, '负例 ' + name)


c_np = np.mean(NP, axis=0).tolist()
negcase('旧B北宫中心点必须落在 HZ-N 内', dist_to_geom(c_np, F['north_palace_extent_gao2023_B']['geometry']) <= 200)
fake = [dict(c, survey=True, schematic=True) for c in D.CONTROL_POINTS]
negcase('只把布尔标记改成 True、不给坐标，共同控制点仍为0（不能靠改标签造出配准）', len(usable_pairs(fake)) == 0)
bad = bytearray(repo[EGP])
bad[100] ^= 1
negcase('改动冻结证据一个字节，SHA 不再匹配', sha(bytes(bad)) != D.FROZEN_EVIDENCE_SHA)
wrong = max(math.hypot(*(np.subtract(px2m(*p, s=10.0), q))) for f in EG['features'] if f.get('geometry')
            for p, q in zip(iter_pairs(f['source_pixel_geometry']), iter_pairs(f['geometry'])))
negcase(f'用错误比例10.0米/像素重算，残差 {wrong:.1f} 米被检出', wrong > 1.0)
if SRC_SHA:
    k0 = next(iter(SRC_SHA))
    negcase('伪造引文“东汉北宫东墙坐标已公布”在来源中找不到', '东汉北宫东墙坐标已公布' not in SRC_SHA[k0]['text'] and all('东汉北宫东墙坐标已公布' not in v['text'] for v in SRC_SHA.values()))
shiftH = [(p[0] - (np.mean([q[0] for q in H]) - c_np[0]), p[1] - (np.mean([q[1] for q in H]) - c_np[1])) for p in H]
negcase('把仓储凸包平移到旧B北宫中心，距离判为0并落入悬置区', poly_poly_dist(shiftH, F['north_palace_extent_gao2023_B']['geometry']) == 0.0)
wjson('qa/selftest.json', {'negatives': neg})

# ---------------------------------------------------------------- 11 控制点表、准入表
cp_out = []
for c in D.CONTROL_POINTS:
    row = dict(c)
    if c['feature'] and c['feature'] in F and F[c['feature']].get('geometry'):
        pts = iter_pairs(F[c['feature']]['geometry'])
        row['schematic_xy'] = pts[c['vertex']] if c['vertex'] is not None else (pts if F[c['feature']]['geometry']['type'] == 'Point' else None)
    row['survey_xy'] = None
    row['usable_as_shared_control_point'] = False
    cp_out.append(row)
wjson('tables/control-points.json', {'frame': FR['id'], 'shared_usable': n_shared, 'rows': cp_out,
                                     'missing_plates': [
                                         '《汉魏洛阳城初步勘查》考古1973(4)：城垣实测平面（城角、城门缺口坐标）',
                                         '《汉魏洛阳故城城垣试掘》考古学报1998(3)：各段城垣分期与位置',
                                         '《汉魏洛阳城北魏建春门遗址的发掘》考古1988(9)：门址平面',
                                         '钱国祥《由阊阖门谈汉魏洛阳城宫城形制》考古2003(7)：宫城实测平面（后期，仅作范围对照）',
                                         '2011宫城西南角发掘资料：宫城西墙与汉晋河渠平面',
                                         '2022千秋门解剖资料：不晚于汉代砖券水道平面、底高程',
                                         '2023宫城东墙/东南角/仓窖区西北角发掘资料：东汉北宫东/南墙段与冲沟道路平面',
                                         '河南省文物考古研究院 News_ID=2283 / 2810 原页（未能访问）',
                                     ]})
num = {
    'north_B_ew_over_later': pal['ratios_B_over_later']['ew'],
    'east_residual_vs_schematic_lower_bound_pct': round((east_lb - 1) * 100, 1),
    'granary_margins_m': {r['zone']: r['margin_m'] for r in ne['distances_m'] if r['zone']},
    'ne_screen_area_m2': area,
}
adm = [dict(a, numbers=num) if a['zone'].startswith('东北') else dict(a) for a in D.ADMISSION]
wjson('tables/admission.json', {'frame': FR['id'], 'rows': adm,
                                'five_things': '本表只回答“能否在项目坐标中落位”。模型能读取、局部通行通过、已入城、真实结构安全、历史复原成立是另外五件事，本表一件也不证明。'})

# ---------------------------------------------------------------- 12 预览图
S = 0.22  # px per m
pad = 60
Wd, Hd = int(2800 * S) + 2 * pad + 520, int(4100 * S) + 2 * pad
img = Image.new('RGB', (Wd, Hd), (248, 245, 236))
dr = ImageDraw.Draw(img, 'RGBA')
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 13)
fontb = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 17)
X0, Y0 = pad + 60 * S, pad + 4000 * S


def T(p):
    return (X0 + p[0] * S, Y0 - p[1] * S)


# 悬置区栅格：先画进单通道遮罩，再一次性合成，避免半透明方块叠缝
grid = 10.0
masks = {k: Image.new('L', img.size, 0) for k in ('palace', 'road', 'screen')}
md = {k: ImageDraw.Draw(v) for k, v in masks.items()}


def mrect(k, x0, y0, x1, y1):
    a, b = T((x0, y1)), T((x1, y0))
    md[k].rectangle([int(a[0]), int(a[1]), int(b[0]) + 1, int(b[1]) + 1], fill=255)


for y in np.arange(-100, 4000, grid):
    for x in np.arange(-100, 2700, grid):
        p = (x + grid / 2, y + grid / 2)
        z = [h for h in HOLD if dist_to_geom(p, F[h['base']]['geometry']) <= h['buffer_m']]
        if z:
            mrect('palace' if any(h['id'] in ('HZ-N', 'HZ-S', 'HZ-C', 'HZ-Y') for h in z) else 'road', x, y, x + grid, y + grid)
for c in cells:
    mrect('screen', c[0] - step / 2, c[1] - step / 2, c[0] + step / 2, c[1] + step / 2)
for k, col, al in (('screen', (60, 130, 90), 90), ('road', (200, 150, 40), 90), ('palace', (196, 80, 60), 80)):
    img.paste(Image.new('RGB', img.size, col), mask=masks[k].point(lambda v, al=al: al if v else 0))
dr = ImageDraw.Draw(img, 'RGBA')
dr.line([T(p) for p in V + [V[0]]], fill=(40, 90, 60), width=3)
for fid, col in [('north_palace_extent_gao2023_B', (150, 40, 30)), ('south_palace_candidate_gao2023_B', (150, 40, 30))]:
    ring = iter_pairs(F[fid]['geometry'])
    for i in range(len(ring) - 1):
        a, b = np.array(T(ring[i])), np.array(T(ring[i + 1]))
        n = int(np.linalg.norm(b - a) // 8)
        for k in range(0, n, 2):
            dr.line([tuple(a + (b - a) * k / n), tuple(a + (b - a) * (k + 1) / n)], fill=col, width=2)
for rid in held_roads + ['palaces_connector_B']:
    dr.line([T(p) for p in iter_pairs(F[rid]['geometry'])], fill=(120, 90, 20), width=2)
for fid, lab in [('region_taicang_B', '太仓（B标签）'), ('region_wuku_B', '武库（B标签）'), ('region_yongan_B', '永安宫（B标签）')]:
    x, y = T(F[fid]['geometry']['coordinates'])
    dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(30, 60, 140))
    dr.text((x + 6, y - 8), lab, font=font, fill=(30, 60, 140))
dr.polygon([T(p) for p in H], outline=(20, 40, 120), fill=(20, 40, 120, 160))
for fid in ['gate_shangdong_B', 'gate_zhongdong_B', 'gate_gu_B', 'gate_xia_B', 'gate_pingcheng_B']:
    x, y = T(F[fid]['geometry']['coordinates'])
    dr.rectangle([x - 3, y - 3, x + 3, y + 3], outline=(40, 90, 60), width=2)
    dr.text((x + 5, y + 2), F[fid]['name'], font=font, fill=(40, 90, 60))
cx, cy = T(np.mean(NP, axis=0))
dr.text((cx - 70, cy - 10), '旧B北宫（虚线，仅对照）', font=font, fill=(150, 40, 30))
cx, cy = T(np.mean(SP, axis=0))
dr.text((cx - 70, cy - 10), '南宫候选B（位置未勘查）', font=font, fill=(150, 40, 30))
a = T((0, -80))
dr.line([a, (a[0] + 500 * S, a[1])], fill=(0, 0, 0), width=3)
dr.text((a[0], a[1] + 4), '500 示意米', font=font, fill=(0, 0, 0))
dr.text((pad, 14), 'LY-003 南北宫与东北约束：悬置区与可落位状态（项目示意坐标 luoyang-local-schematic-v01）', font=fontb, fill=(0, 0, 0))
lx = int(2800 * S) + pad + 30
lines = [
    ('图例', None),
    ('红色浅底：宫区悬置区（旧B外扩200米、复道80米、永安宫400米）', (196, 80, 60)),
    ('黄色浅底：仓库已列“悬置宫缘”的示意道路外扩80米', (200, 150, 40)),
    ('绿色浅底：东北C试放筛查区（不是宫外证明）', (60, 130, 90)),
    ('深蓝实心：现入城仓储组实际GLB平面凸包', (20, 40, 120)),
    ('', None),
    ('不在图上（无任何坐标，不可落位）', None),
    ('· 东汉北宫新发现东墙、南墙段（2023）', None),
    ('· 宫城东墙外冲沟内不晚于东汉道路（宽约23米）', None),
    ('· 千秋门下不晚于汉代砖券水道（内宽1.2米）', None),
    ('· 宫城西南角下汉晋大型河渠', None),
    ('· 南宫任何墙段、门址', None),
    ('· C_NE_APPROACH_LOCAL（bce3211 中未找到）', None),
    ('', None),
    ('数字', None),
    (f'· 共同控制点：{n_shared} 个；相似变换需≥2（校核≥3）', None),
    (f'· 东垣残长比示意东边全长长 {(east_lb - 1) * 100:.1f}%', None),
    (f'· 旧B北宫东西宽 / 后期宫城宽 = {pal["ratios_B_over_later"]["ew"]}', None),
    (f'· 仓储凸包到 HZ-N 外缘 {num["granary_margins_m"]["HZ-N"]} 米', None),
    (f'· 东北筛查区面积 {area / 1e4:.1f} 公顷（5米栅格）', None),
    ('', None),
    ('CPU 栅格示意图，非浏览器/GPU 截图。', None),
    ('坐标无地理原点、无真北；“示意米”不是测绘米。', None),
]
yy = pad + 20
for t, col in lines:
    if col:
        dr.rectangle([lx, yy + 3, lx + 14, yy + 15], fill=col + (140,))
        dr.text((lx + 20, yy), t, font=font, fill=(0, 0, 0))
    else:
        dr.text((lx, yy), t, font=fontb if t in ('图例', '数字') or t.startswith('不在图上') else font, fill=(0, 0, 0))
    yy += 22
(OUT / 'preview').mkdir(exist_ok=True)
buf = io.BytesIO()
img.save(buf, format='PNG', optimize=True)
(OUT / 'preview/constraints-map.png').write_bytes(buf.getvalue())

# ---------------------------------------------------------------- 13 inputs.json
wjson('inputs.json', {
    'seat': 'LY-003', 'lab_commit': full_commit, 'read_mode': 'git show 提交字节，只读；未改、未建、未删仓库文件，未运行 build_assets.py',
    'repo_inputs': inputs_repo, 'prior_seat_inputs': prior,
    'copied_helper': {'path': 'source/glbinfo.py', 'from': 'LY-001/source/glbinfo.py', 'sha256': glbinfo_copy},
    'coordinate_contract': {'frame': FR['id'], 'units': 'schematic_m', 'glTF': '[east, height, -north]', 'geographicOrigin': None, 'rotationToTrueNorth': None},
    'external_sources': [dict(k=k, **{kk: vv for kk, vv in s.items()}, **({'sha256': SRC_SHA[k]['sha256'], 'bytes': SRC_SHA[k]['bytes']} if k in SRC_SHA else {'sha256': None}),
                              **({'pdf_sha256': SRC_SHA[k]['pdf_sha256']} if k in SRC_SHA and 'pdf_sha256' in SRC_SHA[k] else {})) for k, s in D.SOURCES.items()],
    'external_unreachable': D.UNREACHABLE,
    'external_distribution': '外部网页与PDF均有版权，不随包分发；只记SHA256，重算需按URL重新下载到 --external 目录（网页可能已变，SHA不符即记未复核）。',
    'native_sources': '本席位不涉及 .blend/源ZIP；不需要原生件。'})

if FAIL:
    log(f'\n{len(FAIL)} 项失败')
else:
    log('\n全部检查通过（这只说明数据可重算、引文可核、负例有效；结论仍是宫区不可落位）')
(OUT / 'qa/build-run.txt').write_text('\n'.join(LOG) + '\n', encoding='utf-8', newline='\n')
sys.exit(1 if FAIL else 0)
