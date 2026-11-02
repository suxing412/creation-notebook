#!/usr/bin/env python3
"""Restore an exact original ZIP from local, verified byte parts (Python stdlib only)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


def validate_manifest(m):
    if m.get('format') != 'exact-zip-byte-parts-v1':
        raise ValueError('Unsupported manifest format')
    a = m.get('archive', {})
    sha = re.compile(r'^[0-9a-f]{64}$')
    name = a.get('name', '')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.zip', name):
        raise ValueError('Invalid archive name')
    if not sha.fullmatch(a.get('sha256', '')) or type(a.get('bytes')) is not int or a['bytes'] <= 0:
        raise ValueError('Invalid original archive identity')
    if not isinstance(a.get('originalPath'), str) or a['originalPath'].startswith('/') or '..' in a['originalPath'].split('/'):
        raise ValueError('Invalid original path')
    parts = m.get('parts')
    if not isinstance(parts, list) or not parts or m.get('partCount') != len(parts):
        raise ValueError('Invalid part count')
    total = 0
    for i, p in enumerate(parts, 1):
        if p.get('index') != i or p.get('file') != f'{name}.part{i:03d}':
            raise ValueError('Incorrect part order or name')
        if type(p.get('bytes')) is not int or not 0 < p['bytes'] <= 8 * 1024 * 1024:
            raise ValueError('Invalid part size')
        if not sha.fullmatch(p.get('sha256', '')):
            raise ValueError('Invalid part hash')
        total += p['bytes']
    if total != a['bytes']:
        raise ValueError('Part sizes do not equal original ZIP size')
    return a, parts


def restore(manifest_path, output=None):
    manifest_path = Path(manifest_path)
    a, parts = validate_manifest(json.loads(manifest_path.read_text(encoding='utf-8')))
    output = Path(output) if output is not None else Path(a['name'])
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Refusing to overwrite existing output: {output}')
    if not output.parent.is_dir():
        raise ValueError('Output parent directory must already exist')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', prefix='.zip-rebuild-', suffix='.tmp', dir=output.parent, delete=False) as dest:
            temporary = Path(dest.name)
            full_hash = hashlib.sha256()
            full_size = 0
            for p in parts:
                source = manifest_path.parent / p['file']
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f'Missing part or disallowed symlink: {p["file"]}')
                part_hash = hashlib.sha256()
                part_size = 0
                with source.open('rb') as handle:
                    for block in iter(lambda: handle.read(1024 * 1024), b''):
                        part_size += len(block)
                        if part_size > p['bytes']:
                            raise ValueError(f'Part too large: {p["file"]}')
                        part_hash.update(block)
                        full_hash.update(block)
                        full_size += len(block)
                        dest.write(block)
                if part_size != p['bytes'] or part_hash.hexdigest() != p['sha256']:
                    raise ValueError(f'Part size/SHA-256 mismatch: {p["file"]}')
            if full_size != a['bytes'] or full_hash.hexdigest() != a['sha256']:
                raise ValueError('Original ZIP size/SHA-256 mismatch; no output created')
            dest.flush()
            os.fsync(dest.fileno())
        # Same-directory atomic hard link publishes only fully verified bytes, and never replaces.
        # If the filesystem cannot create hard links, fail instead of weakening overwrite safety.
        os.link(temporary, output)
        return {'output': str(output), 'bytes': full_size, 'sha256': full_hash.hexdigest()}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='Local manifest.json beside the downloaded parts')
    parser.add_argument('--output', help='New ZIP path; existing files are never overwritten')
    args = parser.parse_args()
    try:
        result = restore(args.manifest, args.output)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'REFUSED: {error}', file=sys.stderr)
        return 1
    print(f'VERIFIED: {result["output"]} ({result["bytes"]} bytes) SHA-256 {result["sha256"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
