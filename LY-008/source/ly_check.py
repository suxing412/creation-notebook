#!/usr/bin/env python3
"""LY-008 可重跑交付检查器（东汉洛阳 100 席位任务池）。

只读：不改任何输入文件。依赖 Python 3.11 标准库 + numpy（几何数组）+ 可选 Pillow（贴图解码复核）。
运行一律用 `python -I`，从任何目录都可以跑（本文件不 import 同目录别的模块）。

子命令
  glb      <file.glb ...> [--profile base|ly-p01] [--lod N] [--upload-limit BYTES --upload-encoding raw|base64]
           单个 GLB：容器/块长度、JSON、buffer/bufferView/accessor 越界、索引越界、NaN/Inf、POSITION min/max、
           三角数、UV、法线、贴图（存在/内嵌/魔数/尺寸/解码）、路径隐私、越界相对路径、正式 15,000,000 字节上限、
           面数上限；ly-p01 档再加 LY-007 冻结的材质名/贴图分辨率/她的贴图字节/节点 TRS/世界盒式 UV/平直法线/落地。
  lodset   <LOD0> <LOD1> <LOD2> [--family default|house]
           三档关系：LOD0 复制改名禁令、三角比、包围盒（house 族 LOD2 顶部允许下降 ≤ 0.10 m，LY-007 D-LOD-BBOX）。
  package  <seat_dir> [--manifest delivery-manifest.json]
           席位交付包：清单里每个文件的存在/大小/SHA256、路径必须是包内相对路径（无 ..、无绝对、无反斜杠）、
           包内 GLB 逐个跑 glb 检查、文本文件私密路径扫描（public 文件 = 错误，内部文件 = 警告）。
  privacy  <public_dir> [--archived source-archive.json]
           把将要公开的目录（docs/）整树扫：文本文件私密路径（强判据 = 错误，/home/ 式弱判据 = 警告）、源工程扩展名、链接越界。
  official <repo_copy_dir>
           在「仓库导出副本」里调用官方 `python -I lab/tools/build_assets.py --check`，记录规范版本、命令、退出码。
           拒绝在含 .git 的目录（即原仓库）里运行。

输出：--json <path> 写完整报告；标准输出打印摘要。任何 error 级问题 → 退出码 1；只有 warning → 0。
每条问题有稳定的代码（code），自检脚本按代码断言负例确实失败。
"""
import argparse, base64, hashlib, json, math, os, re, struct, subprocess, sys, zlib

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

CHECKER_VERSION = 'ly-check 1.0 (LY-008, 2026-11-05)'

# ---- 正式上限（与官方 docs/asset-spec/categories.json limits 一致：glbMaxMB 15 → 按 1e6 字节/MB 判 >） ----
GLB_MAX_BYTES = 15_000_000
GLB_WARN_BYTES = 5_000_000
TRI_MAX = 500_000
TRI_WARN = 150_000
HIGH_DRAWCALLS = 300

CT = {5120: ('i1', 1), 5121: ('u1', 1), 5122: ('<i2', 2), 5123: ('<u2', 2), 5125: ('<u4', 4), 5126: ('<f4', 4)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
CHUNK_JSON, CHUNK_BIN = 0x4E4F534A, 0x004E4942
MAGIC = {'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff', 'image/webp': b'RIFF'}
KNOWN_EXT = {'KHR_mesh_quantization', 'EXT_meshopt_compression', 'KHR_meshopt_compression', 'KHR_draco_mesh_compression',
             'KHR_texture_transform', 'KHR_materials_emissive_strength', 'KHR_texture_basisu', 'EXT_texture_webp',
             'KHR_materials_unlit', 'KHR_lights_punctual', 'EXT_mesh_gpu_instancing'}
COMPRESSED = {'EXT_meshopt_compression', 'KHR_meshopt_compression', 'KHR_draco_mesh_compression'}

# ---- LY-007 冻结基线（baseline/LY_P01-material-semantics.json、texture-uv-rules.json、lod-rules.json） ----
LY_MATS = ('earth', 'timber', 'tile', 'path', 'paper__stone')
LY_MAT_RE = re.compile(r'^LY_P01_(earth|timber|tile|path|paper__stone)__(PBR|FLAT)$')
LY_TEX_RES = {0: 512, 1: 256}
LY_IMAGE_NAME_RE = re.compile(r'^(earth|wood|tile|stone|path)-(basecolor|normal|orm)$')
LY_ATTRS = ['NORMAL', 'POSITION', 'TEXCOORD_0']
LY_GROUND_TOL = 0.002
LY_LOD_TRI_RATIO = {1: (0.17, 0.62), 2: (0.05, 0.20)}
LY_LOD_BBOX = {'LOD1': 1e-4, 'LOD2': 0.02, 'LOD2_house_top_drop': 0.10}


# ===================================================================== 私密路径与越界路径
def private_patterns(extra_tokens=()):
    """私密路径判据。返回 [(名字, 编译后的正则)]。用户名取环境变量 + 命令行 --private-token。"""
    toks = set(t for t in extra_tokens if t)
    for k in ('USERNAME', 'USER', 'LOGNAME'):
        v = os.environ.get(k)
        if v and len(v) >= 3:
            toks.add(v)
    prof = os.environ.get('USERPROFILE') or os.environ.get('HOME') or ''
    b = os.path.basename(prof.rstrip('\\/'))
    if len(b) >= 3:
        toks.add(b)
    pats = [
        ('drive-absolute', re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]{1,2}[^\s"\'<>|*?\\/][^\s"\'<>|]*')),
        # \u0000、\x20 这类转义序列不是 UNC
        ('unc-path', re.compile(r'\\\\(?![ux][0-9A-Fa-f]{2})[A-Za-z0-9][A-Za-z0-9_.$-]+\\[A-Za-z0-9_.$ -]+')),
        # 只有带了盘符或家目录的 file:// 才算私密（裸的 file:// 是协议名）
        ('file-uri', re.compile(r'file:/{2,3}(?:[A-Za-z]:|(?:Users|home)/)[^\s"\'<>]*', re.I)),
        ('posix-home', re.compile(r'(?<![A-Za-z0-9_.])/(?:Users|home|root)/[^\s"\'<>]*')),
        ('windows-users-dir', re.compile(r'[\\/]Users[\\/][^\s"\'<>\\/]+', re.I)),
        ('appdata', re.compile(r'AppData[\\/](?:Local|Roaming)', re.I)),
    ]
    for t in sorted(toks):
        pats.append(('username:' + t[0] + '*' * (len(t) - 1), re.compile(r'(?<![A-Za-z0-9])' + re.escape(t) + r'(?![A-Za-z0-9])', re.I)))
    return pats


# 二进制块（贴图像素、顶点数据）里反斜杠、斜杠、冒号到处都是，宽松判据会误报（bce3211 普查第一轮里 UNC 判据误报 39 个文件，
# 见 qa/census-round1-falsepositives.json），所以 BIN 只用这些需要成词的严格判据 + 用户名。
BIN_STRICT = [
    ('drive-absolute-strict', re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/](?:Users|GitHub|Documents|Desktop|Blender|tmp|temp|Program Files)[\\/]', re.I)),
    ('file-uri', re.compile(r'file:/{2,3}[A-Za-z0-9]', re.I)),
    ('posix-home-strict', re.compile(r'(?<![A-Za-z0-9_.])/(?:Users|home)/[a-z_][a-z0-9_.-]{1,31}/', re.I)),
    ('windows-users-dir-strict', re.compile(r'[\\/]Users[\\/][A-Za-z0-9._-]{2,}[\\/](?:AppData|Desktop|Documents|Downloads)', re.I)),
    ('appdata', re.compile(r'AppData[\\/](?:Local|Roaming)[\\/]', re.I)),
]


# 弱判据：/home/…、/Users/… 在文档和脚本里常作通用示例或清洗正则出现，公共文件里只记警告；其余为强判据，记错误。
WEAK_KINDS = {'posix-home'}


def scan_private(text, pats, limit=20):
    """在一段文本里找私密路径，返回 [{kind, strong, match(截断)}]。"""
    hits = []
    for name, rx in pats:
        for m in rx.finditer(text):
            s = m.group(0)
            hits.append({'kind': name, 'strong': name not in WEAK_KINDS, 'match': (s[:80] + '…') if len(s) > 80 else s, 'at': m.start()})
            if len(hits) >= limit:
                return hits
    return hits


def scan_private_bytes(data, pats):
    """二进制块里按 ASCII/UTF-8 与 UTF-16LE 两种编码找私密路径（PNG tEXt、嵌入的源路径等）。"""
    hits = []
    try:
        t8 = data.decode('latin-1')
        hits += [dict(h, encoding='latin1/utf8') for h in scan_private(t8, pats)]
    except Exception:  # noqa: BLE001
        pass
    if len(data) >= 2:
        t16 = data[: len(data) - len(data) % 2].decode('utf-16-le', errors='replace')
        hits += [dict(h, encoding='utf-16le') for h in scan_private(t16, pats)]
    return hits


