# LY-077 验收测试计划（制作时直接跑）

验收依据：任务池「本项验收」。院外端口到 A 每个既有入口，都要做完整的支持和体积检查；原 A 入口修订不变；B 模型不混入；外接关系只是 C 的，要明说。

工具：`D:/Blender/blender.exe`（5.2.1）。调用格式：`-b --factory-startup --python-exit-code 1 -P <脚本> -- <参数>`。

检查器：`prep/check_arrival.py`，SHA256 `568c65e363cb6aa57591a3e2d8331c1f43876ee3442e9b0d09e2dfb8165643f2`。每份报告里都写了 `checker_sha256`。以后若改检查器，必须先把下面 §6 的自检全部重跑一遍。

坐标系：A 的 local-study 帧，glTF 轴向，X 向东、Y 向上、Z 向南，单位米。

## 0. 要绑定的 SHA（任一不符就停）

| 对象 | SHA256 |
|---|---|
| A LOD0（公开源包内） | `ed40ae07e41060726781185d709017f43ac95bd2c6eac58f003582109c0a87f6` |
| A LOD1 | `413c2f35ec264dfbc6f24c1ceab9a0f8ce492c975b50e34fd5320ad25be391f2` |
| A LOD2 | `b911beb4c21aa7cc56d8e7d69660e23ac56dcad357635e008a3f300046e03860` |
| A 城景 flat 投影 | `ee4163421d1652b9301b8d50c7fe9f04ed09440000683b9a207ddf3f1600dda3` |
| A 几何哈希（LOD1 = flat，按三角排序，保留 4 位小数） | `283181be5b2737d2…`（完整值见 `qa/measure-LOD1.json`） |
| 公开源包 ZIP | `83556f30e8e88c56f8578b84afba00fe81d4c611cadb23acd30d7e3cbf4e671d` |
| 原入口检查器 `check-entry.py` | `d8c83c3a47fde5dd59dde2d6786f8e68dd810fd17c78f99bc86be5f7b6d5f8a6` |
| B（禁止出现在交付里） | `11b01e4948be0e0e229116b9eaa939f6b932058a0d3513ac676012188a260c57`、`fa828ef0ee2188fbae5149fc8c85dd7df1d8dfc4c2e6cacaaf19903908ecf089`、`eea1607b4d87653e09c69c36c79bc75c38ca7bb07da1ef0769c9b3c7b61a03b4` |
| 新到达地块 GLB、端口 JSON、assembly.json | 制作时填入，写进 `delivery-manifest.json` |

## 1. 原 A 入口修订不变（回归）

- **T1.1：** 对上表四个 A 文件逐个计算 `sha256sum`，必须与表中值逐字节相同。新包只能引用这些文件，不能出现重导出的 A。
- **T1.2：** 把原检查器 `source/check-entry.py` 复制到一个只含三档 A GLB 的干净目录里运行。用 `sort_keys` 归一化后，结果必须与原 `qa/entry-volume.json` 相同：每档每入口侵入 0；踏步支承 27 个、失败 0；平台路线支承 168 / 168 / 117 个、失败 0。准备期已复跑并通过。
- **T1.3：** `check_arrival.py` 的 `A_unchanged_after_install` 和 `A_unchanged_after_withdraw` 两项都要为 true。具体是：A 的四个对象 `taixue-A-static_{earth,timber,tile,fiber}` 在装入地块前、装入后、撤回后，几何哈希相同，世界矩阵也相同（保留 9 位小数比较）。
- **负例 N1.1：** 把检查器的 `--a-sha` 故意填错一位，`A_sha_matches_expected` 必须为 false，整体判 FAIL。

## 2. 院外端口 → 每个入口：支持（三档 + flat 各跑一次）

```
blender ... -P check_arrival.py -- --a <A tier> --a-sha <sha> --patch <新地块.glb> --patch-sha <sha> \
    --port <LY-006 冻结的 X,Z> --port-y 0.0 --out qa/arrival-<tier>.json
```

- **T2.1 阶前垫：** 每个入口前方 2.2 m 宽、1.2 m 深，按 0.1 m 网格竖向探测，每个入口 264 个探针。命中面的高度必须落在 0.000 ± 0.003 m 内，失败数必须是 0。
- **T2.2 第一级踢面：** 第一级踏面顶（0.200）减去阶前地面，结果必须是 0.200 ± 0.003 m，和内部 0.2 m 的踢面一致。地块顶面抬高 5 cm（fixture `raised`）时，踢面变成 0.15，必须判 FAIL。
- **T2.3 端口自身支持：** 端口点的竖向命中必须在 `port-y ± 0.003` 内。
- **T2.4 侧向汇流：** 从端口到三个入口脚下各走一条 L 形路线（先沿 x，再沿 z）。每 0.1 m 取一个截面，每个截面在路线中线及其左右 ±0.39 m 各探一点，全部要有支持；中线上相邻两点的高度差不超过 0.003 m，即路上没有藏起来的台阶。
- 容差沿用 v3.2 的原检查：竖向 3 mm；体积底抬高 15 mm；体积宽 0.8 m、高 1.8 m。

## 3. 院外端口 → 每个入口：体积

