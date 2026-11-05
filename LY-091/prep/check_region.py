"""LY-091 region acceptance checker (framework, read-only).

  python -I check_region.py --baseline baseline-bce3211.json --lab <tree> --dump <city dump of that tree>
                            [--manifest batch-manifest.json] --out result.json
  python -I check_region.py --selftest --baseline baseline-bce3211.json --lab D:/GitHub/creation-notebook-lab
                            --dump _city-dump.json --out selftest.json

Every check returns PASS / FAIL / NOT_IN_BATCH. A FAIL never becomes PASS by being
"not measured"; anything the batch claims but the tree does not show is a FAIL.

Batch manifest (written by the batch owner, bound by SHA in the result):
{
  "batchId": "...", "baseCommit": "<main sha>", "selected_tasks": ["LY-015", ...],
  "dependency_closure": [...], "excluded_regions": [...],
  "replaces": {"<old nodeId>": "<new nodeId or null>"},      # old nodes allowed to change/hide
  "addedNodes": {"<nodeId>": {"task": "LY-0xx", "site": "gate_kaiyang_B", "exclusiveGroup": "kaiyang-body"}},
  "files": {"<repo-relative path>": "<sha256>"},             # whitelist of new/changed public files
  "declaredInCityGateNames": ["雍门", "广阳门", ...],          # what the card/chapter text will claim
  "siteClaims": {"gate_kaiyang_B": {"minClearWidth_m": 3.0, "throughHeights": [0.3, 1.8],
                  "passageSupportFraction": 1.0, "supportVRange_m": [-20, 20], "climbMaxRise_m": 0.25}}
}
"""
import argparse
import copy
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline_ly091 import measure, GATE_CARDS, LIMIT, GLB, city_matrix, asset_file, down_hits  # noqa: E402
import numpy as np  # noqa: E402

PORT_REGISTRY = "D:/GitHub/creation-notebook-workpacks/LY-006/registry/ports.json"

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def res(cid, ok, detail, na=False):
    return {"check": cid, "result": "NOT_IN_BATCH" if na else ("PASS" if ok else "FAIL"), "detail": detail}


