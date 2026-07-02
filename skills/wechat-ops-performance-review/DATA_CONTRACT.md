# DATA_CONTRACT.md — 向前看引擎数据契约

> 本文件是「分析层(Python)」与「看板前端(dashboard)」之间的**唯一接口契约**。
> 分析层(R4b)按本文产出数据;前端(R4d)按本文读取数据。任何一方要改字段,先改本文。
>
> 配套设计文档:`DESIGN.md`(整体)、`SKILL.md`(交互流)。本文只管「向前看引擎」新增的数据结构。

---

## 0. 背景与定位

### 0.1 这是什么

在现有「七模块诊断」(checkup / viral_genes / content_engine / audience / growth_funnel / action_plan / standards)之前,插入一条**向前看主线**:

```
照镜子(现状) → 动态推路(候选方向) → 选方向(用户定目的) → 收口 → 排矩阵(规划)
```

核心公式:**方向 = f(历史文章现状)**。

- 方向不是固定菜单,是**从这个号自己的历史文章里推导出来**的几条可能路径。
- 换一个账号(母婴/财经/情感),投影同一个底池,推出的方向、可行性、差距**全不同**。
- 原七模块降为「**证据层**」,支撑现状判断。

### 0.2 价值中立红线(实现与渲染都必须守)

1. **不预设优劣**:资讯流量号、人设变现号、情感号……都是正当形态,不判优劣、不劝退、不推荐「最佳」。
2. **可行性 ≠ 好坏**:`feasibility` 只衡量「改造成本/信号距离」这一客观量。低档(要改造/阻力大)必须附中立补语:`改造成本高 ≠ 不推荐,是否值得由你的目的决定`。
3. **置信内化**:页面任何位置**不得出现**百分比数字作为置信度、`置信度`三字、英文变量名/桶代码(如 `role:拉新`、`path-1`、`affinity`)。置信只通过**措辞强弱 + 视觉响度 + 行动分档**传达。
4. **demo 不是 spec**:麦总玩AI 的具体题材、方向卡都是 `demo` 实例,通用 spec 里不得写死具体题材桶名。

---

## 1. 落点与不变式

### 1.1 数据落点

- 在 `build_dataset()`(`scripts/build_wechat_ops_report.py`)末尾**追加一个顶层节点** `forward_looking`。
- **绝不修改**任何现有顶层字段(meta / data_quality / articles / analysis / viral_genes / modules / …)。新引擎只读它们、只追加自己的节点。
- 建议实现文件:`scripts/analyze/m8_forward.py`,导出 `build_forward_looking(dataset) -> dict`,在 `build_dataset()` 里:
  ```python
  dataset["forward_looking"] = build_forward_looking(dataset)
  ```
  放在 `dataset["modules"] = {...}` 之后(因为要复用 modules / viral_genes / analysis / articles)。

### 1.2 输入(只读现有 dataset 字段)

| 信号需要 | 复用现有字段 | 说明 |
|---|---|---|
| 题材分布 | `dataset["analysis"]["by_content_type"]` | 每类 count/median/p75/avg;HHI 自算 |
| 爆款锚点 | `dataset["viral_genes"]["viral_formula"]`、`["quadrant"]`、`["quadrant_counts"]` | 已带 `reliable`(sample_count≥3)、`sample_count==0` fallback |
| 互动结构 | `dataset["articles"]["stable"]` 各篇 `reads/shares/comments/likes` | share_rate 已有;comment_rate=comments/reads、like_rate=likes/reads(likes 近似「在看」,口径以仓内实际字段为准,缺失则降级) |
| 原创/人味 | `stable` 各篇正文(经 enrich 匹配到的 `article_length_chars>0` 子集) | 正则近似,见 §4.4 |
| 时效/厚度 | `content_type` + `article_length_chars` | 厚度=字数中位;时效=题材近似 |
| 产能/变现 | `account_profile.publish_frequency`、断更、`account.cumulate_user`;正文私域关键词 | 见 §4.6 |

> **已知约束**:`constants.CONTENT_TYPES` 当前是为 fixtures(麦总号)配置的 AI 题材分类。引擎在「实际命中项」之上工作即可,**不要**在引擎里再写死任何题材名。题材分类通用化属于 R5,不在本次范围。

