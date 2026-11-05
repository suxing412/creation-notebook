"""LY-091 prep: build inputs.json (path, sha256, git blob, load state, loader code location). Read-only on the lab.

v2 (2026-11-06): `sha256` is now the COMMITTED bytes (git cat-file blob HEAD:path); the Windows
autocrlf working-tree bytes are kept as `sha256Worktree` (v1 bound the CRLF bytes for every text file,
the same trap LY-001 reported as its C8). G / dependency package state is read live from workpacks/,
and origin/main drift (cad338b) is recorded from git objects only (no checkout, no write).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

LAB = sys.argv[1] if len(sys.argv) > 1 else "D:/GitHub/creation-notebook-lab"
# v2.1: everything is read from git objects at REV, never from the working tree. The lab checkout was
# fast-forwarded bce3211 -> cad338b by someone else mid-run (reflog 2026-11-06 00:34:10), which silently
# re-pointed a working-tree-based inputs.json at the wrong commit.
REV = sys.argv[2] if len(sys.argv) > 2 else "bce3211f818ee5a8bef1773539da70695ba37b17"
HERE = os.path.dirname(os.path.abspath(__file__))
CITY = LAB + "/docs/cities/luoyang/"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def git(*a):
    return subprocess.run(["git", "-C", LAB] + list(a), capture_output=True, text=True).stdout.strip()


def blob_sha(rev, rel):
    r = subprocess.run(["git", "-C", LAB, "cat-file", "blob", "%s:%s" % (rev, rel)], capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def show(rel):
    r = subprocess.run(["git", "-C", LAB, "cat-file", "blob", "%s:%s" % (REV, rel)], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def ls(dirrel):
    out = git("ls-tree", "--name-only", REV, dirrel.rstrip("/") + "/")
    return [x for x in out.splitlines() if x]


def line_of(relfile, needle):
    b = show(relfile)
    if b is None:
        return None
    for i, ln in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
        if needle in ln:
            return "%s:%d" % (relfile, i)
    return None


HEAD_IS_REV = git("rev-parse", "HEAD") == git("rev-parse", REV)


def row(rel, load, loader, role, **kw):
    b = show(rel)
    r = {"path": rel, "role": role, "exists": b is not None}
    if b is not None:
        cm = hashlib.sha256(b).hexdigest()
        wp = LAB + "/" + rel
        wt = sha(wp) if HEAD_IS_REV and os.path.exists(wp) else None
        r.update(sha256=cm, bytes=len(b), gitBlob=git("rev-parse", "%s:%s" % (REV, rel)),
                 sha256Worktree=wt, worktreeBytesDifferOnlyByCheckout=(wt is not None and wt != cm))
    r.update(loadedInCity=load, loaderRef=loader, **kw)
    return r


base = json.load(open(HERE + "/baseline-bce3211.json", encoding="utf-8"))
rows = []
D = "docs/cities/luoyang/"
CD = D + "city-data.mjs"
rows += [
    row(CD, "yes (manifest)", "docs/cities/luoyang/app.mjs:1 (import manifest)", "city manifest: assets/nodes/chapters/researchModels"),
    row(D + "city-renderer.mjs", "yes (renderer)", "docs/cities/luoyang/app.mjs:177 (dynamic import)",
        "default-load rule %s; chapter loadNodeIds %s; url/nearUrl %s" % (
            line_of(D + "city-renderer.mjs", "let loadedIds = new Set"),
            line_of(D + "city-renderer.mjs", "for (const nodeId of chapter.loadNodeIds"),
            line_of(D + "city-renderer.mjs", "const url = new URL(useNear"))),
    row(D + "app.mjs", "yes", "docs/cities/luoyang/index.html", "city page controller"),
    row(D + "index.html", "yes (entry)", "-", "city entry page; chapter card copy for walls"),
    row(D + "p-luoyang.asset.json", "no (card data, not fetched by scene)", "lab/tools/build_assets.py (site build)",
        "project card: chapter walls statusNote, progress walls count=14"),
    row(D + "data/west/city-wall-interface.json", "v1 archive only", line_of(D + "v1/wall-layer.mjs", "city-wall-interface.json"),
        "A=13 / B=12 expected roots, per-file sha; hard check in v1 wall layer"),
    row(D + "data/west/city-wall-constraints.json", "no (linked)", line_of(D + "v1/wall-layer.mjs", "city-wall-constraints.json"),
        "12 gate B points + C projections used for site sampling"),
    row(D + "data/west/road-plan.json", "no", "-", "gate cuts (e.g. gate_pingcheng_B no new gateway crossing)"),
    row(D + "data/evidence/evidence-geometry.json", "evidence layer", "-", "gate_*_B schematic points"),
    row("lab/data/assets.json", "no (site aggregate)", "lab/tools/build_assets.py output",
        "aggregate card list; bind the HEAD blob (sha256) only; working-tree state recorded per run"),
]
# region + terrain GLBs from the baseline inventory
for x in base["inventory"]:
    rel = x["path"]
    needle = rel.split("docs/cities/luoyang/")[-1] if "docs/cities/luoyang/" in rel else rel.split("/docs/")[-1].replace("library/", "../../library/")
    loader = line_of(CD, needle) or line_of(CD, os.path.basename(rel))
    load = ("default (initial)" if x.get("visibleByDefault", x["loadedByDefault"])
            else "chapter on demand (loadNodeIds)" if x.get("drawnWhenRegionOpen") else "replaced / not drawn")
    rows.append(row(rel, load, loader, "region node %s (%s)" % (x["nodeId"], x["chapter"]), nodeId=x["nodeId"]))
# exclusive B sample walls (v1 archive only)
for rel in sorted(x for x in ls(D + "assets/city-wall/B") if x.endswith(".glb")):
    rows.append(row(rel, "v1 archive only (sample B)", line_of(D + "v1/wall-layer.mjs", "assets/city-wall/"), "exclusive wall sample B"))
# gate card files
city_paths = {x["path"] for x in base["inventory"]}
for c in base["gateFamily"]["cards"]:
    cj = [x for x in ls("docs/library/models/%s" % c["cardId"]) if x.endswith(".asset.json")][0]
    rows.append(row(cj, "no (card)", "-", "gate card %s status=%s" % (c["cardId"], c["status"])))
    for f in c["files"]:
        if f["path"] in city_paths:
            continue
        rows.append(row(f["path"], "no (card file only)", "-", "%s | %s" % (c["cardId"], f["label"])))
# research model GLBs (walls chapter researchModelIds -> on-demand separate space)
dump = json.load(open(HERE + "/_city-dump.json", encoding="utf-8"))
A = {a["id"]: a for a in dump["assets"]}
for r in dump["researchModels"]:
    if r["id"] not in ("research-north13-kaiyang-K", "research-north13-pingcheng-P", "research-north13-shangxi-X",
                       "research-north13-yong-Y", "research-north13-zhongdong-Z", "research-mao-gate"):
        continue
    a = A[r["asset"]]
    rel = os.path.normpath(D + a["sourcePath"]).replace("\\", "/")
    rows.append(row(rel, "research on demand (separate space, cityPlacement=%s)" % r.get("cityPlacement"),
                    line_of(CD, a["sourcePath"]), "research model %s" % r["id"]))
# undeployed city-visible handoff (alternative baseline candidate; LY-010 decides)
for rel in sorted(x for x in ls("modeling-lab/review-batches/2026-11-04-city-visible") if "city-visible-web-handoff-v1-public.zip.part" in x):
    rows.append(row(rel, "no (undeployed handoff, mother 1e8c4d)", "-", "alternative-baseline evidence used by LY-017/018/019; not the docs city"))

own = []
for f in ("glbread.py", "baseline_ly091.py", "check_region.py", "dump_city.mjs", "make_inputs.py",
          "baseline-bce3211.json", "selftest-bce3211.json", "_city-dump.json",
          "drift-cad338b.json", "check-relocated-bce3211.json"):
    if not os.path.exists(HERE + "/" + f):
        continue
    own.append({"path": "workpacks/LY-091/prep/" + f, "sha256": sha(HERE + "/" + f)})

WP = os.path.dirname(os.path.dirname(HERE))


def pkg_state(seat):
    d = WP + "/" + seat
    st = {}
    if os.path.exists(d + "/status.json"):
        j = json.load(open(d + "/status.json", encoding="utf-8"))
        st = {"status": j.get("status"), "blockers": j.get("blockers"), "openItemCount": len(j.get("openItems") or [])}
    st.update(deliveryManifest=os.path.exists(d + "/delivery-manifest.json"),
              deliveryManifestSha256=sha(d + "/delivery-manifest.json") if os.path.exists(d + "/delivery-manifest.json") else None,
              prepOnly=os.path.isdir(d + "/prep") and not os.path.exists(d + "/status.json"),
              prepStatus=os.path.exists(d + "/prep/prep-status.json"), empty=not os.path.isdir(d) or not os.listdir(d))
    return st


ORIGIN = git("rev-parse", "origin/main")
drift_paths = ["docs/cities/luoyang/city-data.mjs", "docs/cities/luoyang/p-luoyang.asset.json",
               "docs/cities/luoyang/city-renderer.mjs", "docs/library/models/m-luoyang-yong-gate/m-luoyang-yong-gate.asset.json",
               "docs/cities/luoyang/progress-assets/yong-road-link-v2/source.json",
               "docs/cities/luoyang/progress-assets/yong-road-link-v2/yong-road-link-LOD0.glb",
               "docs/cities/luoyang/progress-assets/yong-road-link-v2/yong-road-link-LOD1.glb",
               "docs/cities/luoyang/progress-assets/yong-road-link-v2/yong-road-link-LOD2.glb",
               "docs/cities/luoyang/progress-assets/yong-road-link-v2/yong-road-receiver-component209.glb",
               "docs/cities/luoyang/progress-assets/north13-gates/luoyang-yong-gate-study-v1/models/yong-Y-LOD2.glb",
               "docs/cities/luoyang/progress-assets/yong-city-v1/yong-apron-LOD2.glb"]
drift = {"originMain": ORIGIN, "commitsAhead": git("rev-list", "--count", REV + ".." + ORIGIN),
         "log": git("log", "--oneline", REV + ".." + ORIGIN).splitlines(),
         "localHeadAtGeneration": git("rev-parse", "HEAD"),
         "files": [{"path": p_, "sha256AtBaseline": blob_sha(REV, p_), "sha256AtOrigin": blob_sha(ORIGIN, p_)} for p_ in drift_paths]}

out = {"seat": "LY-091", "baselineCommit": git("rev-parse", REV), "inputsVersion": "2.1",
       "readFrom": "git objects at baselineCommit (cat-file / ls-tree); working tree not read",
       "shaConvention": "sha256 = committed blob bytes; sha256Worktree = local autocrlf checkout bytes, only when local HEAD == baselineCommit, else null",
       "localHeadAtGeneration": git("rev-parse", "HEAD"),
       "inputs": rows, "prepArtifacts": own,
       "dependencyPackages": {k: pkg_state(k) for k in ["LY-015", "LY-017", "LY-018", "LY-019", "LY-020", "LY-085", "LY-089"]},
       "gPackages": {k: pkg_state(k) for k in ["LY-001", "LY-002", "LY-005", "LY-006", "LY-007", "LY-008", "LY-009", "LY-010"]},
       "originMainDrift": drift}
json.dump(out, open(HERE + "/inputs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(rows), "inputs")
