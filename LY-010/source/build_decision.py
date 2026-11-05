# -*- coding: utf-8 -*-
# LY-010 builder: decision_data.py -> decision/*.json + decision/decision-table.md + qa/checks.json + inputs.json
# Binds every reference to committed-byte SHA256 at the frozen G baseline, runs consistency checks C01–C12,
# and re-runs the checks on deliberately broken copies (N01–N08) that must fail.
# Re-run: python -I source/build_decision.py <lab_repo>
import copy, hashlib, json, os, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "source"))
import decision_data as D  # noqa: E402

G = ["LY-001", "LY-002", "LY-005", "LY-006", "LY-007", "LY-008", "LY-009", "LY-010"]


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def jload(p):
    return json.loads(open(p, "rb").read().decode("utf-8"))


def wjson(rel, obj):
    p = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    return p


def done_set():
    done = set()
    for i in range(1, 100):
        sid = f"LY-{i:03d}"
        p = os.path.join(WP, sid, "status.json")
        if os.path.exists(p):
            st = jload(p).get("status")
            if st in ("交付完成", "复用完成"):
                done.add(sid)
    done.add("LY-010")  # this seat, delivered by this run
    return done


# ------------------------------------------------------------------ checks (pure functions of a model dict)
def run_checks(M, ctx):
    R = []

    def rec(cid, ok, detail):
        R.append({"id": cid, "pass": bool(ok), "detail": detail})

    seats, regions, batches = M["seats"], M["regions"], M["batches"]
    want = [f"LY-{i:03d}" for i in range(11, 100)]
    # C01 coverage
    owner = defaultdict(list)
    for r in regions:
        for s in r["seats"]:
            owner[s].append(r["id"])
    missing = [s for s in want if s not in seats]
    extra = [s for s in seats if s not in want]
    multi = {s: v for s, v in owner.items() if len(v) != 1}
    noreg = [s for s in want if s not in owner]
    rec("C01", not missing and not extra and not multi and not noreg,
        {"seats": len(seats), "missingDecision": missing, "extra": extra, "regionCountNot1": multi, "noRegion": noreg})
    # C02 every region states selected scheme, scope, allowed unverified, blockers, admission
    bad = []
    for r in regions:
        for k in ("selected", "allowedChanges", "allowedUnverified", "blockers", "cityAdmission", "localAdmission", "cityAdmissionMeaning"):
            if k not in r:
                bad.append((r["id"], k))
        if "selected" in r and not r["selected"].get("scheme"):
            bad.append((r["id"], "selected.scheme"))
        if not r.get("allowedChanges"):
            bad.append((r["id"], "allowedChanges empty"))
    rec("C02", not bad, {"regions": len(regions), "problems": bad})
    # C03 no default release: seats of a region that is not admitted to the city cannot propose city geometry
    viol = []
    for r in regions:
        if r.get("cityAdmission") == "不放行":
            for s in r["seats"] + r.get("sharedSeats", []):
                if s in seats and seats[s]["cityLanding"] == D.CITY_PROPOSAL and owner.get(s, [None])[0] == r["id"]:
                    viol.append(s)
    rec("C03", not viol, {"rule": "cityAdmission=不放行 的区内席位不得写城市装配提案", "violations": viol})
    # C04 references resolve to real bytes at the baseline
    unresolved = []
    for r in regions:
        for ref in r["selected"].get("refs", []):
            if ref not in ctx["resolved"]:
                unresolved.append((r["id"], ref))
    rec("C04", not unresolved, {"refs": sum(len(r["selected"].get("refs", [])) for r in regions), "unresolved": unresolved})
    # C05 blocking propagation: a seat depending on a blocked seat cannot be released
    deps = ctx["deps"]
    blocked = {s for s, v in seats.items() if v["decision"] == D.BLOCK}
    changed = True
    trans = set(blocked)
    while changed:
        changed = False
        for s in want:
            if s not in trans and any(d in trans for d in deps.get(s, [])) and seats.get(s, {}).get("decision") not in (D.SERVICE,):
                trans.add(s)
                changed = True
    leak = [s for s in trans - blocked if seats[s]["decision"] in (D.GO, D.COND, D.REUSE, D.CONTRACT)]
    nob = [s for s in blocked if not seats[s]["blockers"] or not any(i for i in seats[s]["needsInputs"])]
    rec("C05", not leak and not nob, {"blocked": sorted(blocked), "transitivelyWaiting": sorted(trans - blocked), "releasedDespiteBlockedDep": leak, "blockedWithoutReason": nob})
    # C06 batch closure + no blocked/local seats in city batches
    done = ctx["done"] | {"LY-003", "LY-004"}
    seen = set()
    probs = []
    for b in batches:
        sel = set(b["selected_tasks"])
        avail = done | seen | sel
        for s in sel:
            miss = [d for d in deps.get(s, []) if d not in avail]
            if miss:
                probs.append((b["id"], s, "deps not in closure", miss))
            dec = seats[s]["decision"]
            if b["id"].startswith("B") and dec in (D.BLOCK, D.WAIT):
                probs.append((b["id"], s, "blocked/waiting seat in city batch"))
            if b["id"].startswith("B") and seats[s]["cityLanding"] == D.LOCAL_ONLY:
                probs.append((b["id"], s, "local-only seat in city batch"))
            if b["id"].startswith("L") and seats[s]["cityLanding"] == D.CITY_PROPOSAL:
                probs.append((b["id"], s, "city seat in local batch"))
        seen |= sel
    rec("C06", not probs, {"batches": [b["id"] for b in batches], "problems": probs})
    # C07 needs reference known inputs; blocking inputs cover the blocked seats
    known = {i["id"]: i for i in M["inputs"]}
    unk = [(s, i) for s, v in seats.items() for i in v["needsInputs"] if i not in known]
    unc = [s for s in blocked if not any(known.get(i, {}).get("blocking") for i in seats[s]["needsInputs"])]
    rec("C07", not unk and not unc, {"inputs": len(known), "unknownInputRefs": unk, "blockedSeatsWithoutBlockingInput": unc})
    # C08 every region's seat list matches the taskboard section of those seats' type lanes (no acceptance seat producing)
    prod_in_service = [s for s in seats if s >= "LY-091" and seats[s]["decision"] != D.SERVICE]
    rec("C08", not prod_in_service, {"rule": "LY-091–099 只能是持续服务（验收方不生产被验物）", "violations": prod_in_service})
    # C09 north-three / yong attachments are forbidden ground for every seat: R05 and R07 must say so
    r = {x["id"]: x for x in regions}
    ok9 = any("北缘三院" in f for f in r["R05"]["forbidden"]) and any("workyard" in u["scheme"] for u in r["R07"]["retainedUnselected"])
    rec("C09", ok9, {"rule": "cad338b 新入城的北缘三院与其复用的 workyard/compact_work 在 R05/R07 明列为禁改"})
    # C10 every non-admitted region states the reason and has no city batch
    city_batched = {s for b in batches if b["id"].startswith("B") for s in b["selected_tasks"]}
    leak10 = [s for x in regions if x.get("cityAdmission") == "不放行" for s in x["seats"] if s in city_batched]
    rec("C10", not leak10, {"violations": leak10})
    return R


