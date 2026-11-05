"""LY-050 prep: where exactly do the C02-010 local routes meet host solids?

usage: python -I probe_routes.py <lab_root> <out.json>
Body band: an obstacle blocks a walker only if it occupies y in (0.25, 2.0)
(C envelope: 0.05 m above city ground 0.20 up to 2.0 m). Plinth tops (0.42)
are reported as steps, not blocks. Lintels above 2.0 are reported separately.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glbmini as g  # noqa: E402
from measure_ly050 import raycast, corridor_mask, XC, ZC, NX, NZ, CELL, CAT, EXCLUDE  # noqa: E402

LAB, OUT = Path(sys.argv[1]), Path(sys.argv[2])
DOCS = LAB / "docs"


def main():
    res, _, _ = g.node_triangles(DOCS / "cities/luoyang/assets/c02v/A2-LOD0-prototype.glb")
    grids = {CAT[k]: raycast(v["tris"], XC, ZC) for k, v in res.items() if k not in EXCLUDE}
    body = np.zeros((NZ, NX), bool)
    over = np.zeros((NZ, NX), bool)
    for c in ("wall", "timber"):
        ymin, ymax, hits = grids[c]
        body |= (hits > 0) & (ymin < 2.0) & (ymax > 0.25)
        over |= (hits > 0) & (ymin >= 2.0)
    step = grids["plinth"][2] > 0
    lay = json.loads((DOCS / "cities/luoyang/data/c02v/layout.json").read_text(encoding="utf-8"))
    lot = next(l for l in lay["lots"] if l["id"] == "C02-010")
    out = {"body_band": [0.25, 2.0], "routes": {}}
    for k, v in lot["localRoutes"].items():
        poly = [[x, -y] for x, y in v]
        for hw in (0.0, 0.25, 0.4):
            cm = corridor_mask(poly, max(hw, CELL * 0.75))
            def cells(mask):
                jj, ii = np.nonzero(cm & mask)
                if len(ii) == 0:
                    return None
                xs, zs = XC[ii], ZC[jj]
                return {"area_m2": round(len(ii) * CELL * CELL, 4),
                        "x": [round(float(xs.min()), 3), round(float(xs.max()), 3)],
                        "z": [round(float(zs.min()), 3), round(float(zs.max()), 3)]}
            # split by segment to locate
            seg = []
            for s, (a, b) in enumerate(zip(poly[:-1], poly[1:])):
                sm = corridor_mask([a, b], max(hw, CELL * 0.75))
                jj, ii = np.nonzero(sm & body)
                seg.append({"seg": s, "from": a, "to": b,
                            "body_block_m2": round(len(ii) * CELL * CELL, 4),
                            "body_block_x": [round(float(XC[ii].min()), 3), round(float(XC[ii].max()), 3)] if len(ii) else None,
                            "body_block_z": [round(float(ZC[jj].min()), 3), round(float(ZC[jj].max()), 3)] if len(ii) else None,
                            "plinth_step_m2": round(float((sm & step).sum()) * CELL * CELL, 4)})
            out["routes"][f"{k}@hw{hw}"] = {"poly_glb_xz": poly, "body_block": cells(body),
                                            "overhead_only_ge2.0": cells(over & ~body),
                                            "plinth_step": cells(step), "segments": seg}
    # door openings: along the main-house front (z ~ -4.2) and west wing east face (x ~ -4.3)
    def scan_row(z):
        j = int(np.clip(np.floor((z - ZC[0]) / CELL + 0.5), 0, NZ - 1))
        row = body[j]
        runs, start = [], None
        for i, b in enumerate(row):
            if not b and start is None:
                start = i
            if b and start is not None:
                runs.append([round(float(XC[start] - CELL / 2), 3), round(float(XC[i - 1] + CELL / 2), 3)]); start = None
        if start is not None:
            runs.append([round(float(XC[start] - CELL / 2), 3), round(float(XC[-1] + CELL / 2), 3)])
        return runs
    def scan_col(x):
        i = int(np.clip(np.floor((x - XC[0]) / CELL + 0.5), 0, NX - 1))
        col = body[:, i]
        runs, start = [], None
        for j, b in enumerate(col):
            if not b and start is None:
                start = j
            if b and start is not None:
                runs.append([round(float(ZC[start] - CELL / 2), 3), round(float(ZC[j - 1] + CELL / 2), 3)]); start = None
        if start is not None:
            runs.append([round(float(ZC[start] - CELL / 2), 3), round(float(ZC[-1] + CELL / 2), 3)])
        return runs
    out["free_runs_rows_z"] = {str(z): scan_row(z) for z in (-6.0, -5.25, -4.6, -4.3, 11.0, 11.9)}
    out["free_runs_cols_x"] = {str(x): scan_col(x) for x in (-5.0, -4.6, -4.4, -4.2, -3.5)}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", OUT)


if __name__ == "__main__":
    main()
