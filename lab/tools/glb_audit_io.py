"""Bounded GLB input and EXT_meshopt_compression decoding for glb_audit.

Not a complete glTF conformance validator. Unsupported required extensions and
sparse accessors fail closed. No external/data URIs, fallback substitution,
network, optional decoder install, or rewritten GLB is involved.
"""
from decimal import Decimal, DecimalException
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess

EXT = 'EXT_meshopt_compression'
SUPPORTED_REQUIRED = {EXT}
MAX_FILE = 64 * 1024 * 1024
MAX_JSON = 8 * 1024 * 1024
MAX_DECODED = 128 * 1024 * 1024
MAX_ACCESSOR_VALUES = 16_000_000
MAX_ITEMS = 100_000
MAX_NODES = 10_000
MAX_DEPTH = 128
CT = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
HERE = Path(__file__).resolve().parent
DECODER = HERE.parent.parent / 'docs/vendor/meshopt_decoder.module.js'
BRIDGE = HERE / 'glb_meshopt_decode.mjs'
# Change the schema on any semantic/cache contract change. Source hashes also
# invalidate cached summaries when any auditor/bridge/decoder code changes.
AUDIT_SCHEMA = 'glb-audit-meshopt-1'


class AuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def integer(value, label, minimum=0, maximum=MAX_DECODED):
    require(type(value) is int and minimum <= value <= maximum, label)
    return value


def ref(value, seq, label):
    return integer(value, label, 0, len(seq) - 1)


def vector(value, length, label):
    require(isinstance(value, list) and len(value) == length and
            all(type(v) in (int, float) and math.isfinite(v) for v in value), label)
    return value


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_JSON_KEY:' + key)
        result[key] = value
    return result


def json_number(token):
    # glTF integers may use 3.0 or 3e0 notation. Normalize only exact integral
    # tokens, not underflowed nonzero values or rounded fractional numbers.
    value = float(token)
    try:
        if math.isfinite(value) and value.is_integer() and Decimal(token) == Decimal(int(value)):
            return int(value)
    except DecimalException as error:
        raise AuditError('INVALID_JSON_NUMBER') from error
    return value


def reject_constant(value):
    raise AuditError('NONFINITE_JSON:' + value)


def load_glb(raw):
    require(len(raw) >= 20, 'TRUNCATED_GLB_HEADER')
    magic, version, length = struct.unpack_from('<4sII', raw)
    require(magic == b'glTF', 'NOT_GLB_MAGIC')
    require(version == 2, 'UNSUPPORTED_GLB_VERSION')
    require(length == len(raw), 'LENGTH_MISMATCH')
    chunks = []; offset = 12
    while offset < len(raw):
        require(offset + 8 <= len(raw), 'TRUNCATED_CHUNK_HEADER')
        size, kind = struct.unpack_from('<II', raw, offset); offset += 8
        require(size % 4 == 0 and offset + size <= len(raw), 'INVALID_CHUNK_LENGTH')
        chunks.append((kind, memoryview(raw)[offset:offset + size])); offset += size
    require(len(chunks) in (1, 2) and chunks[0][0] == 0x4E4F534A and
            (len(chunks) == 1 or chunks[1][0] == 0x004E4942), 'UNSUPPORTED_CHUNK_LAYOUT')
    require(len(chunks[0][1]) <= MAX_JSON, 'JSON_LIMIT')
    g = json.loads(bytes(chunks[0][1]).decode('utf-8'), object_pairs_hook=no_duplicates,
                   parse_constant=reject_constant, parse_float=json_number)
    require(isinstance(g, dict) and g.get('asset', {}).get('version') == '2.0', 'INVALID_ASSET_VERSION')
    require(g.get('asset', {}).get('minVersion', '2.0') == '2.0', 'UNSUPPORTED_MIN_VERSION')
    return g, chunks[1][1] if len(chunks) == 2 else memoryview(b'')


def cache_identity():
    h = hashlib.sha256(AUDIT_SCHEMA.encode())
    for p in (HERE / 'glb_audit.py', Path(__file__), BRIDGE, DECODER):
        h.update(p.name.encode())
        h.update(p.read_bytes() if p.is_file() else b'MISSING')
    return h.hexdigest()


