# niche 赛道包契约（schema v1）

> 三层模型：通用的是「动作」（引擎代码），赛道的是「知识」（本契约治理的数据包），账号的是「身份」（`~/.wxops/accounts/<slug>/`）。
> 本文档是 niche 包的**唯一格式真源**：引擎 loader、内置包、用户自定义包、测试 fixture 都以此为准。
> 改本契约 = 改 schema 版本，见 §8。

## 1. 定位

niche 包回答一个问题：**这个赛道的读者按什么维度看内容**。它提供四组赛道知识：

| 组 | 回答什么 | 对应引擎函数 |
|---|---|---|
| `content_types` | 文章按题材分几类、靠哪些词识别 | `classify_content` |
| `pain_points` | 每类题材背后读者在焦虑什么 | `classify_pain` |
| `personas` | 什么样的人在读 | `classify_persona` |
| `title_patterns` | 标题里哪些赛道词构成套路信号 | `title_structure` |

引擎（`scripts/analyze/`）**不写死任何题材名、痛点名、人群名、赛道词**——这是 DATA_CONTRACT R5 的收口。引擎只提供分类的**机制**（有序求值、首中即返、fallback、覆盖率闸门）；分类的**内容**全部来自 niche 包。

格式为 JSON 而非 YAML：分析链路承诺 `--demo --data-only` 零第三方依赖（纯 stdlib），YAML 解析需要 PyYAML。issue #41 中 `niche.template.yaml` 的措辞属形式偏差，以本契约为准。

## 2. 包的位置与解析顺序

一个 niche 包 = 一个目录，目录名即 niche id，内含单文件 `niche.json`：

```
<插件根>/niches/<id>/niche.json        # 内置包（入库，随插件分发）
~/.wxops/niches/<id>/niche.json        # 用户包（运行态，永不入库）
```

loader（`scripts/analyze/niche_loader.py`）按以下顺序解析 id：

1. **用户目录优先**：`$WXOPS_HOME/niches/<id>/niche.json`（`WXOPS_HOME` 未设时为 `~/.wxops`，与 cli/env.py 同一约定；loader 直接读环境变量，不 import cli 层）。存在即用——同 id 用户包**整体覆盖**内置包，不做字段级合并。
2. **内置目录**：`<插件根>/niches/<id>/niche.json`。
3. **都没有** → 回落 `_generic` 包，并向 stderr 打警告（`⚠ 未找到赛道包 <id>，已回落 _generic 通用兜底`）。回落事实同时记入报告 `niche_coverage.requested_id`（§5），不允许静默。

**错误语义（缺包 ≠ 坏包）**：

- 缺包（id 查无）→ 回落 `_generic` + 警告。用户可能只是还没建包。
- 坏包（JSON 解析失败 / §7 校验不过）→ **硬报错退出**，报错必须带文件绝对路径与具体哪条校验失败。用户显然在尝试自定义，静默回落只会让他以为生效了。

## 3. `niche.json` schema v1

顶层字段（全部必填，除非标注可选）：

```jsonc
{
  "niche_schema_version": 1,        // int，本契约版本，loader 只认 1
  "id": "ai-tools",                 // 目录名必须与此一致，loader 校验
  "name": "AI 工具与编程",           // 人类可读赛道名，报告/看板展示用
  "description": "……",              // 可选，一句话说明适用范围
  "content_types": { … },           // §3.1
  "pain_points": { … },             // §3.2
  "personas": { … },                // §3.3
  "title_patterns": { … }           // §3.4
}
```

### 3.1 `content_types` — 题材分类

```jsonc
{
  "names": [                        // 题材全集，顺序 = 报告 by_content_type 的行序
    "风险/账号/额度焦虑",
    "价格/额度/羊毛情报",
    "模型发布/能力解读",
    "AI 编程/Agent 工作流",
    "产品/副业/商业化",
    "泛 AI 热点/效率工具"
  ],
  "rules": [                        // 有序词表规则，首中即返；顺序可以 ≠ names 顺序
    { "type": "风险/账号/额度焦虑", "terms": ["封号", "废掉", "…"] },
    { "type": "价格/额度/羊毛情报", "terms": ["免费", "额度", "…"] }
    // …
  ],
  "fallback": {                     // 所有 rules 都未命中时的兜底
    "title_regex": "ai|工具|效率|…",  // 可选；对小写化标题做 re.search
    "type": "泛 AI 热点/效率工具"      // 兜底题材，必须在 names 里
  }
}
```

引擎语义（固定，不随包变）：

- `rules` 按数组顺序求值，`terms` 命中口径 = `has_any(text_blob(record), terms)`（标题+摘要拼接小写全文包含匹配）。**注意 rules 顺序独立于 names 顺序**——ai-tools 包实际求值序是 风险→价格→Agent→模型→商业，而 names 展示序模型在 Agent 前，两者都必须逐项照抄现状，不得"顺手对齐"。
- `fallback.title_regex` 命中与未命中殊途同归都返回 `fallback.type`（继承现状），但**两条路径都计为 fallback 命中**，进覆盖率分母（§5）。
- 空 `rules`（`[]`）合法：一切文章都走 fallback——这是 `_generic` 包的形态（§6）。

