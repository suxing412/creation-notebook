"""Build responsive catalogue WebP images from the four entrance pages.

Requires Pillow. The default command writes images and their manifest only.
Use --write-pages to also update img elements, --dry-run to measure the result
without writing, or --check to verify the saved assets and page references.
Original images are retained in data-source for reproducible regeneration.
"""
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import json
import os
import re

from PIL import Image, ImageOps, __version__ as PILLOW_VERSION


SITE = Path(__file__).resolve().parents[2] / 'docs'
OUTPUT = SITE / 'thumbnails'
MANIFEST = OUTPUT / 'manifest.json'
PAGES = (
    'index.html',
    'model-library/index.html',
    'web-library/index.html',
    'space-library/index.html',
)
WIDTHS = (300, 600)
MAX_IMAGE_BYTES = 80_000
MAX_MODEL_PAGE_BYTES = 3_000_000
RECIPE = 'webp-lanczos-q82-to62-method6-v1'
IMAGE_TAG = re.compile(r'<img\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>', re.IGNORECASE)

# Match the layout's single-column phone, two-column tablet, and desktop cards.
LIBRARY_SIZES = (
    '(max-width: 480px) calc(100vw - 60px), '
    '(max-width: 850px) calc((100vw - 88px) / 2), '
    '(max-width: 1320px) calc((100vw - 144px) / 3), 385px'
)
HOME_CARD_SIZES = (
    '(max-width: 620px) calc((100vw - 68px) / 2), '
    '(max-width: 1320px) calc((100vw - 144px) / 3), 385px'
)
HOME_HERO_SIZES = (
    '(max-width: 620px) min(370px, calc(90vw - 64px)), '
    '(max-width: 1320px) calc((100vw - 160px) / 2), 510px'
)
HOME_PROJECT_SIZES = (
    '(max-width: 620px) calc(100vw - 110px), '
    '(max-width: 1320px) calc((100vw - 260px) / 2), 510px'
)


class PageImages(HTMLParser):
    """Read image attributes and their layout without rewriting the document."""
    VOID_ELEMENTS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                     'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []
        self.parents = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        layout = self.parents[-1][1] if self.parents else 'card'
        classes = attributes.get('class', '').split()
        if 'hero-photo' in classes:
            layout = 'hero'
        elif 'project-sheet' in classes:
            layout = 'project'
        if tag == 'img':
            self.images.append({'attributes': attributes, 'layout': layout})
        if tag not in self.VOID_ELEMENTS:
            self.parents.append((tag, layout))

    def handle_endtag(self, tag):
        for index in range(len(self.parents) - 1, -1, -1):
            if self.parents[index][0] == tag:
                del self.parents[index:]
                break


def local_path(page, url):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        raise ValueError(f'{page}: expected a local image URL, got {url!r}')
    path = (page.parent / unquote(parsed.path)).resolve()
    if not path.is_relative_to(SITE):
        raise ValueError(f'{page}: image escapes docs: {url}')
    if not path.is_file():
        raise ValueError(f'{page}: image is missing: {url}')
    return path


def relative_url(path, page):
    return Path(os.path.relpath(path, page.parent)).as_posix()


def read_pages():
    pages = {}
    for relative in PAGES:
        path = SITE / relative
        content = path.read_text(encoding='utf-8')
        parser = PageImages()
        parser.feed(content)
        images = parser.images
        if len(images) != len(IMAGE_TAG.findall(content)):
            raise ValueError(f'{relative}: unsupported img markup; review before generation')
        for image in images:
            attributes = image['attributes']
            source_url = attributes.get('data-source', attributes.get('src', ''))
            image['source'] = local_path(path, source_url)
        pages[relative] = {'content': content, 'images': images}
    return pages


def encode_webp(image):
    for quality in range(82, 61, -4):
        buffer = BytesIO()
        image.save(buffer, format='WEBP', quality=quality, method=6)
        encoded = buffer.getvalue()
        if len(encoded) <= MAX_IMAGE_BYTES:
            return encoded, quality
    raise ValueError(f'Cannot meet the {MAX_IMAGE_BYTES}-byte image budget')


