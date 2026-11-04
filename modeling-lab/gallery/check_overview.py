"""Read-only static checks for the current notebook, or the legacy overview."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--legacy', action='store_true', help='Check the old overview structure; never rebuild it.')
parser.add_argument('--baseline', type=Path, help='Optional prior site snapshot for file preservation checks.')
parser.add_argument('--report', type=Path, help='Optionally write a JSON report; omitted means no files are written.')
parser.add_argument('--allow-changed', action='append', default=['index.html', 'manifest.json'], help='Baseline-relative file allowed to change; repeat per file.')
args = parser.parse_args()
SITE = ROOT.parents[1] / 'docs'
if args.legacy:
    SITE = next((p for p in (ROOT / 'dist', ROOT.parent / 'dist') if p.is_dir()), SITE)
if args.baseline is not None and not args.baseline.is_dir():
    parser.error('--baseline must be an existing static snapshot directory')


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = []
        self.cards = []
        self.works = []
        self.picks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.urls.extend(attrs[k] for k in ('href', 'src') if k in attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'article' and 'data-search' in attrs:
            self.cards.append(attrs)
        if tag == 'article' and 'data-id' in attrs:
            self.works.append(attrs['data-id'])
        if tag == 'button' and 'data-select' in attrs:
            self.picks.append(attrs['data-select'])


errors = []
references = 0
external = 0
pages = {}
entries = ['index.html'] if args.legacy else ['index.html', 'model-library/index.html', 'web-library/index.html', 'space-library/index.html']
for entry in entries:
    path = SITE / entry
    if not path.is_file():
        errors.append(f'{entry}: entry page missing')
        continue
    page = Page()
    page.feed(path.read_text(encoding='utf-8'))
    pages[entry] = page
    if len(page.ids) != len(set(page.ids)):
        errors.append(f'{entry}: duplicate HTML id')
    for url in page.urls:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc:
            external += 1
            continue
        references += 1
        target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
        if not target.is_relative_to(SITE.resolve()):
            errors.append(f'{entry}: reference escapes site: {url}')
            continue
        if target.is_dir():
            target /= 'index.html'
        if not target.is_file():
            errors.append(f'{entry}: missing local reference: {url}')
        elif not parsed.path and parsed.fragment and unquote(parsed.fragment) not in page.ids:
            errors.append(f'{entry}: missing page anchor: {url}')

counts = {}
if args.legacy:
    catalog = json.loads((SITE / 'catalog.json').read_text(encoding='utf-8'))
    page = pages.get('index.html')
    ids = [item['id'] for item in catalog]
    if page and (len(ids) != len(set(ids)) or set(page.works) != set(ids) or len(page.works) != len(ids) or sorted(page.picks) != sorted(ids * 2)):
        errors.append('Legacy overview/catalog parity mismatch')
    policy = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['designPolicy']
    historical = [item for item in catalog if item['kind'] == 'fusion']
    prototypes = [item for item in catalog if item['kind'] == 'space-design']
    if policy['acceptedSpatialWorks'] != 0 or len(historical) != policy['historicalSpatialExperiments'] or len(prototypes) != policy['spatialPrototypes']:
        errors.append('Legacy spatial counts/acceptance policy mismatch')
    if any(item.get('designStatus') != '\u6309\u65b0\u8bbe\u8ba1\u8981\u6c42\u5f85\u91cd\u505a' or item['publication'] != 'verified' for item in historical):
        errors.append('Legacy historical publication/design status mismatch')
    if any(item['countsAsAcceptedSpatialDesign'] is not False or item['acceptance'] != 'prototype-pending-realtime-and-user-review' for item in prototypes):
        errors.append('Legacy prototype acceptance policy mismatch')
    counts['legacyItems'] = len(ids)
else:
    index = json.loads((SITE / 'notebook-index.json').read_text(encoding='utf-8'))
    for entry, key in [('model-library/index.html', 'models'), ('web-library/index.html', 'websites'), ('space-library/index.html', 'spaces')]:
        page = pages.get(entry)
        if page is None:
            continue
        counts[key] = len(page.cards)
        if counts[key] != len(index[key]):
            errors.append(f'{entry}: {counts[key]} cards do not match {len(index[key])} index entries')
        required = {'search', 'kind', 'matches', 'empty'}
        if not required.issubset(page.ids):
            errors.append(f'{entry}: missing filter controls {sorted(required - set(page.ids))}')
        if any('data-kind' not in card for card in page.cards):
            errors.append(f'{entry}: filter card missing data-kind')

changed = []
if args.baseline is not None:
    for old in args.baseline.rglob('*'):
        if not old.is_file():
            continue
        relative = old.relative_to(args.baseline)
        current = SITE / relative
        if not current.is_file() or hashlib.sha256(old.read_bytes()).digest() != hashlib.sha256(current.read_bytes()).digest():
            changed.append(relative.as_posix())
    unexpected = sorted(set(changed) - set(args.allow_changed))
    if unexpected:
        errors.append(f'Unexpected baseline changes: {unexpected}')

result = {
    'passed': not errors,
    'mode': 'legacy-read-only' if args.legacy else 'current-read-only',
    'entryPages': entries,
    'counts': counts,
    'localReferencesChecked': references,
    'externalReferencesNotFetched': external,
    'baselineChanges': changed,
    'assetPreservation': 'not_checked: no baseline supplied' if args.baseline is None else ('passed' if not (set(changed) - set(args.allow_changed)) else 'failed'),
    'limits': 'Entry-page structure and local file references only. No rebuild, remote URL, browser, GPU, phone, or design acceptance checks.',
    'errors': errors,
}
if args.report:
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['passed'] else 1)