def compare(base, cand, man, lab):
    out = []
    man = man or {}
    replaces = man.get("replaces", {})
    added = man.get("addedNodes", {})
    claims = man.get("siteClaims", {})

    # C1 gate family stays 12, no duplicate / unexpected gate cards
    gf = cand["gateFamily"]
    out.append(res("C1-gate-family-12", gf["cardCount"] == 12 and not gf["missing"] and not gf["unexpected"],
                   {"count": gf["cardCount"], "missing": gf["missing"], "unexpected": gf["unexpected"]}))

    # C2 old nodes unchanged unless declared replaced
    binv = {x["nodeId"]: x for x in base["inventory"]}
    cinv = {x["nodeId"]: x for x in cand["inventory"]}
    changed = []
    for nid, b in binv.items():
        if nid in replaces:
            continue
        c = cinv.get(nid)
        if c is None:
            changed.append({"node": nid, "why": "missing"})
            continue
        for k in ("sha256", "cityNodeRecordSha256", "cityAssetRecordSha256"):
            if b[k] != c[k]:
                changed.append({"node": nid, "why": k, "base": b[k][:16], "cand": c[k][:16]})
        bg = [(m["node"], m["geomSha256"], tuple(m["materials"])) for m in b["meshNodes"]]
        cg = [(m["node"], m["geomSha256"], tuple(m["materials"])) for m in c["meshNodes"]]
        if bg != cg:
            changed.append({"node": nid, "why": "meshNodes geometry/material"})
    out.append(res("C2-old-nodes-unchanged", not changed, {"changed": changed, "declaredReplaced": replaces}))

    # C3 no undeclared new region nodes; every new node owned by a selected task
    sel = set(man.get("selected_tasks", []))
    new_nodes = [n for n in cinv if n not in binv]
    undeclared = [n for n in new_nodes if n not in added]
    wrong_owner = [n for n in new_nodes if n in added and added[n].get("task") not in sel]
    out.append(res("C3-new-nodes-declared-and-owned", not undeclared and not wrong_owner,
                   {"newNodes": new_nodes, "undeclared": undeclared, "ownerNotSelected": wrong_owner}))

    # C4 mutual exclusion: per site at most one gate body family loaded by default; no duplicate sha loaded twice
    viol = []
    vis = lambda x: x.get("visibleByDefault", x["loadedByDefault"])  # noqa: E731  (v1 baselines lack the field)
    loaded = [x for x in cand["inventory"] if vis(x)]
    seen = {}
    for x in loaded:
        if x["sha256"] in seen and x["chapter"] != "terrain":
            viol.append({"duplicateSha": x["sha256"][:16], "nodes": [seen[x["sha256"]], x["nodeId"]]})
        seen.setdefault(x["sha256"], x["nodeId"])
    groups = {}
    for nid, meta in added.items():
        g = meta.get("exclusiveGroup")
        if g and nid in cinv and vis(cinv[nid]):
            groups.setdefault(g, []).append(nid)
    for g, ns in groups.items():
        if len(ns) > 1:
            viol.append({"exclusiveGroup": g, "loadedTogether": ns})
    for nid, new in replaces.items():
        if new and nid in cinv and vis(cinv[nid]) and new in cinv and vis(cinv[new]):
            viol.append({"oldAndNewBothLoaded": [nid, new]})
    out.append(res("C4-mutual-exclusion", not viol, viol))

    # C5 declared in-city gates == measured gate sites with a body == project-card count arithmetic
    meas = sorted(cand["counts"]["gateSitesWithBodyInCityNames"])
    decl = sorted(man.get("declaredInCityGateNames", base["counts"]["gateSitesWithBodyInCityNames"]))
    progs = cand.get("projectCardDeclared", {}).get("progressWalls") or []
    prog = next((p for p in progs if p.get("unit") == "件"), {})      # walls + in-city gate bodies
    resp = next((p for p in progs if p.get("unit") == "座"), {})      # gates kept as research only
    expected_count = cand["counts"]["wallSegmentNodes"] + len(meas)
    ok5 = (meas == decl and prog.get("count") == expected_count and resp.get("count") == 12 - len(meas)
           and cand["counts"]["gateCards"] == 12)
    out.append(res("C5-region-status-consistent", ok5,
                   {"measured": meas, "declared": decl, "cardInCityCount": prog.get("count"),
                    "walls+gates": expected_count, "cardResearchCount": resp.get("count"),
                    "12-inCity": 12 - len(meas)}))

    # C6 public file limits on every region GLB
    bad = [x["nodeId"] for x in cand["inventory"] if x["over15MB"] or x["externalImageUris"] or x["extensionsUsed"]]
    nonfinite = [x["nodeId"] for x in cand["inventory"] for m in x["meshNodes"] if not m["finite"]]
    out.append(res("C6-glb-limits", not bad and not nonfinite, {"overLimitOrExternalOrCompressed": bad, "nonFinite": nonfinite,
                                                                 "limitBytes": LIMIT}))

    # C7 manifest file whitelist SHA binding
    files = man.get("files", {})
    mism = []
    for rel, h in files.items():
        p = os.path.join(lab, rel)
        if not os.path.exists(p) or sha(p) != h:
            mism.append(rel)
    out.append(res("C7-sha-binding", not mism, {"mismatch": mism, "count": len(files)}, na=not files))

    # C8 per-site claims (passage width, support, climb) -- only for sites the batch claims
    csites = {s["featureId"]: s for s in cand["sites"]}
    for fid, cl in claims.items():
        s = csites.get(fid)
        fails = []
        if s is None or not s.get("gateBodiesPresent"):
            fails.append("no gate body in city at site")
        else:
            for h in cl.get("throughHeights", [0.3, 1.8]):
                rr = s["throughClearRunsU"].get(str(h), [])
                if not rr or max(r[2] for r in rr) < cl.get("minClearWidth_m", 0):
                    fails.append("clear width < %.2f at %.1f m" % (cl.get("minClearWidth_m", 0), h))
            if s["passageSupport"]["fraction"] < cl.get("passageSupportFraction", 1.0):
                fails.append("passage support %.4f < %.4f" % (s["passageSupport"]["fraction"], cl.get("passageSupportFraction", 1.0)))
            if "climbMaxRise_m" in cl and (s["maxRiseBetweenTreadBins"]["maxRise"] or 99) > cl["climbMaxRise_m"]:
                fails.append("climb max rise %.2f > %.2f" % (s["maxRiseBetweenTreadBins"]["maxRise"], cl["climbMaxRise_m"]))
        out.append(res("C8-site:" + fid, not fails, fails))
    # sites not claimed: report as NOT_IN_BATCH, never PASS
    for fid in csites:
        if fid not in claims:
            out.append(res("C8-site:" + fid, False, "not claimed by this batch", na=True))

    return out


