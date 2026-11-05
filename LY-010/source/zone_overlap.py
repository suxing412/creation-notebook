# LY-010: do nodes added between bce3211 and cad338b fall inside any LY-006 registry v1 zone/envelope?
# AABB test only (OBB -> enclosing world AABB in XZ, Y range kept). Conservative: a hit means "look closer",
# a miss means the new node cannot touch that write zone. Not a mesh or solid collision test.
# Re-run: python -I source/zone_overlap.py
import json, math, os, hashlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZP = os.path.join(HERE, "..", "LY-006", "registry", "zones.json")


def obb_aabb(o):
    c, yaw, h = o["c"], o["yaw"], o["h"]
    ca, sa = abs(math.cos(yaw)), abs(math.sin(yaw))
    ex = ca * h[0] + sa * h[2]
    ez = sa * h[0] + ca * h[2]
    return [c[0] - ex, c[1] - h[1], c[2] - ez], [c[0] + ex, c[1] + h[1], c[2] + ez]


def hit(a, b, pad=0.0):
    return all(a[0][i] - pad <= b[1][i] and b[0][i] - pad <= a[1][i] for i in (0, 2))


def main():
    raw = open(ZP, "rb").read()
    z = json.loads(raw.decode("utf-8"))
    diff = json.load(open(os.path.join(HERE, "qa", "baseline-diff.json"), encoding="utf-8"))
    boxes = []
    for zz in z["zones"]:
        if zz.get("worldOBB"):
            boxes.append((zz["zoneId"], zz["seat"], obb_aabb(zz["worldOBB"])))
    for e in z["envelopes"]:
        if e.get("worldOBB"):
            boxes.append(("env:" + e["site"], e.get("owner"), obb_aabb(e["worldOBB"])))
    for s, v in z["sites"].items():
        env = v.get("envelope") or {}
        if env.get("frame") == "world":
            for b in env.get("boxes", [env.get("box")] if env.get("box") else []):
                boxes.append(("site:" + s, v.get("owner"), (b[0], b[1])))
    res = {"zonesSha256": hashlib.sha256(raw).hexdigest(), "zoneBoxesTested": len(boxes), "pad_m": 2.0, "nodes": {}}
    for nid, n in diff["nodes"]["addedDetail"].items():
        b = n["bounds"]
        nb = (b["min"], b["max"])
        hits = [{"zone": zid, "seat": seat} for zid, seat, zb in boxes if hit(nb, zb, 2.0)]
        res["nodes"][nid] = {"bounds": b, "hits": hits}
    out = os.path.join(HERE, "qa", "zone-overlap-cad338b.json")
    open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in res["nodes"].items():
        print(k, "hits:", [h["zone"] for h in v["hits"]][:12], "(n=%d)" % len(v["hits"]))
    print("zone boxes tested:", len(boxes))


if __name__ == "__main__":
    main()
