# LY-010: re-check LY-005 rules R1/R2 (unit scale, rotation about Y only) on every node of the cad338b manifest,
# and that nodes present in both baselines kept identical matrices. Re-run: python -I source/contract_recheck.py
import json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(tag):
    return json.load(open(os.path.join(HERE, "qa", f"city-data.{tag}.dump.json"), encoding="utf-8"))


def check(m):
    if m is None:
        return True, 0.0, 0.0
    M = np.array(m, dtype=float).reshape(4, 4).T
    R = M[:3, :3]
    scale_dev = float(np.max(np.abs(np.linalg.norm(R, axis=0) - 1)))
    yonly = float(max(abs(R[1, 0]), abs(R[1, 2]), abs(R[0, 1]), abs(R[2, 1]), abs(R[1, 1] - 1)))
    return scale_dev < 1e-6 and yonly < 1e-6, scale_dev, yonly


A, B = load("bce3211"), load("cad338b")
na = {n["id"]: n for n in A["nodes"]}
rows, bad, drift = [], [], []
for n in B["nodes"]:
    ok, s, y = check(n.get("matrix"))
    rows.append({"id": n["id"], "ok": ok, "scaleDev": s, "nonYRot": y, "hasMatrix": n.get("matrix") is not None})
    if not ok:
        bad.append(n["id"])
    if n["id"] in na and na[n["id"]].get("matrix") != n.get("matrix"):
        drift.append(n["id"])
res = {"nodes": len(rows), "violations": bad, "matrixDriftOnOldNodes": drift,
       "maxScaleDev": max(r["scaleDev"] for r in rows), "maxNonYRot": max(r["nonYRot"] for r in rows), "rows": rows}
open(os.path.join(HERE, "qa", "contract-recheck-cad338b.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1))
print("nodes", res["nodes"], "violations", bad, "drift", drift, "maxScaleDev", res["maxScaleDev"], "maxNonYRot", res["maxNonYRot"])
