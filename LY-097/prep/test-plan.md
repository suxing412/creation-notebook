# LY-097 本项验收的可执行检查（准备稿）

席位：LY-097 真实运行与视觉回归（独立验收）。本稿写于 G 冻结之前，只对当前 main `bce3211f818ee5a8bef1773539da70695ba37b17` 跑了「改前」基线。以后每一批都按这里的步骤在**同一台机器、同一类 GPU**上重放，再和基线对比。

TASKPOOL 本项验收原文要求三件事：记录真实设备与环境；记录加载失败、外观和资源用量；没有的运行环境明列未验，并按 LY-010 的策略判断是否阻断，绝不造截图或指标。

## 0 环境与绑定

| 项 | 基线值（2026-11-05 实测） |
|---|---|
| 被测提交 | `bce3211f818ee5a8bef1773539da70695ba37b17`，用 `source/serve_git_head.py` 按**提交字节**服务（不读 autocrlf 检出），端口 8797，只接受 GET/HEAD |
| 浏览器 | Chrome 156.0.8078.80（`C:/Program Files/Google/Chrome/Application/chrome.exe`），`--headless=new`，一次性 profile，禁用扩展、同步和后台网络 |
| GPU A（独显） | `ANGLE (NVIDIA, NVIDIA GeForce RTX 5090 (0x00002B85) Direct3D11 vs_5_0 ps_5_0, D3D11)`，驱动 32.0.16.2101 |
| GPU B（集显） | 加 `--force_low_power_gpu` 启动，得到 `ANGLE (AMD, AMD Radeon(TM) Graphics (0x000013C0) Direct3D11 …)`，驱动 32.0.21045.16010 |
| 视口 | 1440×1000，DPR 1（整块 `#scene` 画布都在截图内）；手机用**仿真** 390×844、DPR 3、触屏 |
| 没有的环境 | 物理手机、平板、macOS/Safari、Firefox、有头窗口下的 vsync 帧率、其他 GPU 厂商。这些一律写 `UNTESTED`，不能转成 PASS |

脚本（都在 `prep/source/`，SHA256 见 `prep-status.json`）：
- `cdp.mjs`：最小 CDP 客户端，Node 24 自带 WebSocket。
- `run_runtime.mjs`：场景运行器，输出 `run.json` 和 `shots/*.png`。
- `probe_openings.mjs`：开孔射线探针，用的是**插桩版**渲染器，下文 §2 说明。
- `diff_shots.py`：截图差分。
- `check_run.py`：R1–R11 判定器，有 FAIL 时退出码为 1。
- `summarize.py`：资源与帧数据汇总。
- `build_inputs.py`：生成输入清单，SHA 一律按提交 blob 计算。

## 1 每批重放步骤

```sh
# 0) 候选基线：LY-100 给出的批次合并候选提交 <REV>（不是工作树）
python -I prep/source/serve_git_head.py D:/GitHub/creation-notebook-lab <REV> 8797      # 后台
node   prep/source/run_runtime.mjs --base http://127.0.0.1:8797 --out <batch>/run-dgpu --label <batch>-dgpu --rev <REV> --profile <scratch>/p
node   prep/source/run_runtime.mjs ... --out <batch>/run-igpu --chromeArgs --force_low_power_gpu
node   prep/source/probe_openings.mjs --base http://127.0.0.1:8797 --out <batch>/openings [--probes <batch-probes.json>]
node   LY-001/source/dump_city_data.mjs <提交字节的 city-data.mjs 副本，放在 …/docs/cities/luoyang/ 下> > <batch>/city-data.dump.json
python -I prep/source/check_run.py --cand <batch>/run-dgpu --base prep/baseline/bce3211-dgpu-a --dump <batch>/city-data.dump.json \
          --out <batch>/verdict-dgpu.json --expect-changed <manifest 里声明会变的步骤名，逗号分隔>
python -I prep/source/check_run.py --cand <batch>/run-igpu --base prep/baseline/bce3211-igpu-a ...   # 集显跟集显比
python -I prep/source/summarize.py <batch>/summary.json <batch>/run-dgpu <batch>/run-igpu
```

基线一旦冻结，脚本就不能再改。要改脚本，必须先在旧提交上重跑出新基线，并把新的 SHA 记进 `prep-status.json`。

