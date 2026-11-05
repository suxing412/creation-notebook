# 东汉洛阳 · 100 席位生产工作包（workpacks 分支）

这个分支只放任务池的工作包，不部署到网站，也不并进 main。

- `TASKPOOL.md`：任务池原文，伊苏里亚 2026-11-05 整理，核对基线是 `bce3211`。
- `taskboard.json`：从原文解析出的 100 个席位与依赖图。依赖无环，最长链 15 层。
- `LY-###/`：每个席位自己的工作包，包括 brief、inputs、models、assembly、qa、preview、delivery-manifest、status。

源工程（.blend、源 ZIP）不进这个分支。它们照旧放进 `D:/GitHub/creation-notebook-待传/<批次号>/`，再上传到批次 Release。

城景和项目卡只由 LY-100（Claude）分批合入 main。每批都从当时最新的 main 合起，保留同期其他人的成果。
