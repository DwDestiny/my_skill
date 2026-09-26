# UI 全流程来源选型

本页记录 UI 全流程 skill 包的来源取舍，不是方法论正文。内容是对上游能力的原创摘要；不复制上游 skill、第三方 Pro 资源、规则全文或截图。来源如需纳入未来版本，先复查其当时的路径、版本、工具可用性和许可。

研究时间：2026-09-26 12:49–12:57 UTC。代码仓库的 `main` SHA 在当轮读取；官方文档和网站记录当轮访问日期。分支地址会变化，后续复查应以表中 SHA 或官方稳定版本为准。

## 八阶段选型

| 阶段 | 选型 | 适配的来源 | 为什么这样选 / 边界 |
| --- | --- | --- | --- |
| 1. 产品页面规划 | **自研编排** | GOV.UK 用户需求与服务设计指导 | 目前未找到能从产品目标可靠推出页面清单、用户角色、主任务和范围边界的完整 Skill。采用用户需求、现有旅程、数据与约束作为起点；不可让视觉生成工具补写未提供的产品事实。 |
| 2. UX、信息架构、状态、低保真 | **自研骨架，按需引用** | GOV.UK Patterns；WAI-ARIA APG；WCAG 2.2 | GOV.UK 的任务与表单模式可作例子，需按产品领域改写；APG 用来核实键盘操作、角色与状态，WCAG 作项目明确的无障碍验收基线。标准或模式不能替代用户研究，也不能自动决定信息架构。 |
| 3. 多方案视觉方向 | **适配设计原则** | Anthropic `frontend-design`；OpenAI `frontend-app-builder` | 用有依据的方向探索、明确取舍和具体内容来减少模板感。新 Skill 应保留多候选比较；不照抄单一审美，也不照搬 OpenAI 插件对 ImageGen、概念批准或“10/10”评语的硬性要求。 |
| 4. 设计系统与 tokens | **自研词汇与治理，采用格式** | DTCG Format Module 2025.10；`frontend-app-builder` | 由本 Skill 决定语义层级、命名和变更规则；如需跨工具交换，按稳定的 DTCG 2025.10 格式表达。不要把格式标准误当作设计价值判断，也不要使用标成 preview 的 drafts 页面。 |
| 5. 逐页逐屏 hi-fi | **自研检查清单，Figma 作为可选执行工具** | OpenAI Figma `figma-use` | 需要覆盖每一页、关键状态和响应尺寸；高保真应延续已接受的方向与 tokens。Figma Skill 讲的是工具调用和 API 操作，不是产品设计方法；只在 Figma 集成可用、且本轮确需对文件操作时加载。 |
| 6. 动效 | **自研动效规则，按需采用现成组件** | Anthropic `frontend-design`；WCAG 2.2；Libraries.dev free skill | 动效应解释反馈、状态或层级，并考虑 reduced motion；Libraries.dev 是 AI 界面特效组件集，可按场景选择，不承担完整动效设计。Free 与 Pro 内容分开；Pro 的 Studio 导出、预设与配方不进入本包。 |
| 7. 前端实现 | **自研交接规则，适配实现原则** | OpenAI `frontend-app-builder`；Vercel `react-best-practices` | 将已接受设计转成可运行界面，并在尊重项目现有技术约束的前提下复用组件、保持状态有意义。Vercel 指南是 React/Next.js 性能规则，不是通用视觉规范；OpenAI 插件依赖 Codex 浏览器、图像工具等环境。 |
| 8. 真实视觉 QA | **自研证据门槛，按运行环境选工具** | 当前 Codex Browser/内置浏览器；Playwright CLI Skill；Vercel `web-design-guidelines`；WCAG/APG | QA 要查看实际渲染的页面、关键状态和尺寸，并把现状与已接受的设计依据对照；自动化可补交互和截图，文件规则检查不能代替视觉对比、键盘走查或人工判断。Playwright Skill 所在仓库已废弃，因此只作历史操作参考；当前 Codex 插件 Skill 优先。 |

