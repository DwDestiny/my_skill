# 派发提示模板

用户规则原文：

> Put the skill file path and the user's quoted words in every dispatch prompt for a design or UI work package. Tell the agent to read both before it writes code.

把下面的模板填完整后再派发。模型与 effort 按用户的角色表选（设计与视觉打磨给 opus，实现给 sonnet，机械检查给 haiku）。

```
# 任务：<页面名> · <工作包名>

## 先读（写代码前全部读完）
1. 视觉与动效 skill：<skill-root>/visual-motion-design/SKILL.md
   以及 references/gears.md、design-plan-template.md、review.md
2. 设计基础 skill：~/.claude/plugins/cache/claude-plugins-official/frontend-design/*/skills/frontend-design/SKILL.md（取最新目录）
3. 需要时：artifact-design（发布 Artifact）、dataviz（图表）、artifact-diagramming（内联 SVG）、diagram-design、anatomy
4. 内容蓝图：<01-内容规划/blueprint.md 路径>，证据索引：<evidence-index.md 路径>，术语表：<glossary.md 路径>
5. 设计计划：<02-设计/design-plan.md 路径>（已批准，照做；要改先写 handoff-log）

## 用户原话（逐字，不得改写）
> <原话 1>
> <原话 2>

## 档位
<clear|mixed|show>。预算见 gears.md 第 2 节。底线见 gears.md 第 4 节。不要为通过检查表删动效；过不了先改角色、位置、幅度。

## 文件所有权
| 文件 | 所有者 |
|---|---|
| 03-页面/index.html | 本代理 |
| 02-设计/design-plan.md | 只读 |
| 01-内容规划/* | 只读；问题写进 01-内容规划/handoff-log.md |

## 工作目录与分支
<绝对路径>，分支 <名>。只在此目录工作。小步提交。

## 网络与权限
固定版本的 CDN 脚本（GSAP、ScrollTrigger、Lenis）和联网字体可以直接用，`mixed` 与 `show` 默认用 `assets/engine/motion-engine-gsap.js`。取图、发布到公开库、发布 Artifact、调用外部模型或图像生成服务：先停下来问用户。不运行 anatomy 的 publish.mjs，不运行 design-taste-frontend 的 assets.mjs --get。

## 验证
1 级（每次改动后）：HTML 校验、外链只含固定版本 CDN 与 Google Fonts、`lang="zh-CN"`、对比度计算、引擎在减少动效下内容可见。
2 级（里程碑）：按 review.md 第 1 节拍全套截图，逐项过第 2 节自检表，写 ROUND 记录。
把截图放在 05-评审/shots/<日期>/。

## 报告格式
最终提交；检查结果（截图数、未过项与修复、ROUND 记录）；契约变更（退回条目编号）；未验证项。
```
