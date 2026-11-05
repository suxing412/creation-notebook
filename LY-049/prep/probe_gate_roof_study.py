# LY-049 prep: probe the not-in-city gate roof study (m-gate-roof-study) to see whether it would change the gate passage.
# python probe_gate_roof_study.py > gate-roof-study-probe.json
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb49
ML = 'D:/GitHub/creation-notebook-lab/docs/model-library/assets/'
def probe():
  out = {}
  for f in ('gate-near-local.glb', 'gate-original.glb', 'gate-roof.glb'):
      r = glb49.node_tris(ML + f)
      allv = np.concatenate([v.reshape(-1, 3) for v in r.values()])
      low = {k: v for k, v in r.items() if v.reshape(-1, 3)[:, 1].min() < 2.3}
      lowb = {k: [v.reshape(-1, 3).min(0).round(3).tolist(), v.reshape(-1, 3).max(0).round(3).tolist()] for k, v in list(low.items())[:40]}
      out[f] = dict(sha256=glb49.sha256(ML + f), nodes=len(r), bboxMin=allv.min(0).round(3).tolist(), bboxMax=allv.max(0).round(3).tolist(),
                    nodesReachingBelowY2p3=len(low), lowNodeBounds=lowb)
  return out


def body_match():
    """Compare the study's retained gate body (local, centred) with A2-LOD0 gate components shifted by anchor (-3.5, 0, 10.6)."""
    A2 = 'D:/GitHub/creation-notebook-lab/docs/cities/luoyang/assets/c02v/A2-LOD0-prototype.glb'
    a2 = glb49.node_tris(A2)
    st = glb49.node_tris(ML + 'gate-near-local.glb')
    res = {}
    for short in ('architecture_C_plain_timber.001', 'architecture_C_whitebox_earth_wall.001'):
        s = st['original_gate_C02-010__' + short].reshape(-1, 3) + np.array([-3.5, 0, 10.6])
        t = a2[short]; mx, mn = t.max(1), t.min(1)
        t = t[(mn[:, 0] >= -5.0 - 1e-4) & (mx[:, 0] <= -2.0 + 1e-4) & (mn[:, 2] >= 9.4 - 1e-4) & (mx[:, 2] <= 11.8 + 1e-4)].reshape(-1, 3)
        S = {tuple(v) for v in s.round(4)}; T = {tuple(v) for v in t.round(4)}
        res[short] = dict(studyVerts=len(S), a2GateVerts=len(T), studyMinusA2=len(S - T), a2MinusStudy=len(T - S))
    return res


if __name__ == '__main__':
    print(json.dumps(dict(probe=probe(), bodyMatchVsA2Gate_anchor=[-3.5, 0, 10.6], bodyMatch=body_match()), indent=1))
