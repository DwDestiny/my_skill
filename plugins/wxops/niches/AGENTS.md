# niches — 内置赛道包(L2)

## 模块边界
赛道知识数据包(三层模型的"知识"层),一包一目录,核心文件:`niche.json`(题材/痛点/人群/标题套路四组词表,给引擎经 `niche_loader.py` 机器消费,格式真源 `../references/niche-contract.md`)+ `structure.md`(结构契约:文体骨架/必备模块/翻车点,给写作 agents 直读,P4/#42 起为写作三件套之二)+ 可选 `compliance.json`(稿件合规闸规则,给 `lint` 引擎消费)。**纯数据零代码**。

## 包清单
| 目录 | 用途 |
|---|---|
| `ai-tools/` | AI 工具与编程赛道。niche.json 自 classify/constants 旧硬编码**逐词导出**(P3/#41);structure.md 五文体骨架 + 题材×文体速查(P4/#42) |
| `_generic/` | 兜底包:niche.json `rules: []` 恒走 fallback → 恒触发警示恒降级——陌生赛道不装懂;structure.md 只给跨赛道成立的长文结构底线;compliance.json 仅绝对化用语 + 违规引流两条跨赛道通用规则 |

## 本地规则
- 用户自定义包放 `~/.wxops/niches/<id>/`,同 id 覆盖语义**分两种**:`niche.json` **整包覆盖**(用户包目录存在即以用户包 niche.json 为准,坏包硬报错);`structure.md` / `compliance.json` **文件级回落**(用户包 → 内置同 id 包 → `_generic/…`,用户只建词表不写结构/合规时回落内置而非报错)。模板见 `../templates/`。运行态永不入库。
- 改内置包词表 = 改分类行为:必须同步过 `../tests/test_niche_coverage.py` 的字面量钉死测试(改包先改测试,两处一起动),并复核 demo 基线。
- 新增内置包:目录名 = 包 `id`,过 loader 全部校验(契约 §7),并在本表登记。
- schema 演进走 `niche_schema_version` 递增 + 同步修订 niche-contract.md;loader 对不认识的版本硬报错,不猜。
