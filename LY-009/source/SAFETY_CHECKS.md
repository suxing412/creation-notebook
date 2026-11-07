# 洛阳工作流安全预检

这是工作包源码修复与可运行预检，不是 G 冻结、席位验收或城市安装许可。正式 status、锁、所有权、研究坐标、模型和网页不变。

## 运行

需要 Python 3.9+ 标准库、Git，以及包含指定提交真实模型对象的仓库。输出目录必须尚不存在，父目录已存在，并且位于工作包与模型仓库之外。

```sh
python -I -B LY-009/source/test_safety_checks.py
python -I -B LY-009/source/run_safety_checks.py --lab /path/to/model-repo --commit <full-commit-sha> --out /path/to/new-output
```

预检退出 3 表示检查已完成、准入仍 blocked；退出 2 表示输入或检查失败。不要将 3 转译为正式验收通过。输出 summary.json 绑定实际脚本 SHA256 和解析后的完整模型提交 SHA。不存在批准参数，也不消费自填 done 状态。

- LY-004：使用原始 21 项 gate 数据，不传可信安装 tuple。当前应为 0 安装、6 研究标记。没有执行完整几何、版权、引文或测量重建。
- LY-007：实际调用 Git CLI，递归检查全部 path/nearPath 及声明 SHA256，同时扫描同路径 stem 的 LOD0/1/2。忽略 replace refs，按 NUL 解析路径，拒绝 symlink/gitlink 作为模型，不覆盖已有回执。缺对象或错 SHA 不会通过。glTF 外部资源和渲染不在此检查范围。
- LY-009：源码目的路径和大小按本席白名单分类。分类不是领取席位或解除锁的权限。Git 模式保留删除/rename 源端和提交 blob 大小检查。
- LY-010：采用隔离旧构建入口的最小 containment 修复，不采用依赖旧私有证据布局的 replacement builder，不可叠加两套 patch。旧入口立即停止，且不再自加完成席位或剔除 G 依赖。它不会生成新准入合同；现存合同与 status 未重建。

## 原有 run_all.sh

原全量入口仍需它的完整工作包、Git 历史与独立证据。此改动取消 whitelist FAIL 的 `|| true`，任何白名单失败立即停止，不再继续生成后续看板。使用 `-B` 避免写字节码，不删除 source 缓存。它仍是会写 LY-009 产物的原全量工具，不是上面的只读预检，不能用一个 shell 成功码替代整席验收。不要在缺输入时伪造 QA、status 或 manifest。

## 验证与采纳边界

测试中的 Git 仓库、模型字节、身份和提交都是明确的合成 fixture，只证明程序行为，不是历史模型、考古证据或真实项目提交。真实项目验证必须另行记录精确输入 SHA、实际结果和缺项。

本修复不改两条未解决 selected 引用、“二里”史证措辞、gitignore 历史断言、生产 CI/部署或网页。G 未冻结，原有 13 区、89 席、7 批阻断不因本预检改变。独立分支供审查，是否采纳由相应负责人协调；不自动合并、解锁或上线。
