# -*- coding: utf-8 -*-
"""生成 delivery-manifest.json：LY-002 目录白名单、大小、SHA256、分类与使用顺序（不含自身）。"""
import hashlib, json, os
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cls(rel):
    if rel.startswith("source/snapshots/"): return "内部校验快照（公有领域原文，不进公共docs）"
    if rel.startswith("source/"): return "源（生成与核对脚本、唯一数据源）"
    if rel.startswith("tables/"): return "交付数据（可供LY-100语义合并的候选内容）"
    if rel.startswith("qa/"): return "QA证据"
    return "工作包说明"
rows = []
for root, dirs, files in os.walk(PKG):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        p = os.path.join(root, f); rel = os.path.relpath(p, PKG).replace("\\", "/")
        if rel == "delivery-manifest.json": continue
        b = open(p, "rb").read()
        rows.append(dict(path=rel, bytes=len(b), sha256=hashlib.sha256(b).hexdigest(), class_=cls(rel)))
rows.sort(key=lambda r: r["path"])
for r in rows: r["class"] = r.pop("class_")
m = dict(seat="LY-002", baselineCommit="bce3211f818ee5a8bef1773539da70695ba37b17", fileCount=len(rows),
         totalBytes=sum(r["bytes"] for r in rows), files=rows,
         notDistributed=["高崇文2023 PDF及其文字层与图1（SHA见inputs.json）", "徐龙国2019转载网页", "新华网2025报道"],
         dependencies=["LY-001/status.json、qa/family-ledger.json（SHA见inputs.json）", "creation-notebook-lab @ bce3211（只读）"],
         useOrder=["先读 brief.md", "再读 tables/evidence-ledger.md 或 .json", "按家族查 tables/family-binding.json",
                   "复核用 qa/quote-check.json、qa/selftest.json，重算用 source/build.py"],
         install="无安装步骤；本包是资料与契约，不写城市文件。")
open(os.path.join(PKG, "delivery-manifest.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(m, ensure_ascii=False, indent=1) + "\n")
print(len(rows), m["totalBytes"])
