# 造物之匣 · 提交规范 v1

资产库里的每一件数字资产（项目、模型、网页、空间，以及以后新增的分类）都用一张**卡片** `<id>.asset.json` 来描述。卡片写对、推送，网站就会自动收录；卡片写错，检查会拦下来，并逐条说明哪里不对。

网页版（规则、分类和检查报告都是实时的）：本地 `http://localhost:8780/lab/spec.html`，线上在 https://suxing412.github.io/creation-notebook/spec.html 。

## 1. 放在哪里

每件新资产单独一个文件夹，路径是 `docs/library/<分类>/<id>/`：

```
docs/library/models/m-bronze-lamp/
  m-bronze-lamp.asset.json    卡片，文件名必须是 <id>.asset.json
  cover.webp                  封面
  shots/front.webp ...        图集
  files/lamp-LOD0.glb ...     模型
  index.html                  网页设计的作品网页本身
```

- 卡片里的路径一律写成**相对卡片本身**的路径，不能跑出 `docs/`。
- 已有的旧资产不用搬。它们的卡片放在原来的目录，并写了 `"legacyPath": true`。
- id 只用小写字母、数字和连字符。建议加前缀：项目 `p-`、模型 `m-`、网页 `w-`、空间 `s-`。
- 同一件作品的模型和网页用相同的后缀，例如 `m-bronze-lamp` 和 `w-bronze-lamp`，再在 `related` 里互相写上对方的 id。

## 2. 卡片字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `spec` | 是 | 固定写 `1` |
| `id` | 是 | 全库唯一，必须和文件名一致 |
| `category` | 是 | 分类 id，可选值见 `categories.json` |
| `kind` | 是 | 分类下的类型。要用新类型，先把它加进 `categories.json` |
| `title` | 是 | 中文名，不超过 24 字 |
| `english` | 否 | 英文名，用大写 |
| `summary` | 是 | 一句话介绍，不超过 120 字，建议 80 字以内 |
| `status` | 是 | `草稿` / `建设中` / `待审` / `已发布` / `归档`。草稿不会出现在网页上 |
| `statusNote` | 否 | 状态的补充说明，一句话 |
| `cover` | 是 | 封面图，png、jpg 或 webp，宽度至少 600px，建议 1200px 以上 |
| `coverAlt` | 否 | 用文字描述封面画面 |
| `coverIsShot` | 否 | 封面是网页截图时写 `true` |
| `gallery` | 否 | 图集，最多 12 张，最重要的放第一张 |
| `files` | 模型必填 | 写成 `[{"path": "...glb", "label": "LOD0"}]`；也可以写 `"auto"`，表示收录本目录下所有 GLB |
| `page` | 网页必填 | 作品网页本身，在详情页的「实况」里直接浏览 |
| `notes` | 否 | 制作记录，建议至少写「已完成的检查」和「限制与待解决」两条 |
| `stats` | 否 | 需要在属性表里额外显示的数字 |
| `related` | 否 | 关联资产的 id |

面数、体积、贴图数、包围盒和更新时间都由构建自动读出，**不要手写**。

详情页就是最终查看页：有 GLB 的资产默认打开实时 3D，加载失败才退回预览图；网页设计在「实况」里直接浏览。卡片里不写外链按钮（旧的 `links` 字段已停用）。空白卡片模板见 `template.json`。

## 3. 质量下限

**错误**会让这张卡片不上网页，推送前的检查也会失败：

- JSON 不合法；
- 缺必填字段，或文件名和 id 对不上，或 id 重复；
- category、status 的取值不在表里；
- title 或 summary 超长；
- 任何路径找不到，或者跑出了 `docs/`；
- 封面宽度小于 600px；
- 模型分类没有 GLB，或 GLB 读不出来；
- 单个 GLB 超过 15 MB，或面数超过 50 万；
- 网页设计没有 page。

- `docs/` 里出现新的源文件（`.blend`、源码 ZIP 及分卷、`.psd`、`.exr`、`.fbx` 等，见第 7 节）。

**提醒**照常上网页，但会列在检查报告里，评审时会看：

- 缺英文名或封面描述；
- notes 缺上面那两条；
- 没有图集；
- 封面窄于 1200px；
- GLB 大于 5 MB，或面数高于 15 万；
- kind 不在分类表里，或 related 指向不存在的 id；
- 新资产没有放在标准目录；
- 标准目录里有 GLB，但没有任何卡片引用它；
- 展示图是大于 1 MB 的 PNG 或 JPG（建议转 WebP）；
- GLB 大于 1 MB 却没有用 meshopt 压缩（建议 `gltfpack -cc`）。

门槛的具体数字都在 `categories.json` 的 `limits` 里，网站和检查脚本都从这里读取。

## 4. 提交流程

