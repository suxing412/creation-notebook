# LY-039 prep: list every city-data.mjs record whose declared "bounds" (glTF frame:
# x east, y up, z = -north) overlap the NE road region (native x 2280..2322,
# y 3480..3660 -> glTF z -3660..-3480), with a margin. Read-only.
# python -I scan_city_bounds.py <city-data.mjs> [margin_m]
import sys, re, json
src = open(sys.argv[1], encoding='utf-8').read()
margin = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
X0, X1, Z0, Z1 = 2280 - margin, 2322 + margin, -3660 - margin, -3480 + margin
pat = re.compile(r'"id":\s*"([^"]+)"(?:(?!"id":).)*?"bounds":\s*\{\s*"min":\s*\[([^\]]*)\],\s*"max":\s*\[([^\]]*)\]', re.S)
hits, n = [], 0
for m in pat.finditer(src):
    n += 1
    mn = [float(v) for v in m.group(2).split(',')]
    mx = [float(v) for v in m.group(3).split(',')]
    if mx[0] >= X0 and mn[0] <= X1 and mx[2] >= Z0 and mn[2] <= Z1:
        hits.append({'id': m.group(1), 'min': mn, 'max': mx, 'line': src.count('\n', 0, m.start()) + 1})
print(json.dumps({'records_with_bounds': n, 'margin_m': margin, 'region_gltf': [X0, X1, Z0, Z1], 'hits': hits}, ensure_ascii=False, indent=1))
