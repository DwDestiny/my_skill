# design-pipeline · 设计流水线

把一句委托做成一张设计过的页面。四个阶段：内容蓝图、视觉氛围、组件创意、design.md。核心是创意与案例库，实现用开源组件库或自研。入口 `SKILL.md`。

读法是渐进式的（2026-10-21）：入口只路由；一个阶段只读它的阶段文件；阶段文件写明做到哪一步读参考文件的哪一节；库文件不整读，用 `toolbox/lib.mjs` 查简表或单条。

状态（2026-10-18）：用户判定此前流程过度工程化，已瘦身。成品范例保留三个：`mixed-01` 是正向参考，`show-01` 与 `clear-01` 是待改案例。案例库 `library/cases.json`（148 条）。评测记录、调研底稿与 `PLAN.md` 已移出仓库，归档在 `作者的私有归档（不在本仓库）`。后续只按真实项目的用户反馈优化，每次改一处。

## 1. 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 入口：路线与四阶段、读法、贯穿四条、按需读表、术语、红线 |
| `stages/1-blueprint.md` | 阶段 1：接单槽位表，蓝图交 `content-blueprint` skill |
| `stages/2-atmosphere.md` | 阶段 2：主题盘点、点子、页面形态与幕表、材质光空间图像、配色、边角、透明度、动效气质、签名时刻、禁用清单 |
| `stages/3-components.md` | 阶段 3：每屏按槽与目的发牌、本页怎么改、补库规则、案例字段 |
| `stages/4-design-md.md` | 阶段 4：design.md 第 3 节执行规则、自查、实现与看图 |
| `templates/design.md` | 唯一产物模板，三节：氛围、每屏做法、执行规则 |
| `library/case-map.md` | 设计案例地图：高分锚点与身份类参照按"世界"分 8 簇，每条一句装置、一句换题；附换题公式与不雷同三问。选方向先读它（约 11 KB），不整读锚点与主题 |
| `library/cases.json`、`cases.md` | 组件创意案例库。`cases.md` 是索引 |
| `library/` 其他 | `themes.json` 25 个整体主题与获奖案例、`anchors.json` 35 个获奖级与自有锚点、`carriers.json` 9 种载体、`page-forms.json` 15 种页面形态、`expressions.json` 43 种表现形式、`palettes.json` 10 类配色、`references.json` 42 个参照站。`directions.json` 8 张整页方向卡自 2026-10-21 起不再发牌，只供 `deal.mjs --list` 兼容；`motions.json` 无文档引用，待定去留 |
| `references/taste-method.md` | 品味方法：好、氛围感、高级感、优雅、品味的定义，8 条通用做法，氛围 8 层，遮名检查。来源是 2026-10-19 的作品集调研，数值与原则都是起始值 |
| `references/technique-catalog.md` | 手法目录 50 条与技术栈地图，带证据等级。3D 展厅类无样本，不涉及 |
| `references/why-good.md` | 为什么好：高级感的可测部分（秩序感）、氛围感、组件四判据、16 槽好与平庸分界、动效令牌、示意图质感层、何时不要用 |
| `references/restraint.md` | 收放原则：四条禁区、三句话原则、四种动效气质 |
| `references/craft.md` | 工艺附录：起手复制、导出口、截图法、钩子（可选）、开源库 |
| `references/anti-sameness.md` | 反同质化八条与反默认清单 X1 到 X20 |
| `references/carriers.md`、`asset-generation.md`、`blender-pipeline.md` | 载体细则、生成资产、Blender 管线 |
| `examples/mechanisms/` | 21 个机制示例，单文件 HTML。说明在 `index.html` 头部注释，其中 9 个另带 `CARD.md` |
| `examples/finished/` | 3 个成品。`mixed-01`：用户认可整体感觉的正向参考。`show-01`、`clear-01`：待改案例（用户评价：效果很一般），只学单处机制。实现起手从 `mixed-01` 复制工艺层 |
| `toolbox/` | `lib.mjs` 查库（简表、单条、过滤，代替整读 JSON）、`record-motion.py` 录一个站怎么动怎么跟手（入场、滚动、指针三组帧加技术盘点，入库和借案例前跑）、`pick.py` 选图页（候选目录起一页，用户排名与备注写 pick.jsonl，配 cloudflared 临时隧道给用户链接）、`deal.mjs` 组件发牌与使用史（`--record` 记主题与形态）、`pick-form.mjs` 选形态、`shots.py` 截图清单、`flash-check.py` 按动效气质查收放、`defaults-check.py` 反默认、`cases-index.py` 库体检、`selftest.py` 自测（20 项） |
| `history/` | 使用史 `history.json`，运行时唯一会写进本目录的文件 |
| `samples/design.md` | 填好的 design.md 样例（由 E2 发布页的氛围与每屏做法合成） |
| （已归档） | `evals/`、`research/`、`PLAN.md` 于 2026-10-18 移出仓库，见 `作者的私有归档（不在本仓库）` |

## 2. 怎么用

| 场景 | 做法 |
|---|---|
| 新页面 | 触发 `design-pipeline` skill，把用户原话逐字给它。从阶段 1 开始 |
| 已有蓝图 | 从阶段 2 开始。先把原话与载体填进 design.md 第 0 节 |
| 已有 design.md 第 1 节 | 从阶段 3 开始 |
| 用户要求自己选候选时 | `python3 toolbox/pick.py --dir <候选目录> --title <标题>`，另开 `cloudflared tunnel --url http://127.0.0.1:8790 --no-autoupdate`，把隧道地址加口令给用户 |
| 查库 | `node toolbox/lib.mjs`（列库）、`lib.mjs themes`（简表）、`lib.mjs themes T03`（单条）、`lib.mjs anchors --where page_type=studio-home` |
| 发案例 | `node toolbox/deal.mjs --slot hero --purpose "让人第一眼看到产品实体" --carrier desktop-web` |
| 记使用史 | `node toolbox/deal.mjs --record --project <名> --carrier <id> --theme T03 --form P04` |
| 补库 | 项目收口后按 `stages/3-components.md` 第 6 节加 1 到 2 条 |
| 验证 | 真实项目加用户反馈。不跑评测、盲评、多轮评审 |

## 3. 不做的事

不分档位（文档、工具与库 2026-10-21 已全部清除）。不设代码门禁。不从空白令牌起手。不做纯瀑布流。不取网图、不发布，除非用户批准。参照网站可以打开看行为，不存档。