def c10_ports(man, cand, lab, dump, registry=PORT_REGISTRY):
    """C10: every port the batch claims uses a registry portId + version (LY-006), its world position is within
    the port's tolerance_m (LY-005: position 0.005 m, elevation 0.002 m), and for ground/threshold/floor ports a
    drawn surface (region-open state) exists directly under the port within the elevation tolerance."""
    claims = (man or {}).get("ports", [])
    if not claims:
        return res("C10-ports", True, "no ports claimed by this batch", na=True)
    reg = json.load(open(registry, encoding="utf-8"))["ports"]
    reg = {x["portId"]: x for x in (reg if isinstance(reg, list) else reg.values())}
    d = json.load(open(dump, encoding="utf-8")) if isinstance(dump, str) else dump
    A = {x["id"]: x for x in d["assets"]}
    N = {x["id"]: x for x in d["nodes"]}
    city = lab.replace("\\", "/") + "/docs/cities/luoyang/"
    tris = [GLB(asset_file(city, A[N[i]["asset"]])).world_triangles(city_matrix(N[i]))[0]
            for i in cand["regionNodeIds"] + cand["terrainNodeIds"] if i in N]
    tris = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
    fails, rows = [], []
    for c in claims:
        r = reg.get(c["portId"])
        row = {"portId": c["portId"]}
        if r is None:
            fails.append({"portId": c["portId"], "why": "not in LY-006 registry"}); continue
        if c.get("version") != r["version"]:
            fails.append({"portId": c["portId"], "why": "version %s != registry %s" % (c.get("version"), r["version"])}); continue
        tol = r.get("tolerance_m") or {"position": 0.005, "elevation": 0.002}
        w = np.array(c["world"], float)
        rw = np.array(r["world"]["position"], float) if r.get("world") and r["world"].get("position") else None
        if rw is not None:
            dh = float(np.hypot(*(w[[0, 2]] - rw[[0, 2]]))); dy = abs(float(w[1] - rw[1]))
            row.update(dPlan_m=round(dh, 6), dY_m=round(dy, 6))
            if dh > tol["position"] or dy > tol["elevation"]:
                fails.append({"portId": c["portId"], "why": "world off registry", "dPlan_m": dh, "dY_m": dy})
        if r.get("kind") in ("ground", "threshold", "floor"):
            hy = down_hits(np.array([[w[0], w[2]]]), tris, w[1] + 0.05)[0]
            row["surfaceY"] = None if not np.isfinite(hy) else round(float(hy), 6)
            if not np.isfinite(hy) or abs(hy - w[1]) > tol["elevation"]:
                fails.append({"portId": c["portId"], "why": "no drawn surface within elevation tolerance", "surfaceY": row["surfaceY"], "portY": float(w[1])})
        rows.append(row)
    return res("C10-ports", not fails, {"fails": fails, "checked": rows, "registrySha256": sha(registry)})


