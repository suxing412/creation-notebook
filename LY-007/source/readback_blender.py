# -*- coding: utf-8 -*-
"""LY-007 读回核验（Blender 内跑）：基准球与样件 GLB 是否能被官方导入器重新读取，材质语义、颜色空间、UV 尺度、贴图来源。

用法: D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P readback_blender.py -- <LY-007 目录> <glb>...
输出: qa/readback.json（逐文件）。任何一项不符记入 issues；不只报 PASS，逐项写实测值。
"""
import sys, os, json, struct, hashlib, math
argv = sys.argv[sys.argv.index('--') + 1:]
W = os.path.abspath(argv[0]); FILES = argv[1:]
sys.path.insert(0, os.path.join(W, 'source', 'lib'))
import bpy  # noqa: E402
import ly_style as ly  # noqa: E402
ly.TEX_DIR = os.path.join(W, 'textures')
SEM = json.load(open(os.path.join(W, 'baseline', 'LY_P01-material-semantics.json'), encoding='utf-8'))
MATS = {m['material']: m for m in SEM['materials']}
f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]


def read(path):
    b = open(path, 'rb').read(); jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl]); o = 20 + jl; bl = struct.unpack('<I', b[o:o + 4])[0]
    return b, j, b[o + 8:o + 8 + bl]


def tier_of(path):
    n = os.path.basename(path)
    for k in (0, 1, 2):
        if f'LOD{k}' in n:
            return k
    return None