## 2 检查项（正例、负例、容差）

| ID | 检查 | 正例（必须过） | 负例（必须失败，否则检查器无效） | 容差 / 判定 |
|---|---|---|---|---|
| R1 | 真实环境 | `webglRenderer` 是硬件 ANGLE 字符串 | 渲染器名含 SwiftShader / Basic Render / llvmpipe 时判 FAIL；CPU 图不能当 GPU 结果 | 只认字符串相等的同类设备对比 |
| R2 | 加载 | S01 进入 `ready`；非 N 步里没有 `#error`、异常或 pageError；请求无失败（只放行 `/favicon.ico` 的 404） | N01 / N02 两个注入负例都必须触发 `#error` | 0 容差 |
| R3 | 首屏集合 | S01 请求到的 GLB 集合与清单推导出的集合**完全相等**（基线：21=21） | 漏一个或多一个就 FAIL（隐藏试放包误激活、`initial` 写错都会被抓到） | 0 容差 |
| R4 | 章节与研究视图 | 清单里每一章都进入 `ready`：有按钮的章点按钮；没有按钮的章用 `?chapter=<id>` 打开，并在报告里单列。每个研究视图都 `ready` 并显示便签标题（基线：6 章有按钮，另有 `yong-gate`「雍门与通口」只能通过 URL 进入；14 个研究视图） | 漏章、某章报错或不 `ready`，都判 FAIL | 0 容差 |
| R5 | 近景换档覆盖 | 清单里 6 个 `nearUrl` 都被请求到。S05 先在网格上点选不同的院落，再进入院落档（基线：第 23/24/25/20/22/26 院覆盖了全部 6 种） | 少于 6 个时：有覆盖判 WARN，一个都没有判 FAIL | 凡是改院落的批次，必须 6/6 |
| R6 | 模型选择 | S05 用真实指针事件：空白处（画布 8%,50%）点击不出便签；网格搜索命中一座「住宅院落 · 第 N 院」；进入院落档会请求 LOD0 | 空白处点出便签判 FAIL | 基线：第 26 院，请求 `TC03-2-LOD0` |
| R7 | 镜头 | 方向键和 `+` 之后截图 SHA 改变；按 R 能回到 `ready` 的全城档 | 截图没变说明键盘镜头失效 | 只比较 SHA 是否改变 |
| R8 | 故障路径 | N01（GLB 404）、N02（64 字节伪 GLB）、N03（`WEBGL_lose_context`）都显示 `#error`，舞台回到 poster | 任何一项进入 `ready` 判 FAIL | 文案匹配 `/404/`、`/载入未完成/`、`/三维显示已暂停/` |
| R9 | 资源用量 | 峰值 JS 堆、GPU 进程专用显存（Windows 计数器 `GPU Process Memory(pid_*)\Dedicated Usage`）、重载视图 GPU 同步帧 p95，都在基线 ×1.25 + 绝对余量以内（堆 +16 MB、显存 +64 MB、帧 +2 ms） | 超限判 FAIL，除非批次 manifest 预先申报了增量并经 LY-010 接受 | 只和同类设备的基线比；数值见 §3 |
| R10 | 视觉回归 | 和同设备基线逐步差分（只取画布，像素差 >8 才算变化，变化比例 ≤0.002 **且**变化像素 ≤50）；凡有变化的步骤，必须列在 `--expect-changed` 里 | N04（wall-05 换成 wall-00，全城档）和 N05（A2 换成 R01-A，住宅档）都**必须**被抓到，否则检查器无效。实测 N04 只变了 216 个像素（0.029%），**只看比例的门会漏掉它**，所以要加 `--tol-abs 50` | 同设备噪声底：45 张里 44 张字节完全相同，变化像素为 0（最大通道差 8，没超过阈值）。独显对集显最多 1.46% 的像素不同，所以跨设备对比最多给 WARN（实测跨设备 verdict 的 R9、R10 都是 FAIL，说明必须同类设备对比） |
| R11 | 手机 | 仿真模式下先停在 poster、不请求 GLB；点 `#start3d` 后进入 `ready` | — | 只是仿真。真机永远记 `UNTESTED`，是否阻断按 LY-010（目前还没有交付） |
| O1 | 开孔（插桩） | 广阳门门道：在 y=1.6 和 y=0.5 处水平射线 60 m 内无命中；扫描宽度 8.00 m（步长 0.25）。雍门：扫出 3 个门道，宽 2.75 / 4.25 / 2.75 m | 同一条射线移到 wall-09、wall-08 或门楼高度，必须在 30–50 m 处命中实体；门道被堵住时射线会命中，判 FAIL | 宽度误差 ±1 个步长（0.25 m）。这里只说明「单一高度的光线通过」，**不是**人体或车辆通行，也不是净空证明，那是 LY-095 的事 |
| T1 | 纹理与颜色 | 城景渲染器只保留 position 和 normal，颜色按材质名和 baseColor 映射（`pigmentFor`）。静态复算：48 个城景 GLB 的材质**没有**一个落到默认 `#bba98c` | 新件材质名不在映射表里、颜色又是白色时，会落到默认色，必须列出来 | 纹理是否正确显示**不在城景里验**：4 个 GLB 内嵌了 3.50 MB 贴图，城景照样下载、解码，然后丢弃。贴图外观改到资产详情页 `model-library/inspect.mjs` 去验 |