def decode_views(jobs, binary):
    require(DECODER.is_file() and BRIDGE.is_file(), 'MESHOPT_DECODER_MISSING')
    node = shutil.which('node')
    require(node is not None, 'MESHOPT_NODE_MISSING: install an approved Node.js runtime to audit compressed GLBs')
    header = json.dumps(jobs, separators=(',', ':')).encode()
    require(len(header) <= MAX_JSON, 'MESHOPT_JOB_LIMIT')
    data = struct.pack('<I', len(header)) + header + binary
    try:
        # NODE_OPTIONS can inject preload code. This child needs no environment
        # options; PATH is used only to resolve the already installed executable.
        env = {k: v for k, v in os.environ.items() if k not in ('NODE_OPTIONS', 'NODE_PATH')}
        run = subprocess.run([node, '--max-old-space-size=256', str(BRIDGE)], input=data,
                             capture_output=True, timeout=30, env=env, check=False)
    except subprocess.TimeoutExpired as e:
        raise AuditError('MESHOPT_TIMEOUT') from e
    except OSError as e:
        raise AuditError('MESHOPT_PROCESS_UNAVAILABLE') from e
    require(run.returncode == 0, 'MESHOPT_DECODE_FAILED:' + run.stderr[:1000].decode('utf-8', 'replace'))
    require(len(run.stdout) == sum(j['count'] * j['byteStride'] for j in jobs), 'MESHOPT_OUTPUT_LENGTH')
    result = {}; offset = 0
    for j in jobs:
        size = j['count'] * j['byteStride']
        result[j['view']] = memoryview(run.stdout)[offset:offset + size]; offset += size
    return result