---

## 2. 顶层结构总览

```jsonc
"forward_looking": {
  "engine_version": "direction-engine-v1",
  "model_name": "动态方向推导引擎(方向 = f(历史文章现状))",
  "data_sufficiency": { ... },   // §3 强制前置闸门
  "signals": [ ... ],            // §4 六类信号
  "mirror": { ... },             // §5 照镜子:现状画像
  "archetype_affinity": [ ... ], // §6 七大类底池亲缘向量
  "candidate_paths": [ ... ],    // §7 动态方向卡 2-4 张
  "candidate_cap": { "min": 2, "max": 4, "note": "..." },
  "content_matrix": { ... }      // §8 内容矩阵(两层)+ 按方向配比 + 排期
}
```

**闸门未过时**(`data_sufficiency.passed == false`):`signals` 与 `mirror` 仍尽量产出(照镜子);`archetype_affinity` / `candidate_paths` 为**空数组**;`content_matrix.by_direction` 为**空对象**。绝不硬凑方向卡。

---

## 3. data_sufficiency — 数据充分性闸门(强制前置)

```jsonc
"data_sufficiency": {
  "passed": true,                 // bool。下列任一不达标 => false
  "article_count": 42,            // 用于判定的稳定样本数(stable;若 stable 过少可回退 non_deleted,需在 reasons 注明)
  "threshold": 15,                // 文章数阈值(常量)
  "recent_gap_days": 6,           // 最近一次发布距今天数(断更);无数据=null
  "gap_threshold_days": 30,       // 断更阈值(常量)
  "reasons": [],                  // passed=false 时非空,如 ["稳定样本仅 9 篇,不足 15 篇"]
  "statement": "样本充足,可进行方向推导。"  // 中立陈述;闸门未过时如「样本还太少,先把现状照清楚」
}
```

判定规则(任一触发 => `passed=false`):
- 稳定样本 `< threshold(15)`;
- 最近断更 `recent_gap_days > gap_threshold_days(30)`;
- 关键字段(reads/published_at)大面积缺失(缺失率 > 40%)。

---

## 4. signals — 六类信号

数组,固定 6 个对象,顺序固定。**每个信号都必须带 `computability`**。

```jsonc
{
  "key": "topic_distribution",     // 固定枚举键(见下表),前端不渲染此键
  "name": "题材分布与集中度",       // 中文名(可渲染)
  "reads_as": "这个号实际在写什么、主轴清不清晰",  // 一句解读(可渲染)
  "computability": "直接可算",      // 枚举:直接可算 | 正则近似 | 需NLP
  "level": "中",                   // 定性分档:强 | 中 | 弱(用于坐标轴定位与视觉响度)
  "detail": { ... }                // 原始数据(供可视化;数值不得直接渲染成「置信分」)
}
```

### 4.1 key 枚举与口径

| key | name | computability | detail 主要内容 |
|---|---|---|---|
| `topic_distribution` | 题材分布与集中度 | 直接可算 | `distribution:[{type,share}]`、`hhi`、`main_axis` |
| `viral_type` | 爆款类型 | 直接可算(受样本约束) | `topic`、`title_pattern`、`sample_count`、`reliable`(直接取 viral_formula) |
| `interaction` | 互动结构 | 直接可算 | `share_rate`、`comment_rate`、`like_rate`(三者相对高低 + 主导项) |
| `originality` | 原创比例与人味浓度 | 正则近似 | `original_ratio`(若有原创字段则直接可算)、`first_person_density`(分档)、`personal_story_ratio`(分档) |
| `timeliness_depth` | 时效结构与篇幅厚度 | 正则近似 | `median_length`(直接可算)、`hotspot_ratio`(题材近似)、`method_density`(关键词近似分档) |
| `capacity_funnel` | 产能底盘与变现链路痕迹 | 正则近似 | `posts_per_week`、`fans`(直接可算)、`monetization_trace`(有/疑似/无) |

### 4.2 level 分档原则

