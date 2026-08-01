# 置信度内化规则

## 原则

置信度是**内部推理过程**，不是展示内容。算出来后，只用来决定三件事——**怎么说、放多大、归哪档**。页面永远不出现"置信度 / 高置信 / 75%"这类字样。

用户看到的是：一个措辞有分寸的结论、一个大小恰当的视觉块、一个归在正确行动篮子里的建议。他不需要知道背后的分数，但能感受到这条结论"有多硬"。

## 置信度怎么算（沿用现有模型）

`confidence_for_records` 基于三个内部信号产出 `level`(high/medium/low) + `score`(0–1)：

- `sample_size`：样本量。样本越少越不可信。
- `distribution_skew`：分布偏度。单个爆款把均值拉高、中位数很低 = 高偏度 = 结论易被误导。
- `completeness`：数据完整度。字段缺失越多越不可信。

这些原始数字写入 `_internal`，**不进入任何渲染输出**。

## 三通道映射

### ① `voice` 措辞分级

| level | 语气 | 模板 |
| --- | --- | --- |
| high | 祈使肯定 | "立即把 X 做成 Y" |
| medium | 建议 | "可以先小范围试 X" |
| low | 谨慎 | "初步迹象显示 X，但样本还不够，值得继续观察" |

`conclusion` 与 `action` 文案的语气由 `voice` 决定。低置信的结论不会用肯定句下死命令。

### ② `emphasis` 视觉层级

| level | 权重 | dashboard 渲染 |
| --- | --- | --- |
| high | `hero` | 大字号、主视觉位、强调色 |
| medium | `primary` | 正常卡片 |
| low | `secondary` | 缩小、弱化、归入次要区 |

高置信结论占据视觉焦点；低置信结论被刻意做小、做淡，读者一眼就知道"这个还不稳"。

### ③ `action_basket` 行动分档

| level | 篮子 |
| --- | --- |
| high | `now` 现在就做 |
| medium | `experiment` 小步验证 |
| low | `hold` 暂不拍板 |

`final_synthesis` 直接消费各 section 的 `action_basket`，自动归集三篮子。

## 落地（build 脚本）

- `voice_for_confidence(confidence)` → 措辞档
- `emphasis_for_confidence(confidence)` → 视觉权重
- `action_basket_for_confidence(confidence)` → 行动篮子
- confidence 原始数字 → `_internal`，validate 可读、渲染层不读

## 红线

页面（dashboard + markdown）任何位置**禁止**出现：
"置信度"、"高/中/低置信"、"score"、"N% 可信"、置信度进度条、置信度百分比。
违反即 validate 失败。
