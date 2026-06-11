# GEB 项目文档系统 Skill 落地计划

关联 issue: https://github.com/DwDestiny/my_skill/issues/5

## 目标

新增并开源 `geb-project-doc-system` Skill，让大中型代码仓库用 L1 根文档、L2 目录文档、L3 文件头形成可被 Agent 稳定读取和审计的项目地图。

## 任务包

### 任务 1：结构检查基线修正

- 目标：让仓库结构检查与 README 规则一致，`references/` 和 `scripts/` 是推荐/可选资源，不应让无脚本 Skill 失败。
- 文件范围：`scripts/check_skill_structure.sh`
- TDD：先运行现有 `product-expert` 结构检查观察失败，再修正脚本，重新验证 `product-expert`、`visual-ppt-deck-builder`、新 GEB Skill。
- 验收：三个 Skill 的结构检查均通过。

### 任务 2：GEB 审计脚本

- 目标：提供确定性 dry-run 审计，检查 L1/L2/L3、重复文件头、过长文件头和覆盖率。
- 文件范围：`skills/geb-project-doc-system/scripts/audit_geb_docs.py`
- TDD：先写 `tests/test_geb_project_doc_system.py` 覆盖缺失 L1、缺失 L3、重复 L3、目录 L2 阈值。
- 验收：`python3 -m unittest tests/test_geb_project_doc_system.py` 通过。

### 任务 3：GEB 文件头更新脚本

- 目标：默认 dry-run，显式 `--apply` 才写入；重复运行不重复插入。
- 文件范围：`skills/geb-project-doc-system/scripts/update_file_headers.py`
- TDD：测试 dry-run 不改文件、apply 插入文件头、二次 apply 幂等。
- 验收：unittest 通过，手动在临时项目中验证。

### 任务 4：Skill 文档与 references

- 目标：按 Skill 最佳实践创建轻量 `SKILL.md`、UI metadata、规范、模板、迁移流程、审计规则、压力场景。
- 文件范围：`skills/geb-project-doc-system/`
- 验收：`scripts/check_skill_structure.sh skills/geb-project-doc-system` 通过；`SKILL.md` description 只描述触发条件，不总结流程。

### 任务 5：README 中英双语与图文说明

- 目标：重写仓库 README，包含中英双语、架构图、快速开始、安装、触发策略、验证命令和 Skill 目录。
- 文件范围：`README.md`、`docs/assets/geb-project-doc-system-architecture.svg`
- 验收：README 可在 GitHub 渲染；图片使用相对路径；中英信息对齐。

### 任务 6：真实项目试点与本机 Agent 安装

- 目标：用一个真实仓库 dry-run 审计，安装 Skill 到 Codex、Claude Code、Grok/Grok Build 等本机 Agent 可发现目录，并补全局短声明。
- 文件范围：本机 Agent skill 目录与全局规则文件。
- 验收：目标目录存在 `geb-project-doc-system`；全局文档包含短声明；dry-run 输出可复核。

## 不做

- 不把所有历史项目一次性迁移成 GEB。
- 不直接安装第三方 GEB 插件。
- 不用 prompt hook 自动大规模改仓库；首版以 Skill + 脚本审计 + 全局短声明为主。
