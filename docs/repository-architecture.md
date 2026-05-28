# 仓库架构规范

## 设计原则

- 一个 Skill 一个目录，避免多个 Skill 混在一起。
- Skill 本体保持精炼，长资料外置到 `references/`。
- README 只做仓库入口和 Skill 总目录，不替代每个 Skill 的 `SKILL.md`。
- 所有项目治理问题先进入 GitHub issue，再进入实现。

## 目录职责

### `skills/`
存放可被安装、复制或开源的 Skill 本体。每个子目录都是一个独立 Skill。

必填：
- `SKILL.md`：Skill 的唯一必填入口，必须包含 `name` 和 `description`。

推荐：
- `agents/openai.yaml`：展示名、短描述、默认提示词等 UI 信息。

可选：
- `references/`：长方法论、模板说明、评分规则、API 资料等。
- `scripts/`：稳定、重复、容易出错的自动化脚本。
- `assets/`：模板、图标、示例素材等。

### `docs/`
存放仓库级规范、入库流程、验收清单和协作说明。这里服务仓库维护者，不作为 Skill 运行时上下文。

### `templates/`
存放新增 Skill 时可复用的小模板，例如 README 目录条目、issue 草稿结构。

### `.github/ISSUE_TEMPLATE/`
存放 GitHub issue 模板，确保每次新增 Skill 都有可追溯的背景、价值和验收标准。

## 命名规范

- Skill 目录：小写短横线，例如 `product-expert`。
- Skill frontmatter 的 `name`：与目录名保持一致。
- 文档文件：小写短横线，例如 `skill-intake-checklist.md`。
- 代码变量和脚本内部命名：小写下划线。

## README 目录规则

新增 Skill 时必须更新 README 的 `Skill 目录` 表格，至少包含：
- Skill 名称
- 路径
- 状态
- 适用场景

README 不写长篇方法论，只承担“入口”和“索引”职责。
