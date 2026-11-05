"""City fingerprint for LY-050 install / withdraw checks (read-only).

usage:
  python -I fingerprint.py make <city-dump.json> <lab_docs_cities_luoyang_dir> <out.json>
  python -I fingerprint.py diff <a.json> <b.json>           # exit 1 if any difference
  python -I fingerprint.py selftest <city-dump.json> <lab_docs_cities_luoyang_dir>

The fingerprint covers: every node record (canonical JSON SHA256), every asset
record, the residential chapter (nodeIds + loadNodeIds), the 44-court set, the
column-major matrices of all courtyard nodes, and SHA256 of every GLB a
courtyard or ground asset points at (far + near). city-dump.json comes from
dump_city.mjs (node import of city-data.mjs, url fields stripped).
"""
import copy
import hashlib
import json
import sys
from pathlib import Path


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def make(dump, city_dir=None):
    nodes = {n["id"]: n for n in dump["nodes"]}
    assets = {a["id"]: a for a in dump["assets"]}
    res = next(c for c in dump["chapters"] if c["id"] == "residential")
    courts = [i for i in res.get("nodeIds", []) if nodes.get(i, {}).get("asset", "").startswith("courtyard")]
    fp = {
        "counts": {"nodes": len(nodes), "assets": len(assets), "chapters": len(dump["chapters"]),
                   "residential_courts": len(courts),
                   "initial_nodes": sum(1 for n in nodes.values() if n.get("initial", True) is not False)},
        "node_sha": {i: canon(n) for i, n in sorted(nodes.items())},
        "asset_sha": {i: canon(a) for i, a in sorted(assets.items())},
        "residential_chapter_sha": canon(res),
        "court_ids": courts,
        "court_matrices": {i: nodes[i].get("matrix") for i in courts},
        "glb_sha": {},
    }
    if city_dir:
        city_dir = Path(city_dir)
        used = {nodes[i]["asset"] for i in courts} | {a for a in assets if a.startswith("ground")}
        for a in sorted(used):
            for key in ("sourcePath",):
                rel = assets[a].get(key)
                if rel:
                    fp["glb_sha"][rel] = sha_file(city_dir / rel)
            near = assets[a].get("nearSha256")
            if near:
                fp["glb_sha"][a + ":nearSha256(declared)"] = near
    fp["total"] = canon({k: v for k, v in fp.items() if k != "total"})
    return fp


def diff(a, b):
    out = []
    for k in ("counts", "residential_chapter_sha", "court_ids", "total"):
        if a.get(k) != b.get(k):
            out.append([k, a.get(k), b.get(k)])
    for k in ("node_sha", "asset_sha", "court_matrices", "glb_sha"):
        ka, kb = a.get(k, {}), b.get(k, {})
        for i in sorted(set(ka) | set(kb)):
            if ka.get(i) != kb.get(i):
                out.append([f"{k}.{i}", ka.get(i), kb.get(i)])
    return out


def selftest(dump, city_dir):
    base = make(dump, city_dir)
    cases = {}
    d = copy.deepcopy(dump)
    for n in d["nodes"]:
        if n["id"] == "C02-010":
            n["matrix"][12] += 0.001
    cases["C02-010 tx +1 mm"] = diff(base, make(d, city_dir))
    d = copy.deepcopy(dump)
    for n in d["nodes"]:
        if n["id"] == "C02-011":
            n["matrix"][14] -= 0.001
    cases["neighbour C02-011 tz -1 mm"] = diff(base, make(d, city_dir))
    d = copy.deepcopy(dump)
    d["nodes"].append({"id": "C02-010-extra", "asset": "courtyard-A2", "chapter": "residential", "matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 531, 0, -818.45, 1]})
    cases["extra node added"] = diff(base, make(d, city_dir))
    d = copy.deepcopy(dump)
    for c in d["chapters"]:
        if c["id"] == "residential":
            c["nodeIds"] = c["nodeIds"] + ["C02-010-life"]
    cases["residential count +1"] = diff(base, make(d, city_dir))
    d = copy.deepcopy(dump)
    for a in d["assets"]:
        if a["id"] == "courtyard-A2":
            a["excludeNodes"] = a["excludeNodes"][:2]
    cases["A2 excludeNodes changed"] = diff(base, make(d, city_dir))
    d = json.loads(json.dumps(dump, sort_keys=True))  # key order shuffled
    cases["key order only (must be identical)"] = diff(base, make(d, city_dir))
    res = {k: {"differences": len(v), "first": v[:3]} for k, v in cases.items()}
    ok = all(res[k]["differences"] > 0 for k in cases if not k.startswith("key order")) and \
        res["key order only (must be identical)"]["differences"] == 0
    return {"pass": ok, "base_total": base["total"], "cases": res}


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "make":
        dump = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        Path(sys.argv[4]).write_text(json.dumps(make(dump, sys.argv[3]), indent=1, ensure_ascii=False), encoding="utf-8")
        print("ok")
    elif mode == "diff":
        a, b = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[2:4])
        dd = diff(a, b)
        print(json.dumps(dd, ensure_ascii=False, indent=1))
        sys.exit(1 if dd else 0)
    elif mode == "selftest":
        dump = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        r = selftest(dump, sys.argv[3])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(0 if r["pass"] else 1)