- `直接可算` 信号:按实际数值相对本号/常识阈值分 强/中/弱。
- `正则近似` 信号:只用于把账号放到坐标轴某一档(强/中/弱),**不输出精确分**,且 `detail` 里对近似项标注「近似」。

### 4.3 viral_type 与样本闸门

直接复用 `viral_genes.viral_formula`。`reliable==false`(sample_count<3)时,该信号在 mirror / 方向卡里只能作**线索级**表述(「流量命脉疑似来自X(样本偏少)」),不得作硬结论。

### 4.4 originality / 人味(正则近似)

- 第一人称密度:扫匹配到正文的文章,正文中 `我/我们/咱` 词频 → 分档。
- 个人经历篇:标题/开头命中 `我的/亲历/复盘/这一年/踩坑` 等 → 占比分档。
- 只在 `article_length_chars>0`(匹配到正文)的子集上算;匹配率低时 `detail` 注明覆盖率与不确定性。

### 4.5 timeliness_depth(正则近似)

- 厚度:`article_length_chars` 中位(直接可算)。
- 方法/案例密度:正文扫 `步骤/方法/案例/拆解/清单` → 分档(近似)。
- 时效:追热点题材占比(由 content_type 近似)。

### 4.6 capacity_funnel(正则近似)

- 产能:`account_profile.publish_frequency`(篇/周)、断更天数、`account.cumulate_user`(粉丝)→ 直接可算。
- 变现痕迹:正文扫 `微信/二维码/加群/扫码/领取/星球/咨询/付费` → 三档 `有 | 疑似 | 无`(近似检出)。

---

## 5. mirror — 照镜子(现状画像)

```jsonc
"mirror": {
  "statement": "你现在是一个聚焦中等、信任取向偏强、厚度中上、人味中等的早期号,主轴是 AI 工具测评,流量命脉来自风险/额度类(基于 N 篇样本),变现链路基本空白。",
  // ↑ 第一落点导语本体。纯中立陈述,无褒贬、不贴菜单标签,显式带出样本量与不确定性。

  "axes": [
    { "key": "orientation", "label": "取向", "low": "流量钩子", "high": "信任认同", "level": "强", "note": "在看率偏高" },
    { "key": "focus",       "label": "聚焦", "low": "泛",       "high": "单一主轴", "level": "中", "note": "" },
    { "key": "timeliness",  "label": "时效", "low": "资讯",     "high": "长青",     "level": "中", "note": "" },
    { "key": "depth",       "label": "厚度", "low": "轻薄",     "high": "厚重方法", "level": "中", "note": "" },
    { "key": "humanity",    "label": "人味", "low": "资产化",   "high": "强人设",   "level": "中", "note": "近似" },
    { "key": "emotion",     "label": "情绪", "low": "信息导向", "high": "情绪共鸣", "level": "弱", "note": "" }
  ],
  // 坐标轴价值中立,position 用 level(强/中/弱)即可,不输出数字分。
  // 底盘(产能/规模)不入轴,作为 candidate_paths 可行性的修正项。

  "main_axis": "AI 工具测评",
  "traffic_artery": { "topic": "风险/账号/额度焦虑", "sample_count": 4, "reliable": true },
  "monetization_maturity": "空白",   // 空白 | 早期 | 成长 | 成熟
  "uncertainty_note": "人味/厚度为正则近似;爆款锚点基于 4 篇样本,样本有限,结论可用但不宜过度外推。"
}
```

前端:`statement` 作为照镜子屏顶部大字导语;`axes` 渲染成一张「现状坐标定位图」作主视觉;`traffic_artery.reliable==false` 时该项以较低视觉响度 + 中立措辞标注。

---

## 6. archetype_affinity — 七大类底池亲缘向量

底池(pool,固定 7 类,**不是菜单**):资讯流量型 / 人设IP型 / 知识服务型 / 垂直专家型 / 产品品牌型 / 带货电商型 / 社群情感型。

