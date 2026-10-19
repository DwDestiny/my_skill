---
name: design-pipeline
description: 设计流水线入口。四个阶段把一句委托做成设计过的页面：内容蓝图、视觉氛围、组件创意、design.md。核心是创意与案例库，不是代码门禁。触发词：设计页面、做一个 HTML、小程序原型、App 原型、发布页、讲解页、高级效果、炫一点、视觉氛围、配色风格、组件创意、3D、流体、视频背景、像模板、太 AI 味。不适用：原生 macOS / iOS / Android 代码、仪表盘与后台表单、纯文字文档、写沟通话术。
---

# 设计流水线

本文件是入口，只做三件事：读原话、定阶段、路由。每个阶段一个文件在 `stages/`，案例在 `library/cases.json`，唯一产物模板是 `templates/design.md`。

> **注意**：用户原话优先于本文件和所有引用文件的任何规则。原话与规则冲突时，按原话做，在 design.md 第 0 节写明分歧。

## 1. 四个阶段

| 阶段 | 回答的问题 | 产物 | 读 |
|---|---|---|---|
| 1 内容蓝图 | 给谁看、讲什么、分几章、哪些章是舞台 | `01-内容规划/blueprint.md`、design.md 第 0 节 | `stages/1-blueprint.md`，`content-blueprint` skill |
| 2 视觉氛围 | 配色、边角、透明度、材质、光、空间、图像、动效气质、页面形态、签名时刻 | design.md 第 1 节 | `stages/2-atmosphere.md`，`references/taste-method.md`，`references/restraint.md` |
| 3 组件创意 | 每一屏用市面上最好的哪种表达，怎么改成本页的 | design.md 第 2 节 | `stages/3-components.md`，`library/cases.md`，`references/technique-catalog.md` |
| 4 design.md | 令牌、动效规则、载体数值、实现建议，入口文件加交付包，让空上下文的实现者不需追问就能做 | design.md 第 3 节 | `stages/4-design-md.md`，`references/craft.md` |

实现按 design.md 做，用开源组件库或自研都可以。做完看真实截图，对照 design.md 第 3.5 节看图清单，交给评审者（见第 3 节第 7 条）。收口后补库。

已有蓝图的项目从阶段 2 开始。已有 design.md 第 1 节的从阶段 3 开始。

## 2. 术语表

| 术语 | 含义 |
|---|---|
| 氛围 | 阶段 2 的全部表面决定。氛围决定收放，没有分级 |
| 动效气质 | 静、呼吸、驱动、沉浸四种，用"什么在动、何时动、占屏多少"定义，见 `references/restraint.md` |
| 页面形态 | 章节在空间里怎样排、读者怎样推进。先选形态，再排章节 |
| 纯瀑布流 | 章节纵向等宽堆叠、滚动只做位移、无舞台无空间结构。不做 |
| 签名时刻 | 全页唯一允许"响"的画面或交互 |
| 案例 | `library/cases.json` 一条：某个组件为某个目的的最佳表达，写出处、为什么好、适合什么氛围、怎么改 |
| 发牌 | `toolbox/deal.mjs` 按槽与目的发 3 条候选，选 1 条或库外自拟 |
| design.md | 交给实现的入口文件，三节：氛围、每屏做法、执行规则。第 0 节“交付包清单”列出蓝图、证据索引、术语表、资产的路径 |

## 3. 最少约束

1. 原话优先于一切规则。
2. 点子先于库。发牌不翻库。使用史跨项目。每条选中案例写"本页怎么改"。
3. 先选页面形态再排章节。
4. 签名时刻全页 1 处。首屏 3 秒内可读。动效回答一个动作或一个状态变化。舞台章占比、相邻屏版式、重复次数、填充率、空白高度是带适用条件的默认值，偏离时在 design.md 写理由（`references/restraint.md` 第 7 节）。
5. 正文对比 ≥4.5:1。Reduce Motion 有退路。390 宽无横向溢出。
6. design.md 第 2 节一屏一行，没有空行。
7. 看真实截图对照看图清单。评审者首选第二个独立 agent 看截图，有 Fable 且用户要求时才用 Fable。design.md 记录实际评审者与未覆盖项。
8. 炫技是默认。3D、GLSL 流体、滚动相机、WebGL、glTF 与 Blender 是常规选项，不因"风险"降级。收放看 `references/restraint.md`。

## 4. 路由表

| 情况 | 读 |
|---|---|
| 任何阶段开始前 | `frontend-design` skill。先探测当前宿主有没有它：用 Skill 工具加载，或在宿主的插件目录找（Claude Code 的插件缓存 `~/.claude/plugins/cache/*/frontend-design/*/skills/frontend-design/SKILL.md` 是其中一处，取最新版本）。找不到就读 `references/anti-sameness.md`，并在 design.md 记“未读 frontend-design” |
| 载体数值与平替 | `library/carriers.json`、`references/carriers.md`。壳尺寸 = 视口尺寸，不画设备外框 |
| 页面形态与幕表 | `library/page-forms.json`，`toolbox/pick-form.mjs` |
| 氛围选项 | `library/expressions.json` 表现形式、`library/palettes.json` 配色类、`library/directions.json` 整页案例 |
| 组件案例 | `library/cases.md` 索引，`toolbox/deal.mjs --slot <槽> --purpose "<目的>" --carrier <id>` |
| 避免同质化 | `references/anti-sameness.md` |
| 3D、WebGPU、流体、滚动相机、glTF 与 Blender | `examples/mechanisms/<id>/`，`references/blender-pipeline.md` |
| 起手复制与工艺 | `examples/finished/<id>/`（先读 README"不可照抄的部分"），`references/craft.md` |
| 营销页、发布页，或用户说"像模板""AI 味" | `design-taste-frontend` 的 `references/tells.md`、`critique.md` |
| 生成图像、纹理、插画 | `image-gen` skill，`references/asset-generation.md` |
| 图表、等轴测图 | `dataviz` skill，`anatomy` skill |
| 可选工具 | `toolbox/`：截图清单、默认值检查、收放检查、使用史 |

## 5. 权限与红线

已授权，不必逐次问：用 `image-gen` 生成设计资产（每个资产写进 `ASSETS.md`）。固定版本的 CDN 脚本与 Google Fonts。用 `agent-browser` 打开参照网站看行为（用户 2026-10-17 批准），只记录看到的行为，不截图存档、不下载素材、不存代码。

> **警告**：下列动作先停下来问用户。原因：它们把内容交给第三方，或让别人看到。

1. 从任何网站取图或下载素材。
2. 发布到公开画廊。发布 Artifact。

其他红线：不自己另开对模型厂商的请求。不把项目源码、隐私、示例环境路径写进生图提示词。不复制 Anthropic / Claude 的品牌色、字体、logo。Defaults 反默认清单 X1 到 X20 见 `references/anti-sameness.md`。

## 6. 补库与验证

每个项目收口后补 1 到 2 条案例，规则见 `stages/3-components.md`。验证只用真实项目：做用户要的页面，拿用户反馈，每次只改一处。不再跑评测任务、盲评和多轮评审（2026-10-18 用户决定，旧评测记录在归档 作者的私有归档（不在本仓库））。
