"""Build texture-free GLB projections while preserving all geometry bytes.

Input is a JSON array, or {"jobs": [...]}, on stdin or in --jobs FILE. Each job
contains id, repository-relative sourcePath, and expectedSha256. A previously
generated source.json can also be passed to --jobs for regeneration. --dry-run
performs the same transformation and validation without writing files.
"""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import base64
import json
import math
import re
import struct
import sys

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/cities/luoyang/progress-assets/flat'
RECIPE = 'texture-free-geometry-preserving-v1'
COMPRESSED_EXTENSIONS = {'KHR_draco_mesh_compression', 'EXT_meshopt_compression'}
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942
SRGB_TO_LINEAR = [
    value / 255 / 12.92 if value <= 10 else ((value / 255 + 0.055) / 1.055) ** 2.4
    for value in range(256)
]


def checked_path(path):
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT) or not resolved.is_file():
        raise ValueError(f'Missing or out-of-repository input: {path}')
    return resolved


def digest_record(path, content):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(content),
            'sha256': sha256(content).hexdigest()}


def parse_glb(content):
    if len(content) < 20:
        raise ValueError('Truncated GLB header')
    magic, version, length = struct.unpack_from('<4sII', content)
    if magic != b'glTF' or version != 2 or length != len(content):
        raise ValueError('Invalid glTF 2.0 binary header or length')
    chunks = {}
    offset = 12
    while offset < length:
        if offset + 8 > length:
            raise ValueError('Truncated GLB chunk header')
        size, kind = struct.unpack_from('<II', content, offset)
        offset += 8
        if size % 4 or offset + size > length or kind in chunks:
            raise ValueError('Invalid GLB chunk length or duplicate chunk')
        if kind not in (JSON_CHUNK, BIN_CHUNK) or (not chunks and kind != JSON_CHUNK):
            raise ValueError('Unsupported GLB chunk order or type')
        chunks[kind] = content[offset:offset + size]
        offset += size
    if JSON_CHUNK not in chunks:
        raise ValueError('GLB JSON chunk is missing')
    return json.loads(chunks[JSON_CHUNK].decode('utf-8')), chunks.get(BIN_CHUNK)


