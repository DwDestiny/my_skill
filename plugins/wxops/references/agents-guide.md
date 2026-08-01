# agents — 编辑部 subagents(L2)

> 本文件是 `agents/` 目录的 L2 文档,住 `references/` 而非 `agents/` 目录内:插件校验器会把 `agents/` 下(含子目录)所有 .md 当 agent 定义扫描,无 frontmatter 的文档文件过不了 `--strict`。

## 模块边界

内容产线的四个专职 agent(Claude Code plugin agents,frontmatter + 提示词即全部实现,零代码)。**agents 是三层模型的"通用引擎"层**:提示词零账号知识、零赛道知识——账号身份(persona)与赛道知识(niche 包)全部由调用方在任务书里以文件路径喂入。换账号换 persona、换赛道换包,本目录一行不改。

## 成员清单

| agent | 岗位 | 写权限 | 被谁派 |
|---|---|---|---|
| `niche-scout.md` | 选题情报侦察(热点/竞品/风向,只读+联网) | 无 | topics 站 |
| `draft-writer.md` | 初稿执笔(吃三件套,证据包外零事实) | drafts/<slug>/draft.md | write 站 |
| `style-auditor.md` | 人设对照审计(对抗镜头,只审不改) | drafts/<slug>/audit.md | write 站 |
| `title-smith.md` | 标题候选(赛道公式×账号样本,人拍板) | 无 | write 站 |

## 本地规则

- `model: inherit` 统一——跟随用户会话模型,插件不替用户选模型档位
- tools 白名单最小化:侦察与标题岗无 Write;执笔与审计岗的 Write 仅为落盘产物
- 提示词里写死的是**纪律**(证据纪律/审计清单/产出格式),写不死的是**知识**(口吻/词表/结构)——新增 agent 前先问:它的知识是不是该住 niche 包或 persona
- 派单契约:调用方(工位 SKILL.md)负责把所需文件路径全部写进任务书;agent 收到残缺输入必须报缺、不许拿模型内知识垫
