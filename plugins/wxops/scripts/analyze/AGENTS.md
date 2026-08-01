# scripts/analyze — 分析模块层(L2)

## 模块边界
输入统一为发布记录 JSON(publish-records-*.json,158 条实测结构)与可选的 raw/ 抓取数据;输出为报告的各分析章节 dict,汇总由上层 `build_wechat_ops_report.py` 编排。本目录只做纯计算与判定,不碰网络、不写 workspace。

## 文件清单
| 文件 | 职责 |
|---|---|
| `m1_checkup.py` | 账号体检:基础指标概览 |
| `m2_viral_genes.py` | 爆款基因:四象限定位(x=阅读 vs 中位数,y=分享率 vs 中位数) |
| `m3_content_engine.py` | 内容引擎:题材/栏目产出结构 |
| `m4_audience.py` | 受众画像:容忍缺失数据,画像不可用时降级(`age=[]` → "年龄段未知") |
| `m5_growth_funnel.py` | 增长漏斗:阅读→互动→转化链路 |
| `m6_action_plan.py` | 行动计划三栏(v2) |
| `m7_standards.py` | 全局相对论基准:只看本号相对值,不看绝对值 |
| `m8_forward.py` | 向前看引擎(Direction Engine v1) |
| `m9_account_type.py` | 账号类型识别与分析路由(account-type-router-v1) |
| `classify.py` / `stats.py` / `confidence.py` | 题材分类 / 统计原语 / 置信度判定 |
| `constants.py` | 阈值与常量,改阈值只动这里 |
| `enrich.py` | 记录级衍生字段计算 |
| `io_utils.py` | IO 口径:画像字段"有数据" = 非空 list/dict,字符串/None/标量一律不算 |

## 本地规则
- 新增分析模块沿用 `m<N>_<name>.py` 命名,并在 `build_wechat_ops_report.py` 注册。
- 所有模块必须容忍字段缺失/畸形数据,降级输出而不是抛异常(m4 修复的教训,见 issue #24)。
- 改判定口径先改 `io_utils.py`/`constants.py`,不要在各模块内散落魔法值。
- 对应测试在 `../../tests/`,改动后必须跑 `python3 -m pytest tests -q`。