def bad_relpath(p):
    """相对路径是否越界：绝对路径、盘符、反斜杠、.. 段、空段。返回原因或 None。"""
    if not isinstance(p, str) or not p:
        return 'empty'
    if p.startswith('data:'):
        return None
    if re.match(r'^[A-Za-z]:', p) or p.startswith(('/', '\\')):
        return 'absolute'
    if re.match(r'^[a-z][a-z0-9+.-]*://', p, re.I):
        return 'remote-uri'
    if '\\' in p:
        return 'backslash'
    from urllib.parse import unquote
    segs = unquote(p).split('/')
    if any(s == '..' for s in segs):
        return 'parent-escape'
    if any(s == '' for s in segs[:-1]):
        return 'empty-segment'
    return None


# ===================================================================== 报告工具
class Report:
    def __init__(self, subject):
        self.subject = subject
        self.issues = []
        self.info = {}

    def err(self, code, msg, **kw):
        self.issues.append({'level': 'error', 'code': code, 'msg': msg, **kw})

    def warn(self, code, msg, **kw):
        self.issues.append({'level': 'warning', 'code': code, 'msg': msg, **kw})

    def note(self, code, msg, **kw):
        self.issues.append({'level': 'info', 'code': code, 'msg': msg, **kw})

    @property
    def errors(self):
        return [i for i in self.issues if i['level'] == 'error']

    @property
    def warnings(self):
        return [i for i in self.issues if i['level'] == 'warning']

    def as_dict(self):
        return {'subject': self.subject, 'ok': not self.errors, 'errorCodes': sorted({i['code'] for i in self.errors}),
                'warningCodes': sorted({i['code'] for i in self.warnings}), 'info': self.info, 'issues': self.issues}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


# ===================================================================== GLB 容器
def parse_container(raw, R):
    """严格解析 GLB 容器。返回 (json_dict, bin_bytes) 或 (None, None)。"""
    n = len(raw)
    R.info['bytes'] = n
    if n < 12:
        R.err('GLB_TRUNCATED', f'文件只有 {n} 字节，连 12 字节头都不够')
        return None, None
    magic, ver, length = struct.unpack_from('<4sII', raw, 0)
    if magic != b'glTF':
        R.err('GLB_BAD_MAGIC', f'魔数是 {magic!r}，不是 b"glTF"')
        return None, None
    if ver != 2:
        R.err('GLB_BAD_VERSION', f'容器版本 {ver}，只接受 2')
    if length != n:
        R.err('GLB_LENGTH_MISMATCH', f'头部声明长度 {length}，实际文件 {n} 字节')
    if n % 4:
        R.err('GLB_UNALIGNED', f'文件长度 {n} 不是 4 的倍数')
    off, chunks = 12, []
    end = min(length, n) if length >= 12 else n
    while off < end:
        if off + 8 > end:
            R.err('GLB_CHUNK_TRUNCATED', f'偏移 {off} 处块头不完整')
            break
        clen, ctype = struct.unpack_from('<II', raw, off)
        if clen % 4:
            R.err('GLB_CHUNK_UNALIGNED', f'块 {len(chunks)} 长度 {clen} 不是 4 的倍数')
        if off + 8 + clen > end:
            R.err('GLB_CHUNK_OVERRUN', f'块 {len(chunks)}（类型 0x{ctype:08X}）声明 {clen} 字节，超出文件（剩 {end - off - 8}）')
            chunks.append((ctype, raw[off + 8:end]))
            off = end
            break
        chunks.append((ctype, raw[off + 8: off + 8 + clen]))
        off += 8 + clen
    if off != end and not R.errors:
        R.err('GLB_TRAILING_BYTES', f'块结束于 {off}，声明长度 {end}')
    if not chunks or chunks[0][0] != CHUNK_JSON:
        R.err('GLB_NO_JSON_CHUNK', '第一个块不是 JSON 块')
        return None, None
    try:
        jtxt = chunks[0][1].decode('utf-8').rstrip(' \x00')
        js = json.loads(jtxt)
    except Exception as e:  # noqa: BLE001
        R.err('GLB_BAD_JSON', f'JSON 块解析失败：{e}')
        return None, None
    if not isinstance(js, dict):
        R.err('GLB_BAD_JSON', 'JSON 块不是对象')
        return None, None
    bins = [c for t, c in chunks[1:] if t == CHUNK_BIN]
    if len([1 for t, _ in chunks if t == CHUNK_BIN]) > 1:
        R.err('GLB_MULTI_BIN', '有多个 BIN 块')
    R.info['jsonChunkBytes'] = len(chunks[0][1])
    R.info['binChunkBytes'] = len(bins[0]) if bins else 0
    return js, (bins[0] if bins else b'')


