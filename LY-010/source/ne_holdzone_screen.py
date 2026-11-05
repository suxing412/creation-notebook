# LY-010: screen the existing NE C geometry (196 m C_NE_APPROACH_LOCAL road chunk and the wuku trial chunk
# with C_WUKU_ISOLATED_SUPPORT_PATCH) against LY-003 hold zones and the NE C trial screening cells.
# This is the re-check LY-003 asked for ("LY-039 需要提供实际 GLB 和 SHA，再按 hold-zones 与 NE-C-SCREEN 复核").
# Distance = min(geometry vertices -> base geometry, base vertices -> plan triangle edges).
# Result meaning (LY-003 wording): outside a hold zone != proven outside the palace; it only shows no conflict
# with the old research schematic.
# Usage: python -I source/ne_holdzone_screen.py <evidence-geometry.json from cad338b> <glb> [<glb> ...]
import json, math, os, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "..", "LY-005", "source"))
import glbio  # noqa: E402


def iter_pairs(geom):
    c, t = geom["coordinates"], geom["type"]
    if t == "Point":
        return [c]
    if t == "LineString":
        return c
    if t == "Polygon":
        return c[0]
    raise ValueError(t)


def seg_dist(p, a, b):
    p, a, b = map(np.asarray, (p, a, b))
    ab = b - a
    t = 0.0 if not ab.any() else max(0.0, min(1.0, float((p - a) @ ab / (ab @ ab))))
    return float(np.linalg.norm(p - (a + t * ab)))


def inside(p, poly):
    x, y = p
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def dist_pts_geom(P, geom):
    g = iter_pairs(geom)
    if geom["type"] == "Point":
        return min(math.dist(p, g[0]) for p in P)
    if geom["type"] == "Polygon":
        ring = g[:-1] if g[0] == g[-1] else g
        if any(inside(p, ring) for p in P):
            return 0.0
        d1 = min(seg_dist(p, ring[i], ring[(i + 1) % len(ring)]) for p in P for i in range(len(ring)))
        return d1
    return min(seg_dist(p, g[i], g[i + 1]) for p in P for i in range(len(g) - 1))


def main():
    egp, glbs = sys.argv[1], sys.argv[2:]
    egraw = open(egp, "rb").read()
    EG = json.loads(egraw.decode("utf-8"))
    F = {f["id"]: f for f in EG["features"]}
    hz_path = os.path.join(HERE, "..", "LY-003", "tables", "hold-zones.json")
    cells_path = os.path.join(HERE, "..", "LY-003", "tables", "ne-screening-cells.json")
    HZ = json.loads(open(hz_path, "rb").read().decode("utf-8"))
    CE = json.loads(open(cells_path, "rb").read().decode("utf-8"))
    step = CE["step_m"]
    cells = {(round(x, 1), round(y, 1)) for x, y in CE["cell_centers_xy"]}
    cx = np.array([c[0] for c in cells]); cy = np.array([c[1] for c in cells])
    out = {"frame": EG["frame"]["id"], "evidenceGeometrySha256": hashlib.sha256(egraw).hexdigest(),
           "holdZonesSha256": hashlib.sha256(open(hz_path, "rb").read()).hexdigest(),
           "screenCellsSha256": hashlib.sha256(open(cells_path, "rb").read()).hexdigest(),
           "screenCells": len(cells), "screenStep_m": step,
           "meaning": HZ["not_meaning"], "items": []}
    for gp in glbs:
        g = glbio.read_glb(gp)
        per = []
        allP = []
        for _, name, w, pos, t, _ in glbio.mesh_items(g):
            P = glbio.apply(w, pos)
            P2 = np.c_[P[:, 0], -P[:, 2]]  # (east, north)
            allP.append(P2)
            per.append((name, P2))
        Pall = np.concatenate(allP)
        rec = {"glb": os.path.basename(gp), "sha256": g["sha256"], "vertices": int(len(Pall)),
               "bbox_en": [round(float(Pall[:, 0].min()), 2), round(float(Pall[:, 1].min()), 2),
                           round(float(Pall[:, 0].max()), 2), round(float(Pall[:, 1].max()), 2)],
               "zones": [], "nodes": []}
        # vertex in screening cell (axis-aligned 5 m square around a centre)
        def in_screen(P):
            ok = 0
            for x, y in P:
                if np.any((np.abs(cx - x) <= step / 2 + 1e-6) & (np.abs(cy - y) <= step / 2 + 1e-6)):
                    ok += 1
            return ok
        for name, P2 in per:
            rec["nodes"].append({"node": name, "vertices": int(len(P2)), "verticesInScreenCells": in_screen(P2)})
        # triangle edges in plan, for the base-vertex -> geometry-edge direction
        edges = []
        for _, _, w, pos, t, _ in glbio.mesh_items(g):
            P = glbio.apply(w, pos)
            Q = np.c_[P[:, 0], -P[:, 2]]
            for a, b, c in t:
                edges += [(Q[a], Q[b]), (Q[b], Q[c]), (Q[c], Q[a])]
        for z in HZ["zones"]:
            geom = F[z["base"]]["geometry"]
            d = dist_pts_geom(Pall.tolist(), geom)
            gv = iter_pairs(geom)
            d2 = min(seg_dist(v, a, b) for v in gv for a, b in edges)
            d = min(d, d2)
            rec["zones"].append({"zone": z["id"], "base": z["base"], "buffer_m": z["buffer_m"],
                                 "minVertexDist_m": round(d, 1), "outside": d > z["buffer_m"],
                                 "margin_m": round(d - z["buffer_m"], 1)})
        out["items"].append(rec)
    p = os.path.join(HERE, "qa", "ne-holdzone-screen.json")
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(out, ensure_ascii=False, indent=1))
    for r in out["items"]:
        print(r["glb"], r["sha256"][:12], "bbox(e,n)", r["bbox_en"])
        for z in r["zones"]:
            print("   ", z["zone"], "d", z["minVertexDist_m"], "buf", z["buffer_m"], "outside" if z["outside"] else "INSIDE", z["margin_m"])
        for n in r["nodes"]:
            print("   node", n["node"][:60], n["verticesInScreenCells"], "/", n["vertices"], "in NE-C-SCREEN")


if __name__ == "__main__":
    main()
