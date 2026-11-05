# LY-010: triangle-level (XZ plan, 2D SAT) check of the cad338b yong-road-receiver against LY-006 zones.
# The receiver is a 209-triangle component cut from network-ground-stitched C_stitch_primary and is
# initial=true from cad338b on. This tells which frozen write zones now have a *default-visible* road
# triangle over them in plan. Plan overlap only; no height or solid test.
# Usage: python -I source/receiver_overlap.py <glb> [nodeId=yong-road-receiver]   (glb exported with git show cad338b:<path>)
import json, math, os, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "..", "LY-005", "source"))
import glbio  # noqa: E402  (read-only reuse of LY-005 reader)


def rect_corners(o):
    c, yaw, h = o["c"], o["yaw"], o["h"]
    # three.js yaw about +Y: x' = x cos + z sin ; z' = -x sin + z cos
    ca, sa = math.cos(yaw), math.sin(yaw)
    pts = []
    for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        lx, lz = sx * h[0], sz * h[2]
        pts.append((c[0] + lx * ca + lz * sa, c[2] - lx * sa + lz * ca))
    return np.array(pts)


def sat(a, b):
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            e = poly[(i + 1) % n] - poly[i]
            ax = np.array([-e[1], e[0]])
            pa, pb = a @ ax, b @ ax
            if pa.max() < pb.min() - 1e-9 or pb.max() < pa.min() - 1e-9:
                return False
    return True


def main():
    glb = sys.argv[1]
    nid = sys.argv[2] if len(sys.argv) > 2 else "yong-road-receiver"
    g = glbio.read_glb(glb)
    dump = json.load(open(os.path.join(HERE, "qa", "city-data.cad338b.dump.json"), encoding="utf-8"))
    node = {n["id"]: n for n in dump["nodes"]}[nid]
    N = glbio.gltf_col_major_to_np(node["matrix"]) if node.get("matrix") else np.eye(4)
    tris = []
    for _, _, w, pos, t, _ in glbio.mesh_items(g):
        P = glbio.apply(N @ w, pos)
        for a, b, c in t:
            tris.append(np.array([[P[a][0], P[a][2]], [P[b][0], P[b][2]], [P[c][0], P[c][2]]]))
    zraw = open(os.path.join(HERE, "..", "LY-006", "registry", "zones.json"), "rb").read()
    z = json.loads(zraw.decode("utf-8"))
    hits = []
    for zz in z["zones"]:
        o = zz.get("worldOBB")
        if not o:
            continue
        R = rect_corners(o)
        lo, hi = R.min(0), R.max(0)
        n = sum(1 for T in tris if (T.max(0) >= lo).all() and (T.min(0) <= hi).all() and sat(T, R))
        if n:
            hits.append({"zone": zz["zoneId"], "seat": zz["seat"], "label": zz.get("label"), "trianglesOverPlan": n})
    res = {"nodeId": nid, "glbSha256": g["sha256"], "glbBytes": g["size"], "triangles": len(tris),
           "cityMatrix": node.get("matrix"), "zonesSha256": hashlib.sha256(zraw).hexdigest(),
           "method": "2D SAT triangle vs zone worldOBB rectangle in XZ; no Y test", "hits": hits}
    open(os.path.join(HERE, "qa", f"plan-zone-overlap.{nid}.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    print(nid, g["sha256"][:12], g["size"], "tris", len(tris), "zones hit", len(hits))
    for h in hits:
        print(" ", h["zone"], h["trianglesOverPlan"], h["label"])


if __name__ == "__main__":
    main()