- **T3.1：** 每条路线的 0.8 × 1.8 m 体积，与 A 和地块的**全部**三角做裁剪，侵入必须是 0。不对任何物件对整体豁免。体积在入口脚线 z = 4.85 处截断，台阶段由 T1.2 覆盖。
- **T3.2 地块不进 A 实体：** 地块三角在 A 平台盒和九个踏步盒内部（内缩 1 mm）的裁剪面积必须是 0。y = 0 处的贴面、踢面处的贴面属于合法局部接面，要在报告里写明。
- **限制（写进 qa）：** 只做了表面 BVH 和三角裁剪，不能说实体碰撞已经穷尽；也不是连续步态、转身扫掠、人群疏散或法规认证。

## 4. A/B 不混、互斥与叠载

- **T4.1：** 在交付目录里 grep `taixue-B`、`hall-B`、`study-taixue-B`、`B_`，以及 §0 里 B 的三个 SHA，命中数必须为 0。
- **T4.2：** 读取地块 GLB 的节点名和 extras，不得包含 `B_` 前缀，也不得包含 B 的源路径。
- **负例 N4.1：** 用 B 的 flat GLB 顶替 A 跑检查器，必须 FAIL。准备期实测：SHA 不符；中入口第一级踢面差 −0.2 m，阶前 28/264 失败。
- **T4.3 旧新不叠载：** `assembly.json` 必须写明新地块与两者互斥：v1 的 `A_presentation_ground`（`hall-A-LOD1.gltf` `1403135d…`），以及原生母版的 `C_TAIXUE_ISOLATED_SUPPORT_PATCH`（x ±23、z ±9、y −0.4…0，原生帧）。
- **负例 N4.2：** 把新地块和 v1 `A_presentation_ground` 同时装入，检查两者的共面重叠面积。只要大于 0，就证明「同时装入 = 叠载」，`assembly.json` 必须禁止这种组合。

## 5. C 明示与不焊接观经空间

- **T5.1：** 端口 JSON 按 LY-005 port-schema（`30854ed9…`）来写。`elevationClass` 必须是 `C-engineering`；`frames.local` 写 `taixue-A-local-study`。只要 A 还是 `cityPlacement=null`，`world` 就必须标「未配准」（null，或 LY-005 给的替代写法），不得用原生 [2367.347, −632.653, 0] 冒充城景坐标。
- **T5.2：** 地块、端口和路线的说明文字里必须写「C 工程设计」。不得写「太学门」「观经」「石经」「180 年」等确定性措辞，也不得引用讲堂十丈 / 三丈之类西晋尺寸（LY-002 X18）。
- **T5.3：** 交付文件不得引用观经空间三档 GLB 的 SHA（`0fcb76be…`、`5a0ff55f…`、`1b45de37…`），也不得放入任何把 A 与观经空间合在一个变换下的节点。和观经空间的衔接只留一个面向 LY-078 的冻结端口 ID。
- **T5.4：** 院外端口的 x 必须等于 LY-006 冻结值。中线 x = 0 与中入口 x = 1.5 都是 C，报告里写明选了哪个、为什么。准备期两种都用 fixture 验过可以通过。

## 6. 检查器自检（每次改检查器都要重跑；准备期结果在 `qa/selftest/`）

| 用例 | 期望 | 准备期结果 |
|---|---|---|
| `--patch none` | FAIL：阶前 264/264 × 3 失败，路线 462 / 99 / 372 失败 | FAIL ✔ |
| `synthetic:ok`（LOD0 / LOD1 / LOD2 / flat） | PASS | 4 × PASS ✔ |
| `synthetic:raised`（顶面 +5 cm） | FAIL：踢面 0.15，路线侵入 4 / 2 / 3，实体内 9 | FAIL ✔ |
| `synthetic:gap`（x 3…9 缺地） | FAIL：只有东入口路线失败（180/372） | FAIL ✔ |
| `synthetic:intrude`（凸块进西入口第一级） | FAIL：实体内 10 | FAIL ✔ |
| B 顶替 A | FAIL | FAIL ✔ |
| v1 `A_presentation_ground` 复用探针 | PASS（只证明几何可行，不等于可交付） | PASS ✔ |
| 端口放在长堂中线 x = 0 | PASS | PASS ✔ |

## 7. 交付层检查

- **T7.1：** 每个 GLB 不超过 15,000,000 字节。地块本身很小；A 的 LOD0（27,855,752 字节）不重新发布，只在 qa 里引用。
- **T7.2：** 新地块用米制，原点就是 A 的局部原点，不另做变换。若分三档，不得把一档复制改名当另外两档；若是与档位无关的单一件，要明示「三档共用」。UV 和法线要齐全，退化三角为 0，材质语义写成「earth / ground C」。
- **T7.3：** 至少做一次严格安装和撤回：§1.3 与 §4.3 同时通过。
- **T7.4：** 在隔离副本上运行官方 `lab/tools/build_assets.py --check`，交给 LY-100 / 协调者执行。本席位不在 lab 仓库里运行。
- **T7.5：** 预览用同一机位出前后对比、反面和入口剖面，图注写明是 CPU 渲染；没有在 GPU 或手机上测过，就不写「已测」。
