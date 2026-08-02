---
name: review
description: Use when 复盘、文章数据回看、对照选题预期、总结发布效果, or comparing published-article metrics against the topic card's expectations and turning findings into persona/niche revision suggestions for human approval.
---

# review — 复盘工位

## 核心原则

- **对照选题卡，不是看个热闹**：复盘的锚点是选题卡当初写下的预期（完读率/阅读/转发钩子）——达成还是偏差，偏差多少，为什么
- **建议止步于建议**：复盘结论可以转成 persona.md / niche 包的修订建议，但本站**绝不代改**这两类文件——人设与赛道知识的每一笔改动都要人拍板后由人（或人授意的主控）落笔
- **数据没就绪就如实说**：文章刚发、analyze 数据还没覆盖到，就报「数据未就绪，T+N 后再来」，不拿旧数据凑数、不编数字

## 前置

| 件 | 说明 |
|---|---|
| 发布台账 | `accounts/<slug>/published/<topic-slug>.json` 存在（publish 站产物）——没发布过就没有复盘 |
| 选题卡 | `accounts/<slug>/topics/<topic-slug>/card.md`（预期指标段） |
| 新鲜数据 | 先跑 `wxops analyze --account <slug>` 拉最新文章数据；报告日期要晚于发布日 |

## 流程

### 1. 确认数据新鲜

发布后建议 T+3 起复盘（前 72 小时数据未定型）。先看 desk 或直接跑 analyze 更新数据。

### 2. 生成复盘报告

```bash
cd <插件根> && scripts/wxops review --account <slug> --topic <topic-slug>
```

报告落 `accounts/<slug>/reports/review-<topic-slug>.md`，包含：

- **基本面**：草稿创建时间（实际群发时间以后台为准）、标题、图片数
- **对照表**：选题卡预期 vs 实际（阅读/完读率/在看/转发，以 analyze 数据为准）
- **结论**：达成 / 部分达成 / 偏差，逐项写差多少
- **修订建议**（如有）：哪条经验值得进 persona（口吻/标题公式/结构）或 niche 包（题材矩阵/结构契约）——标注「建议，待主编确认」

找不到该文章的数据时，报告如实写「数据未就绪」并给出建议重跑时间。

### 3. 陪用户读报告

把达成/偏差结论念清楚，和用户讨论归因：是选题问题（预期定错）、内容问题（标题/开头/结构）、还是分发问题（发布时段/封面）。归因讨论是人机协作段——数据是你的，判断是用户的。

### 4. 修订建议的去向

用户对某条建议点头后：

- persona.md 的改动：主控当场改（基础设施文件），改完把 diff 念给用户
- niche 包的改动：同上，注意用户包在 `~/.wxops/niches/`、内置包在插件目录（内置包改动走 git 流程）
- 用户没点头的建议：留在报告里，下次复盘还能看到——不催、不重复推销

## 红线

- `wxops review` 命令与本站流程**绝不直接写** persona.md / niche 包——建议在报告里，落笔要人点头
- 不编造数据：analyze 里没有的数字，报告里不出现
- 复盘结论只对照本号自己的基线与选题卡预期，不拿别号数据攀比
