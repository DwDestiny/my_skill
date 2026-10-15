# 蓝图模板与交接契约（B 侧）

A 侧对应文件：`visual-motion-design/references/handoff.md`。改契约两边同改。

## 1. `blueprint.md` 结构

```markdown
---
title: <页面名，2 到 12 字>
one_line: <一句话：给谁看、看完能做什么>
version: 0.1
date: YYYY-MM-DD
delivery: local-html | artifact | other
language: zh-CN
audience:
  who: <一句话>
  use_mode: [速读, 翻查]        # 速读 / 翻查 / 学习 / 体验，主次排序
  device: [desktop, mobile]
gear_suggestion: clear          # clear | mixed | show
style_quotes:                   # 用户关于风格的原话，逐字；没有则留空数组
  - "<原话>"
outcomes: [O1, O2, O3]
sources_file: evidence-index.md
glossary_file: glossary.md
credibility_legend: "高=官方原文；中=媒体转述；低=厂商自述；未验证=未读到原文"
notes: <与用户原话冲突的处理、口径差异等>
---

# <title>

## 顶部摘要
- <要点 1> [C001] 事实 · 中
- <要点 2> [C014] 判断
- <要点 3> [C030] 缺口

## 章节

### s1 · <论点句标题，≤25 字>
- id: s1
- outcome_ids: [O1]
- pattern: 答案先行
- intro: <导语 1 到 3 句，可空>
- claims: [C001, C002, C005]
- new_terms: [设计院, 工程总承包]
- blocks:
  - block: s1-1
    shape: 多对象 × 多属性
    form: table
    title: <一句结论>
    claims: [C001, C002]
    budget: rows=4, cols=3
    mobile: 堆叠
    twin: 无（本身是表）
  - block: s1-2
    shape: 单个判断
    form: text
    claims: [C005]
- fold: [C006, C007]            # 放进折叠的断言
- screens: 2                    # 预计屏数，1 到 3
- checkpoint: 读完这节你能说出 2025 年设计收入与变化方向
- stage: no                     # yes 表示 B 认为此章可作舞台区候选，由 A 决定

### s2 · …

## 信息缺口
- id: gaps
- claims: [C030, C031]

## 信息架构
- 导航：目录，显示当前位置
- 折叠清单：<章节 id → 断言 ID>
- 附录：来源表、术语表、口径差异
- 可信度图例位置：顶部摘要之后
- 速读通道检查：通过 / 未通过（原因）

## 章节到结果对照
| 章节 | 结果 |
|---|---|
| s1 | O1 |

## 删除清单
| 断言 | 原因 |
|---|---|
| C012 | 不挂任何结果 |
```

## 2. A 开工的门禁（B 自检同一清单）

1. front matter 字段齐全。
2. 每章 `claims` 的每个 ID 在 `evidence-index.md` 里存在。
3. 每个 block 的 `form` 是允许值之一。
4. 每个非 `text` 的 block 有 `budget` 数值。
5. 每章 `screens` 为 1 到 3。
6. `gear_suggestion` 为三值之一。

## 3. A 的退回类型

| 类型 | 含义 | B 的典型处理 |
|---|---|---|
| `over_budget` | 图或表超预算 | 拆章、拆图、改表 |
| `wont_fit` | 在 390px 或 1440px 放不下 | 缩标题、拆块、移折叠 |
| `form_mismatch` | 指定形式画不出 | 改 form |
| `missing_source` | 页面需要的内容没有证据 ID | 补登记或改为缺口 |
| `term_conflict` | 术语不一致或缺词 | 改术语表与蓝图 |
| `incomplete` | 门禁未过 | 补字段 |
| `gear_conflict` | A 认为档位不符 | 写理由，交用户裁决 |

## 4. `handoff-log.md` 条目格式

B 发出：

```
### R<三位序号> · ready · <日期> · 发自 B
- 蓝图版本：0.1
- 章数 / 断言数 / 建议档位：…
- 状态：待 A 确认
```

A 退回与 B 回复（追加，不改旧条目）：

```
### F<三位序号> · <类型> · <日期> · 发自 A
- 章节：<id>
- 位置：<元素或截图编号>
- 实际 / 上限：<数值>
- 建议：<一句>
- 状态：待 B 处理
- B 回复（<日期>）：调整 | 保留并说明 | 需用户裁决
- 变更：<蓝图字段与新版本号>
- 状态：已处理 | 待用户
```

A 交付：

```
### D<三位序号> · delivered · <日期> · 发自 A
- 页面：<路径>
- 档位：…
- 每章实际屏数：s1=2, s2=1 …
- 每图实际节点数：…
- 未渲染断言：无 | [C0xx]
```

## 5. 版本规则

1. 蓝图每次改动升小版本（0.1 → 0.2）。
2. 结果或章节结构变化升中版本（0.x → 1.0）。
3. 旧版本不删，改名为 `blueprint-v0.1.md` 归档，或靠 git 历史。
