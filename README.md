# my_skill

老党的开源 Skill 仓库：把反复验证过的 Agent 工作方法，沉淀成可复用、可安装、可测试的 Skills。

[English](#english) · [GitHub](https://github.com/DwDestiny/my_skill) · [Issue #5](https://github.com/DwDestiny/my_skill/issues/5)

![GEB Project Doc System Architecture](docs/assets/geb-project-doc-system-architecture.svg)

## 为什么这个仓库存在

很多 Agent 配置最后都会变成一堆长提示词：看起来很完整，真正工作时却触发不稳、不可测试、不可复用。

这个仓库的目标更直接：把高价值工作流做成 Skill。Skill 本体保持轻，细节放 references，重复动作放 scripts，最后用测试和真实项目狗粮验证。

## Skill 目录

| Skill | 路径 | 状态 | 适用场景 |
|---|---|---|---|
| product-expert | `skills/product-expert/` | 已入库 | 从一个产品想法出发，完成需求探知、产品定位、MVP 规划、评分和推荐 |
| visual-ppt-deck-builder | `skills/visual-ppt-deck-builder/` | 已入库 | 从主题、大纲和风格样张出发，生成高视觉质量且可编辑的 PPTX |
| geb-project-doc-system | `skills/geb-project-doc-system/` | v0.1 | 为大中型代码仓库建立 L1/L2/L3 AI 项目文档体系，减少 Agent 盲读和上下文浪费 |

## 重点：GEB Project Doc System

`geb-project-doc-system` 是给大项目用的 AI 项目地图 Skill。

它不试图让 Agent 一次读完整个仓库，而是让 Agent 按层读取：

```mermaid
flowchart LR
  L1["L1 根文档<br/>AGENTS.md / CLAUDE.md"] --> L2["L2 目录文档<br/>模块边界 / 文件清单"]
  L2 --> L3["L3 文件头<br/>Input / Output / Pos"]
  L3 --> Code["精确读取目标代码"]
  Code --> Sync["结构变更后<br/>L3 -> L2 -> L1 同步"]
```

适合这些场景：

- 中大型代码仓库，新会话经常重新摸项目。
- 多 Agent 协作，经常有人改结构但不更新项目说明。
- Claude Code、Codex、Grok Build、Gemini、OpenCode 等工具混用。
- 你希望减少盲读文件、重复解释和 token 浪费。

## 快速开始

审计一个项目：

```bash
python3 skills/geb-project-doc-system/scripts/audit_geb_docs.py /path/to/repo
```

先 dry-run 看会补哪些文件头：

```bash
python3 skills/geb-project-doc-system/scripts/update_file_headers.py /path/to/repo --json
```

确认后再写入：

```bash
python3 skills/geb-project-doc-system/scripts/update_file_headers.py /path/to/repo --apply
```

安装 Git hook：

```bash
skills/geb-project-doc-system/scripts/install_git_hook.sh /path/to/repo
```

## 推荐安装方式

一键安装到本机常见 Agent 目录，并给已有全局规则文件追加短触发声明：

```bash
scripts/install_geb_project_doc_system.sh --dry-run
scripts/install_geb_project_doc_system.sh
```

也可以手动链接：

```bash
ln -sfn "$(pwd)/skills/geb-project-doc-system" ~/.codex/skills/geb-project-doc-system
ln -sfn "$(pwd)/skills/geb-project-doc-system" ~/.claude/skills/geb-project-doc-system
ln -sfn "$(pwd)/skills/geb-project-doc-system" ~/.grok/skills/geb-project-doc-system
```

再在全局 `AGENTS.md` / `CLAUDE.md` 放一段短声明：

```md
仓库工作默认遵守 GEB 项目文档规范。结构变更前读取 L1/L2/L3；
结构变更后同步更新 L3 -> L2 -> L1；初始化、审计或迁移时使用
`geb-project-doc-system` Skill。
```

全局文档只放短声明，不要把完整规范塞进去。完整规则按需从 Skill 加载。

## 验证

```bash
scripts/check_skill_structure.sh skills/geb-project-doc-system
python3 tests/test_geb_project_doc_system.py
tests/smoke_visual_ppt_deck_builder.sh
```

## 仓库结构

```text
skills/
  product-expert/
  visual-ppt-deck-builder/
  geb-project-doc-system/
docs/
  repository-architecture.md
  skill-intake-checklist.md
  assets/
scripts/
tests/
templates/
```

## 新增 Skill 的标准

- `SKILL.md` 必须有 `name` 和 `description`。
- description 只写触发条件，不总结完整流程。
- 长资料放 `references/`，可重复动作放 `scripts/`。
- 先写压力场景或测试，再写 Skill。
- README 的 Skill 目录必须同步更新。
- 不提交密钥、账号、令牌或私有日志。

## 致谢与许可证边界

`geb-project-doc-system` 受赵纯想公开分享的 GEB 分形文档系统思路启发，尤其是 L1 根文档、L2 目录文档、L3 文件头 `Input / Output / Pos` 的分层项目地图思想。

开发过程中参考过这些开源项目的产品形态和落地经验：

- [`Claudate/project-multilevel-index`](https://github.com/Claudate/project-multilevel-index) — MIT License，提供完整 L1/L2/L3 自动化工具形态参考。
- [`longranger2/project-doc-bootstrap`](https://github.com/longranger2/project-doc-bootstrap) — MIT License，提供 `CLAUDE.md` / `AGENTS.md` 分层文档 Skill 形态参考。

本仓库首版 `geb-project-doc-system` 的 Skill 文档、审计脚本和文件头更新脚本为独立实现，不是上述项目的官方版本，也不代表赵纯想本人或相关项目背书。若未来复制、改编或合并第三方项目代码，应保留原项目版权声明和许可证文本，并在变更说明中明确标注来源。

## License

MIT. See [LICENSE](LICENSE).

---

## English

`my_skill` is an open-source skill repository for reusable, tested agent workflows.

Instead of growing one giant global prompt, each workflow becomes a focused Skill: light `SKILL.md`, deeper `references/`, deterministic `scripts/`, and real validation.

## Skills

| Skill | Path | Status | Use case |
|---|---|---|---|
| product-expert | `skills/product-expert/` | Available | Product discovery, positioning, MVP planning, scoring, and recommendation |
| visual-ppt-deck-builder | `skills/visual-ppt-deck-builder/` | Available | Build high-quality editable PPTX decks from a topic, outline, and visual direction |
| geb-project-doc-system | `skills/geb-project-doc-system/` | v0.1 | Maintain L1/L2/L3 AI-facing project documentation for medium and large code repositories |

## GEB Project Doc System

`geb-project-doc-system` helps AI coding agents understand a repository progressively:

- **L1 root guide**: `AGENTS.md` / `CLAUDE.md`
- **L2 folder guide**: module boundaries, files, dependencies, local rules
- **L3 file header**: short `Input / Output / Pos` coordinates for source files

The goal is simple: read the map before reading the whole world.

## Quick Start

Audit a repository:

```bash
python3 skills/geb-project-doc-system/scripts/audit_geb_docs.py /path/to/repo
```

Preview missing file headers:

```bash
python3 skills/geb-project-doc-system/scripts/update_file_headers.py /path/to/repo --json
```

Apply headers after reviewing the dry run:

```bash
python3 skills/geb-project-doc-system/scripts/update_file_headers.py /path/to/repo --apply
```

Install the pre-commit hook:

```bash
skills/geb-project-doc-system/scripts/install_git_hook.sh /path/to/repo
```

## Installation

Install into common local agent skill directories and append a short trigger rule to existing global rule files:

```bash
scripts/install_geb_project_doc_system.sh --dry-run
scripts/install_geb_project_doc_system.sh
```

Or link the Skill manually:

```bash
ln -sfn "$(pwd)/skills/geb-project-doc-system" ~/.codex/skills/geb-project-doc-system
ln -sfn "$(pwd)/skills/geb-project-doc-system" ~/.claude/skills/geb-project-doc-system
ln -sfn "$(pwd)/skills/geb-project-doc-system" ~/.grok/skills/geb-project-doc-system
```

Then add a short global rule to `AGENTS.md` / `CLAUDE.md`:

```md
Repository work follows the GEB project documentation standard by default.
Before structural changes, read L1/L2/L3. After structural changes, update
L3 -> L2 -> L1. Use the `geb-project-doc-system` Skill for initialization,
audit, or migration.
```

Keep global prompts short. Load the Skill when detail is needed.

## Validation

```bash
scripts/check_skill_structure.sh skills/geb-project-doc-system
python3 tests/test_geb_project_doc_system.py
tests/smoke_visual_ppt_deck_builder.sh
```

## Acknowledgements and License Boundaries

`geb-project-doc-system` is inspired by Zhao Chunxiang's public discussion of the GEB fractal documentation idea, especially the layered map of L1 root guides, L2 folder guides, and L3 `Input / Output / Pos` file headers.

The implementation also learned from these open-source projects:

- [`Claudate/project-multilevel-index`](https://github.com/Claudate/project-multilevel-index) — MIT License, useful as a reference for full L1/L2/L3 automation.
- [`longranger2/project-doc-bootstrap`](https://github.com/longranger2/project-doc-bootstrap) — MIT License, useful as a reference for `CLAUDE.md` / `AGENTS.md` skill packaging.

The first version of `geb-project-doc-system` is an independent implementation. It is not an official release from those projects and is not endorsed by Zhao Chunxiang or the referenced repositories. If future versions copy, adapt, or merge third-party code, the original copyright notices and license texts must be preserved and the source must be documented in the changelog or release notes.

## License

MIT. See [LICENSE](LICENSE).
