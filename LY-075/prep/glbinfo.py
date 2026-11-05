import json, struct, sys, hashlib
import numpy as np

def load(path):
    b = open(path, 'rb').read()
    magic, ver, length = struct.unpack_from('<III', b, 0)
    off = 12; js = None; bin_ = None
    while off < length:
        clen, ctype = struct.unpack_from('<II', b, off); off += 8
        chunk = b[off:off+clen]; off += clen
        if ctype == 0x4E4F534A: js = json.loads(chunk.decode('utf-8'))
        elif ctype == 0x004E4942: bin_ = chunk
    return js, bin_

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def acc(js, bin_, i):
    a = js['accessors'][i]; bv = js['bufferViews'][a['bufferView']]
    dt = np.dtype(CT[a['componentType']]); n = NC[a['type']]
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    cnt = a['count']
    if stride == dt.itemsize * n:
        arr = np.frombuffer(bin_, dtype=dt, count=cnt * n, offset=start).reshape(cnt, n)
    else:
        arr = np.stack([np.frombuffer(bin_, dtype=dt, count=n, offset=start + k * stride) for k in range(cnt)])
    return arr

if __name__ == '__main__':
    for p in sys.argv[1:]:
        js, bin_ = load(p)
        print('==', p.split('/')[-1])
        print(' nodes', [(n.get('name'), n.get('mesh'), n.get('translation'), n.get('rotation'), n.get('scale')) for n in js['nodes']])
        print(' meshes', [(m.get('name'), [(pr.get('material'), list(pr['attributes'].keys())) for pr in m['primitives']]) for m in js['meshes']])
        for i, m in enumerate(js.get('materials', [])):
            pbr = m.get('pbrMetallicRoughness', {})
            print(' mat', i, m.get('name'), 'ds', m.get('doubleSided'), 'bcf', pbr.get('baseColorFactor'), 'bct', pbr.get('baseColorTexture'), 'mf', pbr.get('metallicFactor'), 'rf', pbr.get('roughnessFactor'), 'mrt', pbr.get('metallicRoughnessTexture'), 'nt', m.get('normalTexture'), 'ot', m.get('occlusionTexture'), 'alpha', m.get('alphaMode'))
        for i, im in enumerate(js.get('images', [])):
            bv = js['bufferViews'][im['bufferView']]
            data = bin_[bv.get('byteOffset', 0): bv.get('byteOffset', 0) + bv['byteLength']]
            w, h = struct.unpack('>II', data[16:24]) if data[:8] == b'\x89PNG\r\n\x1a\n' else (None, None)
            print(' img', i, im.get('name'), im.get('mimeType'), bv['byteLength'], (w, h), hashlib.sha1(data).hexdigest()[:10])
        print(' textures', js.get('textures'))
        print(' samplers', js.get('samplers'))
