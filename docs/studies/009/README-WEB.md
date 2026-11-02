# 009 HINGE / 姿态工作台
这一包包含完整原模型于 `model/`、独立网页、复现脚本、前后证据和限定验收记录。网页为离散姿态对照，不宣称已验实时动画。

## 浏览
用静态HTTP服务打开 `index.html`。直接 file:// 打开时浏览器可能禁止 fetch；无脚本图册和直接模型链接仍在页面内。

## 网页复现与验证
在这一包根目录，Python 3.12.14 + Pillow 13.0.0，Node 24.22.1，执行：

- `node web-source/test_state.cjs`
- `node web-source/test_app.cjs`
- `node web-review/audit_pose_workbench/regressions.cjs`
- `node web-review/audit_pose_workbench/independent_checks.cjs`
- `python web-source/verify.py`
- `python web-source/verify_model_binding.py`

重新生成主网页到单独输出目录：
`python web-source/compose.py --model-dir model --output rebuilt`

该命令重建主页面、数据、原模型副本及JS/CSS，并复制归档的脚本、报告与冻结清单。历史截图和评审报告仍是原验收证据，不伪装成新一轮浏览器测试。模型重新生成的方法见 `model/README.md`。

## 状态与边界
模型171项原始字节保留。三变体×三姿态的角度读取每份 model-info 的实际 pose，而非默认config角。主图使用同一front机位的固定等幅裁片；图册与原图保持完整画幅。

原生云浏览器完成九组合、键盘、导航、窄CSS视口、无脚本、缺图保底与一个实际GLB下载验收。恢复磁盘资源后点击Retry那一分支受到预览热重载干扰，没有算成原生通过；对应逻辑已有单元覆盖。具体见 web-review/native-checks.json。

GPU、动态闪烁、真实手机、完整读屏与200%专项未验；没有照度、机械稳定性或制造安全认证。
