# LY-066 测试计划（制作时直接跑）

所有脚本都在 `prep/scripts/`，都是只读的。Python 用 `python -I` 运行，Blender 用 `D:/Blender/blender.exe -b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。
`$F` 指 `D:/GitHub/creation-notebook-lab/docs/library/models/m-luoyang-yutang-halls/files`，`$O` 指交付包的输出目录（`workpacks/LY-066/qa/`）。

## 0. 绑定的 SHA（输入冻结）

| 文件 | sha256 |
|---|---|
| yutang-A-LOD0.glb | 6e7f06c054d07984e611f9bfdff80117feee3af246a2394eb289a35e8496e4f1 |
| yutang-A-LOD1.glb | 297c11b01604122c93167ede4a8417cb5f5e54cefc050e33d9a0bb78d9d005a8 |
| yutang-A-LOD2.glb | 6ff5440cc0be55639148c73f7e5c16179be269b5532da5f6672312a84b2738be |
| yutang-B-LOD0.glb | 92091dbe9c51e72b717a69c9ba41f6db13a2c79e77eb5f145c1881e9570b9eba |
| yutang-B-LOD1.glb | 1566de0280fbe50d345abee80b27169254f685eda7252d3e1c254ef4cf8ad38b |
| yutang-B-LOD2.glb | 965ab0b851398f1f3ac52e5ca02f5873c73648ad150730f7969377a1ea267844 |
| asset card（提交字节） | 72266b3ecc7b8b156ffa3ce358451a0461e07d3b82be779c2415c7dbc3bba82b |

节点几何指纹由 `fingerprint_ports.py` 生成，取 `nodes.*.geom_sha256_r1e4`：

| | earth | timber | tile |
|---|---|---|---|
| A-LOD0 | be9c3bcb8049… | aa1efa4c303e… | b31c82a6bdea… |
| A-LOD1 | be9c3bcb8049… | aa1efa4c303e… | 3ff80813a43a… |
| A-LOD2 | be9c3bcb8049… | 7d84e63785cc… | 6a49b71a7ba5… |
| B-LOD0 | 80f07aeac1b6… | c926966fcf42… | 266cf666b696… |
| B-LOD1 | 80f07aeac1b6… | c926966fcf42… | 33710b85b30a… |
| B-LOD2 | 80f07aeac1b6… | 5d125184bef5… | f70c310083e2… |

完整 64 位值见 `prep/out/ports-*.json`。G 冻结之后，如果 LY-001 的新快照显示 SHA 有变化，就先重跑第 0 到 2 节，重定基线，然后才进入制作。

## T1 输入未变（正例与负例）
- 先跑 `sha256sum $F/*.glb`，六个值都必须与上表一致。再用 `git -C lab show <main>:…asset.json | sha256sum` 核对资产卡（比的是提交字节，不是 CRLF 检出的字节）。
- 负例：把任意一份 GLB 复制到临时目录，翻转 1 个字节，T1 必须报失败。

## T2 交付包引用原件、不复制改名
- `delivery-manifest.json` 里每个模型条目都要写原路径和上表的 SHA。如果包内带了 GLB 副本，副本字节必须与原件相同。
- 三档 LOD 的 SHA 两两不同，tile 指纹也两两不同。负例：把 LOD0 复制成 LOD1，T2 必须失败。

## T3 组件世界相对关系（安装后重算）
- 对安装后的输出（演示域里经过变换的 GLB，或场景导出的 GLB）运行 `python -I scripts/fingerprint_ports.py <out.glb> $O/ports-<v>.json`。
- 把安装变换 M 的逆作用到输出坐标上，得到的组件表（平台、踏步、墙、柱、廊顶的包围盒）必须与 `prep/out/ports-*.json` 和 `prep/out/measure-*.json` 一致，容差 ≤0.001 m。
- 必须成立的关系（A/B 分开验）：
  - 庭面 y=0.000；殿台和廊台顶面 0.600；
  - 前殿台基 z∈[12.5, 31.5]（A）/[10.0, 29.0]（B）；后殿台基 z∈[−31.5, −12.5]（A）/[−29.0, −10.0]（B）；
  - 两组廊柱 x=±10.85、±13.15；A 为 8 列，间距 4.0；B 为 7 列，间距 3.833；
  - 前殿柱距 5.6，后殿柱距 8.0。
- 负例：把后殿平移 +0.05 m 生成测试 GLB（在 Blender 里内存操作后导出到 temp），T3 必须报偏差。

## T4 屋顶端部不回退
- tile 节点几何指纹必须与第 0 节的值完全相同（不设容差）。原因是本席位不允许改 tile。
- R3 指纹：廊顶端部 z=±15.0000（A）/±12.5000（B）；殿檐边线 ±14.2869（A）/±11.7869（B）；廊顶 y 最大 4.485；端部最小净空 1.2686 m；殿顶范围 x±13.7 / ±15.7，屋脊 8.835 / 8.435。容差 0.001。
- 负例：把廊顶端部的顶点削去 0.7 m（缩回到殿檐以外），T4 必须失败。
- 限制：这项检查只能证明「与 bce3211 现状一致」，证明不了「与旧修订一致」，因为旧修订的记录不在仓库里。

## T5 外接端口可重算
- 端口必须由 `fingerprint_ports.py` 从几何重新推导，不能从旧 JSON 拷贝。期望值如下（模型坐标）：
  - 前入口 front-entry-step-foot：A (0, 0, 32.86)，B (0, 0, 30.36)；宽 4.0；高程 0→0.6。
  - court-step-rear-hall：A z=−11.14，B z=−8.64。court-step-front-hall：A z=+11.14，B z=+8.64。宽都是 4.0。
  - rear-hall-door：A (0, 0.6, −16.0)，B (0, 0.6, −13.5)；净宽 4.0。
- 端口要同时用模型局部坐标和安装后的世界坐标表达（LY-005 的要求）。用 M 作用到局部端口上，结果必须等于对安装后几何重算出的端口，容差 0.001。
- 端口 ID 和版本必须与 LY-006 的模板一致。
- 负例：踏步换成 3 级，端口高程或宽度变了，比对必须失败。

## T6 接地
- 平台和踏步底面 y=0.000；庭台基脚 y=−0.24，属于声明的埋入。
- 所有柱和础的支持落差 ≤0.005（`measure.py` R4，现值为 0）。
- 演示域的外部地面 y=0 必须覆盖踏步脚外至少 2 m（具体数值以 LY-005/006 为准）。前入口踏步脚处下射线必须命中地面。负例：撤掉外部地面后，这条射线必须报悬空。

## T7 A/B 互斥与安装/撤回
- `assembly.json` 必须写明 `exclusiveGroup: "yutang-config"`，A 和 B 各自作为一个成员。
- 在演示场景里只启用 A 时通过，只启用 B 时通过，两个同时启用时检查器必须报错。现在 B 的占地 100% 落在 A 内，正好可以作为负例。
- 安装后撤回：场景节点、矩阵、材质和几何指纹都要回到安装前的状态。原有三个节点的指纹前后不变，场景里不残留节点。
- 旧方案和新方案不能叠在一起加载。

## T8 cityPlacement 和身份字段
- `assembly.json` 里 `cityPlacement` 必须是 null，`historicalPalace` 是 null，`cityInstalled` 是 false。
- 用 grep 检查交付包：不得出现「复原」「宫址」「南宫某处」这类定位措辞，也不得出现绝对城市坐标。出现「玉堂」只能作为来源殿名的 C 研究语境。
- 负例：如果在 assembly 里写一个 cityPlacement 对象，T8 必须失败。

## T9 继承缺陷原样披露（数值回归）
- R1：7 段墙顶到屋面的缝在三档里都是 0.552±0.001 m。数值变了，说明有人偷偷改了殿体，这一项算失败，而不是算修好了。
- R7：A-LOD0 的 AABB 侵入对数为 100（墙×柱 16、墙×础 16、墙×枋 12、墙×墙 4、柱×枋 52）；B 的数值以 `prep/out/measure-B-LOD0.json` 为基准。逐对归类后写进 `qa/contacts.json`，不允许整类豁免。
- Blender 回读用 `blender_readback.py`：尺寸 A 为 35×64.36×9.075，B 为 35×59.36×9.075；UVMap 层存在；earth×tile 的表面重叠对为 0。

## T10 有限通行（回归）
- 跑 `python -I scripts/route_probe.py $F/yutang-A-LOD0.glb $O/route-A.json -19`，B 跑同样命令，末参数为 −16.5。
- 期望结果：A 有 209 个样点，B 有 189 个；相邻高差最大 0.15；最小净高 5.06 以上；包络侵入为 0。
- 负例：在路线上放一个 0.3 m 高的障碍盒（内存操作），侵入数必须大于 0。
- 说明：这是盒子样点，不是连续人体运动，也不是步态或无障碍认证。

## T11 官方检查与预览
- 由 LY-100 在合并队列里运行 `lab/tools/build_assets.py --check`，本席位不运行。本席位只跑 LY-008 的检查器。
- 预览图标注「CPU（Blender Workbench）」：A/B 各出同机位的前视、背视、俯视，再加墙顶缝的剖面。不声称做过 GPU 或手机测试。

## T12 LY-006 接口校验（第二轮新增）
- 命令：`python -I LY-006/source/validate_interface.py LY-006/registry LY-066/interface.json LY-066`，结果必须是 PASS。
- 现有基线：prep 草案 `prep/interface-draft/interface.draft.json` 已经 PASS。
- 负例：以下 5 个文件必须全部 FAIL，并分别报出 prep 中记录的错误：
  - `neg-modify-tile`
  - `neg-world-while-unplaced`
  - `neg-outside-zone`
  - `neg-port-version`
  - `neg-foreign-object`
- 正式交付时，`portsProduced[0].local.position` 必须等于 `fingerprint_ports.py` 对实际选定变体重算出的 front-entry-step-foot，误差不超过 0.005，高程误差不超过 0.002。
- 需要绑定的 SHA：
  - registry seats a1426412…
  - ports 28bcfb68…
  - zones 6b3595ac…
  - ownership ecbbbcf5…
  - seams ca4d81f8…
- 如果 registry 升级到 v2，先重跑本项和 T5，再继续。

## T13 写入区包含
- 本席位交付的任何新几何（例如 `gp:LY-066:apron`），包围盒都必须落在 [-19.5,-0.3,-33.5]..[19.5,0.3,34.9] 内。
- 负例：一块 x 到 −20 的地坪片必须被 T12 拒收。prep 里已经验证过这一点。
- 六份原 GLB 不算作写入，它们是 keep。

## T14 变体与端口一致
- 如果只交 A：端口取 (0,0,32.86)。
- 如果只交 B：端口取 (0,0,30.36)。
- 负例：用 A 的端口值去配 B 的几何，残差 2.50 m，必须 FAIL。
- 如果两者都交，registry 必须已经有分变体的端口 ID，否则直接判阻断。
