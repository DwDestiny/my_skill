# grok-cli

**把 xAI 官方 Grok Build CLI 当"外部子智能体"用的实测手册。**

不是教你怎么跟 grok 聊天,是教你怎么在自己的 agent 工作流里 `grok -p ...` 跑一次性任务、拿结构化 JSON 结果、并行择优——用它承担调研、写码、对抗审查。

## 解决什么问题

官方 `--help` 能告诉你有哪些 flag,但有几件事只有跑过才知道:

| 你会踩的坑 | 手册给的答案 |
|---|---|
| 配置里写的模型没生效,还不报错 | `config.toml` 的 `default` 拿不到时 CLI **静默 fallback**。用 `jq '.modelUsage \| keys'` 验真身,永远显式传 `-m` |
| `--effort xhigh` 直接报错 | README 列的八档是**跨模型通用文档**,`grok-4.5` 实际只认 `high/medium/low` |
| 命令挂住不返回 | headless 必须 `--always-approve`(否则等工具确认)+ `</dev/null`(否则等 stdin) |
| 想用 Composer 2.5 Fast 却报 unknown model id | 该模型**真实存在**,但可能你的账号没被供应。「服务端不供应」≠「模型不存在」——判定链在手册里 |
| 拿不到结构化结果 | `--json-schema` 强制 schema 输出,结果在顶层 `structuredOutput`,**别去解析 `text` 里那串转义 JSON** |
| 不知道花了多少钱 | `--output-format json` 后 `jq '.total_cost_usd'`;单次 ≈ $0.04–0.05,系统提示占大头 |

## 内容

| 文件 | 讲什么 |
|---|---|
| `SKILL.md` | 主体:标准调用模板(逐条解释每个 flag 为什么加)、结构化输出与解析口径、模型 ID 与 effort 的真实可用范围、11 条坑、权限收敛、三条委托通路 |
| `references/cookbook.md` | 进阶:多镜头结构化对抗审查、批量 pipeline、把输出喂回宿主 agent、权限与安全、成本控制表、排障速查表 |

## 前置条件

```bash
# 装 CLI(官方安装方式以 xAI 文档为准),然后登录
grok login

# 确认你的账号实际被供应哪些模型 —— 这一步不能跳
grok models
```

手册里的模型清单是 2026-07-25 在 `0.2.112` 上用某一个账号实测的快照。**模型供应按账号、订阅、时间变化,以你自己 `grok models` 的返回为准。** 手册里长期有效的是方法(怎么判定、怎么解析、怎么避坑),不是那份清单。

## 最小可跑示例

```bash
grok -p "用一句话说明这个仓库是干什么的" \
  -m grok-4.5 --effort high --output-format json \
  --cwd "$PWD" --always-approve --max-turns 5 </dev/null \
  | jq -r '.text, .total_cost_usd'
```

跑通了(有文本 + 有费用数字),说明登录态、模型 ID、headless 三件事都对,可以往下用了。

## 安装

作为 skill 使用,把本目录放进你的 agent skills 目录即可;或用仓库根 `README.md` 里的 plugin / 手动安装方式。
