# wxops — 公众号多账号编辑部插件

一个人的编辑部：人是主编，插件是编辑部。覆盖公众号运营全环节——账号、数据、选题、写作、配图、发布、复盘——自动化推进到"最后负责时刻"为止：**草稿入箱，人点发布；人设改动，人来确认。**

## 三层模型（本插件的宪法）

| 层 | 是什么 | 住哪 |
|---|---|---|
| 通用引擎 | 动作：拉数据/分析/写作/发布的代码与 agents 提示词，一份跑所有号 | 插件 `scripts/` + `agents/`（只读） |
| 赛道知识 | 题材分类、爆款词表、标题公式（`niche.json`）+ 文体结构契约（`structure.md`） | `niches/` 数据包（内置 ai-tools / _generic；用户包放 `~/.wxops/niches/` 覆盖） |
| 账号身份 | 登录态 + 凭证 + 人设 persona + 数据 | `~/.wxops/accounts/<slug>/`（永不入库） |

判据一句话：通用的是动作，赛道的是知识，账号的是身份。

## 八个工位

`skills/` 下每站一个 skill，调用名 `/wxops:<站名>`：

| 工位 | 状态 | 职责 |
|---|---|---|
| desk 总控台 | ✅ P1 | 跨账号流水线状态 + 在途内容 + 下一步建议 |
| accounts | ✅ P1 | 加号/列表/切换/退休/迁移/按号登录 |
| analyze | ✅ P1 | 拉数据 → 诊断报告 → 叙事看板（P6 起看板运行时加载，可在多个号之间切换） |
| topics | ✅ P4 | 报告信号 + 赛道矩阵 +（可选）niche-scout 调研 → 选题卡 |
| write | ✅ P4 | 三件套开工制（`wxops kit` 门禁）→ 初稿 → 审计 → 标题 → 人终审 |
| illustrate | ✅ P4 | 封面 900×383 + 正文图；通路可插拔（AI 生成/人工供图） |
| publish | ✅ P5 | dry-run 先行 → 渲染 → 网关上传 + 建草稿 → **草稿箱止步**；凭证按账号隔离 |
| review | ✅ P5 | 发布后对照选题卡预期出达成/偏差结论 → persona/niche 修订**建议**（人拍板） |

写作产线四 agents（`agents/`）：niche-scout 情报侦察 / draft-writer 初稿执笔 / style-auditor 人设审计（对抗镜头）/ title-smith 标题候选。提示词零账号零赛道知识——身份与知识按三层模型在运行时喂入。派单契约与写权限表见 `references/agents-guide.md`（`agents/` 下所有 .md 都会被插件校验器当 agent 扫描，L2 文档只能住 references）。

## 目录结构

```
plugins/wxops/
├── .claude-plugin/plugin.json   # 插件清单
├── skills/                      # 八工位 SKILL.md
├── agents/                      # 写作产线四 agents（niche-scout/draft-writer/style-auditor/title-smith）
├── scripts/                     # Python 引擎（cli/fetch/analyze 自旧 skill 迁入；publish/ 复制自 hermes 带来源头注）
├── niches/                      # 内置赛道包（niche.json 词表 + structure.md 结构契约；ai-tools / _generic）
├── templates/                   # 用户侧模板（persona / evidence-pack / topic-card / niche 词表包）
├── tests/  fixtures/            # 引擎测试与演示数据
├── dashboard/                   # 看板模板（构建时复制到账号目录）
├── references/  DATA_CONTRACT.md
├── README.md                    # 本文件：产品是什么（面向用户的 L1）
└── AGENTS.md                    # 怎么在这棵子树里干活、什么不能碰（面向 agent 的 L1）
```

各目录有自己的 `AGENTS.md`（L2），每个源文件顶部有 `# GEB-L3` 头——按 L1 → L2 → L3 逐级展开，不必全仓扫描。

运行态一律在 `~/.wxops/`（可用 `WXOPS_HOME` 覆盖），布局见 `skills/accounts/SKILL.md`。

## 快速上手

```bash
scripts/wxops accounts add maizong --name "麦总玩AI"   # 或老用户: scripts/wxops migrate
scripts/wxops login --account maizong
scripts/wxops analyze --account maizong
scripts/wxops desk                                     # 随时看全局
```

零依赖试跑：`scripts/wxops analyze --demo --data-only`。

从 npm 包 `create-wechat-ops-skill` 装过单账号老技能的，升级路径见 [packages/create-wechat-ops-skill/MIGRATION.md](../../packages/create-wechat-ops-skill/MIGRATION.md)——`wxops migrate` 是 copy-first 的，源目录一个字节不动。

## 红线

- 不自动点「发布/群发」——自动化止步草稿箱
- 凭证/登录态/账号数据永不入库（`credentials/` 0600）
- 同账号浏览器 profile 并发互斥；多账号拉数逐号顺序，严禁并行
- 看板任何位置不渲染置信度数字（置信度内化契约）
- 迁移/清理一律 copy-first，源文件保留由人处置

## 开发

- 测试：插件根 `python3 -m pytest tests/ -q`
- 校验：`claude plugin validate ./plugins/wxops --strict`
- 本地热加载：`~/.claude/skills/` 下软链本目录，`/reload-plugins` 生效
- 上游冻结源：`skills/wechat-ops-performance-review/`（npm 老用户继续用，只读；演进都在本插件）
- 台账：epic #38，分期 #39-#44