def json_material_check(j, bn, lod):
    out, issues = [], []
    man = {m['sha256']: m for m in json.load(open(os.path.join(W, 'textures', 'manifest.json'), encoding='utf-8'))}
    for m in j.get('materials', []):
        nm = m.get('name', '')
        base = nm.rsplit('__', 1)[0].replace('LY_P01_', '')
        sem = MATS.get(base)
        rec = dict(name=nm, material=base, known=bool(sem))
        pb = m.get('pbrMetallicRoughness', {})
        if sem is None:
            issues.append(f'{nm}: 不在 LY_P01 语义表'); out.append(rec); continue
        if lod is not None and lod >= 2:
            want = [f32(x) for x in sem['flat']['baseColorFactor_linear']]
            got = pb.get('baseColorFactor', [None] * 4)[:3]
            rec.update(baseColorFactor=got, factor_bit_exact=got == want,
                       metallic=pb.get('metallicFactor'), roughness=pb.get('roughnessFactor'))
            if got != want:
                issues.append(f'{nm}: baseColorFactor {got} ≠ 语义表 {want}')
            if pb.get('metallicFactor') != 0:
                issues.append(f'{nm}: metallicFactor {pb.get("metallicFactor")}')
            if abs((pb.get('roughnessFactor') or 0) - sem['flat']['roughness']) > 1e-6:
                issues.append(f'{nm}: roughness {pb.get("roughnessFactor")} ≠ {sem["flat"]["roughness"]}')
            if any(k in pb for k in ('baseColorTexture', 'metallicRoughnessTexture')) or 'normalTexture' in m:
                issues.append(f'{nm}: FLAT 不应带贴图')
        else:
            slots = {}
            for slot, ref in (('baseColor', pb.get('baseColorTexture')), ('metallicRoughness(ORM)', pb.get('metallicRoughnessTexture')),
                              ('normal', m.get('normalTexture'))):
                if ref is None:
                    slots[slot] = None; continue
                tex = j['textures'][ref['index']]; im = j['images'][tex['source']]
                bv = j['bufferViews'][im['bufferView']]
                data = bn[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
                h = hashlib.sha256(data).hexdigest()
                w = struct.unpack('>I', data[16:20])[0]
                slots[slot] = dict(image=im.get('name'), sha256=h, px=w, in_library=h in man,
                                   library_file=man.get(h, {}).get('file'), texCoord=ref.get('texCoord', 0),
                                   scale=ref.get('scale'), sampler=j.get('samplers', [{}])[tex.get('sampler', 0)] if 'sampler' in tex else None)
            rec['slots'] = slots
            exp = sem['pbr']['textures']
            for slot, stem in (('baseColor', exp.get('baseColor')), ('metallicRoughness(ORM)', exp.get('orm')), ('normal', exp.get('normal'))):
                got = slots.get(slot)
                if stem is None:
                    if got is not None:
                        issues.append(f'{nm}: {slot} 不应挂图')
                    continue
                if got is None:
                    issues.append(f'{nm}: 缺 {slot}'); continue
                if got['image'] != stem:
                    issues.append(f'{nm}: {slot} 图名 {got["image"]} ≠ {stem}')
                if not got['in_library']:
                    issues.append(f'{nm}: {slot} 字节不在共享贴图库')
                if lod is not None and got['px'] != {0: 512, 1: 256}[lod]:
                    issues.append(f'{nm}: {slot} {got["px"]}px 与 LOD{lod} 不符')
                if got.get('scale') not in (None, 1, 1.0):
                    issues.append(f'{nm}: normal scale {got.get("scale")}')
            if 'metallicFactor' in pb or 'roughnessFactor' in pb:
                issues.append(f'{nm}: PBR 写了因子')
            if 'baseColorFactor' in pb and exp.get('baseColor'):
                issues.append(f'{nm}: 挂图又写 baseColorFactor')
            if exp.get('baseColor') is None:
                want = [f32(x) for x in sem['flat']['baseColorFactor_linear']]
                if pb.get('baseColorFactor', [None])[:3] != want:
                    issues.append(f'{nm}: 无底色图材料的 baseColorFactor {pb.get("baseColorFactor")} ≠ {want}')
            if 'occlusionTexture' in m:
                issues.append(f'{nm}: 带 occlusionTexture')
        rec['doubleSided'] = m.get('doubleSided')
        if not m.get('doubleSided'):
            issues.append(f'{nm}: 非 doubleSided')
        if m.get('extensions') or m.get('alphaMode') or m.get('emissiveFactor'):
            issues.append(f'{nm}: 带扩展/alpha/emissive')
        out.append(rec)
    return out, issues


def uv_cube_check(j, bn):
    """标定块：在每个 static 网格里找 1 m 方盒的 12 个三角（包围盒 1x1x1，按连通块），核对每个面 UV 跨度。"""
    import numpy as np
    res = {}
    for nd in j['nodes']:
        if 'mesh' not in nd:
            continue
        pr = j['meshes'][nd['mesh']]['primitives'][0]
        P = ly._acc(j, bn, pr['attributes']['POSITION']); U = ly._acc(j, bn, pr['attributes']['TEXCOORD_0'])
        I = ly._acc(j, bn, pr['indices']).reshape(-1, 3).astype(int)
        # 标定块位于 glTF z ∈ [-1.9, -0.9]
        sel = [t for t in I if (P[t][:, 2] <= -0.9 + 1e-6).all() and (P[t][:, 2] >= -1.9 - 1e-6).all()]
        if not sel:
            continue
        spans = []
        for t in sel:
            du = U[t][:, 0].max() - U[t][:, 0].min(); dv = U[t][:, 1].max() - U[t][:, 1].min()
            dp = P[t].max(0) - P[t].min(0)
            spans.append((round(float(du), 6), round(float(dv), 6), [round(float(x), 6) for x in dp]))
        uvs = sorted({(a, b) for a, b, _ in spans})
        res[nd['name']] = dict(triangles=len(sel), uv_spans=uvs, metres_per_uv=1.0 if all(abs(a - 1) < 1e-6 and abs(b - 1) < 1e-6 for a, b in uvs) else None)
    return res


def reimport(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    out = {'objects': [], 'images': [], 'materials': []}
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            out['objects'].append(dict(name=o.name, mesh=o.data.name, polys=len(o.data.polygons), uv_layers=[u.name for u in o.data.uv_layers],
                                       loc=[round(x, 6) for x in o.location], mats=[m.name for m in o.data.materials if m]))
    for im in bpy.data.images:
        if im.name in ('Render Result', 'Viewer Node'):
            continue
        out['images'].append(dict(name=im.name, colorspace=im.colorspace_settings.name, size=list(im.size), packed=bool(im.packed_file)))
    for m in bpy.data.materials:
        links = []
        if m.use_nodes:
            for l in m.node_tree.links:
                fn = l.from_node; tn = l.to_node
                src = fn.image.name if fn.type == 'TEX_IMAGE' and fn.image else fn.type
                links.append(f'{src}.{l.from_socket.name}->{tn.type}.{l.to_socket.name}')
        out['materials'].append(dict(name=m.name, links=sorted(links), backface_culling=m.use_backface_culling))
    return out


report = {}
for f in FILES:
    path = os.path.abspath(f)
    b, j, bn = read(path)
    lod = tier_of(path)
    rec = dict(file=os.path.relpath(path, W).replace('\\', '/'), sha256=hashlib.sha256(b).hexdigest(), bytes=len(b), lod=lod)
    insp = ly.inspect_glb(path, expect_lod=lod)
    rec['inspect_glb'] = {k: v for k, v in insp.items() if k != 'extras'}
    rec['node_extras'] = insp.get('extras')
    mats, mi = json_material_check(j, bn, lod)
    rec['materials'] = mats
    rec['uv_calibration'] = uv_cube_check(j, bn) if 'lyref' in path else None
    ri = reimport(path)
    rec['reimport'] = ri
    cs_issues = []
    for im in ri['images']:
        want = 'sRGB' if 'basecolor' in im['name'] else 'Non-Color'
        if im['colorspace'] != want:
            cs_issues.append(f'导入后 {im["name"]} 颜色空间 {im["colorspace"]} ≠ {want}')
    rec['issues'] = list(insp['issues']) + mi + cs_issues
    if rec['uv_calibration'] is not None:
        for k, v in rec['uv_calibration'].items():
            if v['metres_per_uv'] != 1.0:
                rec['issues'].append(f'{k}: 标定块 UV 跨度 {v["uv_spans"]} 不是 1.0')
    report[rec['file']] = rec
    print('READBACK', rec['file'], rec['sha256'][:12], 'issues', rec['issues'])

out = os.path.join(W, 'qa', 'readback.json')
json.dump(report, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('READBACK DONE', len(report), 'files;', sum(1 for r in report.values() if r['issues']), 'with issues')
