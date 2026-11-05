"""LY-009: independent re-parse of TASKPOOL.md (the original text).

Usage: python -I parse_taskpool.py <TASKPOOL.md> <out.json>

Rules (written from the original text, not from taskboard.json):
  * a seat section starts at a line '### LY-###｜<title>' and ends right before
    the next line that starts with '#' (any heading level);
  * trailing blank lines and a trailing '---' rule are stripped from the text;
  * '- **类型 / 依赖**：<type>；<deps>。' gives type and deps;
    deps 'G' expands to the gate set stated in the general rules
    (`G` = LY-001、002、005、006、007、008、009、010);
    '无（首先执行）' means no deps;
  * '- **唯一写入区**：`workpacks/LY-###/`' gives the write area;
  * every '## NN—NN｜…' heading inside the list gives a section with its intro.
"""
import json, re, sys, hashlib

SEAT_RE = re.compile(r'^### (LY-\d{3})｜(.+?)\s*$')
TYPE_RE = re.compile(r'^- \*\*类型 / 依赖\*\*：(.+?)；(.+?)。\s*$')
WRITE_RE = re.compile(r'^- \*\*唯一写入区\*\*：`([^`]+)`')
SECTION_RE = re.compile(r'^## (\d{2,3})—(\d{2,3})｜(.+?)\s*$')
G_RE = re.compile(r'`G` = (LY-\d{3}(?:、\d{3})+)')
FIELD_RE = re.compile(r'^- \*\*(.+?)\*\*：(.*)$')


def parse(path):
    raw = open(path, 'rb').read()
    text = raw.decode('utf-8')
    lines = text.split('\n')
    # gate set from the general rules
    m = None
    for ln in lines:
        m = G_RE.search(ln)
        if m:
            break
    if not m:
        raise SystemExit('G definition not found')
    parts = m.group(1).split('、')
    gset = [parts[0]] + ['LY-' + p for p in parts[1:]]

    seats, sections = [], []
    cur, cur_sec = None, None
    list_start = next(i for i, ln in enumerate(lines) if ln.strip() == '# 100项完整清单')

    def close_seat(end):
        nonlocal cur
        if cur is None:
            return
        body = lines[cur['_start']:end]
        while body and body[-1].strip() in ('', '---'):
            body.pop()
        cur['text'] = '\n'.join(body)
        cur['lineStart'] = cur['_start'] + 1
        cur['lineEnd'] = cur['_start'] + len(body)
        del cur['_start']
        seats.append(cur)
        cur = None

    for i, ln in enumerate(lines):
        if i < list_start:
            continue
        if ln.startswith('#'):
            close_seat(i)
            if cur_sec is not None and 'introEnd' not in cur_sec:
                cur_sec['introEnd'] = i
            sm = SECTION_RE.match(ln)
            if sm:
                cur_sec = {'range': [int(sm.group(1)), int(sm.group(2))], 'title': sm.group(3),
                           'line': i + 1, '_i': i}
                sections.append(cur_sec)
                continue
            m2 = SEAT_RE.match(ln)
            if m2:
                cur = {'id': m2.group(1), 'title': m2.group(2), '_start': i,
                       'section': cur_sec['title'] if cur_sec else None}
            elif ln.startswith('# '):
                cur_sec = None
            continue
        if cur is not None:
            fm = FIELD_RE.match(ln)
            if fm:
                cur.setdefault('fields', {})[fm.group(1)] = fm.group(2)
            tm = TYPE_RE.match(ln)
            if tm:
                cur['type'] = tm.group(1)
                d = tm.group(2)
                cur['depsRaw'] = d
                toks = [t.strip() for t in d.split('、')]
                if d.startswith('无'):
                    explicit, uses_g = [], False
                else:
                    uses_g = 'G' in toks
                    explicit = [t for t in toks if t != 'G']
                    bad = [t for t in explicit if not re.fullmatch(r'LY-\d{3}', t)]
                    if bad:
                        raise SystemExit(f"{cur['id']}: bad dep tokens {bad}")
                cur['usesG'] = uses_g
                cur['depsExplicit'] = explicit
                cur['deps'] = sorted(set(explicit) | (set(gset) if uses_g else set()))
            wm = WRITE_RE.match(ln)
            if wm:
                cur['writeArea'] = wm.group(1)
    close_seat(len(lines))
    for s in sections:
        i = s.pop('_i')
        end = s.pop('introEnd', i + 1)
        intro = '\n'.join(l for l in lines[i + 1:end] if l.strip())
        s['intro'] = intro
    return {
        'source': path.replace('\\', '/').split('/')[-1],
        'sha256': hashlib.sha256(raw).hexdigest(),
        'bytes': len(raw),
        'crlf': raw.count(b'\r\n'),
        'G': gset,
        'sections': sections,
        'seats': seats,
    }


if __name__ == '__main__':
    out = parse(sys.argv[1])
    with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(len(out['seats']), 'seats;', len(out['sections']), 'sections; G =', out['G'])
