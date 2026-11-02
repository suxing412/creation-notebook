# VEIL 008 · 几何与文件门禁评审

**本轮结论：通过限定范围的最终 native / GLB / 法向对应与专项回归门禁。** 这是模型层结论，不代替图像摄影、浏览器/GPU、制造或结构验收。核对时间：2026-11-02T01:50:02.612132+00:00。

## 1. 最终身份：只认三份 64 点资产

生产配方固定 `EDGE_STEPS=16`，每孔环 64 点；Blender 4.3.2，米，单件纯 raw mesh。以下每个身份报告同时核对退出码、新报告、显式 PASS、run ID、模型/GLB/info/checker/recipe SHA，以及检查前后输入稳定。此表不使用32点、中断或隔离实验的身份代替最终资产。

| 资产 | Native 顶点 | 三角形 | 真孔数 / 闭壳 genus | 前后 mouth 折线间距保守下界（取小） | GLB 角法向最大向量误差 | 证据 |
|---|---:|---:|---:|---:|---:|---|
| veil | 34,146 | 68,480 | 48 / 48 | 6.5708 mm | 8.4073239e-05 | [最终身份](gate-locked-veil-v1-identity.json) |
| horizon | 32,040 | 64,256 | 45 / 45 | 5.7004 mm | 8.5222033e-05 | [最终身份](gate-locked-horizon-v1-identity.json) |
| fold | 25,690 | 51,520 | 36 / 36 | 6.1453 mm | 8.1388593e-05 | [最终身份](gate-locked-fold-v1-identity.json) |

最终文件 SHA（再次从当前文件读取，不从旧候选借用）：

```json
{
  "veil": {
    "native": "77b4d3379cc69a879b28f4292b8892f2afb9fbb38ef381abd99d720a955aa59a",
    "glb": "288418a17258eb8a8c4deb03250502b4b580b950b4a2eacdd3ca94bd6747e177",
    "info": "4c50a17ee287efae8500ba47c7a5e70268de23e438d5996aa9c4d7bd0e9ceb35"
  },
  "horizon": {
    "native": "c2a0d59ce723f86b7e8b776c3532a3c65ec31e583f94256a5f2e775ede5a3a30",
    "glb": "09ff5f7b9da8a949cffac59c162235cb67c820812286974fc25944d2b37689f0",
    "info": "cfff9c63828fc7795e77bf3394016baef7b8c85f7ad27b5b02f2f0b94d539b13"
  },
  "fold": {
    "native": "a861bc31ee5bfbcd03b16ac4a150b37b75f8eddeac740c84c9eb8a75436e2e09",
    "glb": "2a3f7ebec1cc9041681d7ac7b70f7215bc66d854c0e44fd6a5a90be98bdfaae6",
    "info": "a0363b9454c4b6a41688eeeaa344997c79b47fab54f13a05cfe5b6711c6903aa"
  }
}
```

原生检查包含完整顶点及有向 polygon 索引循环契约、局部绕序、float64 世界有向体积、退化/重复面、非流形、连通分量、Euler/genus、逐孔实际环边 incidence/显式孔壁、中心贯穿射线、对应顶点法向厚度（非全表面最薄）、有限自交与近共面检查、metadata/纯模型状态/锁定材质和角法向有限单位长度/几何同半球。

GLB 检查解析真实 payload：chunk/buffer/view/accessor/stride/offset/alignment/min-max/有限数/索引/三角面积/单位法向/PBR与单场景单mesh契约。对应检查使用 `(x,y,z)→(x,z,−y)` 后**精确有向三角坐标多重集**，并逐匹配三角角比较法向（向量容差 `2e-4`，约0.0115°）。允许导出拆点；不是仅比较点集，也不声称索引图同构或精确法向相等。

## 2. 连料数值究竟保证什么

每条**实际网格 mouth / 外缘折线**边四等分，每64边孔口256样本；分别比较前、后侧孔口与其它孔口及同侧外缘的3D欧氏距离。采样最小值是连续折线最小值的上估计；逐边界对减去两侧最大采样间距的一半及0.2µm数值余量，形成报告中的保守折线下界，门槛4mm。输入层另要求 developed cell margin≥5mm。

**不是**圆弧/孔壁全表面的最薄连料、测地距离、投影间隙、制造壁厚、强度或站立稳定性。详见各native报告 `ligament_sampling.definition/excludes`。64点使采样覆盖余量缩小；下界升高不能单独当作实际物理连料变厚。

## 3. 实际坏文件与有限参数覆盖