### 3.2 `pain_points` — 痛点映射

```jsonc
{
  "names": [ /* 痛点全集，顺序 = 报告 by_pain_point 行序 */ ],
  "by_content_type": {              // 题材 → 痛点直映射
    "风险/账号/额度焦虑": "账号安全与权限焦虑"
    // …
  },
  "term_rules": [                   // 直映射未覆盖的题材，按词表回落，有序首中即返
    { "terms": ["免费", "价格", "额度", "订阅"], "pain": "成本、额度与订阅压力" }
  ],
  "default": "热点信息差与谈资"       // 全部未中的最终值
}
```

求值序（引擎固定）：`by_content_type` 精确查 → `term_rules` 顺序求值（口径同 §3.1 的 text_blob）→ `default`。所有映射值必须 ∈ `names`。

### 3.3 `personas` — 人群规则链

```jsonc
{
  "names": [ /* 人群全集，顺序 = 报告 by_persona 行序 */ ],
  "rules": [                        // 有序规则，首中即返
    {
      "if": {                       // 条件对象，多键为 AND；至少一键
        "terms_any": ["codex", "claude", "…"],   // text_blob 命中任一词
        "content_type": "AI 编程/Agent 工作流",   // 题材精确等于
        "pain": "成本、额度与订阅压力"             // 痛点精确等于
      },
      "then": "AI 编程/Agent 实践者"
    }
    // …
  ],
  "default": "AI 新闻观察者"
}
```

三种条件键：`terms_any`（词表任一命中）、`content_type`、`pain`（精确匹配）。多键同现取 AND。嵌套分支用「先窄后宽」的有序规则展开表达——ai-tools 导出时原代码的

```python
if has_any(text, 品牌词):
    if content_type == "AI 编程/Agent 工作流": return A
    return B
```

展开为两条规则：`{terms_any+content_type} → A` 在前，`{terms_any} → B` 在后。所有 `then`/`default` 值必须 ∈ `names`。

### 3.4 `title_patterns` — 标题套路词表

```jsonc
{
  "keys": [                         // 套路全集，顺序 = 报告 by_title_pattern 行序
    "风险损失型", "价格福利型", "模型发布型", "对比替代型",
    "教程清单型", "疑问反常识型", "工作流案例型", "普通资讯型"
  ],
  "slots": {                        // 四个赛道语义槽：给词表 + 给标签
    "risk":     { "label": "风险损失型", "terms": ["封号", "废掉", "…"] },
    "price":    { "label": "价格福利型", "terms": ["免费", "额度", "…"] },
    "release":  { "label": "模型发布型",
                  "subject_terms": ["glm", "kimi", "…"],      // 主体词（现 has_model_word 词表）
                  "action_terms": ["发布", "开源", "上线", "新", "更新", "拿下"] },
    "workflow": { "label": "工作流案例型", "terms": ["codex", "agent", "…"] }
  }
}
```

**引擎/包边界（本契约最重要的一条切线）**：

- **进包**：四个槽的词表与标签。槽名 `risk / price / release / workflow` 是引擎固定词汇（换赛道换词不换槽——母婴号的 risk 槽放安全隐患词，release 槽放品牌上新词）。
- **留引擎**：通用结构特征及其标签——数字（`has_number`，CJK 数字感知）、对比（`对比替代型`）、教程清单（`教程清单型`）、疑问（`疑问反常识型`）、兜底（`普通资讯型`），任何语言任何赛道都成立，niche 包不可改。
- **求值与拼装序（引擎固定，决定 `primary_pattern`）**：risk → price → release（subject 且 action 同现）→ 对比 → 教程|数字 → 疑问 → workflow → 全空补「普通资讯型」。
- **输出字段名不变**：`title_structure` 返回的 `has_price_word / has_risk_word / has_model_word / has_comparison / has_question / has_tutorial / has_number` 等布尔字段名是 report.json 既有 schema（DATA_CONTRACT），槽词表换内容不换字段名。
- 校验：`keys` 必须恰好等于 4 个槽 label ∪ 4 个引擎固定标签（集合相等，顺序由包定）。槽可留空词表（`terms: []`），对应套路恒不触发，但 label 仍须在 `keys` 里。

## 4. niche 的选择与传导

```
account 模式:  account.json 的 "niche" 字段（accounts add --niche 写入，缺省 "ai-tools"）
legacy --workspace / --demo:  固定 "ai-tools"（npm 老用户零行为变更）
```

传导链：`main.py` → `analyze_cmd.run(niche=…)` → `_run_build` 子进程参数 `--niche <id>` → `build_wechat_ops_report.py` argparse（default `"ai-tools"`）→ `niche_loader.set_active(load_niche(id))`。

