# 公众号运营内容线总索引(wechat-content-ops-map)

> 这是"公众号"主题在本仓库及关联资产中的唯一索引页。任何 agent 接到公众号相关任务,先读这一页再展开;新增公众号相关资产必须回填本页。
> 更新时间 2026-08-02 · 关联 issue:[#38](https://github.com/DwDestiny/my_skill/issues/38)(epic)、[#36](https://github.com/DwDestiny/my_skill/issues/36)(索引建立)

**现在的主力是 `plugins/wxops/` 插件,不是 `skills/wechat-ops-performance-review/`。** 后者是插件的来源,已冻结只读,仅供 npm 老用户继续使用;所有演进都在插件里做。改错地方是这个主题最容易犯的错。

## 资产地图

```text
公众号运营
├── 工具线(全环节:账号/数据/选题/写作/配图/发布/复盘)
│   ├── plugins/wxops/                          ← ★ 主力:多账号编辑部插件,八个工位
│   ├── skills/wechat-ops-performance-review/   ← 冻结只读:单账号老技能,npm 老用户在用
│   └── packages/create-wechat-ops-skill/       ← npm 分发包(npx 安装上面那个老技能)
├── 内容线(写什么、怎么卖)
│   └── docs/ai-workflow-series-outline.md      ← 付费系列《一个人的 Agent 工程》十篇大纲
├── 知识线(沉淀在仓库外)
│   ├── ~/wiki/concepts/                        ← 选题依据的方法论概念页(6 页,2026-07-27 落档)
│   └── ~/.wxops/                               ← 运行态 workspace(账号/登录态/raw/报告),不入库
└── 治理线
    └── GitHub Issues                            ← 问题单一真源
```

## 工具线 · 主力插件 `plugins/wxops/`

多账号编辑部,八个工位(`/wxops:<站名>`):desk 总控台 / accounts / analyze / topics / write / illustrate / publish / review。宪法是**三层模型**——通用的是动作(引擎代码)、赛道的是知识(niche 数据包)、账号的是身份(`~/.wxops/accounts/<slug>/`)。

| 资产 | 路径 | 说明 |
|---|---|---|
| 产品 L1 | [plugins/wxops/README.md](../plugins/wxops/README.md) | 产品是什么、八个工位、三层模型 |
| agent L1 | [plugins/wxops/AGENTS.md](../plugins/wxops/AGENTS.md) | 怎么在这棵子树里干活、架构不变量、红线 |
| 数据契约 | [DATA_CONTRACT.md](../plugins/wxops/DATA_CONTRACT.md) | 报告字段与置信度内化约定 |
| agents 派单契约 | [references/agents-guide.md](../plugins/wxops/references/agents-guide.md) | 四个写作 agents 的派单与写权限表 |
| L2 层文档 | [cli](../plugins/wxops/scripts/cli/AGENTS.md) · [analyze](../plugins/wxops/scripts/analyze/AGENTS.md) · [fetch](../plugins/wxops/scripts/fetch/AGENTS.md) · [publish](../plugins/wxops/scripts/publish/AGENTS.md) · [dashboard](../plugins/wxops/dashboard/AGENTS.md) · [niches](../plugins/wxops/niches/AGENTS.md) · [templates](../plugins/wxops/templates/AGENTS.md) · [tests](../plugins/wxops/tests/AGENTS.md) | 各模块边界与本地规则 |

## 工具线 · 冻结源与分发

| 资产 | 路径 | 说明 |
|---|---|---|
| 老技能(冻结) | [skills/wechat-ops-performance-review/](../skills/wechat-ops-performance-review/SKILL.md) | 单账号:init/login/analyze;插件的来源,**只读,不许双向同步** |
| npm 分发包 | [packages/create-wechat-ops-skill/](../packages/create-wechat-ops-skill/README.md) | `npx create-wechat-ops-skill` 装的是上面那个老技能;发布凭证在 `~/.npmrc`(2026-09-25 到期) |
| 升级指引 | [MIGRATION.md](../packages/create-wechat-ops-skill/MIGRATION.md) | 老用户 `~/.wxops/` 单账号 → 插件 accounts 模型;`wxops migrate` copy-first,源不动 |

## 内容线

| 资产 | 路径 | 状态 |
|---|---|---|
| 付费系列大纲 | [ai-workflow-series-outline.md](ai-workflow-series-outline.md) | v2(2026-07-27,主线=能力):十篇标题+大纲+定价+排期 |
| 选题数据依据 | `~/.wxops/reports/wechat/publish-records-*.json` | 158 篇实测发布记录(运行态,不入库,分析结论已写入大纲第一节) |
| 爆款调研报告 | `/tmp/ai_workflow_hot_topics.md` | 临时产物;结论已固化进大纲第六节与 wiki 概念页 |

## 知识线(仓库外,`~/wiki/`)

2026-07-27 落档的选题方法论概念页:

- `~/wiki/concepts/AgenticEngineering.md` — Karpathy 2026-02 接替 vibe coding 的范式词
- `~/wiki/concepts/ContextEngineering.md` — 上下文工程(系列第 02 篇的依据)
- `~/wiki/concepts/AskedVsForced.md` — 建议 vs 强制(第 03 篇依据)
- `~/wiki/concepts/SpecDrivenDevelopment.md` — 规格驱动(第 04 篇依据)
- `~/wiki/concepts/LoopEngineering.md` — 循环工程(第 07 篇相关)
- `~/wiki/concepts/HarnessEngineering.md` — harness > 模型(系列总主线依据)

## 治理线(GitHub Issues,单一真源)

| Issue | 主题 | 状态 |
|---|---|---|
| [#38](https://github.com/DwDestiny/my_skill/issues/38) | **epic**:多账号图文编辑部插件,全环节收口 | open |
| [#39](https://github.com/DwDestiny/my_skill/issues/39)–[#44](https://github.com/DwDestiny/my_skill/issues/44) | 分期 P1-P6:骨架/登录态/赛道解耦/内容三站/发布复盘/看板与文档 | #39-#43 closed · #44 本批 |
| [#24](https://github.com/DwDestiny/my_skill/issues/24) | wxops 数据链路缺陷(m4 已修;account/audience/login 三缺口待诊断) | open |
| [#31](https://github.com/DwDestiny/my_skill/issues/31) | build_wechat_ops_report.py 体量大维护成本高 | open |
| [#36](https://github.com/DwDestiny/my_skill/issues/36) | GEB 合规缺口:L3/L2 回填与本索引建立 | closed |
| [#33](https://github.com/DwDestiny/my_skill/issues/33) | 账号类型自动识别(已实现 m9) | closed |

## 边界与铁律

- **自动化止步草稿箱**:任何代码路径都不得调用发布/群发接口。网关客户端只有"上传素材 + 建草稿"两个方法,这是结构性保证。发布键永远留给人。
- `~/.wxops/` 是运行态:账号、登录态、raw 抓取、真实报告,**永不入库**,也不加 GEB 文档。
- 凭证不落任何仓库文件,`credentials/` 权限 0600,值不打印、不进日志、不进报错。
- 真实发布记录(含阅读/点赞数据)属账号隐私,fixtures 一律用构造数据。
- 爬虫只抓自己有管理权的账号;多账号拉数逐号顺序执行,严禁并行(风控)。
- 迁移/清理一律 copy-first,源文件保留由人处置,不许 `mv`、不许直接删。
- 看板任何位置不渲染置信度数字(置信度内化契约)。
