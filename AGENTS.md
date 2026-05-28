# my_skill 项目协作规则

## 语言与沟通
- 默认使用中文简体沟通、写文档和写注释。
- 先说结论，再说原因和下一步；少堆术语，必要时把技术细节翻译成人话。
- 用户可称呼为“老党”，语气自然、直接、有判断。

## 项目定位
- 本仓库用于沉淀、维护和开源高价值 Codex Skills。
- 每个 Skill 必须能独立解释自己的触发场景、工作流、资源依赖和验收方式。
- 仓库级 README 负责做 Skill 总目录；新增、删除、改名 Skill 时必须同步更新 README 的 Skill 目录表。

## 固定目录
```text
skills/                      # Skill 本体，每个子目录一个 Skill
  <skill_slug>/
    SKILL.md                 # 必填，含 name 和 description frontmatter
    agents/openai.yaml        # 推荐，面向 UI 的展示信息
    references/               # 可选，按需加载的长参考资料
    scripts/                  # 可选，可执行的稳定脚本
    assets/                   # 可选，模板、图标、示例素材等
docs/                         # 仓库规范、入库流程、验收清单
templates/                    # 新 Skill 或目录索引用模板
.github/ISSUE_TEMPLATE/       # GitHub issue 模板
```

## 新增 Skill 流程
1. 先确认 Skill 候选：适用场景、解决问题、预期收益、计划动作、目标路径。
2. 未获用户明确确认前，不创建或更新 Skill 文件。
3. 开工前先查重 GitHub issue；没有合适 issue 时，先创建或起草 issue。
4. 新 Skill 默认放在 `skills/<skill_slug>/`，目录名使用小写短横线。
5. `SKILL.md` 必须保持精炼，只放触发规则和核心工作流；大段方法论放到 `references/`。
6. 如需稳定、重复、易出错的操作，优先放入 `scripts/`，不要让模型每次临场重写。
7. 完成后必须更新 README 的 Skill 目录，并补充必要的规范文档或验收说明。

## 质量门禁
- 涉及代码或脚本变更时，先写测试或最小验证，再实现。
- 每次修改后至少做结构检查：确认 `SKILL.md` 存在、frontmatter 有 `name` 和 `description`、README 目录已同步。
- 如项目配置了测试、格式化或静态检查，提交前必须运行。
- 不把密钥、账号、令牌、私有日志放进仓库。

## Git 与 GitHub
- 使用 Git 管理版本，GitHub 作为远程仓库。
- 默认分支为 `main`。
- 提交信息用中文，说明“做了什么”和“为什么”。
- 任何问题治理默认以 GitHub issue 为单一台账：查重、记录根因链、关联提交和关闭。

## Wiki 维护
- 本项目相关的调研、查询、结构决策和新增知识，结束前维护到 `/Users/dw/wiki/`。
- 维护失败时必须明说失败原因，不静默跳过。

## Skill 候选确认协议
识别到高价值知识点时，主动向用户发起确认，内容必须包含：
- 适用场景
- 解决问题
- 预期收益
- 计划动作：新建或更新
- 目标路径

未获得明确确认前，只记录候选结论，不落盘。
