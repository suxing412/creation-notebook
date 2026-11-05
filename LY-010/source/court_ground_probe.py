# LY-010: which ground file actually lies under the candidate demonstration court C02-010 and its lane,
# now that cad338b makes ground-retained initial=true? Vertical point-in-triangle sampling on a 0.5 m grid.
# Reports, per ground file, coverage fraction and the set of top heights. Plan sampling only.
# Usage: python -I source/court_ground_probe.py <retained.glb> <south.glb>
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "..", "LY-005", "source"))
import glbio  # noqa: E402

BOXES = {  # world XZ boxes (LY-006 registry v1)
    "S-COURT C02-010 envelope": (531.0 - 9.0, -818.45 - 12.0, 531.0 + 9.0, -818.45 + 12.0),
    "S-COURT-LANE (LY-082)": (526.0, -806.45, 530.0, -796.45),
}


def tris_of(path, node_matrix=None):
    g = glbio.read_glb(path)
    N = np.eye(4) if node_matrix is None else glbio.gltf_col_major_to_np(node_matrix)
    T = []
    for _, _, w, pos, t, _ in glbio.mesh_items(g):
        P = glbio.apply(N @ w, pos)
        T.append(P[t])
    return g, np.concatenate(T)


def probe(T, box, step=0.5):
    x0, z0, x1, z1 = box
    xs = np.arange(x0 + step / 2, x1, step)
    zs = np.arange(z0 + step / 2, z1, step)
    # prefilter triangles by plan AABB
    mn, mx = T.min(axis=1), T.max(axis=1)
    keep = (mx[:, 0] >= x0) & (mn[:, 0] <= x1) & (mx[:, 2] >= z0) & (mn[:, 2] <= z1)
    T = T[keep]
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = 0
    hit = 0
    tops = {}
    for x in xs:
        for z in zs:
            n += 1
            v0 = c[:, [0, 2]] - a[:, [0, 2]]
            v1 = b[:, [0, 2]] - a[:, [0, 2]]
            v2 = np.array([x, z]) - a[:, [0, 2]]
            d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
            d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
            den = d00 * d11 - d01 * d01
            ok = np.abs(den) > 1e-12
            u = np.where(ok, (d11 * d20 - d01 * d21) / np.where(ok, den, 1), -1)
            v = np.where(ok, (d00 * d21 - d01 * d20) / np.where(ok, den, 1), -1)
            ins = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
            if ins.any():
                hit += 1
                y = (a[ins, 1] + u[ins] * (c[ins, 1] - a[ins, 1]) + v[ins] * (b[ins, 1] - a[ins, 1])).max()
                k = round(float(y), 4)
                tops[k] = tops.get(k, 0) + 1
    return {"samples": n, "covered": hit, "fraction": round(hit / n, 4) if n else None, "topY": tops,
            "trianglesInBox": int(keep.sum())}


def main():
    dump = json.load(open(os.path.join(HERE, "qa", "city-data.cad338b.dump.json"), encoding="utf-8"))
    nodes = {n["id"]: n for n in dump["nodes"]}
    out = {"method": "0.5 m grid, vertical point-in-triangle in XZ, highest hit y; city node matrix applied"}
    for label, path, nid in (("ground-retained", sys.argv[1], "ground-retained"), ("ground-south", sys.argv[2], "ground-south")):
        g, T = tris_of(path, nodes[nid].get("matrix"))
        out[label] = {"sha256": g["sha256"], "bytes": g["size"], "initial_cad338b": nodes[nid].get("initial"),
                      "boxes": {k: probe(T, b) for k, b in BOXES.items()}}
    open(os.path.join(HERE, "qa", "court-ground-probe.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    for k in ("ground-retained", "ground-south"):
        print(k, out[k]["sha256"][:12], "initial", out[k]["initial_cad338b"])
        for b, r in out[k]["boxes"].items():
            print("  ", b, r["covered"], "/", r["samples"], r["fraction"], "tops", r["topY"], "tris", r["trianglesInBox"])


if __name__ == "__main__":
    main()
