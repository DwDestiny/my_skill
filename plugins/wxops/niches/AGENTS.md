# niches — 内置赛道包(L2)

## 模块边界
赛道知识数据包(三层模型的"知识"层):题材/痛点/人群名单与词表、标题套路四槽。**纯 JSON 数据,零代码**;引擎(`../scripts/analyze/`)经 `niche_loader.py` 加载消费。格式唯一真源:`../references/niche-contract.md`(schema v1)。

## 包清单
| 目录 | 用途 |
|---|---|
| `ai-tools/` | AI 工具与编程赛道。自 classify/constants 旧硬编码**逐词导出**(P3/#41),导出后包文件即唯一真源 |
| `_generic/` | 兜底包:`rules: []` 恒走 fallback → 覆盖率恒 0 → 恒触发警示恒降级——陌生赛道不装懂,只保结构/长度/时间类通用分析 |

## 本地规则
- 用户自定义包放 `~/.wxops/niches/<id>/niche.json`,同 id **整包覆盖**内置(字段级合并是 v1 非目标);模板见 `../templates/niche.template.json`。运行态永不入库。
- 改内置包词表 = 改分类行为:必须同步过 `../tests/test_niche_coverage.py` 的字面量钉死测试(改包先改测试,两处一起动),并复核 demo 基线。
- 新增内置包:目录名 = 包 `id`,过 loader 全部校验(契约 §7),并在本表登记。
- schema 演进走 `niche_schema_version` 递增 + 同步修订 niche-contract.md;loader 对不认识的版本硬报错,不猜。