class Accessors:
    def __init__(self, g, binary):
        self.g = g; self.acc = g.get('accessors', []); self.bvs = g.get('bufferViews', [])
        for field in ('accessors', 'bufferViews', 'buffers', 'meshes', 'nodes', 'scenes', 'images', 'materials'):
            seq = g.get(field, [])
            require(isinstance(seq, list) and len(seq) <= MAX_ITEMS and all(isinstance(x, dict) for x in seq), 'INVALID_LIST:' + field)
        used = g.get('extensionsUsed', []); required = g.get('extensionsRequired', [])
        for seq in (used, required):
            require(isinstance(seq, list) and all(isinstance(x, str) for x in seq) and len(set(seq)) == len(seq), 'INVALID_EXTENSION_LIST')
        require(set(required) <= set(used), 'REQUIRED_EXTENSION_NOT_USED')
        require(not (set(required) - SUPPORTED_REQUIRED), 'EXT_REQUIRED_UNSUPPORTED:' + ','.join(sorted(set(required) - SUPPORTED_REQUIRED)))
        buffers = g.get('buffers', [])
        require(len(buffers) <= 2, 'UNSUPPORTED_BUFFER_LAYOUT')
        self.views = {}; jobs = []; total = 0
        for i, buf in enumerate(buffers):
            extensions = buf.get('extensions', {})
            require(isinstance(extensions, dict), 'INVALID_BUFFER_EXTENSIONS')
            if EXT in extensions:
                require(isinstance(extensions[EXT], dict), 'INVALID_BUFFER_MESHOPT_EXTENSION')
                if 'fallback' in extensions[EXT]:
                    require(type(extensions[EXT]['fallback']) is bool, 'INVALID_FALLBACK_FLAG')
            require('uri' not in buf, 'EXTERNAL_BUFFER_UNSUPPORTED')
            size = integer(buf.get('byteLength'), 'INVALID_BUFFER_LENGTH')
            if i == 0:
                require(size <= len(binary) <= size + 3, 'BIN_BUFFER_LENGTH')
            else:
                # A URI-less placeholder is permitted when compression is required.
                # The buffer-level fallback marker is optional in EXT_meshopt.
                require(EXT in required, 'INVALID_VIRTUAL_FALLBACK')
        require(buffers or not binary, 'BIN_WITHOUT_BUFFER')
        for i, bv in enumerate(self.bvs):
            bi = ref(bv.get('buffer'), buffers, 'INVALID_VIEW_BUFFER')
            offset = integer(bv.get('byteOffset', 0), 'INVALID_VIEW_OFFSET')
            size = integer(bv.get('byteLength'), 'INVALID_VIEW_LENGTH', 1)
            require(offset + size <= buffers[bi]['byteLength'], 'VIEW_OUT_OF_BOUNDS')
            if 'byteStride' in bv:
                stride = integer(bv['byteStride'], 'INVALID_VIEW_STRIDE', 4, 252)
                require(stride % 4 == 0, 'INVALID_VIEW_STRIDE')
            require(bv.get('target', 34962) in (34962, 34963), 'INVALID_VIEW_TARGET')
            extensions = bv.get('extensions', {})
            require(isinstance(extensions, dict), 'INVALID_VIEW_EXTENSIONS')
            if EXT in extensions:
                require(isinstance(extensions[EXT], dict), 'INVALID_MESHOPT_EXTENSION')
            ext = extensions.get(EXT)
            if ext is None:
                require(bi == 0, 'UNBACKED_VIEW')
                require(not buffers[bi].get('extensions', {}).get(EXT, {}).get('fallback'), 'FALLBACK_RAW_REFERENCE')
                self.views[i] = binary[offset:offset + size]
                continue
            require(EXT in used and isinstance(ext, dict), 'INVALID_MESHOPT_EXTENSION')
            require(ref(ext.get('buffer'), buffers, 'INVALID_MESHOPT_BUFFER') == 0, 'UNBACKED_MESHOPT_SOURCE')
            require(not buffers[0].get('extensions', {}).get(EXT, {}).get('fallback'), 'FALLBACK_SOURCE_REFERENCE')
            src = integer(ext.get('byteOffset', 0), 'INVALID_MESHOPT_OFFSET')
            length = integer(ext.get('byteLength'), 'INVALID_MESHOPT_LENGTH', 1)
            require(src + length <= buffers[0]['byteLength'], 'MESHOPT_SOURCE_OUT_OF_BOUNDS')
            stride = integer(ext.get('byteStride'), 'INVALID_MESHOPT_STRIDE', 1, 256)
            count = integer(ext.get('count'), 'INVALID_MESHOPT_COUNT', 1)
            require(count * stride == size, 'MESHOPT_DECODED_LENGTH')
            require('byteStride' not in bv or bv['byteStride'] == stride, 'MESHOPT_PARENT_STRIDE_MISMATCH')
            mode = ext.get('mode'); filt = ext.get('filter', 'NONE')
            require(mode in ('ATTRIBUTES', 'TRIANGLES', 'INDICES'), 'MESHOPT_MODE_UNSUPPORTED')
            require(filt in ('NONE', 'OCTAHEDRAL', 'QUATERNION', 'EXPONENTIAL'), 'MESHOPT_FILTER_UNSUPPORTED')
            if mode == 'ATTRIBUTES':
                require(stride % 4 == 0, 'MESHOPT_ATTRIBUTE_STRIDE')
            else:
                require(stride in (2, 4) and filt == 'NONE', 'MESHOPT_INDEX_LAYOUT')
                require(mode != 'TRIANGLES' or count % 3 == 0, 'MESHOPT_TRIANGLE_COUNT')
            require(filt != 'OCTAHEDRAL' or stride in (4, 8), 'MESHOPT_OCTAHEDRAL_STRIDE')
            require(filt != 'QUATERNION' or stride == 8, 'MESHOPT_QUATERNION_STRIDE')
            require(filt != 'EXPONENTIAL' or stride % 4 == 0, 'MESHOPT_EXPONENTIAL_STRIDE')
            total += size
            require(total <= MAX_DECODED, 'MESHOPT_DECODED_LIMIT')
            jobs.append({'view': i, 'byteOffset': src, 'byteLength': length, 'byteStride': stride,
                         'count': count, 'mode': mode, 'filter': filt})
        for im in g.get('images', []):
            require('uri' not in im, 'EXTERNAL_IMAGE_UNSUPPORTED')
            ref(im.get('bufferView'), self.bvs, 'INVALID_IMAGE_VIEW')
            require(im.get('mimeType') in ('image/png', 'image/jpeg', 'image/webp', 'image/ktx2'), 'UNSUPPORTED_IMAGE_MIME')
        self.layouts = []; values = 0
        for a in self.acc:
            require('sparse' not in a, 'SPARSE_ACCESSOR_UNSUPPORTED')
            vi = ref(a.get('bufferView'), self.bvs, 'INVALID_ACCESSOR_VIEW')
            count = integer(a.get('count'), 'INVALID_ACCESSOR_COUNT', 1, 4_000_000)
            require(a.get('type') in NC and a.get('componentType') in CT, 'INVALID_ACCESSOR_TYPE')
            n = NC[a['type']]; fmt = CT[a['componentType']]; cs = struct.calcsize(fmt)
            offsets = list(range(0, cs * n, cs)); elem = cs * n
            if a['type'].startswith('MAT'):
                side = int(a['type'][-1]); column = (side * cs + 3) // 4 * 4
                offsets = [c * column + r * cs for c in range(side) for r in range(side)]; elem = side * column
            bv = self.bvs[vi]; stride = bv.get('byteStride', elem)
            start = integer(a.get('byteOffset', 0), 'INVALID_ACCESSOR_OFFSET')
            require(start % cs == 0 and (bv.get('byteOffset', 0) + start) % cs == 0 and
                    stride >= elem and stride % cs == 0, 'INVALID_ACCESSOR_ALIGNMENT')
            if a['type'].startswith('MAT'):
                require(start % 4 == 0 and (bv.get('byteOffset', 0) + start) % 4 == 0 and stride % 4 == 0,
                        'INVALID_MATRIX_ALIGNMENT')
            # The last matrix column need not carry trailing padding. Repeated
            # elements still advance by the full padded element stride.
            extent = offsets[-1] + cs
            require(start + (count - 1) * stride + extent <= bv['byteLength'], 'ACCESSOR_OUT_OF_BOUNDS')
            norm = a.get('normalized', False)
            require(type(norm) is bool and (not norm or a['componentType'] in (5120, 5121, 5122, 5123)), 'INVALID_NORMALIZATION')
            for k in ('min', 'max'):
                if k in a: vector(a[k], n, 'INVALID_ACCESSOR_' + k.upper())
            if 'min' in a and 'max' in a:
                require(all(x <= y for x, y in zip(a['min'], a['max'])), 'INVALID_MINMAX_ORDER')
            values += count * n
            require(values <= MAX_ACCESSOR_VALUES, 'ACCESSOR_VALUE_LIMIT')
            self.layouts.append((vi, count, start, stride, offsets, fmt, norm))
        # Validate layout and allocation bounds BEFORE asking the decoder to allocate.
        if jobs:
            self.views.update(decode_views(jobs, binary))
        self.decoded_views = len(jobs); self.decoded_bytes = total
        self._validate_graph()

    def read(self, ai, limit=None):
        ref(ai, self.acc, 'INVALID_ACCESSOR_INDEX')
        vi, count, start, stride, offsets, fmt, norm = self.layouts[ai]
        view = self.views[vi]; result = []
        for i in range(count if limit is None else min(count, limit)):
            row = tuple(struct.unpack_from('<' + fmt, view, start + i * stride + offset)[0] for offset in offsets)
            require(all(math.isfinite(v) for v in row), 'NONFINITE_ACCESSOR_DATA')
            if norm:
                divisor = {'b': 127, 'B': 255, 'h': 32767, 'H': 65535}[fmt]
                row = tuple(max(v / divisor, -1) if fmt in ('b', 'h') else v / divisor for v in row)
            result.append(row)
        return result

    def _validate_graph(self):
        g = self.g; nodes = g.get('nodes', []); meshes = g.get('meshes', [])
        require(len(nodes) <= MAX_NODES, 'NODE_LIMIT')
        parents = [0] * len(nodes)
        for n in nodes:
            require(not ('matrix' in n and any(k in n for k in ('translation', 'rotation', 'scale'))), 'MATRIX_AND_TRS')
            for key, size in (('matrix', 16), ('translation', 3), ('rotation', 4), ('scale', 3)):
                if key in n: vector(n[key], size, 'INVALID_NODE_' + key.upper())
            if 'mesh' in n: ref(n['mesh'], meshes, 'INVALID_NODE_MESH')
            for child in n.get('children', []):
                ref(child, nodes, 'INVALID_CHILD_NODE'); parents[child] += 1
                require(parents[child] <= 1, 'MULTIPLE_NODE_PARENTS')
        require(sum(len(meshes[n['mesh']].get('primitives', [])) for n in nodes if 'mesh' in n) <= 100_000, 'SCENE_WORK_LIMIT')
        states = [0] * len(nodes); heights = [0] * len(nodes)
        def visit(i, depth):
            require(depth <= MAX_DEPTH, 'NODE_DEPTH_LIMIT')
            require(states[i] != 1, 'NODE_CYCLE')
            if states[i] == 2:
                require(depth + heights[i] <= MAX_DEPTH, 'NODE_DEPTH_LIMIT')
                return heights[i]
            states[i] = 1
            heights[i] = max((1 + visit(child, depth + 1) for child in nodes[i].get('children', [])), default=0)
            require(depth + heights[i] <= MAX_DEPTH, 'NODE_DEPTH_LIMIT')
            states[i] = 2
            return heights[i]
        for i in range(len(nodes)): visit(i, 0)
        for scene in g.get('scenes', []):
            roots = scene.get('nodes', [])
            require(len(set(roots)) == len(roots), 'DUPLICATE_SCENE_ROOT')
            for i in roots:
                ref(i, nodes, 'INVALID_SCENE_NODE')
                require(parents[i] == 0, 'SCENE_NODE_NOT_ROOT')
        if 'scene' in g: ref(g['scene'], g.get('scenes', []), 'INVALID_SCENE_INDEX')
        primitive_count = 0; geometry_work = 0
        for mesh in meshes:
            for p in mesh.get('primitives', []):
                primitive_count += 1; require(primitive_count <= 10_000, 'PRIMITIVE_LIMIT')
                integer(p.get('mode', 4), 'INVALID_PRIMITIVE_MODE', 0, 6)
                require('KHR_draco_mesh_compression' not in p.get('extensions', {}), 'DRACO_UNSUPPORTED')
                attrs = p.get('attributes', {})
                pi = ref(attrs.get('POSITION'), self.acc, 'INVALID_POSITION_ACCESSOR'); pa = self.acc[pi]
                require(pa['type'] == 'VEC3' and pa['componentType'] == 5126, 'UNSUPPORTED_POSITION_FORMAT')
                geometry_work += pa['count'] * 3
                if 'indices' in p:
                    ref(p['indices'], self.acc, 'INVALID_INDEX_ACCESSOR')
                    geometry_work += self.acc[p['indices']]['count']
                require(geometry_work <= MAX_ACCESSOR_VALUES, 'GEOMETRY_WORK_LIMIT')
                for ai in attrs.values():
                    ref(ai, self.acc, 'INVALID_ATTRIBUTE_ACCESSOR')
                    require(self.acc[ai]['count'] == pa['count'], 'ATTRIBUTE_COUNT_MISMATCH')
                if 'material' in p: ref(p['material'], g.get('materials', []), 'INVALID_MATERIAL')
                if 'indices' in p:
                    ai = ref(p['indices'], self.acc, 'INVALID_INDEX_ACCESSOR'); a = self.acc[ai]
                    require(a['type'] == 'SCALAR' and a['componentType'] in (5121, 5123, 5125) and not a.get('normalized'), 'INVALID_INDEX_FORMAT')
                    require('byteStride' not in self.bvs[a['bufferView']], 'STRIDED_INDICES_UNSUPPORTED')
                    require(p.get('mode', 4) != 4 or a['count'] % 3 == 0, 'TRIANGLE_INDEX_COUNT')
                    for row in self.read(ai): require(row[0] < pa['count'], 'INDEX_OUT_OF_RANGE')
                elif p.get('mode', 4) == 4:
                    require(pa['count'] % 3 == 0, 'TRIANGLE_VERTEX_COUNT')
                # Check actual positions, not only metadata. Other attributes are
                # range-checked above; this is not a material/image/animation validator.
                positions = self.read(pi)
                if 'min' in pa and 'max' in pa:
                    low, high = pa['min'], pa['max']
                    for row in positions:
                        require(all(low[k] - 1e-5 * max(1, abs(low[k])) <= row[k] <= high[k] + 1e-5 * max(1, abs(high[k])) for k in range(3)), 'POSITION_OUTSIDE_MINMAX')