def make_asset(source):
    source_bytes = source.read_bytes()
    source_hash = sha256(source_bytes).hexdigest()
    identity = sha256(source_bytes + RECIPE.encode('ascii')).hexdigest()[:12]
    stem = re.sub(r'[^a-zA-Z0-9_-]', '-', source.stem)[:45].strip('-') or 'image'
    variants = []
    outputs = {}
    with Image.open(BytesIO(source_bytes)) as opened:
        image = ImageOps.exif_transpose(opened)
        has_alpha = 'A' in image.getbands() or 'transparency' in image.info
        image = image.convert('RGBA' if has_alpha else 'RGB')
        original_width, original_height = image.size
        for width in sorted({min(width, original_width) for width in WIDTHS}):
            height = max(1, round(original_height * width / original_width))
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            encoded, quality = encode_webp(resized)
            path = OUTPUT / f'{stem}-{identity}-{width}.webp'
            outputs[path] = encoded
            variants.append({
                'path': path.relative_to(SITE).as_posix(),
                'width': width,
                'height': height,
                'bytes': len(encoded),
                'sha256': sha256(encoded).hexdigest(),
                'quality': quality,
            })
    return {
        'source_sha256': source_hash,
        'source_bytes': len(source_bytes),
        'source_width': original_width,
        'source_height': original_height,
        'variants': variants,
    }, outputs


def image_sizes(page, layout):
    if page != 'index.html':
        return LIBRARY_SIZES
    if layout == 'hero':
        return HOME_HERO_SIZES
    if layout == 'project':
        return HOME_PROJECT_SIZES
    return HOME_CARD_SIZES


def responsive_attributes(page_name, image, asset):
    page = SITE / page_name
    attributes = image['attributes'].copy()
    variants = asset['variants']
    largest = variants[-1]
    attributes.update({
        'src': relative_url(SITE / largest['path'], page),
        'srcset': ', '.join(
            f"{relative_url(SITE / variant['path'], page)} {variant['width']}w"
            for variant in variants
        ),
        'sizes': image_sizes(page_name, image['layout']),
        'width': str(largest['width']),
        'height': str(largest['height']),
        'decoding': 'async',
        'data-source': relative_url(image['source'], page),
    })
    return attributes


def render_image(attributes):
    parts = [name if value is None else f'{name}="{escape(value, quote=True)}"'
             for name, value in attributes.items()]
    return '<img ' + ' '.join(parts) + '>'


def page_summary(page, assets):
    sources = [image['source'].relative_to(SITE).as_posix() for image in page['images']]
    unique_sources = sorted(set(sources))
    return {
        'image_count': len(sources),
        'source_bytes': sum(assets[source]['source_bytes'] for source in unique_sources),
        # Conservative image-only budget: load the largest candidate for every image.
        'largest_candidate_bytes': sum(
            assets[source]['variants'][-1]['bytes'] for source in unique_sources
        ),
        'sources': sources,
    }


def write_atomic(path, data):
    if path.exists() and path.read_bytes() == data:
        return
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def build(pages, write_pages, dry_run):
    assets = {}
    outputs = {}
    sources = sorted({image['source'] for page in pages.values() for image in page['images']})
    for source in sources:
        key = source.relative_to(SITE).as_posix()
        assets[key], encoded = make_asset(source)
        outputs.update(encoded)
    summary = {name: page_summary(page, assets) for name, page in pages.items()}
    if summary['model-library/index.html']['largest_candidate_bytes'] > MAX_MODEL_PAGE_BYTES:
        raise ValueError('Model library images exceed the 3 MB page budget')
    manifest = {
        'recipe': RECIPE,
        'pillow_version': PILLOW_VERSION,
        'widths': list(WIDTHS),
        'max_image_bytes': MAX_IMAGE_BYTES,
        'assets': assets,
        'pages': summary,
    }
    if dry_run:
        return {'mode': 'dry-run', 'unique_images': len(assets), 'pages': summary}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path, encoded in outputs.items():
        write_atomic(path, encoded)
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    write_atomic(MANIFEST, manifest_bytes)
    if write_pages:
        # Check all snapshots before editing any page, so other ongoing work is retained.
        for name, page in pages.items():
            if (SITE / name).read_text(encoding='utf-8') != page['content']:
                raise ValueError(f'{name} changed during generation; rerun the command')
        for name, page in pages.items():
            replacements = []
            for image in page['images']:
                asset = assets[image['source'].relative_to(SITE).as_posix()]
                replacements.append(render_image(responsive_attributes(name, image, asset)))
            replacement_iterator = iter(replacements)
            updated = IMAGE_TAG.sub(lambda match: next(replacement_iterator), page['content'])
            write_atomic(SITE / name, updated.encode('utf-8'))
    return {'mode': 'write-pages' if write_pages else 'assets-only',
            'unique_images': len(assets), 'pages': summary}


