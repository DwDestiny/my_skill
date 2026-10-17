# 60fps.design：UI 动效细节库

核实：2026-10-15 读首页、`/mcp`、`/snippets`、`/why`、`/glossary`。未看视频。条款页（`/terms`）未读。

## 1. 它是什么

2022 年起收集 App 的动效细节，现有约 2110 条短片（shots）、494 个应用、83 条动效（Motion）、20 个代码片段、67 个故事板，另有词汇表和招聘页。内容以 iOS 为主，网页较少（App Sites 93 个）。

## 2. 网址与筛选

| 项 | 网址模式 |
|---|---|
| 短片 | `/shots/<名称>` |
| 筛选 | `/shots/filter/<名称>` |
| 应用 | `/apps/<名称>`，类别 `/apps/category/<名称>` |
| 其他栏目 | `/appsites`、`/motion`、`/snippets`、`/storyboards`、`/glossary`、`/mcp`、`/pro` |

筛选词（均来自首页）：

| 维度 | 词 |
|---|---|
| 手势 | drag、flick、flip、hold、long-press、pan、pinch、pull、scroll、scrub、slide、swipe、tap、typing |
| 模式 | empty、intro、loading、onboarding、pricing、recap、reward、setup、shared-element、stats、success-state、theme、timer 等 |
| 效果 | blur、bounce、confetti、draw、fade、glow、grow、morph、orbit、parallax、particles、pulse、reveal、sequence、shimmer、show-hide、spring-physics、stagger、ticker、zoom 等 |
| 元素 | badge、bottom-sheet、button、card、counter、graph、input、menu、progress、slider、tabs、toast、tooltip 等 |

## 3. 范围

只用网页可看的短片和词汇表。只看，不下载，不转存。本 skill 不收录该站的 MCP（付费，向外部服务发请求）和代码片段（SwiftUI，不是 HTML）。条款页（`/terms`）未读。

## 4. 怎么用

1. 写出动效要回答的动作或状态变化（`motion.md`）。例："成熟度阶梯依次填满"。
2. 用筛选词定位：效果 `sequence`、`stagger`、`grow`、`reveal`；元素 `progress`、`counter`、`graph`；模式 `empty`、`stats`、`recap`。
3. 每个筛选看 5 到 8 条。只记三件事：触发、运动、落定。
4. 把节奏改写成本 skill 的时长表（`motion.md`）。不抄时长数值。
5. 检查减少动效版本：直接落到终态。

## 5. 示例（来自首页列出的真实条目名）

| 本页任务 | 筛选 | 候选条目 | 取 | 舍 |
|---|---|---|---|---|
| s5 成熟度阶梯依次填满 | 效果 `sequence`+`stagger` | CRED Autopay Bills Stack Animation | 逐层出现的顺序和间隔 | 3D 堆叠外观 |
| s1 指标数字滚动到位 | 元素 `counter` | Revolut Number of Transactions Interaction | 数字落定的方式 | 货币与品牌外观 |
| 折叠区展开 | 元素 `card`+效果 `show-hide` | 不限，按列表选 | 展开后其余内容的位移 | 弹簧回弹（结构类不回弹） |
| 页面加载 | 模式 `loading` | Uber Loading Animation | 加载表达进度 | 品牌图形（`mixed` 档加载器 ≤1.2 秒） |
| 打开术语弹层 | 元素 `tooltip`、`bottom-sheet` | Circle Menu Dropdown Morph Interaction | 弹层出现的起点（从触发点生长） | 圆形菜单形状 |

候选条目名来自列表，视频效果本次没看。落地前先看视频。

## 6. 词汇

首页词汇表共 55 个词（如 Morph：一个形状平滑变成另一个；Empty State：无内容时的引导占位；Scrub：沿时间线拖动）。写动效描述时用这些词，保持一词一义。