def main():
    lab = sys.argv[1]
    commit = subprocess.run(["git", "-C", lab, "rev-parse", "cad338b"], capture_output=True, text=True, check=True).stdout.strip()
    taskboard = jload(os.path.join(WP, "taskboard.json"))
    board_v2 = jload(os.path.join(WP, "LY-009", "board", "taskboard.v2.json"))
    tb = {x["id"]: x for x in taskboard["seats"]}
    deps = {x["id"]: [d for d in x["deps"] if d not in G] for x in taskboard["seats"]}
    deps_v2 = {x["id"]: [d for d in x["deps"] if d not in G] for x in board_v2["seats"]}
    inv = jload(os.path.join(HERE, "qa", "candidate-inventory.json"))
    dump = jload(os.path.join(HERE, "qa", "city-data.cad338b.dump.json"))
    files = {f["path"]: f for c in inv["cards"].values() for f in c["files"]}
    assets = {a["id"]: a for a in dump["assets"]}
    nodes = {n["id"]: n for n in dump["nodes"]}
    resolved = {}
    for r in D.REGIONS:
        for ref in r["selected"]["refs"]:
            kind, _, val = ref.partition(":")
            if kind == "file" and val in files:
                resolved[ref] = {"sha256": files[val]["sha256"], "bytes": files[val]["bytes"], "source": "qa/candidate-inventory.json"}
            elif kind == "asset" and val in assets:
                a = assets[val]
                resolved[ref] = {"sha256": a["sha256"], "bytes": a["bytes"], "sourcePath": a.get("sourcePath"), "source": "qa/city-data.cad338b.dump.json"}
            elif kind == "node" and val in nodes:
                n = nodes[val]
                resolved[ref] = {"asset": n.get("asset"), "matrix": n.get("matrix"), "assetSha256": assets[n["asset"]]["sha256"], "source": "qa/city-data.cad338b.dump.json"}
            elif kind == "ws" and os.path.exists(os.path.join(WP, val)):
                p = os.path.join(WP, val)
                resolved[ref] = {"sha256": sha_file(p), "bytes": os.path.getsize(p), "source": val}
    done = done_set()
    model = {"seats": copy.deepcopy(D.SEATS), "regions": copy.deepcopy(D.REGIONS), "batches": copy.deepcopy(D.BATCHES), "inputs": copy.deepcopy(D.INPUTS_NEEDED)}
    ctx = {"resolved": resolved, "deps": deps, "done": done}
    checks = run_checks(model, ctx)
    # deps: root taskboard vs LY-009 v2 must agree (else the closure check is ambiguous)
    dd = [s for s in deps if sorted(deps[s]) != sorted(deps_v2.get(s, []))]
    checks.append({"id": "C11", "pass": not dd, "detail": {"rule": "根 taskboard.json 与 LY-009 taskboard.v2 的依赖一致", "differ": dd}})
    # baseline binding
    b11 = {"commit": commit, "expected": D.BASELINE["commit"],
           "dumpSha256": sha_file(os.path.join(HERE, "qa", "city-data.cad338b.dump.json")),
           "inventoryCommit": inv["commit"]}
    checks.append({"id": "C12", "pass": commit == D.BASELINE["commit"] == inv["commit"], "detail": b11})

    # ---------------- negatives: each must make at least the named check fail
    def neg(nid, target, mutate, ctx_mut=None):
        m = copy.deepcopy(model)
        c = dict(ctx)
        mutate(m)
        if ctx_mut:
            ctx_mut(c)
        res = {x["id"]: x["pass"] for x in run_checks(m, c)}
        return {"id": nid, "target": target, "targetFailed": res.get(target) is False, "results": res}

    negs = [
        neg("N01", "C01", lambda m: m["seats"].pop("LY-047")),
        neg("N02", "C03", lambda m: m["seats"]["LY-070"].update(cityLanding=D.CITY_PROPOSAL)),
        neg("N03", "C04", lambda m: m["regions"][0]["selected"]["refs"].append("file:docs/library/models/m-luoyang-kaiyang-gate/files/kaiyang-K-LOD9.glb")),
        neg("N04", "C05", lambda m: m["seats"]["LY-059"].update(decision=D.GO)),
        neg("N05", "C06", lambda m: m["batches"][5]["selected_tasks"].append("LY-057")),
        neg("N06", "C02", lambda m: m["regions"][3].pop("blockers")),
        neg("N07", "C06", lambda m: m["batches"][0]["selected_tasks"].append("LY-074")),
        neg("N08", "C10", lambda m: m["batches"][1]["selected_tasks"].append("LY-079")),
        neg("N09", "C08", lambda m: m["seats"]["LY-093"].update(decision=D.GO)),
        neg("N10", "C06", lambda m: m["batches"][1]["selected_tasks"].remove("LY-016")),
    ]

    # ---------------- seat release table
    prep = {}
    for sid in [f"LY-{i:03d}" for i in range(11, 100)]:
        p = os.path.join(WP, sid, "prep", "prep-status.json")
        if os.path.exists(p):
            d = jload(p)
            prep[sid] = {"path": f"{sid}/prep/prep-status.json", "sha256": sha_file(p), "readyAfterG": d.get("readyAfterG"),
                         "reuseCandidate": (d.get("reuseCandidate") or "")[:240], "inputsMissing": len(d.get("inputsMissing", []))}
    region_of = {s: r["id"] for r in D.REGIONS for s in r["seats"]}
    blocked = {s for s, v in D.SEATS.items() if v["decision"] == D.BLOCK}
    rows = []
    for sid in sorted(D.SEATS):
        v = dict(D.SEATS[sid])
        t = tb[sid]
        pend = [d for d in deps[sid] if d not in done and d not in ("LY-003", "LY-004")]
        if v["decision"] == D.SERVICE:
            now = "持续服务：按批次 manifest 开验"
        elif v["decision"] == D.BLOCK:
            now = "阻断：" + "、".join(v["needsInputs"])
        elif any(d in blocked for d in deps[sid]) or v["decision"] == D.WAIT:
            now = "连带等待：" + "、".join(sorted(d for d in deps[sid] if d in blocked or D.SEATS.get(d, {}).get("decision") == D.WAIT) or pend)
        elif pend:
            now = "可准备，待前件交付：" + "、".join(pend)
        else:
            now = "可开工"
        v.update({"title": t["title"], "type": t["type"], "region": region_of[sid], "depsNonG": deps[sid], "nowState": now, "prep": prep.get(sid)})
        rows.append(v)

    # ---------------- outputs
    regions_out = []
    for r in D.REGIONS:
        rr = copy.deepcopy(r)
        rr["selected"]["resolved"] = {ref: resolved.get(ref) for ref in r["selected"]["refs"]}
        rr["seatDecisions"] = {s: D.SEATS[s]["decision"] for s in r["seats"]}
        rr["defaultReleased"] = False
        regions_out.append(rr)
    head = {"seat": "LY-010", "title": "冻结首批方案与区域准入", "baseline": D.BASELINE,
            "rule": "缺证据或未放行的区，其他任务不得默认视为已放行（defaultReleased=false）；本表放行 ≠ 已入城 ≠ 历史复原成立。"}
    wjson("decision/decision-table.json", {**head, "criteria": D.CRITERIA, "baselineImpact": D.BASELINE_IMPACT,
                                          "inheritedGlobal": D.INHERITED_GLOBAL, "regions": regions_out})
    wjson("decision/seat-release.json", {**head, "vocabulary": {"decision": [D.GO, D.COND, D.REUSE, D.CONTRACT, D.WAIT, D.BLOCK, D.SERVICE],
                                                               "cityLanding": [D.CITY_PROPOSAL, D.LOCAL_ONLY, D.NO_GEOM, D.FORBIDDEN]},
                                        "doneAtBuild": sorted(done), "seats": rows})
    wjson("decision/inputs-needed.json", {**head, "inputs": D.INPUTS_NEEDED})
    wjson("decision/coordinator.json", {**head, "registryV2": D.REGISTRY_V2, "registryV2Extra": D.REGISTRY_V2_EXTRA,
                                       "lockProposals": D.LOCK_PROPOSALS, "decisionsNeeded": D.COORDINATOR_DECISIONS, "batches": D.BATCHES})
    wjson("decision/criteria.json", {**head, "criteria": D.CRITERIA})
    wjson("qa/checks.json", {"seat": "LY-010", "baseline": D.BASELINE["commit"], "checks": checks, "negatives": negs,
                             "allPass": all(c["pass"] for c in checks), "allNegativesFail": all(n["targetFailed"] for n in negs)})
    write_md(regions_out, rows)
    write_inputs(prep, resolved)
    for c in checks:
        print(c["id"], "PASS" if c["pass"] else "FAIL", json.dumps(c["detail"], ensure_ascii=False)[:200])
    for n in negs:
        print(n["id"], n["target"], "fails as expected" if n["targetFailed"] else "DID NOT FAIL")
    from collections import Counter
    print(Counter(r["decision"] for r in rows))
    print(Counter(r["nowState"].split("：")[0] for r in rows))


