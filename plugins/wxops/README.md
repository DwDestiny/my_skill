# wxops — 公众号多账号编辑部插件

一个人的编辑部：人是主编，插件是编辑部。覆盖公众号运营全环节——账号、数据、选题、写作、配图、发布、复盘——自动化推进到"最后负责时刻"为止：**草稿入箱，人点发布；人设改动，人来确认。**

## 三层模型（本插件的宪法）

| 层 | 是什么 | 住哪 |
|---|---|---|
| 通用引擎 | 动作：拉数据/分析/发布的代码，一份跑所有号 | 插件 `scripts/`（只读） |
| 赛道知识 | 题材分类、爆款词表、标题公式 | `niches/` 数据包（P3 解耦） |
| 账号身份 | 登录态 + 凭证 + 人设 + 数据 | `~/.wxops/accounts/<slug>/`（永不入库） |

判据一句话：通用的是动作，赛道的是知识，账号的是身份。

## 八个工位

`skills/` 下每站一个 skill，调用名 `/wxops:<站名>`：

| 工位 | 状态 | 职责 |
|---|---|---|
| desk 总控台 | ✅ P1 | 跨账号流水线状态 + 下一步建议 |
| accounts | ✅ P1 | 加号/列表/切换/退休/迁移/按号登录 |
| analyze | ✅ P1 | 拉数据 → 诊断报告 → 叙事看板 |
| topics / write / illustrate | 🚧 P4 | 选题卡 / 三件套写作流 / 配图 |
| publish | 🚧 P5 | 渲染 → 网关 → **草稿箱止步** |
| review | 🚧 P5 | 发布后对照选题卡复盘，回灌人设建议 |

## 目录结构

```
plugins/wxops/
├── .claude-plugin/plugin.json   # 插件清单
├── skills/                      # 八工位 SKILL.md
├── scripts/                     # Python 引擎（cli/fetch/analyze，自旧 skill copy-first 迁入）
├── tests/  fixtures/            # 引擎测试与演示数据
├── dashboard/                   # 看板模板（构建时复制到账号目录）
├── references/  DATA_CONTRACT.md
└── README.md                    # 本文件（L1）
```

运行态一律在 `~/.wxops/`（可用 `WXOPS_HOME` 覆盖），布局见 `skills/accounts/SKILL.md`。

## 快速上手

```bash
scripts/wxops accounts add maizong --name "麦总玩AI"   # 或老用户: scripts/wxops migrate
scripts/wxops login --account maizong
scripts/wxops analyze --account maizong
scripts/wxops desk                                     # 随时看全局
```

零依赖试跑：`scripts/wxops analyze --demo --data-only`。

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
