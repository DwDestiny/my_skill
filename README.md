# my_skill

这是老党的 Skill 仓库，用来沉淀、维护和开源高价值 Codex Skills。仓库先追求两件事：结构清楚、后续新增不乱。

## Skill 目录

| Skill | 路径 | 状态 | 适用场景 |
|---|---|---|---|
| product-expert | `skills/product-expert/` | 已入库 | 从一个产品想法出发，完成需求探知、产品定位、MVP 规划、评分和推荐 |
| visual-ppt-deck-builder | `skills/visual-ppt-deck-builder/` | 已入库 | 从主题、大纲和风格样张出发，生成高视觉质量且可编辑的 PPTX |

新增 Skill 时，必须同步更新这张表。README 是仓库的入口，也是 Skill 总目录。

## 仓库结构

```text
skills/
  product-expert/
    SKILL.md
    agents/openai.yaml
    references/
  visual-ppt-deck-builder/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
docs/
  repository-architecture.md
  skill-intake-checklist.md
templates/
  skill-catalog-entry.md
.github/
  ISSUE_TEMPLATE/
```

## 新增 Skill 的标准流程

1. 先做 Skill 候选确认：适用场景、解决问题、预期收益、计划动作、目标路径。
2. 开工前查重或创建 GitHub issue，写清现象、直接机制、系统设计缺口。
3. 在 `skills/<skill_slug>/` 新建 Skill，目录名使用小写短横线。
4. `SKILL.md` 只放核心触发规则和工作流；长资料放 `references/`。
5. 有稳定脚本、模板或素材时，分别放入 `scripts/`、`assets/`。
6. 更新 README 的 Skill 目录。
7. 运行结构验收，提交并关联 issue。

## 基础验收

每次新增或修改 Skill，至少确认：

- `skills/<skill_slug>/SKILL.md` 存在。
- `SKILL.md` frontmatter 包含 `name` 和 `description`。
- README 的 Skill 目录已更新。
- 没有提交密钥、账号、令牌、私有日志。
- 如新增脚本，脚本有最小可运行验证。

常用本地验收命令：

```bash
scripts/check_skill_structure.sh skills/visual-ppt-deck-builder
tests/smoke_visual_ppt_deck_builder.sh
```

## 当前远程

- GitHub: https://github.com/DwDestiny/my_skill
- 默认分支：`main`
