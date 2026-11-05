# LY-034 prep: strict byte fingerprint of a GLB (pure python, read-only).
# python -I fingerprint.py in.glb [measure.json] > fp.json
# - file sha256; per node: name, TRS/matrix; per primitive: material name + sha256 of each accessor's bytes
#   (POSITION / NORMAL / TEXCOORD_n / indices); per image: sha256 of bytes
# - if a measure_frontfield.py output is given, also emits the island-level geometric fingerprint of the
#   receiving shelter, check table, cargo on/near the field, ground slab and both stairs (local coords).
import json, struct, sys, hashlib
p = sys.argv[1]
b = open(p, 'rb').read()
cl = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + cl])
off = 20 + cl; bl = struct.unpack('<I', b[off:off + 4])[0]; bin_ = b[off + 8:off + 8 + bl]
SZ = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
def acc_bytes(i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    es = SZ[a['componentType']] * NC[a['type']]; st = bv.get('byteStride', es)
    o = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    return b''.join(bin_[o + k * st:o + k * st + es] for k in range(a['count']))
h = lambda x: hashlib.sha256(x).hexdigest()
out = {'file': p, 'bytes': len(b), 'sha256': h(b), 'nodes': [], 'images': []}
for n in j.get('nodes', []):
    rec = {'name': n.get('name'), **{k: n[k] for k in ('translation', 'rotation', 'scale', 'matrix') if k in n}}
    if 'mesh' in n:
        prims = []
        for pr in j['meshes'][n['mesh']]['primitives']:
            e = {'material': j['materials'][pr['material']].get('name') if 'material' in pr else None}
            for k, v in sorted(pr['attributes'].items()): e[k] = h(acc_bytes(v))
            if 'indices' in pr: e['indices'] = h(acc_bytes(pr['indices']))
            prims.append(e)
        rec['primitives'] = prims
    out['nodes'].append(rec)
for im in j.get('images', []):
    if 'bufferView' in im:
        bv = j['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
        out['images'].append({'name': im.get('name'), 'mime': im.get('mimeType'), 'sha256': h(bin_[o:o + bv['byteLength']])})
if len(sys.argv) > 2:
    m = json.load(open(sys.argv[2], encoding='utf-8'))
    isl = m['islands']; sh = m['shelter']
    def inside(s, x0, z0, x1, z1): return s['min'][0] >= x0 and s['max'][0] <= x1 and s['min'][2] >= z0 and s['max'][2] <= z1
    sx0, sx1, sz0, sz1 = sh['min'][0] - 0.5, sh['max'][0] + 0.5, sh['min'][2] - 0.5, sh['max'][2] + 0.5
    out['islandFingerprint'] = {
        'measure': sys.argv[2],
        'receivingShelterAndTable': sorted([s for s in isl if inside(s, sx0, sz0, sx1, sz1) and s['max'][1] > 0.21], key=lambda s: (s['min'][0], s['min'][2], s['min'][1])),
        'fieldCargoOutsideShelter': sorted([s for s in isl if 'cargo' in (s['material'] or '') and s['min'][2] > max(st['footZ'] for st in m['stairs']) and not inside(s, sx0, sz0, sx1, sz1)], key=lambda s: (s['min'][0], s['min'][2])),
        'groundSlab': m['groundIslands'],
        'stairs': [{k: st[k] for k in ('xCentre', 'width', 'risers', 'rises', 'footZ', 'headZ', 'topLanding', 'floorInside', 'doorClearWidthAt1.2m', 'doorClearHeight')} | {'island': st['island']} for st in m['stairs']],
    }
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
