# visual-motion-design

**视觉与动效。** 读取 [`content-blueprint`](../content-blueprint/README.md) 产出的蓝图，设计并搭建 HTML 页面：版式、令牌、图表与图示、等轴测 3D、动效引擎、视觉炫技。

动效和炫技是一级能力。它按场合分配预算（档位），不是开或关。文字、来源、可信度标记在任何档位都保持可读。

## 什么时候触发

| 场景 | 例子 |
|---|---|
| 设计页面、做 HTML、排版、配色 | "做一个 HTML""令牌" |
| 要动效或视觉冲击 | "入场动画""炫一点""要有冲击力" |
| 要图表、图示或 3D 图 | "等轴测""图表怎么画" |
| 页面像模板 | "太 AI 味" |

不适用：决定页面说什么和章节怎么拆（用 `content-blueprint`）；原生 macOS 或 iOS 界面；仪表盘与后台表单；纯文字文档。

## 配对方式

1. 有 `blueprint.md`：按 `references/handoff.md` 过入口门禁，然后开工。
2. 讲解、学习、汇报类页面没有蓝图：先用 `content-blueprint`。
3. 纯展示页（发布页、作品页、概念演示）：用户简报就是输入，直接开工。
4. 读蓝图、证据索引、术语表，不读原始资料，不自己补内容。
5. 发现问题时在 `handoff-log.md` 追加退回条目，共 7 种类型：`over_budget`、`wont_fit`、`form_mismatch`、`missing_source`、`term_conflict`、`incomplete`、`gear_conflict`。
6. 交付后追加一条 `delivered` 条目。

## 档位

| 档位 | 用于 | 动效预算 |
|---|---|---|
| `clear` | 读者主要读文字：速读、翻查、学习 | 阅读区 0 个动效元素。舞台区只有 hero，最多 3 个。使用零依赖引擎 |
| `mixed` | 读和看都有 | 阅读区最多 2 个，舞台区最多 6 个。使用 GSAP 引擎 |
| `show` | 读者主要看和体验：发布页、作品页 | 阅读区最多 2 个，舞台区最多 12 个，允许 WebGL。使用 GSAP 引擎 |

完整预算表在 `references/gears.md`。用户原话指明风格时，原话优先于档位建议。

任何档位都保持这些底线：`prefers-reduced-motion` 下内容完整可见，浅色与深色都过对比度，来源与可信度标记不被遮蔽，不劫持滚动，文字是真文本。

## 流程

SKILL.md 把流程分为 8 步：选档位、写设计计划、静态搭建、动效层、本机门禁、截图自检、独立视觉评审、报告收尾。静态版本必须先完整好看，再加动效。

## 目录

```text
visual-motion-design/
├── SKILL.md                  主流程与路由表
├── agents/openai.yaml
├── assets/
│   ├── base-tokens.css       令牌起点
│   ├── page-skeleton*.html   页面骨架（零依赖版与 GSAP 版）
│   ├── fonts-web.html        联网字体片段
│   └── engine/               动效引擎与 LICENSE-MIT.txt
└── references/               档位、设计计划模板、令牌与字体、动效、图、
                              组件、评审、交接契约、派发模板、来源与致谢、项目叠加层说明
```

## 安装

1. 把本目录放进你的 agent skills 目录，或用仓库根 `README.md` 的安装方式。
2. 同时安装 `content-blueprint`。
3. 安装依赖的第三方 skill（下表）。

| 依赖 | 安装命令 | 必需性 |
|---|---|---|
| frontend-design | Claude Code 官方插件 `frontend-design` | SKILL.md 第 1 节要求先读 |
| design-taste-frontend | `npx skills add Leonxlnx/taste-skill` | 营销页、落地页、作品页时按路由表使用 |
| diagram-design | `npx skills add cathrynlavery/diagram-design` | 可选。成套风格图时使用 |
| anatomy | `npx skills add wheresryan22/anatomy` | 可选。3D 等轴测图时使用 |

diagram-design 或 anatomy 缺失时的降级行为：SKILL.md 没有写明，未验证。

> **警告**：不要在没有用户批准时运行 anatomy 的 `scripts/publish.mjs`。它会把作品发布到公开画廊。原因：发布后任何人都能看到。本 skill 也不运行 design-taste-frontend 的 `assets.mjs --get`。

## 网络与权限

1. 固定版本的 CDN 脚本（GSAP、ScrollTrigger、Lenis）和 Google Fonts 可以直接用。引擎脚本对 CDN 脚本带 SRI 校验。
2. CDN 不可达时，页面回退到零依赖引擎，内容照常可见。
3. 取图、发布到公开库、发布 Artifact、调用外部模型或图像服务：先问用户。

## 验证状态

| 项 | 状态 |
|---|---|
| `scripts/check_skill_structure.sh skills/visual-motion-design` | 通过 |
| 动效引擎在真实浏览器 1440 与 390 宽度 | 已测 |
| 深色模式 | 已测 |
| 减少动效（reduced-motion） | 已测 |
| CDN 失败时的回退 | 已测 |
| `node --check` 两个引擎文件 | 通过 |
| WebGL 加载 | 未测 |
| 真机与触屏 | 未测 |
| 慢速 CDN | 未测 |
| `SKILL.md` 第 10 节的样例任务 A1、A2、A3 | 未跑 |

## 许可与来源

1. 仓库许可：MIT，见仓库根 [LICENSE](../../LICENSE)。
2. `assets/engine/` 派生自 juliobsz/skills 的 awwwards motion engine（MIT）。版权声明在 `assets/engine/LICENSE-MIT.txt`。
3. GSAP（标准免费许可）与 Lenis（MIT）只从 CDN 加载，本仓库不分发。
4. 其余吸收与舍弃的来源见 `references/sources-and-credits.md`。
5. 不使用 Anthropic 或 Claude 的品牌色、字体名、图标、logo。
