# 造物手记协作约定

- 伊苏里亚负责内容和模型，Codex 负责网页，Claude 负责独立质量评审和建议。
- Claude 的评审记录保存在远程 `reviews` 分支。开始修复前运行 `git fetch origin reviews`，读取 `git show origin/reviews:LATEST.md`。历史评审路径为 `origin/reviews:<tag>.md`。
- W 编号由 Codex 处理，C 编号交给伊苏里亚。修复提交的说明须包含对应编号，例如 `Fix W1: optimize catalogue thumbnails`。
- 一批工作完成并通过检查后，将提交推送到 `main`，在该提交上创建附注 tag 并推送。格式为 `rYYYY.MM.DD-N`，日期使用 Asia/Shanghai，N 为当天批次序号。先查询远程已有 tag，零碎提交无需打 tag。
- Claude 只评审已打 tag 的版本。推送 tag 后通常约 30 分钟内产生评审，读取该 tag 的评审文件并核对其提交 SHA。
- Codex 不向 `reviews` 分支提交，不 force push `main`。
- `D:/GitHub/creation-notebook-review/` 下的两个 Git worktree 是评审专用目录。不得删除、prune 或修改其工作状态。
