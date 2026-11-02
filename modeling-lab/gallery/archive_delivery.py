#!/usr/bin/env python3
"""Reproducible GitHub delivery projection; never recompresses a source ZIP.

Clone a full static tree into a NEW output directory, then split only ZIPs whose
base64 request cannot fit the 16 MiB budget with a 64 KiB request reserve.
Existing projected builds call apply_projection() to preserve download routing.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import os
import re
import shutil
from urllib.parse import urlsplit, unquote

REQUEST_LIMIT = 16 * 1024 * 1024
REQUEST_RESERVE = 64 * 1024
RAW_SAFE_LIMIT = ((REQUEST_LIMIT - REQUEST_RESERVE) // 4) * 3
PART_BYTES = 8 * 1024 * 1024
ASSET_NAMES = ('archive.mjs', 'archive.css', 'restore-source.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_page(root, folder, manifest):
    archive = manifest['archive']
    page = folder.parent / 'source-download.html'
    css = os.path.relpath(root / 'downloads' / 'archive.css', page.parent).replace(os.sep, '/')
    js = os.path.relpath(root / 'downloads' / 'archive.mjs', page.parent).replace(os.sep, '/')
    restore = os.path.relpath(root / 'downloads' / 'restore-source.py', page.parent).replace(os.sep, '/')
    manifest_path = folder / 'manifest.json'
    manifest_href = os.path.relpath(manifest_path, page.parent).replace(os.sep, '/')
    manifest_sha = sha(manifest_path.read_bytes())
    chunks = ''.join(f'<li><a href="source-parts/{html.escape(p["file"])}" download>{html.escape(p["file"])} · 第 {p["index"]} 卷</a><p>{p["bytes"]:,} 字节 · SHA-256<br><code>{p["sha256"]}</code></p></li>' for p in manifest['parts'])
    page.write_text(f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="referrer" content="no-referrer"><title>分卷源包 · 校验并还原 ZIP</title><link rel="stylesheet" href="{css}"><script type="module" src="{js}"></script></head>
<body><main data-archive-manifest="{manifest_href}" data-manifest-sha256="{manifest_sha}"><nav><a href="index.html">← 返回作品</a></nav><header><p class="eyebrow">SOURCE ARCHIVE / EXACT BYTE DELIVERY</p><h1>分卷源包。<br>校验后，回到完整 ZIP。</h1><p>这是完整原始源码包的二进制分卷，不是删减包，也没有重新压缩。每卷最多 8 MiB；单卷<strong>不是可单独解压的 ZIP</strong>。</p></header>
<dl><dt>还原文件名</dt><dd><code>{html.escape(archive['name'])}</code></dd><dt>完整大小</dt><dd>{archive['bytes']:,} 字节 · {manifest['partCount']} 卷</dd><dt>完整 SHA-256</dt><dd><code>{archive['sha256']}</code></dd><dt>原快照路径</dt><dd><code>{html.escape(archive['originalPath'])}</code><br><span class="small">仅描述原件身份；本交付不在此路径直接存放 ZIP。</span></dd></dl>
<section aria-labelledby="browser-heading"><h2 id="browser-heading">01 / 浏览器内校验还原</h2><p>在 HTTPS 静态站点中逐卷读取并校验，再核对完整 ZIP 的 SHA-256。取消或失败后，同一页面内已校验的卷可以继续使用；刷新页面则从头开始。不发送数据到第三方，也不使用持久存储。</p><div class="actions"><button id="start" disabled>校验并还原 ZIP</button><button id="cancel" disabled>取消</button><button id="clear" disabled>清除本页缓存</button></div><progress id="progress" max="{manifest['partCount']}" value="0" aria-label="已校验分卷数量"></progress><p id="status" role="status" aria-live="polite">尚未开始。若脚本不可用，请使用下面的离线还原。</p><a id="save" class="save" hidden>保存已校验 ZIP ↓</a><p class="small">本页不直接写入或覆写磁盘文件。保存时由浏览器选择名称或显示确认；下载完成情况请以浏览器为准。浏览器内重组需要约数倍于原包大小的可用内存。</p><noscript><p class="notice">JavaScript 已关闭。下方分卷、清单和 Python 标准库脚本仍可下载并离线还原。</p></noscript></section>
<section aria-labelledby="offline-heading"><h2 id="offline-heading">02 / 无脚本也能完整还原</h2><p>下载以下全部分卷、<a href="{manifest_href}" download="manifest.json">身份与顺序清单 manifest.json</a>以及<a href="{restore}" download="restore-source.py">Python 标准库还原脚本 restore-source.py</a>，放入同一个新文件夹。保留文件名，勿手工改顺序。请从该文件夹运行：</p><pre><code>python3 restore-source.py manifest.json --output {html.escape(archive['name'])}</code></pre><p class="small">Windows 可将命令开头换为 <code>py -3</code>。无需安装依赖或联网。脚本逐卷验证大小和 SHA-256，完整 SHA-256 正确后才发布输出；默认拒绝覆写已有文件。缺卷、破损、错序或完整哈希不符会失败，不会留下冒充成品的 ZIP。输出目录须支持硬链接，否则安全失败，不降级成覆写。</p><ol>{chunks}</ol><p>清单自身 SHA-256：<code>{manifest_sha}</code></p><p><a href="../../downloads/delivery-map.json">查看本交付的原路径与分卷映射</a></p></section><footer>原始模型、配置、生成源与历史检查保留原身份。分卷校验只证明字节还原，不代表新增几何、GPU 或真机验收。</footer></main></body></html>''', encoding='utf-8')
    return page


def split_archive(root, archive):
    raw = archive.read_bytes()
    folder = archive.parent / 'source-parts'
    folder.mkdir(exist_ok=True)
    parts = []
    for index, offset in enumerate(range(0, len(raw), PART_BYTES), 1):
        chunk = raw[offset:offset + PART_BYTES]
        name = f'{archive.name}.part{index:03d}'
        (folder / name).write_bytes(chunk)
        parts.append({'index': index, 'file': name, 'bytes': len(chunk), 'sha256': sha(chunk)})
    manifest = {'format': 'exact-zip-byte-parts-v1', 'archive': {'name': archive.name, 'originalPath': archive.relative_to(root).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)}, 'partCount': len(parts), 'partSizeLimitBytes': PART_BYTES, 'reconstruction': 'Concatenate verified parts in listed order, then verify the complete original SHA-256 before publishing output. No recompression.', 'parts': parts}
    dump(folder / 'manifest.json', manifest)
    rebuilt = b''.join((folder / p['file']).read_bytes() for p in parts)
    if rebuilt != raw or sha(rebuilt) != manifest['archive']['sha256']:
        raise ValueError('Byte identity failed; refusing removal of direct ZIP')
    archive.unlink()
    return folder, manifest


def patch_links(root, mappings):
    modified = []
    targets = {m['originalPath']: m for m in mappings}
    pattern = re.compile(r'<a\b(?P<attrs>[^>]*\bhref\s*=\s*["\'](?P<href>[^"\']+)["\'][^>]*)>(?P<body>.*?)</a>', re.I | re.S)
    for path in sorted(root.rglob('*.html')):
        text = path.read_text(encoding='utf-8')
        def replace(match):
            href = html.unescape(match['href'])
            uri = urlsplit(href)
            if uri.scheme or uri.netloc or uri.path.startswith('/'):
                return match[0]
            target = (path.parent / unquote(uri.path)).resolve()
            try:
                rel = target.relative_to(root.resolve()).as_posix()
            except ValueError:
                return match[0]
            if rel not in targets:
                return match[0]
            m = targets[rel]
            new_href = os.path.relpath(root / m['downloadPage'], path.parent).replace(os.sep, '/')
            attrs = match['attrs'].replace(match['href'], new_href, 1)
            attrs = re.sub(r'\s+download(?:\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27|[^\s>]+))?', '', attrs, flags=re.I)
            label = '分卷源包 / 校验并还原 ZIP'
            body = match['body']
            if '<small>' in body:
                body = f'<span>分卷源包<small>{m["partCount"]} 卷 / 校验并还原 ZIP · 完整原包</small></span><b>↗</b>'
            elif '<strong>' in body:
                body = f'<strong>{label}</strong><span>{m["partCount"]} 卷 · 模型、配置、生成脚本和检查记录</span><b aria-hidden="true">↗</b>'
            else:
                body = label
            return '<a' + attrs + '>' + body + '</a>'
        updated = pattern.sub(replace, text)
        if updated != text:
            path.write_text(updated, encoding='utf-8')
            modified.append(path.relative_to(root).as_posix())
    return modified


def apply_projection(root):
    root = Path(root).resolve()
    downloads = root / 'downloads'
    downloads.mkdir(exist_ok=True)
    for name in ASSET_NAMES:
        if not (downloads / name).is_file():
            raise ValueError('Missing delivery runtime asset: ' + name)
    for archive in sorted(root.rglob('*.zip')):
        if archive.stat().st_size > RAW_SAFE_LIMIT:
            split_archive(root, archive)
    mappings = []
    for path in sorted(root.rglob('source-parts/manifest.json')):
        manifest = json.loads(path.read_text(encoding='utf-8'))
        # Reuse the same strict offline validator; never bless a merely named part.
        import runpy
        validator = runpy.run_path(str(downloads / 'restore-source.py'))['validate_manifest']
        archive, parts = validator(manifest)
        raw = b''.join((path.parent / p['file']).read_bytes() for p in parts)
        for p in parts:
            chunk = (path.parent / p['file']).read_bytes()
            if len(chunk) != p['bytes'] or sha(chunk) != p['sha256']:
                raise ValueError('Part changed: ' + p['file'])
        if len(raw) != archive['bytes'] or sha(raw) != archive['sha256']:
            raise ValueError('Full archive identity mismatch')
        if (root / archive['originalPath']).exists():
            raise ValueError('Projected original ZIP path must be absent')
        relocated = (path.parent.parent / Path(archive['originalPath']).name).relative_to(root).as_posix()
        is_history = relocated != archive['originalPath']
        page = path.parent.parent / 'source-download.html' if is_history else write_page(root, path.parent, manifest)
        if not page.is_file():raise ValueError('Historical download page missing')
        mapped_archive = {**archive, 'originalPath':relocated}
        if is_history:mapped_archive['originalSnapshotPath']=archive['originalPath']
        mappings.append({**mapped_archive, 'originalPathPresentInThisDelivery': False, 'downloadPage': page.relative_to(root).as_posix(), 'manifest': path.relative_to(root).as_posix(), 'manifestSha256': sha(path.read_bytes()), 'partCount': len(parts), 'parts': [{**p, 'path': (path.parent / p['file']).relative_to(root).as_posix()} for p in parts]})
    patch_links(root, mappings)
    delivery = {'format': 'github-exact-zip-delivery-map-v1', 'projection': True, 'requestLimitBytes': REQUEST_LIMIT, 'requestMetadataReserveBytes': REQUEST_RESERVE, 'rawArchiveSafeLimitBytes': RAW_SAFE_LIMIT, 'partSizeLimitBytes': PART_BYTES, 'note': 'Only oversized source ZIPs are delivered as exact byte parts. Original source manifests, frozen hash lists and historical reports describe the original full snapshot, not current direct-path availability. Use this map for this delivery. Other models, images, source code and dependencies retain their original bytes.', 'archives': mappings}
    dump(downloads / 'delivery-map.json', delivery)
    return delivery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', required=True, help='Full static source directory (read only)')
    parser.add_argument('--output-dir', required=True, help='New, nonexistent static projection directory')
    args = parser.parse_args()
    source = Path(args.source_dir).resolve()
    output = Path(args.output_dir).resolve()
    if not source.is_dir() or output.exists() or source == output or source in output.parents or output in source.parents:
        raise SystemExit('Require distinct, non-nested source directory and nonexistent output directory')
    here = Path(__file__).resolve().parent
    asset_root = here / 'dist' / 'downloads'
    if not asset_root.is_dir():
        asset_root = (here.parent / 'dist' / 'downloads') if (here.parent / 'dist' / 'downloads').is_dir() else here.parents[1] / 'docs' / 'downloads'
    for name in ASSET_NAMES:
        if not (asset_root / name).is_file():
            raise SystemExit('Delivery assets must accompany this tool in the published static downloads directory')
    shutil.copytree(source, output)
    (output / 'downloads').mkdir(exist_ok=True)
    for name in ASSET_NAMES:
        shutil.copyfile(asset_root / name, output / 'downloads' / name)
    result = apply_projection(output)
    print(f'Projected {len(result["archives"])} oversized source archives; original input untouched.')


if __name__ == '__main__':
    main()