## 来源与许可快照

以下链接指向一手来源。标记“未知”表示本轮没有找到能支持可再分发结论的具体许可文件；不可由公开可读或可下载推导出再发布权。链接与原创摘要可以用于溯源，skill 包不内嵌上游正文。

| # | 一手来源、路径与版本 | 能支持的环节 | 许可证与不可再分发边界 | 短板与结论 |
| --- | --- | --- | --- | --- |
| 1 | [Anthropic `frontend-design`](https://github.com/anthropics/skills/blob/33375500bcea98d610eb30ce10ac4e59b89c390d/skills/frontend-design/SKILL.md)；`skills/frontend-design/SKILL.md`，`main` SHA `33375500bcea98d610eb30ce10ac4e59b89c390d`；[该目录 LICENSE.txt](https://github.com/anthropics/skills/blob/33375500bcea98d610eb30ce10ac4e59b89c390d/skills/frontend-design/LICENSE.txt) | 第 3、6、7 阶段：依据主题做视觉取舍、克制动效、响应式与自我批评 | 目录内明确 Apache-2.0。若复制或改编其表达/文件，须遵守许可证并保留适用的版权、许可、NOTICE 与修改说明；本包只吸收高层做法并用自己的流程表述，不带入正文。 | 不覆盖产品发现、IA、逐屏交付与可复现 QA；作为设计质量来源适配，不作为全流程主 Skill。 |
| 2 | [OpenAI `frontend-app-builder`](https://github.com/openai/plugins/blob/1dc195897af4161d039b80d8471ec0a10c9bbc89/plugins/build-web-apps/skills/frontend-app-builder/SKILL.md)；路径 `plugins/build-web-apps/skills/frontend-app-builder/SKILL.md`；插件清单版本 `0.1.2`，`openai/plugins` `main` SHA `1dc195897af4161d039b80d8471ec0a10c9bbc89`；[插件清单](https://github.com/openai/plugins/blob/1dc195897af4161d039b80d8471ec0a10c9bbc89/plugins/build-web-apps/.codex-plugin/plugin.json) | 第 3–5、7–8 阶段：概念到 tokens/组件盘点、实现、浏览器检查 | 插件清单声明 MIT。若复制源文件，保留 MIT 版权和许可文本；本包不 vendoring，只原创适配流程。 | 很接近视觉 UI 交付链，但依赖 OpenAI 的图像生成与浏览器能力，并含严格的风格默认与批准门槛。抽取逐状态设计盘点、按页比较和迭代思路；不把其默认值设成普遍规则。 |
| 3 | [OpenAI Figma `figma-use`](https://github.com/openai/plugins/blob/1dc195897af4161d039b80d8471ec0a10c9bbc89/plugins/figma/skills/figma-use/SKILL.md)；[Figma 新建文件 Skill](https://github.com/openai/plugins/blob/1dc195897af4161d039b80d8471ec0a10c9bbc89/plugins/figma/skills/figma-create-new-file/SKILL.md)；`openai/plugins` `main` SHA 同上。旧目录许可快照见 [openai/skills 的 Figma `LICENSE.TXT`](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/figma-use/LICENSE.TXT)。 | 第 5 阶段按工具调用；涉及 Figma 文件、变量、组件和页面结构 | 旧目录许可明确受 Figma Developer Terms 约束，并标为 Beta；它不是 MIT/Apache。当前 `openai/plugins` 对应路径本轮未找到许可证文件，不能推定旧条款或推定可再发布；本包只链接，绝不收录 Figma Skill 正文。 | 说明如何调用工具，依赖 Figma MCP 和 Plugin API；不告诉我们该设计什么或如何验证用户需求。属于可选工具接入，不是完整交付流程。 |
| 4 | [OpenAI `playwright` CLI Skill](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/playwright/SKILL.md)；路径 `skills/.curated/playwright/SKILL.md`，`openai/skills` `main` SHA `49f948faa9258a0c61caceaf225e179651397431` | 第 8 阶段：真实浏览器导航、交互快照、截图与追踪 | `openai/skills` README 已宣布该仓库废弃，转向 `openai/plugins`；该 Skill 路径未找到自己的 `LICENSE.TXT`，许可未知，不再分发其原文。 | 操作循环对浏览器自动化有用，但偏命令行操作，不定义 UI 视觉验收；当前环境优先选择能用的内置浏览器/Browser 插件，Playwright 作明确回退。 |
| 5 | [OpenAI `skill-creator`](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/SKILL.md)；`skills/.system/skill-creator/SKILL.md`，同一 `openai/skills` SHA；该仓库 [README](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/README.md) 声明 `.system` 原为随 Codex 自动安装。 | 包结构、渐进披露、按需引用资源与验证方式 | 仓库 README 现标记 deprecated；该 Skill 路径未找到单独 `LICENSE.TXT`，不可据此复制正文。创建本包时应使用当前已安装的 `$skill-creator`，并按主控核过的 [OpenAI 插件文档](https://developers.openai.com/plugins/build/plugins) 定义兼容结构；本研究不移植旧目录内容。 | 它负责“如何写 Skill”，不提供 UI 领域知识；旧仓库的实现细节不应作为当前插件打包/CLI 指令来源。 |
| 6 | [Libraries.dev Agent Skill](https://github.com/Jakubantalik/Libraries.dev/blob/f20116327f4e3b28d0fb70b04437dfd092bf88fe/skills/libraries-dev/SKILL.md)；路径 `skills/libraries-dev/SKILL.md`，`main` SHA `f20116327f4e3b28d0fb70b04437dfd092bf88fe`；[免费/Pro 使用边界](https://libraries.dev/skill)、[免费组件列表](https://libraries.dev/how-to-use) | 第 6 阶段的可选动效/视觉组件 | 仓库根许可证声明 MIT；网站说明免费组件 MIT，可用于商业项目。Pro 的 Studio 导出、预设和配方由购买计划授权；不复制、打包或伪装 Pro 内容为开源。 | 七个 AI UI 效果库和安装指导，不是动效策略或全局设计系统。只作用户选择某个免费组件时的外部选项，不将它作为依赖打入 skill 包。 |
| 7 | [Vercel `react-best-practices`](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-best-practices/SKILL.md)；路径 `skills/react-best-practices/SKILL.md`，metadata 版本 `vercel 1.0.0`，`main` SHA `063bee94c3f4df8453406c830b0a7df0f2860278` | 第 7 阶段：React/Next.js 性能实现和代码复核 | Skill metadata 声明 MIT；仓库 README 也声明 MIT。若拷贝规则原文，保留相关许可；本包只按原则原创归纳。 | 关注性能，不评价页面信息架构、设计方向或截图保真；只在 React/Next.js 项目且性能问题相关时引用。 |
| 8 | [Vercel `web-design-guidelines` Skill](https://github.com/vercel-labs/agent-skills/blob/063bee94c3f4df8453406c830b0a7df0f2860278/skills/web-design-guidelines/SKILL.md)；路径 `skills/web-design-guidelines/SKILL.md`，`main` SHA 同上；Skill 指向的活动规则为 [raw `command.md`](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)。 | 第 8 阶段的文件级 UI 规则检查 | Skill wrapper 在 `agent-skills` MIT 仓库内；它运行时另取的规则文件许可与版本本轮未核。把规则文件当外链实时读取，不把规则全文复制进包。 | 能检查源文件与规则，不等同于真实浏览器截图对比、用户走查或可访问性完整验证；动态获取也会导致规则随时间变化。 |
| 9 | [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)；Recommendation；本轮查阅 W3C 正式发布页（含 2024-12-12 勘误记录）。 | 第 2、5、6、8 阶段：可访问性验收条件，包含焦点、拖动替代、目标尺寸、认证等准则 | W3C 标准文档，不是代码库许可。本包仅列章节/准则编号并写原创检查项，不拷贝整份准则或示例；具体复用全文规则前先核 W3C 文档版权条款。 | 规范需要结合技术栈、目标 WCAG 等级和辅助技术实测；仅有自动扫描不能证明符合标准。 |
| 10 | [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)；W3C WAI 指南，页面无独立语义版本号；本轮查阅日期见页首。 | 第 2、5、8 阶段：常见控件的语义、键盘交互、状态属性和功能例子 | W3C 指南文本和示例，本包只引用 pattern 名称和链接；不将例子实现源码整体复制进 Skill。 | APG 是实现 ARIA 的指南，不会自动让自定义控件比原生 HTML 更合适；模式示例也不能替代屏幕阅读器和键盘实测。 |
| 11 | [DTCG Design Tokens Format Module 2025.10](https://www.designtokens.org/tr/2025.10/format/)；Final Community Group Report，2025-10-28；[技术报告索引](https://www.designtokens.org/technical-reports/) 当前列为 Stable。 | 第 4 阶段：跨工具的 tokens 文件交换和序列化格式 | 报告受 W3C Community Final Specification Agreement 管理；官方说明格式可自由实现。实施格式不等于可不注明来源地再发布整份标准文本；本包链接标准、只写原创约定。 | 它不是 W3C Standard/Standards Track，也不是 token 命名治理方案。本轮发现无版本号的 `/tr/drafts/format/` 明示“preview/experimental，勿作为权威、勿实现”；使用固定的 `2025.10` 稳定报告。 |
| 12 | [GOV.UK Design System Patterns](https://design-system.service.gov.uk/patterns/)；[GOV.UK 用户研究/设计服务手册](https://www.gov.uk/service-manual/user-research)；首页当轮标出 Frontend `6.5.0`（2026-08-27 发布）。 | 第 1–2 阶段：从真实用户任务、服务旅程、问题页/表单/错误恢复模式规划信息与页面 | `alphagov/govuk-design-system` 代码仓库为 MIT；网页指导正文的具体复用条款本轮未核。对 Skill 只链接并原创转述；若复用代码或长段正文另做许可证核验。 | 主要面向政府公共服务，许多规律可迁移，但具体流程和组件是情境化示例，不能原样强加给商业产品。部分 Service Manual 文章较旧，设计决策应结合当轮用户证据。 |

包装/安装备注（主控本轮核验）：按当前 [OpenAI 插件打包文档](https://developers.openai.com/plugins/build/plugins) 处理可移植 manifest 与 `.codex-plugin` 兼容清单；本机 CLI 添加插件的命令是 `codex plugin add`。不要沿用旧 `openai/skills` 仓库的安装指引。

## 明确不选与不打包项

- 不把 Anthropic、OpenAI、Vercel、Playwright 或 Libraries.dev 的 Skill 正文复制成新 Skill；相同功能用本项目自己的触发、顺序、边界与产物格式表达。
- 不打包 Libraries.dev Pro Studio 内容、Pro Skill 或导出配方；免费包也作为用户可选依赖，不能默认安装或联网写入项目。
- 不把任何来源当作“世界最好”或普遍有效的 UI 规范。阶段门槛应由用户目标、现有代码约束、证据和批准的设计决定。
- 本轮没有把 NNG 纳入 12 项主矩阵：现有 W3C/APG 与 GOV.UK 一手指南已覆盖本 Skill 的标准和任务模式需求；若具体任务要求 NN/g 某项研究，再单独定位该研究、版本和引用边界，而非把整站作为默认知识包。
- 上游源文件仍会变化。发布或 vendoring 之前必须重新确认来源 SHA、每个具体文件的许可（尤其 OpenAI 的逐 Skill 许可和 Vercel 动态规则）、平台工具依赖和当前插件打包规则。
