---
name: write
description: Use when 写稿、写文章、把选题卡变成初稿、审稿、改稿、定标题, or running the three-piece-kit gated writing flow (persona + structure contract + evidence pack) for any managed account.
---

# write — 写作工位

## 核心原则

**三件套开工制，缺一不开工**：

| 件 | 是什么 | 住哪 |
|---|---|---|
| 人设 persona.md | 这个号是谁、怎么说话、什么不碰 | `~/.wxops/accounts/<slug>/persona.md` |
| 结构契约 structure.md | 本赛道文章怎么组织（文体骨架/必备模块） | niche 包内（用户包 → 内置包 → `_generic` 兜底） |
| 证据包 evidence.md | 这篇稿的事实底料，唯一事实来源 | `~/.wxops/accounts/<slug>/topics/<topic-slug>/evidence.md` |

这是血的教训制度化：没有人设的稿千号一面，没有结构的稿散架，没有证据的稿编造。**门禁是脚本不是自觉**——`wxops kit` 说缺件就是缺件，补齐再来，没有"先写着"。

## 工作流

插件根 = 本 SKILL.md 所在目录的上上级。

### 第 0 步 · 门禁体检（必须、脚本执行）

```bash
<插件根>/scripts/wxops kit --account <slug> --topic <topic-slug>
```

- 退出码 0 = 三件套齐备（外加选题卡），逐项 ✓，可开工
- 退出码非 0 = 缺件或空壳（文件缺失/为空/含未替换的 `{{...}}` 占位符），输出列明**缺什么 + 怎么补**。照指引补齐后重跑，通过前不进第 1 步

**首次使用没有 persona？** 两条路：① 从模板起——复制 `templates/persona.template.md` 到账号目录逐节填写（引导用户口述，你来执笔整理）；② 从既有材料导出——用户已有运营手册/账号 playbook 的，读它（只读，不动原文件）按模板骨架重组成 persona.md。**人设是账号资产，导出稿必须念给用户确认后才算就位；后续任何改动同样人来确认。**

### 第 1 步 · 初稿（draft-writer agent）

派 `draft-writer`，任务书给全五个路径：persona、结构契约（kit 输出里会写实际解析到哪一层）、evidence、选题卡、输出路径 `~/.wxops/accounts/<slug>/drafts/<topic-slug>/draft.md`。收到交稿说明后向用户转述要点（文体/字数/证据缺口/待主编注意）。

### 第 2 步 · 审计（style-auditor agent）

派 `style-auditor`，任务书给 draft、persona、结构契约、evidence 与输出路径 `drafts/<topic-slug>/audit.md`。按结论分流：

- **放行** → 进第 3 步
- **整改后放行** → 把审计报告必改项交回 draft-writer 改稿，改完重审。**审计循环最多 2 轮**——2 轮后仍不放行说明三件套本身有问题（人设写糊了/证据不够/选题不成立），停下来和用户一起修上游，不在稿面上死磕
- **打回**（红线/事实失据）→ 直接停，向用户报告命中条款；补证据或撤选题由人决定

### 第 3 步 · 标题（title-smith agent）

派 `title-smith`，给 draft、niche.json、persona 路径。把候选清单原样呈给用户，**人拍板定题**；定题后把最终标题写回 draft.md 首行。

### 第 4 步 · 主编终审（人）

把定稿全文呈给用户过目。用户点头 = 本站完成，稿件停在 `drafts/<topic-slug>/`，下一站 illustrate 配图。**你不迈过这一步**——没有人的"可以"，稿子永远是草稿。

## 红线

- 门禁体检绝不跳过、绝不"这次先手工确认"——脚本说了算
- 证据包外零事实：审计发现编造 = 一票打回，没有"改一下就好"
- persona 的建立与修改必须人确认；agent 只能提建议
- 审计循环上限 2 轮，超限修上游而不是磨稿面
- 全流程止于草稿：发布是 publish 站（P5）的事，且发布键永远在人手里
