# 交接契约（A 侧）：读什么、怎么退回

对应文件：`content-blueprint/references/blueprint-template.md`。两边必须一致。改契约时两边同时改。

## 0. 四阶段对照

`design-pipeline` 调用本 skill 时，按下表只做当前阶段对应的步骤。步骤编号见 `SKILL.md` 第 4 节。

| design-pipeline 阶段 | 本 skill 步骤 | 读的蓝图字段 |
|---|---|---|
| 1 内容蓝图 | 无。由 `content-blueprint` 完成 | 产出 `blueprint.md` 与交付包清单里的其他文件 |
| 2 视觉氛围 | 步骤 1 定氛围与预算（氛围以 design.md 第 1 节为准），步骤 2 写设计计划 | `reader_mode` `audience.use_mode` `stage`，职责卡“视觉重量” |
| 3 组件创意 | 步骤 2 角色表，步骤 3 静态搭建 | 每章 `pattern` `blocks` `screens` `fold`，`image_needs` |
| 4 design.md | 步骤 4 动效层，步骤 5 门禁，步骤 6 截图自检，步骤 7 评审，步骤 8 报告 | 每个 block 的 `shape` `form` `budget` `mobile` `twin`，职责卡“离开时必须做到” |

## 1. A 读什么

| 文件 | 位置 | A 用哪些字段 |
|---|---|---|
| `blueprint.md` | `01-内容规划/` | front matter：`title` `one_line` `reader_mode` `audience.use_mode` `audience.language` `delivery`；产品层：根本目标、工作故事、职责卡；每章：`id` `heading` `outcome_ids` `pattern` `claims` `new_terms` `blocks` `screens` `fold` `checkpoint` `stage` `image_needs`；每个 block：`shape` `form` `title` `claims` `budget` `mobile` `twin` |
| `evidence-index.md`，或 `blueprint.md` 附录 | 路径以 design.md 第 0 节“交付包清单”为准，默认 `01-内容规划/` | 断言 ID、原话、类型、来源、定位、日期、可信度，用来渲染标记与脚注 |
| `glossary.md`，或 `blueprint.md` 附录 | 同上 | 首选词、一句话定义、首次出现章节，用来渲染 `dfn` |
| `audience-outcomes.md`，或 `blueprint.md` 附录 | 同上 | 结果清单，用来写章末检查点与顶部摘要 |
| `handoff-log.md` | `01-内容规划/` | 双方的来往记录 |

A 不读原始资料。页面上的每个数字、每句断言都来自证据索引（独立文件或蓝图附录）。A 发现蓝图没覆盖的内容，不自己补，退回 B。

产品层与新字段的读法（字段定义见 `content-blueprint/references/blueprint-template.md` 第 1.1 节）：

| 蓝图内容 | A 在哪一步用 | 怎么用 |
|---|---|---|
| `stage: yes` | 阶段 2 方向单、设计计划第 2 节 | 进舞台幕表候选。A 从中选舞台区，未选的章写理由 |
| `stage: no` | 同上 | 默认安静区。A 改成舞台区时写理由 |
| `image_needs` | 阶段 3 资产清单 | 每项一行。A 按 `kind`（`data` / `mechanism` / `atmosphere`）定做法与风格：生成图像按 `design-pipeline/references/asset-generation.md` 写提示词，或自绘 SVG |
| 职责卡"视觉重量" | 阶段 3 页面规划、设计计划第 6 节 | 主角章分配舞台预算，背景章只做阅读 |
| 职责卡"唯一主任务""离开时必须做到" | 阶段 3 首屏、阶段 4 验收 | 首屏对照首屏卡。验收时逐章核"离开时必须做到" |
| 职责卡"禁止出现" | 阶段 4 验收 | 截图里出现即为问题，修后再交 |

A 不改职责卡。A 认为职责卡与预算预设冲突时，按第 3 节写 `gear_conflict`。

舞台章占比由 B 在 design.md 阶段 1、2 决定（默认值与适用条件见 `design-pipeline/references/restraint.md`），A 的门禁只查字段存在。

## 2. 进入 A 的门禁

蓝图满足以下条件 A 才开工。不满足时写 `handoff-log.md`，类型 `incomplete`：

1. front matter 字段齐全。
2. 每章有 `claims`，且每个 ID 在证据索引里存在（独立文件或蓝图附录，以交付包清单为准）。
3. 每个 block 的 `form` 是允许值之一：`text` `table` `compare` `timeline` `metric` `chart` `diagram` `figure3d` `exploded`。
4. 每个非 `text` 的 block 有 `budget` 数值（节点数、行列数、序列数、字数）。
5. 每章 `screens` 为 1 到 3。
6. `reader_mode` 为 读、读看、看 之一。
7. 每章有 `stage` 字段，值为 `yes` 或 `no`。

## 3. 退回类型

| 类型 | 触发条件 | A 必须附 |
|---|---|---|
| `over_budget` | 图超节点、箭头、泳道、时间线上限；表格超 7 列；章节超 3 屏 | 实际数、上限、建议拆法 |
| `wont_fit` | 内容在 390px 或 1440px 下放不下（标题超 2 行、标签超 12 字、同屏字号超 4） | 截图编号、超出多少 |
| `form_mismatch` | 蓝图指定的形式画不出该内容（例如数据不足 3 点却要折线图） | 建议的形式 |
| `missing_source` | 页面需要的数字或断言没有证据 ID | 位置、所需内容 |
| `term_conflict` | 同一概念在蓝图里有两个词，或术语表缺词 | 两处位置 |
| `incomplete` | 第 2 节门禁未过 | 缺哪一项 |
| `gear_conflict` | A 认为预算预设与读者使用方式不符 | 理由；最终由用户裁决 |

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

页面完成后，A 在 `handoff-log.md` 末尾追加一条 `delivered`：页面路径、预算预设、每章实际屏数、每张图的实际节点数、未渲染的断言 ID（若有）。B 据此更新蓝图的 `screens` 实际值。