1. 在 `docs/library/<分类>/<id>/` 里放好文件，从 `template.json` 复制一份写成卡片。源文件不放进来，留到第 5 步。
2. 运行检查：`python -I lab/tools/build_assets.py --check`。有错误时会逐条列出，并以非零状态退出。
3. 检查通过后提交。提交说明写清楚是哪件资产，例如 `Add m-bronze-lamp: bronze lamp LOD0/LOD1`。
4. 推送到 main。部署接好之后，每次推送都会自动重跑检查并发布；检查不通过时，网站保持上一版。
5. 一批工作完成后，照旧打 `rYYYY.MM.DD-N` tag，把这一批的源文件上传到同名 GitHub Release（见第 7 节）。Claude 按版本评审。

## 5. 加分类

在 `categories.json` 的 `categories` 里加一项，写明 `id`、`zh`、`en`、`desc`、`kinds` 和 `requires`。可选 `sort` 定这个分类页的默认顺序：`updated` 是最近更新的在前（3D 模型用的就是这个），不写就按卡片顺序。网站会自动多出一个页签；总览的小城里，这个新分类会先显示为一块「待建」地，等对应的建筑做好后再换上。

## 6. 大型项目

大型项目（`category: "projects"`）的详情页包括这几部分：首屏的实时场景、章节、建设进度、研究手记和组成资产。这些内容都写在项目卡片里，参考样例是 `docs/cities/luoyang/p-luoyang.asset.json`。

| 字段 | 必填 | 说明 |
|---|---|---|
| `scene` | 是 | 实时场景模块（`.mjs`），接口见下方「场景约定」 |
| `chapters` | 是 | 章节列表，最多 12 章。每章写 `id`、`title`、`status`、`line`（一句话）、`image`，可选 `statusNote`、`text`（正文）、`focus`（点「在城中看」时飞去的位置，不写就用 `id`） |
| `progress` | 建议 | 建设进度列表。每项写 `title`、`status`，可选 `count`、`unit`、`chapter`（所属章节 id）、`focus`、`note` |
| `evidence` | 建议 | 史料等级说明，每项写 `level`（`有据` / `推测` / `未知`）和 `text` |
| `journal` | 建议 | 建设记录，每条写 `date`（YYYY-MM-DD）、`title`，可选 `batch`（版本 tag）、`text`。页面按日期倒序显示 |
| `members` | 否 | 组成这个项目的资产 id，显示为卡片 |

章节和进度的 `status` 只能取 `已入城`、`已建模`、`研究中`、`待建` 中的一个，定义在 `categories.json` 的 `project` 里。

**每交付一批，项目卡片要同步更新：**

- 新做出的模型在 `progress` 里加一项，或把对应项的数量和状态改掉。只完成建模的写「已建模」，已经放进城里的写「已入城」。
- 在 `journal` 最前面加一条建设记录，写上日期和这一批的 tag。
- 如果这批东西也单独做成了资产（有自己的卡片），把它的 id 加进 `members`。

**场景约定**：`scene` 指向的模块要导出 `mountScene(canvas, { signal, onSelect, onStatus })`，返回一个对象：

- `focus(target)`：`target` 可以是章节的 `focus` 值、`"city"`（全城），或 `"research:<模型 id>"`（单独查看一件研究模型）；
- `reset()`：回到初始视角；
- `setEvidence(on)`：开关史料等级显示；
- `dispose()`：释放资源。

用户点选建筑时，模块调用 `onSelect({ title, summary, status, tier, basis })`，页面会弹出这处建筑的便签。场景打不开时，页面退回显示封面海报。洛阳的实现见 `docs/cities/luoyang/scene.mjs`。

## 7. 源文件与体积

网站只放给人看的东西：展示图、GLB 和网页。GitHub Pages 整站上限 1 GB，部署时一旦超过上限就会失败，线上停在上一版。

- **源文件不提交进仓库。** `.blend`、源码 ZIP 及其分卷、`.psd`、`.exr`、`.fbx` 这类文件，改为上传到这一批 tag 的 GitHub Release：
  ```
  gh release create rYYYY.MM.DD-N --title "rYYYY.MM.DD-N" --notes "这一批的源文件" model.blend source.zip
  gh release upload rYYYY.MM.DD-N another.blend    # 这个 tag 已经有 Release 时，用这一条追加
  ```
  在 `docs/` 里提交新的源文件，检查会报错。
- **旧源文件已经归档。** 仓库里原有的源文件都放进了 Release `sources-2026.11.05`，分卷也已还原成校验过的完整 ZIP。部署时这些文件不会发布，页面上的下载链接会自动改成 Release 的地址。对照表在 `source-archive.json`，由 `lab/tools/archive_sources.py` 生成。
- **展示图用 WebP。** PNG 和 JPG 超过 1 MB 时检查会提醒。
- **GLB 用 meshopt 压缩**，命令是 `gltfpack -i in.glb -o out.glb -cc`。资产库的查看器和洛阳城景都能读取压缩后的 GLB；超过 1 MB 且没有压缩的 GLB，检查会提醒。
