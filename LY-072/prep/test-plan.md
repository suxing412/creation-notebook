# LY-072 测试计划（v2，2026-11-06；制作时直接跑）

所有检查都绑定实际文件的 SHA256，结果写进 `workpacks/LY-072/qa/`。检查只用 CPU 射线和 BVH，所以不声称做过 GPU 测试、人体连续运动或荷载验证。

「模型能读取 / 局部通行通过 / 已入城 / 真实结构安全 / 历史复原成立」五项分开写结论，任何一项的通过都不能替另一项作证。

## 0. 前置绑定（有一项不符就阻断，不开跑）

| 绑定 | 期望值（当前） | 冻结后改绑 |
|---|---|---|
| 礼堂A LOD0/1/2 | 937a3192…e1e8 / 5dc71e32…fcbfb / 48222261…21dd4 | 改绑 LY-071 交付的 SHA |
| 围护 | L-LOD0/1/2：88f227d0… / 69ae00ce… / 60026711…（×4 R_y），或 A-v2 | 用 LY-071 选定的版本 |
| 试配分块 | 1bd1c446…ffa1（ZIP 5895ef23…） | 改绑 LY-071/073 的冻结输入 |
| 坐标契约 | LY-005 coordinate-contract.json b6d7fe9d…、port-schema.json 30854ed9… | 改绑正式冻结版 |
| 端口与区 | LY-006 zones.json 6b3595ac…、ports.json 28bcfb68…、seams.json ca4d81f8… | 只有 **registry v2** 能用，见 T9 |
| 质量基线 | LY-007 lod-rules.json fbf53757…；检查器 LY-008 ly_check.py 39aaa491… | 改绑二者的冻结版 |
| 证据 | LY-002 evidence-ledger.md ea060db6…，E-R05 已复核 | — |
| 方案 | LY-010 决策表里辟雍的布局与实例方位 | — |
| 本项交付 | crossing-LOD0/1/2.glb、assembly.json、interface JSON，各自的 SHA 写进 qa | — |

上表任一项缺失，结论一律写「待输入」，不能写「通过」。

## T1 支承（check_crossing.py）
- **方法**：从桥底逐格向下打射线，步长 0.05，覆盖全宽。射线只打上下文实体（岛、外岸地面、支座）；水网格不参与。
- **正例**：内、外两端在最差的那条侧向线上，连续支承长度都要 ≥ 0.30 m（这是 C 设计值，不是荷载结论）；`gap<-0.005` 的格数为 0，即没有正体积侵入。
- **负例**（每条都必须失败）：
  - 4 块旧 A_crossing：已跑，外端 0.0 m，T1=false（qa/baseline-placeholder-*.json）。
  - 交付件沿轴外移 0.5 m：内端支承应 < 0.30。
  - 删掉外支座或外岸：外端应为 0。
- **容差**：面接触 ±0.005 m；采样量化 ±0.05 m。

## T2 桥面连续与高差（不只用中心线）
- **方法**：用 5 条侧向线，即 −0.925w、−0.5w、0、+0.5w、+0.925w（w 为半宽）。从内端口前 2 m 一直走到外端口后 2 m。
- **正例**：
  - 相邻采样高差 ≤ 0.20 m，与礼堂踏步的踢面相同。
  - 坡度 ≤ 1:7（14.3 %）。墙外只有 1.45 m（68.35→69.8），坡最多能升 0.207 m。
  - 没有空采样：外端过口后要有外岸，这一条依赖 LY-073。
  - 2.0 m 净空内没有遮挡。
- **负例**：旧件的 0.30 m 高差和外端空采样（已跑，失败）；把桥面抬高 0.35 m，必须失败。
- **身体包络（C）**：宽 0.6 m、高 1.8 m，沿 5 条线离散采样。货物和车辆不在本项范围，写「未测」；「车驾从北门入」也不能用这个包络来证明。

## T3 端口
- 端口 ID 必须是 `biyong:crossing-ends:ground`，version 1。内、外两端都要写 local（local:biyong，glTF Y-up）、world，以及所用的 N 和测量文件的 SHA。world 必须能用 N·local 重算回来，残差 ≤ 1e-5 m。
- **内端**：高程与 LY-071 `biyong:hall-enclosure:ground` 的岛面差 ≤ 0.002 m（这是 LY-006 的 elevation 容差），否则要由踏步或坡过渡。宽度 ≥ 墙门口 8.0 m，或者明确写出收窄。
- **外端**：LY-073 使用的 portId、version 和数值必须与本项逐字节相同；位置容差 0.005 m。LY-073 还没冻结时，只能输出「外端口待对接」，不能标通过。
- **负例**：把端口 version 改成 2，或把 z 改动 0.01 m，校验必须失败。
- **模板**：用 LY-006 的 templates/interface.template.json 填表，跑 schemas/interface.schema.json 的校验器。

