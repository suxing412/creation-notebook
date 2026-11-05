# LY-010: inventory of every model file listed on the asset cards this decision table selects from,
# hashed from committed bytes at the frozen G baseline (git show, read-only; no checkout, no writes to the lab repo).
# Usage: python -I source/candidate_inventory.py <lab_repo> <commit>
import json, os, posixpath, subprocess, sys, hashlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = [
    "m-luoyang-kaiyang-gate", "m-luoyang-pingcheng-gate", "m-luoyang-gu-gate", "m-luoyang-xia-gate",
    "m-luoyang-earthwall-family", "m-luoyang-yong-gate",
    "m-luoyang-market-frontage", "m-luoyang-market-modular-assembly", "m-market-functional", "m-well-family",
    "m-storage-functional", "m-luoyang-wuku",
    "m-courtyard-family", "m-luoyang-inner-door-components", "m-luoyang-wall-house-court",
    "m-luoyang-residential-preparation", "m-luoyang-cooking-stove", "m-luoyang-service-court",
    "m-luoyang-household-service", "m-luoyang-court-layout-kit",
    "m-luoyang-stable", "m-luoyang-tile-kiln", "m-luoyang-hand-mill", "m-luoyang-foot-pestle", "m-luoyang-workyard-shed",
    "m-luoyang-palace-admission-court", "m-luoyang-palace-guard", "m-luoyang-palace-sidehall",
    "m-luoyang-palace-paired-que", "m-luoyang-deyang-hall", "m-luoyang-yutang-halls", "m-luoyang-palace-gallery",
    "m-luoyang-gallery-access",
    "m-luoyang-biyong", "m-luoyang-mingtang", "m-luoyang-lingtai", "m-luoyang-taixue-a",
    "m-luoyang-stoneclassic-access-court", "m-luoyang-southern-altar", "m-luoyang-northern-altar",
    "m-luoyang-palace-waterway-interface", "m-passage-interface",
]


ALT = {  # cards kept under docs/model-library (older layout)
    "m-market-functional": "docs/model-library/m-market-functional.asset.json",
    "m-well-family": "docs/model-library/well-study/m-well-family.asset.json",
    "m-storage-functional": "docs/model-library/m-storage-functional.asset.json",
    "m-courtyard-family": "docs/model-library/m-courtyard-family.asset.json",
    "m-passage-interface": "docs/model-library/m-passage-interface.asset.json",
}


def git(repo, *a):
    return subprocess.run(["git", "-C", repo, "-c", "core.autocrlf=false", *a], capture_output=True, check=True).stdout


def main():
    repo, commit = sys.argv[1], sys.argv[2]
    full = git(repo, "rev-parse", commit).decode().strip()
    out = {"commit": full, "cards": {}}
    for c in CARDS:
        cardpath = ALT.get(c, f"docs/library/models/{c}/{c}.asset.json")
        base = posixpath.dirname(cardpath)
        cj = git(repo, "show", f"{full}:{cardpath}")
        card = json.loads(cj.decode("utf-8"))
        files = []
        for f in card.get("files", []):
            p = posixpath.normpath(posixpath.join(base, f["path"]))
            try:
                b = git(repo, "show", f"{full}:{p}")
                files.append({"path": p, "label": f.get("label"), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
            except subprocess.CalledProcessError:
                files.append({"path": p, "label": f.get("label"), "missing": True})
        out["cards"][c] = {"cardPath": cardpath, "cardSha256": hashlib.sha256(cj).hexdigest(), "status": card.get("status"),
                           "statusNote": card.get("statusNote"), "files": files}
    p = os.path.join(HERE, "qa", "candidate-inventory.json")
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(out, ensure_ascii=False, indent=1))
    n = sum(len(v["files"]) for v in out["cards"].values())
    miss = [f["path"] for v in out["cards"].values() for f in v["files"] if f.get("missing")]
    over = [(f["path"], f["bytes"]) for v in out["cards"].values() for f in v["files"] if f.get("bytes", 0) > 15_000_000]
    print("cards", len(out["cards"]), "files", n, "missing", len(miss), "over15MB", over)
    for m in miss:
        print("  missing", m)


if __name__ == "__main__":
    main()
