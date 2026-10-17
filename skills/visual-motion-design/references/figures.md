# 图、图表与 3D：路由与预算

"要不要画"由 `content-blueprint` 在 `blueprint.md` 的 `form` 字段决定。本文管"怎么画"。

## 1. 路由

| 蓝图里的 form | 用什么 | 加载方式 | 何时不用 |
|---|---|---|---|
| `table` | HTML 表格 | 本文第 4 节 | 超过约 7 类且每类有含义时，也用表格，不画多色图 |
| `metric` 指标磁贴 / KPI 行 | `dataviz` | Skill 工具加载 | 单个数字不画图 |
| `chart` 数据图（条、线、堆叠、热力） | `dataviz` | Skill 工具加载；运行 `validate_palette.js` 浅深两次 | 数据不足 3 个点 |
| `diagram` 机制图（流程、路径、边界、差异） | `artifact-diagramming` 的内联 SVG 法 | Skill 工具加载 | 一句话说得更快 |
| `diagram` 需要成套风格的图（泳道、时间线、分层、象限、服务蓝图、飞轮） | `diagram-design` | 读其 `SKILL.md` 与对应 `references/type-*.md` | 节点 >9 时拆成两张 |
| `figure3d` 等轴测交互图 | `anatomy` | 读其 `SKILL.md`、`references/craft.md`、`motion.md`、`verify.md` | 内容没有物理对应物 |
| `exploded` 分层或部件关系，不需交互 | `diagram-design` 的 Exploded axonometric 或 Layer stack | 同上 | 部件 >5 |

路由规则：

1. 一张图承担一个论点，标题写成一句结论。
2. 先声明再画：类型、画布尺寸、要删掉什么。
3. 两种类型都合适时，选主导的轴。
4. 图下方必须有同内容的文字摘要或表格孪生（折叠也可）。
5. 等轴测交互图成本最高（Figure 档 40 到 80 部件）。只有"读者要拨一下才懂"的机制才用。

## 2. 预算（对非专家读者再收紧）

| 项 | diagram-design 原值 | 本 skill 取值 |
|---|---|---|
| 单图节点 | ≤9 | 总览 ≤7，细节 ≤9 |
| 箭头 | ≤12 | ≤10 |
| 焦点元素（强调色） | ≤2 | ≤2 |
| 泳道 | ≤5 | ≤4 |
| 时间线节点 | ≤9 | ≤8 |
| 分层 | ≤6 | ≤6 |
| 图内中文标签 | 每标签 ≤12 字 | 同 |
| 一页同屏可见的图 | 未规定 | ≤2 |
| anatomy 部件 | Figure 40 到 80 | 40 到 60，读数 ≤12 字 |
| 图内最小字号 | 12px | 12px；中文标签不转大写、不加字距 |

超预算时退回 `content-blueprint`：写 `handoff-log.md` 条目，类型 `over_budget`，附实际数与上限。

## 3. 视觉语法（全部图共用）

1. 4px 网格：位置、尺寸、间距、内边距都能被 4 整除。
2. 形状与线型承载类型，颜色不单独承载。虚线表可选或异步。
3. 中性底加一个强调色。`currentColor` 跟随深浅色；只有承载含义的那一个元素用字面色相，且两种底色都可读。
4. 每条箭头有标签（写动作："写入""每 30 秒轮询"），标签 ≤14 字符，距线 6 到 10px，有不透明遮罩。
5. 连线正交，圆角肘 r=8。无斜线。
6. 无阴影，无浮动图例。图例放底部横条，且只在同一编码重复出现时才需要。
7. `<figure>` + `<figcaption>`，`<svg role="img" aria-label="同结论">`，`viewBox` + `max-width:100%; height:auto`。SVG 内不放 `<script>`、`<style>`、`<foreignObject>`。
8. 文字永不用系列色。文字用主 / 次文字令牌，旁边的色块表明身份。
9. 宽图在手机上：容器 `overflow-x: auto`，`svg{min-width: viewBox 宽}`，并有"可横向滑动"提示；或为手机另出竖向 `viewBox`。

## 4. 表格

1. 数字列 `tabular-nums` 右对齐；文字列左对齐。
2. 表头固定（`position: sticky; top`）；行高一致；斑马纹用面板明度差，不用线。
3. 宽表放进 `.scroll-x` 容器；手机下可切换为"每行一卡"的堆叠视图。
4. 单位写在表头，不写在每格。
5. 每个表有标题（结论句）和来源行。

## 5. dataviz 要点

1. 顺序：选形式 → 按职责分配颜色 → 运行校验器 → 标记规格 → 悬停层 → 无障碍终检 → 渲染看图。
2. 一个序列是重点时用强调法：一个强调色其余灰。
3. 名义类别的单序列条一律同色，不按数值给深浅。
4. 直接标注节制：终点、极值、重点序列。放不下的标签移出，不裁切。
5. 每个图有表格视图孪生；tooltip 不是读数的唯一方式。
6. 校验器命令以 `dataviz` skill 文档为准。浅色与深色各跑一次。校验器只在本机运行，不联网。

## 6. diagram-design 的离线与中文

1. 字体源选 `system`，去掉 Google Fonts `<link>`，用 `scripts/self_check.py --offline` 自检。
2. 简体中文字体栈：`'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei'`，由观众本机提供。
3. 宽度估算：全角字符 1em，拉丁 0.60em（无衬线），加内边距后向上取整到 4 的倍数。SVG `<text>` 不自动换行，手动拆行。
4. 它的默认皮肤（米白纸、衬线标题、橙色强调、全大写 eyebrow）踩中用户的 Defaults 禁令。按其 `style-guide.md` 换成本页令牌，去掉 eyebrow 与点阵背景。
5. 导出 PNG 需要 Playwright，不自动安装。HTML/SVG 产出不需要。

## 7. anatomy 的边界

1. 读其 `SKILL.md` 后按它的流程做：定尺寸等级 → 收集真实数字 → 发明物体 → 部件清单 → 构建 → 验证。
2. 不运行 `scripts/publish.mjs`。它把图推到公开社区库，本 skill 不使用。
3. 检查脚本需要 Chrome。没有 Chrome 时用 `agent-browser` 截图，并在报告里写明哪些检查没跑。
4. 一张 Figure 档的图约 150KB 以内，可内嵌。Hero 档 2 到 4 小时，先问用户。
5. 图内不放文字，中文放卡片四角与图例；读数用真实单位，`tabular-nums`。
