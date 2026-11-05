#!/usr/bin/env python3
"""从 LY-007 的好样件确定性地生成负例（错误注入），并写 qa/negatives/cases.json（每个用例：注入方法、期望错误代码、SHA256）。

用法：python -I source/make_negatives.py <LY-008 目录> <LY-007 目录>
小文件写 qa/negatives/；超过 1 MB 的体积用例写 tmp/neg-big/（不进交付白名单，可按本脚本逐字节重出，SHA 记在 cases.json）。
不读写任何仓库文件。
"""
import copy, hashlib, json, os, shutil, struct, sys, zlib

ROOT = os.path.abspath(sys.argv[1])
LY7 = os.path.abspath(sys.argv[2])
NEG = os.path.join(ROOT, 'qa', 'negatives')
BIG = os.path.join(ROOT, 'tmp', 'neg-big')
GOOD0 = os.path.join(LY7, 'models', 'samples', 'S84-LOD0.glb')
GOOD1 = os.path.join(LY7, 'models', 'samples', 'S84-LOD1.glb')
GOOD2 = os.path.join(LY7, 'models', 'samples', 'S84-LOD2.glb')
# 负例里用的「私密路径」是虚构的占位用户名，不是本机真实用户名；真实用户名判据由检查器在运行时从环境变量取，
# 另有一个用例（N13c）在运行时把检查器的 --private-token 设成这个占位名，证明用户名判据生效。
FAKE_USER = 'lyneguser'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_glb(p):
    raw = open(p, 'rb').read()
    jl = struct.unpack_from('<I', raw, 12)[0]
    js = json.loads(raw[20:20 + jl].decode('utf-8'))
    bl = struct.unpack_from('<I', raw, 20 + jl)[0]
    return js, bytearray(raw[28 + jl: 28 + jl + bl])


def pack(js, binb, allow_nan=False):
    jb = json.dumps(js, separators=(',', ':'), ensure_ascii=False, allow_nan=allow_nan).encode('utf-8')
    jb += b' ' * (-len(jb) % 4)
    bb = bytes(binb) + b'\x00' * (-len(binb) % 4)
    total = 12 + 8 + len(jb) + 8 + len(bb)
    return struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<II', len(jb), 0x4E4F534A) + jb + struct.pack('<II', len(bb), 0x004E4942) + bb


