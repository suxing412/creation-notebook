# 造物手记 · 版本评审

这个分支（`reviews`）只放 Claude 的质量评审，不含网站代码，也不会部署到网站。

- **最新一份**：[LATEST.md](LATEST.md)
- **纯文本地址**（适合直接读取）：`https://raw.githubusercontent.com/suxing412/creation-notebook/reviews/LATEST.md`
- 历史评审：`<tag>.md`；基线评审：[baseline-59b5a65.md](baseline-59b5a65.md)

## 怎么运转
1. Codex 做完一批工作，在 `main` 上打一个 tag 并推送，格式为 `rYYYY.MM.DD-N`，例如 `r2026.11.04-1`。
2. Claude 每 30 分钟检查一次。发现新 tag 后拉下来评审，把 `<tag>.md` 推送到这个分支，并同步更新 `LATEST.md`。电脑开着且 Claude 应用在运行时才会检查。
3. 每份评审都会先复审上一份的问题，再列新问题。

## 编号
- **C**：内容与模型问题，交给伊苏里亚。
- **W**：网页问题，交给 Codex。
- 编号一直沿用，修好后在后续评审里标「已修」。提交说明里写上编号（例如 `Fix W1: ...`），复审时更容易对上。

## 文件
- `PROCEDURE.md`：评审规程（定时任务按它执行）
- `state.json`：上次评审到哪个版本、还有哪些问题没修
- `tools/`：检查脚本（只用 Python 标准库加 Pillow）
- `evidence/<版本>/`：截图、拼图和模型指标
- `plans/`：Claude 提出、经制作人同意的改进方案（例如 [洛阳城页面重做](plans/luoyang-redesign.md)）
