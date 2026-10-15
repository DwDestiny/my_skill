---
name: visual-motion-design
description: 视觉与动效总 skill。负责 HTML 页面的整体视觉、设计系统、版式、图表与图示、3D 等轴测图、动效引擎与视觉炫技。按场合选档位（清晰讲解 / 混合 / 展示冲击）分配预算，而不是关掉动效。触发词：设计页面、做一个 HTML、视觉、排版、配色、令牌、动效、入场动画、滚动效果、炫一点、要有冲击力、展示页、发布页、讲解页的视觉、图表怎么画、等轴测、3D 图、设计计划、线框、截图自检、视觉评审、页面看起来像模板、太 AI 味。串联 frontend-design、artifact-design、dataviz、artifact-diagramming、design-taste-frontend、diagram-design、anatomy，并吸收 juliobsz awwwards 与 open-claude-ui 的方法。不适用：决定页面说什么、章节怎么拆、哪些内容保留（那是 content-blueprint）；原生 macOS / iOS 应用界面；仪表盘与后台表单的交互设计；纯文字文档。
---

# 视觉与动效

把内容蓝图变成一张设计过的页面。动效引擎和视觉炫技是一级能力，按档位分配预算。文字、来源、可信度标记在任何档位都保持可读。

效果优先：预算与效果冲突时先保效果，底线（减少动效、对比度、可读性、可信度标记）不退。可以接受固定版本的 CDN 依赖（GSAP、ScrollTrigger、Lenis）和联网字体。

## 1. 触发后先做的三件事

1. 读用户原话。把原话逐字抄进设计计划第 9 节。原话优先于本文件的任何规则。
2. 读 `frontend-design` skill（路径：`~/.claude/plugins/cache/claude-plugins-official/frontend-design/*/skills/frontend-design/SKILL.md`，取最新目录）。发布为 Artifact 时再加载 `artifact-design`。
3. 判断输入类型：
   - 有 `01-内容规划/blueprint.md`：按 `references/handoff.md` 第 2 节过门禁，然后开工。
   - 没有蓝图，且页面是讲解、学习、汇报、展示资料：先调用 `content-blueprint`，拿到蓝图再回来。
   - 没有蓝图，且页面是纯展示（发布页、作品页、概念演示、Demo 外壳）：用户的简报就是输入，直接开工，档位通常为 `show`。

## 2. 术语表

| 术语 | 含义 |
|---|---|
| 档位 | 预算档：`clear` 清晰讲解、`mixed` 混合、`show` 展示冲击 |
| 阅读区 | 正文、表格、来源、术语、折叠内容、图注、目录 |
| 舞台区 | hero、章节开场、签名时刻、页脚收尾、独立的图或 3D 场景 |
| 签名时刻 | 页面里唯一允许"响"的动效或构图 |
| 动效动词 | 全页动效共用的一个比喻（"像纸落定"） |
| 驱动模块 | 一个变量驱动全部承载概念的视觉 |
| 角色表 | 设计计划里登记每个炫技元素职责的表 |
| 蓝图 | `content-blueprint` 产出的 `blueprint.md` |
| 退回 | A 发现蓝图问题时写进 `handoff-log.md` 的条目 |

## 3. 路由表：什么时候读什么

| 情况 | 读 | 做 |
|---|---|---|
| 任何页面 | 本文件；`references/gears.md`；`references/design-plan-template.md`；`references/tokens-and-type.md` | 定档位、写设计计划 |
| 要加动效 | `references/motion.md`（含"选引擎"一节）；`assets/engine/` | 按档位选引擎并接入 |
| 蓝图有 `metric` / `chart` | Skill 工具加载 `dataviz` | 运行其校验器（本机） |
| 蓝图有 `diagram`（机制图） | Skill 工具加载 `artifact-diagramming` | 内联 SVG |
| 蓝图有 `diagram`（成套风格图） | `.claude/skills/diagram-design/SKILL.md` 与对应 `type-*.md` | 离线模式，换皮肤 |
| 蓝图有 `figure3d` | `.claude/skills/anatomy/SKILL.md`、`references/craft.md`、`motion.md`、`verify.md` | Figure 档，≤1 张（clear / mixed） |
| 页面是营销页、落地页、作品页，或用户说"像模板""AI 味" | `.claude/skills/design-taste-frontend/SKILL.md`；其 `references/tells.md`、`critique.md` | 可用 `scripts/draw.mjs` 发方向（本机、写 `~/.taste-skill/history.json`）；不用 `assets.mjs --get` |
| 发布为 Artifact | `references/artifact-contract.md`；Skill 工具加载 `artifact-design` | 按平台契约改骨架 |
| 派发给子代理 | `references/dispatch-template.md` | 填模板 |
| 评审 | `references/review.md` | 截图、ROUND、Fable |
| 项目有自己的边界 | `references/project-overlay.md`（通用说明，说明如何建项目叠加层） | 补充项目边界 |