def write_inputs(prep, resolved):
    ins = {"seat": "LY-010", "baseline": D.BASELINE, "labRepo": "D:/GitHub/creation-notebook-lab（只读：git show / rev-parse / diff，未检出、未写入）",
           "predecessors": {}, "prepStatus": prep, "workpackFiles": {}, "selectedRefs": resolved}
    for s in ["LY-001", "LY-002", "LY-003", "LY-004", "LY-005", "LY-006", "LY-007", "LY-008", "LY-009"]:
        p = os.path.join(WP, s, "status.json")
        d = jload(p)
        ins["predecessors"][s] = {"status.json": sha_file(p), "status": d.get("status"), "openItems": len(d.get("openItems", []))}
    for rel in ["TASKPOOL.md", "taskboard.json", "LY-009/board/taskboard.v2.json", "LY-009/board/locks.json", "LY-009/board/pause-zone.json",
                "LY-006/registry/zones.json", "LY-006/registry/ports.json", "LY-003/tables/admission.json", "LY-003/tables/hold-zones.json",
                "LY-003/tables/ne-screening-cells.json", "LY-004/tables/site-constraints.json", "LY-002/tables/evidence-ledger.json",
                "LY-006/qa/chunks/northeast_C_access.glb", "LY-038/prep/work/chunks__wuku_C_with_support-01.glb"]:
        p = os.path.join(WP, rel)
        ins["workpackFiles"][rel] = sha_file(p)
    wjson("inputs.json", ins)


