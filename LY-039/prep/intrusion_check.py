# LY-039 prep: positive-volume intrusion test between the road solid and the two
# end slabs (Taicang ground slab, old wuku support patch), for a given road offset.
# Road solid is the measured analytic form from glb_raw_check.py / measure-ne-approach.json
# (top 0.2 -> 0.0 linear over y 3647.469 -> 3487.5 on the north leg, 0 elsewhere,
# thickness 0.18). Boxes are the measured bboxes (both slabs are 12-tri boxes).
# Seam probes cannot see overlap; this test can. Volume by 5 cm voxel sampling near ends.
# python -I intrusion_check.py <out.json> [dx,dy,dz ...]
import sys, json
outp = sys.argv[1]; offs = sys.argv[2:] or ['0,0,0']
BOX = {'original_city_ground_preserved': ((2249.714111, 3647.468994, 0.0), (2321.714111, 3699.468994, 0.2)),
       'C_WUKU_ISOLATED_SUPPORT_PATCH': ((2307.326904, 3490.0, -0.4), (2329.326904, 3510.0, 0.0))}
RECTS = [(2284.2141, 2287.2141, 3484.5, 3647.469), (2284.2141, 2317.8269, 3484.5, 3487.5), (2314.8269, 2317.8269, 3487.5, 3490.0)]
def top(x, y):
    if 2284.2141 <= x <= 2287.2141 and y > 3487.5: return 0.2 * (y - 3487.5) / (3647.469 - 3487.5)
    return 0.0
def in_road(x, y, z):
    if not any(a <= x <= b and c <= y <= d for a, b, c, d in RECTS): return False
    t = top(x, y); return t - 0.18 <= z <= t
res = []
h = 0.05; eps = 1e-4
for o in offs:
    dx, dy, dz = [float(v) for v in o.split(',')]
    r = {'offset': [dx, dy, dz]}
    for name, (lo, hi) in BOX.items():
        # sample only where box and shifted road bbox overlap
        x0, x1 = max(lo[0], 2284.2141 + dx), min(hi[0], 2317.8269 + dx)
        y0, y1 = max(lo[1], 3484.5 + dy), min(hi[1], 3647.469 + dy)
        z0, z1 = max(lo[2], -0.18 + dz), min(hi[2], 0.2 + dz)
        n = 0
        if x0 < x1 - eps and y0 < y1 - eps and z0 < z1 - eps:
            nx, ny, nz = max(1, int((x1 - x0) / h)), max(1, int((y1 - y0) / (h / 5))), max(1, int((z1 - z0) / (h / 5)))
            for i in range(nx):
                x = x0 + (i + 0.5) * (x1 - x0) / nx
                for j in range(ny):
                    y = y0 + (j + 0.5) * (y1 - y0) / ny
                    for k in range(nz):
                        z = z0 + (k + 0.5) * (z1 - z0) / nz
                        if lo[0] + eps < x < hi[0] - eps and lo[1] + eps < y < hi[1] - eps and lo[2] + eps < z < hi[2] - eps and in_road(x - dx, y - dy, z - dz):
                            n += 1
            vol = n * (x1 - x0) / nx * (y1 - y0) / ny * (z1 - z0) / nz
        else:
            vol = 0.0
        # face contact: sample each box face (2 cm), point just outside the face inside the road solid
        area = 0.0; g = 0.02
        for ax in range(3):
            for side, sgn in ((lo, -1), (hi, 1)):
                o1, o2 = [a for a in range(3) if a != ax]
                a0, a1 = max(lo[o1], [2284.2141 + dx, 3484.5 + dy, -0.18 + dz][o1]), min(hi[o1], [2317.8269 + dx, 3647.469 + dy, 0.2 + dz][o1])
                b0, b1 = max(lo[o2], [2284.2141 + dx, 3484.5 + dy, -0.18 + dz][o2]), min(hi[o2], [2317.8269 + dx, 3647.469 + dy, 0.2 + dz][o2])
                if a1 <= a0 or b1 <= b0: continue
                na, nb = max(1, int((a1 - a0) / g)), max(1, int((b1 - b0) / (g if o2 != 2 else 0.005)))
                hit = 0
                for i in range(na):
                    for j in range(nb):
                        q = [0, 0, 0]; q[ax] = side[ax] + sgn * 2 * eps
                        q[o1] = a0 + (i + 0.5) * (a1 - a0) / na; q[o2] = b0 + (j + 0.5) * (b1 - b0) / nb
                        if in_road(q[0] - dx, q[1] - dy, q[2] - dz): hit += 1
                area += hit * (a1 - a0) / na * (b1 - b0) / nb
        cls = 'positive-volume intrusion' if vol > 1e-5 else ('legal local face contact' if area > 1e-4 else 'separate')
        r[name] = {'intrusion_volume_m3': round(vol, 5), 'face_contact_area_m2': round(area, 4), 'class': cls}
    res.append(r)
rep = {'method': 'analytic road solid vs measured slab boxes, voxel sampling (x 5 cm, y/z 1 cm); surface contact counted separately; not exhaustive solid CSG', 'cases': res}
json.dump(rep, open(outp, 'w', encoding='utf-8'), indent=1)
for r in res: print(r['offset'], {k: (v['class'], v['intrusion_volume_m3']) for k, v in r.items() if k != 'offset'})
