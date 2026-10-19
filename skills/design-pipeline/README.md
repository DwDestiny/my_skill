# design-pipeline · 设计流水线

把一句委托做成一张设计过的页面。四个阶段：内容蓝图、视觉氛围、组件创意、design.md。核心是创意与案例库，实现用开源组件库或自研。入口 `SKILL.md`。

状态（2026-10-18）：用户判定此前流程过度工程化，已瘦身。成品范例保留三个：`mixed-01` 是正向参考，`show-01` 与 `clear-01` 是待改案例。案例库 `library/cases.json`（148 条）。评测记录、调研底稿与 `PLAN.md` 已移出仓库，归档在 作者的私有归档（不在本仓库）。后续只按真实项目的用户反馈优化，每次改一处。

## 1. 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 入口：四阶段、术语、最少约束 8 条、路由表、红线 |
| `stages/1-blueprint.md` | 阶段 1：接单槽位表，蓝图交 `content-blueprint` skill |
| `stages/2-atmosphere.md` | 阶段 2：主题盘点、点子、页面形态与幕表、材质光空间图像、配色、边角、透明度、动效气质、签名时刻、禁用清单 |
| `stages/3-components.md` | 阶段 3：每屏按槽与目的发牌、本页怎么改、补库规则、案例字段 |
| `stages/4-design-md.md` | 阶段 4：design.md 第 3 节执行规则、自查、实现与看图 |
| `templates/design.md` | 唯一产物模板，三节：氛围、每屏做法、执行规则 |
| `library/cases.json`、`cases.md` | 组件创意案例库。`cases.md` 是索引 |
| `library/` 其他 | `carriers.json` 9 种载体、`page-forms.json` 15 种页面形态、`expressions.json` 表现形式、`palettes.json` 配色类、`directions.json` 整页方向、`references.json`、`motions.json` |
| `references/taste-method.md` | 品味方法：好、氛围感、高级感、优雅、品味的定义，8 条通用做法，氛围 8 层，遮名检查。来源是 2026-10-19 的作品集调研，数值与原则都是起始值 |
| `references/technique-catalog.md` | 手法目录 50 条与技术栈地图，带证据等级。3D 展厅类无样本，不涉及 |
| `references/why-good.md` | 为什么好：高级感的可测部分（秩序感）、氛围感、组件四判据、16 槽好与平庸分界、动效令牌、示意图质感层、何时不要用 |
| `references/restraint.md` | 收放原则：四条禁区、三句话原则、四种动效气质 |
| `references/craft.md` | 工艺附录：起手复制、导出口、截图法、钩子（可选）、开源库 |
| `references/anti-sameness.md` | 反同质化八条与反默认清单 X1 到 X20 |
| `references/carriers.md`、`asset-generation.md`、`blender-pipeline.md` | 载体细则、生成资产、Blender 管线 |
| `examples/mechanisms/` | 21 个机制示例，单文件 HTML。说明在 `index.html` 头部注释，其中 9 个另带 `CARD.md` |
| `examples/finished/` | 3 个成品。`mixed-01`：用户认可整体感觉的正向参考。`show-01`、`clear-01`：待改案例（用户评价：效果很一般），只学单处机制。实现起手从 `mixed-01` 复制工艺层 |
| `toolbox/` | 可选工具：`deal.mjs` 发牌与使用史、`pick-form.mjs` 选形态、`shots.py` 截图清单、`selftest.py` 自测、`defaults-check.py` 反默认、`flash-check.py` 收放 |
| `history/` | 使用史 `history.json`，运行时唯一会写进本目录的文件 |
| `samples/design.md` | 填好的 design.md 样例（由 E2 发布页的氛围与每屏做法合成） |
| （已归档） | `evals/`、`research/`、`PLAN.md` 于 2026-10-18 移出仓库，见 作者的私有归档（不在本仓库） |

## 2. 怎么用

| 场景 | 做法 |
|---|---|
| 新页面 | 触发 `design-pipeline` skill，把用户原话逐字给它。从阶段 1 开始 |
| 已有蓝图 | 从阶段 2 开始。先把原话与载体填进 design.md 第 0 节 |
| 已有 design.md 第 1 节 | 从阶段 3 开始 |
| 发案例 | `node toolbox/deal.mjs --slot hero --purpose "让人第一眼看到产品实体" --carrier desktop-web` |
| 补库 | 项目收口后按 `stages/3-components.md` 第 6 节加 1 到 2 条 |
| 验证 | 真实项目加用户反馈。不跑评测、盲评、多轮评审 |

## 3. 不做的事

不分档位。不设代码门禁。不从空白令牌起手。不做纯瀑布流。不取网图、不发布，除非用户批准。参照网站可以打开看行为，不存档。
