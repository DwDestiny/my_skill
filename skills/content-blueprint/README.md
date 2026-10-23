# content-blueprint

**内容与讲解方案。** 把资料和目标拆成一份"蓝图"：读者是谁、读完能做什么、保留什么、按什么顺序讲、每块用什么形式、每条断言的来源与可信度。

它不决定颜色、字号、间距和动效。这些由配对的 [`visual-motion-design`](../visual-motion-design/README.md) 负责。

## 什么时候触发

| 场景 | 例子 |
|---|---|
| 要把资料整理成讲解、学习、汇报、介绍、说明页 | "整理成一页""给人讲清楚" |
| 不确定内容怎么拆、章节怎么排 | "先讲什么后讲什么""哪些该删" |
| 不确定用文字、表还是图 | "用表还是用图" |

不适用：决定视觉与动效；写沟通话术、提问顺序、销售说法；替任何人作承诺；没有资料就凭空编内容。

## 配对方式

1. `content-blueprint` 读资料，产出蓝图文件。
2. `visual-motion-design` 只读蓝图，不读原始资料，搭建 HTML 页面。
3. 视觉侧发现蓝图问题时，在 `handoff-log.md` 追加退回条目。内容侧回复。

| 产物 | 内容 |
|---|---|
| `audience-outcomes.md` | 用户原话、典型读者、可检验的结果 O1… |
| `evidence-index.md` | 断言 C001… 的类型、来源、日期、可信度、反面证据 |
| `glossary.md` | 首选词、禁用同义词、定义、类比、边界 |
| `blueprint.md` | front matter、逐章块、删除清单、信息架构 |
| `handoff-log.md` | 两侧往来记录，只追加不改旧条目 |

退回有 7 种类型：`over_budget`、`wont_fit`、`form_mismatch`、`missing_source`、`term_conflict`、`incomplete`、`gear_conflict`。契约见 `references/blueprint-template.md` 与对侧的 `visual-motion-design/references/handoff.md`。改契约时两边同改。

蓝图里的 `reader_mode` 取 `读`、`读看`、`看` 之一。它只提示读者主要怎么用这页，不是分级。视觉氛围与动效预算由 [`visual-motion-design`](../visual-motion-design/README.md) 在设计阶段决定。

## 目录

```text
content-blueprint/
├── SKILL.md                  主流程：11 步
├── agents/openai.yaml
├── assets/templates/         五个产物模板
└── references/               受众与结果、证据与可信度、结构模式、
                              形式选择、蓝图模板与契约、写法、展示文案写法、
                              项目叠加层说明
```

## 安装

1. 把本目录放进你的 agent skills 目录，或用仓库根 `README.md` 的安装方式。
2. 同时安装 `visual-motion-design`，才能完成"蓝图到页面"的链路。

本 skill 没有脚本，没有网络依赖，没有第三方 skill 依赖。

## 边界

1. 不发明数据。资料里没有的写成"缺口"。
2. 评价词（"显著""领先"）视为断言，必须有来源。
3. 受众分析只记"对方关心什么"，不写"怎么说"。
4. 用户原话优先于本 skill 的任何规则。
5. 项目特有规则放在项目叠加层。写法见 `references/project-overlay.md`。

## 验证状态

| 项 | 状态 |
|---|---|
| `scripts/check_skill_structure.sh skills/content-blueprint` | 通过 |
| `SKILL.md` 第 9 节的样例任务 B1、B2、B3 | 未跑 |
| 与视觉侧的退回往来 | 未在真实项目里完整验证 |

## 许可与来源

MIT，见仓库根 [LICENSE](../../LICENSE)。写法规则参考 ASD-STE100 风格，细则见 `references/writing-style.md`。