不要一次读完全部。按表取用。

## 4. 流程

### 步骤 1：选档位

1. 读蓝图的 `gear_suggestion` 与 `audience.use_mode`。
2. 用户原话指明风格时，用户原话优先。
3. 按 `references/gears.md` 第 1 节定档，写进设计计划第 2 节，附理由。
4. 列出舞台区与安静区。

### 步骤 2：写设计计划

1. 用 `references/design-plan-template.md`，写到 `02-设计/design-plan.md`。
2. 先写点子（第 3 节），再写令牌（第 4 节）。
3. 每个炫技元素登记进角色表（第 6 节）。没有角色的元素不做。
4. 对照用户原话（第 9 节）。做通用默认审查（第 10 节），至少改一处。
5. 计划里有未决问题时，先问用户，再写代码。

### 步骤 3：静态搭建

1. 复制 `assets/base-tokens.css` 为起点，按设计计划改写每个值。
2. 写语义 HTML：`lang="zh-CN"`、一个 `h1`、有序标题、landmarks、skip link、目录。参考 `assets/page-skeleton.html` 的结构。
3. 按蓝图逐章搭建。每章的 `claims` 全部渲染，附可信度标记与来源编号。组件做法见 `references/components.md`。
4. 图按 `references/figures.md` 路由。每张图有结论标题、表格孪生、12px 以上文字。
5. 动效关闭时页面必须完整、好看。此时拍一次截图。

### 步骤 4：动效层

1. 按 `references/motion.md` 第 2 节"选引擎"接入 `assets/engine/`。`clear` 用 `motion-engine.js`。`mixed` 与 `show` 用 `motion-engine-gsap.js`，起点是 `assets/page-skeleton-gsap.html`。调用 `boot({ gear })`。
2. 阅读区只做反馈与状态。舞台区按 `references/gears.md` 第 5 节的菜单选手法。
3. 做签名时刻。写清它表达主题的哪一点。
4. 查减少动效版本：内容完整，无空白带。

### 步骤 5：门禁（本机，离线）

1. HTML 可解析；外链只允许固定版本的 CDN 脚本和 Google Fonts（grep `http`，逐条核对版本号）。
2. `lang="zh-CN"`；一个 `h1`；每个 `img` 有 `alt`；每个 `svg` 有 `role="img"` 与 `aria-label`。
3. 对比度：正文 4.5:1，大字 3:1，浅色与深色各算。
4. 同屏字号 ≤4；中文 ≥12px；强调色 <5%。
5. 有图表时跑 `dataviz` 校验器，浅深两次。
6. 有 diagram-design 图时跑 `self_check.py --offline`。
7. 可用 `design-taste-frontend/scripts/lint.mjs` 扫源码；其 FAIL 项里"功能性表格线、真实 `<ol>` 编号、来源编号"可豁免，豁免写理由。

门禁通过不代表设计好。继续步骤 6。

### 步骤 6：截图自检

1. 按 `references/review.md` 第 1 节拍全套截图，放 `05-评审/shots/<日期>/`。
2. 每张截图过第 2 节自检表的每一项。
3. 写 ROUND 记录。修前三问题。至多 3 轮。
4. 不为通过检查表删动效。过不了先改角色、位置、幅度；确需删除时写进报告。

### 步骤 7：Fable 视觉评审

1. 用 `references/review.md` 第 5 节模板发起评审。模板里放用户原话、档位、截图目录、自评。
2. 处理意见。Fable 与用户原话冲突时，按用户原话，并写明分歧。
3. `show` 档建议再做一次盲评（第 6 节）。

### 步骤 8：报告与收尾

1. 按 `references/review.md` 第 7 节格式报告：路径、档位、检查结果、契约变更、未验证项。
2. 在 `handoff-log.md` 追加 `delivered` 条目。
3. 清理中间截图，只留最后一轮。
4. 不声称没跑过的检查。

## 5. 档位摘要

完整预算、检查表逐项处理、炫技菜单见 `references/gears.md`。

