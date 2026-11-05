# -*- coding: utf-8 -*-
"""ly_style 检查工具的反例测试 + 「从 LOD0 物体派生 LOD」测试。
用法: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P test_checks.py -- <outdir>
每项都应「测出问题」；最后打印 PASS/FAIL 汇总，有 FAIL 时以退出码 1 结束。"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import ly_style as ly  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(HERE, 'demo', 'test')
os.makedirs(OUT, exist_ok=True)
results = []


def expect(name, cond, detail):
    results.append((name, bool(cond), detail))
    print(('PASS ' if cond else 'FAIL ') + name, detail)


# 1) 悬空：离地 0.3 的方盒
a = ly.Assembly('t-float', 'A', profile='house')
a.box((0, 0, 0), (2, 2, 0.2), 'earth', name='base', tags=('platform',))
a.box((0.5, 0.5, 0.5), (1.0, 1.0, 0.8), 'timber', name='floater', tags=('beam',))
a.box((1.2, 1.2, 0.2), (1.5, 1.5, 0.6), 'timber', name='sitter', tags=('post',))
fl, allr = ly.check_floating(a)
expect('floating detects floater', [r['name'] for r in fl] == ['floater'], [(r['name'], r['min_gap']) for r in fl])

# 2) 穿插：墙穿过柱
b = ly.Assembly('t-cross', 'A', profile='house')
b.wall('X', -2, 2, 0.0, 0.28, 0.0, 2.5, name='wall')
b.column(0.0, 0.14, 0.0, 3.0, d=0.32, base=False, name='col')
bad, allp = ly.check_intersections(b)
expect('intersection detects wall x column', any({r['a'], r['b']} == {'wall', 'col'} for r in bad), [(r['a'], r['b'], r['overlap_box']) for r in bad])

# 3) 共面同向重叠：两块板顶面在同一平面且部分重合
c = ly.Assembly('t-coplanar', 'A', profile='house')
c.box((0, 0, 0), (2, 2, 0.2), 'earth', name='slabA')
c.box((1, 1, 0.1), (3, 3, 0.2), 'earth', name='slabB')
cop = ly.check_coplanar(c)
expect('coplanar detects shared top face', any({h['a'], h['b']} == {'slabA', 'slabB'} for h in cop), cop[:3])

# 4) 入口净空：关着的门扇挡住通道；门洞净宽不足
d = ly.Assembly('t-door', 'A', profile='house')
d.floor_slab(-2, 0, 2, 3, h=0.22)
d.wall('X', -2, 2, 0.0, 0.28, 0.22, 2.8, openings=[(-0.4, 0.4, 0.22, 2.0)], name='wall')
d.door_frame('X', -0.4, 0.4, 0.0, 0.28, 0.22, 2.0, jamb=0.08, head=0.08)
d.door_leaf((-0.32, 0.28, 0.23), 0.64, 1.7, t=0.06, angle_deg=0, name='leaf_closed')
cl = ly.check_clearance(d, (0, 0.14, 0.22), (0, 1, 0), min_width=0.8, min_height=1.9)
expect('clearance fails (narrow, low, blocked)', (not cl['pass']) and cl['blocked'] > 0 and cl['clear_width'] < 0.8 and cl['clear_height'] < 1.9,
       {k: cl[k] for k in ('clear_width', 'clear_height', 'blocked', 'blockers')})

# 5) 落地：整体抬高 0.1
e = ly.Assembly('t-ground', 'A', profile='house')
e.box((0, 0, 0.1), (1, 1, 0.5), 'earth', name='lifted')
g = ly.check_grounded(e)
expect('grounded detects lift', not g['grounded'], g)

# 6) 导出自检：非规范材质名、带变换的静态节点、未落地
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0))
cube = bpy.context.active_object
cube.name = 'bad-A-static_earth'
m = bpy.data.materials.new('Material'); cube.data.materials.append(m)
p = os.path.join(OUT, 'bad-A-LOD0.glb')
ly.export_glb([cube], p)
rep = ly.inspect_glb(p, expect_lod=0)
expect('inspect_glb flags bad material / TRS / ground', len(rep['issues']) >= 3, rep['issues'])
bpy.data.objects.remove(cube, do_unlink=True)

# 7) 从 LOD0 物体派生：用小屋的 LOD0 预览物体 + 一个手工物体还原 Assembly，三档三角数应与直接导出一致（+ 手工件）
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location('demo_build_mod', os.path.join(HERE, 'demo_build.py'))
src = open(os.path.join(HERE, 'demo_build.py'), encoding='utf-8').read()
ns = {'__name__': 'demo_lib', '__file__': os.path.join(HERE, 'demo_build.py')}
code = src.split('for builder in (build_hut, build_pavilion):')[0]   # 只取建模函数定义
exec(compile(code, 'demo_build.py', 'exec'), ns)
hut, roof, door = ns['build_hut']()
direct = {lod: sum((ly.component_geometry(cc, lod, hut.profile) or ly.Geo()).tri_count() for cc in hut.components) for lod in (0, 1, 2)}
objs = list(hut.collection.objects)
man = ly._make_object('manual_bench', ly.geo_box((-1.0, 1.5, 0.22), (0.2, 1.9, 0.62)), ly.material_for('timber', 0), hut.collection)
derived = ly.assembly_from_objects(objs + [man], 'demohut-derived', 'A', evidence='C derived test', profile='house')
res = ly.export_lods(derived, OUT, verbose=False)
got = {lod: res[lod]['triangles'] for lod in res}
want = {lod: direct[lod] + 12 for lod in direct}
expect('derive LOD1/LOD2 from LOD0 objects', got == want and all(not res[l]['issues'] for l in res), {'got': got, 'want': want,
       'issues': {l: res[l]['issues'] for l in res}})

# 8) 类型门檐口逐片瓦：每片 28 顶点 / 52 三角，LOD2 删除，不悬空
f = ly.Assembly('t-eave', 'A', profile='gate')
rf = f.roof_gable(-2.0, 2.0, -2.0, 2.0, z_eave=3.0, rise=0.8, t=0.08)
ntile = f.eave_tiles(rf)
tiles = [cc for cc in f.components if 'eave_tile' in cc['tags']]
sig = {(len(cc['params']['verts']), ly.Geo(cc['params']['verts'], cc['params']['faces']).tri_count()) for cc in tiles}
fl8, _ = ly.check_floating(f)
fl8 = [r for r in fl8 if 'eave_tile' in r['tags']]          # 测试里屋面板本身没有墙柱支承，只看瓦片
lod2 = sum(1 for cc in tiles if ly.component_geometry(cc, 2, f.profile) is not None)
expect('eave tiles 28v/52t, removed at LOD2, supported', sig == {(28, 52)} and lod2 == 0 and not fl8,
       {'n': ntile, 'sig': sorted(sig), 'lod2_left': lod2, 'floating': [r['name'] for r in fl8][:5]})

# 9) 单独节点门扇（jin 做法）：节点 <slug>-<V>-leaf_0_L 带铰点 TRS 与 extras，三档都在，UV 仍为世界盒式
h = ly.Assembly('t-leafnode', 'A', profile='gate')
h.floor_slab(-2, 0, 2, 2, h=0.2)
h.wall('X', -2, 2, 0.0, 0.3, 0.2, 3.0, openings=[(-0.8, 0.8, 0.2, 2.6)], name='wall')
h.door_frame('X', -0.8, 0.8, 0.0, 0.3, 0.2, 2.6, jamb=0.1, head=0.1)
h.door_leaf((-0.7, 0.3, 0.21), 1.4, 2.3, t=0.1, angle_deg=30, bands=(0.16, 0.51, 0.86), separate_node='leaf_0_L', name='leaf')
res9 = ly.export_lods(h, OUT, verbose=False)
import struct as _st  # noqa: E402
def _nodes(p):
    b = open(p, 'rb').read(); jl = _st.unpack('<I', b[12:16])[0]; return json.loads(b[20:20 + jl])['nodes']
nd = {lod: {n['name']: n for n in _nodes(os.path.join(OUT, f't-leafnode-A-LOD{lod}.glb'))} for lod in (0, 1, 2)}
leaf_ok = all('t-leafnode-A-leaf_0_L' in nd[l] and 'translation' in nd[l]['t-leafnode-A-leaf_0_L'] and
              nd[l]['t-leafnode-A-leaf_0_L'].get('extras', {}).get('angle_range_deg') == [0, 90] for l in nd)
expect('separate hinged leaf node exported in all LODs', leaf_ok and all(not res9[l]['issues'] for l in res9),
       {'nodes0': list(nd[0]), 'leaf0': {k: v for k, v in nd[0].get('t-leafnode-A-leaf_0_L', {}).items() if k != 'mesh'},
        'tris': {l: res9[l]['triangles'] for l in res9}, 'issues': {l: res9[l]['issues'] for l in res9}})

ok = all(r[1] for r in results)
json.dump([{'test': n, 'pass': p, 'detail': str(dd)} for n, p, dd in results], open(os.path.join(OUT, 'test_report.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('TESTS', 'ALL PASS' if ok else 'SOME FAILED', f'{sum(r[1] for r in results)}/{len(results)}')
if not ok:
    sys.exit(1)