def walk_extensions(value):
    if isinstance(value, dict):
        yield from value.get('extensions', {})
        for key, child in value.items():
            if key != 'extras':
                yield from walk_extensions(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_extensions(child)


def read_uri(uri, source, dependencies):
    if uri.startswith('data:'):
        header, encoded = uri.split(',', 1)
        if not header.endswith(';base64'):
            raise ValueError('Only base64 data URIs are supported')
        return base64.b64decode(encoded, validate=True)
    parsed = urlsplit(uri)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or '\\' in uri:
        raise ValueError(f'Unsupported external URI: {uri}')
    relative = Path(unquote(parsed.path))
    if relative.is_absolute():
        raise ValueError(f'Absolute dependency URI: {uri}')
    path = checked_path(source.parent / relative)
    content = path.read_bytes()
    dependencies[path.relative_to(ROOT).as_posix()] = digest_record(path, content)
    return content


def load_source(source, expected_hash):
    content = source.read_bytes()
    if sha256(content).hexdigest() != expected_hash:
        raise ValueError(f'Source SHA-256 mismatch: {source.relative_to(ROOT)}')
    if source.suffix.lower() == '.glb':
        document, binary_chunk = parse_glb(content)
    elif source.suffix.lower() == '.gltf':
        document, binary_chunk = json.loads(content.decode('utf-8-sig')), None
    else:
        raise ValueError('Only .glb and .gltf source files are supported')
    if document.get('asset', {}).get('version') != '2.0':
        raise ValueError('Only glTF 2.0 is supported')
    extensions = (set(walk_extensions(document)) | set(document.get('extensionsUsed', []))
                  | set(document.get('extensionsRequired', [])))
    if extensions & COMPRESSED_EXTENSIONS:
        raise ValueError('Compressed geometry cannot be projected without decompression')
    dependencies = {}
    buffers = []
    for index, record in enumerate(document.get('buffers', [])):
        if 'uri' in record:
            data = read_uri(record['uri'], source, dependencies)
        elif index == 0 and binary_chunk is not None:
            data = binary_chunk
        else:
            raise ValueError(f'Buffer {index} has no source bytes')
        declared = record['byteLength']
        if not isinstance(declared, int) or declared < 0 or len(data) < declared:
            raise ValueError(f'Invalid byteLength in buffer {index}')
        if 'uri' in record and len(data) != declared:
            raise ValueError(f'External buffer {index} byteLength mismatch')
        if 'uri' not in record and len(data) - declared > 3:
            raise ValueError(f'Unexpected padding in buffer {index}')
        buffers.append(data[:declared])
    return document, buffers, dependencies, digest_record(source, content)


def view_bytes(document, buffers, index):
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise ValueError('Invalid bufferView reference')
    view = document['bufferViews'][index]
    buffer_index = view['buffer']
    if not isinstance(buffer_index, int) or isinstance(buffer_index, bool) or buffer_index < 0:
        raise ValueError(f'Invalid buffer index in bufferView {index}')
    buffer = buffers[buffer_index]
    start, length = view.get('byteOffset', 0), view['byteLength']
    if not isinstance(start, int) or not isinstance(length, int) or start < 0 or length < 0:
        raise ValueError(f'Invalid offset/length in bufferView {index}')
    if start + length > len(buffer):
        raise ValueError(f'bufferView {index} exceeds its buffer')
    return buffer[start:start + length]


def image_bytes(document, buffers, index, source, dependencies):
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise ValueError('Invalid image reference')
    image = document['images'][index]
    if 'bufferView' in image:
        return view_bytes(document, buffers, image['bufferView'])
    return read_uri(image['uri'], source, dependencies)


def alpha_weighted_linear_mean(content, cache):
    identity = sha256(content).hexdigest()
    if identity not in cache:
        with Image.open(BytesIO(content)) as image:
            rgba = image.convert('RGBA')
            histograms = [[0] * 256 for _ in range(3)]
            total_alpha = 0
            for red, green, blue, alpha in struct.iter_unpack('BBBB', rgba.tobytes()):
                histograms[0][red] += alpha
                histograms[1][green] += alpha
                histograms[2][blue] += alpha
                total_alpha += alpha
        cache[identity] = [
            sum(weight * linear for weight, linear in zip(histogram, SRGB_TO_LINEAR)) / total_alpha
            if total_alpha else 0.0
            for histogram in histograms
        ]
    return cache[identity]


def pigment_hex(linear_color, factor):
    channels = []
    for channel, multiplier in zip(linear_color, factor[:3]):
        value = max(0.0, min(1.0, channel * multiplier))
        srgb = 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055
        channels.append(round(255 * srgb))
    return '#' + ''.join(f'{channel:02x}' for channel in channels)


def strip_material_textures(value):
    if isinstance(value, dict):
        for key in list(value):
            if key.lower().endswith('texture') and isinstance(value[key], dict) and 'index' in value[key]:
                del value[key]
            elif key != 'extras':
                strip_material_textures(value[key])
    elif isinstance(value, list):
        for child in value:
            strip_material_textures(child)


def remap_view_references(value, mapping):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'bufferView':
                value[key] = mapping[child]
            elif key != 'extras':
                remap_view_references(child, mapping)
    elif isinstance(value, list):
        for child in value:
            remap_view_references(child, mapping)


def collect_view_references(value):
    references = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'bufferView':
                references.add(child)
            elif key != 'extras':
                references.update(collect_view_references(child))
    elif isinstance(value, list):
        for child in value:
            references.update(collect_view_references(child))
    return references


def pack_glb(document, binary):
    text = json.dumps(document, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    text += b' ' * (-len(text) % 4)
    binary += b'\0' * (-len(binary) % 4)
    length = 12 + 8 + len(text) + 8 + len(binary)
    return (struct.pack('<4sII', b'glTF', 2, length)
            + struct.pack('<II', len(text), JSON_CHUNK) + text
            + struct.pack('<II', len(binary), BIN_CHUNK) + binary)


def project(job, mean_cache):
    source = checked_path(job['sourcePath'])
    original, buffers, dependencies, source_record = load_source(source, job['expectedSha256'])
    result = deepcopy(original)
    pigments = []
    for index, material in enumerate(result.get('materials', [])):
        pbr = material.get('pbrMetallicRoughness', {})
        texture_info = pbr.get('baseColorTexture')
        if texture_info is not None:
            texture_index = texture_info['index']
            if not isinstance(texture_index, int) or isinstance(texture_index, bool) or texture_index < 0:
                raise ValueError(f'Invalid texture reference on material {index}')
            texture = original['textures'][texture_index]
            content = image_bytes(original, buffers, texture['source'], source, dependencies)
            factor = pbr.get('baseColorFactor', [1, 1, 1, 1])
            if len(factor) != 4 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in factor):
                raise ValueError(f'Invalid baseColorFactor on material {index}')
            pigment = pigment_hex(alpha_weighted_linear_mean(content, mean_cache), factor)
            extras = material.setdefault('extras', {})
            if not isinstance(extras, dict):
                raise ValueError('Material extras must be an object to attach notebookPigment')
            extras['notebookPigment'] = pigment
            pigments.append({'material': index, 'name': material.get('name', ''), 'color': pigment})
        strip_material_textures(material)
    # Read all external dependencies for a complete input-bundle provenance record.
    for image in original.get('images', []):
        if 'uri' in image:
            read_uri(image['uri'], source, dependencies)
    for key in ('images', 'textures', 'samplers'):
        result.pop(key, None)
    image_views = {image['bufferView'] for image in original.get('images', []) if 'bufferView' in image}
    referenced_views = collect_view_references(result)
    for index in referenced_views | image_views:
        view_bytes(original, buffers, index)
    removed_views = image_views - referenced_views
    binary = bytearray()
    mapping = {}
    retained = []
    for index, view in enumerate(original.get('bufferViews', [])):
        content = view_bytes(original, buffers, index)
        if index in removed_views:
            continue
        binary.extend(b'\0' * (-len(binary) % 4))
        output_view = deepcopy(view)
        output_view.update({'buffer': 0, 'byteOffset': len(binary)})
        mapping[index] = len(retained)
        retained.append(output_view)
        binary.extend(content)
    result['bufferViews'] = retained
    remap_view_references(result, mapping)
    result['buffers'] = [{'byteLength': len(binary)}]
    live_extensions = set(walk_extensions(result))
    for key in ('extensionsUsed', 'extensionsRequired'):
        if key in result:
            result[key] = [extension for extension in result[key] if extension in live_extensions]
            if not result[key]:
                del result[key]
    content = pack_glb(result, bytes(binary))
    decoded, output_binary = parse_glb(content)
    for old_index, new_index in mapping.items():
        if view_bytes(original, buffers, old_index) != view_bytes(decoded, [output_binary], new_index):
            raise ValueError(f'Geometry bufferView {old_index} changed')
    for key in ('meshes', 'nodes', 'scenes', 'scene', 'animations', 'skins'):
        expected = deepcopy(original.get(key))
        remap_view_references(expected, mapping)
        if expected != decoded.get(key):
            raise ValueError(f'{key} changed in flat projection')
    expected_accessors = deepcopy(original.get('accessors'))
    remap_view_references(expected_accessors, mapping)
    if expected_accessors != decoded.get('accessors'):
        raise ValueError('Accessor metadata changed in flat projection')
    for before, after in zip(original.get('materials', []), decoded.get('materials', [])):
        if before.get('name') != after.get('name'):
            raise ValueError('Material name changed in flat projection')
        before_factor = before.get('pbrMetallicRoughness', {}).get('baseColorFactor')
        after_factor = after.get('pbrMetallicRoughness', {}).get('baseColorFactor')
        if before_factor != after_factor:
            raise ValueError('Material baseColorFactor changed in flat projection')
    total_source_bytes = source_record['bytes'] + sum(record['bytes'] for record in dependencies.values())
    model_id = job['id']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', model_id):
        raise ValueError(f'Unsafe projection ID: {model_id}')
    identity = sha256(content).hexdigest()
    filename = f'{model_id}-{identity[:12]}.glb'
    primitives = [primitive for mesh in original.get('meshes', []) for primitive in mesh.get('primitives', [])]
    triangle_count = 0
    for primitive in primitives:
        accessor = primitive.get('indices', primitive['attributes']['POSITION'])
        element_count = original['accessors'][accessor]['count']
        mode = primitive.get('mode', 4)
        if mode == 4:
            triangle_count += element_count // 3
        elif mode in (5, 6):
            triangle_count += max(0, element_count - 2)
    counts = {
        'nodes': len(original.get('nodes', [])), 'meshes': len(original.get('meshes', [])),
        'primitives': len(primitives), 'triangles': triangle_count,
        'accessors': len(original.get('accessors', [])),
        'bufferViewsBefore': len(original.get('bufferViews', [])), 'bufferViewsAfter': len(retained),
        'imageOnlyBufferViewsRemoved': len(removed_views), 'retainedViewBytes': sum(v['byteLength'] for v in retained),
        'imagesRemoved': len(original.get('images', [])), 'texturesRemoved': len(original.get('textures', [])),
    }
    record = {
        'id': model_id, 'file': filename, 'bytes': len(content), 'sha256': identity,
        'source': source_record, 'dependencies': sorted(dependencies.values(), key=lambda record: record['path']),
        'sourceBundleBytes': total_source_bytes, 'savedBytes': total_source_bytes - len(content),
        'geometryBytePreserved': True, 'structurePreserved': True, 'counts': counts, 'pigments': pigments,
    }
    if model_id in ('study-mao-gate', 'research-mao-gate') and len(content) > 1_200_000:
        raise ValueError('Mao gate projection exceeds the 1.2 MB budget')
    return record, content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=Path, help='JSON jobs file; defaults to stdin')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--check', action='store_true', help='Rebuild in memory and compare saved files')
    args = parser.parse_args()
    try:
        text = args.jobs.read_text(encoding='utf-8-sig') if args.jobs else sys.stdin.read()
        payload = json.loads(text)
        if isinstance(payload, dict) and 'models' in payload:
            jobs = [{'id': model['id'], 'sourcePath': model['source']['path'],
                     'expectedSha256': model['source']['sha256']} for model in payload['models']]
        else:
            jobs = payload['jobs'] if isinstance(payload, dict) else payload
        if not isinstance(jobs, list) or not jobs or len({job['id'] for job in jobs}) != len(jobs):
            raise ValueError('Expected a nonempty list of jobs with distinct IDs')
        mean_cache = {}
        built = [project(job, mean_cache) for job in jobs]
        records = [record for record, content in built]
        manifest = {'recipe': RECIPE, 'pigmentColorSpace': 'alpha-weighted linear mean encoded as sRGB hex',
                    'geometryBytePreserved': True, 'models': records}
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        if args.check:
            for record, content in built:
                if (OUTPUT / record['file']).read_bytes() != content:
                    raise ValueError(f'Saved projection differs: {record["id"]}')
            # Git checkouts may convert text to CRLF; the generated GLBs stay byte-exact.
            saved_manifest = (OUTPUT / 'source.json').read_text(encoding='utf-8')
            if saved_manifest != manifest_bytes.decode('utf-8'):
                raise ValueError('Saved source manifest differs')
        elif not args.dry_run:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            for record, content in built:
                target = OUTPUT / record['file']
                if not target.exists() or target.read_bytes() != content:
                    target.write_bytes(content)
            (OUTPUT / 'source.json').write_bytes(manifest_bytes)
        print(json.dumps({'mode': 'check' if args.check else 'dry-run' if args.dry_run else 'build',
                          'models': records}, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, IndexError, TypeError) as error:
        parser.exit(1, f'Flat projection failed: {error}\n')


if __name__ == '__main__':
    main()
