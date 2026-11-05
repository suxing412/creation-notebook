# -*- coding: utf-8 -*-
"""LY-002 生成与核对脚本。

用法（只读仓库，只写 LY-002 目录）：
  python -I build.py --lab D:/GitHub/creation-notebook-lab --commit bce3211 \
      --ly001 D:/GitHub/creation-notebook-workpacks/LY-001 --external <放置版权材料抽取文本的目录>

做的事：
1. 逐条核对 ledger_data.py 中每个 quote 是否为来源快照去空白后的子串；
2. 读取仓库提交字节（git show，只读）计算输入 SHA256；
3. 生成 tables/、qa/、inputs.json、delivery-manifest.json。
外部版权材料（高2023 PDF、徐2019网页、新华网）不随包分发；--external 目录不存在时相应引文记为"未复核"而不是通过。
"""
import argparse, hashlib, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ledger_data as L  # noqa: E402

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def sha256_file(p):
    with open(p, "rb") as f:
        return sha256_bytes(f.read())

def norm(t):
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", "", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&nbsp;", "")
    return re.sub(r"\s+", "", t)

def load_source_text(sid, ext_dir):
    s = L.SOURCES[sid]
    if "snapshot" in s:
        p = os.path.join(HERE, s["snapshot"])
        raw = open(p, "rb").read()
        return norm(raw.decode(s["encoding"], "replace")), dict(kind="snapshot", path="source/" + s["snapshot"], sha256=sha256_bytes(raw), bytes=len(raw))
    if "external" in s and ext_dir:
        p = os.path.join(ext_dir, s["external"])
        po = os.path.join(ext_dir, s["externalOriginal"])
        if os.path.exists(p) and os.path.exists(po):
            orig_sha = sha256_file(po)
            return norm(open(p, encoding="utf-8", errors="replace").read()), dict(
                kind="external", originalSha256=orig_sha, expectedSha256=s["externalSha256"],
                originalMatches=(orig_sha == s["externalSha256"]))
    return None, dict(kind="unavailable")

def git_show(lab, commit, path):
    return subprocess.run(["git", "-C", lab, "show", f"{commit}:{path}"], capture_output=True, check=True).stdout