def c9_rollback(base, cand):
    """C9: the rollback tree must reproduce the baseline exactly (inventory, gate family, sites, counts).
    Environment fields (checkout path, HEAD, dirty flag, dump hash) and absolute paths are ignored."""
    diffs = []
    bi = {x["nodeId"]: x for x in base["inventory"]}
    ci = {x["nodeId"]: x for x in cand["inventory"]}
    for nid in sorted(set(bi) | set(ci)):
        if nid not in ci:
            diffs.append({"node": nid, "why": "missing after rollback"})
        elif nid not in bi:
            diffs.append({"node": nid, "why": "left behind after rollback"})
        else:
            for k in ("sha256", "cityNodeRecordSha256", "cityAssetRecordSha256", "visibleByDefault", "drawnWhenRegionOpen"):
                if bi[nid].get(k) != ci[nid].get(k):
                    diffs.append({"node": nid, "why": k})
            if [m["geomSha256"] for m in bi[nid]["meshNodes"]] != [m["geomSha256"] for m in ci[nid]["meshNodes"]]:
                diffs.append({"node": nid, "why": "meshNodes geometry"})

    def strip(cards):
        return [dict({k: v for k, v in c.items() if k != "files"},
                     files=[{k: v for k, v in f.items() if k != "path"} for f in c["files"]]) for c in cards]
    if strip(base["gateFamily"]["cards"]) != strip(cand["gateFamily"]["cards"]):
        diffs.append({"why": "gateFamily cards differ"})
    bs = {s["featureId"]: s for s in base["sites"]}
    for s in cand["sites"]:
        if s["featureId"] in bs and json.dumps(bs[s["featureId"]], sort_keys=True) != json.dumps(s, sort_keys=True):
            diffs.append({"site": s["featureId"], "why": "site measurement differs"})
    if base["counts"] != cand["counts"]:
        diffs.append({"why": "counts differ", "base": base["counts"], "cand": cand["counts"]})
    if base.get("projectCardSha256") != cand.get("projectCardSha256"):
        diffs.append({"why": "project card sha differs"})
    return res("C9-rollback-reproduces-baseline", not diffs, diffs)


def verdict(rows):
    fails = [r["check"] for r in rows if r["result"] == "FAIL"]
    return {"verdict": "BLOCK" if fails else "PASS-FOR-CLAIMED-SCOPE", "failed": fails}