- [最终 Veil 文件为基线的实际反例](gate-faults-final64-v1.json)：23个native坏网格/状态/控制、6个畸形GLB，全部达到各自指定字段预期；正式文件及依赖前后 SHA 不变。孔封闭、壁缺失、环错配、genus变化、实际厚度/连料缩窄、世界反向、岛/穿插/共面与移离控制均独立命中所声明的字段。世界反向例同时要求局部体积正、世界体积负；包容岛和+1µm控制要求没有表面相交命中。
- [三个合法却错误的导出](gate-export-comparison-tests-final64-v1.json)：平移位置、反向三角、翻转单位normal均先通过payload检查，再被对应字段拒绝。后两例保留坐标点集，证明只比较点集不足。
- [输入回归](gate-input-final64-v1.json)：183项显式输入测试；512个二值参数盒角点中276通过有限公式完整validator。角点未逐一生成网格，不能当连续域证明。
- 两个命名边界真实网格：[low](gate-boundary-low-64-v1-identity.json)、[high](gate-boundary-high-64-v1-identity.json)；它们不是所有端点组合的实际几何验收。
- 同64点、相同摄影/材质/渲染预算的rev0 before拥有[自己的最终文件门禁](gate-rebuild-2bf55b6c0963-final-identity.json)，不是借32点报告。外观比较由作者/独立视觉评审负责。

**覆盖缺口明确保留：** `input_contract_failures`、`nonfinite_coordinates`、`object_contract_failures`、`object_transform_failures`、`recipe_topology_failures`、`recipe_vertex_envelope_failures` 没有被本批专门以该字段为目标定向触发；其它反例中顺带出现不算独立覆盖。normal字段只专门注入反向半球，native NaN/非单位法向分支未独立注入；状态测试覆盖modifier/shape key/parent/object animation，不是所有constraint/driver/mesh-animation。畸形glTF测试不是穷尽。

## 4. 失败历史没有被覆盖成“从未失败”

1. 原32点首版孔壁 quad 多反转一次，真实 local winding 错误。稳定复测见[原坏网格](gate-historical-original-archived32-v3-native.json)：local winding、配方有向拓扑与48孔wall专用字段失败。它不是合格before；64 before另行生成、另绑身份。
2. 最初门禁运行中recipe变化，身份wrapper明确失败；最初材质QA也把白Emission Color错误当作发光，未乘以零strength。初始报告保留，修复不追改旧结果。
3. 加normal字段时的QA文本替换引入tuple key回归：实际缩窄网格被整体拒绝，但因KeyError而**漏掉专用连料字段**。见[失败与同一坏网格修复复测](gate-qa-regression-history-v3.json)。精确坏checker源码安全归档；坏binary不公开。新增AST键契约只是补充，不能替代真实坏网格。
4. 64隔离原型曾因计数变量与normal变量重名而不能写出native报告；wrapper正确拒绝。修复后的[64实验整套](64-probe-suite-summary-v3.json)只算实验依据；最终三asset仍以第1节为准。
5. [暂停的32 final-v2链](gate-interrupted-final-v2.json)退出130，标签作废，未获得最终放行。

### 32历史源码：精确 SHA 对应，不拿最后快照冒充所有版本

完整对应关系见[历史源身份索引](history-source-sha-index.json)。以下哈希只证明源码字节对应；复跑必须配对报告所需recipe/checker/test及原输入字节，重新保存blend并不保证原文件SHA，时间/run ID也不会逐字复现。

