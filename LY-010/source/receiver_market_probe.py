# -*- coding: utf-8 -*-
# LY-010: where exactly does the cad338b default-visible yong-road-receiver lie over the market site,
# and does it cover the well hole or any LY-021/LY-023/LY-025 write zone of the six seats released first?
# Vertical point-in-triangle sampling (XZ plan) on a 0.10 m grid inside each probed rectangle; reports
# hit fraction and top heights. Plan + height only; not a solid or rendering test.
# Usage: python -I source/receiver_market_probe.py <receiver.glb> <zones.json>
import hashlib, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "..", "LY-005", "source"))
import glbio  # noqa: E402

SITE = np.array([214.286, 0.0, -1959.184])  # local:market-site origin (LY-006 frames), yaw 0


def tris_world(path):
    g = glbio.read_glb(path)
    T = []
    for _, _, w, pos, tri, _ in glbio.mesh_items(g):
        P = glbio.apply(w, pos)
        T.append(P[tri])
    return np.concatenate(T)


def hits(T, xs, zs):
    # returns array of max hit height per sample (nan if none)
    X, Z = np.meshgrid(xs, zs)
    px, pz = X.ravel(), Z.ravel()
    best = np.full(px.shape, np.nan)
    for t in T:
        (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = t
        if px.max() < min(x0, x1, x2) or px.min() > max(x0, x1, x2) or pz.max() < min(z0, z1, z2) or pz.min() > max(z0, z1, z2):
            continue
        d = (z1 - z2) * (x0 - x2) + (x2 - x1) * (z0 - z2)
        if abs(d) < 1e-12:
            continue
        a = ((z1 - z2) * (px - x2) + (x2 - x1) * (pz - z2)) / d
        b = ((z2 - z0) * (px - x2) + (x0 - x2) * (pz - z2)) / d
        c = 1 - a - b
        m = (a >= -1e-9) & (b >= -1e-9) & (c >= -1e-9)
        y = a * y0 + b * y1 + c * y2
        best = np.where(m & ~(y <= best), y, best)
    return best


def probe(T, label, box, step=0.10, disc=None):
    (x0, z0), (x1, z1) = box
    xs = np.arange(x0 + step / 2, x1, step)
    zs = np.arange(z0 + step / 2, z1, step)
    h = hits(T, xs, zs)
    if disc is not None:
        X, Z = np.meshgrid(xs, zs)
        keep = ((X.ravel() - disc[0]) ** 2 + (Z.ravel() - disc[1]) ** 2) <= disc[2] ** 2
        h = h[keep]
    n = h.size
    k = int(np.sum(~np.isnan(h)))
    tops = sorted({round(float(v), 4) for v in h[~np.isnan(h)]})
    return {"probe": label, "samples": n, "hits": k, "hitFraction": round(k / n, 4) if n else None,
            "topHeights_m": tops[:12] + (["..."] if len(tops) > 12 else [])}


def main():
    glb, zp = sys.argv[1], sys.argv[2]
    T = tris_world(glb)
    zones = json.load(open(zp, encoding="utf-8"))["zones"]
    out = {"glb": os.path.basename(glb), "glbSha256": hashlib.sha256(open(glb, "rb").read()).hexdigest(), "triangles": int(len(T)),
           "zonesSha256": hashlib.sha256(open(zp, "rb").read()).hexdigest(), "grid_m": 0.10,
           "method": "vertical point-in-triangle in XZ, world coords (receiver has no city matrix)", "probes": []}
    # receiver triangles over the whole market slab, in local frame
    loc = T - SITE
    inside = [(t - 0).tolist() for t in loc if (np.all(t[:, 0] > -31) and np.all(t[:, 0] < 31) and np.all(t[:, 2] > -23) and np.all(t[:, 2] < 23))]
    over = [t for t in loc if (t[:, 0].max() > -30 and t[:, 0].min() < 30 and t[:, 2].max() > -22 and t[:, 2].min() < 22)]
    if over:
        o = np.concatenate(over)
        out["overMarketSlab"] = {"triangles": len(over), "localXRange": [round(float(o[:, 0].min()), 3), round(float(o[:, 0].max()), 3)],
                                 "localZRange": [round(float(o[:, 2].min()), 3), round(float(o[:, 2].max()), 3)],
                                 "yRange": [round(float(o[:, 1].min()), 4), round(float(o[:, 1].max()), 4)]}
    out["probes"].append(probe(T, "market slab 60x44 (LY-025:write:002)", ((SITE[0] - 30, SITE[2] - 22), (SITE[0] + 30, SITE[2] + 22)), step=0.25))
    out["probes"].append(probe(T, "well hole disc r=0.65 at local (-18,+7)", ((SITE[0] - 18.7, SITE[2] + 6.3), (SITE[0] - 17.3, SITE[2] + 7.7)), step=0.02,
                               disc=(SITE[0] - 18, SITE[2] + 7, 0.65)))
    for z in zones:
        if z["seat"] in ("LY-021", "LY-023", "LY-025", "LY-022") and z.get("frame") == "local:market-site":
            (bx0, _, bz0), (bx1, _, bz1) = z["box"]
            out["probes"].append({**probe(T, z["zoneId"] + " " + z["label"], ((SITE[0] + bx0, SITE[2] + bz0), (SITE[0] + bx1, SITE[2] + bz1)), step=0.10)})
    p = os.path.join(HERE, "qa", "receiver-market-probe.json")
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out.get("overMarketSlab"), ensure_ascii=False))
    for x in out["probes"]:
        print(x["probe"], x["hits"], "/", x["samples"], x["topHeights_m"][:4])


if __name__ == "__main__":
    main()
