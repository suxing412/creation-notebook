# -*- coding: utf-8 -*-
"""生成 baseline/LY_P01-material-semantics.json：LY_P01 五种材料的冻结语义表。
数值不手抄：FLAT 因子与粗糙度从 commit 中她的 GLB 读出（lingtai-A-LOD2：earth/timber/tile/path；
foot-pestle-LOD2：paper__stone），PBR 结构从 kaiyang-K-LOD0 / foot-pestle-LOD0 / lingtai-A-LOD1 读出，
贴图 SHA 取 textures/manifest.json（已由 verify_textures.py 与她 GLB 嵌入字节逐字节核对）。
用法: python -I make_semantics.py <LY-007 目录> <lab 仓库> <commit>
"""
import sys, os, json, struct, subprocess, hashlib

W, LAB, COMMIT = sys.argv[1], sys.argv[2], sys.argv[3]
M = 'docs/library/models/'
SRC = dict(flat4=M + 'm-luoyang-lingtai/files/lingtai-A-LOD2.glb', flat_stone=M + 'm-luoyang-foot-pestle/files/foot-pestle-LOD2.glb',
           pbr=M + 'm-luoyang-kaiyang-gate/files/kaiyang-K-LOD0.glb', pbr_stone=M + 'm-luoyang-foot-pestle/files/foot-pestle-LOD0.glb',
           pbr_path=M + 'm-luoyang-lingtai/files/lingtai-A-LOD1.glb')


def glb(path):
    b = subprocess.run(['git', '-C', LAB, 'show', f'{COMMIT}:{path}'], capture_output=True, check=True).stdout
    jl = struct.unpack('<I', b[12:16])[0]
    return json.loads(b[20:20 + jl]), hashlib.sha256(b).hexdigest()


def lin2srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def srgb2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
J = {k: glb(p) for k, p in SRC.items()}
flat = {}
for key in ('flat4', 'flat_stone'):
    for m in J[key][0]['materials']:
        nm = m['name']
        base = nm[len('LY_P01_'):-len('__FLAT')] if nm.endswith('__FLAT') else None
        # lingtai 给 earth/timber/tile/path；foot-pestle 只取 paper__stone（它的 timber__FLAT 粗糙度 0.90 是器物族特例，见 decisions D-FLAT-ROUGH）
        if base and (key == 'flat4' or base == 'paper__stone'):
            flat[base] = dict(m['pbrMetallicRoughness'], _src=SRC[key], _sha=J[key][1])
man = json.load(open(os.path.join(W, 'textures', 'manifest.json'), encoding='utf-8'))
tex = {(m['image_name'], m['size'][0]): m for m in man if 'legacy' not in m['file']}

ROLE = {
    'earth': ('夯土', '夯土墙、台基、墩台、柱础（并入 earth 网格）、踏步、室内地坪、院墙墙身、地面补丁',
              '城门、礼制、市肆、住屋四族逐三角核过；宫院、生产两族只有分析员部分输出'),
    'timber': ('木', '柱、梁枋、檩、门框、门叶、窗框窗棂、栌斗、柜台、扶手', '同上；贴图前缀叫 wood'),
    'tile': ('瓦', '屋面板、瓦垄、正脊/戗脊、院墙压顶', '同上'),
    'path': ('路面', '路面、台面铺装（灵台 static_path）；PBR 借用 earth 三张贴图，FLAT 更浅', '只在灵台一张卡见到（LOD1/LOD2，无 LOD0）'),
    'paper__stone': ('纸样石', '石臼、石础等石质器物的占位色（研究性浅色样件，不声称石种与加工）；PBR 不挂底色图，只写 baseColorFactor，挂 stone-orm、stone-normal',
                     '见于 foot-pestle（器物）、workyard、TC03 院落'),
}
STEM = {'earth': 'earth', 'timber': 'wood', 'tile': 'tile', 'path': 'earth', 'paper__stone': 'stone'}
out = []
for mat in ('earth', 'timber', 'tile', 'path', 'paper__stone'):
    f = flat[mat]
    lin = f['baseColorFactor'][:3]
    srgb = [lin2srgb(c) * 255 for c in lin]
    srgb_int = [round(c) for c in srgb]
    back = [f32(srgb2lin(c / 255)) for c in srgb_int]
    stem = STEM[mat]
    has_base = mat != 'paper__stone'
    texrec = {}
    for kind, slot in (('basecolor', 'baseColor'), ('orm', 'orm'), ('normal', 'normal')):
        if kind == 'basecolor' and not has_base:
            continue
        texrec[slot] = {str(res): dict(image_name=f'{stem}-{kind}', file=tex[(f'{stem}-{kind}', res)]['file'],
                                       sha256=tex[(f'{stem}-{kind}', res)]['sha256'], bytes=tex[(f'{stem}-{kind}', res)]['bytes'],
                                       mean_srgb_8bit=tex[(f'{stem}-{kind}', res)]['mean_srgb'],
                                       std=tex[(f'{stem}-{kind}', res)]['std'])
                        for res in (512, 256)}
    orm_g = tex[(f'{stem}-orm', 512)]['mean_srgb'][1]
    out.append(dict(
        material=mat, cn=ROLE[mat][0], use=ROLE[mat][1], validated_on=ROLE[mat][2],
        names={'LOD0': f'LY_P01_{mat}__PBR', 'LOD1': f'LY_P01_{mat}__PBR', 'LOD2': f'LY_P01_{mat}__FLAT'},
        flat=dict(baseColorFactor_linear=lin, roughness=f['roughnessFactor'], metallic=f.get('metallicFactor'),
                  srgb_8bit_from_linear=[round(c, 3) for c in srgb], srgb_8bit_int=srgb_int,
                  hex='#' + ''.join(f'{c:02X}' for c in srgb_int),
                  roundtrip_int_srgb_to_linear_float32_bit_exact=back == lin,
                  source=dict(glb=f['_src'], glb_sha256=f['_sha'], commit=COMMIT)),
        pbr=dict(baseColor='texture' if has_base else 'factor (= flat.baseColorFactor_linear)',
                 metallicFactor='不写（默认 1；ORM.B = 0 压成非金属）', roughnessFactor='不写（默认 1；ORM.G 给粗糙度）',
                 orm_G_mean_8bit=orm_g, effective_roughness=round(orm_g / 255, 3),
                 textures={k: stem + '-' + {'baseColor': 'basecolor', 'orm': 'orm', 'normal': 'normal'}[k] for k in texrec} |
                 ({'baseColor': None} if not has_base else {}),
                 files=texrec),
    ))