| 历史源码（iteration-32-source） | SHA-256 | 匹配报告示例 |
|---|---|---|
| [`check-1.0-corrected32.py`](iteration-32-source/check-1.0-corrected32.py) | `5ded39d1c74aecd70ff577e0a11efce1a49df39788085286fc8d10d85b6eea7c` | gate-baseline-corrected-v1-identity.json, gate-baseline-corrected-v1-native.json, gate-boundary-high-v1-identity.json … |
| [`check-1.0-initial.py`](iteration-32-source/check-1.0-initial.py) | `bb6ca476b5a298dea2be602958bac2e79135100534bde4f5137d6214d49f647d` | gate-first-v1-identity.json, gate-first-v1-native.json |
| [`check-1.1-known-ligament-key-regression.py`](iteration-32-source/check-1.1-known-ligament-key-regression.py) | `8cb7f7239eedc7d7ba73f1187e8a6a63bd402dfc3805de12033f286542a88e6b` | gate-baseline-corrected-v2-identity.json, gate-baseline-corrected-v2-native.json, gate-boundary-high-v2-identity.json … |
| [`check.py`](iteration-32-source/check.py) | `47eb13f1d3257ae97f2ff8fd9b4efd68516ecb973d20d1f52332464d61148cdf` | gate-historical-original-archived32-v3-native.json, gate-historical-original-archived32-v3-proof.json, gate-ligament-qa-regression-repaired-v3.json … |
| [`check_glb-initial.py`](iteration-32-source/check_glb-initial.py) | `98a73972b6b4bef972305af660f24e32a1880514b9083d8f413a1b2f574592d5` | gate-first-v1-comparison.json, gate-first-v1-glb.json, gate-first-v1-identity.json |
| [`check_glb.py`](iteration-32-source/check_glb.py) | `5e682d4a4e74a920adb86f49f15b448f619cdda81fd13d904b950dfff58dce11` | gate-baseline-corrected-64-v1-comparison.json, gate-baseline-corrected-64-v1-glb.json, gate-baseline-corrected-64-v1-identity.json … |
| [`compare_exports-initial.py`](iteration-32-source/compare_exports-initial.py) | `129d79a93d8e0109beff692c448d425989fe12598b231b9f068621c9732e979f` | gate-baseline-corrected-v1-comparison.json, gate-baseline-corrected-v1-identity.json, gate-boundary-high-v1-comparison.json … |
| [`compare_exports.py`](iteration-32-source/compare_exports.py) | `bc5315bb1849db6106f82bf982bc7c69d18decb2a621460673649782404dc629` | gate-baseline-corrected-64-v1-comparison.json, gate-baseline-corrected-64-v1-identity.json, gate-baseline-corrected-v2-comparison.json … |
| [`generate.py`](iteration-32-source/generate.py) | `45252476b9be9b15da726d9213dcf5cf56bbf4050d2346353d657e8e22355834` | 无已匹配历史报告；仅归档，不追认 |
| [`recipe-original-invalid.py`](iteration-32-source/recipe-original-invalid.py) | `f695b183a5a3fab45ed9d8fc78ab412bc667e07227d73c72cc4733ad99a7bbae` | gate-first-v1-native.json |
| [`recipe.py`](iteration-32-source/recipe.py) | `2ce6832921c86a5ad763ffb036d2bbd816b385dce6fce2f8e56272b571659a37` | gate-baseline-corrected-v1-identity.json, gate-baseline-corrected-v1-native.json, gate-baseline-corrected-v2-identity.json … |
| [`run_gates.py`](iteration-32-source/run_gates.py) | `5910c837e77e7277dcf5d7406217979a00ae9b08584ada42d262239df2eb73fc` | gate-baseline-corrected-64-v1-identity.json, gate-baseline-corrected-v1-identity.json, gate-baseline-corrected-v2-identity.json … |
| [`test_contract.py`](iteration-32-source/test_contract.py) | `be1cae28a4dba5be7091b9e08d85ad8a9dc059f88a1add17309c3f270841d3ba` | gate-input-final64-v1.json, gate-input-v1.json |
| [`test_export_comparison-v1.py`](iteration-32-source/test_export_comparison-v1.py) | `3d05ae4442cbace2b13b767fc8533597df87b8cd57c65223065ad0a7c40e8d52` | gate-export-comparison-tests-refined-v1.json |
| [`test_export_comparison.py`](iteration-32-source/test_export_comparison.py) | `d1f55cd79d96e488bf96bd15afb44bb688cc038aa44507997e66f62da234dfae` | gate-export-comparison-tests-refined-v2.json |
| [`test_faults-v1.py`](iteration-32-source/test_faults-v1.py) | `fb23f8b3a6e7238180ee132ee39d92f959afe187eadc74013c25afc685c12323` | gate-faults-v1.json |
| [`test_faults.py`](iteration-32-source/test_faults.py) | `898a1b44d4aa3cefec4a618b864b51a7ef7762d57201d6e60be8f438be14508a` | 无已匹配历史报告；仅归档，不追认 |

## 5. 最终检查源码身份

- `recipe.py`：`0ae15a7cf8eb67d715b682665aa932c1725517da817e568070d2f80307a7a52d`
- `check.py`：`7c022dddc455c992d4766075b59a76fd3acad6d4e2dfba3a41d5359592759671`
- `check_glb.py`：`5e682d4a4e74a920adb86f49f15b448f619cdda81fd13d904b950dfff58dce11`
- `compare_exports.py`：`bc5315bb1849db6106f82bf982bc7c69d18decb2a621460673649782404dc629`
- `run_gates.py`：`5910c837e77e7277dcf5d7406217979a00ae9b08584ada42d262239df2eb73fc`
- `test_faults.py`：`e28260fea8899927ce8d7fda9d25f500c9a80aa5eb1a5eee09f4f1bb4601327e`
- `test_export_comparison.py`：`6b493d6eab28eb39d978b5eaa1b74a6b107dda8547d319212bbb5e826f01b160`
- `test_contract.py`：`be1cae28a4dba5be7091b9e08d85ad8a9dc059f88a1add17309c3f270841d3ba`

## 6. 限制与未验

BVH候选排除共享顶点三角，因此非共面的相邻面折返并未被完全独立证明；近共面是双向float64平面距离+投影SAT容差测试，不是精确符号谓词。完整配方坐标/有向拓扑契约限制了可接受家族，但不能替任意网格证明。native法向合理性与GLB对应通过，不等于独立证明作者解析法向公式。角法向差值的量化来源是合理解释，未被单独隔离证明。

本报告不证明GPU/WebGL运行、动态闪烁、真实触控/iPhone、物理制造、承载或稳定性；没有把这些未验项目改写成已通过。摄影scene.blend不是纯模型state门禁对象。坏样本与原始工作日志留在work，不能混入正式资产包。
