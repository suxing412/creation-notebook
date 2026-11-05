# 造物手记协作约定

- 伊苏里亚负责内容和模型；网站（资产库网页、详情页、构建与部署）由 Claude 维护，Claude 同时做质量评审。2026-11-05 起 Codex 不再参与这个项目。
- Claude 的评审记录保存在远程 `reviews` 分支。开始修复前运行 `git fetch origin reviews`，读取 `git show origin/reviews:LATEST.md`。历史评审路径为 `origin/reviews:<tag>.md`。
- C 编号交给伊苏里亚，W 编号（网页）由 Claude 处理。修复提交的说明须包含对应编号，例如 `Fix W1: optimize catalogue thumbnails`。
- 一批工作完成并通过检查后，将提交推送到 `main`，在该提交上创建附注 tag 并推送。格式为 `rYYYY.MM.DD-N`，日期使用 Asia/Shanghai，N 为当天批次序号。先查询远程已有 tag，零碎提交无需打 tag。
- Claude 只评审已打 tag 的版本。推送 tag 后通常约 30 分钟内产生评审，读取该 tag 的评审文件并核对其提交 SHA。
- 任何协作者都不向 `reviews` 分支提交，不 force push `main`。
- `D:/GitHub/creation-notebook-review/` 下的两个 Git worktree 是评审专用目录。不得删除、prune 或修改其工作状态。
- **资产提交规范**（`docs/asset-spec/README.md`）：每件资产一张卡片 `<id>.asset.json`；新资产放在 `docs/library/<分类>/<id>/`。提交前运行 `python -I lab/tools/build_assets.py --check`，有错误不提交。分类和门槛只在 `docs/asset-spec/categories.json` 里改。