# ------------------------------------------------------------------ self test
def selftest(base, lab, dump, outdir):
    d0 = json.load(open(dump, encoding="utf-8"))
    cases = []

    def run(name, d, man, expect_fail):
        cand = measure(lab, d, "gate_yong_B,gate_guangyang_B,gate_kaiyang_B")
        # restrict baseline sites to the same subset for comparison
        rows = compare(base, cand, man, lab)
        v = verdict(rows)
        ok = (v["verdict"] == "BLOCK") == expect_fail
        cases.append({"case": name, "expectFail": expect_fail, "verdict": v, "selftestOk": ok})

    yong_claim = {"siteClaims": {"gate_yong_B": {"minClearWidth_m": 2.5, "throughHeights": [0.3, 1.8],
                                                 "passageSupportFraction": 0.475}}}
    # P1: baseline against itself, claiming only what baseline actually shows
    run("P1-baseline-self", copy.deepcopy(d0), yong_claim, False)
    # N1: move one old wall node by 1 cm
    d = copy.deepcopy(d0)
    nd = next(n for n in d["nodes"] if n["id"] == "wall-A-wall-05")
    nd["position"] = [0.01, 0, 0]
    run("N1-old-wall-moved-1cm", d, yong_claim, True)
    # N2: co-load a second copy of the Yong body under a new undeclared id
    d = copy.deepcopy(d0)
    dup = copy.deepcopy(next(n for n in d["nodes"] if n["id"] == "yong-gate-body"))
    dup["id"] = "yong-gate-body-dup"
    d["nodes"].append(dup)
    next(c for c in d["chapters"] if c["id"] == "yong-gate")["nodeIds"].append("yong-gate-body-dup")
    run("N2-duplicate-body-coloaded", d, yong_claim, True)
    # N3: drop the Yong apron/wings -> support claim must fail
    d = copy.deepcopy(d0)
    ch = next(c for c in d["chapters"] if c["id"] == "yong-gate")
    ch["nodeIds"] = [x for x in ch["nodeIds"] if x != "yong-gate-interface"]
    # v2: the node is initial:true, so dropping it from nodeIds alone would still draw it; remove the node itself
    d["nodes"] = [n for n in d["nodes"] if n["id"] != "yong-gate-interface"]
    man = dict(yong_claim, replaces={"yong-gate-interface": None})
    run("N3-apron-removed-support-claim", d, man, True)
    # N4: claim Kaiyang in city while only cards exist
    run("N4-claim-kaiyang-not-in-city", copy.deepcopy(d0),
        {"siteClaims": {"gate_kaiyang_B": {"minClearWidth_m": 3.0}}, "declaredInCityGateNames": ["雍门", "广阳门", "开阳门"]}, True)
    # N5: whitelist SHA mismatch
    run("N5-sha-mismatch", copy.deepcopy(d0),
        dict(yong_claim, files={"docs/cities/luoyang/assets/city-wall/A/wall-05.glb": "0" * 64}), True)
    # N6: claim a climb route at Yong (baseline has none: coarse max rise 1.25 m)
    run("N6-claim-climb-yong", copy.deepcopy(d0),
        {"siteClaims": {"gate_yong_B": {"minClearWidth_m": 2.5, "passageSupportFraction": 0.4, "climbMaxRise_m": 0.25}}}, True)
    # N7: corrupt a wall GLB copy (header length) and point the asset at it -> reader must refuse
    neg = os.path.join(outdir, "_neg")
    os.makedirs(neg, exist_ok=True)
    src = os.path.join(lab, "docs/cities/luoyang/assets/city-wall/A/wall-05.glb")
    bad = os.path.join(neg, "wall-05-badlen.glb")
    b = bytearray(open(src, "rb").read())
    b[8:12] = (len(b) + 4).to_bytes(4, "little")
    open(bad, "wb").write(bytes(b))
    d = copy.deepcopy(d0)
    next(a for a in d["assets"] if a["id"] == "wall-A-wall-05")["absPath"] = bad
    try:
        measure(lab, d, "gate_yong_B")
        cases.append({"case": "N7-bad-glb-length", "expectFail": True, "verdict": "reader accepted", "selftestOk": False})
    except ValueError as e:
        cases.append({"case": "N7-bad-glb-length", "expectFail": True, "verdict": "reader refused: %s" % e, "selftestOk": True})
    # N8: a 13th gate card is detected (simulated by counting rule on an extra id)
    from baseline_ly091 import discover_gate_cards
    found = discover_gate_cards(lab) + ["m-luoyang-guangyang2-gate"]
    cases.append({"case": "N8-thirteenth-gate-card", "expectFail": True,
                  "verdict": "count=%d" % len(found), "selftestOk": len(found) != 12})
    shutil.rmtree(neg, ignore_errors=True)

    # ---- v2 cases (added 2026-11-06 after the cad338b drift replay exposed v1 blind spots)
    # P2: the same tree dumped from another checkout path (url/nearUrl resolve differently) must PASS
    d = copy.deepcopy(d0)
    for a_ in d["assets"]:
        for k in ("url", "nearUrl"):
            if k in a_:
                a_[k] = "file:///X:/elsewhere/" + a_[k].rsplit("/docs/", 1)[-1]
    run("P2-relocated-checkout-urls", d, yong_claim, False)
    # N9: an undeclared default-visible far-tier copy listed only by its own chapter field (not in nodeIds)
    d = copy.deepcopy(d0)
    far = copy.deepcopy(next(n for n in d["nodes"] if n["id"] == "yong-gate-body"))
    far["id"] = "yong-gate-body-far-undeclared"
    far["chapter"] = "walls"
    d["nodes"].append(far)
    run("N9-chapter-field-only-node", d, yong_claim, True)
    # C9 rollback cases use a full-site measurement so counts are comparable with the baseline
    def run_c9(name, dd, expect_fail):
        cand = measure(lab, dd)
        r = c9_rollback(base, cand)
        ok = (r["result"] == "FAIL") == expect_fail
        cases.append({"case": name, "expectFail": expect_fail,
                      "verdict": {"verdict": r["result"], "failed": [str(x)[:120] for x in r["detail"]][:6]}, "selftestOk": ok})
    run_c9("P3-rollback-exact", copy.deepcopy(d0), False)
    run_c9("N10-rollback-leaves-node", d, True)
    d = copy.deepcopy(d0)
    next(n for n in d["nodes"] if n["id"] == "wall-A-wall-03")["initial"] = False
    run_c9("N11-rollback-hides-old-wall", d, True)
    # C10 port cases (LY-005 frozen Yong ports imported into the LY-006 registry)
    cand0 = measure(lab, d0, "gate_yong_B")
    reg = json.load(open(PORT_REGISTRY, encoding="utf-8"))["ports"]
    reg = {x["portId"]: x for x in (reg if isinstance(reg, list) else reg.values())}
    good = [{"portId": k, "version": reg[k]["version"], "world": reg[k]["world"]["position"]}
            for k in ("yong-gate:passage-C:threshold-inner", "yong-gate:passage-C:threshold-outer", "yong-gate:passage-N:threshold-inner")]

    def run_c10(name, ports, expect_fail):
        r = c10_ports({"ports": ports}, cand0, lab, d0)
        ok = (r["result"] == "FAIL") == expect_fail
        cases.append({"case": name, "expectFail": expect_fail, "verdict": {"verdict": r["result"], "failed": r["detail"]["fails"] if isinstance(r["detail"], dict) else r["detail"]}, "selftestOk": ok})
    run_c10("P4-yong-ports-on-surface", good, False)
    bad = copy.deepcopy(good[:1]); bad[0]["world"] = [bad[0]["world"][0], bad[0]["world"][1] + 0.01, bad[0]["world"][2]]
    run_c10("N12-port-elevation-off-1cm", bad, True)
    run_c10("N13-unknown-port-id", [dict(good[0], portId="yong-gate:passage-X:threshold-inner")], True)
    run_c10("N14-port-version-mismatch", [dict(good[0], version=2)], True)
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--lab", required=True)
    ap.add_argument("--dump", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--out", required=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rollback", action="store_true", help="--lab is the rollback tree: also run C9 against the baseline")
    a = ap.parse_args()
    base = json.load(open(a.baseline, encoding="utf-8"))
    if a.selftest:
        cases = selftest(base, a.lab, a.dump, os.path.dirname(os.path.abspath(a.out)))
        rep = {"baselineSha256": sha(a.baseline), "baselineHead": base["head"], "cases": cases,
               "allOk": all(c["selftestOk"] for c in cases)}
    else:
        man = json.load(open(a.manifest, encoding="utf-8")) if a.manifest else None
        cand = measure(a.lab, json.load(open(a.dump, encoding="utf-8")))
        rows = compare(base, cand, man, a.lab)
        rows.append(c10_ports(man, cand, a.lab, a.dump))
        if a.rollback:
            rows.append(c9_rollback(base, cand))
        rep = {"baselineSha256": sha(a.baseline), "baselineHead": base["head"], "candidateHead": cand["head"],
               "manifestSha256": sha(a.manifest) if a.manifest else None, "rows": rows, **verdict(rows)}
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in rep if k in ("allOk", "verdict", "failed")}, ensure_ascii=False))
    if a.selftest:
        for c in rep["cases"]:
            print(c["case"], c["selftestOk"], c["verdict"] if isinstance(c["verdict"], str) else c["verdict"]["failed"])


if __name__ == "__main__":
    main()
