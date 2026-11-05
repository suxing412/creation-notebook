"""LY-050 prep measurements (read-only on the lab repo).

usage: python -I measure_ly050.py <lab_root> <city-dump.json> <ly006_zones.json> <out.json>

What it measures (all numbers land in <out.json>):
  1. SHA256 + byte size of every input GLB / data file.
  2. City fingerprint: canonical-JSON SHA256 per node / asset, 44-courtyard set,
     nodes sharing courtyard-A2, neighbours of C02-010, envelope intersections.
  3. A2 host occupancy (LOD0 and LOD1, kept nodes only) on a 0.05 m grid in the
     court frame: wall / plinth / timber footprint, roof underside height.
  4. City ground (ground-south) support height under the lot (world frame).
  5. LY-006 facility zones vs host solids, roof headroom, ground support, and vs
     the C02-010 local routes (layout.json, converted to GLB frame).
  6. Facility candidates (library GLB LOD0): bbox footprint, height, feasible
     placements inside their LY-006 zone and anywhere in the free yard.
  7. Budget: bytes / triangles of the full near set if everything were loaded.
Never writes to the lab repo.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glbmini as g  # noqa: E402

T = np.array([531.0, 0.0, -818.45])  # C02-010 calt translation (identity rotation)
CELL = 0.05
X0, X1, Z0, Z1 = -9.0, 9.0, -12.0, 12.0
NX, NZ = int(round((X1 - X0) / CELL)), int(round((Z1 - Z0) / CELL))
XC = X0 + CELL * (np.arange(NX) + 0.5)
ZC = Z0 + CELL * (np.arange(NZ) + 0.5)

HOST = {
    "LOD0": "cities/luoyang/assets/c02v/A2-LOD0-prototype.glb",
    "LOD1": "cities/luoyang/assets/c02v/A2-LOD1-prototype.glb",
}
EXCLUDE = {"site_lot", "site_neutral_lane", "designed_hardpacked_activity_ground"}
CAT = {
    "architecture_C_whitebox_earth_wall.001": "wall",
    "architecture_C_floor_plinth.001": "plinth",
    "architecture_C_plain_timber.001": "timber",
    "architecture_C_roof_rhythm_not_glaze_copy.001": "roof",
}
GROUND = "cities/luoyang/assets/ground-atomic/south.glb"
FAC = {
    "stove-A": ("library/models/m-luoyang-cooking-stove/files/stove-A-LOD0.glb", "LY-044"),
    "stove-B": ("library/models/m-luoyang-cooking-stove/files/stove-B-LOD0.glb", "LY-044"),
    "service-A(latrine-pen)": ("library/models/m-luoyang-service-court/files/service-A-LOD0.glb", "LY-045"),
    "service-enclosure": ("library/models/m-luoyang-household-service/files/service-enclosure-LOD0.glb", "LY-047"),
    "workshed": ("library/models/m-luoyang-workyard-shed/files/workshed-LOD0.glb", "LY-047"),
}
OTHER = [
    "library/models/m-luoyang-cooking-stove/files/stove-A-LOD1.glb",
    "library/models/m-luoyang-cooking-stove/files/stove-B-LOD1.glb",
    "library/models/m-luoyang-service-court/files/service-A-LOD1.glb",
    "library/models/m-luoyang-household-service/files/service-enclosure-LOD1.glb",
    "library/models/m-luoyang-workyard-shed/files/workshed-LOD1.glb",
    "library/models/m-luoyang-workyard-shed/files/workyard-LOD0.glb",
    "library/models/m-luoyang-residential-preparation/files/W2-stove-A-LOD0.glb",
    "library/models/m-luoyang-inner-door-components/files/paired-door-LOD0.glb",
    "library/models/m-luoyang-inner-door-components/files/single-door-LOD0.glb",
    "library/models/m-luoyang-wall-house-court/files/wall-house-LOD0.glb",
    "library/models/m-luoyang-residential-life/files/life-block-LOD0.glb",
]
DATA = [
    "cities/luoyang/city-data.mjs", "cities/luoyang/city-renderer.mjs", "cities/luoyang/app.mjs",
    "cities/luoyang/index.html", "cities/luoyang/p-luoyang.asset.json",
    "cities/luoyang/data/c02v/layout.json", "cities/luoyang/data/far44/instances-calt.json",
    "cities/luoyang/data/far44/preflight-contract.json", "cities/luoyang/data/west/ground-atomic-contract.json",
]


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def raycast(tris, xs, zs):
    """Vertical rays at cell centres. Returns (ymin, ymax, hits) grids (NZ, NX)."""
    nz, nx = len(zs), len(xs)
    ymin = np.full((nz, nx), np.inf)
    ymax = np.full((nz, nx), -np.inf)
    hits = np.zeros((nz, nx), np.int32)
    if len(tris) == 0:
        return ymin, ymax, hits
    x0, dx = xs[0], xs[1] - xs[0]
    z0, dz = zs[0], zs[1] - zs[0]
    for t in tris:
        a, b, c = t
        mnx, mxx = min(a[0], b[0], c[0]), max(a[0], b[0], c[0])
        mnz, mxz = min(a[2], b[2], c[2]), max(a[2], b[2], c[2])
        i0 = max(0, int(np.ceil((mnx - x0) / dx - 1e-9)))
        i1 = min(nx - 1, int(np.floor((mxx - x0) / dx + 1e-9)))
        j0 = max(0, int(np.ceil((mnz - z0) / dz - 1e-9)))
        j1 = min(nz - 1, int(np.floor((mxz - z0) / dz + 1e-9)))
        if i1 < i0 or j1 < j0:
            continue
        px, pz = np.meshgrid(xs[i0:i1 + 1], zs[j0:j1 + 1])
        v0x, v0z = c[0] - a[0], c[2] - a[2]
        v1x, v1z = b[0] - a[0], b[2] - a[2]
        den = v0x * v1z - v1x * v0z
        if abs(den) < 1e-14:
            continue  # vertical face: no vertical-ray hit
        wx, wz = px - a[0], pz - a[2]
        u = (wx * v1z - v1x * wz) / den
        v = (v0x * wz - wx * v0z) / den
        m = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        if not m.any():
            continue
        y = a[1] + u * (c[1] - a[1]) + v * (b[1] - a[1])
        sub = (slice(j0, j1 + 1), slice(i0, i1 + 1))
        ymin[sub] = np.where(m, np.minimum(ymin[sub], y), ymin[sub])
        ymax[sub] = np.where(m, np.maximum(ymax[sub], y), ymax[sub])
        hits[sub] += m
    return ymin, ymax, hits


def box_mask(box):
    (bx0, _, bz0), (bx1, _, bz1) = box
    mx = (XC > bx0) & (XC < bx1)
    mz = (ZC > bz0) & (ZC < bz1)
    return mz[:, None] & mx[None, :]


def corridor_mask(poly, hw):
    P = np.stack(np.meshgrid(XC, ZC), -1)  # (NZ,NX,2) as (x,z)
    m = np.zeros((NZ, NX), bool)
    for (ax, az), (bx, bz) in zip(poly[:-1], poly[1:]):
        a, b = np.array([ax, az]), np.array([bx, bz])
        ab = b - a
        t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.linalg.norm(P - (a + t[..., None] * ab), axis=-1)
        m |= d <= hw
    return m


def integral(bad):
    s = np.zeros((bad.shape[0] + 1, bad.shape[1] + 1), np.int64)
    s[1:, 1:] = bad.astype(np.int64).cumsum(0).cumsum(1)
    return s


def feasible(bad, w, d):
    """Count axis-aligned w x d (x,z metres) placements whose cells are all good."""
    cw, cd = int(np.ceil(w / CELL - 1e-9)), int(np.ceil(d / CELL - 1e-9))
    if cw > NX or cd > NZ:
        return 0, None
    s = integral(bad)
    tot = s[cd:, cw:] - s[:-cd, cw:] - s[cd:, :-cw] + s[:-cd, :-cw]
    ok = tot == 0
    n = int(ok.sum())
    if n == 0:
        return 0, None
    j, i = np.argwhere(ok)[0]
    return n, [round(X0 + i * CELL + w / 2, 3), round(Z0 + j * CELL + d / 2, 3)]


def main():
    global LAB, DUMP, ZONES, OUT, DOCS, CITY
    LAB, DUMP, ZONES, OUT = (Path(a) for a in sys.argv[1:5])
    DOCS = LAB / "docs"
    CITY = DOCS / "cities/luoyang"
    out = {"lab_root": str(LAB), "cell_m": CELL, "court_frame": "C02-010 local = world - (531,0,-818.45), yaw 0"}
    # 1. hashes
    files = {}
    for rel in list(HOST.values()) + [GROUND] + [v[0] for v in FAC.values()] + OTHER + DATA:
        p = DOCS / rel
        files["docs/" + rel] = {"sha256": g.sha256(p), "bytes": p.stat().st_size}
    out["files"] = files

    # 2. city fingerprint
    dump = json.loads(DUMP.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in dump["nodes"]}
    assets = {a["id"]: a for a in dump["assets"]}
    res_ch = next(c for c in dump["chapters"] if c["id"] == "residential")
    court_ids = [i for i in res_ch.get("nodeIds", []) if i in nodes]
    fp_nodes = {i: canon(n) for i, n in nodes.items()}
    fp_assets = {i: canon(a) for i, a in assets.items()}
    a2_users = sorted(i for i, n in nodes.items() if n.get("asset") == "courtyard-A2")
    c = nodes["C02-010"]
    cb = c["bounds"]
    neigh = []
    for i, n in nodes.items():
        b = n.get("bounds")
        if not b or i == "C02-010":
            continue
        gx = max(b["min"][0] - cb["max"][0], cb["min"][0] - b["max"][0], 0)
        gz = max(b["min"][2] - cb["max"][2], cb["min"][2] - b["max"][2], 0)
        if max(gx, gz) <= 30:
            neigh.append({"id": i, "asset": n.get("asset"), "gap_x": round(gx, 4), "gap_z": round(gz, 4),
                          "initial": n.get("initial", True), "chapter": n.get("chapter")})
    env = {"min": [522.0, -1.6, -830.45], "max": [540.0, 5.6, -806.45]}
    env_hits = []
    for i, n in nodes.items():
        b = n.get("bounds")
        if not b or i == "C02-010":
            continue
        if all(b["min"][k] < env["max"][k] and b["max"][k] > env["min"][k] for k in range(3)):
            env_hits.append({"id": i, "asset": n.get("asset"), "bounds": b})
    out["city"] = {
        "nodes": len(nodes), "assets": len(assets), "chapters": len(dump["chapters"]),
        "residential_nodeIds": len(court_ids),
        "residential_court_nodes": len([i for i in court_ids if nodes[i].get("asset", "").startswith("courtyard")]),
        "fingerprint_all_nodes": canon(sorted(fp_nodes.items())),
        "fingerprint_all_assets": canon(sorted(fp_assets.items())),
        "fingerprint_residential_44": canon([(i, fp_nodes[i]) for i in court_ids]),
        "C02-010": {"record_sha": fp_nodes["C02-010"], "matrix": c["matrix"], "asset": c["asset"],
                    "initial": c.get("initial", True), "chapter": c.get("chapter"), "bounds": cb},
        "courtyard-A2": {"record_sha": fp_assets["courtyard-A2"], "users": a2_users, "user_count": len(a2_users),
                         "excludeNodes": assets["courtyard-A2"].get("excludeNodes")},
        "neighbours_within_30m": sorted(neigh, key=lambda r: max(r["gap_x"], r["gap_z"])),
        "S-COURT_envelope_world": env,
        "envelope_intersects": env_hits,
        "ground_nodes": {i: {"initial": n.get("initial", True), "chapter": n.get("chapter")}
                         for i, n in nodes.items() if i.startswith("ground")},
        "nodes_with_replaces": [i for i, n in nodes.items() if n.get("replaces")],
    }

    # 3. host occupancy
    host = {}
    occ = {}
    for lod, rel in HOST.items():
        res, js, size = g.node_triangles(DOCS / rel)
        grids = {}
        for name, v in res.items():
            if name in EXCLUDE:
                continue
            cat = CAT.get(name, "other:" + name)
            grids[cat] = raycast(v["tris"], XC, ZC)
        solid = np.zeros((NZ, NX), bool)
        for k in ("wall", "plinth", "timber"):
            solid |= grids[k][2] > 0
        roofmin = grids["roof"][0]
        occ[lod] = {"solid": solid, "grids": grids, "roofmin": roofmin}
        a = CELL * CELL
        host[lod] = {
            "kept_nodes": sorted(k for k in res if k not in EXCLUDE),
            "excluded_present": sorted(k for k in res if k in EXCLUDE),
            "area_m2": {k: round(float((grids[k][2] > 0).sum() * a), 3) for k in grids},
            "solid_area_m2": round(float(solid.sum() * a), 3),
            "open_area_m2": round(float((~solid).sum() * a), 3),
            "open_unroofed_m2": round(float(((~solid) & ~np.isfinite(roofmin)).sum() * a), 3),
            "open_roofed_m2": round(float(((~solid) & np.isfinite(roofmin)).sum() * a), 3),
            "roof_underside_min_over_open": float(np.min(np.where(~solid, roofmin, np.inf))),
            "plinth_top_y": float(np.max(np.where(grids["plinth"][2] > 0, grids["plinth"][1], -np.inf))),
        }
    same = bool((occ["LOD0"]["solid"] == occ["LOD1"]["solid"]).all())
    rf0, rf1 = occ["LOD0"]["roofmin"], occ["LOD1"]["roofmin"]
    both = np.isfinite(rf0) & np.isfinite(rf1)
    host["LOD0_vs_LOD1"] = {
        "solid_footprint_identical": same,
        "roof_cover_cells_differ": int((np.isfinite(rf0) != np.isfinite(rf1)).sum()),
        "roof_underside_max_abs_diff": float(np.max(np.abs(rf0[both] - rf1[both]))) if both.any() else None,
    }
    out["host"] = host

    # 4. ground support
    gres, _, _ = g.node_triangles(DOCS / GROUND)
    gt = np.concatenate([v["tris"] for v in gres.values()])
    loc = gt - T
    sel = (loc[:, :, 0].max(1) >= X0 - 0.1) & (loc[:, :, 0].min(1) <= X1 + 0.1) & \
          (loc[:, :, 2].max(1) >= Z0 - 0.1) & (loc[:, :, 2].min(1) <= Z1 + 0.1)
    gmin, gmax, ghits = raycast(loc[sel], XC, ZC)
    gtop = np.where(ghits > 0, gmax, np.nan)
    out["ground"] = {
        "nodes": list(gres.keys()), "tris_total": int(len(gt)), "tris_in_lot": int(sel.sum()),
        "covered_cells": int((ghits > 0).sum()), "cells": NX * NZ,
        "top_y_min": float(np.nanmin(gtop)), "top_y_max": float(np.nanmax(gtop)),
    }

    # 5. zones vs host / routes
    zj = json.loads(ZONES.read_text(encoding="utf-8"))
    zones = [z for z in zj["zones"] if z.get("site") == "S-COURT" and z["seat"] in
             ("LY-042", "LY-044", "LY-045", "LY-046", "LY-047", "LY-049") and z["class"] in ("write", "cut")]
    lay = json.loads((CITY / "data/c02v/layout.json").read_text(encoding="utf-8"))
    lot = next(l for l in lay["lots"] if l["id"] == "C02-010")
    routes = {k: [[x, -y] for x, y in v] for k, v in lot["localRoutes"].items()}  # layout (x,y) -> GLB (x,-z)
    solid = occ["LOD0"]["solid"]
    roofmin = occ["LOD0"]["roofmin"]
    grids = occ["LOD0"]["grids"]
    a = CELL * CELL
    route_rep = {}
    for hw in (0.4, 0.6):
        for k, poly in routes.items():
            cm = corridor_mask(poly, hw)
            rec = {"poly_glb_xz": poly, "corridor_area_m2": round(float(cm.sum() * a), 3),
                   "blocked_by": {c: round(float((cm & (grids[c][2] > 0)).sum() * a), 3) for c in ("wall", "plinth", "timber")},
                   "low_roof_lt_2.0_m2": round(float((cm & (roofmin < 2.0)).sum() * a), 3),
                   "ground_uncovered_m2": round(float((cm & (ghits == 0)).sum() * a), 3),
                   "zone_overlap_m2": {}}
            for z in zones:
                ov = float((cm & box_mask(z["box"])).sum() * a)
                if ov > 0:
                    rec["zone_overlap_m2"][z["zoneId"]] = round(ov, 3)
            route_rep[f"{k}@hw{hw}"] = rec
    zone_rep = {}
    for z in zones:
        m = box_mask(z["box"])
        (zx0, zy0, zz0), (zx1, zy1, zz1) = z["box"]
        zone_rep[z["zoneId"]] = {
            "seat": z["seat"], "label": z["label"], "box": z["box"],
            "area_m2": round(float(m.sum() * a), 3),
            "overlap_m2": {c: round(float((m & (grids[c][2] > 0)).sum() * a), 3) for c in ("wall", "plinth", "timber")},
            "roofed_m2": round(float((m & np.isfinite(roofmin)).sum() * a), 3),
            "roof_underside_min": float(np.min(np.where(m, roofmin, np.inf))),
            "zone_top_vs_roof_conflict_m2": round(float((m & (roofmin < zy1)).sum() * a), 3),
            "ground_top_range": [float(np.nanmin(np.where(m, gtop, np.nan))), float(np.nanmax(np.where(m, gtop, np.nan)))],
        }
    pair = []
    for i in range(len(zones)):
        for j in range(i + 1, len(zones)):
            A, B = zones[i]["box"], zones[j]["box"]
            ov = [max(0.0, min(A[1][k], B[1][k]) - max(A[0][k], B[0][k])) for k in range(3)]
            vol = ov[0] * ov[1] * ov[2]
            if vol > 1e-9 and zones[i]["seat"] != zones[j]["seat"]:
                pair.append([zones[i]["zoneId"], zones[j]["zoneId"], round(vol, 4)])
    fac_union = np.zeros((NZ, NX), bool)
    for z in zones:
        if z["seat"] in ("LY-044", "LY-045", "LY-047") and z["class"] == "write":
            fac_union |= box_mask(z["box"])
    out["zones"] = zone_rep
    out["zone_pair_overlaps_cross_seat_m3"] = pair
    out["routes"] = route_rep
    out["yard_use_if_all_facility_zones_reserved"] = {
        "open_area_m2": host["LOD0"]["open_area_m2"],
        "facility_zone_union_m2": round(float(fac_union.sum() * a), 3),
        "facility_zone_union_on_open_m2": round(float((fac_union & ~solid).sum() * a), 3),
        "share_of_open": round(float((fac_union & ~solid).sum() / (~solid).sum()), 4),
    }

    # 6. facility candidates
    cor_any = np.zeros((NZ, NX), bool)
    for k, poly in routes.items():
        cor_any |= corridor_mask(poly, 0.4)
    fac_rep = {}
    total_bytes = files["docs/" + HOST["LOD0"]]["bytes"]
    total_tris = 0
    for name, (rel, seat) in FAC.items():
        res, js, size = g.node_triangles(DOCS / rel)
        allt = np.concatenate([v["tris"] for v in res.values()])
        b = g.bounds(allt)
        w, h, d = (b[1][0] - b[0][0]), (b[1][1] - b[0][1]), (b[1][2] - b[0][2])
        zbox = [z for z in zones if z["seat"] == seat and z["class"] == "write"]
        zm = np.zeros((NZ, NX), bool)
        for z in zbox:
            zm |= box_mask(z["box"])
        rec = {"file": "docs/" + rel, "seat_zone": [z["zoneId"] for z in zbox], "bytes": size, "tris": int(len(allt)),
               "nodes": {k: int(len(v["tris"])) for k, v in res.items()}, "bounds_local": b,
               "bbox_w_x": round(w, 4), "bbox_d_z": round(d, 4), "height": round(h, 4), "base_y": b[0][1]}
        for yaw, (ww, dd) in {"0/180": (w, d), "90/270": (d, w)}.items():
            low_roof = roofmin < (0.2 + h)  # facility placed on y=0.2
            bad_zone = ~zm | solid | low_roof
            bad_yard = solid | low_roof | cor_any
            nz_, ez = feasible(bad_zone, ww, dd)
            ny_, ey = feasible(bad_yard, ww, dd)
            nz2, _ = feasible(~zm | solid, ww, dd)  # ignoring roof headroom
            rec[f"yaw{yaw}"] = {"footprint": [round(ww, 3), round(dd, 3)],
                               "placements_in_zone": nz_, "example_centre_in_zone": ez,
                               "placements_in_zone_ignoring_roof": nz2,
                               "placements_free_yard_off_routes": ny_, "example_centre_yard": ey}
        fac_rep[name] = rec
        total_bytes += size
        total_tris += int(len(allt))
    out["facilities"] = fac_rep
    hostres, _, _ = g.node_triangles(DOCS / HOST["LOD0"])
    host_tris = sum(len(v["tris"]) for k, v in hostres.items() if k not in EXCLUDE)
    out["budget_all_LOD0_one_each"] = {
        "host_kept_tris": host_tris, "facility_tris": total_tris,
        "sum_bytes_host_plus_all_facilities": total_bytes,
        "under_15MB_if_baked_into_one_glb": total_bytes < 15_000_000,
        "note": "stove-A and stove-B are alternatives, service-enclosure and workshed are alternatives; sum is an upper bound",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", OUT)


if __name__ == "__main__":
    main()
