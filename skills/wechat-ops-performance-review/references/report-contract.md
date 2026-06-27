# 报告输出契约 v2

## 设计哲学

**总分总。** 先一句总判断，再逐维度下钻，最后收口成行动板。这是决策报告，不是图表墙——字少、图文、强引导，看完就知道下一步做什么。

## 三层结构

### 总 · 开篇 `top_conclusion`

全局唯一的核心判断，取代冗长的 headline + subheadline。风格：**判断 + 行动指向**。

| 字段 | 格式 | 字数上限 |
| --- | --- | --- |
| `verdict` | 一句核心判断，陈述句 | 8 |
| `next_action` | 下一步行动，以 `→ ` 引导 | 24 |

措辞受**全局**置信度调制（见 [confidence-internalization.md](confidence-internalization.md)）。

示例：`verdict="稳定底盘没起来"` / `next_action="→ 抬中位阅读、拆开管理三件事"`

### 分 · 维度下钻 `analysis_sections[]`

固定 9 节，顺序不变：
`overview → content-engine → title-structure → article-length → audience → timing → evidence → quality → final-synthesis`

每节字段：

| 字段 | 格式 | 字数上限 |
| --- | --- | --- |
| `id` | 维度标识 | — |
| `title` | 维度名 | 8 |
| `question` | 本节回答的问题 | 20 |
| `analysis` | **分析情况**：客观数据观察，陈述事实 | 60 |
| `conclusion` | **得出结论**：可落地判断（措辞受 `voice` 调制） | 40 |
| `action` | 下一步动作 | 30 |
| `chart_payload` | 图表数据 | dict |
| `voice` | 措辞档（internal 派生，驱动文案语气） | — |
| `emphasis` | 视觉权重 `hero`/`primary`/`secondary` | — |
| `action_basket` | `now`/`experiment`/`hold` | — |
| `ui_slot` | 渲染槽位 | — |

**不再有裸 `confidence` 字段**：原 level/score/sample_size 等移入 `_internal`（见下）。每节是"分析情况 + 得出结论"二段式——先讲数据看到什么，再讲该怎么判断。

### 总 · 收口 `final_synthesis`

由各 section 的 `action_basket` **自动归集**成三篮子，不手工硬编码：

| 篮子 | 含义 | 每条上限 |
| --- | --- | --- |
| `now` | 现在就做（高置信结论的动作） | 25 |
| `experiment` | 小步验证（中置信） | 25 |
| `hold` | 暂不拍板（低置信） | 25 |

## 内部信号 `_internal`

置信度原始数据（`score`/`sample_size`/`completeness`/`distribution_skew`/`reasons`）放 `_internal` 子树，供 validate 校验与调试。

**渲染层（dashboard）与 markdown 报告绝不输出这些。** 页面任何位置不得出现"置信度""高/中/低置信""score""N% 可信"等字样。置信度只通过措辞、视觉层级、行动分档**隐性**传达。

## 校验 `validate_dataset`（强制）

1. 各字段字数 ≤ 上限（超限报错）。
2. 渲染文案正则扫描，无"置信度"等字样。
3. 每 section 都有 `voice` / `emphasis` / `action_basket`。
4. section 顺序与上方固定顺序一致。
5. `top_conclusion.verdict` / `next_action` 非空且符合字数。

## 数据隔离

dashboard 只读 build 生成的 `report.json`，绝不直接调用公众号后台。
