# 007 · 原生浏览器局部验收

日期：2026-11-01 UTC。环境：云端 Chromium 与唯一 sites-preview；最终批准模型文件，主图 960²。以下是有限原生检查，不是整站无障碍或 GPU 合格证。

## 首版与真实候选历史

首版占位主图与行动入口同屏，根审查者也实际查看。真实候选接入后实见 grid 图片裁掉下部，修复明确图框 contain 后复看完整雕塑。v1 为占位首版、v2 为 640² 候选；两者都不替代以下最终检查。

## 最终桌面与键盘

原生截图为 1173×751；DOM窗口1188×761、文档 clientWidth=scrollWidth=1173。真实主图960²，图框 y89.39–509.39；图版控件 y553.39–597.39，主图和主要入口同屏。正文四章均在 main 地标内。

从整体斜视按钮按 Tab，焦点到正面图版且 focus-visible 为真。按 Space 后，解码等待时仍保留旧图身份；随后正面图960、alt、图注02、原图href与 aria-pressed 一起更新。不是只检查视觉换图。

正侧投影比较实际看见：左为围合内空，右被实体投影遮挡。最终主模型正面约432cm²，明确为二维栅格估算，不是实体通道。截图 projection-comparison.jpg。

## 受控窄 CSS 视口

同一实际最终页面置于 CSS iframe；320 / 390 / 768 / 1280 / 1600 / 1920px 框分别读到 clientWidth 与 scrollWidth 都为305 / 375 / 753 / 1265 / 1585 / 1905，没有横向溢出。15px差为滚动条；每档三图按钮均72×44px，主图 naturalWidth=960。

mobile-320.jpg 是320×680 CSS iframe的原生截图，非真机截图。完整雕塑、主要入口与图版按钮均可见；正文纵向顺序阅读，不劫持滚轮。

## 无 JavaScript

受控390×360 iframe仅 sandbox="allow-same-origin"，不含allow-scripts。enhanced=false；图版切换按钮隐藏；noscript说明出现；三张静态图的naturalWidth均960，正文与档案仍存在。原生summary以Enter展开，details.open=true，clientWidth=scrollWidth=375。nojs.jpg显示展开说明与键盘焦点。该证据仅限这种实际禁脚本环境，不代表屏幕阅读器完整验收。

## 真实缺图、重试与恢复

临时测试副本只加入相对base，并将侧面按钮data-src改为实际不存在的本地资源；其余正文和实际app.js/gallery-state.js不变，逐字比较确认。原生直接打开该资源显示“Cannot GET”；未单独采集数值HTTP状态。不是模拟Promise拒绝或修改浏览器安全设置。

Enter选择缺失侧图后，状态明确失败并保留成功的beauty960；图、alt、图注01、原图href与pressed=beauty一致。Enter重试仍失败，身份不变。Enter选有效正面后全部更新为front960，重试消失。image-failure.jpg与image-recovery.jpg记录最终失败和恢复，不把等待截图误作失败。

另一副本仅把初始beauty src/data-src指向不存在资源：naturalWidth=0、主图隐藏、无任何pressed成功，说明“尚无可加载主图”。Space选择有效front后恢复960与匹配图注/原图href。正文和投影不依赖主图成功。测试副本已从发布目录移除。

## 独立观察器往返

从主网页真实链接进入观察室，按Enter载入真实3D，原生状态明确“当前环境没有可用的WebGL上下文”。Orison beauty960与对应GLB下载保留；网格、旋转、复位禁用；返回主网页标题正确。viewer-fallback.jpg记录的是失败后的诚实离线图，不是GPU截图。

根审查者另在独立原生tab确认Latitude/front载入失败时保持同variant图片与GLB；主动离线再选Ascend保持离线，浏览器Back恢复Latitude/front，回主网页正确。根另复核桌面、320 CSS和noJS；未重跑本页缺图实验。观察器更全面的模型作者证据保留在原review路径，不将其扩大成网页作者亲测。

## 证据与未验

browser-checks.json记录最终页面、脚本、图版、投影的SHA，freeze.py在冻结前核对一致；实际DOM读数不等于所有环境的保证。单元测试另列13项纯状态、5项实际app异步模拟、31项投影子集、16项导入隔离回归。

GPU实际绘制、真实iPhone/Android、200%浏览器缩放、完整屏幕阅读器播报、物理自立、材料与制造性能均未验证。GLB CPU读数与静态色对计算不替代这些项目。