def selftest(ext_dir):
    """负例：核对器必须能拒绝不存在的引文，并确认关键否定事实。"""
    s01, _ = load_source_text("S01", ext_dir)
    s04, _ = load_source_text("S04", ext_dir)
    rows = [
        dict(case="伪造引文'雒阳城十三门'不得在S01中找到", expectFound=False, found="雒阳城十三门" in s01),
        dict(case="S01城门名单中不含'旋门'", expectFound=False, found="旋门" in s01),
        dict(case="S04（郡国志成皋条注）含'旋门'，证明其为成皋地名", expectFound=True, found="旋门膎" in s04),
        dict(case="S01城门名单含'秏门'", expectFound=True, found="秏门" in s01),
    ]
    for r in rows:
        r["pass"] = (r["found"] == r["expectFound"])
    return rows

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", required=True)
    ap.add_argument("--commit", default="bce3211")
    ap.add_argument("--ly001", required=True)
    ap.add_argument("--external", default="")
    a = ap.parse_args()

    # ---------- 1. 引文核对
    cache = {}
    qrows = []
    for f in L.FACTS:
        for col in ("sameLuoyang", "otherHan", "beiweiLater"):
            for i, e in enumerate(f[col]):
                sid = e["src"]
                if sid not in L.SOURCES:
                    raise SystemExit(f"{f['id']} 未登记来源 {sid}")
                row = dict(fact=f["id"], column=col, index=i, src=sid, locator=e["locator"], quote=e["quote"])
                if e["quote"] is None:
                    kind = L.SOURCES[sid]["kind"]
                    row["result"] = "无引文（仓库沿用或图像目视记录）"
                    row["ok"] = kind in ("仓库沿用", "研究图") or L.SOURCES[sid].get("noLocalBytes", False)
                else:
                    if sid not in cache:
                        cache[sid] = load_source_text(sid, a.external)
                    text, meta = cache[sid]
                    qn = re.sub(r"\s+", "", e["quote"])
                    row["quoteChars"] = len(qn)
                    row["oneSentence"] = ("。" not in qn[:-1]) and len(qn) <= 40
                    row["sourceBytes"] = meta
                    if text is None:
                        row["result"] = "未复核：来源文本不在本机"
                        row["ok"] = None
                    else:
                        found = qn in text
                        row["result"] = "原文中找到" if found else "未找到"
                        row["ok"] = found and row["oneSentence"]
                qrows.append(row)
    bad = [r for r in qrows if r["ok"] is False]
    unver = [r for r in qrows if r["ok"] is None]

    # ---------- 2. 输入哈希（仓库提交字节）
    lab_inputs = [
        "docs/cities/luoyang/p-luoyang.asset.json", "docs/cities/luoyang/README.md", "docs/cities/luoyang/city-data.mjs",
        "docs/cities/luoyang/research/2026-11-03/reference-review.md", "docs/cities/luoyang/research/2026-11-03/density-evidence.json",
        "docs/cities/luoyang/research/2026-11-03/eaves-evidence.json", "docs/cities/luoyang/research/2026-11-03/city-milestones.json",
        "docs/cities/luoyang/data/evidence/evidence-geometry.json", "docs/cities/luoyang/data/research-unplaced.json",
        "docs/cities/luoyang/data/west/north-palace-conflict-layer.json", "docs/cities/luoyang/data/west/city-wall-constraints.json",
        "docs/cities/luoyang/data/west/market-precedents.json", "docs/cities/luoyang/data/west/storage-precedents.json",
        "docs/cities/luoyang/data/west/road-preconstraints.json", "docs/cities/luoyang/data/c02/research-mask.json",
        "docs/cities/luoyang/progress-assets/palace-admission-court/evidence.md",
        "docs/cities/luoyang/progress-assets/yong-city-v1/source.json", "docs/cities/luoyang/progress-assets/mao-gate/source.json",
        "docs/research/han-architecture/reference.md",
    ]
    ls = subprocess.run(["git", "-C", a.lab, "ls-tree", "-r", "--name-only", a.commit, "docs/library/models/"],
                        capture_output=True, text=True, check=True).stdout.split()
    lab_inputs += sorted(p for p in ls if re.match(r"docs/library/models/m-luoyang-[^/]+/m-luoyang-[^/]+\.asset\.json$", p))
    commit_full = subprocess.run(["git", "-C", a.lab, "rev-parse", a.commit], capture_output=True, text=True, check=True).stdout.strip()
    input_rows = []
    for p in lab_inputs:
        b = git_show(a.lab, a.commit, p)
        input_rows.append(dict(path=p, bytes=len(b), sha256=sha256_bytes(b), basis="git show 提交字节"))
    ly001_files = ["status.json", "qa/family-ledger.json", "qa/snapshot-ledger.json"]
    ly001_rows = [dict(path="LY-001/" + p, sha256=sha256_file(os.path.join(a.ly001, p))) for p in ly001_files]
    snap_rows = []
    for sid, s in L.SOURCES.items():
        r = dict(src=sid, title=s["title"], url=s["url"], kind=s["kind"], read=s["read"], textDate=s["textDate"])
        if "snapshot" in s:
            p = os.path.join(HERE, s["snapshot"]); r.update(snapshot="source/" + s["snapshot"], sha256=sha256_file(p), bytes=os.path.getsize(p))
        if "externalSha256" in s:
            r.update(externalOriginalSha256=s["externalSha256"], distributed=False)
        if "externalImageSha256" in s:
            r.update(externalImageSha256=s["externalImageSha256"], distributed=False)
        if s.get("noLocalBytes"):
            r.update(localBytes=None)
        snap_rows.append(r)

    # ---------- 3. 家族绑定
    fam = json.load(open(os.path.join(a.ly001, "qa/family-ledger.json"), encoding="utf-8"))
    families = [(x["family"], x["name"], x.get("cityState")) for x in fam["families"]]
    expand = {}
    for f in L.FACTS:
        for t in f["affects"]:
            for fid in L.FAMILY_GROUPS.get(t, [t]):
                expand.setdefault(fid, []).append(f["id"])
    proh_by_fact = {}
    for x in L.PROHIBITED:
        proh_by_fact.setdefault(x["ref"], []).append(x["id"])
    binding = []
    for fid, name, state in families:
        facts = sorted(set(expand.get(fid, [])))
        proh = sorted({p for fct in facts for p in proh_by_fact.get(fct, [])})
        issues = sorted({d["id"] for d in L.REPO_ISSUES for fct in facts if fct in d["evidence"]})
        binding.append(dict(family=fid, name=name, cityState=state, facts=facts, prohibited=proh, repoIssues=issues))
    unbound = [b["family"] for b in binding if not b["facts"]]
    unknown_targets = sorted(set(expand) - {f for f, _, _ in families})

    # ---------- 4. 覆盖检查
    required_topics = {"门名与方位": ["E-G01", "E-G02", "E-G03"], "南北宫": ["E-P01", "E-P02", "E-P03"], "市": ["E-M01"],
                       "太仓武库": ["E-S01", "E-S02"], "太学灵台明堂辟雍": ["E-R06", "E-R04", "E-R03", "E-R05"],
                       "南北郊": ["E-R01", "E-R02"], "住宅市肆作坊类比": ["E-H01", "E-M01", "E-H02"]}
    ids = {f["id"] for f in L.FACTS}
    topic_ok = {k: all(i in ids for i in v) for k, v in required_topics.items()}
    per_fact = []
    for f in L.FACTS:
        n_loc = sum(1 for c in ("sameLuoyang", "otherHan", "beiweiLater") for e in f[c] if e["locator"])
        per_fact.append(dict(id=f["id"], cols={c: len(f[c]) for c in ("sameLuoyang", "otherHan", "beiweiLater")},
                             unknown=len(f["unknown"]), locators=n_loc, hasModelUse=bool(f.get("modelUse")),
                             hasDisputeField=("dispute" in f)))
    fact_problems = [p["id"] for p in per_fact if p["locators"] == 0 or not p["hasModelUse"]]

    os.makedirs(os.path.join(PKG, "tables"), exist_ok=True)
    os.makedirs(os.path.join(PKG, "qa"), exist_ok=True)

    def dump(rel, obj):
        p = os.path.join(PKG, rel)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
            fh.write("\n")

    master = dict(schema="creation-notebook.luoyang.evidence-ledger.v1", seat="LY-002", snapshotYearCE=L.SNAPSHOT_YEAR,
                  baselineCommit=commit_full,
                  columns=dict(sameLuoyang="同期洛阳：东汉人所记，或后世成书而记东汉洛阳制度者（逐条 textDate）",
                               otherHan="异地或异期汉代：类比，不能直接作洛阳事实",
                               beiweiLater="曹魏、西晋、北魏及后世：分期排除或追述",
                               unknown="未知：保留空白"),
                  gradeLegend={"有据（文献）": "有原文定位", "考古（二手）": "转引考古报告，原报告未读",
                               "推断": "研究者推论", "C": "本项目工程设计", "未知": "无资料"},
                  sources=L.SOURCES, gates=L.GATES, facts=L.FACTS, prohibited=L.PROHIBITED, repoIssues=L.REPO_ISSUES)
    dump("tables/evidence-ledger.json", master)
    dump("tables/family-binding.json", dict(baselineCommit=commit_full, ly001FamilyCount=len(families), binding=binding))
    dump("qa/quote-check.json", dict(total=len(qrows), passed=sum(1 for r in qrows if r["ok"] is True),
                                     failed=len(bad), unverified=len(unver),
                                     noQuoteRecords=sum(1 for r in qrows if r["quote"] is None), rows=qrows))
    # 两宫距离核算（E-P02）：仓库研究示意几何 vs 蔡质'七里'
    eg = json.loads(git_show(a.lab, a.commit, "docs/cities/luoyang/data/evidence/evidence-geometry.json"))
    F = {x["id"]: x for x in eg["features"]}
    def poly(fid):
        pts = F[fid]["geometry"]["coordinates"][0][:-1]
        ys = [p[1] for p in pts]
        return dict(centerY=sum(ys) / len(ys), minY=min(ys), maxY=max(ys))
    sp, npal = poly("south_palace_candidate_gao2023_B"), poly("north_palace_extent_gao2023_B")
    cy = [p[1] for p in F["city_wall_schematic_B"]["geometry"]["coordinates"][0]]
    C_chi = [0.23, 0.24]  # C 假设：每尺米数区间；本轮未引量器出处
    li = [300 * 6 * c for c in C_chi]
    dump("qa/palace-spacing-check.json", dict(
        basis="evidence-geometry.json（提交字节）顶点均值；单位 schematic_m，非测绘",
        southPalace=sp, northPalace=npal, centerDistance_schematic_m=npal["centerY"] - sp["centerY"],
        edgeGap_schematic_m=npal["minY"] - sp["maxY"], cityNS_schematic_m=max(cy) - min(cy),
        assumption_C=dict(metersPerChi=C_chi, buPerLi=300, chiPerBu=6, metersPerLi=li),
        qiLi_m=[7 * x for x in li], jiuLi100bu_m=[9 * x + 100 * 6 * c for x, c in zip(li, C_chi)],
        reading="七里约2.9公里，远大于示意图两宫中心距；不构成配准依据，只说明文本与研究图之间存在未解释的差距。"))
    st = selftest(a.external)
    dump("qa/selftest.json", dict(rows=st, allPass=all(r["pass"] for r in st)))
    dump("qa/coverage.json", dict(requiredTopics=topic_ok, perFact=per_fact, factsMissingLocatorOrModelUse=fact_problems,
                                  familiesWithoutFacts=unbound, affectsTargetsNotInLY001=unknown_targets,
                                  familyCount=len(families)))
    dump("inputs.json", dict(seat="LY-002", baselineCommit=commit_full, repoReadOnly=True,
                             labInputs=input_rows, ly001=ly001_rows, sources=snap_rows,
                             note="仓库输入按 git show 提交字节计；LY-001 已指出本机 CRLF 检出字节与提交字节不同。"))
    write_md(binding, commit_full)
    print(json.dumps(dict(quotes=len(qrows), failed=len(bad), unverified=len(unver), familiesWithoutFacts=unbound,
                          unknownTargets=unknown_targets, topicOk=topic_ok, factProblems=fact_problems), ensure_ascii=False))
    for r in bad:
        print("FAIL", r["fact"], r["src"], r["quote"], r.get("quoteChars"), r.get("oneSentence"))
    return 1 if (not all(r["pass"] for r in st) or bad or unbound or unknown_targets or fact_problems or not all(topic_ok.values())) else 0

