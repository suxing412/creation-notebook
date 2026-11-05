"""Build the asset library from asset cards.

Every digital asset is described by one card, docs/**/<id>.asset.json (format: docs/asset-spec/README.md).
This script finds every card, checks it against docs/asset-spec/categories.json, reads GLB stats, makes WebP
previews, and writes:
  lab/data/assets.json   what the site shows (cards with errors and drafts are left out)
  lab/data/report.json   the check result for every card (the site's 规范 page shows it)

Run from anywhere:
  python -I lab/tools/build_assets.py           build, print a summary
  python -I lab/tools/build_assets.py --check   same, but exit 1 if any card has an error (use before pushing / in CI)
"""
import json, os, re, glob, subprocess, sys, datetime
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DOCS = os.path.join(ROOT, 'docs')
LAB = os.path.join(ROOT, 'lab')
MEDIA = os.path.join(LAB, 'media')
SPEC = json.load(open(os.path.join(DOCS, 'asset-spec', 'categories.json'), encoding='utf-8'))
LIM = SPEC['limits']
CATS = {c['id']: c for c in SPEC['categories']}
STATUS = {s['id']: s for s in SPEC['statuses']}
sys.path.insert(0, HERE)
from glb_audit import audit  # noqa: E402

CACHE_PATH = os.path.join(LAB, 'data', 'glb-cache.json')
cache = json.load(open(CACHE_PATH, encoding='utf-8')) if os.path.exists(CACHE_PATH) else {}
FIELDS = {'spec', 'id', 'category', 'kind', 'title', 'english', 'summary', 'status', 'statusNote', 'cover', 'coverAlt', 'coverIsShot',
          'gallery', 'files', 'page', 'notes', 'stats', 'related', 'legacyPath', '$schema',
          'scene', 'chapters', 'progress', 'evidence', 'journal', 'members'}
PROJ = SPEC.get('project', {})
NOTE_KEYS = ('已完成的检查', '限制与待解决')


def rel_docs(card_dir, p):
    """card-relative path -> docs-relative path (None if it leaves docs/)."""
    full = os.path.normpath(os.path.join(card_dir, p))
    r = os.path.relpath(full, DOCS).replace('\\', '/')
    return None if r.startswith('..') else r


def thumb(rel, width):
    src = os.path.join(DOCS, rel)
    name = re.sub(r'[^a-zA-Z0-9]+', '-', rel.rsplit('.', 1)[0]).strip('-') + f'-{width}.webp'
    out = os.path.join(MEDIA, name)
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        im = Image.open(src)
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(out, 'WEBP', quality=80, method=6)
    w, h = Image.open(out).size
    return {'src': 'media/' + name, 'w': w, 'h': h}


def pic(rel):
    return {'small': thumb(rel, 720), 'large': thumb(rel, 1800), 'original': '../docs/' + rel}


def glb_info(rel):
    full = os.path.join(DOCS, rel)
    st = os.stat(full)
    key = f'{rel}:{st.st_size}:{int(st.st_mtime)}'
    if key not in cache:
        a = audit(full)
        cache[key] = {k: a.get(k) for k in ('bytes', 'triangles', 'vertices', 'primitives', 'materials', 'images', 'size', 'primsNoUV')}
    return cache[key]


def updated(rels):
    rels = [r for r in rels if r]
    if not rels:
        return None
    out = subprocess.run(['git', '-C', ROOT, 'log', '-1', '--format=%cI', '--', *['docs/' + r for r in rels]], capture_output=True, text=True).stdout.strip()
    return out or None