## T4 接触分类
- **方法**：桥与岛、支座、外岸逐对用 BVH overlap 找候选三角对，再用体积采样分成三类：合法面接触、正体积侵入、完全包含。只做了表面 BVH 时，结论写「表面检查，实体碰撞未穷尽」。
- **负例**：桥与墙（t ≤ 68.35）应该没有接触，试配里两者相距 1.45 m。出现交叠就必须报出来。
- **继承缺陷**：礼堂 earth 的 20 条非流形边只注明，不计入本项。

## T5 水
- 桥底与水面的净距 ≥ 0。试配是 0.10 m；顶在 +0.20、板厚 0.30 时净距正好是 0，属边界情况，要明写。
- 水网格不计入支承。
- **开关测试**：隐藏水符号后重跑 T1/T2，结果 JSON 的 results 必须逐项相同。
- 不报水深、流速，也不下水工结论。

## T6 三档结构轮廓（按 LY-007 lod-rules）
- `python -I LY-008/source/ly_check.py lodset crossing-LOD0.glb crossing-LOD1.glb crossing-LOD2.glb`：SHA 互不相同，三角数 LOD0 > LOD1 ≥ LOD2，包围盒差 ≤ 0.01 m。
- 夯土支座、梁、板按「keep」规则：**三档顶点逐一相同**（0 偏差）。圆木桩柱按 16/12 边 → 8 边 → 2r 方盒。LOD2 用 FLAT 材质。
- **轮廓**：两端支座区的俯视占地栅格（0.05 m）IoU ≥ 0.95；纵剖面（中心及 ±0.5w）最大高差 ≤ 0.05 m；支座、跨体分件的语义三档都在。
- **负例**：
  - LOD0 复制改名充当 LOD1/2，会被 SHA 检查拦下。
  - LOD2 只剩一块平板、没有支座时，IoU 和分件检查都应失败。

## T7 GLB 规范
- 对每档跑 `python -I LY-008/source/ly_check.py glb crossing-LODn.glb --profile ly-p01 --lod n --json qa/glb-LODn.json`，error 数必须为 0。
- 单文件 ≤ 15,000,000 字节；米制；本地 +Y 向上，原点在接地面（LY-005 newAssetRules）；节点和材质有名；UV、法线齐全；没有退化三角，几何值有限；焊接后边界边为 0，或逐条解释。
- 官方 `lab/tools/build_assets.py --check` 只在 LY-100 的合并副本上跑（ly_check.py official），本席位不在 lab 仓库里运行。

## T8 安装与撤回
- **安装**：在冻结的输入上，隐藏或替换被选方位的 A_crossing，加载新件。
- **撤回**：撤回后，原节点的几何、材质、矩阵 SHA 要与安装前一致（对照 qa/chunk-extract-record.json 里各节点的 evaluated_world_directed_triangle_sha256）。
- **负例**：新旧件同时可见就算失败，判据是同一轴向 t∈[69.8, 78.2] 内同时存在两套跨水件。
- N 只施加一次：把 +1.2 再加一遍，T3 内端高程必须失败（差 1.2 m）。

## T9 写入区与所有权（zone_evidence_check.py 改成读 v2）
- 交付件每个顶点都要落在 LY-072 的写入区里（registry v2），并且和 LY-073 区的交集体积为 0。
- 要隐藏或替换的每个源节点，在 ownership 里都必须是 LY-072 的 modify/replace。
- **负例**：用 v1 的区（x 20.4–30，±2.5）跑当前的试配件，包含率应为 0.0。已跑：qa/zone-evidence-check.json。

## T10 证据方位
- 实例方位必须与 LY-010 的选择和 LY-002 复核后的 E-R05 一致。
- 如果复核后的结论仍是「北无水」：北面（Blender +Y，glTF −z）不能有跨水件，`side-water.json` 的 N 带 crossingCells 必须为 0。
- 如果改读为「水周其外」：北面实例只能标 C，并注明「原文未记桥」。
- 卡片和说明里不能出现「四桥」「后世辟雍桥」作为依据。

## 不做的声明
- 几何支点 ≠ 承重；本项不做荷载计算，不写结构安全。
- 局部通行通过 ≠ 已入城 ≠ 历史复原成立。
- CPU 渲染的图要标 CPU；没有在浏览器或 GPU 上实测，就不写「已测」。

## 运行
```
python -I prep/extract_chunk.py <scratch_dir>
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/check_crossing.py -- qa/params-<axis>.json qa/result-<axis>.json
D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P prep/measure_side_water.py -- <chunk_or_assembled.glb> qa/side-water.json
python -I prep/zone_evidence_check.py D:/GitHub/creation-notebook-workpacks qa/zone-evidence-check.json
python -I ../LY-008/source/ly_check.py lodset|glb|package ...
```
params 的格式见 check_crossing.py 文件头。候选 GLB 以 `role: crossing` 加入并给出 `matrix`；旧 A_crossing 通过 context 的 `exclude` 排除。
