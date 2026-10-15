# 交接契约（A 侧）：读什么、怎么退回

对应文件：`content-blueprint/references/blueprint-template.md`。两边必须一致。改契约时两边同时改。

## 1. A 读什么

| 文件 | 位置 | A 用哪些字段 |
|---|---|---|
| `blueprint.md` | `01-内容规划/` | front matter：`title` `one_line` `gear_suggestion` `audience.use_mode` `audience.language` `delivery`；每章：`id` `heading` `outcome_ids` `pattern` `claims` `new_terms` `blocks` `screens` `fold` `checkpoint` `stage`；每个 block：`shape` `form` `title` `claims` `budget` `mobile` `twin` |
| `evidence-index.md` | `01-内容规划/` | 断言 ID、原话、类型、来源、定位、日期、可信度，用来渲染标记与脚注 |
| `glossary.md` | `01-内容规划/` | 首选词、一句话定义、首次出现章节，用来渲染 `dfn` |
| `audience-outcomes.md` | `01-内容规划/` | 结果清单，用来写章末检查点与顶部摘要 |
| `handoff-log.md` | `01-内容规划/` | 双方的来往记录 |

A 不读原始资料。页面上的每个数字、每句断言都来自 `evidence-index.md`。A 发现蓝图没覆盖的内容，不自己补，退回 B。

## 2. 进入 A 的门禁

蓝图满足以下条件 A 才开工。不满足时写 `handoff-log.md`，类型 `incomplete`：

1. front matter 字段齐全。
2. 每章有 `claims`，且每个 ID 在 `evidence-index.md` 里存在。
3. 每个 block 的 `form` 是允许值之一：`text` `table` `compare` `timeline` `metric` `chart` `diagram` `figure3d` `exploded`。
4. 每个非 `text` 的 block 有 `budget` 数值（节点数、行列数、序列数、字数）。
5. 每章 `screens` 为 1 到 3。
6. `gear_suggestion` 为 `clear` `mixed` `show` 之一。

## 3. 退回类型

| 类型 | 触发条件 | A 必须附 |
|---|---|---|
| `over_budget` | 图超节点、箭头、泳道、时间线上限；表格超 7 列；章节超 3 屏 | 实际数、上限、建议拆法 |
| `wont_fit` | 内容在 390px 或 1440px 下放不下（标题超 2 行、标签超 12 字、同屏字号超 4） | 截图编号、超出多少 |
| `form_mismatch` | 蓝图指定的形式画不出该内容（例如数据不足 3 点却要折线图） | 建议的形式 |
| `missing_source` | 页面需要的数字或断言没有证据 ID | 位置、所需内容 |
| `term_conflict` | 同一概念在蓝图里有两个词，或术语表缺词 | 两处位置 |
| `incomplete` | 第 2 节门禁未过 | 缺哪一项 |
| `gear_conflict` | A 认为档位与读者使用方式不符 | 理由；最终由用户裁决 |

## 4. 退回条目格式

写入 `01-内容规划/handoff-log.md`，追加，不改旧条目：

```
### F<三位序号> · <类型> · <日期> · 发自 A
- 章节：<id>
- 位置：<元素或截图编号>
- 实际 / 上限：<数值>
- 建议：<一句>
- 状态：待 B 处理
```

B 处理后在同一条目下追加：

```
- B 回复（<日期>）：调整 | 保留并说明 | 需用户裁决
- 变更：<改了蓝图哪一字段>
- 状态：已处理 | 待用户
```

## 5. A 的产出回传给 B 的字段

页面完成后，A 在 `handoff-log.md` 末尾追加一条 `delivered`：页面路径、档位、每章实际屏数、每张图的实际节点数、未渲染的断言 ID（若有）。B 据此更新蓝图的 `screens` 实际值。