def append_view(js, binb, data):
    while len(binb) % 4:
        binb.append(0)
    off = len(binb)
    binb.extend(data)
    js['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data)})
    js['buffers'][0]['byteLength'] = len(binb)
    return len(js['bufferViews']) - 1


def acc_off(js, ai):
    a = js['accessors'][ai]
    bv = js['bufferViews'][a['bufferView']]
    return bv.get('byteOffset', 0) + a.get('byteOffset', 0)


cases = []


def emit(cid, data, what, expect_codes, cmd='glb', args=None, big=False, note=None):
    d = BIG if big else NEG
    os.makedirs(d, exist_ok=True)
    name = f'{cid}.glb'
    p = os.path.join(d, name)
    open(p, 'wb').write(data)
    cases.append({'id': cid, 'file': os.path.relpath(p, ROOT).replace('\\', '/'), 'bytes': len(data), 'sha256': sha(data),
                  'inject': what, 'cmd': cmd, 'args': args or [], 'expectFail': bool(expect_codes), 'expectCodes': expect_codes,
                  'inDeliveryWhitelist': not big, **({'note': note} if note else {})})


def main():
    os.makedirs(NEG, exist_ok=True)
    good = open(GOOD0, 'rb').read()
    J, B = read_glb(GOOD0)
    pos_ai = J['meshes'][0]['primitives'][0]['attributes']['POSITION']
    uv_ai = J['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']
    idx_ai = J['meshes'][0]['primitives'][0]['indices']

    # ---- 对照：只经本脚本重新打包、不注入任何错误（证明 pack() 本身不制造问题） ----
    j, bb = read_glb(GOOD0)
    emit('C00-repacked-unchanged', pack(j, bb), '读出再打包，不改内容（JSON 紧凑化）', [], note='期望通过；对照组')
    cases[-1]['args'] = ['--profile', 'ly-p01', '--lod', '0', '--tex-manifest', '{LY7}/textures/manifest.json']

    # ---- 容器 ----
    b = bytearray(good); struct.pack_into('<I', b, 8, len(good) + 8)
    emit('N01-bad-header-length', bytes(b), '头部 length 字段 +8（文件字节不变）', ['GLB_LENGTH_MISMATCH'])
    emit('N02-truncated', good[:-1000], '文件截掉末尾 1000 字节（头部仍声明原长度）', ['GLB_LENGTH_MISMATCH', 'GLB_CHUNK_OVERRUN'])
    b = bytearray(good); struct.pack_into('<I', b, 12 + 8 + struct.unpack_from('<I', good, 12)[0], len(good))
    emit('N03-bad-bin-chunk-length', bytes(b), 'BIN 块长度字段改成整个文件长度（越过文件末尾）', ['GLB_CHUNK_OVERRUN'])
    emit('N22-bad-magic', b'gLTF' + good[4:], '魔数改为 gLTF', ['GLB_BAD_MAGIC'])

    # ---- NaN / Inf ----
    j, bb = read_glb(GOOD0); bb = bytearray(bb)
    struct.pack_into('<f', bb, acc_off(j, pos_ai) + 4, float('nan'))
    emit('N04-nan-position', pack(j, bb), 'POSITION 第 1 个顶点的 y 写成 NaN（min/max 不动）', ['GEOM_NONFINITE'])
    j, bb = read_glb(GOOD0); bb = bytearray(bb)
    struct.pack_into('<f', bb, acc_off(j, uv_ai), float('inf'))
    emit('N05-inf-uv', pack(j, bb), 'TEXCOORD_0 第 1 个 u 写成 +Inf', ['GEOM_NONFINITE'])
    j, bb = read_glb(GOOD0)
    j['nodes'][0]['extras'] = {'scale_hint': float('nan')}
    emit('N06-nan-json', pack(j, bb, allow_nan=True), 'JSON 里写入 NaN 字面量（nodes[0].extras）', ['GLTF_JSON_NONFINITE'])

    # ---- 缺纹理 / 坏纹理 ----
    j, bb = read_glb(GOOD0)
    j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'] = 99
    emit('N07-missing-texture-index', pack(j, bb), 'materials[0] baseColorTexture.index = 99（只有 9 个 texture）', ['TEXTURE_MISSING'])
    j, bb = read_glb(GOOD0)
    j['textures'][0]['source'] = 50
    emit('N08-missing-image-source', pack(j, bb), 'textures[0].source = 50（只有 9 张 image）', ['TEXTURE_MISSING'])
    j, bb = read_glb(GOOD0)
    im = j['images'][0]; im.pop('bufferView'); im.pop('mimeType', None); im['uri'] = 'earth-normal.png'
    emit('N09-external-texture-missing', pack(j, bb), 'images[0] 改为外部 uri earth-normal.png（同目录不存在）', ['TEXTURE_NOT_EMBEDDED', 'TEXTURE_MISSING'])
    j, bb = read_glb(GOOD0); bb = bytearray(bb)
    o = j['bufferViews'][j['images'][0]['bufferView']].get('byteOffset', 0)
    bb[o:o + 16] = b'\x00' * 16
    emit('N10-corrupt-texture-bytes', pack(j, bb), 'images[0] 前 16 字节清零（PNG 头被毁）', ['TEXTURE_MIME_MISMATCH', 'TEXTURE_CORRUPT'])
    j, bb = read_glb(GOOD0)
    del j['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']
    emit('N21-missing-uv', pack(j, bb), '带贴图材质的图元删去 TEXCOORD_0', ['UV_MISSING'])

    # ---- 越界：索引 / accessor / bufferView / min-max ----
    j, bb = read_glb(GOOD0); bb = bytearray(bb)
    struct.pack_into('<H', bb, acc_off(j, idx_ai), 65000)
    emit('N17-index-out-of-range', pack(j, bb), '第 1 个索引写成 65000（顶点数 < 200）', ['GEOM_INDEX_OUT_OF_RANGE'])
    j, bb = read_glb(GOOD0)
    j['accessors'][pos_ai]['count'] += 100000
    emit('N18-accessor-overrun', pack(j, bb), 'POSITION accessor.count += 100000', ['GLTF_ACCESSOR_OVERRUN'])
    j, bb = read_glb(GOOD0)
    j['bufferViews'][0]['byteLength'] += len(bb) * 2
    emit('N19-bufferview-overrun', pack(j, bb), 'bufferViews[0].byteLength 加上两倍 BIN 长', ['GLTF_BUFFERVIEW_OVERRUN'])
    j, bb = read_glb(GOOD0)
    j['accessors'][pos_ai]['max'] = [v + 5.0 for v in j['accessors'][pos_ai]['max']]
    emit('N20-minmax-wrong', pack(j, bb), 'POSITION.max 各分量 +5 m', ['GLTF_POSITION_MINMAX_WRONG'])

    # ---- 私密路径 ----
    j, bb = read_glb(GOOD0)
    j['nodes'][0]['extras'] = {'source_blend': f'C:/Users/{FAKE_USER}/Desktop/S84.blend'}
    emit('N13a-private-path-extras', pack(j, bb), 'nodes[0].extras 写入 C:/Users/<占位用户>/Desktop/S84.blend', ['PRIVATE_PATH_IN_JSON'])
    j, bb = read_glb(GOOD0)
    j['nodes'][1]['name'] = 'D:/GitHub/creation-notebook-lab/docs/S84'
    emit('N13b-private-path-nodename', pack(j, bb), 'nodes[1].name 写成 D:/GitHub/… 盘符路径', ['PRIVATE_PATH_IN_JSON'])
    j, bb = read_glb(GOOD0)
    j['asset']['generator'] = f'Khronos glTF Blender I/O v5.2.40 ({FAKE_USER})'
    emit('N13c-username-generator', pack(j, bb), 'asset.generator 末尾带占位用户名（检查时用 --private-token 指定该名）', ['PRIVATE_PATH_IN_JSON'],
         args=['--private-token', FAKE_USER])
    # PNG 文字块里藏路径：给 images[0] 插 tEXt 块，重排 BIN
    j, bb = read_glb(GOOD0)
    bvi = j['images'][0]['bufferView']; bv = j['bufferViews'][bvi]
    png = bytes(bb[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']])
    body = b'Source\x00' + f'C:\\Users\\{FAKE_USER}\\AppData\\Local\\Temp\\bake\\earth.png'.encode()
    chunk = struct.pack('>I', len(body)) + b'tEXt' + body + struct.pack('>I', zlib.crc32(b'tEXt' + body) & 0xffffffff)
    ihdr_end = 8 + 8 + 13 + 4
    png2 = png[:ihdr_end] + chunk + png[ihdr_end:]
    nv = append_view(j, bb, png2)
    j['images'][0]['bufferView'] = nv
    emit('N14-private-path-png-text', pack(j, bb), 'images[0] 的 PNG 插入 tEXt 块 Source=C:\\Users\\<占位用户>\\AppData\\…（像素不变）',
         ['PRIVATE_PATH_IN_TEXTURE', 'PRIVATE_PATH_IN_BIN'])

    # ---- 越界相对路径 ----
    j, bb = read_glb(GOOD0)
    im = j['images'][0]; im.pop('bufferView'); im.pop('mimeType', None); im['uri'] = '../../LY-007/textures/512/earth-normal.png'
    emit('N15-path-escape-image-uri', pack(j, bb), 'images[0].uri = ../../LY-007/textures/512/earth-normal.png（向上越出）',
         ['PATH_ESCAPE', 'TEXTURE_NOT_EMBEDDED'])
    j, bb = read_glb(GOOD0)
    j['buffers'].append({'byteLength': 16, 'uri': '../outside/extra.bin'})
    emit('N16-path-escape-buffer-uri', pack(j, bb), '追加 buffers[1].uri = ../outside/extra.bin', ['PATH_ESCAPE', 'GLTF_EXTERNAL_BUFFER'])

    # ---- 超面数：把第 0 个图元的索引重复到 > 500,000 三角（文件约 3 MB → tmp/neg-big） ----
    j, bb = read_glb(GOOD0); bb = bytearray(bb)
    a = j['accessors'][idx_ai]
    o = acc_off(j, idx_ai)
    one = bytes(bb[o:o + a['count'] * 2])
    rep = 500_001 * 3 // a['count'] + 1
    data = one * rep
    nv = append_view(j, bb, data)
    j['accessors'].append({'bufferView': nv, 'componentType': 5123, 'count': a['count'] * rep, 'type': 'SCALAR'})
    j['meshes'][0]['primitives'][0]['indices'] = len(j['accessors']) - 1
    emit('N23-over-triangle-limit', pack(j, bb), f'第 0 个图元索引重复 {rep} 次（> 500,000 三角）', ['GEOM_OVER_TRI_LIMIT'], big=True)

    # ---- 体积：正式上限与上传承载 ----
    def padded_to(total):
        j, bb = read_glb(GOOD0); bb = bytearray(bb)
        base = len(pack(j, bb))
        # 追加一个未被引用的 bufferView：pack 后总长 = base + 填充 + 4 对齐
        extra = total - base
        assert extra > 0 and extra % 4 == 0
        append_view(j, bb, b'\x00' * extra)
        out = pack(j, bb)
        # bufferViews 多一条，JSON 可能变长几字节：回头修正
        diff = len(out) - total
        if diff:
            j, bb = read_glb(GOOD0); bb = bytearray(bb)
            append_view(j, bb, b'\x00' * (extra - diff))
            out = pack(j, bb)
        assert len(out) == total, (len(out), total)
        return out
    emit('N11-oversize-15000004', padded_to(15_000_004), '追加未引用的 bufferView 填零，使文件 = 15,000,004 字节（几何不变）',
         ['GLB_OVER_FORMAL_LIMIT'], big=True)
    emit('B11-boundary-15000000', padded_to(15_000_000), '同法填到恰好 15,000,000 字节（边界：正式上限是「超过」才错）', [], big=True,
         note='期望通过（只有 GLB_LARGE 警告）')
    emit('N12-upload-channel-14000000', padded_to(14_000_000), '填到 14,000,000 字节：正式上限内；按 base64 承载 18,666,668 字节',
         ['UPLOAD_OVER_CHANNEL_LIMIT'], args=['--upload-limit', '15000000', '--upload-encoding', 'base64'], big=True,
         note='同一文件不带 --upload-limit 时期望通过（B12），证明两种上限分开判')
    cases.append({**cases[-1], 'id': 'B12-same-file-no-channel-limit', 'args': [], 'expectFail': False, 'expectCodes': [],
                  'inject': 'N12 同一文件，不给通道上限', 'note': '期望通过；upload.verdict = not-judged'})

    # ---- LY_P01 档 ----
    j, bb = read_glb(GOOD0)
    j['materials'][0]['name'] = 'LY_P01_earth__PBR.001'
    emit('L01-material-name-suffix', pack(j, bb), '材质名改为 LY_P01_earth__PBR.001', ['LY_MATERIAL_NAME'], args=['--profile', 'ly-p01', '--lod', '0'])
    cases.append({'id': 'L02-lod0-checked-as-lod1', 'file': os.path.relpath(GOOD0, ROOT).replace('\\', '/'), 'bytes': len(good), 'sha256': sha(good),
                  'inject': '好样件 S84-LOD0（512² 贴图）按 LOD1 检查', 'cmd': 'glb', 'args': ['--profile', 'ly-p01', '--lod', '1'],
                  'expectFail': True, 'expectCodes': ['LY_TEXTURE_RES'], 'inDeliveryWhitelist': False})
    g1 = open(GOOD1, 'rb').read()
    cases.append({'id': 'L03-lod1-checked-as-lod2', 'file': os.path.relpath(GOOD1, ROOT).replace('\\', '/'), 'bytes': len(g1), 'sha256': sha(g1),
                  'inject': '好样件 S84-LOD1（PBR + 256² 贴图）按 LOD2 检查', 'cmd': 'glb', 'args': ['--profile', 'ly-p01', '--lod', '2'],
                  'expectFail': True, 'expectCodes': ['LY_LOD_MATERIAL_TIER', 'LY_LOD2_HAS_TEXTURE'], 'inDeliveryWhitelist': False})
    j, bb = read_glb(GOOD0)
    j['nodes'][0]['translation'] = [0.0, 0.05, 0.0]
    emit('L04-static-node-trs', pack(j, bb), 'nodes[0]（静态件）加 translation [0,0.05,0]', ['LY_STATIC_NODE_TRS'], args=['--profile', 'ly-p01', '--lod', '0'])
    j, bb = read_glb(GOOD0); bb = bytearray(bb)
    a = j['accessors'][uv_ai]; o = acc_off(j, uv_ai)
    for k in range(a['count']):
        u = struct.unpack_from('<f', bb, o + 8 * k)[0]
        struct.pack_into('<f', bb, o + 8 * k, u + 0.37)
    emit('L05-uv-shifted', pack(j, bb), 'earth 图元 UV 的 u 整体 +0.37（不再是 1 UV = 1 m 无平移的世界盒投影）', ['LY_UV_NOT_WORLD_BOX'],
         args=['--profile', 'ly-p01', '--lod', '0'])
    cases.append({'id': 'L06-texture-not-hers', 'file': 'qa/negatives/N14-private-path-png-text.glb', 'inject': 'N14 文件（贴图字节被改）按 ly-p01 + 她的贴图清单检查',
                  'cmd': 'glb', 'args': ['--profile', 'ly-p01', '--lod', '0', '--tex-manifest', '{LY7}/textures/manifest.json'],
                  'expectFail': True, 'expectCodes': ['LY_TEXTURE_NOT_HERS'], 'inDeliveryWhitelist': False,
                  **{k: cases[[c['id'] for c in cases].index('N14-private-path-png-text')][k] for k in ('bytes', 'sha256')}})

    # ---- 三档 ----
    s84 = [os.path.relpath(p, ROOT).replace('\\', '/') for p in (GOOD0, GOOD1, GOOD2)]
    shutil.copyfile(GOOD0, os.path.join(NEG, 'S01-LOD1-is-LOD0-copy.glb'))
    cases.append({'id': 'S01-lod0-copied-as-lod1', 'cmd': 'lodset', 'files': [s84[0], 'qa/negatives/S01-LOD1-is-LOD0-copy.glb', s84[2]],
                  'args': ['--family', 'house'], 'inject': 'S84-LOD0 原字节复制改名当 LOD1', 'expectFail': True,
                  'expectCodes': ['LOD_COPY_OF_LOD0'], 'inDeliveryWhitelist': True,
                  'file': 'qa/negatives/S01-LOD1-is-LOD0-copy.glb', 'bytes': len(good), 'sha256': sha(good)})
    cases.append({'id': 'S02-house-bbox-under-default-family', 'cmd': 'lodset', 'files': s84, 'args': ['--family', 'default'],
                  'inject': 'S84 三档按普通家族判（LOD2 顶部降 0.0997 m > 0.02）', 'expectFail': True, 'expectCodes': ['LOD_BBOX'],
                  'inDeliveryWhitelist': False})
    cases.append({'id': 'S03-tiers-swapped', 'cmd': 'lodset', 'files': [s84[0], s84[2], s84[1]], 'args': ['--family', 'house'],
                  'inject': 'LOD1/LOD2 对调', 'expectFail': True, 'expectCodes': ['LOD_NOT_DECREASING'], 'inDeliveryWhitelist': False})

    # ---- 交付包 ----
    pk = os.path.join(NEG, 'packages')
    shutil.rmtree(pk, ignore_errors=True)

    def mkpkg(name, mutate, expect, note):
        d = os.path.join(pk, name)
        os.makedirs(os.path.join(d, 'models'))
        open(os.path.join(d, 'brief.md'), 'w', encoding='utf-8', newline='\n').write('# 负例包\n\n只用于 LY-008 package 检查自检。\n')
        shutil.copyfile(GOOD2, os.path.join(d, 'models', 'S84-LOD2.glb'))
        files = []
        for rel in ('brief.md', 'models/S84-LOD2.glb'):
            bts = open(os.path.join(d, rel), 'rb').read()
            files.append({'path': rel, 'bytes': len(bts), 'sha256': sha(bts), 'public': rel.endswith('.glb')})
        man = {'seat': 'LY-NEG', 'public': False, 'files': files}
        mutate(d, man)
        json.dump(man, open(os.path.join(d, 'delivery-manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        cases.append({'id': name, 'cmd': 'package', 'dir': os.path.relpath(d, ROOT).replace('\\', '/'), 'args': [], 'inject': note,
                      'expectFail': bool(expect), 'expectCodes': expect, 'inDeliveryWhitelist': True})

    mkpkg('P00-good', lambda d, m: None, [], '好包：两个文件，清单大小/SHA 正确')
    mkpkg('P01-size-mismatch', lambda d, m: m['files'][0].update(bytes=m['files'][0]['bytes'] + 1), ['MANIFEST_SIZE_MISMATCH'], '清单 bytes +1')
    mkpkg('P02-sha-mismatch', lambda d, m: m['files'][0].update(sha256='0' * 64), ['MANIFEST_SHA_MISMATCH'], '清单 sha256 全 0')
    mkpkg('P03-missing-file', lambda d, m: m['files'].append({'path': 'models/S84-LOD9.glb', 'bytes': 1, 'sha256': '0' * 64}),
          ['MANIFEST_FILE_MISSING'], '清单列了不存在的文件')
    mkpkg('P04-path-escape-parent', lambda d, m: m['files'].append({'path': '../P00-good/brief.md', 'bytes': 1, 'sha256': '0' * 64}),
          ['PATH_ESCAPE'], '清单路径 ../P00-good/brief.md')
    mkpkg('P05-path-absolute', lambda d, m: m['files'].append({'path': 'D:/GitHub/creation-notebook-lab/README.md', 'bytes': 1, 'sha256': '0' * 64}),
          ['PATH_ESCAPE'], '清单路径为盘符绝对路径')

    def p06(d, m):
        p = os.path.join(d, 'public-note.md')
        open(p, 'w', encoding='utf-8', newline='\n').write(f'导出自 C:\\Users\\{FAKE_USER}\\Documents\\luoyang\\S84.blend\n')
        bts = open(p, 'rb').read()
        m['files'].append({'path': 'public-note.md', 'bytes': len(bts), 'sha256': sha(bts), 'public': True})
    mkpkg('P06-private-path-public-file', p06, ['PRIVATE_PATH_PUBLIC_FILE'], '公共文件 public-note.md 写了 C:\\Users\\<占位用户>\\…')

    def p07(d, m):
        src = os.path.join(NEG, 'N04-nan-position.glb')
        shutil.copyfile(src, os.path.join(d, 'models', 'bad.glb'))
        bts = open(src, 'rb').read()
        m['files'].append({'path': 'models/bad.glb', 'bytes': len(bts), 'sha256': sha(bts), 'public': True})
    mkpkg('P07-contains-bad-glb', p07, ['PACKAGE_GLB_INVALID'], '包内 GLB 带 NaN 顶点')

    def p08(d, m):
        m['files'][0]['path'] = 'models\\..\\brief.md'
    mkpkg('P08-backslash-path', p08, ['PATH_ESCAPE'], '清单路径用反斜杠并含 ..')

    def p09(d, m):
        m['files'][1]['expectFail'] = True
    mkpkg('P09-fixture-unexpectedly-passes', p09, ['FIXTURE_UNEXPECTEDLY_PASSES'], '好 GLB 被清单登记成负例夹具（expectFail: true）')

    def p10(d, m):
        p07(d, m)
        m['files'][-1]['expectFail'] = True
    mkpkg('P10-fixture-registered', p10, [], '坏 GLB 在清单里登记为负例夹具（expectFail: true）：包应通过')

    # ---- 公共目录整树扫（privacy 子命令） ----
    tr = os.path.join(NEG, 'trees')
    shutil.rmtree(tr, ignore_errors=True)

    def mktree(name, files, expect, note, archived=None):
        d = os.path.join(tr, name)
        for rel, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
            mode = 'wb' if isinstance(text, bytes) else 'w'
            with open(os.path.join(d, rel), mode, **({} if mode == 'wb' else {'encoding': 'utf-8', 'newline': '\n'})) as fh:
                fh.write(text)
        cases.append({'id': name, 'cmd': 'privacy', 'dir': os.path.relpath(d, ROOT).replace('\\', '/'), 'args': [], 'inject': note,
                      'expectFail': bool(expect), 'expectCodes': expect, 'inDeliveryWhitelist': True})
    clean = {'library/models/x/x.asset.json': '{"id": "x", "files": [{"path": "files/x-LOD0.glb"}]}\n', 'README.md': '# 公共说明\n\n协议名 file:// 与 https:// 不算路径。\n'}
    mktree('T00-clean-tree', clean, [], '干净的公共目录（提到裸 file:// 协议名不算）')
    mktree('T01-source-file', {**clean, 'library/models/x/x.blend': b'BLENDER-v502 fixture\n'}, ['SOURCE_FILE_IN_PUBLIC'], '公共目录里混进 .blend')
    mktree('T02-private-path', {**clean, 'cities/luoyang/notes.md': f'源包在 C:\\Users\\{FAKE_USER}\\Desktop\\luoyang.zip\n'},
           ['PRIVATE_PATH_PUBLIC_FILE'], '公共 md 写了 C:\\Users\\<占位用户>\\Desktop\\…')
    mktree('T03-drive-path', {**clean, 'asset-spec/HOWTO.md': '源包落盘到 D:/GitHub/somewhere/r1/model.blend\n'},
           ['PRIVATE_PATH_PUBLIC_FILE'], '公共 md 写了 D:/ 盘路径')
    mktree('T04-weak-only', {**clean, 'studies/x/run.py': "SCRUB = re.compile(r'/home/agent/')\n"}, [],
           '只有 /home/agent/ 式通用路径（弱判据：警告不判错）')

    # ---- 第一轮普查误报的回归正例（文件取自 bce3211 导出副本 tmp/repo，SHA = 提交字节） ----
    for cid, rel, note in (
            ('R01-bin-backslash-noise', 'tmp/repo/docs/cities/luoyang/assets/c02/C02-environment.glb', '贴图二进制里有大量 0x5C（第一轮 UNC 判据误报）'),
            ('R02-meshopt-fallback-buffer', 'tmp/repo/docs/library/models/m-luoyang-a1-neighborhood/files/A1-v3-LOD1.glb', 'meshopt 回退缓冲无数据（第一轮误判 GLTF_BUFFER_NO_SOURCE）'),
            ('R03-instanced-mesh', 'tmp/repo/docs/library/models/m-luoyang-residential-life/files/life-block-LOD0.glb', 'mesh 多实例：官方口径 116,108 三角，绘制 506,828（第一轮误判超限，现为警告）')):
        full = os.path.join(ROOT, rel)
        if os.path.isfile(full):
            bts = open(full, 'rb').read()
            cases.append({'id': cid, 'file': rel, 'bytes': len(bts), 'sha256': sha(bts), 'cmd': 'glb', 'args': [], 'inject': note,
                          'expectFail': False, 'expectCodes': [], 'inDeliveryWhitelist': False})

    # 好样本
    for p in sorted(os.listdir(os.path.join(LY7, 'models', 'samples'))) + ['../refsphere/' + x for x in sorted(os.listdir(os.path.join(LY7, 'models', 'refsphere')))]:
        full = os.path.normpath(os.path.join(LY7, 'models', 'samples', p))
        bts = open(full, 'rb').read()
        rel = os.path.relpath(full, ROOT).replace('\\', '/')
        lod = int(p.rsplit('LOD', 1)[1][0])
        for prof in ('base', 'ly-p01'):
            cases.append({'id': f'G-{prof}-{os.path.basename(p)}', 'file': rel, 'bytes': len(bts), 'sha256': sha(bts), 'cmd': 'glb',
                          'args': ['--profile', prof] + (['--lod', str(lod), '--tex-manifest', '{LY7}/textures/manifest.json'] if prof == 'ly-p01' else []),
                          'inject': '无（LY-007 好样件原字节）', 'expectFail': False, 'expectCodes': [], 'inDeliveryWhitelist': False})
    for nm, fam in (('S84', 'house'), ('G10', 'house'), ('lyref-A', 'default')):
        sub = 'refsphere' if nm == 'lyref-A' else 'samples'
        fs = [os.path.relpath(os.path.join(LY7, 'models', sub, f'{nm}-LOD{i}.glb'), ROOT).replace('\\', '/') for i in range(3)]
        cases.append({'id': f'G-lodset-{nm}', 'cmd': 'lodset', 'files': fs, 'args': ['--family', fam], 'inject': '无（LY-007 三档原字节）',
                      'expectFail': False, 'expectCodes': [], 'inDeliveryWhitelist': False})

    json.dump({'generator': 'source/make_negatives.py', 'goodSource': {os.path.basename(p): sha(open(p, 'rb').read()) for p in (GOOD0, GOOD1, GOOD2)},
               'fakeUserNote': f'私密路径负例用占位用户名 {FAKE_USER}（虚构），真实用户名判据在运行时取环境变量', 'cases': cases},
              open(os.path.join(NEG, 'cases.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(len(cases), 'cases')


if __name__ == '__main__':
    main()
