---
name: design-pipeline
description: 设计流水线入口。新页面走四个阶段：内容蓝图、视觉氛围、组件创意、design.md；已有产品按一页设计源统一改版走改版路线。核心是方法与案例库，不是代码门禁。触发词：设计页面、做一个 HTML、小程序原型、App 原型、发布页、讲解页、高级效果、炫一点、视觉氛围、配色风格、组件创意、3D、流体、视频背景、像模板、太 AI 味、按首页风格统一、全站视觉升级、页面改版、卡片太丑、信息没主次。不适用：原生 macOS / iOS / Android 代码、仪表盘与后台表单、纯文字文档、写沟通话术。
---

# 设计流水线

本文件只做三件事：读原话、定路线和阶段、告诉你下一步读哪一个文件。一个阶段只读它自己的阶段文件，阶段文件再告诉你做到哪一步读哪一节。库不整读，用 `toolbox/lib.mjs` 查。

> **注意**：用户原话优先于本文件和所有引用文件的任何规则。原话与规则冲突时，按原话做，在 design.md 第 0 节写明分歧。

## 1. 路线与阶段

| 路线 | 什么时候 | 读 |
|---|---|---|
| 像素优先最小路径（实验中） | 新页面默认。候选从 `library/case-map.md` 出，独立评审选，agent 换题复现，用户只打档 | `stages/minimal-path.md` |
| 新页面 | 用户要完整流程、点名手法，或没人能选图 | 下表四个阶段，按序 |
| 改版 | 已有产品要按一页确认过的设计统一，功能不变 | `stages/redesign.md` |

| 阶段 | 回答的问题 | 产物 | 只读这一个文件 |
|---|---|---|---|
| 1 内容蓝图 | 给谁看、讲什么、分几章、哪些章是舞台 | `01-内容规划/blueprint.md`、design.md 第 0 节 | `stages/1-blueprint.md` |
| 2 视觉氛围 | 身份、主题打分、方向板与获奖锚点盲比、配色、材质、动效气质、页面形态、签名时刻 | design.md 第 1 节 | `stages/2-atmosphere.md` |
| 3 组件创意 | 每一屏用市面上最好的哪种表达，怎么改成本页的 | design.md 第 2 节 | `stages/3-components.md` |
| 4 design.md 与实现 | 令牌、动效规则、载体数值、实现建议；实现后看图与整页循环 | design.md 第 3 节、页面 | `stages/4-design-md.md` |

已有蓝图的项目从阶段 2 开始。已有 design.md 第 1 节的从阶段 3 开始。唯一产物模板：`templates/design.md`。

## 2. 读法

1. 一个阶段只打开它的阶段文件。阶段文件写"做到某步读某节"时再读那一节，不提前整读参考文件。
2. 库（`library/*.json`，最大 95 KB）不整读。`node toolbox/lib.mjs` 列库；`lib.mjs <库>` 看简表（每条一行）；`lib.mjs <库> <id>` 看一条全文；`--where k=v` 过滤。
3. 同一个任务里，每个获奖锚点只现场打开一次，截图留在项目临时目录复用（`references/judging.md` 第 3 节）。
4. 选方向、选候选默认由评审做，用户主动要求时才给用户选。真正只有用户能答的事（资料缺口、业务口径），写进 `process/ASK.md` 然后停（`references/iteration-loop.md` 第 3 节）。

## 3. 贯穿四条

1. 原话优先于一切规则。原话点名的手法必须出现在决定里，做不到时写理由。
2. 炫技是默认。3D、GLSL 流体、滚动相机、WebGL、glTF 与 Blender 是常规选项，不因"风险"降级。放在哪里、放多大看 `references/restraint.md`。
3. 好坏由并排看图决定。尺子是获奖级作品（`references/judging.md`），不是规则清单。技术检查只说明能用。
4. 签名时刻全页 1 处。首屏 3 秒内可读。正文对比 ≥4.5:1，Reduce Motion 有退路，390 宽无横向溢出。其余数值是带适用条件的默认值，偏离时在 design.md 写理由（`references/restraint.md` 第 7 节）。

## 4. 按需读

做到那一步再读，不预读。