classify 各函数经 `niche_loader.get_active()` 取当前包；`get_active()` 在未显式 set 时懒加载 `ai-tools`——保证任何旧调用路径（含直接 import classify 的测试）行为不变。批量模式（`analyze --all`）逐号传各自的 niche。

## 5. 覆盖率闸门（C4）——专治「静默错误」

一个包用在不对的账号上，最危险的输出不是报错而是**看起来像样的错误结论**。闸门语义：

- **口径**：与 `analysis.by_content_type` 相同的 stable 文章集合。
- **命中定义**：`classify_content` 经 `rules` 词表命中 = term hit；走 `fallback`（无论 regex 中否）= fallback。
- **hit_rate** = term hits ÷ total（total=0 时记 0.0 且不触发 alert——空数据不是覆盖问题）。
- **阈值**：0.6，引擎常量（`constants.py`，通用层），v1 不做包级覆写。

报告新增块 `report.json → niche_coverage`：

```jsonc
{
  "niche_id": "ai-tools",          // 实际生效的包
  "niche_name": "AI 工具与编程",
  "requested_id": "ai-tools",      // 请求的包；≠ niche_id 即发生过 _generic 回落
  "total": 123,
  "term_hits": 100,
  "fallback_count": 23,
  "hit_rate": 0.813,               // round 3 位
  "threshold": 0.6,
  "alert": false                    // hit_rate < threshold（total>0 时）
}
```

`alert == true` 时的**显式降级**（禁止任何一处静默）：

1. Markdown 报告顶部插入红色警示块：赛道包与账号内容不匹配，题材/痛点/人群三组分布不可作为决策依据，并给出两条出路（换 `--niche` / 建自定义包，指路本契约）。
2. `m8_forward`（向前看方向引擎）：降级为通用建议——只基于标题结构、长度、时间窗等**不依赖题材分类**的信号产出，输出块标 `"degraded": true` 与降级原因。
3. `m9_account_type`（账号类型路由）：回退通用链路，输出块标 `"degraded": true`。
4. 看板渲染警示留 P6（dashboard 多账号期），本期只保证数据与 MD 层完整。

## 6. `_generic` 兜底包——陌生赛道不装懂

`<插件根>/niches/_generic/niche.json`，设计意图是**恒降级**：

- `content_types.rules = []`，只有 fallback → 一切文章 fallback → `hit_rate = 0` → 闸门恒触发 → m8/m9 恒降级。
- 题材/痛点/人群各只有一个兜底名（如「综合内容」「读者关注与谈资」「大盘读者」），统计组各渲染一行——诚实地说明"引擎不认识这个赛道"。
- `title_patterns.slots` 四槽 `terms: []`，只有通用四型可触发；`keys` = 四槽 label + 通用四标签（八项仍须齐全，见 §3.4 校验）。

`_generic` 的价值不是分类质量，是**降级路径的兜底可用**：结构/长度/时间维度的分析（m1-m7 大部分）在任何赛道都成立，这些照常产出。

## 7. loader 校验规则（坏包硬报错清单）

loader 读入后必须逐条校验，任一不过即报错退出（带路径与条目）：

1. `niche_schema_version == 1`；
2. `id` 与所在目录名一致；`name` 非空；
3. 四大组俱全；各 `names` 非空、无重复；
4. `content_types.rules[*].type`、`fallback.type` ∈ `content_types.names`；
5. `pain_points` 的 `by_content_type` 值、`term_rules[*].pain`、`default` ∈ `pain_points.names`；`by_content_type` 键 ∈ `content_types.names`；
6. `personas.rules[*].then`、`default` ∈ `personas.names`；`if` 至少一键且键 ∈ {terms_any, content_type, pain}；`if.content_type` ∈ `content_types.names`，`if.pain` ∈ `pain_points.names`；
7. `title_patterns.keys` 恰好 = 4 槽 label ∪ 4 引擎固定标签（集合相等）；四槽俱全（词表可空）；
8. 所有词表元素为非空字符串；`title_regex` 若给出必须能 `re.compile`。

## 8. 版本与非目标

- schema 演进走 `niche_schema_version` 递增 + 本契约同步修订；loader 对不认识的版本硬报错（不猜）。
- 顶层未知字段：警告后忽略（给未来版本留余地）；组内未知字段同理。
- **v1 非目标**：字段级包合并、包级阈值覆写、多包混用、正则型题材规则（词表 `has_any` 之外的匹配）、看板层警示渲染（P6）。

## 9. 内置 ai-tools 包的导出纪律（C2）

`niches/ai-tools/niche.json` 由 `classify.py` / `constants.py` 现值**逐词照抄**导出：词表不增删改一词、names 顺序照抄 `constants` 四名单、rules 求值序照抄 `classify_content` 的 if 顺序。验收即零行为变更：demo 分类输出与导出前 byte 级一致（排除时间戳类易变字段）。
