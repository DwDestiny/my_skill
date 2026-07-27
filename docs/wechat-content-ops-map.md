# 公众号运营内容线总索引(wechat-content-ops-map)

> 这是"公众号"主题在本仓库及关联资产中的唯一索引页。任何 agent 接到公众号相关任务,先读这一页再展开;新增公众号相关资产必须回填本页。
> 更新时间 2026-07-27 · 关联 issue:[#36](https://github.com/DwDestiny/my_skill/issues/36)

## 资产地图

```text
公众号运营
├── 工具线(拿数据、出报告)
│   ├── skills/wechat-ops-performance-review/   ← 核心 skill:抓取 + 9 模块分析 + 看板
│   └── packages/create-wechat-ops-skill/       ← npm 分发包(npx 一键安装上面的 skill)
├── 内容线(写什么、怎么卖)
│   └── docs/ai-workflow-series-outline.md      ← 付费系列《一个人的 Agent 工程》十篇大纲
├── 知识线(沉淀在仓库外)
│   ├── ~/wiki/concepts/                        ← 选题依据的方法论概念页(6 页,2026-07-27 落档)
│   └── ~/.wxops/                               ← 运行态 workspace(登录态/raw/报告),不入库
└── 治理线
    └── GitHub Issues                            ← 问题单一真源
```

## 工具线

| 资产 | 路径 | 说明 |
|---|---|---|
| 核心 skill | [skills/wechat-ops-performance-review/](../skills/wechat-ops-performance-review/SKILL.md) | `wxops` CLI:init/login/analyze;四接口抓取 + m1-m9 分析 + dashboard |
| 数据契约 | [DATA_CONTRACT.md](../skills/wechat-ops-performance-review/DATA_CONTRACT.md) · [report-contract.md](../skills/wechat-ops-performance-review/references/report-contract.md) | 报告字段与数据源约定 |
| 设计文档 | [DESIGN.md](../skills/wechat-ops-performance-review/DESIGN.md) | 分析链路与看板设计 |
| 账号类型手册 | [account-type-playbooks.md](../skills/wechat-ops-performance-review/references/account-type-playbooks.md) | m9 路由后的差异化分析策略 |
| L2 层文档 | [analyze](../skills/wechat-ops-performance-review/scripts/analyze/AGENTS.md) · [cli](../skills/wechat-ops-performance-review/scripts/cli/AGENTS.md) · [fetch](../skills/wechat-ops-performance-review/scripts/fetch/AGENTS.md) · [tests](../skills/wechat-ops-performance-review/tests/AGENTS.md) | 各模块边界与本地规则(2026-07-27 补齐) |
| npm 分发包 | [packages/create-wechat-ops-skill/](../packages/create-wechat-ops-skill/README.md) | `npx create-wechat-ops-skill`;发布凭证在 `~/.npmrc`(2026-09-25 到期) |

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
| [#36](https://github.com/DwDestiny/my_skill/issues/36) | GEB 合规缺口:L3/L2 回填与本索引建立 | open(本批) |
| [#24](https://github.com/DwDestiny/my_skill/issues/24) | wxops 数据链路缺陷(m4 已修;account/audience/login 三缺口待诊断) | open |
| [#33](https://github.com/DwDestiny/my_skill/issues/33) | 账号类型自动识别(已实现 m9) | closed |

## 边界与铁律

- `~/.wxops/` 是运行态:登录态、raw 抓取、真实报告,**永不入库**,也不加 GEB 文档。
- 真实发布记录(含阅读/点赞数据)属账号隐私,fixtures 一律用构造数据。
- 爬虫只抓自己有管理权的账号。
- token 等凭证不落任何仓库文件;导出物 URL 先脱敏。
