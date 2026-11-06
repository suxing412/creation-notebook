# -*- coding: utf-8 -*-
"""LY-007 近景保留核验（只读 Git；仅写指定 LY-007/qa 输出）。
递归核验 assetRecords 中所有 path/nearPath 模型引用及相邻 SHA256；
路径相对 docs/cities/luoyang 规范化，包含 .glb 与 .gltf。
用法: python -I near_retention.py <LY-007 目录> <lab 仓库> <commit>
本脚本不验证渲染、glTF 外部资源、G 冻结、锁或所有权。
"""
import sys, os, re, json, hashlib, subprocess, collections, posixpath, shlex
from pathlib import Path

BASE = 'docs/cities/luoyang'


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def parse_asset_records(src):
    """Read a strict JSON literal, never execute the JavaScript module."""
    found = list(re.finditer(r'^\s*const\s+assetRecords\s*=\s*', src, re.M))
    if len(found) != 1:
        raise ValueError('expected exactly one const assetRecords declaration')
    records, end = json.JSONDecoder(object_pairs_hook=_unique_object).raw_decode(src, found[0].end())
    if not isinstance(records, list) or not records:
        raise ValueError('assetRecords must be a non-empty array')
    if not re.match(r'\s*;', src[end:]):
        raise ValueError('assetRecords must be a complete JSON literal followed by ;')
    if any(not isinstance(r, dict) for r in records):
        raise ValueError('each assetRecords entry must be an object')
    return records


def resolve_model_path(path):
    if not isinstance(path, str) or not path or path != path.strip():
        raise ValueError('path must be a non-empty string without surrounding whitespace')
    if (path.startswith('/') or '\\' in path or ':' in path or '?' in path or '#' in path
            or any(ord(c) < 32 for c in path)):
        raise ValueError('path must be a repository-relative POSIX model path')
    result = posixpath.normpath(posixpath.join(BASE, path))
    if result == '..' or result.startswith('../'):
        raise ValueError('path escapes the repository')
    if posixpath.splitext(result)[1].lower() not in ('.glb', '.gltf'):
        raise ValueError('path must reference .glb or .gltf')
    return result