```jsonc
"archetype_affinity": [
  { "archetype": "资讯流量型", "affinity": "高", "adjacent": ["人设IP型"], "reason": "题材以工具情报为主、单篇生命周期短" },
  { "archetype": "人设IP型",   "affinity": "中", "adjacent": ["垂直专家型","社群情感型","知识服务型"], "reason": "在看率高、有复盘人味原料" }
  // 只列被命中的原型(affinity≠无)。纯转载号不触发人设/专家/情感等。
]
```

- `affinity`:`高 | 中 | 低 | 无`(无亲缘的原型**不出现**在数组里)。
- 产出的是**亲缘向量**,不归一到单一原型 → 候选方向可落在两相邻原型之间(参考 `adjacent`,如 资讯×人设)。

---

## 7. candidate_paths — 动态方向卡(2-4 张)

```jsonc
"candidate_paths": [
  {
    "id": "path-1",                    // 内部 id,前端不渲染
    "path_name": "把测评做成 AI 工具资讯号",   // 该号自己的具象路径名(非大类名)
    "mode": "顺势放大",                 // 命中的推导模式(可渲染为小标签或不渲染)
    "rationale_from_status": "你 60% 已是工具测评、它也是你的流量命脉(基于现有 N 篇样本),顺着最强的线放大信号距离最小。",
    "feasibility": "顺手",              // 顺手 | 够得着 | 要改造 | 阻力大
    "feasibility_note": null,          // 低档(要改造/阻力大)必填中立补语;高档可 null
    "gap": [                           // 与现状的差距清单(可执行)
      "更新频率要更稳更勤",
      "标题更钩子化、选题追新品热点",
      "876 粉离流量主门槛还远,前半段先把阅读和粉丝做起来"
    ],
    "monetization": "流量主广告分成为主,放大覆盖面与更新频率即放大收入。",
    "matrix_hint": "拉新桶填入「热点速递+工具情报」题材、配比拉到 55%+,节奏调快。"  // 引用 role 桶名 + 该号动态题材名
  }
]
```

### 7.1 候选生成流程(实现要点)

1. 六类信号 → 现状向量;
2. 投影七大类底池 → `archetype_affinity`(亲缘向量,可落两相邻原型之间);
3. 被亲缘命中的推导模式各产出一条候选,`candidate_cap`:不足 2 条只呈现可成立者并说明、超过 4 条按信号距离升序截断;并列方向**不分高下、平铺**;
4. 用该号真实素材把「模式产物模板」**重写**成它自己的具象方向卡(模板不得直接作卡片文案)。

### 7.2 五推导模式(+ 兜底)

| mode | 触发(when) | 产物语义(须用真实素材重写) |
|---|---|---|
| 顺势放大 | 主轴清晰 且 有稳定爆款类型(样本达阈值) | 沿当前最强信号线扩量推到极致(信号距离最小) |
| 转型升级 | 在看率/原创比例高(有认同与资产)但变现痕迹基本空 | 把已有认同升级为可承接的变现链路 |
| 收窄聚焦 | 题材偏泛/散 但某垂直题材爆款/互动显著优于整体 | 收口到单一垂直信号点深做(前提:先验证该点稳健) |
| 跨类迁移 | 现受众与另一大类亲缘高度重叠 **且 用户主动想换变现模式** | 借现有受众迁移到亲缘大类(改造成本高≠不推荐) |
| 混合演进 | 题材 2-3 块均衡 且 各块互动性质不同 | 按 role 分层组合现有内容块 |
| insufficient_data | 未过数据充分性闸门 | 不产出方向卡,只照镜子 + 提示补数据 |

### 7.3 feasibility 计算

`feasibility = g(信号距离)`:距离小=顺手,需从 0 建人设/换受众=阻力大;再叠加底盘修正(粉丝/产能弱时,需要「养」的路径往中期挪)。只衡量改造成本,不掺方向好坏。低档统一附 `feasibility_note`。

---

## 8. content_matrix — 内容矩阵(两层)