def cell(entries):
    if not entries:
        return "—"
    out = []
    for e in entries:
        s = L.SOURCES[e["src"]]
        qt = f"「{e['quote']}」" if e["quote"] else "（无引文）"
        td = f"〔{e['textDate']}〕" if e.get("textDate") else ""
        ns = f"；不支持：{e['notSupports']}" if e.get("notSupports") else ""
        out.append(f"{e['src']} {e['locator'] or ''} {qt}{td} → {e['supports']}{ns}")
    return "<br>".join(x.replace("|", "／") for x in out)

def write_md(binding, commit_full):
    lines = [f"# 约180年雒阳证据与禁用表（LY-002）", "",
             f"基线 `{commit_full}`。本文件由 `source/build.py` 从 `source/ledger_data.py` 生成；机器可读版为 `tables/evidence-ledger.json`。",
             "引文均为去空白后在来源快照中逐字核对的原文片段（见 `qa/quote-check.json`）；文献数字与模型尺度分开，模型尺寸一律另记为 C。", "",
             "## 一、十二门", "", "| 门 | 异写 | 面 | 李尤铭方位 | 北魏名 | 资产卡 | 备注 |", "|---|---|---|---|---|---|---|"]
    for g in L.GATES:
        lines.append(f"| {g['name']} | {'、'.join(g['alias']) or '—'} | {g['side']} | {g['sideOrderFromLiYouOrBranch']}"
                     f"{('「'+g['branchQuote']+'」') if g['branchQuote'] else ''} | {g['beiwei']} | {g['card']} | {g['notes'] or '—'} |")
    lines += ["", "## 二、证据条目（四栏）", ""]
    for f in L.FACTS:
        lines += [f"### {f['id']}｜{f['title']}", "", f"**结论**：{f['claim']}", "", f"**等级**：{f['grade']}", ""]
        if f.get("dispute"):
            lines += [f"**争议**：{f['dispute']}", ""]
        lines += ["| 同期洛阳 | 异地汉代 | 北魏及后世 | 未知 |", "|---|---|---|---|",
                  f"| {cell(f['sameLuoyang'])} | {cell(f['otherHan'])} | {cell(f['beiweiLater'])} | {'<br>'.join(f['unknown']) or '—'} |", "",
                  f"**模型可用**：{f['modelUse']['allowed']}　**不可用**：{f['modelUse']['notAllowed']}", ""]
    lines += ["## 三、不可外推（禁用）表", "", "| 编号 | 禁用内容 | 原因 | 影响范围 | 依据条目 |", "|---|---|---|---|---|"]
    for x in L.PROHIBITED:
        lines.append(f"| {x['id']} | {x['item']} | {x['reason']} | {x['appliesTo']} | {x['ref']} |")
    lines += ["", "## 四、仓库现状与证据的出入（只报告，交 LY-100/LY-098）", "", "| 编号 | 级别 | 文件 | 位置 | 发现 | 建议 |", "|---|---|---|---|---|---|"]
    for d in L.REPO_ISSUES:
        lines.append(f"| {d['id']} | {d['severity']} | `{d['file']}` | {d['where']} | {d['finding']} | {d['action']} |")
    lines += ["", "## 五、资产家族绑定（54 家族，LY-001 口径）", "", "| 家族 | 名称 | 城市状态 | 证据条目 | 禁用 | 出入 |", "|---|---|---|---|---|---|"]
    for b in binding:
        lines.append(f"| {b['family']} | {b['name']} | {b['cityState']} | {'、'.join(b['facts'])} | {'、'.join(b['prohibited']) or '—'} | {'、'.join(b['repoIssues']) or '—'} |")
    lines += ["", "## 六、来源登记", "", "| 编号 | 来源 | 成书/年代 | 类别 | 阅读状态 | URL |", "|---|---|---|---|---|---|"]
    for sid, s in L.SOURCES.items():
        lines.append(f"| {sid} | {s['title']} | {s['textDate']} | {s['kind']} | {s['read']} | {s['url']} |")
    with open(os.path.join(PKG, "tables/evidence-ledger.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    sys.exit(main())