def check_city(src, read_blob, commit):
    """Keep every occurrence, including invalid references, with its JSON pointer."""
    records = parse_asset_records(src)
    city, near_far, errors = [], [], []

    def walk(obj, pointer, aid, required_model=False):
        if isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, pointer + '/' + str(i), aid, required_model)
            return
        if not isinstance(obj, dict):
            if required_model:
                errors.append(dict(pointer=pointer, error='model reference container must be an object'))
            return
        aid = obj.get('id', aid)
        pair = {}
        for key, sha_key, kind in (('path', 'sha256', 'far'), ('nearPath', 'nearSha256', 'near')):
            if key not in obj and sha_key not in obj and not (required_model and key == 'path'):
                continue
            row = dict(id=aid, kind=kind, pointer=pointer + '/' + key,
                       raw_path=obj.get(key), path=None, declared_sha256=obj.get(sha_key),
                       exists=False, actual_sha256=None, match=False, restore=None, errors=[])
            try:
                row['path'] = resolve_model_path(obj.get(key))
            except ValueError as exc:
                row['errors'].append(str(exc))
            declared = obj.get(sha_key)
            if not isinstance(declared, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', declared):
                row['errors'].append(sha_key + ' must be a 64-digit hex string')
            if not row['errors']:
                blob = read_blob(row['path'])
                row['exists'] = blob is not None
                row['restore'] = 'git -C <lab> show ' + shlex.quote(commit + ':' + row['path']) + ' > <out>'
                if blob is None:
                    row['errors'].append('model blob does not exist')
                else:
                    row['actual_sha256'] = hashlib.sha256(blob).hexdigest()
                    row['match'] = row['actual_sha256'] == declared.lower()
                    if not row['match']:
                        row['errors'].append('SHA256 mismatch')
            city.append(row)
            pair[kind] = row
            errors.extend(dict(pointer=row['pointer'], error=error) for error in row['errors'])
        if 'near' in pair:
            if 'far' not in pair:
                errors.append(dict(pointer=pointer, error='nearPath has no sibling path/sha256'))
            else:
                near, far = pair['near'], pair['far']
                verified = near['match'] and far['match']
                same = near['actual_sha256'] == far['actual_sha256'] if verified else None
                near_far.append(dict(id=aid, pointer=pointer, near=near['path'], far=far['path'],
                                     verified=verified, same_bytes=same))
                if same:
                    errors.append(dict(pointer=pointer, error='near/far models have identical bytes'))
        for key, value in obj.items():
            escaped = key.replace('~', '~0').replace('/', '~1')
            # These optional containers are model references in the current data contract.
            required = key in ('sourceAsset', 'availableLod2')
            if required and not isinstance(value, dict):
                errors.append(dict(pointer=pointer + '/' + escaped,
                                   error='model reference container must be an object'))
            else:
                walk(value, pointer + '/' + escaped, aid, required)

    # Every top-level asset is a model; missing both fields is not an absent reference.
    walk(records, '/assetRecords', None, required_model=True)
    if not city:
        errors.append(dict(pointer='/assetRecords', error='no model references found'))
    paths = {r['path'] for r in city if r['path'] is not None}
    summary = dict(commit=commit, city_refs=len(city), city_refs_match=sum(r['match'] for r in city),
                   path_refs=sum(r['kind'] == 'far' for r in city),
                   near_refs=sum(r['kind'] == 'near' for r in city),
                   unique_model_paths=len(paths),
                   unique_glb_paths=sum(p.lower().endswith('.glb') for p in paths),
                   unique_gltf_paths=sum(p.lower().endswith('.gltf') for p in paths),
                   near_far_pairs=len(near_far), near_far_same_bytes=[x for x in near_far if x['same_bytes']],
                   reference_errors=len(errors), references_pass=not errors)
    return dict(summary=summary, city=city, near_far=near_far, reference_errors=errors)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3:
        raise SystemExit('usage: near_retention.py <LY-007 output> <lab repo> <commit>')
    W, LAB, C = args
    C = subprocess.run(['git', '--no-optional-locks', '--no-replace-objects', '-C', LAB,
                        'rev-parse', '--verify', '--end-of-options', C + '^{commit}'],
                       capture_output=True, text=True, check=True).stdout.strip()

    tree = subprocess.run(['git', '--no-optional-locks', '--no-replace-objects', '-C', LAB,
                           'ls-tree', '-r', '-z', C], capture_output=True, check=True).stdout
    entries = {}
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        meta, path = entry.split(b'\t', 1)
        mode, kind, oid = meta.split(b' ')
        entries[os.fsdecode(path)] = (mode, kind, oid.decode('ascii'))

    def show(path):
        entry = entries.get(path)
        if entry is None:
            return None
        mode, kind, oid = entry
        if mode not in (b'100644', b'100755') or kind != b'blob':
            raise ValueError('model input is not a regular Git blob: ' + path)
        result = subprocess.run(['git', '--no-optional-locks', '--no-replace-objects', '-C', LAB,
                                 'cat-file', 'blob', oid], capture_output=True)
        return result.stdout if result.returncode == 0 else None

    src = show(BASE + '/city-data.mjs')
    if src is None:
        raise ValueError('city-data.mjs is missing at the specified commit')
    report = check_city(src.decode('utf-8'), show, C)
    ls = entries
    grp = collections.defaultdict(dict)
    for path in ls:
        match = re.match(r'(.*luoyang.*/[^/]+?)-LOD([012])\.glb$', path, re.S)
        if match:
            grp[match.group(1)][int(match.group(2))] = path
    cards = []
    for stem, tiers in sorted(grp.items()):
        sh = {}
        for k, path in tiers.items():
            blob = show(path)
            if blob is None:
                raise ValueError('LOD blob is missing: ' + path)
            sh[k] = hashlib.sha256(blob).hexdigest()
        cards.append(dict(stem=stem, tiers=sorted(tiers), has_LOD0=0 in tiers,
                          lod1_equals_lod0=(sh.get(1) == sh.get(0)) if 0 in sh and 1 in sh else None,
                          lod2_equals_lod0=(sh.get(2) == sh.get(0)) if 0 in sh and 2 in sh else None,
                          sha256={f'LOD{k}': v for k, v in sh.items()}))
    report['card_tiers'] = cards
    report['summary'].update(tier_stems=len(cards),
        stems_without_LOD0=[c['stem'] for c in cards if not c['has_LOD0']],
        stems_with_tier_copy_of_LOD0=[c['stem'] for c in cards if c['lod1_equals_lod0'] or c['lod2_equals_lod0']])
    destination = Path(W).absolute() / 'qa' / 'near-retention.json'
    if any(path.is_symlink() for path in (destination, *destination.parents)):
        raise ValueError('symlink output path is forbidden')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=1)
    print(json.dumps(report['summary'], ensure_ascii=False, indent=1))
    return 0 if report['summary']['references_pass'] and not report['summary']['stems_with_tier_copy_of_LOD0'] else 1


if __name__ == '__main__':
    sys.exit(main())