```jsonc
"content_matrix": {
  "model_name": "方向参数化内容矩阵(role 维度固定 / 题材维度动态)",
  "roles": ["拉新", "养信任", "建专业", "转化", "留存"],   // 固定层,任何账号通用
  "by_direction": {
    "path-1": {                       // key = candidate_path.id,每张方向卡一份
      "buckets": [
        {
          "role": "拉新",
          "topics": ["热点速递", "工具情报"],   // 动态:现状题材聚类(CONTENT_TYPES 实际命中项)+ 方向缺口
          "weight": 0.55,                       // 配比(0-1);前端渲染成环/条,不渲染成「置信度」
          "horizon": "本周可发",                 // 本周可发 | 需积累
          "rhythm": "节奏调快、标题钩子化"
        }
        // ≤6 桶;无内容的 role 可不出桶(可少于 5)
      ],
      "schedule": [                   // 分阶段起号节奏表
        { "phase": "第 1-2 周", "focus": "把更新频率做稳", "cadence": "每周 5 更", "topics": ["工具情报", "热点速递"] },
        { "phase": "第 3-4 周", "focus": "钩子化标题 + 追新品", "cadence": "每周 5-7 更", "topics": ["新品测评"] }
      ]
    }
  }
}
```

参数化规则:
- **role 维度固定**(拉新/养信任/建专业/转化/留存),**题材维度动态**(由「现状题材聚类 + 所选方向缺口」生成,非预置)。
- **方向定配比**(每张方向卡一组 weight),**现状定起点**(已强桶顺势放大、空白桶从小比例试水)。
- 同一框架,换方向换配比、换账号换题材。`by_direction` 为**每张候选方向卡都预算好一份**,前端选方向时直接读对应那份 → 实时重排。

---

## 9. 前端契约(R4d 怎么读)

### 9.1 新增主屏(插在七模块前)

| 屏 | 数据源 | 主视觉 | 关键渲染 |
|---|---|---|---|
| 数据不足屏(闸门未过) | `data_sufficiency`(passed=false) | 无;大字导语 | `statement` 作 hero;reasons 列待补项(butter 色) |
| 照镜子屏 | `mirror` | 现状坐标定位图 | `statement` 作 hero 导语;`axes` 主视觉;不可靠项低响度 |
| 动态推路屏 | `candidate_paths` | 纵向方向卡列(2-4) | 导语点明「从你文章里长出来、非通用菜单」;每卡 path_name+rationale+feasibility(中文档)+gap+matrix_hint;平等排布无高下 |
| 规划矩阵屏 | `content_matrix.by_direction[selected]` | ≤6 桶配比环/条(55%+) | 桶按 role 马卡龙着色、题材标签为动态题材名;切换方向实时重排;排期表纵向下落在主视觉下 |

### 9.2 选方向交互(全链路真算)

- 用户点选 `candidate_paths` 中一张 → 前端 state `selectedPathId`(默认第一张或不选)。
- 规划矩阵屏读 `content_matrix.by_direction[selectedPathId]` → 配比/排期实时重排。
- 选中卡以马卡龙色描边发丝线标记、其余退后(响度差)。**不给**「推荐/最佳/避坑/逃离」任何标签。

### 9.3 量化标准屏(保留独立,改造)

- 保留为独立屏(读现有 `modules.standards` / m7 产出)。
- 改造成「一个巨数(爆款门槛)+ 三个无框小注」定义表,数字右对齐成列,Space Grotesk。

### 9.4 渲染禁令(对照 §0.2)

- 不渲染:`%` 作置信度、`置信度`三字、英文 key/id/role 代码(`path-1`、`role:拉新`、`affinity`、`weight` 字样)。
- `feasibility` 低档 → 中立措辞 + `feasibility_note`,**不渲染成劝退**。
- 配比 `weight` 可视化成环/条,旁注用中文百分比是允许的(那是配比不是置信度);但**置信**永不用数字。

---

## 10. 验收(R4b pytest 必须覆盖)

放 `tests/test_forward.py`(或扩 `test_modules.py`):

