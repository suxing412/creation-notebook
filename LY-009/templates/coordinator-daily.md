# 协调者日报 · YYYY-MM-DD

> 用法：先按顺序重跑（全部只读，只写 LY-009/）：
> ```
> python -I LY-009/source/check_whitelist.py --scan . LY-009/qa/whitelist-scan.json
> python -I LY-009/source/build_board.py . D:/GitHub/creation-notebook-lab bce3211 LY-009
> python -I LY-009/source/board_diff.py <昨日 taskboard.v2.json> LY-009/board/taskboard.v2.json
> python -I LY-009/source/check_board.py . D:/GitHub/creation-notebook-lab bce3211 LY-009 <临时目录>
> ```
> 再把结果填进下面各栏。昨日的 v2 由协调者自行留存（LY-009 不替协调者存档）。

## 1 状态变化（board_diff 输出）

| 席位 | 昨日 | 今日 | 依据（status.json SHA） |
|---|---|---|---|

今日新转为「可开工」的席位：…

## 2 G 开工包

G = LY-001、002、005、006、007、008、009、010：已冻结 / 未冻结（缺 …）。

## 3 锁

- lab origin/main 相对基线的新提交：…；落在锁路径内的文件：…（locks.json `changedAfterBaseline`）。
- 解锁或改锁申请：…（只有持锁人/协调者能批）。

## 4 暂停区

| 编号 | 今日变化（新增/解除/不变） | 裁决人 | 记录 |
|---|---|---|---|

## 5 写入白名单

check_whitelist --scan：PASS / FAIL；违规文件数 …，涉及席位 …。根文件（TASKPOOL.md、taskboard.json、README.md）有没有被改：…

## 6 今日合并（只有 LY-100）

批次 manifest：selected_tasks / dependency_closure / gate_results / excluded_regions；本批「未纳入」区域不记为通过。

## 7 明日释放

按依赖图可以释放的席位：…；仍在暂停区不能落城的：…
