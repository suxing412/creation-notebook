# LY-084 prep: hash every input (working-tree bytes AND committed blob bytes at
# bce3211, since text files differ by CRLF in this Windows checkout) and extract
# the one road chunk we need from the split city-visible zip into prep/work/.
# Read-only on the lab repo: only `git cat-file` / `git show` (read ops).
#
#   python -I hash_inputs.py D:/GitHub/creation-notebook-lab  > out/hashes.json
import hashlib, io, json, os, subprocess, sys, zipfile

lab = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
BASE = 'bce3211f818ee5a8bef1773539da70695ba37b17'
RB = 'modeling-lab/review-batches/2026-11-04-city-visible/'

INPUTS = [
    # path, role
    ('docs/cities/luoyang/city-data.mjs', 'city manifest: what is loaded'),
    ('docs/cities/luoyang/app.mjs', 'page bootstrap; imports city-data.mjs, lazy-loads city-renderer.mjs'),
    ('docs/cities/luoyang/city-renderer.mjs', 'GLTFLoader + node transform (L374-387) + excludeNodes merge (L323)'),
    ('docs/cities/luoyang/p-luoyang.asset.json', 'project card: NE C path explicitly not connected'),
    ('docs/cities/luoyang/assets/ground-atomic/network-ground-stitched.glb', 'atomic ground 1/4 (6m network)'),
    ('docs/cities/luoyang/assets/ground-atomic/retained.glb', 'atomic ground 2/4'),
    ('docs/cities/luoyang/assets/ground-atomic/south.glb', 'atomic ground 3/4'),
    ('docs/cities/luoyang/assets/ground-atomic/D08.glb', 'atomic ground 4/4 (city node position 580,0,-960)'),
    ('docs/cities/luoyang/assets/city-wall/A/wall-00.glb', 'C wall north-west'),
    ('docs/cities/luoyang/assets/city-wall/A/wall-01.glb', 'C wall north-east / east (nearest wall to all three candidates)'),
    ('docs/cities/luoyang/assets/city-wall/A/wall-02.glb', 'C wall east (Shangdong-Zhongdong)'),
    ('docs/cities/luoyang/assets/city-wall/A/wall-03.glb', 'C wall east (south of Zhongdong)'),
    ('docs/cities/luoyang/progress-assets/granary-city-v1/granary-city-LOD0.glb', 'storage-main in city (Taicang ground + 2 granaries)'),
    ('docs/cities/luoyang/progress-assets/granary-city-v1/source.json', 'externalRoadActivated:false'),
    ('docs/cities/luoyang/data/evidence/evidence-geometry.json', 'frozen 42 B features (frame luoyang-local-schematic-v01)'),
    ('docs/cities/luoyang/data/west/road-preconstraints.json', '11 road relations + palace link classification (NE lines hold_palace_interface)'),
    ('docs/cities/luoyang/data/west/road-plan.json', 'derived 6m C pieces (C_4 middle_cross east piece is the nearest built ground)'),
    ('docs/cities/luoyang/data/west/north-palace-conflict-layer.json', 'new north palace A walls unregistered; old B for comparison only'),
    ('docs/cities/luoyang/data/west/storage-precedents.json', 'Taicang/Wuku B points; access rule: only C service spur'),
    ('docs/cities/luoyang/data/west/storage-interface.json', 'externalRoad: nearest B relation is palace-edge held'),
    ('docs/cities/luoyang/data/west/ground-atomic-contract.json', 'atomic ground contract'),
    ('docs/cities/luoyang/data/west/city-wall-constraints.json', 'wall C constraints, no moat'),
    ('docs/cities/luoyang/data/west/road-interface.json', 'road runtime assets / widths'),
    (RB + 'adapter/adapter.json', 'node visible-current-node-northeast_C_access (not published)'),
    (RB + 'README.zh-CN.md', 'mother .blend SHA 1e8c4d2c... ; coordinate contract'),
]
for i in range(1, 6):
    INPUTS.append((RB + 'city-visible-web-handoff-v1-public.zip.part0%d' % i, 'split zip %d/5 (road chunk container)' % i))


def sh(b):
    return hashlib.sha256(b).hexdigest()


def blob(path):
    try:
        return subprocess.run(['git', '-C', lab, 'cat-file', 'blob', BASE + ':' + path],
                              capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None


rows = []
for p, role in INPUTS:
    fp = os.path.join(lab, p)
    wt = open(fp, 'rb').read() if os.path.exists(fp) else None
    cb = blob(p)
    rows.append({'path': p, 'role': role,
                 'bytes': len(cb) if cb is not None else None,
                 'sha256_commit_blob': sh(cb) if cb is not None else None,
                 'sha256_worktree': sh(wt) if wt is not None else None,
                 'crlf_differs': (wt is not None and cb is not None and sh(wt) != sh(cb))})

parts = b''.join(open(os.path.join(lab, RB + 'city-visible-web-handoff-v1-public.zip.part0%d' % i), 'rb').read()
                 for i in range(1, 6))
derived = [{'path': '(concat part01..05)/city-visible-web-handoff-v1-public.zip', 'bytes': len(parts), 'sha256': sh(parts)}]
z = zipfile.ZipFile(io.BytesIO(parts))
work = os.path.join(here, 'work')
os.makedirs(work, exist_ok=True)
for m in ('chunks/northeast_C_access.glb', 'qa/source-node-manifest.json'):
    b = z.read(m)
    derived.append({'path': 'zip:' + m, 'bytes': len(b), 'sha256': sh(b)})
    with open(os.path.join(work, os.path.basename(m)), 'wb') as f:
        f.write(b)

json.dump({'lab': 'creation-notebook-lab', 'baseline': BASE, 'inputs': rows, 'derived': derived},
          sys.stdout, ensure_ascii=False, indent=1)
