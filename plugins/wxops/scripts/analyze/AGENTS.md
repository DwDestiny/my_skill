# scripts/analyze — 分析模块层(L2)

## 模块边界
输入统一为发布记录 JSON(publish-records-*.json,158 条实测结构)与可选的 raw/ 抓取数据;输出为报告的各分析章节 dict,汇总由上层 `build_wechat_ops_report.py` 编排。本目录只做纯计算与判定,不碰网络、不写 workspace。

## 文件清单
| 文件 | 职责 |
|---|---|
| `m1_checkup.py` | 账号体检:基础指标概览；互动满分 25 按可得维度重分配（issue #61） |
| `m2_viral_genes.py` | 爆款基因:四象限定位(x=阅读 vs 中位数,y=分享率 vs 中位数) |
| `m3_content_engine.py` | 内容引擎:题材/栏目产出结构 |
| `m4_audience.py` | 受众画像:容忍缺失数据,画像不可用时降级(`age=[]` → "年龄段未知")；`fans_portrait_available` 供上层质量章双覆盖披露（issue #54，质量章文案在 `build_wechat_ops_report.py`，不改 completeness） |
| `m5_growth_funnel.py` | 增长漏斗:阅读→互动→转化链路 |
| `m6_action_plan.py` | 行动计划三栏(v2) |
| `m7_standards.py` | 全局相对论基准:只看本号相对值,不看绝对值；zaikan 不可得时阈值输出 None（issue #61） |
| `m8_forward.py` | 向前看引擎(Direction Engine v1) |
| `m9_account_type.py` | 账号类型识别与分析路由(account-type-router-v1) |
| `classify.py` / `stats.py` / `confidence.py` | 题材分类(数据驱动,名单与词表来自 niche 赛道包) / 统计原语 / 置信度判定 |
| `rates.py` | 互动率聚合唯一入口（issue #59）：`aggregate_rate`=ratio-of-means；`median_rate`=min_reads 过滤后中位数 |
| `scoring_thresholds.py` | 公众号互动率打分阈值（issue #74）：`InteractionThresholds` frozen dataclass + `DEFAULT_INTERACTION_THRESHOLDS` 平台级默认；m9 互动判据唯一落脚点；并负责赛道覆写校验（`validate_threshold_overrides` / `merge_thresholds` / 字段归类守卫） |
| `topic_roles.py` | 题材运营角色判定（issue #60）：数据特征→workhorse/volatile/reach_entry/loyalty_base；`assign_topic_roles` |
| `metric_registry.py` | 指标维度注册表 + 可得性探测（issue #61）：`METRIC_DIMENSIONS` 单一真源；`probe_availability` 四态申报；core 缺口驱动 `metric_pending_count` |
| `niche_loader.py` | 赛道包加载:解析序(用户覆盖→内置→_generic 回落)、schema v1 校验、可选 recommendations / scoring、会话态 get_active/set_active |
| `constants.py` | 阈值与常量(含覆盖率闸门 `NICHE_COVERAGE_ALERT_THRESHOLD`),改阈值只动这里 |
| `enrich.py` | 记录级衍生字段计算 |
| `io_utils.py` | IO 口径:画像字段"有数据" = 非空 list/dict,字符串/None/标量一律不算 |

## 本地规则
- 新增分析模块沿用 `m<N>_<name>.py` 命名,并在 `build_wechat_ops_report.py` 注册。
- 所有模块必须容忍字段缺失/畸形数据,降级输出而不是抛异常(m4 修复的教训,见 issue #24)。
- 改判定口径先改 `io_utils.py`/`constants.py`,不要在各模块内散落魔法值。
- 赛道知识(题材/痛点/人群名单与词表)只进 `../../niches/<id>/niche.json`,不进本目录代码;格式真源 `../../references/niche-contract.md`。`niche_coverage.alert` 时 m8/m9 显式降级(`degraded: true`),非 alert 不加任何字段。
- 对应测试在 `../../tests/`,改动后必须跑 `python3 -m pytest tests -q`。
