"""LY-091 baseline ("before") measurement of the gate/wall region on a read-only lab tree.

Usage:
  python -I baseline_ly091.py --lab D:/GitHub/creation-notebook-lab --dump _city-dump.json --out baseline-bce3211.json

Reads only. Measures:
  1. region inventory: every city node in chapters walls + yong-gate (+ terrain support),
     asset path, sha256, bytes, git blob at HEAD, GLB fingerprint, world AABB;
  2. gate family: the 12 gate cards (files, sha, bytes, triangles, 15 MB limit, LOD labels,
     in-city / research / card-only state);
  3. 12 gate sites (B points -> C projection): wall gap edges along the wall tangent,
     gate body present, through-passage clear widths at 0.3/1.8 m, ground support
     fraction under a 32 x 40 m site footprint, up-facing tread heights (climb evidence);
  4. counts declared by the project card (progress.walls) for consistency with 1-3.

v2 (2026-11-06), after a drift replay on origin/main cad338b exposed three v1 defects:
  - record hashes dropped the environment-resolved `url` / `nearUrl` fields (v1 hashed the
    absolute file:// path, so any replay on a relocated copy false-FAILed C2 for every node);
  - region = chapter nodeIds UNION nodes whose own `chapter` field is walls / yong-gate
    (cad338b adds yong-gate-body-far / yong-gate-interface-far with chapter=walls that are
    not listed in the walls chapter nodeIds; v1 missed them);
  - the renderer's `replaces` rule (city-renderer.mjs rebuild()) is applied: a node replaced
    by another active node is not drawn. Sites are measured in the "region open" state
    (walls + yong-gate + terrain chapters loaded); visibleByDefault applies it to initial nodes.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbread import GLB  # noqa: E402

GATE_CARDS = [
    "m-luoyang-xia-gate", "m-luoyang-gu-gate", "m-luoyang-shangxi-gate", "m-luoyang-yong-gate",
    "m-luoyang-guangyang-gate", "m-luoyang-shangdong-gate", "m-luoyang-zhongdong-gate", "m-luoyang-mao-gate",
    "m-luoyang-jin-gate", "m-luoyang-xiaoyuan-gate", "m-luoyang-pingcheng-gate", "m-luoyang-kaiyang-gate",
]
# B feature id -> card id. gate_xuan_B ("旋门" in B data) is mapped to the 旄门 card; the
# alias itself is an LY-002 question, recorded as such, not settled here.
SITE_CARD = {
    "gate_xia_B": "m-luoyang-xia-gate", "gate_gu_B": "m-luoyang-gu-gate", "gate_shangxi_B": "m-luoyang-shangxi-gate",
    "gate_yong_B": "m-luoyang-yong-gate", "gate_guangyang_B": "m-luoyang-guangyang-gate",
    "gate_shangdong_B": "m-luoyang-shangdong-gate", "gate_zhongdong_B": "m-luoyang-zhongdong-gate",
    "gate_xuan_B": "m-luoyang-mao-gate", "gate_jin_B": "m-luoyang-jin-gate", "gate_xiaoyuan_B": "m-luoyang-xiaoyuan-gate",
    "gate_pingcheng_B": "m-luoyang-pingcheng-gate", "gate_kaiyang_B": "m-luoyang-kaiyang-gate",
}
GATE_NAMES = ["夏门", "谷门", "上西门", "雍门", "广阳门", "上东门", "中东门", "旄门", "津门", "小苑门", "平城门", "开阳门"]
LIMIT = 15_000_000
WALK_CAP = 1.0  # m, absolute glTF Y; ground-level support surfaces must lie below this
RESEARCH_GATES = {"research-north13-kaiyang-K", "research-north13-pingcheng-P", "research-north13-shangxi-X",
                  "research-north13-yong-Y", "research-north13-zhongdong-Z", "research-mao-gate"}


def max_rise(hb, base, top, min_area=0.5):
    """Largest vertical gap in the ladder base -> tread bins (area >= min_area) -> wall top."""
    ys = sorted(float(k) for k, v in hb.items() if v >= min_area)
    lad = [base] + ys + [top]
    gaps = [round(lad[i + 1] - lad[i], 3) for i in range(len(lad) - 1)]
    return {"ladder": [round(y, 3) for y in lad], "maxRise": max(gaps) if gaps else None, "minArea_m2": min_area}


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def git(lab, *args):
    return subprocess.run(["git", "-C", lab] + list(args), capture_output=True, text=True).stdout.strip()


def city_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], float).reshape(4, 4).T
    M = np.eye(4)
    M[:3, 3] = node.get("position", [0, 0, 0])
    return M


ENV_KEYS = ("url", "nearUrl")  # resolved against import.meta.url by city-data.mjs -> depend on checkout path


def canon(o):
    if isinstance(o, dict):
        o = {k: v for k, v in o.items() if k not in ENV_KEYS}
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def active_after_replaces(ids, N):
    """Mirror city-renderer.mjs rebuild(): nodes listed in `replaces` of an active node are not drawn."""
    ids = [i for i in ids if i in N]
    replaced = {r for i in ids for r in (N[i].get("replaces") or [])}
    return [i for i in ids if i not in replaced], sorted(replaced & set(ids))


# ------------------------------------------------------------------ geometry helpers
def seg_hits(P0, P1, tris, eps=1e-9):
    """Boolean per segment: does segment P0->P1 hit any triangle (Moller-Trumbore, chunked)."""
    out = np.zeros(len(P0), bool)
    if len(tris) == 0:
        return out
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    for i in range(len(P0)):
        o = P0[i]
        d = P1[i] - P0[i]
        pv = np.cross(d, e2)
        det = (e1 * pv).sum(1)
        ok = np.abs(det) > eps
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        tv = o - v0
        u = (tv * pv).sum(1) * inv
        qv = np.cross(tv, e1)
        v = (qv * d).sum(1) * inv
        t = (qv * e2).sum(1) * inv
        out[i] = bool((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t >= 0) & (t <= 1)).any())
    return out


def down_hits(pts_xz, tris, ycap=np.inf):
    """For each XZ point return the highest triangle Y below ycap (nan if none)."""
    res = np.full(len(pts_xz), np.nan)
    if len(tris) == 0:
        return res
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    ax, az, bx, bz, cx, cz = a[:, 0], a[:, 2], b[:, 0], b[:, 2], c[:, 0], c[:, 2]
    den = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
    good = np.abs(den) > 1e-12
    a, b, c = a[good], b[good], c[good]
    ax, az, bx, bz, cx, cz, den = ax[good], az[good], bx[good], bz[good], cx[good], cz[good], den[good]
    lo = np.minimum(np.minimum(ax, bx), cx); hi = np.maximum(np.maximum(ax, bx), cx)
    lz = np.minimum(np.minimum(az, bz), cz); hz = np.maximum(np.maximum(az, bz), cz)
    for i, (px, pz) in enumerate(pts_xz):
        m = (lo <= px) & (hi >= px) & (lz <= pz) & (hz >= pz)
        if not m.any():
            continue
        w1 = ((bz[m] - cz[m]) * (px - cx[m]) + (cx[m] - bx[m]) * (pz - cz[m])) / den[m]
        w2 = ((cz[m] - az[m]) * (px - cx[m]) + (ax[m] - cx[m]) * (pz - cz[m])) / den[m]
        w3 = 1 - w1 - w2
        inside = (w1 >= -1e-9) & (w2 >= -1e-9) & (w3 >= -1e-9)
        if inside.any():
            y = w1 * a[m][:, 1] + w2 * b[m][:, 1] + w3 * c[m][:, 1]
            y = y[inside & (y < ycap)]
            if len(y):
                res[i] = float(y.max())
    return res


def point_tri_dist(p, tris):
    """Min distance from point p to a set of triangles (Ericson closest-point, vectorized)."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    ab, ac, ap_ = b - a, c - a, p - a
    d1, d2 = (ab * ap_).sum(1), (ac * ap_).sum(1)
    bp = p - b
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = p - c
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    denom = va + vb + vc
    denom = np.where(np.abs(denom) < 1e-18, 1e-18, denom)
    v = vb / denom
    w = vc / denom
    q = a + ab * v[:, None] + ac * w[:, None]
    # vertex / edge regions
    def sel(mask, val):
        q[mask] = val[mask]
    sel((d1 <= 0) & (d2 <= 0), a)
    sel((d3 >= 0) & (d4 <= d3), b)
    sel((d6 >= 0) & (d5 <= d6), c)
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
    t = np.where(m, d1 / np.where(d1 - d3 == 0, 1, d1 - d3), 0)
    sel(m, a + ab * t[:, None])
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
    t = np.where(m, d2 / np.where(d2 - d6 == 0, 1, d2 - d6), 0)
    sel(m, a + ac * t[:, None])
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = np.where(m, (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1, (d4 - d3) + (d5 - d6)), 0)
    sel(m, b + (c - b) * t[:, None])
    return float(np.linalg.norm(q - p, axis=1).min()) if len(q) else float("inf")