pbr_json = {k: [m for m in J[k][0]['materials']] for k in ('pbr', 'pbr_stone', 'pbr_path')}
res = dict(
    baseline='LY_P01', frozen_by='LY-007', commit=COMMIT,
    scope_note='规范只在城门、礼制、市肆、住屋四族上验证过（S84、G10 三档顶点级复刻；G10/H64/H72/H96/S84/workshed/kaiyang/gate-A 逐三角 UV 核对）；'
               '宫院（宫殿、廊、阙、武库等）与生产（窑、磨、碓、灶等器物）两族的事实来自分析员的部分输出，未逐三角复核。',
    color_space=dict(
        baseColor_texture='sRGB（8-bit RGB PNG，无 alpha；Blender 导入/建材时 colorspace = sRGB）',
        orm_texture='线性数据（Non-Color）。R = 255 恒定（不当 occlusion 用，材质不引用 occlusionTexture）；G = 粗糙度；B = 0 金属度',
        normal_texture='线性数据（Non-Color），glTF 切线空间法线；均值 (127,127,254)，起伏极弱；Y 向约定（OpenGL/DirectX）未量到，因起伏 std ≤ 10/255 肉眼不可辨',
        flat_factor='glTF baseColorFactor 为线性值。她的 FLAT = 8-bit sRGB 整数色经 sRGB→线性换算后存 float32，逐位可重算（见 roundtrip 字段）',
        workbench_note='CPU Workbench 预览（mq/render.py）用 TEXTURE/MATERIAL 色，Standard 视图变换；预览图只是 CPU 图，不是浏览器/GPU 结果'),
    gltf_material_structure=dict(
        pbr_example_from_her_glb=pbr_json['pbr'][:1], pbr_stone_example=pbr_json['pbr_stone'][:1], pbr_path_example=pbr_json['pbr_path'][3:4],
        sampler={'magFilter': 9729, 'minFilter': 9987, 'wrap': '不写（REPEAT）'}, doubleSided=True,
        forbidden=['metallicFactor/roughnessFactor on __PBR', 'occlusionTexture', 'emissive*', 'alphaMode', 'KHR_materials_*', 'KHR_texture_transform',
                   '副本后缀 .001', '无后缀名（LY_P01_earth）', 'REUSED_*', '__VC 顶点色（城垣续做除外）', '旧灰贴图 legacy_grey']),
    materials=out,
    new_material_rule='新材料（真石材、砖、灰泥、金属、草席、货物代理等）先由制作人定调色板与贴图，本基线不起新名。现状中已出现的非五种角色见 decisions.json D-MAT-NEW。',
    sources={k: dict(path=p, sha256=J[k][1]) for k, p in SRC.items()},
)
os.makedirs(os.path.join(W, 'baseline'), exist_ok=True)
json.dump(res, open(os.path.join(W, 'baseline', 'LY_P01-material-semantics.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for m in out:
    print(m['material'], m['flat']['hex'], m['flat']['roundtrip_int_srgb_to_linear_float32_bit_exact'], m['flat']['roughness'], m['pbr']['effective_roughness'])