# ===================================================================== GLB 内容
def _finite_tree(x, path, out):
    """在 JSON 里找 NaN/Inf（Python json 会把 NaN/Infinity 字面量读成 float）。"""
    if isinstance(x, float):
        if not math.isfinite(x):
            out.append(path)
    elif isinstance(x, dict):
        for k, v in x.items():
            _finite_tree(v, f'{path}.{k}', out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            _finite_tree(v, f'{path}[{i}]', out)


def _all_strings(x, out, path='$'):
    if isinstance(x, str):
        out.append((path, x))
    elif isinstance(x, dict):
        for k, v in x.items():
            out.append((f'{path}.<key>', k))
            _all_strings(v, out, f'{path}.{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            _all_strings(v, out, f'{path}[{i}]')


def png_info(data):
    """PNG：IHDR 宽高、色深、色型；文字块（tEXt/iTXt/zTXt）内容；CRC 检查。"""
    if data[:8] != MAGIC['image/png']:
        return None
    off, out, texts, crc_bad = 8, {}, [], 0
    while off + 8 <= len(data):
        ln, typ = struct.unpack_from('>I4s', data, off)
        body = data[off + 8: off + 8 + ln]
        crc = data[off + 8 + ln: off + 12 + ln]
        if len(body) < ln or len(crc) < 4:
            out['truncated'] = True
            break
        if zlib.crc32(typ + body) & 0xffffffff != struct.unpack('>I', crc)[0]:
            crc_bad += 1
        if typ == b'IHDR':
            out['w'], out['h'], out['depth'], out['colorType'] = struct.unpack('>IIBB', body[:10])
        elif typ in (b'tEXt', b'iTXt'):
            texts.append(body.decode('latin-1', 'replace'))
        elif typ == b'zTXt':
            try:
                k, rest = body.split(b'\x00', 1)
                texts.append(k.decode('latin-1') + '=' + zlib.decompress(rest[1:]).decode('latin-1', 'replace'))
            except Exception:  # noqa: BLE001
                texts.append('<zTXt unreadable>')
        off += 12 + ln
        if typ == b'IEND':
            break
    out['texts'] = texts
    out['crcBad'] = crc_bad
    return out


def read_accessor(g, binb, ai, R, what):
    """把 accessor 读成 numpy 数组（float64 或 int64），越界则记错误并返回 None。"""
    accs, bvs = g.get('accessors', []), g.get('bufferViews', [])
    if not isinstance(ai, int) or not (0 <= ai < len(accs)):
        R.err('GLTF_BAD_ACCESSOR_INDEX', f'{what} 引用了不存在的 accessor {ai}')
        return None
    a = accs[ai]
    if a.get('componentType') not in CT or a.get('type') not in NC:
        R.err('GLTF_BAD_ACCESSOR_TYPE', f'accessor {ai}（{what}）类型 {a.get("componentType")}/{a.get("type")} 不认识')
        return None
    if 'sparse' in a:
        R.warn('GLTF_SPARSE_UNCHECKED', f'accessor {ai} 是 sparse，本检查器未展开')
    cnt = a.get('count', 0)
    dt, cs = CT[a['componentType']]
    nc = NC[a['type']]
    if 'bufferView' not in a:
        return np.zeros((cnt, nc))
    bi = a['bufferView']
    if not (0 <= bi < len(bvs)):
        R.err('GLTF_BAD_BUFFERVIEW_INDEX', f'accessor {ai} 引用了不存在的 bufferView {bi}')
        return None
    bv = bvs[bi]
    if bv.get('_meshopt'):
        return 'compressed'
    elem = cs * nc
    stride = bv.get('byteStride') or elem
    ao = a.get('byteOffset', 0)
    need = ao + (stride * (cnt - 1) + elem if cnt else 0)
    if need > bv.get('byteLength', 0):
        R.err('GLTF_ACCESSOR_OVERRUN', f'accessor {ai}（{what}）需要 {need} 字节，bufferView {bi} 只有 {bv.get("byteLength")}')
        return None
    if (bv.get('byteOffset', 0) + ao) % cs:
        R.err('GLTF_ACCESSOR_MISALIGNED', f'accessor {ai} 偏移没有按 {cs} 字节对齐')
    if not bv.get('_inbin', True):
        return None
    base = bv.get('byteOffset', 0) + ao
    if stride == elem:
        arr = np.frombuffer(binb, dt, count=cnt * nc, offset=base).reshape(cnt, nc)
    else:
        arr = np.ndarray(shape=(cnt, nc), dtype=np.dtype(dt), buffer=binb[base: base + (stride * (cnt - 1) + elem if cnt else 0)],
                         strides=(stride, cs))
    if a.get('normalized') and a['componentType'] != 5126:
        info = np.iinfo(np.dtype(dt))
        arr = np.maximum(arr.astype(np.float64) / info.max, -1.0)
    return arr.astype(np.float64) if a['componentType'] == 5126 or a.get('normalized') else arr.astype(np.int64)


def node_matrix(n):
    if 'matrix' in n:
        return np.array(n['matrix'], dtype=np.float64).reshape(4, 4).T
    t = n.get('translation', [0, 0, 0]); r = n.get('rotation', [0, 0, 0, 1]); s = n.get('scale', [1, 1, 1])
    x, y, z, w = r
    Rm = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                   [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                   [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    M = np.eye(4)
    M[:3, :3] = Rm * np.array(s)[None, :]
    M[:3, 3] = t
    return M


def check_glb(path, profile='base', lod=None, upload_limit=None, upload_encoding='base64', pats=None, tex_manifest=None,
              display_path=None):
    """检查一个 GLB 文件。返回 Report。"""
    R = Report(display_path or path.replace('\\', '/'))
    pats = pats if pats is not None else private_patterns()
    try:
        raw = open(path, 'rb').read()
    except OSError as e:
        R.err('FILE_UNREADABLE', f'读不到文件：{e}')
        return R
    R.info['sha256'] = sha256_bytes(raw)
    n = len(raw)
    # ---- 体积：正式上限与上传承载分开 ----
    R.info['formalLimitBytes'] = GLB_MAX_BYTES
    if n > GLB_MAX_BYTES:
        R.err('GLB_OVER_FORMAL_LIMIT', f'{n:,} 字节 > 正式上限 {GLB_MAX_BYTES:,}（官方 glbMaxMB=15，按 1e6 字节/MB）')
    elif n > GLB_WARN_BYTES:
        R.warn('GLB_LARGE', f'{n:,} 字节 > 建议值 {GLB_WARN_BYTES:,}')
    b64 = 4 * ((n + 2) // 3)
    R.info['upload'] = {'rawBytes': n, 'base64Bytes': b64, 'encoding': upload_encoding, 'limit': upload_limit,
                        'note': '上传承载与正式上限分开判：正式上限只看文件字节；承载只在给出具体通道上限时判'}
    if upload_limit:
        carried = b64 if upload_encoding == 'base64' else n
        R.info['upload']['carriedBytes'] = carried
        if carried > upload_limit:
            R.err('UPLOAD_OVER_CHANNEL_LIMIT', f'按 {upload_encoding} 承载 {carried:,} 字节 > 通道上限 {upload_limit:,}（与正式上限无关）')
        R.info['upload']['verdict'] = 'fail' if carried > upload_limit else 'pass'
    else:
        R.info['upload']['verdict'] = 'not-judged'
    if np is None:
        R.err('CHECKER_NO_NUMPY', '缺 numpy，几何检查无法进行')
        return R
    g, binb = parse_container(raw, R)
    if g is None:
        return R
    # ---- JSON 层：版本、扩展、NaN/Inf、私密路径 ----
    asset = g.get('asset') or {}
    R.info['gltfVersion'] = asset.get('version')
    R.info['generator'] = asset.get('generator')
    if asset.get('version') != '2.0':
        R.err('GLTF_BAD_ASSET_VERSION', f'asset.version = {asset.get("version")!r}，应为 "2.0"')
    eu, er = g.get('extensionsUsed') or [], g.get('extensionsRequired') or []
    R.info['extensionsUsed'] = eu
    for e in er:
        if e not in eu:
            R.err('GLTF_EXT_REQUIRED_NOT_USED', f'extensionsRequired 里的 {e} 不在 extensionsUsed')
        if e not in KNOWN_EXT:
            R.err('GLTF_EXT_REQUIRED_UNKNOWN', f'必需扩展 {e} 本检查器与站点加载器都没有登记')
    if set(er) & COMPRESSED:
        R.note('GLTF_COMPRESSED', f'几何经 {sorted(set(er) & COMPRESSED)} 压缩，本检查器不解压，几何数值检查跳过')
    nonfinite = []
    _finite_tree(g, '$', nonfinite)
    if nonfinite:
        R.err('GLTF_JSON_NONFINITE', f'JSON 里有 {len(nonfinite)} 个 NaN/Inf：{nonfinite[:5]}')
    strs = []
    _all_strings(g, strs)
    priv = []
    for p_, s in strs:
        for h in scan_private(s, pats, limit=5):
            priv.append({'jsonPath': p_, **h})
    if priv:
        R.err('PRIVATE_PATH_IN_JSON', f'JSON 里有 {len(priv)} 处私密路径/用户名', hits=priv[:20])
    # ---- buffers / bufferViews ----
    bufs, bvs = g.get('buffers', []), g.get('bufferViews', [])
    meshopt = set(er) & COMPRESSED or set(eu) & COMPRESSED
    for i, b in enumerate(bufs):
        bl = b.get('byteLength', 0)
        if 'uri' in b:
            why = bad_relpath(b['uri'])
            if why and why != 'remote-uri':
                R.err('PATH_ESCAPE', f'buffers[{i}].uri 越界（{why}）：{b["uri"][:80]}')
            if not str(b['uri']).startswith('data:'):
                R.err('GLTF_EXTERNAL_BUFFER', f'buffers[{i}] 引用外部文件 {b["uri"][:80]}，GLB 须自包含')
        elif i == 0:
            if bl > len(binb):
                R.err('GLTF_BUFFER_OVERRUN', f'buffers[0].byteLength={bl} > BIN 块 {len(binb)} 字节')
            elif len(binb) - bl > 3:
                R.err('GLTF_BUFFER_SLACK', f'BIN 块比 buffers[0].byteLength 多 {len(binb) - bl} 字节（只允许 ≤3 字节填充）')
        elif ((b.get('extensions') or {}).get('EXT_meshopt_compression') or (b.get('extensions') or {}).get('KHR_meshopt_compression') or {}).get('fallback'):
            pass  # meshopt 回退缓冲：规范允许无数据
        else:
            R.err('GLTF_BUFFER_NO_SOURCE', f'buffers[{i}] 没有 uri 也不是 GLB BIN')
    for i, bv in enumerate(bvs):
        bi = bv.get('buffer', -1)
        if not (0 <= bi < len(bufs)):
            R.err('GLTF_BAD_BUFFER_INDEX', f'bufferViews[{i}] 引用不存在的 buffer {bi}')
            bv['_inbin'] = False
            continue
        end = bv.get('byteOffset', 0) + bv.get('byteLength', 0)
        lim = min(bufs[bi].get('byteLength', 0), len(binb)) if bi == 0 and 'uri' not in bufs[bi] else bufs[bi].get('byteLength', 0)
        if end > lim:
            R.err('GLTF_BUFFERVIEW_OVERRUN', f'bufferViews[{i}] 结束于 {end}，buffer {bi} 只有 {lim} 字节')
            bv['_inbin'] = False
        else:
            bv['_inbin'] = bi == 0 and 'uri' not in bufs[bi]
        if (bv.get('extensions') or {}).keys() & COMPRESSED:
            bv['_meshopt'] = True
    # ---- 贴图：材质引用 → texture → image → 字节 ----
    imgs, texs, mats = g.get('images', []), g.get('textures', []), g.get('materials', [])
    image_report = []
    tex_sha = {}
    for i, im in enumerate(imgs):
        rec = {'index': i, 'name': im.get('name'), 'mimeType': im.get('mimeType')}
        data = None
        if 'bufferView' in im:
            bi = im['bufferView']
            if not (0 <= bi < len(bvs)) or not bvs[bi].get('_inbin'):
                R.err('TEXTURE_MISSING', f'images[{i}]（{im.get("name")}）的 bufferView {bi} 不存在或越界')
            else:
                o = bvs[bi].get('byteOffset', 0)
                data = binb[o: o + bvs[bi]['byteLength']]
        elif 'uri' in im:
            u = im['uri']
            if u.startswith('data:'):
                try:
                    data = base64.b64decode(u.split(',', 1)[1])
                    R.warn('TEXTURE_DATA_URI', f'images[{i}] 用 data: URI 内嵌（体积多 1/3）')
                except Exception:  # noqa: BLE001
                    R.err('TEXTURE_CORRUPT', f'images[{i}] 的 data: URI 解不开')
            else:
                why = bad_relpath(u)
                if why:
                    R.err('PATH_ESCAPE', f'images[{i}].uri 越界（{why}）：{u[:80]}')
                R.err('TEXTURE_NOT_EMBEDDED', f'images[{i}] 引用外部文件 {u[:80]}，公共 GLB 的纹理必须内嵌')
                ext = os.path.normpath(os.path.join(os.path.dirname(path), u)) if not why else None
                if not ext or not os.path.isfile(ext):
                    R.err('TEXTURE_MISSING', f'images[{i}] 外部文件不存在：{u[:80]}')
        else:
            R.err('TEXTURE_MISSING', f'images[{i}] 既没有 bufferView 也没有 uri')
        if data is not None:
            rec['bytes'] = len(data)
            rec['sha256'] = sha256_bytes(data)
            tex_sha[i] = rec['sha256']
            mt = im.get('mimeType')
            if mt and mt in MAGIC and not data.startswith(MAGIC[mt]):
                R.err('TEXTURE_MIME_MISMATCH', f'images[{i}] 声明 {mt}，字节头是 {data[:8]!r}')
            if not any(data.startswith(m) for m in MAGIC.values()):
                R.err('TEXTURE_CORRUPT', f'images[{i}] 不是 PNG/JPEG/WebP（头 {data[:8]!r}）')
            pi = png_info(data)
            if pi is not None:
                rec.update({k: pi.get(k) for k in ('w', 'h', 'depth', 'colorType')})
                if pi.get('truncated') or pi.get('crcBad') or not pi.get('w'):
                    R.err('TEXTURE_CORRUPT', f'images[{i}] PNG 结构损坏（截断 {pi.get("truncated")}，CRC 错 {pi.get("crcBad")}）')
                for t in pi.get('texts', []):
                    for h in scan_private(t, pats, limit=3):
                        R.err('PRIVATE_PATH_IN_TEXTURE', f'images[{i}] PNG 文字块里有私密路径', hit=h)
            try:
                from PIL import Image
                import io
                with Image.open(io.BytesIO(data)) as pim:
                    pim.load()
                    rec['decoded'] = [pim.width, pim.height, pim.mode]
            except ImportError:
                rec['decoded'] = 'pillow-missing'
            except Exception as e:  # noqa: BLE001
                R.err('TEXTURE_CORRUPT', f'images[{i}] 解码失败：{e}')
        image_report.append(rec)
    for i, t in enumerate(texs):
        src = t.get('source')
        exts = t.get('extensions') or {}
        alt = [v.get('source') for v in exts.values() if isinstance(v, dict) and 'source' in v]
        srcs = [s for s in [src, *alt] if s is not None]
        if not srcs:
            R.err('TEXTURE_MISSING', f'textures[{i}] 没有 source')
        for s in srcs:
            if not (isinstance(s, int) and 0 <= s < len(imgs)):
                R.err('TEXTURE_MISSING', f'textures[{i}].source = {s}，images 只有 {len(imgs)} 张')
        if 'sampler' in t and not (0 <= t['sampler'] < len(g.get('samplers', []))):
            R.err('GLTF_BAD_SAMPLER_INDEX', f'textures[{i}].sampler = {t["sampler"]} 不存在')
    TEXKEYS = ('baseColorTexture', 'metallicRoughnessTexture', 'normalTexture', 'occlusionTexture', 'emissiveTexture')
    mat_texcoords = {}
    for mi, m in enumerate(mats):
        refs = []
        pb = m.get('pbrMetallicRoughness') or {}
        for k in TEXKEYS:
            ti = (pb.get(k) or {}) if k in ('baseColorTexture', 'metallicRoughnessTexture') else (m.get(k) or {})
            if ti:
                refs.append((k, ti))
        for k, ti in refs:
            idx = ti.get('index')
            if not (isinstance(idx, int) and 0 <= idx < len(texs)):
                R.err('TEXTURE_MISSING', f'materials[{mi}]（{m.get("name")}）.{k} 引用不存在的 texture {idx}（共 {len(texs)}）')
            mat_texcoords.setdefault(mi, set()).add(ti.get('texCoord', 0))
    R.info['images'] = image_report
    # ---- 节点与场景 ----
    nodes, meshes = g.get('nodes', []), g.get('meshes', [])
    scenes = g.get('scenes', [])
    if not scenes:
        R.err('GLTF_NO_SCENE', '没有 scenes')
    sc = g.get('scene', 0)
    if scenes and not (0 <= sc < len(scenes)):
        R.err('GLTF_BAD_SCENE_INDEX', f'scene = {sc} 不存在')
        sc = 0
    world = {}
    seen = set()

    def walk(ni, M, depth):
        if not (isinstance(ni, int) and 0 <= ni < len(nodes)):
            R.err('GLTF_BAD_NODE_INDEX', f'引用不存在的节点 {ni}')
            return
        if ni in seen:
            R.err('GLTF_NODE_CYCLE', f'节点 {ni} 被引用多次或成环')
            return
        seen.add(ni)
        Mi = M @ node_matrix(nodes[ni])
        world[ni] = Mi
        for c in nodes[ni].get('children', []):
            walk(c, Mi, depth + 1)
    for r in (scenes[sc].get('nodes', []) if scenes else []):
        walk(r, np.eye(4), 0)
    nontrivial = []
    for ni, n in enumerate(nodes):
        if 'mesh' in n and not (0 <= n['mesh'] < len(meshes)):
            R.err('GLTF_BAD_MESH_INDEX', f'nodes[{ni}].mesh = {n["mesh"]} 不存在')
        if 'matrix' in n and any(k in n for k in ('translation', 'rotation', 'scale')):
            R.err('GLTF_MATRIX_AND_TRS', f'nodes[{ni}] 同时写了 matrix 与 TRS')
        if ni in world:
            M3 = world[ni][:3, :3]
            d = float(np.linalg.det(M3))
            sc_ = np.linalg.norm(M3, axis=0)
            if 'mesh' in n and d < 0:
                R.warn('NODE_MIRRORED', f'nodes[{ni}]（{n.get("name")}）世界矩阵 det={d:.4f} < 0（镜像）')
            if 'mesh' in n and np.any(np.abs(sc_ - 1) > 1e-6):
                nontrivial.append(n.get('name') or ni)
    if nontrivial:
        R.warn('NODE_NONUNIT_SCALE', f'{len(nontrivial)} 个网格节点世界缩放不是 1（LY-005 R2 只约束城市节点 N；GLB 内部缩放需在端口里说明）',
               nodes=nontrivial[:10])
    # ---- 几何 ----
    tri = verts = prims = degen = nouv = nonorm = 0
    lo = np.full(3, np.inf); hi = np.full(3, -np.inf)
    prim_reports = []
    geometry_read = True
    flat_min, uvbox_min = 1.0, 1.0
    ly_attr_bad = []
    inst = [(n['mesh'], world[ni], n.get('name') or ni, True) for ni, n in enumerate(nodes)
            if 'mesh' in n and ni in world and isinstance(n['mesh'], int) and 0 <= n['mesh'] < len(meshes)]
    used_meshes = {x[0] for x in inst}
    unused = [mi for mi in range(len(meshes)) if mi not in used_meshes]
    if unused:
        R.warn('GLTF_UNUSED_MESH', f'{len(unused)} 个 mesh 没有被默认场景的节点引用（官方 glb_audit 仍把它们计入面数；本检查器照样逐个查数据）')
    inst += [(mi, np.eye(4), f'mesh{mi}(未在场景)', False) for mi in unused]
    multi = sorted({mi for mi in used_meshes if sum(1 for x in inst if x[0] == mi and x[3]) > 1})
    if multi:
        R.note('GLTF_INSTANCED_MESH', f'{len(multi)} 个 mesh 被多个节点实例化：「绘制三角数」按实例计，「官方口径三角数」按 mesh 定义各计一次')
    for mi_, M, nname, drawn in inst:
        for pi_, p in enumerate(meshes[mi_].get('primitives', [])):
            prims += drawn
            tag = f'{nname}#{pi_}'
            at = p.get('attributes') or {}
            mode = p.get('mode', 4)
            if mode != 4:
                R.warn('GLTF_NON_TRIANGLE_MODE', f'{tag} mode={mode}（不是三角形）')
            if profile == 'ly-p01' and sorted(at) != LY_ATTRS:
                ly_attr_bad.append((tag, sorted(at)))
            if 'POSITION' not in at:
                R.err('GLTF_NO_POSITION', f'{tag} 没有 POSITION')
                continue
            pa = g['accessors'][at['POSITION']] if 0 <= at['POSITION'] < len(g.get('accessors', [])) else {}
            pos = read_accessor(g, binb, at['POSITION'], R, f'{tag}.POSITION')
            if isinstance(pos, str):
                geometry_read = False
                if drawn:
                    tri += (g['accessors'][p['indices']]['count'] if 'indices' in p else pa.get('count', 0)) // 3
                    verts += pa.get('count', 0)
                continue
            if pos is None:
                geometry_read = False
                continue
            verts += len(pos) * drawn
            bad = ~np.isfinite(pos)
            if bad.any():
                R.err('GEOM_NONFINITE', f'{tag}.POSITION 有 {int(bad.any(1).sum())} 个顶点含 NaN/Inf')
                pos = np.where(bad, 0, pos)
            if 'min' not in pa or 'max' not in pa:
                R.err('GLTF_POSITION_NO_MINMAX', f'{tag}.POSITION 缺 min/max（glTF 必需）')
            elif len(pos):
                amin, amax = pos.min(0), pos.max(0)
                tol = 1e-5 * max(1.0, float(np.abs(pos).max()))
                if np.any(np.abs(amin - np.array(pa['min'])) > tol) or np.any(np.abs(amax - np.array(pa['max'])) > tol):
                    R.err('GLTF_POSITION_MINMAX_WRONG', f'{tag}.POSITION min/max 与数据不符（声明 {pa["min"]}/{pa["max"]}，实测 {amin.round(5).tolist()}/{amax.round(5).tolist()}）')
            for k in [k for k in at if k != 'POSITION']:
                arr = read_accessor(g, binb, at[k], R, f'{tag}.{k}')
                if isinstance(arr, str) or arr is None:
                    continue
                if len(arr) != len(pos):
                    R.err('GLTF_ATTRIBUTE_COUNT', f'{tag}.{k} 有 {len(arr)} 个，POSITION 有 {len(pos)} 个')
                if arr.dtype.kind == 'f' and not np.isfinite(arr).all():
                    R.err('GEOM_NONFINITE', f'{tag}.{k} 含 NaN/Inf（{int((~np.isfinite(arr)).any(1).sum())} 个）')
                if k == 'NORMAL' and arr.dtype.kind == 'f' and len(arr):
                    ln = np.linalg.norm(np.nan_to_num(arr), axis=1)
                    if np.any(np.abs(ln - 1) > 1e-3):
                        R.warn('GEOM_NORMAL_NOT_UNIT', f'{tag}.NORMAL 有 {int((np.abs(ln - 1) > 1e-3).sum())} 个不是单位长')
            if 'NORMAL' not in at:
                nonorm += 1
            mi = p.get('material')
            if mi is None:
                R.warn('GLTF_PRIM_NO_MATERIAL', f'{tag} 没有材质')
            elif not (0 <= mi < len(mats)):
                R.err('GLTF_BAD_MATERIAL_INDEX', f'{tag}.material = {mi} 不存在')
            need_uv = mat_texcoords.get(mi, set())
            for tc in need_uv:
                if f'TEXCOORD_{tc}' not in at:
                    R.err('UV_MISSING', f'{tag} 的材质用了贴图（texCoord {tc}），图元没有 TEXCOORD_{tc}')
            if 'TEXCOORD_0' not in at:
                nouv += 1
            # 索引
            if 'indices' in p:
                idx = read_accessor(g, binb, p['indices'], R, f'{tag}.indices')
                if isinstance(idx, str) or idx is None:
                    geometry_read = geometry_read and not isinstance(idx, str)
                    continue
                idx = idx.reshape(-1)
                if g['accessors'][p['indices']].get('componentType') not in (5121, 5123, 5125):
                    R.err('GLTF_BAD_INDEX_TYPE', f'{tag} 索引类型不是无符号整数')
                if len(idx) and (idx.max() >= len(pos) or idx.min() < 0):
                    R.err('GEOM_INDEX_OUT_OF_RANGE', f'{tag} 索引最大 {int(idx.max())} ≥ 顶点数 {len(pos)}')
                    idx = idx[idx < len(pos)]
                    idx = idx[: len(idx) // 3 * 3]
            else:
                idx = np.arange(len(pos))
            if mode == 4:
                if len(idx) % 3:
                    R.err('GEOM_INDEX_COUNT', f'{tag} 索引数 {len(idx)} 不是 3 的倍数')
                    idx = idx[: len(idx) // 3 * 3]
                t3 = idx.reshape(-1, 3)
                tri += len(t3) * drawn
                wp = (np.c_[pos, np.ones(len(pos))] @ M.T)[:, :3]
                if len(wp) and drawn:
                    lo = np.minimum(lo, wp.min(0)); hi = np.maximum(hi, wp.max(0))
                P = wp[t3]
                fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
                ar = np.linalg.norm(fn, axis=1)
                same = (t3[:, 0] == t3[:, 1]) | (t3[:, 1] == t3[:, 2]) | (t3[:, 0] == t3[:, 2])
                dg = int((same | (ar < 1e-10)).sum())
                degen += dg
                if profile == 'ly-p01' and len(t3):
                    fnu = fn / np.maximum(ar[:, None], 1e-12)
                    if 'NORMAL' in at:
                        nor = read_accessor(g, binb, at['NORMAL'], R, f'{tag}.NORMAL')
                        if isinstance(nor, np.ndarray) and len(nor) == len(pos):
                            wn = nor @ M[:3, :3].T
                            flat_min = min(flat_min, float((np.einsum('tij,tj->ti', wn[t3], fnu) > 0.9999).mean()))
                    if 'TEXCOORD_0' in at:
                        uv = read_accessor(g, binb, at['TEXCOORD_0'], R, f'{tag}.TEXCOORD_0')
                        if isinstance(uv, np.ndarray) and len(uv) == len(pos):
                            uvbox_min = min(uvbox_min, uv_world_box_ratio(P, fnu, uv[t3]))
            prim_reports.append({'prim': tag, 'vertices': len(pos), 'triangles': len(idx) // 3 if mode == 4 else 0})
    # 官方口径（与 lab/tools/glb_audit.audit 相同）：每个 mesh 定义计一次，不管场景引用几次、是否引用
    accs = g.get('accessors', [])
    m_tri = m_verts = m_prims = 0
    for m in meshes:
        for p in m.get('primitives', []):
            m_prims += 1
            pa = accs[p['attributes']['POSITION']] if isinstance((p.get('attributes') or {}).get('POSITION'), int) and p['attributes']['POSITION'] < len(accs) else {}
            m_verts += pa.get('count', 0)
            if p.get('mode', 4) == 4:
                ic = accs[p['indices']].get('count', 0) if isinstance(p.get('indices'), int) and p['indices'] < len(accs) else pa.get('count', 0)
                m_tri += ic // 3
    R.info.update(trianglesDrawn=int(tri), verticesDrawn=int(verts), primitivesDrawn=prims)
    tri, verts, prims_drawn, prims = m_tri, m_verts, prims, m_prims
    R.info.update(meshes=len(meshes), nodes=len(nodes), primitives=prims, triangles=int(tri), vertices=int(verts),
                  materials=[m.get('name') for m in mats], textures=len(texs), imageCount=len(imgs),
                  degenerateTriangles=degen, primsNoUV=nouv, primsNoNormal=nonorm, geometryRead=geometry_read)
    if np.isfinite(lo).all():
        R.info['bboxMin'] = [round(float(x), 5) for x in lo]
        R.info['bboxMax'] = [round(float(x), 5) for x in hi]
        R.info['size'] = [round(float(h - l), 5) for l, h in zip(lo, hi)]
    if tri > TRI_MAX:
        R.err('GEOM_OVER_TRI_LIMIT', f'{tri:,} 三角 > 官方上限 {TRI_MAX:,}')
    elif tri > TRI_WARN:
        R.warn('GEOM_TRI_HIGH', f'{tri:,} 三角 > 建议值 {TRI_WARN:,}')
    if R.info['trianglesDrawn'] > TRI_MAX >= tri:
        R.warn('GEOM_DRAWN_TRI_OVER_LIMIT', f'官方口径 {tri:,} 三角未超限，但按场景实例绘制 {R.info["trianglesDrawn"]:,} 三角 > {TRI_MAX:,}'
               '（官方 glb_audit 不按实例计；该判据口径待 LY-100/制作人定）')
    if max(prims, prims_drawn) > HIGH_DRAWCALLS:
        R.warn('HIGH_DRAWCALLS', f'{prims} 个图元定义 / {prims_drawn} 个绘制图元（> {HIGH_DRAWCALLS}）')
    if degen:
        (R.err if profile == 'ly-p01' else R.warn)('GEOM_DEGENERATE', f'{degen} 个退化三角')
    if nonorm:
        R.warn('GEOM_NO_NORMAL', f'{nonorm} 个图元没有 NORMAL')
    if tri == 0 and geometry_read:
        R.err('GEOM_EMPTY', '没有任何三角形')
    # ---- 二进制块里的私密路径（贴图元数据、残留字符串） ----
    bh = scan_private_bytes(binb, BIN_STRICT + [p for p in pats if p[0].startswith('username:')])
    if bh:
        R.err('PRIVATE_PATH_IN_BIN', f'BIN 块里有 {len(bh)} 处像私密路径的字符串', hits=bh[:10])
    if profile == 'ly-p01':
        ly_p01_checks(g, R, lod, tex_sha, image_report, ly_attr_bad, flat_min, uvbox_min, lo, tex_manifest)
    return R


def uv_world_box_ratio(P, fnu, UV, tie=1e-4):
    """LY-007 texture-uv-rules：世界盒式投影 1 UV = 1 m；与 ly_style.inspect_glb 同一判据（Blender 坐标，v_b = 1 - v）。
    并列面（主轴分量差 < 1e-4）不计入。返回吻合率。"""
    xb, yb, zb = P[..., 0], -P[..., 2], P[..., 1]
    nb = np.stack([fnu[:, 0], -fnu[:, 2], fnu[:, 1]], 1)
    ax = np.abs(nb)
    au, av = UV[..., 0], 1.0 - UV[..., 1]
    cand = {2: (xb, yb), 1: (xb, zb), 0: (yb, zb)}
    ch = np.where((ax[:, 2] >= ax[:, 0]) & (ax[:, 2] >= ax[:, 1]), 2, np.where(ax[:, 1] > ax[:, 0], 1, 0))
    match = {d: ((np.abs(au - pu) < 2e-3) & (np.abs(av - pv) < 2e-3)).all(1) for d, (pu, pv) in cand.items()}
    ok = np.select([ch == 2, ch == 1, ch == 0], [match[2], match[1], match[0]])
    mx = ax.max(1)
    ntie = (ax >= mx[:, None] - tie).sum(1) >= 2
    return float(ok[~ntie].mean()) if (~ntie).any() else 1.0


def ly_p01_checks(g, R, lod, tex_sha, image_report, attr_bad, flat_min, uvbox_min, lo, tex_manifest):
    """LY-007 冻结基线：材质名、PBR/FLAT 与档位、禁用项、贴图分辨率与她的贴图字节、节点 TRS、属性、UV、法线、落地。"""
    mats = g.get('materials', [])
    R.info['lyProfile'] = {'lod': lod, 'flatNormals': round(flat_min, 4), 'uvWorldBox': round(uvbox_min, 4)}
    for m in mats:
        nm = m.get('name') or ''
        if not LY_MAT_RE.fullmatch(nm):
            R.err('LY_MATERIAL_NAME', f'材质名 {nm!r} 不是 LY_P01_<earth|timber|tile|path|paper__stone>__<PBR|FLAT>')
        if lod is not None:
            want = 'FLAT' if lod >= 2 else 'PBR'
            if not nm.endswith('__' + want):
                R.err('LY_LOD_MATERIAL_TIER', f'LOD{lod} 应为 __{want}：{nm}')
        if not m.get('doubleSided'):
            R.err('LY_NOT_DOUBLESIDED', f'{nm} 不是 doubleSided')
        pb = m.get('pbrMetallicRoughness') or {}
        if nm.endswith('__PBR') and ('metallicFactor' in pb or 'roughnessFactor' in pb):
            R.err('LY_PBR_FACTORS', f'{nm} 写了 metallic/roughness 因子（她的 PBR 不写）')
        for k in ('occlusionTexture', 'emissiveTexture', 'emissiveFactor', 'alphaMode'):
            if k in m:
                R.err('LY_FORBIDDEN_MATERIAL_KEY', f'{nm} 用了禁用项 {k}')
        if m.get('extensions'):
            R.err('LY_FORBIDDEN_MATERIAL_KEY', f'{nm} 带材质扩展 {list(m["extensions"])}')
    if g.get('extensionsUsed'):
        R.err('LY_EXTENSIONS', f'LY_P01 新件不用扩展：{g.get("extensionsUsed")}')
    man = tex_manifest or {}
    for rec in image_report:
        if rec.get('name') and not LY_IMAGE_NAME_RE.fullmatch(rec['name']):
            R.err('LY_IMAGE_NAME', f'贴图名 {rec["name"]!r} 不是 <earth|wood|tile|stone>-<basecolor|normal|orm>')
        if man and rec.get('sha256'):
            ent = man.get(rec['sha256'])
            if not ent:
                R.err('LY_TEXTURE_NOT_HERS', f'贴图 {rec.get("name")} 字节不在 LY-007 textures/manifest.json（不是她的原字节）')
            elif 'legacy_grey' in ent.get('file', ''):
                R.err('LY_TEXTURE_LEGACY_GREY', f'贴图 {rec.get("name")} 是旧灰调色板（新模型禁用）')
        if lod is not None and lod < 2 and rec.get('w') and (rec.get('w'), rec.get('h')) != (LY_TEX_RES[lod],) * 2:
            R.err('LY_TEXTURE_RES', f'LOD{lod} 贴图应为 {LY_TEX_RES[lod]}²：{rec.get("name")} {rec.get("w")}×{rec.get("h")}')
    if lod is not None and lod >= 2 and image_report:
        R.err('LY_LOD2_HAS_TEXTURE', f'LOD2 不应带贴图（有 {len(image_report)} 张）')
    for n in g.get('nodes', []):
        nm = n.get('name') or ''
        if not nm:
            R.err('LY_UNNAMED_NODE', '有未命名节点')
        if re.search(r'\.\d{3}$', nm):
            R.err('LY_BLENDER_SUFFIX', f'节点名带 Blender 副本后缀 {nm}')
        movable = 'hinge_axis_native' in (n.get('extras') or {})
        if not movable and any(k in n for k in ('translation', 'rotation', 'scale', 'matrix')):
            R.err('LY_STATIC_NODE_TRS', f'静态节点 {nm} 带变换（只有 leaf_* 动件可带铰点变换）')
    for m in g.get('meshes', []):
        if re.search(r'\.\d{3}$', m.get('name', '')):
            R.err('LY_BLENDER_SUFFIX', f'网格名带 Blender 副本后缀 {m.get("name")}')
    for tag, at in attr_bad:
        R.err('LY_ATTRIBUTES', f'{tag} 顶点属性 {at}，应只有 POSITION/NORMAL/TEXCOORD_0')
    if flat_min < 0.999:
        R.err('LY_NORMALS_NOT_FLAT', f'平直法线吻合率 {flat_min:.4f} < 0.999')
    if uvbox_min < 0.999:
        R.err('LY_UV_NOT_WORLD_BOX', f'世界盒式 UV 吻合率 {uvbox_min:.4f} < 0.999')
    if np.isfinite(lo).all() and abs(lo[1]) > LY_GROUND_TOL:
        R.warn('LY_NOT_GROUNDED', f'最低点 y={lo[1]:.4f}，未落在 y=0（地面补丁可另出文件）')


# ===================================================================== 三档关系
def geometry_hash(path):
    """按 (材质名, 世界坐标顶点按三角排序) 算几何哈希，与文件字节无关。"""
    raw = open(path, 'rb').read()
    R = Report(path)
    g, binb = parse_container(raw, R)
    if g is None:
        return None
    h = hashlib.sha256()
    parts = []
    nodes, meshes, mats = g.get('nodes', []), g.get('meshes', []), g.get('materials', [])
    for ni, n in enumerate(nodes):
        if 'mesh' not in n:
            continue
        for p in meshes[n['mesh']]['primitives']:
            pos = read_accessor(g, binb, p['attributes']['POSITION'], R, 'pos')
            idx = read_accessor(g, binb, p['indices'], R, 'idx').reshape(-1) if 'indices' in p else np.arange(len(pos))
            T = np.round(pos[idx.reshape(-1, 3)], 5).reshape(-1, 9)
            T = T[np.lexsort(T.T[::-1])]
            mname = mats[p['material']].get('name', '') if 'material' in p else ''
            parts.append((re.sub(r'__(PBR|FLAT)$', '', mname), T.tobytes()))
    for mname, b in sorted(parts):
        h.update(mname.encode()); h.update(b)
    return h.hexdigest()


def check_lodset(paths, family='default', pats=None):
    R = Report(' | '.join(p.replace('\\', '/') for p in paths))
    reps = [check_glb(p, profile='base', pats=pats) for p in paths]
    raws = [open(p, 'rb').read() for p in paths]
    R.info['files'] = [{'path': p.replace('\\', '/'), 'sha256': r.info.get('sha256'), 'triangles': r.info.get('triangles'),
                        'bboxMin': r.info.get('bboxMin'), 'bboxMax': r.info.get('bboxMax'),
                        'images': [(x.get('w'), x.get('h')) for x in r.info.get('images', [])],
                        'materials': r.info.get('materials')} for p, r in zip(paths, reps)]
    for i, r in enumerate(reps):
        if r.errors:
            R.err('LOD_FILE_INVALID', f'LOD{i} 自身有错误：{r.as_dict()["errorCodes"]}')
    if any(r.errors for r in reps):
        return R
    ghs = [geometry_hash(p) for p in paths]
    R.info['geometryHash'] = ghs
    for i in range(1, len(paths)):
        if raws[i] == raws[0]:
            R.err('LOD_COPY_OF_LOD0', f'LOD{i} 与 LOD0 字节相同（LOD0 复制改名）')
            continue
        same_geo = ghs[i] == ghs[0]
        same_tex = R.info['files'][i]['images'] == R.info['files'][0]['images']
        same_mat = R.info['files'][i]['materials'] == R.info['files'][0]['materials']
        if same_geo and same_tex and same_mat:
            R.err('LOD_COPY_OF_LOD0', f'LOD{i} 几何哈希、贴图分辨率、材质名都与 LOD0 相同（LOD0 复制改名）')
        elif same_geo:
            R.err('LOD_SAME_GEOMETRY', f'LOD{i} 几何与 LOD0 完全相同（只换了材质/贴图），不是降档')
    t0 = reps[0].info['triangles'] or 1
    ratios = {}
    for i in (1, 2):
        if i < len(reps):
            rt = reps[i].info['triangles'] / t0
            ratios[f'LOD{i}/LOD0'] = round(rt, 4)
            lo_, hi_ = LY_LOD_TRI_RATIO[i]
            if not (lo_ <= rt <= hi_):
                R.warn('LOD_TRI_RATIO', f'LOD{i}/LOD0 三角比 {rt:.3f} 不在 [{lo_}, {hi_}]（LY-007 lod-rules，超出时先查夯土）')
            if reps[i].info['triangles'] >= reps[i - 1].info['triangles']:
                R.err('LOD_NOT_DECREASING', f'LOD{i} 三角数 {reps[i].info["triangles"]} ≥ LOD{i - 1} {reps[i - 1].info["triangles"]}')
    R.info['triRatio'] = ratios
    b0n, b0x = np.array(reps[0].info['bboxMin']), np.array(reps[0].info['bboxMax'])
    for i in range(1, len(reps)):
        bn, bx = np.array(reps[i].info['bboxMin']), np.array(reps[i].info['bboxMax'])
        d = np.r_[bn - b0n, bx - b0x]
        R.info[f'bboxDeltaLOD{i}'] = [round(float(x), 5) for x in d]
        if i == 1:
            if np.abs(d).max() > LY_LOD_BBOX['LOD1']:
                R.err('LOD_BBOX', f'LOD1 包围盒与 LOD0 不同（最大差 {np.abs(d).max():.4f} m，应逐值相同）')
        else:
            other = np.abs(np.delete(d, 4)).max()
            top = d[4]
            if family == 'house':
                if other > LY_LOD_BBOX['LOD2'] or top > LY_LOD_BBOX['LOD2'] or top < -LY_LOD_BBOX['LOD2_house_top_drop'] - 1e-4:
                    R.err('LOD_BBOX', f'house 族 LOD2：顶部差 {top:.4f}（允许 −0.10…+0.02），其余最大差 {other:.4f}（≤0.02）')
            elif max(other, abs(top)) > LY_LOD_BBOX['LOD2']:
                R.err('LOD_BBOX', f'LOD2 包围盒最大差 {max(other, abs(top)):.4f} m > 0.02（house 族才允许顶部降 ≤0.10）')
    R.info['family'] = family
    return R


# ===================================================================== 席位交付包
TEXT_EXT = {'.md', '.json', '.txt', '.py', '.mjs', '.js', '.csv', '.html', '.yml', '.yaml', '.toml', '.cfg', '.ini', '.sh', '.ps1'}


def check_package(seat_dir, manifest='delivery-manifest.json', pats=None, glb_profile='base', tex_manifest=None, deep_glb=True):
    seat_dir = os.path.abspath(seat_dir)
    R = Report(os.path.basename(seat_dir))
    pats = pats if pats is not None else private_patterns()
    mp = os.path.join(seat_dir, manifest)
    try:
        man = json.load(open(mp, encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        R.err('MANIFEST_UNREADABLE', f'{manifest} 读不出来：{e}')
        return R
    entries = None
    for key in ('files', 'whitelist'):
        if isinstance(man.get(key), list) and man[key] and isinstance(man[key][0], dict):
            entries = man[key]; R.info['manifestKey'] = key
            break
    if entries is None:
        R.err('MANIFEST_NO_FILES', '清单里没有 files/whitelist 列表')
        return R
    pkg_public = man.get('public')
    R.info['entries'] = len(entries)
    seen, glbs = set(), []
    total = 0
    for e in entries:
        p = e.get('path')
        why = bad_relpath(p)
        if why:
            R.err('PATH_ESCAPE', f'清单路径越界（{why}）：{p}')
            continue
        full = os.path.normpath(os.path.join(seat_dir, p))
        if os.path.commonpath([full, seat_dir]) != seat_dir:
            R.err('PATH_ESCAPE', f'清单路径跑出席位目录：{p}')
            continue
        if p in seen:
            R.err('MANIFEST_DUPLICATE', f'清单重复：{p}')
        seen.add(p)
        if os.path.isdir(full):
            R.warn('MANIFEST_DIR_ENTRY', f'清单条目是目录，未逐文件核对：{p}')
            continue
        if not os.path.isfile(full):
            R.err('MANIFEST_FILE_MISSING', f'清单文件不存在：{p}')
            continue
        real = os.path.realpath(full)
        if os.path.commonpath([real, os.path.realpath(seat_dir)]) != os.path.realpath(seat_dir):
            R.err('PATH_ESCAPE', f'清单文件经链接跑出席位目录：{p}')
            continue
        size = os.path.getsize(full)
        total += size
        if p in ('delivery-manifest.json', 'status.json') or os.path.normpath(full) == os.path.normpath(mp):
            continue  # 自引用：清单不能含自身 SHA
        if 'bytes' in e and e['bytes'] != size:
            R.err('MANIFEST_SIZE_MISMATCH', f'{p}：清单 {e["bytes"]} 字节，实际 {size}')
        if 'sha256' in e:
            s = sha256_file(full)
            if e['sha256'] != s:
                R.err('MANIFEST_SHA_MISMATCH', f'{p}：清单 SHA {e["sha256"][:12]}…，实际 {s[:12]}…')
        else:
            R.warn('MANIFEST_NO_SHA', f'{p} 没有 sha256')
        public = e.get('public', pkg_public if pkg_public is not None else None)
        ext = os.path.splitext(p)[1].lower()
        if ext in TEXT_EXT and size < 20_000_000:
            txt = open(full, 'rb').read().decode('utf-8', 'replace')
            hits = scan_private(txt, pats, limit=5)
            if hits:
                if public is True and any(h['strong'] for h in hits):
                    R.err('PRIVATE_PATH_PUBLIC_FILE', f'公共文件 {p} 含私密路径', hits=hits)
                elif public is True:
                    R.warn('PRIVATE_PATH_WEAK', f'公共文件 {p} 含 /home/、/Users/ 式通用路径（弱判据，需人工看）', hits=hits)
                else:
                    R.warn('PRIVATE_PATH_INTERNAL_FILE', f'内部文件 {p} 含私密路径（不得进公共 docs）', hits=hits[:3])
        if ext == '.glb':
            glbs.append((p, bool(e.get('expectFail')), e.get('fixture') or {}))
    R.info['totalBytes'] = total
    R.info['glbs'] = []
    if deep_glb:
        for p, expect_fail, fx in glbs:
            # 负例夹具（清单 expectFail: true）：按清单 fixture 写明的方式检查，必须判出 fixture.expectCodes；判不出说明夹具失效。
            # fixture = {cmd: glb|lodset, profile, lod, privateTokens, expectCodes}；lodset 夹具要三个文件一起判，这里只登记不单查。
            if expect_fail and fx.get('cmd', 'glb') != 'glb':
                R.note('FIXTURE_NOT_SINGLE_GLB', f'{p} 是 {fx.get("cmd")} 夹具，单文件不判（见 qa/selftest.json）')
                R.info['glbs'].append({'path': p, 'expectFail': True, 'fixture': fx, 'checked': False})
                continue
            prof = fx.get('profile', glb_profile) if expect_fail else glb_profile
            fpats = private_patterns(fx.get('privateTokens', [])) if fx.get('privateTokens') else pats
            r = check_glb(os.path.join(seat_dir, p), profile=prof, lod=fx.get('lod') if expect_fail else None, pats=fpats,
                          tex_manifest=tex_manifest, display_path=p)
            got = r.as_dict()['errorCodes']
            R.info['glbs'].append({'path': p, 'sha256': r.info.get('sha256'), 'bytes': r.info.get('bytes'), 'expectFail': expect_fail,
                                   'fixture': fx or None, 'errorCodes': got, 'warningCodes': r.as_dict()['warningCodes']})
            if expect_fail:
                want = set(fx.get('expectCodes') or [])
                if not r.errors:
                    R.err('FIXTURE_UNEXPECTEDLY_PASSES', f'{p} 登记为负例夹具，却没有任何错误')
                elif not want <= set(got):
                    R.err('FIXTURE_WRONG_CODES', f'{p} 应判出 {sorted(want)}，实际 {got}')
            elif r.errors:
                R.err('PACKAGE_GLB_INVALID', f'{p}：{got}')
    R.info['negativeFixtures'] = sum(1 for _, x, _f in glbs if x)
    return R


# ===================================================================== 公共目录的路径隐私
SOURCE_EXT = re.compile(r'\.(blend|blend1|zip|part\d{3}|psd|exr|fbx|max|ma|mb|c4d|spp|kra)$', re.I)  # 与官方 build_assets.SOURCE 同


def check_tree(root, pats=None, archived=()):
    """把一个将要公开的目录（如 docs/）当公共内容扫：文本文件私密路径 = 错误；源工程扩展名 = 错误（官方 source-archive 登记的除外）；
    符号链接跑出目录 = 错误。GLB 内部的私密路径由 glb 子命令查（这里不重复解析）。"""
    root = os.path.abspath(root)
    R = Report(os.path.basename(root))
    pats = pats if pats is not None else private_patterns()
    n_txt = n_all = 0
    for dp, dn, fn in os.walk(root):
        for f in fn:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root).replace('\\', '/')
            n_all += 1
            real = os.path.realpath(full)
            if os.path.commonpath([real, os.path.realpath(root)]) != os.path.realpath(root):
                R.err('PATH_ESCAPE', f'{rel} 经链接指向目录外')
                continue
            if SOURCE_EXT.search(f) and rel not in archived:
                R.err('SOURCE_FILE_IN_PUBLIC', f'{rel}：源工程文件不进公共目录')
            if os.path.splitext(f)[1].lower() in TEXT_EXT and os.path.getsize(full) < 50_000_000:
                n_txt += 1
                hits = scan_private(open(full, 'rb').read().decode('utf-8', 'replace'), pats, limit=5)
                if any(h['strong'] for h in hits):
                    R.err('PRIVATE_PATH_PUBLIC_FILE', f'公共文件 {rel} 含私密路径', hits=hits)
                elif hits:
                    R.warn('PRIVATE_PATH_WEAK', f'公共文件 {rel} 含 /home/、/Users/ 式通用路径（弱判据，需人工看）', hits=hits)
    R.info.update(files=n_all, textFiles=n_txt)
    return R


# ===================================================================== 官方 checker（只在导出副本里）
def run_official(copy_dir, python=sys.executable, extra_env=None, timeout=3600):
    copy_dir = os.path.abspath(copy_dir)
    R = Report(copy_dir.replace('\\', '/'))
    if os.path.exists(os.path.join(copy_dir, '.git')):
        R.err('OFFICIAL_REFUSED_REAL_REPO', '目标目录含 .git：拒绝在原仓库里运行 build_assets.py（它会改写 lab/data）')
        return R
    tool = os.path.join(copy_dir, 'lab', 'tools', 'build_assets.py')
    spec = os.path.join(copy_dir, 'docs', 'asset-spec', 'categories.json')
    if not os.path.isfile(tool) or not os.path.isfile(spec):
        R.err('OFFICIAL_NOT_FOUND', '副本里没有 lab/tools/build_assets.py 或 docs/asset-spec/categories.json')
        return R
    sp = json.load(open(spec, encoding='utf-8'))
    R.info['spec'] = {'spec': sp.get('spec'), 'limits': sp.get('limits'),
                      'categories.json.sha256': sha256_file(spec),
                      'README.md.sha256': sha256_file(os.path.join(copy_dir, 'docs', 'asset-spec', 'README.md'))
                      if os.path.isfile(os.path.join(copy_dir, 'docs', 'asset-spec', 'README.md')) else None,
                      'build_assets.py.sha256': sha256_file(tool),
                      'glb_audit.py.sha256': sha256_file(os.path.join(copy_dir, 'lab', 'tools', 'glb_audit.py'))}
    cmd = [python, '-I', 'lab/tools/build_assets.py', '--check']
    env = dict(os.environ)
    # 副本没有 .git；挡住 git 向上找到外层仓库（updated 字段退回文件时间，不影响 --check 判定）
    env['GIT_CEILING_DIRECTORIES'] = os.path.dirname(copy_dir)
    env['PYTHONIOENCODING'] = 'utf-8'
    env.update(extra_env or {})
    import time
    t = time.time()
    pr = subprocess.run(cmd, cwd=copy_dir, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, timeout=timeout)
    R.info['command'] = ' '.join(['python', '-I', 'lab/tools/build_assets.py', '--check']) + f'   (cwd = 导出副本 {os.path.basename(copy_dir)})'
    R.info['exitCode'] = pr.returncode
    R.info['seconds'] = round(time.time() - t, 1)
    R.info['stdoutTail'] = pr.stdout.splitlines()[-40:]
    R.info['stderrTail'] = pr.stderr.splitlines()[-20:]
    rp = os.path.join(copy_dir, 'lab', 'data', 'report.json')
    if os.path.isfile(rp):
        rep = json.load(open(rp, encoding='utf-8'))
        R.info['reportCounts'] = rep.get('counts')
        R.info['repoErrors'] = rep.get('repoErrors')
        R.info['cardErrors'] = [{'card': it['card'], 'errors': it['errors']} for it in rep.get('items', []) if it.get('errors')]
        R.info['orphans'] = len(rep.get('orphans') or [])
    if pr.returncode != 0:
        R.err('OFFICIAL_CHECK_FAILED', f'官方 build_assets.py --check 退出码 {pr.returncode}')
    return R


# ===================================================================== CLI
def load_tex_manifest(p):
    if not p:
        return None
    d = json.load(open(p, encoding='utf-8'))
    return {m['sha256']: m for m in d}


def _print(R):
    d = R.as_dict()
    flag = 'OK  ' if d['ok'] else 'FAIL'
    print(f'{flag} {d["subject"]}  errors={d["errorCodes"]}  warnings={d["warningCodes"]}')
    for i in R.issues:
        if i['level'] != 'info':
            print(f'      {i["level"]:7s} {i["code"]}: {i["msg"][:200]}')


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--json', help='完整报告写到这个文件')
    ap.add_argument('--private-token', action='append', default=[], help='额外的私密词（用户名等），可重复')
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('glb'); a.add_argument('files', nargs='+'); a.add_argument('--profile', default='base', choices=['base', 'ly-p01'])
    a.add_argument('--lod', type=int); a.add_argument('--upload-limit', type=int); a.add_argument('--upload-encoding', default='base64', choices=['raw', 'base64'])
    a.add_argument('--tex-manifest', help='LY-007 textures/manifest.json（ly-p01 档核她的贴图字节）')
    b = sub.add_parser('lodset'); b.add_argument('files', nargs=3); b.add_argument('--family', default='default', choices=['default', 'house'])
    c = sub.add_parser('package'); c.add_argument('seat_dir'); c.add_argument('--manifest', default='delivery-manifest.json')
    c.add_argument('--glb-profile', default='base', choices=['base', 'ly-p01']); c.add_argument('--tex-manifest')
    d = sub.add_parser('official'); d.add_argument('copy_dir')
    e = sub.add_parser('privacy'); e.add_argument('public_dir'); e.add_argument('--archived', help='source-archive.json（官方登记的源文件清单）')
    args = ap.parse_args(argv)
    pats = private_patterns(args.private_token)
    reports = []
    if args.cmd == 'glb':
        tm = load_tex_manifest(args.tex_manifest)
        for f in args.files:
            lod = args.lod
            if lod is None:
                m = re.search(r'LOD(\d)', os.path.basename(f))
                lod = int(m.group(1)) if m and args.profile == 'ly-p01' else None
            reports.append(check_glb(f, args.profile, lod, args.upload_limit, args.upload_encoding, pats, tm))
    elif args.cmd == 'lodset':
        reports.append(check_lodset(args.files, args.family, pats))
    elif args.cmd == 'package':
        reports.append(check_package(args.seat_dir, args.manifest, pats, args.glb_profile, load_tex_manifest(args.tex_manifest)))
    elif args.cmd == 'official':
        reports.append(run_official(args.copy_dir))
    elif args.cmd == 'privacy':
        arch = set(json.load(open(args.archived, encoding='utf-8')).get('files', [])) if args.archived else set()
        reports.append(check_tree(args.public_dir, pats, arch))
    for r in reports:
        _print(r)
    out = {'checker': CHECKER_VERSION, 'checkerSha256': sha256_file(os.path.abspath(__file__)), 'command': args.cmd,
           'reports': [r.as_dict() for r in reports]}
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        json.dump(out, open(args.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return 1 if any(r.errors for r in reports) else 0


if __name__ == '__main__':
    sys.exit(main())
