# LY-047 prep: read-only parser for docs/cities/luoyang/city-data.mjs (JSON literals inside JS).
import json, re

BS = chr(92)


def _array_after(src, marker):
    i = src.index(marker)
    j = src.index('[', i)
    depth, k, instr, esc = 0, j, False, False
    while True:
        c = src[k]
        if instr:
            if esc:
                esc = False
            elif c == BS:
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return json.loads(src[j:k + 1]), src[:j].count('\n') + 1
        k += 1


def load(path):
    src = open(path, encoding='utf-8').read()
    assets, aline = _array_after(src, 'const assetRecords =')
    nodes, nline = _array_after(src, 'export const nodes =')
    lines = src.split('\n')
    idline = {}
    for n, L in enumerate(lines, 1):
        m = re.match(r'\s*"id": "([^"]+)"', L)
        if m and m.group(1) not in idline:
            idline[m.group(1)] = n
    return {'assets': {a['id']: a for a in assets}, 'nodes': nodes, 'idline': idline,
            'assetsLine': aline, 'nodesLine': nline}