def near(tris, cx, cz, r):
    if len(tris) == 0:
        return tris
    c = tris.mean(1)
    ext = np.abs(tris - c[:, None, :]).max(1)
    m = (np.abs(c[:, 0] - cx) <= r + ext[:, 0]) & (np.abs(c[:, 2] - cz) <= r + ext[:, 2])
    return tris[m]


def runs(mask, xs):
    """Contiguous True runs -> list of [start, end, width]."""
    out = []
    i = 0
    step = xs[1] - xs[0] if len(xs) > 1 else 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append([round(float(xs[i]), 3), round(float(xs[j]), 3), round(float(xs[j] - xs[i] + step), 3)])
            i = j + 1
        else:
            i += 1
    return out


# ------------------------------------------------------------------ main
def asset_file(city, asset):
    """Candidate overlays / negative cases may point an asset at a file outside the lab via absPath."""
    return os.path.normpath(asset["absPath"]) if asset.get("absPath") else os.path.normpath(city + asset["sourcePath"])


def discover_gate_cards(lab):
    """All library cards that are city gates: id m-luoyang-<x>-gate, or a title equal to one of the 12 gate names."""
    names = set(GATE_NAMES)
    found = []
    for f in sorted(glob.glob(lab + "/docs/library/models/*/*.asset.json")):
        cj = json.load(open(f, encoding="utf-8"))
        cid = cj.get("id", "")
        if re.fullmatch(r"m-luoyang-[a-z]+-gate", cid) or (cj.get("title") in names):
            found.append(cid)
    return found


