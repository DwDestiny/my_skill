# templates — 用户侧模板(L2)

## 模块边界

复制到运行态(`~/.wxops/`)后由用户填写的模板。插件内模板只读;填完的实例是账号/赛道资产,永不入库。

## 成员清单

| 模板 | 复制到 | 用途 |
|---|---|---|
| `persona.template.md` | `accounts/<slug>/persona.md` | 账号人设(三件套之一) |
| `evidence-pack.template.md` | `accounts/<slug>/topics/<topic-slug>/evidence.md` | 证据包(三件套之三) |
| `topic-card.template.md` | `accounts/<slug>/topics/<topic-slug>/card.md` | 选题卡(topics 站产出) |
| `niche.template.json` | `~/.wxops/niches/<id>/niche.json` | 自定义赛道词表包(P3) |

## 本地规则(占位符契约——kit 门禁判定依据)

- Markdown 模板的必填位一律用 `{{...}}` 占位符。**`wxops kit` 以"文件含 `{{` 子串"判定为空壳拒绝开工**——改模板不许引入非占位符用途的 `{{`,也不许换占位符记号(要换先改 kit 与本文)
- 模板头部 HTML 注释写明落点路径与填写约定;`> 填写指引` 引用块建议用户填完删除
- 新增模板:头注释 + `{{}}` 占位符 + 本表登记,三件一起做
