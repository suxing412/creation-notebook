# LY-010: read-only diff of the Luoyang city manifest between two frozen commits.
# Inputs: qa/city-data.<sha>.dump.json produced by LY-001/source/dump_city_data.mjs from
#   git -c core.autocrlf=false show <sha>:docs/cities/luoyang/city-data.mjs
# Output: qa/baseline-diff.json (stdout summary). Re-run: python -I source/baseline_diff.py
import json, hashlib, sys, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A, B = "bce3211", "cad338b"


def load(tag):
    p = os.path.join(HERE, "qa", f"city-data.{tag}.dump.json")
    raw = open(p, "rb").read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def strip(o):
    # url fields are resolved against the dump location, not part of the committed contract
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in ("url", "nearUrl")}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def by_id(lst):
    return {x["id"]: x for x in lst}


def diff_map(a, b):
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = {}
    for k in sorted(set(a) & set(b)):
        x, y = strip(a[k]), strip(b[k])
        if x != y:
            fields = sorted(f for f in set(x) | set(y) if x.get(f) != y.get(f))
            changed[k] = {f: {"before": x.get(f), "after": y.get(f)} for f in fields}
    return added, removed, changed


def main():
    da, sa = load(A)
    db, sb = load(B)
    out = {"base": A, "head": B, "dumpSha256": {A: sa, B: sb}}
    for key in ("assets", "nodes", "chapters"):
        ad, rm, ch = diff_map(by_id(da[key]), by_id(db[key]))
        out[key] = {"countBefore": len(da[key]), "countAfter": len(db[key]),
                    "added": ad, "removed": rm, "changed": ch,
                    "addedDetail": {k: strip(by_id(db[key])[k]) for k in ad}}
    ra = [strip(x) for x in da.get("researchModels", [])]
    rb = [strip(x) for x in db.get("researchModels", [])]
    out["researchModels"] = {"countBefore": len(ra), "countAfter": len(rb), "identical": ra == rb}
    out["counts"] = {"before": da["provenance"].get("counts"), "after": db["provenance"].get("counts")}
    out["sourceContracts"] = {"before": da["provenance"].get("sourceContracts"),
                              "after": db["provenance"].get("sourceContracts")}
    out["initialNodes"] = {
        A: sorted(n["id"] for n in da["nodes"] if n.get("initial") is not False),
        B: sorted(n["id"] for n in db["nodes"] if n.get("initial") is not False)}
    p = os.path.join(HERE, "qa", "baseline-diff.json")
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(out, ensure_ascii=False, indent=1))
    s = sys.stdout
    for key in ("assets", "nodes", "chapters"):
        o = out[key]
        s.write(f"{key}: {o['countBefore']} -> {o['countAfter']}  +{len(o['added'])} -{len(o['removed'])} ~{len(o['changed'])}\n")
        for k in o["added"]:
            s.write(f"  + {k}\n")
        for k in o["removed"]:
            s.write(f"  - {k}\n")
        for k, v in o["changed"].items():
            s.write(f"  ~ {k}: {', '.join(v)}\n")
    s.write(f"researchModels identical: {out['researchModels']['identical']}\n")
    s.write(f"counts: {out['counts']}\n")
    ia, ib = set(out['initialNodes'][A]), set(out['initialNodes'][B])
    s.write(f"initial: {len(ia)} -> {len(ib)}; +{sorted(ib-ia)} -{sorted(ia-ib)}\n")


if __name__ == "__main__":
    main()