def check(pages):
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if manifest['recipe'] != RECIPE or manifest['widths'] != list(WIDTHS):
        raise ValueError('Thumbnail recipe changed; regenerate thumbnails')
    assets = manifest['assets']
    current_sources = {
        image['source'].relative_to(SITE).as_posix()
        for page in pages.values() for image in page['images']
    }
    if set(assets) != current_sources:
        raise ValueError('Image sources changed; regenerate the thumbnail manifest')
    for source, asset in assets.items():
        source_bytes = (SITE / source).read_bytes()
        if sha256(source_bytes).hexdigest() != asset['source_sha256']:
            raise ValueError(f'{source} changed; regenerate its thumbnails')
        with Image.open(BytesIO(source_bytes)) as opened:
            source_width, source_height = ImageOps.exif_transpose(opened).size
        if (source_width, source_height, len(source_bytes)) != (
            asset['source_width'], asset['source_height'], asset['source_bytes']
        ):
            raise ValueError(f'{source}: source dimensions or byte count mismatch')
        expected_widths = sorted({min(width, source_width) for width in WIDTHS})
        if [variant['width'] for variant in asset['variants']] != expected_widths:
            raise ValueError(f'{source}: responsive width candidates mismatch')
        for variant in asset['variants']:
            expected_height = max(1, round(source_height * variant['width'] / source_width))
            if variant['height'] != expected_height:
                raise ValueError(f'{source}: thumbnail aspect ratio mismatch')
            path = local_path(SITE / 'index.html', variant['path'])
            content = path.read_bytes()
            if len(content) != variant['bytes'] or sha256(content).hexdigest() != variant['sha256']:
                raise ValueError(f'{variant["path"]}: byte count or SHA-256 mismatch')
            if len(content) > MAX_IMAGE_BYTES:
                raise ValueError(f'{variant["path"]}: exceeds image budget')
            with Image.open(BytesIO(content)) as image:
                if image.format != 'WEBP' or image.size != (variant['width'], variant['height']):
                    raise ValueError(f'{variant["path"]}: format or dimensions mismatch')
    for name, page in pages.items():
        for index, image in enumerate(page['images']):
            asset = assets[image['source'].relative_to(SITE).as_posix()]
            expected = responsive_attributes(name, image, asset)
            for attribute in ('src', 'srcset', 'sizes', 'width', 'height', 'decoding', 'data-source'):
                if image['attributes'].get(attribute) != expected[attribute]:
                    raise ValueError(f'{name}, image {index + 1}: incorrect {attribute}')
        if page_summary(page, assets) != manifest['pages'][name]:
            raise ValueError(f'{name}: page budget manifest is stale')
    model_bytes = manifest['pages']['model-library/index.html']['largest_candidate_bytes']
    if model_bytes > MAX_MODEL_PAGE_BYTES:
        raise ValueError('Model library images exceed the 3 MB page budget')
    return {'mode': 'check', 'passed': True, 'unique_images': len(assets),
            'pages': manifest['pages'],
            'limits': 'Image files and responsive markup only. Browser transfer totals need browser verification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write-pages', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        pages = read_pages()
        result = check(pages) if args.check else build(pages, args.write_pages, args.dry_run)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Thumbnail check failed: {error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