每一条 FAIL 都要定位到具体步骤、URL 或资产 ID 和截图；截图不能代替数值。

## 3 基线数值（「改前」，同机实测）

数值以 `prep/qa/baseline-summary.json` 为准，下表摘录。

| 量 | 独显 RTX 5090 | 集显 AMD Radeon |
|---|---|---|
| 导航到 `ready` | 631 / 636 ms（两次运行；本机回环，无网络延迟） | 711 ms |
| 首屏 | 54 次绘制 / 123,860 个三角形 / 59 个实例 / 3.87 MB | 相同 |
| 全城 66 节点 + 全城档 | 136 次绘制 / 690,048 个三角形 | 相同 |
| 重载视图 GPU 同步帧（全城档 + 66 节点，108 次绘制 / 634,440 个三角形；每次 rAF 后 readPixels 1×1；画布 1110×681） | p50 1.3 ms，p95 1.5 / 1.6 ms | p50 13.3 ms，p95 13.8 ms（距 60 Hz 的 16.7 ms 预算只剩约 3 ms） |
| 峰值 JS 堆 | 49.3 / 49.4 MB | 51.1 MB（较早一轮的单次运行曾到 77.8 MB 和 84 MB：堆峰值受 GC 时机影响，抖动大，所以 R9 留了 +16 MB 余量） |
| GPU 进程专用显存（整个浏览器 GPU 进程，不只是这一页） | 121–212 MB | 190–256 MB（集显主要用共享内存，这个计数器意义有限；Shared Usage 没有采） |

帧数据说明：页面按需渲染，没有连续循环。`intervalMs` 在 headless 下不受 vsync 限制，**不能当 FPS**。键盘环绕的帧间隔约 31 ms，由 CDP 发键节奏决定，不由 GPU 决定。

## 3b 检查器自身的负例（`source/selftest_checker.py`）

把一次正常运行复制一份再逐项篡改，每次只该打到目标检查：

| 篡改 | 应该 FAIL 的检查 | 结果 |
|---|---|---|
| 不篡改 | 无 | 全过（R5 也是 PASS） |
| 在市肆章节注入一条异常 | R2 | 只有 R2 FAIL |
| 从首屏请求里删掉一个 GLB | R3 | 只有 R3 FAIL |
| 渲染器名改成 SwiftShader | R1 | 只有 R1 FAIL |
| N01 负例改成没触发 | R8 | 只有 R8 FAIL |
| 重载帧 p95 乘以 3 | R9 | 只有 R9 FAIL |
| 用仓储截图替换市肆截图 | R10 | 只有 R10 FAIL |
| 空白点选的负例改成失败 | R6 | 只有 R6 FAIL |

结果记在 `qa/checker-selftest.json`（`allAsExpected: true`）。

## 4 不在本席位验、也不能被本席位代替的

- 「模型能读取」「局部通行通过」「已入城」「真实结构安全」「历史复原成立」是五件不同的事。LY-097 只给出「真实浏览器能加载、能交互、外观与资源有记录」，不替 LY-091–095 和 LY-098 下结论。
- 视觉比较只比画面，不改地理布局或基础资产；发现变化只能回报，不能修。