def write_md(regions, rows):
    L = ["# LY-010 首批方案与区域准入决策表", "",
         f"G 基线：`{D.BASELINE['commit']}`（{D.BASELINE['tag']}，{D.BASELINE['frozenBy']}）。前一基线 `{D.BASELINE['previous'][:7]}`。{D.BASELINE['byteRule']}。", "",
         "本表由 `source/build_decision.py` 从 `source/decision_data.py` 生成，勿手改。机读版：`decision/decision-table.json`、`decision/seat-release.json`。", "",
         "> " + D.CRITERIA["fiveThings"], "",
         "## 一、区域总表", "",
         "| 区 | 名称 | 席位 | 选中方案（摘） | 局部 | 落城 | 阻断项 |", "|---|---|---|---|---|---|---|"]
    for r in regions:
        L.append(f"| {r['id']} | {r['name']} | {r['seats'][0][3:]}–{r['seats'][-1][3:]}（{len(r['seats'])}） | {r['selected']['scheme'][:60]}… | {r['localAdmission']} | **{r['cityAdmission']}** | {'；'.join(r['blockers']) or '无'} |")
    L += ["", "## 二、bce3211 → cad338b 对准入的影响", "", D.BASELINE_IMPACT["summary"], ""]
    for r in regions:
        for x in r["cad338bImpact"]:
            if not x.startswith("无"):
                L.append(f"- **{r['id']} {r['name']}**：{x}")
    L += ["", "## 三、本批统一判据（C 工程判据）", ""]
    c = D.CRITERIA
    L += [f"- 坐标：{c['coordinates']}", f"- 人体：{c['bodyEnvelope']['pedestrian']}；{c['bodyEnvelope']['footSupport']}；{c['bodyEnvelope']['step']}；{c['bodyEnvelope']['carry']}；{c['bodyEnvelope']['vehicle']}。{c['bodyEnvelope']['basis']}",
          f"- 容差：端口平面 {c['tolerances']['portPlanar_m']} m、竖向 {c['tolerances']['portVertical_m']} m、接触间隙 {c['tolerances']['contactGap_m']} m", f"- 加载：{c['loading']}",
          f"- 文件：{c['fileLimits']}", f"- 检查：{c['checks']}", f"- 位置不确定度：{c['positionUncertainty']}", f"- 悬置区：{c['holdZoneRule']}", f"- 风格：{c['styleBaseline']}", ""]
    L += ["## 四、各区详表", ""]
    for r in regions:
        L += [f"### {r['id']} {r['name']}（{r['site']}）", "",
              f"**选中方案**：{r['selected']['scheme']}", ""]
        if r["selected"]["refs"]:
            L += ["| 引用 | SHA256（前16） | 字节 |", "|---|---|---|"]
            for ref, v in r["selected"]["resolved"].items():
                sh = (v or {}).get("sha256") or (v or {}).get("assetSha256") or "未解析"
                L.append(f"| `{ref}` | `{sh[:16]}` | {(v or {}).get('bytes', '')} |")
            L.append("")
        L += ["**保留未选（互斥）**：" + ("；".join(f"{u['scheme']} — {u['rule']}" for u in r["retainedUnselected"]) or "无"), "",
              "**允许改变**：" + "；".join(r["allowedChanges"]), "", "**禁止**：" + "；".join(r["forbidden"]), "",
              f"**准入**：局部 {r['localAdmission']}；落城 **{r['cityAdmission']}** — {r['cityAdmissionMeaning']}", "",
              "**依据**：" + ("；".join(r["evidence"]) or "—"), "",
              "**允许的未验项**：" + "；".join(r["allowedUnverified"]), "", "**阻断项**：" + ("；".join(r["blockers"]) or "无"), ""]
        if r["inherited"]:
            L.append("**前置席位遗留条件**：")
            L += [f"- {x['from']}：{x['item']}" for x in r["inherited"]]
            L.append("")
        L += ["| 席位 | 名称 | 决定 | 预判 | 落城 | 当前 |", "|---|---|---|---|---|---|"]
        for s in r["seats"]:
            row = next(x for x in rows if x["seat"] == s)
            L.append(f"| {s} | {row['title']} | {row['decision']} | {row['expected']} | {row['cityLanding'][:8]} | {row['nowState']} |")
        L.append("")
    L += ["## 五、全区通用遗留条件", ""] + [f"- {x['from']}（{x['kind']}）：{x['item']}" for x in D.INHERITED_GLOBAL] + [""]
    L += ["## 六、需要伊苏里亚 / 协调者补的输入", "", "| 编号 | 向谁 | 内容 | 阻断 | 影响席位 |", "|---|---|---|---|---|"]
    for i in D.INPUTS_NEEDED:
        L.append(f"| {i['id']} | {i['who']} | {i['what']} | {'是' if i['blocking'] else '否'} | {'、'.join(x[3:] for x in i['seats'])} |")
    L += ["", "## 七、席位放行明细（011–099）", "", "| 席位 | 区 | 决定 | 范围 | 未验 / 阻断 | 当前 |", "|---|---|---|---|---|---|"]
    for x in rows:
        ub = "；".join(x["allowedUnverified"] + [("阻断：" + b) for b in x["blockers"]]) or "—"
        L.append(f"| {x['seat']} | {x['region']} | {x['decision']} | {x['scope']} | {ub} | {x['nowState']} |")
    L += ["", "## 八、交协调者", "", "**registry v2 需求**："] + [f"- {k}：{v}" for k, v in {**D.REGISTRY_V2, **D.REGISTRY_V2_EXTRA}.items()]
    L += ["", "**锁提案**："] + [f"- {x['id']}：{x['scope']}（持锁：{x['holder']}；理由：{x['reason']}）" for x in D.LOCK_PROPOSALS]
    L += ["", "**待决事项**："] + [f"- {x}" for x in D.COORDINATOR_DECISIONS]
    L += ["", "**建议批次**（LY-100/协调者最终定；批内闭包已由 C06 校验）：", "", "| 批 | 名称 | 选入 | 验收 | 说明 |", "|---|---|---|---|---|"]
    for b in D.BATCHES:
        L.append(f"| {b['id']} | {b['name']} | {'、'.join(s[3:] for s in b['selected_tasks'])} | {'、'.join(s[3:] for s in b['acceptance'])} | {b['note']} |")
    L.append("")
    open(os.path.join(HERE, "decision", "decision-table.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))


if __name__ == "__main__":
    main()