1. **闸门**:构造 stable<15 的 fixture → `forward_looking.data_sufficiency.passed==false` 且 `candidate_paths==[]` 且 `content_matrix.by_direction=={}`。
2. **signals 完整**:6 个信号齐全、key 顺序固定、每个有合法 `computability`(三枚举之一)与 `level`(强/中/弱)。
3. **候选数量**:达标 fixture → `2 <= len(candidate_paths) <= 4`。
4. **方向卡字段**:每张卡 path_name/rationale_from_status/feasibility/gap/monetization/matrix_hint 齐全;feasibility ∈ {顺手,够得着,要改造,阻力大};低档卡 `feasibility_note` 非空。
5. **矩阵两层**:`content_matrix.roles == ["拉新","养信任","建专业","转化","留存"]`(固定);每个 `by_direction[path_id]` 有 buckets(≤6)与 schedule;桶 topics 来自实际命中题材(非空)。
6. **中立性**:遍历所有会被渲染的中文字符串字段(statement/rationale/gap/feasibility_note/matrix_hint/schedule.focus 等),断言**不含** `置信度`、不含裸英文 key(`path-`、`role:`、`affinity`)、feasibility 不含 `%`。
7. **demo 可跑**:对仓内 fixtures(麦总号)跑通,`candidate_paths` ≥ 2 张。
8. **不破坏旧字段**:断言所有原有顶层键仍在(回归)。

---

## 11. demo 实例(麦总玩AI,仅供参考,非通用预置)

| path_name | feasibility | rationale 要点 | matrix_hint |
|---|---|---|---|
| 把测评做成 AI 工具资讯号 | 顺手 | 60% 已是工具测评 + 流量命脉,顺最强线放大 | 拉新桶「热点速递+工具情报」55%+,节奏快 |
| 放大复盘+判断做独立开发者人设号 | 够得着 | 在看率高=认同,信任变现地基;已有复盘人味 | 养信任桶「我的判断+复盘实战」45%+,加私域承接 |
| 收窄到 Agent 工作流做垂直专家号 | 要改造 | 测评太宽难有壁垒;若 Agent 工作流信号更优(需验证) | 建专业桶「单场景工作流方法拆解」60%+,厚度上调 |

> 这三张卡是从麦总号**真实构成动态推导**出来的它自己的产物,不是内置菜单。换账号则全变。

---

## 12. account_type — 账号类型识别与路由（追加节点，v1.1）

在 `forward_looking` 之后追加顶层节点 `account_type`（`scripts/analyze/m9_account_type.py`，engine `account-type-router-v1`）。**只增不删**：不修改任何现有字段；dashboard 未消费该节点时可安全忽略。

```jsonc
"account_type": {
  "engine_version": "account-type-router-v1",
  "primary":   { "key": "knowledge_service", "name": "知识服务/教育号", "score": 0.78 },  // general 时 score=null
  "secondary": { "key": "personal_ip", "name": "内容IP/个人品牌号", "score": 0.65 },      // 次优达阈值才有,否则 null
  "confidence": "medium",            // high | medium | low(内部档位,不渲染成数字)
  "fallback_to_general": false,      // 样本<8 或全类型得分<0.45 时 true
  "decision_note": "类型特征基本成立,建议积累样本后复核",
  "scores": { "media_news": 0.15, "personal_ip": 0.65, "...": 0.0 },   // 六类型 0-1
  "evidence": ["方法/教程类内容占 33%,篇幅中位 2520 字"],               // 中文,引用真实特征值
  "features": { "sample_count": 18, "posts_per_week": 2.6, "...": 0 }, // 识别用原始特征
  "playbook": {
    "name": "知识服务/教育号",
    "north_star": ["..."],           // 该类型核心成功指标
    "diagnosis_focus": ["..."],      // 诊断重点
    "module_weights": { "checkup": "中", "viral_genes": "高", "...": "低" },  // m1-m8 权重(高/中/低)
    "reading_guide": "...",          // 差异化解读口径(可渲染)
    "action_bias": ["..."]           // 行动建议倾斜(可渲染)
  },
  "routing": { "chain": ["viral_genes", "content_engine", "..."], "note": "..." }  // 按权重排的诊断阅读顺序
}
```

红线：类型间不判优劣；所有可渲染字符串不含"置信度"等禁词；类型体系与判定细节见 `references/account-type-playbooks.md`。

---

*Contract v1.1 · 维护者:Claude(技术总监)· 实现:grok(R4b) + Fable(account_type)· 消费:dashboard(R4d)*