| 情况 | 读 |
|---|---|
| 设计原则（阶段 1 或 2 开始前读一次） | `frontend-design` skill：用 Skill 工具加载，或找宿主插件目录（Claude Code 是 `~/.claude/plugins/cache/*/frontend-design/*/skills/frontend-design/SKILL.md`，取最新版）。找不到就读 `references/anti-sameness.md`，并在 design.md 记"未读 frontend-design" |
| 载体数值与平替 | `node toolbox/lib.mjs carriers <id>`，`references/carriers.md`。壳尺寸 = 视口尺寸，不画设备外框 |
| 选方向、找最接近的获奖案例、怎么改成本题材、避免雷同 | `library/case-map.md`（先读这个，再查主题与锚点） |
| 整体主题（视频、摄影、3D、流体、大字、交互玩具等）、主题打分 | `node toolbox/lib.mjs themes`，`stages/2-atmosphere.md` 2.1.3 |
| 分清身份与例子、题材研究、发散方向 | `references/direction-and-appeal.md` |
| 判断好坏、和获奖作品比、深化还是换方向 | `references/judging.md`，`node toolbox/lib.mjs anchors --where page_type=<页型>` |
| 迭代几轮、什么时候停、越改越差 | `references/iteration-loop.md` |
| 氛围、冲击力、"炫酷"、配色太灰太平 | `references/atmosphere-and-impact.md` |
| 品味、高级感、优雅、遮名检查 | `references/taste-method.md`（按节读，文件头写了哪步读哪节） |
| 收放、动效气质、浮夸判定 | `references/restraint.md` |
| 页面形态与幕表 | `node toolbox/pick-form.mjs`，`node toolbox/lib.mjs forms` |
| 表现形式、配色类、同页型标杆 | `node toolbox/lib.mjs expressions`、`lib.mjs palettes`、`lib.mjs references` |
| 组件案例 | `node toolbox/deal.mjs --slot <槽> --purpose "<目的>" --carrier <id>` |
| 组件好坏判据、16 槽分界、动效令牌、示意图质感 | `references/why-good.md` |
| 手法目录与技术栈 | `references/technique-catalog.md` |
| 避免同质化、反默认清单 X1 到 X20 | `references/anti-sameness.md` |
| 3D、WebGPU、流体、滚动相机、glTF 与 Blender | `examples/mechanisms/<id>/`，`references/blender-pipeline.md` |
| 起手复制、工艺、截图与检查脚本 | `examples/finished/mixed-01/`（先读 README"不可照抄的部分"），`references/craft.md` |
| 营销页、发布页，或用户说"像模板""AI 味" | `design-taste-frontend` 的 `references/tells.md`、`critique.md` |
| 生成图像、纹理、插画；logo、头像、图标要不要配图 | `image-gen` skill，`references/asset-generation.md` |
| 卡片层级、表面与底色、焦点与状态、页头、弹窗 | `references/product-ui.md` |
| 看截图、找最该改的地方 | `references/critique-method.md` |
| 图表、等轴测图 | `dataviz` skill，`anatomy` skill |

## 5. 术语

| 术语 | 含义 |
|---|---|
| 氛围 | 阶段 2 的全部表面决定。氛围决定收放，没有分级 |
| 动效气质 | 静、呼吸、驱动、沉浸四种，用"什么在动、何时动、占屏多少"定义（`references/restraint.md` 第 3 节） |
| 页面形态 | 章节在空间里怎样排、读者怎样推进。先选形态，再排章节。纯瀑布流（章节等宽堆叠、滚动只做位移）不做 |
| 签名时刻 | 全页最响的一处画面或交互。只限高潮，其他章不必安静 |
| 案例与发牌 | `library/cases.json` 一条是某个组件为某个目的的最佳表达；`deal.mjs` 按槽与目的发 3 条，选 1 条或库外自拟 |
| design.md | 交给实现的入口文件，三节：氛围、每屏做法、执行规则。第 0 节"交付包清单"列出蓝图、证据索引、术语表、资产的路径 |

## 6. 权限与红线

已授权，不必逐次问：用 `image-gen` 生成设计资产（每个资产写进 `ASSETS.md`）。固定版本的 CDN 脚本与 Google Fonts。用 `agent-browser` 打开参照网站看行为（用户 2026-10-17 批准），只记录看到的行为，不下载素材、不存代码；锚点截图只留在项目临时目录，不入库。

> **警告**：下列动作先停下来问用户。原因：它们把内容交给第三方，或让别人看到。

1. 从任何网站取图或下载素材入库。
2. 发布到公开画廊。发布 Artifact。

其他红线：不自己另开对模型厂商的请求。不把项目源码、隐私、示例环境路径写进生图提示词。不复制 Anthropic / Claude 的品牌色、字体、logo。

## 7. 补库与验证

每个项目收口后补 1 到 2 条案例（`stages/3-components.md` 第 6 节），并用 `deal.mjs --record` 写使用史。验证只用真实项目：做用户要的页面，拿用户反馈，每次只改一处（2026-10-18 用户决定）。
