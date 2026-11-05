# -*- coding: utf-8 -*-
"""LY-007 贴图来源核验（只读 lab 仓库，读提交 blob，不读检出字节）。
用法: python -I verify_textures.py <LY-007 目录> <lab 仓库> <commit>
1. 本席位 textures/ 下每张 PNG 的 sha256、尺寸、位深、通道、均值 / std 与 manifest.json 记录逐项比对；
2. 从 commit 中 manifest 记录的 source_glb（及 G10/S84 三档）读 GLB，取出嵌入的 PNG 原字节，按 image.name 对应，
   核对本席位贴图与她 GLB 里嵌入的字节逐字节相同；
3. 输出 qa/texture-provenance.json。
"""
import sys, os, json, hashlib, struct, subprocess, zlib

W, LAB, COMMIT = sys.argv[1], sys.argv[2], sys.argv[3]
TEX = os.path.join(W, 'textures')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def png_info(b):
    assert b[:8] == b'\x89PNG\r\n\x1a\n'
    w, h, depth, ctype = struct.unpack('>IIBB', b[16:26])
    # 解码求均值（8-bit RGB 无隔行）
    pos, idat = 8, b''
    while pos < len(b):
        ln = struct.unpack('>I', b[pos:pos + 4])[0]; typ = b[pos + 4:pos + 8]
        if typ == b'IDAT':
            idat += b[pos + 8:pos + 8 + ln]
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {2: 3, 6: 4, 0: 1}[ctype]
    stride = w * ch
    rows, prev = [], bytearray(stride)
    i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0
            c = prev[x - ch] if x >= ch else 0
            up = prev[x]
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + up) & 255
            elif f == 3: line[x] = (line[x] + ((a + up) >> 1)) & 255
            elif f == 4:
                p = a + up - c; pa, pb, pc = abs(p - a), abs(p - up), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (up if pb <= pc else c))) & 255
        rows.append(bytes(line)); prev = line
    n = w * h
    sums = [0] * ch; sq = [0] * ch
    for r in rows:
        for k in range(ch):
            col = r[k::ch]
            sums[k] += sum(col); sq[k] += sum(v * v for v in col)
    mean = [s / n for s in sums]
    std = [max(q / n - m * m, 0) ** 0.5 for q, m in zip(sq, mean)]
    return dict(size=[w, h], bit_depth=depth, color_type=ctype, channels=ch,
                mean=[round(m, 2) for m in mean], std=[round(s, 2) for s in std])


def git_blob(path):
    return subprocess.run(['git', '-C', LAB, 'show', f'{COMMIT}:{path}'], capture_output=True, check=True).stdout


def glb_images(b):
    jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + jl]); off = 20 + jl
    bl = struct.unpack('<I', b[off:off + 4])[0]
    bn = b[off + 8:off + 8 + bl]
    out = {}
    for im in j.get('images', []):
        bv = j['bufferViews'][im['bufferView']]
        o = bv.get('byteOffset', 0)
        out[im.get('name')] = bn[o:o + bv['byteLength']]
    return out


man = json.load(open(os.path.join(TEX, 'manifest.json'), encoding='utf-8'))
rows = []
for m in man:
    p = os.path.join(TEX, m['file'])
    b = open(p, 'rb').read()
    info = png_info(b)
    row = dict(file='textures/' + m['file'], image_name=m['image_name'], bytes=len(b), sha256=sha(b),
               manifest_sha_match=sha(b) == m['sha256'], manifest_bytes_match=len(b) == m['bytes'], **info,
               manifest_mean=m.get('mean_srgb'), manifest_std=m.get('std'), source_glb=m.get('source_glb'))
    row['mean_match'] = all(abs(a - c) <= 0.02 for a, c in zip(info['mean'], m.get('mean_srgb', info['mean'])))
    rows.append(row)

# 她的 GLB 嵌入字节核对
srcs = sorted({r['source_glb'] for r in rows if r['source_glb']})
srcs += ['library/models/m-luoyang-market-modular-assembly/files/S84-LOD0.glb',
         'library/models/m-luoyang-market-modular-assembly/files/S84-LOD1.glb',
         'library/models/m-luoyang-ordinary-house-types/files/G10-LOD0.glb',
         'library/models/m-luoyang-ordinary-house-types/files/G10-LOD1.glb']
embedded = {}
for s in srcs:
    path = 'docs/' + s if not s.startswith('docs/') else s
    try:
        b = git_blob(path)
    except subprocess.CalledProcessError:
        embedded[s] = {'error': 'not in commit'}
        continue
    ims = glb_images(b)
    embedded[s] = {'glb_sha256': sha(b), 'images': {k: sha(v) for k, v in ims.items()}}

for r in rows:
    hits = []
    for s, e in embedded.items():
        for nm, h in e.get('images', {}).items():
            if h == r['sha256']:
                hits.append(f'{s}#{nm}')
    r['byte_identical_in_her_glb_at_commit'] = hits

ok = all(r['manifest_sha_match'] and r['manifest_bytes_match'] for r in rows)
non_legacy = [r for r in rows if 'legacy' not in r['file']]
prov_ok = all(r['byte_identical_in_her_glb_at_commit'] for r in non_legacy if r['source_glb'])
res = dict(commit=COMMIT, textures=rows, her_glbs=embedded,
           summary=dict(n=len(rows), all_manifest_match=ok,
                        non_legacy=len(non_legacy),
                        non_legacy_with_byte_identical_source_in_commit=sum(1 for r in non_legacy if r['byte_identical_in_her_glb_at_commit']),
                        legacy=len(rows) - len(non_legacy)))
json.dump(res, open(os.path.join(W, 'qa', 'texture-provenance.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res['summary'], ensure_ascii=False))
for r in rows:
    print(r['file'], r['sha256'][:12], r['size'], r['channels'], r['mean'], 'man', r['manifest_sha_match'], 'src', len(r['byte_identical_in_her_glb_at_commit']))