| 预算 | clear | mixed | show |
|---|---|---|---|
| 同屏字号 | ≤4 | ≤4 | ≤4 |
| 阅读屏动效元素 | 0 | ≤2 | ≤2 |
| 舞台屏动效元素 | ≤3（仅 hero） | ≤6 | ≤12 |
| 入场时长 | 400 到 700ms | 500 到 900ms | 700 到 1300ms |
| 签名时刻 | 0 到 1 | 1 | 1 + 1 转场系统 |
| 加载器 | 无 | ≤1.2 秒 | 1.1 到 2.6 秒，真实进度 |
| 固定舞台 / scrub | 无 | ≤1，位移 ≤8% | 允许 |
| WebGL | 无 | 图内 ≤1 | 允许 |
| 3D 等轴测 | ≤1 | ≤1 | ≤2 |
| 允许炫技区域 | 无 | hero、章节开场、1 张核心图、页脚 | 全部舞台区 |

## 6. 任何档位都不退的底线

1. 尊重 `prefers-reduced-motion`：内容全部可见，无位移、无循环、无平滑滚动、无加载表演。
2. 浅色和深色都过对比度：正文 4.5:1，大字与图形 3:1。
3. 可读性：中文正文 16 到 18px，行高 1.7 到 1.9，每行 32 到 40 字，图内中文 ≥12px。
4. 可信度标记与来源不被遮蔽、不延迟出现、不小于 12px、不只靠颜色。
5. 原生光标可见；不劫持滚动（Lenis 只给惯性，不锁滚动、不改方向）；键盘与 Ctrl+F 正常。
6. 文字是真文本。Canvas 与 GL 不承载唯一信息。
7. 交互元素四态齐全；命中区 ≥24px，主操作 ≥44px。
8. 静态帧完整。
9. Defaults 禁令：无奶油底加衬线加陶土、无近黑底加酸色、无同款圆角卡、无全大写 eyebrow、无点号连接的元信息、无装饰编号、无等宽小标签。

## 7. 交接契约

A 读蓝图、证据索引、术语表。A 不读原始资料，不自己补内容。发现问题按 `references/handoff.md` 第 3 节的七种类型退回：`over_budget`、`wont_fit`、`form_mismatch`、`missing_source`、`term_conflict`、`incomplete`、`gear_conflict`。退回写进 `01-内容规划/handoff-log.md`，追加不改。

## 8. 网络与权限

> **警告**：下列动作先停下来问用户，得到同意再做。原因：它们把内容交给第三方，或发布后别人能看到。

1. 从任何网站取图。
2. 发布到公开库（anatomy 的 `publish.mjs`、任何画廊）。
3. 发布 Artifact。
4. 调用外部模型或图像生成服务。

不需要先问：

1. 固定版本的 CDN 脚本（GSAP、ScrollTrigger、Lenis，以及按需的 OGL 或 three.js）。版本须精确，发布满 14 天，见 `assets/engine/motion-engine-gsap.js` 的 `CDN` 常量。
2. 联网字体（默认 `assets/fonts-web.html`）。

默认：`mixed` 与 `show` 用 GSAP 引擎，字体联网，系统中文字体栈作回退。CDN 不可达时页面回退到零依赖引擎，内容照常可见。不运行 `design-taste-frontend/scripts/assets.mjs --get`。本 skill 的任何步骤都不向模型厂商发请求。

## 9. 版权

不复制 Anthropic / Claude 的品牌色、字体名、图标、logo。open-claude-ui 只吸收方法。引擎保留 juliobsz 的 MIT 声明。GSAP 与 Lenis 只从 CDN 加载，本 skill 不分发。详见 `references/sources-and-credits.md`。

## 10. 验证方法（协调者照做）

样例任务 A1（clear）：给 `assets/page-skeleton.html` 换上一个真实蓝图的三章内容，档位 `clear`。

1. 检查产出目录有 `02-设计/design-plan.md`，且第 3、6、9、10 节非空。
2. 用 `agent-browser` 打开页面，拍 1440 / 390 / 深色 / 减少动效四张截图。
3. 减少动效截图里标题与要点全部可见，无空白带。
4. 任一截图同屏字号 ≤4；来源编号与可信度标记可见。
5. `grep -c "http" index.html` 只命中固定版本的 CDN 与 Google Fonts 链接。
6. `05-评审/` 有 ROUND 记录，且至少改过一处。

样例任务 A2（show）：同一内容，档位 `show`，要求一个签名时刻与一个驱动模块。

1. 设计计划角色表至少 3 行，每行有减少动效行为。
2. hover 前后截图成对；主要目标的 hover 不只是换色。
3. 加载器总时长在 1.1 到 2.6 秒之间（录屏或时间戳）。
4. 减少动效截图无加载器、无漂移，内容完整。
5. 阅读区截图的动效元素 ≤2。

样例任务 A3（退回）：给 A 一张 11 个节点的流程图蓝图。

1. A 不画图，而是在 `handoff-log.md` 写一条 `over_budget`，含实际数 11、上限 9、拆法建议。

通过标准：三个样例都满足各自全部条目。任一条不满足，记录在报告"未验证项"。