def check_card(path):
    """Return (asset or None, errors, warnings)."""
    E, W = [], []
    card_dir = os.path.dirname(path)
    card_rel = os.path.relpath(path, DOCS).replace('\\', '/')
    try:
        c = json.load(open(path, encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        return None, [f'不是合法的 JSON：{e}'], []
    if not isinstance(c, dict):
        return None, ['卡片必须是一个 JSON 对象'], []
    for k in c:
        if k not in FIELDS:
            W.append(f'未知字段「{k}」，会被忽略')
    # identity
    if c.get('spec') != SPEC['spec']:
        E.append(f'spec 必须是 {SPEC["spec"]}')
    cid = c.get('id', '')
    if not re.fullmatch(LIM['id'], str(cid)):
        E.append('id 只能用小写字母、数字和连字符，2–49 位')
    if os.path.basename(path) != f'{cid}.asset.json':
        E.append(f'文件名必须是「{cid}.asset.json」')
    cat = CATS.get(c.get('category'))
    if not cat:
        E.append(f'category 必须是 {"、".join(CATS)} 之一')
    if c.get('status') not in STATUS:
        E.append(f'status 必须是 {"、".join(STATUS)} 之一')
    # text
    title, summary = str(c.get('title') or ''), str(c.get('summary') or '')
    if not title:
        E.append('缺 title')
    elif len(title) > LIM['titleMax']:
        E.append(f'title 超过 {LIM["titleMax"]} 字')
    if not summary:
        E.append('缺 summary（一句话介绍）')
    elif len(summary) > LIM['summaryMax']:
        E.append(f'summary 超过 {LIM["summaryMax"]} 字（现在 {len(summary)}）')
    elif len(summary) > LIM['summaryWarn']:
        W.append(f'summary 偏长（{len(summary)} 字，建议 ≤ {LIM["summaryWarn"]}）')
    if not c.get('kind'):
        E.append('缺 kind（类型）')
    elif cat and c['kind'] not in cat['kinds']:
        W.append(f'kind「{c["kind"]}」不在分类表里（{"、".join(cat["kinds"])}）；是新类型就先加进分类表')
    if not c.get('english'):
        W.append('缺 english（英文名）')
    if not c.get('coverAlt'):
        W.append('缺 coverAlt（封面图的文字描述）')

    # images
    def image(p, what):
        r = rel_docs(card_dir, p) if isinstance(p, str) else None
        if not r:
            E.append(f'{what}路径无效或跑出了 docs/：{p}')
            return None
        if not os.path.isfile(os.path.join(DOCS, r)):
            E.append(f'{what}找不到：{p}')
            return None
        if os.path.splitext(r)[1].lower() not in LIM['imageTypes']:
            E.append(f'{what}只能是 {" / ".join(LIM["imageTypes"])}：{p}')
            return None
        return r
    cover = image(c['cover'], '封面') if c.get('cover') else None
    if not c.get('cover'):
        E.append('缺 cover（封面图）')
    if cover:
        w = Image.open(os.path.join(DOCS, cover)).width
        if w < LIM['coverMinWidth']:
            E.append(f'封面太小：宽 {w}px，至少 {LIM["coverMinWidth"]}px')
        elif w < LIM['coverWarnWidth']:
            W.append(f'封面宽 {w}px，建议 ≥ {LIM["coverWarnWidth"]}px')
    gal = c.get('gallery') or []
    if not isinstance(gal, list):
        E.append('gallery 必须是列表')
        gal = []
    if len(gal) > LIM['galleryMax']:
        E.append(f'gallery 最多 {LIM["galleryMax"]} 张')
    gallery = [r for r in (image(p, '图集图片') for p in gal) if r and r != cover]
    if not gal and c.get('category') in ('models', 'spaces', 'projects'):
        W.append('没有 gallery（图集），详情页只有一张封面')

    # files
    files, raw = [], c.get('files', [])
    if raw == 'auto':
        found = sorted(glob.glob(os.path.join(card_dir, '**', '*.glb'), recursive=True))
        raw = [{'path': os.path.relpath(f, card_dir).replace('\\', '/')} for f in found]
    if not isinstance(raw, list):
        E.append('files 必须是列表，或写 "auto"（自动收录卡片所在目录下全部 GLB）')
        raw = []
    for f in raw:
        p = f.get('path') if isinstance(f, dict) else None
        r = rel_docs(card_dir, p) if p else None
        if not r or not os.path.isfile(os.path.join(DOCS, r)):
            E.append(f'模型文件找不到：{p}')
            continue
        if not r.lower().endswith('.glb'):
            E.append(f'模型文件只收 .glb：{p}')
            continue
        try:
            info = glb_info(r)
        except Exception as e:  # noqa: BLE001
            E.append(f'GLB 读不出来：{p}（{e}）')
            continue
        mb = (info.get('bytes') or 0) / 1e6
        if mb > LIM['glbMaxMB']:
            E.append(f'GLB 超过 {LIM["glbMaxMB"]} MB：{p}（{mb:.1f} MB）')
        elif mb > LIM['glbWarnMB']:
            W.append(f'GLB 偏大：{p}（{mb:.1f} MB，建议 ≤ {LIM["glbWarnMB"]} MB）')
        tri = info.get('triangles') or 0
        if tri > LIM['trianglesMax']:
            E.append(f'面数超过 {LIM["trianglesMax"]:,}：{p}（{tri:,}）')
        elif tri > LIM['trianglesWarn']:
            W.append(f'面数偏高：{p}（{tri:,}）')
        files.append({'label': (f.get('label') if isinstance(f, dict) else None) or os.path.basename(r), 'path': r, 'url': '../docs/' + r, 'format': 'GLB', **info})

    # page + links
    page = None
    if c.get('page'):
        page = rel_docs(card_dir, c['page'])
        if not page or not os.path.exists(os.path.join(DOCS, page)):
            E.append(f'page 找不到：{c["page"]}')
            page = None
    if cat:
        if 'files' in cat.get('requires', []) and not files and not any('模型文件' in e or 'GLB' in e for e in E):
            E.append('这个分类至少要有一个 GLB（files）')
        if 'page' in cat.get('requires', []) and not c.get('page'):
            E.append('这个分类必须有 page（入口网页）')
    if 'links' in c:
        W.append('links 已停用：详情页就是最终查看页，不再放外链按钮；请删掉这个字段')
    notes = c.get('notes') or {}
    if not isinstance(notes, dict):
        E.append('notes 必须是 {"标题": "内容"}')
        notes = {}
    for k in NOTE_KEYS:
        if not notes.get(k):
            W.append(f'notes 里缺「{k}」')

    # large projects: live scene, chapters, progress, evidence levels, journal, member assets
    proj = {}
    if c.get('category') == 'projects' or any(k in c for k in ('scene', 'chapters', 'progress', 'journal')):
        req = cat.get('requires', []) if cat else []
        if c.get('scene'):
            r = rel_docs(card_dir, c['scene'])
            if not r or not os.path.isfile(os.path.join(DOCS, r)) or not r.endswith('.mjs'):
                E.append(f'scene 必须是存在的 .mjs 场景模块：{c["scene"]}')
            else:
                proj['scene'] = '../docs/' + r
        elif 'scene' in req:
            E.append('大型项目必须有 scene（实时场景模块，见规范「场景约定」）')
        ps = PROJ.get('progressStatuses', [])
        chapters, ch_ids = [], set()
        raw_ch = c.get('chapters') or []
        if not isinstance(raw_ch, list):
            E.append('chapters 必须是列表')
            raw_ch = []
        if not raw_ch and 'chapters' in req:
            E.append('大型项目至少要有一个章节（chapters）')
        if len(raw_ch) > PROJ.get('chaptersMax', 12):
            E.append(f'chapters 最多 {PROJ.get("chaptersMax", 12)} 章')
        for i, ch in enumerate(raw_ch, 1):
            if not isinstance(ch, dict):
                E.append(f'第 {i} 章必须是对象')
                continue
            for k in ('id', 'title', 'status', 'line', 'image'):
                if not ch.get(k):
                    E.append(f'第 {i} 章缺 {k}')
            if ch.get('id') in ch_ids:
                E.append(f'章节 id「{ch.get("id")}」重复')
            ch_ids.add(ch.get('id'))
            if ch.get('status') and ch['status'] not in ps:
                E.append(f'第 {i} 章 status 必须是 {"、".join(ps)} 之一')
            im = image(ch['image'], f'第 {i} 章配图') if ch.get('image') else None
            if im:
                w = Image.open(os.path.join(DOCS, im)).width
                if w < PROJ.get('chapterImageMinWidth', 600):
                    W.append(f'第 {i} 章配图宽 {w}px，建议 ≥ {PROJ.get("chapterImageMinWidth", 600)}px')
            if not ch.get('text'):
                W.append(f'第 {i} 章没有 text（正文）')
            item = {k: ch.get(k) for k in ('id', 'title', 'status', 'statusNote', 'line', 'text', 'focus')}
            item['image'] = pic(im) if im else None
            chapters.append(item)
        progress = []
        for i, pr in enumerate(c.get('progress') or [], 1):
            if not isinstance(pr, dict) or not pr.get('title') or not pr.get('status'):
                E.append(f'progress 第 {i} 项至少要有 title 和 status')
                continue
            if pr['status'] not in ps:
                E.append(f'progress 第 {i} 项 status 必须是 {"、".join(ps)} 之一')
            if pr.get('chapter') and pr['chapter'] not in ch_ids:
                W.append(f'progress 第 {i} 项的 chapter「{pr["chapter"]}」不在 chapters 里')
            if 'count' in pr and not isinstance(pr['count'], (int, float)):
                E.append(f'progress 第 {i} 项 count 必须是数字')
            progress.append({k: pr.get(k) for k in ('title', 'status', 'count', 'unit', 'chapter', 'focus', 'note')})
        if c.get('category') == 'projects' and not progress:
            W.append('没有 progress（建设进度）')
        lv = PROJ.get('evidenceLevels', [])
        evidence = []
        for i, ev in enumerate(c.get('evidence') or [], 1):
            if not isinstance(ev, dict) or ev.get('level') not in lv or not ev.get('text'):
                E.append(f'evidence 第 {i} 项要写 level（{"、".join(lv)}）和 text')
                continue
            evidence.append({'level': ev['level'], 'text': ev['text']})
        journal = []
        for i, j in enumerate(c.get('journal') or [], 1):
            if not isinstance(j, dict) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(j.get('date', ''))) or not j.get('title'):
                E.append(f'journal 第 {i} 条要有 date（YYYY-MM-DD）和 title')
                continue
            journal.append({k: j.get(k) for k in ('date', 'batch', 'title', 'text')})
        journal.sort(key=lambda j: j['date'], reverse=True)
        if c.get('category') == 'projects' and not journal:
            W.append('没有 journal（研究手记 / 建设记录）')
        proj.update({'chapters': chapters, 'progress': progress, 'evidence': evidence, 'journal': journal, 'members': list(c.get('members') or [])})
    # placement
    std = re.fullmatch(r'library/([a-z0-9-]+)/([a-z0-9-]+)/[^/]+', card_rel)
    if not c.get('legacyPath') and (not std or std.group(1) != c.get('category') or std.group(2) != cid):
        W.append(f'新资产请放在 docs/library/{c.get("category")}/{cid}/ 下')
    if E:
        return None, E, W
    stats = dict(c.get('stats') or {})
    if 'glbCount' in cat.get('autoStats', []):
        stats = {'模型文件': len(glob.glob(os.path.join(card_dir, '**', '*.glb'), recursive=True)), **stats}
    st = c['status'] + (' · ' + c['statusNote'] if c.get('statusNote') else '')
    asset = {
        'id': cid, 'category': c['category'], 'kind': c['kind'], 'title': title, 'english': c.get('english', ''),
        'summary': summary, 'alt': c.get('coverAlt', ''), 'cover': pic(cover), 'coverIsShot': bool(c.get('coverIsShot')),
        'gallery': [pic(r) for r in gallery], 'files': files, 'page': '../docs/' + page if page else None, 'notes': notes, 'stats': stats,
        'state': c['status'], 'status': st, 'public': STATUS[c['status']]['public'],
        'updated': updated([cover, page, *gallery, *[f['path'] for f in files]]), 'related': list(c.get('related') or []),
        'card': card_rel,
        **proj,
    }
    asset['bytes'] = sum(f.get('bytes') or 0 for f in files)
    asset['triangles'] = max([f.get('triangles') or 0 for f in files] or [0])
    asset['textured'] = any((f.get('images') or 0) > 0 for f in files)
    return asset, E, W


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.makedirs(MEDIA, exist_ok=True)
    cards = sorted(glob.glob(os.path.join(DOCS, '**', '*.asset.json'), recursive=True))
    items, assets, seen = [], [], {}
    for path in cards:
        rel = os.path.relpath(path, DOCS).replace('\\', '/')
        a, E, W = check_card(path)
        try:
            raw = json.load(open(path, encoding='utf-8'))
            raw = raw if isinstance(raw, dict) else {}
        except Exception:  # noqa: BLE001
            raw = {}
        cid = raw.get('id')
        if cid and cid in seen:
            E.append(f'id「{cid}」和 {seen[cid]} 重复')
            a = None
        if cid:
            seen.setdefault(cid, rel)
        items.append({'card': rel, 'id': cid, 'title': raw.get('title'), 'category': raw.get('category'), 'status': raw.get('status'),
                      'errors': E, 'warnings': W})
        if a:
            assets.append(a)
    ids = {a['id'] for a in assets}
    by_card = {it['card']: it for it in items}
    for a in assets:
        missing = [r for r in a['related'] if r not in ids]
        if missing:
            by_card[a['card']]['warnings'].append('related 里有不存在的 id：' + '、'.join(missing))
        a['related'] = [r for r in a['related'] if r in ids]
        if 'members' in a:
            gone = [r for r in a['members'] if r not in ids]
            if gone:
                by_card[a['card']]['warnings'].append('members 里有不存在的 id：' + '、'.join(gone))
            a['members'] = [r for r in a['members'] if r in ids]
    # GLBs dropped in the standard folders that no card mentions
    used = {f['path'] for a in assets for f in a['files']}
    orphans = [os.path.relpath(f, DOCS).replace('\\', '/') for f in glob.glob(os.path.join(DOCS, 'library', '**', '*.glb'), recursive=True)]
    orphans = [o for o in orphans if o not in used]
    order = {c: i for i, c in enumerate(CATS)}
    assets.sort(key=lambda a: (order.get(a['category'], 99), a['card']))
    public = [a for a in assets if a['public']]
    json.dump(cache, open(CACHE_PATH, 'w', encoding='utf-8'))
    out = {'generatedFrom': 'docs/**/*.asset.json', 'spec': SPEC['spec'],
           'categories': [{k: c[k] for k in ('id', 'zh', 'en', 'desc')} for c in SPEC['categories']], 'assets': public}
    json.dump(out, open(os.path.join(LAB, 'data', 'assets.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n_err = sum(1 for it in items if it['errors'])
    report = {'generated': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'spec': SPEC['spec'],
              'counts': {'cards': len(items), 'published': len(public), 'drafts': len(assets) - len(public), 'withErrors': n_err,
                         'withWarnings': sum(1 for it in items if it['warnings'])},
              'orphans': orphans, 'items': items}
    json.dump(report, open(os.path.join(LAB, 'data', 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{len(items)} cards · {len(public)} on the site · {len(assets) - len(public)} drafts · {n_err} with errors · '
          f'{report["counts"]["withWarnings"]} with warnings')
    for it in items:
        for e in it['errors']:
            print(f'  ERROR {it["card"]}: {e}')
    for o in orphans:
        print(f'  WARN  {o}: 没有任何卡片引用这个 GLB')
    if '--check' in sys.argv and n_err:
        sys.exit(1)


if __name__ == '__main__':
    main()