def measure(lab, d, sites_arg="all"):
    lab = lab.replace("\\", "/")
    city = lab + "/docs/cities/luoyang/"
    A = {x["id"]: x for x in d["assets"]}
    N = {x["id"]: x for x in d["nodes"]}
    C = {x["id"]: x for x in d["chapters"]}
    head = git(lab, "rev-parse", "HEAD")
    dirty_docs = git(lab, "status", "--porcelain", "--", "docs")

    def union(*seqs):
        out = []
        for s in seqs:
            for i in s:
                if i not in out:
                    out.append(i)
        return out

    REGION_CH = ("walls", "yong-gate")
    listed = union(C["walls"]["nodeIds"], C["yong-gate"]["nodeIds"])
    by_field = [n["id"] for n in d["nodes"] if n.get("chapter") in REGION_CH]
    all_region_ids = union(listed, by_field)
    all_terrain_ids = union(C["terrain"]["nodeIds"], [n["id"] for n in d["nodes"] if n.get("chapter") == "terrain"])
    initial_ids = [i for i in N if N[i].get("initial", True) is not False]
    chapter_loaded = union(C["walls"]["nodeIds"], C["yong-gate"]["nodeIds"], C["terrain"]["nodeIds"])
    # renderer: loadedIds = initial nodes; opening a chapter adds its nodeIds; rebuild() drops replaced ones
    open_ids, replaced_open = active_after_replaces(union(initial_ids, chapter_loaded), N)
    default_ids, replaced_default = active_after_replaces(initial_ids, N)
    region_ids = [i for i in all_region_ids if i in open_ids]      # drawn when the region chapters are open
    terrain_ids = [i for i in all_terrain_ids if i in open_ids]
    report = {"lab": lab, "head": head, "docsDirty": dirty_docs or "", "measureVersion": 2,
              "regionNodeIds": region_ids, "terrainNodeIds": terrain_ids,
              "allRegionNodeIds": all_region_ids, "allTerrainNodeIds": all_terrain_ids,
              "regionNodesNotInChapterList": [i for i in by_field if i not in listed],
              "replacedWhenRegionOpen": replaced_open, "replacedByDefault": replaced_default,
              "measuredState": "walls + yong-gate + terrain chapters open; replaces applied"}
    default_set = set(default_ids)

    # ---------------------------------------------------------- 1. inventory
    glbs, inv = {}, []
    world_tris = {}
    for nid in all_region_ids + all_terrain_ids:
        n = N[nid]
        asset = A[n["asset"]]
        p = asset_file(city, asset)
        g = GLB(p)
        M = city_matrix(n)
        fp = g.fingerprint()
        tris, owners = g.world_triangles(M)
        world_tris[nid] = (tris, owners)
        relrepo = os.path.relpath(p, lab).replace("\\", "/")
        blob = git(lab, "rev-parse", "HEAD:" + relrepo)
        lo, hi = (tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)) if len(tris) else (np.zeros(3), np.zeros(3))
        inv.append({
            "nodeId": nid, "chapter": n["chapter"], "assetId": n["asset"], "title": n.get("title"),
            "tier": n.get("tier"), "initial": n.get("initial", True),
            "loadedByDefault": n.get("initial", True) is not False,
            "visibleByDefault": nid in default_set,
            "drawnWhenRegionOpen": nid in open_ids,
            "replaces": n.get("replaces") or [],
            "nearSha256": asset.get("nearSha256"), "nearBytes": asset.get("nearBytes"),
            "path": relrepo, "gitBlobAtHead": blob, "sha256": fp["sha256"], "bytes": fp["bytes"],
            "nearPath": asset.get("nearUrl"),
            "cityTransform": n.get("matrix") or {"position": n.get("position")},
            "cityNodeRecordSha256": canon(n), "cityAssetRecordSha256": canon(asset),
            "triangles": fp["triangles"], "meshNodes": fp["meshNodes"], "materials": fp["materials"],
            "images": fp["images"], "externalImageUris": fp["externalImageUris"],
            "extensionsUsed": fp["extensionsUsed"],
            "worldAabb": [[round(float(x), 3) for x in lo], [round(float(x), 3) for x in hi]],
            "over15MB": fp["bytes"] > LIMIT,
        })
    report["inventory"] = inv

    # ---------------------------------------------------------- 2. gate family
    cards = []
    city_paths = {asset_file(city, A[N[i]["asset"]]) for i in all_region_ids}
    city_shas = {x["sha256"] for x in inv} | {x["nearSha256"] for x in inv if x.get("nearSha256")}
    research_assets = {r["asset"]: r for r in d.get("researchModels", [])}
    discovered = discover_gate_cards(lab)
    for cid in discovered:
        cd = lab + "/docs/library/models/" + cid
        cj = json.load(open(glob.glob(cd + "/*.asset.json")[0], encoding="utf-8"))
        files = []
        for f in cj.get("files", []):
            fp_ = os.path.normpath(cd + "/" + f["path"])
            row = {"label": f.get("label"), "path": os.path.relpath(fp_, lab).replace("\\", "/"), "exists": os.path.exists(fp_)}
            if row["exists"] and fp_.endswith(".glb"):
                g = GLB(fp_)
                fpr = g.fingerprint()
                row.update(bytes=g.bytes, sha256=g.sha256, triangles=fpr["triangles"], images=fpr["images"],
                           meshNodes=[m["node"] for m in fpr["meshNodes"]], over15MB=g.bytes > LIMIT,
                           inCity=(fp_ in city_paths or g.sha256 in city_shas))
            files.append(row)
        lods = sorted({lab_ for f in files for lab_ in ["LOD0", "LOD1", "LOD2"] if lab_ in (f.get("label") or "") and "附件" not in (f.get("label") or "")})
        cards.append({"cardId": cid, "title": cj.get("title"), "status": cj.get("status"), "statusNote": cj.get("statusNote"),
                      "files": files, "gateBodyLods": lods,
                      "anyFileInCity": any(f.get("inCity") for f in files)})
    report["gateFamily"] = {"cardCount": len(cards), "cards": cards, "discoveryRule": "id ~ m-luoyang-[a-z]+-gate or title in 12 gate names",
                            "expectedSet": GATE_CARDS, "missing": sorted(set(GATE_CARDS) - set(discovered)),
                            "unexpected": sorted(set(discovered) - set(GATE_CARDS))}

    # ---------------------------------------------------------- 3. sites
    cons = json.load(open(city + "data/west/city-wall-constraints.json", encoding="utf-8"))
    wall_ids = [i for i in region_ids if N[i]["asset"].startswith("wall-") and "gate-body" not in N[i]["asset"]]
    body_ids = [i for i in region_ids if i not in wall_ids]  # gate bodies + gate-owned wings/aprons
    wall_tris = np.concatenate([world_tris[i][0] for i in wall_ids])
    body = {i: world_tris[i][0] for i in body_ids}
    ground_ids = terrain_ids + body_ids  # gate floors/aprons count; only surfaces below WALK_CAP are used
    ground_tris = np.concatenate([world_tris[i][0] for i in ground_ids])
    # default state (no chapter opened): only nodes visible by default, replaces applied
    dground_ids = [i for i in all_region_ids + all_terrain_ids
                   if i in default_set and not (N[i]["asset"].startswith("wall-") and "gate-body" not in N[i]["asset"])]
    dground_tris = (np.concatenate([world_tris[i][0] for i in dground_ids]) if dground_ids else np.zeros((0, 3, 3)))
    all_solid = np.concatenate([wall_tris] + list(body.values()))
    sites = []
    for gdiag in cons["gate_projection_diagnostics"]:
        fid = gdiag["feature_id"]
        if sites_arg != "all" and fid not in sites_arg.split(","):
            continue
        cx, cz = gdiag["C_projection_only"][0], -gdiag["C_projection_only"][1]
        wv = near(wall_tris, cx, cz, 70).reshape(-1, 3)
        rel = wv[:, [0, 2]] - [cx, cz]
        rel = rel[np.hypot(rel[:, 0], rel[:, 1]) < 70]
        if len(rel) < 3:
            sites.append({"featureId": fid, "name": gdiag["name"], "error": "no wall within 70 m"})
            continue
        w, V = np.linalg.eigh(np.cov(rel.T))
        tan = V[:, np.argmax(w)]
        nrm = np.array([-tan[1], tan[0]])
        tu, tv = rel @ tan, rel @ nrm
        band = np.abs(tv) < 6.0
        plus = tu[band & (tu > 0)]
        minus = tu[band & (tu < 0)]
        gap = [round(float(minus.max()), 3) if len(minus) else None, round(float(plus.min()), 3) if len(plus) else None]
        # bodies at site
        present = []
        for bid, bt in body.items():
            nb = near(bt, cx, cz, 20)
            if len(nb):
                present.append({"nodeId": bid, "trianglesWithin20m": int(len(nb))})
        # local solid set
        loc_solid = near(all_solid, cx, cz, 45)
        loc_ground = near(ground_tris, cx, cz, 45)
        T3 = np.array([tan[0], 0, tan[1]]); N3 = np.array([nrm[0], 0, nrm[1]]); O = np.array([cx, 0, cz])
        # ground support grid over the gate gap (u in gap or +-16), v in +-20
        u0 = gap[0] if gap[0] is not None else -16.0
        u1 = gap[1] if gap[1] is not None else 16.0
        us = np.arange(u0 + 0.25, u1 - 0.25 + 1e-9, 0.5)
        vs = np.arange(-19.75, 19.75 + 1e-9, 0.5)
        UU, VV = np.meshgrid(us, vs)
        P = O + UU.reshape(-1, 1) * T3 + VV.reshape(-1, 1) * N3
        gy = down_hits(P[:, [0, 2]], loc_ground, WALK_CAP)
        hit = np.isfinite(gy)
        dloc = near(dground_tris, cx, cz, 45) if len(dground_tris) else dground_tris
        dgy = down_hits(P[:, [0, 2]], dloc, WALK_CAP) if len(dloc) else np.full(len(P), np.nan)
        dhit = np.isfinite(dgy)
        walk = hit  # ground-level support only: highest surface below WALK_CAP (roofs/wing tops excluded)
        base_y = float(np.nanmedian(gy[walk])) if walk.any() else 0.17
        # through passages: across-wall segments at 0.3 and 1.8 m above base
        ul = np.arange(u0 + 0.125, u1 - 0.125 + 1e-9, 0.25)
        passages = {}
        for h in (0.3, 1.8):
            P0 = O + ul[:, None] * T3 - 25 * N3 + np.array([0, base_y + h, 0])
            P1 = O + ul[:, None] * T3 + 25 * N3 + np.array([0, base_y + h, 0])
            blocked = seg_hits(P0, P1, loc_solid)
            passages[str(h)] = runs(~blocked, ul)
        # support under the open passage columns at 0.3 m
        openu = np.zeros(len(us), bool)
        for r0, r1, _w in passages["0.3"]:
            openu |= (us >= r0 - 0.125) & (us <= r1 + 0.125)
        colmask = np.tile(openu, len(vs))
        passage_support = {"samples": int(colmask.sum()), "walkHit": int((walk & colmask).sum()),
                           "fraction": round(float((walk & colmask).sum() / max(colmask.sum(), 1)), 4),
                           "unsupportedAlongV": runs(~(walk.reshape(len(vs), len(us))[:, openu].all(1)), vs) if openu.any() else []}
        # up-facing tread heights between base+0.4 and wall top - 0.2 inside the gap footprint
        lt = near(np.concatenate([loc_solid, loc_ground]), cx, cz, 25)
        nrm3 = np.cross(lt[:, 1] - lt[:, 0], lt[:, 2] - lt[:, 0])
        area = 0.5 * np.linalg.norm(nrm3, axis=1)
        ny = np.where(area > 0, nrm3[:, 1] / np.maximum(2 * area, 1e-12), 0)
        cy = lt[:, :, 1].mean(1)
        cc = lt.mean(1)
        cu = (cc[:, [0, 2]] - [cx, cz]) @ tan
        cv = (cc[:, [0, 2]] - [cx, cz]) @ nrm
        wall_top = float(wv[:, 1].max())
        sel = (np.abs(ny) > 0.7) & (cy > base_y + 0.4) & (cy < wall_top - 0.2) & (np.abs(cu) < 20) & (np.abs(cv) < 20)
        hb = {}
        for yv, ar in zip(np.round(cy[sel] * 4) / 4, area[sel]):
            hb[str(round(float(yv), 2))] = round(hb.get(str(round(float(yv), 2)), 0) + float(ar), 3)
        # wall-end seam residual: distance of each wall end-cap vertex to the nearest gate-owned triangle
        seams = {}
        gate_owned = near(np.concatenate(list(body.values())), cx, cz, 30) if body else np.zeros((0, 3, 3))
        for side, edge in (("minus", gap[0]), ("plus", gap[1])):
            if edge is None:
                continue
            capm = band & (np.abs(tu - edge) < 0.02)
            capv = wv[np.hypot(*(wv[:, [0, 2]] - [cx, cz]).T) < 70][capm] if capm.any() else np.zeros((0, 3))
            if len(gate_owned) and len(capv):
                dd = [point_tri_dist(v, gate_owned) for v in capv]
                seams[side] = {"capVertices": int(len(capv)), "maxResidual_m": round(max(dd), 5), "minResidual_m": round(min(dd), 5)}
            else:
                seams[side] = {"capVertices": int(len(capv)), "maxResidual_m": None, "note": "no gate-owned geometry at site"}
        sites.append({
            "featureId": fid, "name": gdiag["name"], "card": SITE_CARD.get(fid),
            "wallEndSeams": seams,
            "cProjectionGltf": [round(cx, 3), round(cz, 3)],
            "wallTangentXZ": [round(float(tan[0]), 5), round(float(tan[1]), 5)],
            "wallGapEdgesU": gap, "wallGapWidth": round(gap[1] - gap[0], 3) if None not in gap else None,
            "wallTopY": round(wall_top, 3),
            "gateBodiesPresent": present,
            "groundSupport": {"samples": int(hit.size), "walkHitBelowCap": int(walk.sum()), "walkCapY": WALK_CAP,
                              "walkFraction": round(float(walk.mean()), 4),
                              "yMin": round(float(np.nanmin(gy)), 3) if hit.any() else None,
                              "yMax": round(float(np.nanmax(gy)), 3) if hit.any() else None,
                              "grid": "u in wall gap (0.5 m), v in +-20 m across wall (0.5 m)"},
            "groundSupportDefaultState": {"samples": int(dhit.size), "walkHitBelowCap": int(dhit.sum()),
                                          "walkFraction": round(float(dhit.mean()), 4),
                                          "nodes": [i for i in dground_ids if len(near(world_tris[i][0], cx, cz, 45))]},
            "baseYUsed": round(base_y, 3),
            "throughClearRunsU": passages,
            "passageSupport": passage_support,
            "maxRiseBetweenTreadBins": max_rise(hb, base_y, wall_top),
            "upFacingTreadAreaByHeight": hb,
        })
    report["sites"] = sites

    # ---------------------------------------------------------- 4. declared counts
    card = json.load(open(city + "p-luoyang.asset.json", encoding="utf-8"))
    # LF-normalised: a Windows autocrlf checkout and the committed bytes must hash the same (LY-001 C8 finding)
    raw = open(city + "p-luoyang.asset.json", "rb").read()
    report["projectCardSha256"] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    report["projectCardSha256Raw"] = hashlib.sha256(raw).hexdigest()
    report["projectCardDeclared"] = {
        "chapterWalls": next((c for c in card.get("chapters", []) if c.get("id") == "walls"), None),
        "progressWalls": [p for p in card.get("progress", []) if p.get("chapter") == "walls"],
    }
    report["counts"] = {
        "gateCards": len(cards),
        "wallSegmentNodes": len(wall_ids),
        "gateRegionNodesInCity": len(body_ids),
        "gateSitesWithBodyInCity": sum(1 for s in sites if s.get("gateBodiesPresent")),
        "gateSitesWithBodyInCityNames": [s["name"] for s in sites if s.get("gateBodiesPresent")],
        "researchGateModels": sorted(r["id"] for r in d.get("researchModels", []) if r["id"] in RESEARCH_GATES),
    }
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", required=True)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sites", default="all")
    a = ap.parse_args()
    d = json.load(open(a.dump, encoding="utf-8"))
    report = measure(a.lab, d, a.sites)
    report["dumpSha256"] = sha_file(a.dump)
    json.dump(report, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
